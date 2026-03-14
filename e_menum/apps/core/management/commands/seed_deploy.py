"""
seed_deploy — Single orchestration command for deploy-time seeding.

Runs ALL seed commands in the correct dependency order. Every sub-command
is idempotent (get_or_create / update_or_create), so this command is safe
to call on every deploy without risk of duplicating data.

Dependency order:
    1. seed_roles          — Roles & permissions (no deps)
    2. seed_plans          — Plans & features (no deps)
    3. seed_allergens      — EU 14 allergens (no deps)
    4. seed_menu_data      — Lezzet Sarayi org + menu + products (needs allergens)
    5. seed_all_data       — Orders, customers, media, etc. (needs menu_data)
    6. seed_extra_orgs     — 3 additional organizations (needs allergens)
    7. seed_cms_content    — Website CMS pages (no deps)
    8. seed_seo_data       — TXT configs, redirects (no deps)
    9. seed_shield_data    — Bot whitelist, rule sets (no deps)
   10. seed_report_definitions — Report catalog (no deps)

Usage in deploy.sh:
    python manage.py migrate
    python manage.py seed_deploy

Options:
    python manage.py seed_deploy --force      # Force-update existing records
    python manage.py seed_deploy --skip=seo,shield  # Skip specific seeds
    python manage.py seed_deploy --only=roles,plans  # Run only specific seeds
"""

import logging
import time

from django.core.management import call_command
from django.core.management.base import BaseCommand

logger = logging.getLogger(__name__)

# Ordered list of (key, command_name, description, supports_force)
SEED_COMMANDS = [
    ("roles", "seed_roles", "Roles & Permissions", True),
    ("plans", "seed_plans", "Plans & Features", True),
    ("allergens", "seed_allergens", "Allergens (EU 14)", True),
    ("menu", "seed_menu_data", "Menu Data (Lezzet Sarayi)", False),
    ("all", "seed_all_data", "All Admin Models", False),
    ("extra_orgs", "seed_extra_orgs", "Extra Organizations", False),
    ("cms", "seed_cms_content", "CMS Content", False),
    ("seo", "seed_seo_data", "SEO Data", False),
    ("shield", "seed_shield_data", "Shield Data", False),
    ("reports", "seed_report_definitions", "Report Definitions", False),
]


class Command(BaseCommand):
    help = (
        "Run ALL seed commands in correct order. "
        "Idempotent — safe to call on every deploy."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            help="Pass --force to commands that support it (roles, plans, allergens)",
        )
        parser.add_argument(
            "--skip",
            type=str,
            default="",
            help="Comma-separated list of seed keys to skip (e.g. --skip=seo,shield)",
        )
        parser.add_argument(
            "--only",
            type=str,
            default="",
            help="Comma-separated list of seed keys to run (e.g. --only=roles,plans)",
        )

    def handle(self, *args, **options):
        force = options["force"]
        skip_keys = {k.strip() for k in options["skip"].split(",") if k.strip()}
        only_keys = {k.strip() for k in options["only"].split(",") if k.strip()}

        self.stdout.write(
            self.style.MIGRATE_HEADING("\n═══ seed_deploy: Starting ═══\n")
        )

        total_start = time.monotonic()
        success_count = 0
        skip_count = 0
        fail_count = 0

        for key, cmd_name, description, supports_force in SEED_COMMANDS:
            # Filter logic
            if only_keys and key not in only_keys:
                continue
            if key in skip_keys:
                self.stdout.write(f"  ⊘ {description} — skipped")
                skip_count += 1
                continue

            self.stdout.write(f"\n  ▸ {description} ({cmd_name})")
            start = time.monotonic()

            try:
                cmd_kwargs = {}
                if supports_force and force:
                    cmd_kwargs["force"] = True

                call_command(cmd_name, **cmd_kwargs, stdout=self.stdout)
                elapsed = time.monotonic() - start
                self.stdout.write(self.style.SUCCESS(f"    ✓ done ({elapsed:.1f}s)"))
                success_count += 1
            except Exception as exc:
                elapsed = time.monotonic() - start
                self.stdout.write(
                    self.style.ERROR(f"    ✗ FAILED ({elapsed:.1f}s): {exc}")
                )
                logger.exception("seed_deploy: %s failed", cmd_name)
                fail_count += 1

        total_elapsed = time.monotonic() - total_start

        self.stdout.write(
            self.style.MIGRATE_HEADING(
                f"\n═══ seed_deploy: Complete ({total_elapsed:.1f}s) ═══"
            )
        )
        self.stdout.write(
            f"  ✓ {success_count} succeeded, "
            f"⊘ {skip_count} skipped, "
            f"✗ {fail_count} failed"
        )

        if fail_count:
            self.stdout.write(
                self.style.WARNING(
                    "\n  ⚠ Some seeds failed. Check logs above for details."
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS("\n  All seeds completed successfully! 🎉")
            )
