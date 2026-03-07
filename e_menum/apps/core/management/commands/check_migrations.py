"""
Django management command for checking migration status.

This command is designed for CI/CD pipelines: it inspects the current
migration state and returns exit code 1 when action is needed, allowing
automated gates before deployment.

Checks performed:
- Unapplied migrations (files exist but not in django_migrations table)
- Model changes that need new migrations (like makemigrations --check)
- Migration file conflicts (multiple leaf nodes per app)
- Migration dependency graph issues (missing deps, circular refs)
- Per-app migration status summary

Usage:
    # Full check (CI gate - exits 1 if anything needs attention)
    python manage.py check_migrations

    # Check only unapplied migrations
    python manage.py check_migrations --unapplied-only

    # Show detailed per-app status
    python manage.py check_migrations --detail

    # Output as JSON (for pipeline parsing)
    python manage.py check_migrations --json
"""

import json
import sys
from io import StringIO

from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db import connections
from django.db.migrations.executor import MigrationExecutor
from django.db.migrations.loader import MigrationLoader


class Command(BaseCommand):
    """
    Check migration status for CI/CD pipeline gating.

    Returns exit code 0 if everything is clean, exit code 1 if migrations
    are needed or issues are detected.
    """

    help = (
        "Check migration status: unapplied migrations, missing migration files, "
        "dependency issues, and conflicts. Returns exit code 1 if action needed."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--unapplied-only",
            action="store_true",
            help="Only check for unapplied migrations (skip model change detection).",
        )
        parser.add_argument(
            "--detail",
            action="store_true",
            help="Show detailed per-app migration status.",
        )
        parser.add_argument(
            "--json",
            action="store_true",
            dest="output_json",
            help="Output results as JSON for pipeline consumption.",
        )
        parser.add_argument(
            "--database",
            default="default",
            help='Database alias to check (default: "default").',
        )

    def handle(self, *args, **options):
        self.db_alias = options["database"]
        self.show_detail = options["detail"]
        self.output_json = options["output_json"]
        self.unapplied_only = options["unapplied_only"]
        self.verbosity = options["verbosity"]

        results = {
            "unapplied_migrations": [],
            "model_changes_needed": False,
            "conflicts": [],
            "dependency_issues": [],
            "app_status": {},
            "total_migrations": 0,
            "total_applied": 0,
            "total_unapplied": 0,
            "has_issues": False,
        }

        db_connection = connections[self.db_alias]
        loader = MigrationLoader(db_connection)
        executor = MigrationExecutor(db_connection)

        # 1. Check unapplied migrations
        self._check_unapplied(executor, loader, results)

        # 2. Check for model changes that need new migrations
        if not self.unapplied_only:
            self._check_model_changes(loader, results)

        # 3. Check for migration conflicts
        self._check_conflicts(loader, results)

        # 4. Check dependency graph issues
        self._check_dependencies(loader, results)

        # 5. Per-app status
        self._compute_app_status(loader, executor, results)

        # Determine overall status
        results["has_issues"] = bool(
            results["unapplied_migrations"]
            or results["model_changes_needed"]
            or results["conflicts"]
            or results["dependency_issues"]
        )

        # Output
        if self.output_json:
            self.stdout.write(json.dumps(results, indent=2, default=str))
        else:
            self._print_report(results)

        if results["has_issues"]:
            sys.exit(1)

    # ─── Checks ───────────────────────────────────────────────────

    def _check_unapplied(self, executor, loader, results):
        """Find migrations that exist on disk but are not applied to the database."""
        plan = executor.migration_plan(executor.loader.graph.leaf_nodes())
        for migration, backward in plan:
            if not backward:
                results["unapplied_migrations"].append(
                    {
                        "app": migration.app_label,
                        "name": migration.name,
                    }
                )
        results["total_unapplied"] = len(results["unapplied_migrations"])

    def _check_model_changes(self, loader, results):
        """
        Detect if models have changed in ways that require new migrations.

        This is equivalent to running `makemigrations --check --dry-run`.
        """
        try:
            out = StringIO()
            err = StringIO()
            call_command(
                "makemigrations",
                "--check",
                "--dry-run",
                verbosity=0,
                stdout=out,
                stderr=err,
                no_input=True,
            )
            # Exit code 0 means no changes needed
            results["model_changes_needed"] = False
        except SystemExit as exc:
            # Exit code 1 means changes were detected
            if exc.code == 1:
                results["model_changes_needed"] = True
            else:
                # Other exit codes are unexpected
                results["model_changes_needed"] = True

    def _check_conflicts(self, loader, results):
        """
        Detect migration conflicts (multiple leaf nodes for the same app).

        Conflicts occur when two developers create migrations from the same
        parent, producing a fork in the migration graph.
        """
        conflicts = loader.detect_conflicts()
        for app_label, migration_names in conflicts.items():
            results["conflicts"].append(
                {
                    "app": app_label,
                    "migrations": list(migration_names),
                }
            )

    def _check_dependencies(self, loader, results):
        """
        Check for broken migration dependencies.

        This catches cases where a migration references a dependency that
        does not exist (e.g. deleted migration file, typo in dependency).
        """
        graph = loader.graph

        for node_key in graph.nodes:
            node = graph.node_map.get(node_key)
            if node is None:
                continue
            for parent_key in node.parents:
                if parent_key not in graph.nodes:
                    results["dependency_issues"].append(
                        {
                            "migration": f"{node_key[0]}.{node_key[1]}",
                            "missing_dependency": f"{parent_key[0]}.{parent_key[1]}",
                        }
                    )

    def _compute_app_status(self, loader, executor, results):
        """Compute migration counts per app."""
        applied = set(executor.loader.applied_migrations)
        all_migrations = set(loader.graph.nodes)

        app_stats = {}
        for app_label, migration_name in all_migrations:
            if app_label not in app_stats:
                app_stats[app_label] = {"total": 0, "applied": 0, "unapplied": 0}
            app_stats[app_label]["total"] += 1
            if (app_label, migration_name) in applied:
                app_stats[app_label]["applied"] += 1
            else:
                app_stats[app_label]["unapplied"] += 1

        results["app_status"] = app_stats
        results["total_migrations"] = sum(s["total"] for s in app_stats.values())
        results["total_applied"] = sum(s["applied"] for s in app_stats.values())

    # ─── Output ───────────────────────────────────────────────────

    def _print_report(self, results):
        self.stdout.write("")
        self.stdout.write("=" * 60)
        self.stdout.write("  E-Menum Migration Status Report")
        self.stdout.write("=" * 60)

        # Summary
        self.stdout.write(f"\n  Total migrations: {results['total_migrations']}")
        self.stdout.write(f"  Applied:          {results['total_applied']}")
        self.stdout.write(f"  Unapplied:        {results['total_unapplied']}")

        # Unapplied migrations
        if results["unapplied_migrations"]:
            self.stdout.write(
                self.style.WARNING(
                    f"\n  Unapplied Migrations ({len(results['unapplied_migrations'])}):"
                )
            )
            for m in results["unapplied_migrations"]:
                self.stdout.write(f"    - {m['app']}.{m['name']}")
        else:
            self.stdout.write(self.style.SUCCESS("\n  All migrations are applied."))

        # Model changes
        if results["model_changes_needed"]:
            self.stdout.write(self.style.WARNING("\n  Model Changes Detected:"))
            self.stdout.write(
                '    Models have changed. Run "makemigrations" to create new migrations.'
            )
        else:
            if not self.unapplied_only:
                self.stdout.write(self.style.SUCCESS("\n  No model changes detected."))

        # Conflicts
        if results["conflicts"]:
            self.stdout.write(
                self.style.ERROR(
                    f"\n  Migration Conflicts ({len(results['conflicts'])}):"
                )
            )
            for c in results["conflicts"]:
                migrations_str = ", ".join(c["migrations"])
                self.stdout.write(f"    - {c['app']}: {migrations_str}")
        else:
            self.stdout.write(self.style.SUCCESS("\n  No migration conflicts."))

        # Dependency issues
        if results["dependency_issues"]:
            self.stdout.write(
                self.style.ERROR(
                    f"\n  Dependency Issues ({len(results['dependency_issues'])}):"
                )
            )
            for d in results["dependency_issues"]:
                self.stdout.write(
                    f"    - {d['migration']} depends on missing: {d['missing_dependency']}"
                )
        else:
            self.stdout.write(self.style.SUCCESS("\n  No dependency issues."))

        # Per-app detail
        if self.show_detail and results["app_status"]:
            self.stdout.write(self.style.MIGRATE_HEADING("\n  Per-App Status:"))
            self.stdout.write(
                f"    {'App':<30} {'Total':>6} {'Applied':>8} {'Pending':>8}"
            )
            self.stdout.write(f"    {'-' * 52}")
            for app_label in sorted(results["app_status"].keys()):
                stats = results["app_status"][app_label]
                style = (
                    self.style.SUCCESS
                    if stats["unapplied"] == 0
                    else self.style.WARNING
                )
                self.stdout.write(
                    style(
                        f"    {app_label:<30} {stats['total']:>6} "
                        f"{stats['applied']:>8} {stats['unapplied']:>8}"
                    )
                )

        # Final verdict
        self.stdout.write("")
        self.stdout.write("=" * 60)
        if results["has_issues"]:
            self.stdout.write(
                self.style.ERROR("  RESULT: Issues found. Migration action required.")
            )
        else:
            self.stdout.write(
                self.style.SUCCESS("  RESULT: All clear. No migration action needed.")
            )
        self.stdout.write("=" * 60)
        self.stdout.write("")
