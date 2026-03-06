"""
Django management command for safe database migration execution.

This command wraps Django's built-in migrate with production-safe features:
- Pre-migration checks for pending migrations
- Advisory locking to prevent concurrent migration runs
- Dry-run mode to preview changes without applying
- Rollback support to a specific migration
- Dangerous operation detection (DROP TABLE, DROP COLUMN)
- Full audit logging via MigrationLog model
- Clear success/failure reporting

Usage:
    # Apply all pending migrations safely
    python manage.py safe_migrate

    # Dry run - show what would be applied
    python manage.py safe_migrate --dry-run

    # Rollback a specific app to a migration
    python manage.py safe_migrate --rollback core 0005_add_username_to_user

    # Skip dangerous operation checks (use with caution)
    python manage.py safe_migrate --skip-dangerous-check

    # Specify who triggered the migration (for audit trail)
    python manage.py safe_migrate --applied-by deploy-pipeline
"""

import ast
import hashlib
import os
import re
import socket
import sys
import time

from django.apps import apps
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.db import connection, connections
from django.db.migrations.executor import MigrationExecutor
from django.db.migrations.loader import MigrationLoader
from django.utils import timezone

# Advisory lock ID: deterministic hash of 'safe_migrate' so it is stable
# across restarts but unique enough to not collide with application locks.
ADVISORY_LOCK_ID = int(hashlib.md5(b'safe_migrate').hexdigest()[:15], 16)


class Command(BaseCommand):
    """
    Production-safe database migration command with auditing and safety checks.
    """

    help = (
        'Apply database migrations with safety checks, advisory locking, '
        'dangerous operation detection, and full audit logging.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what migrations would be applied without executing them.',
        )
        parser.add_argument(
            '--rollback',
            nargs=2,
            metavar=('APP_LABEL', 'MIGRATION_NAME'),
            help='Rollback the specified app to the given migration name.',
        )
        parser.add_argument(
            '--skip-dangerous-check',
            action='store_true',
            help='Skip detection of dangerous operations (DROP TABLE, DROP COLUMN).',
        )
        parser.add_argument(
            '--applied-by',
            default='system',
            help='Identifier for who/what triggered this migration (default: system).',
        )
        parser.add_argument(
            '--database',
            default='default',
            help='Database alias to migrate (default: "default").',
        )

    def handle(self, *args, **options):
        self.dry_run = options['dry_run']
        self.rollback = options['rollback']
        self.skip_dangerous_check = options['skip_dangerous_check']
        self.applied_by = options['applied_by']
        self.db_alias = options['database']
        self.verbosity = options['verbosity']
        self.hostname = socket.gethostname()

        self._print_header()

        # Acquire advisory lock to prevent concurrent execution
        if not self._acquire_advisory_lock():
            raise CommandError(
                'Another safe_migrate process is already running. '
                'If this is an error, the lock will be released when that '
                'connection closes.'
            )

        try:
            if self.rollback:
                self._handle_rollback()
            else:
                self._handle_forward()
        finally:
            self._release_advisory_lock()

    # ─── Forward migration ────────────────────────────────────────

    def _handle_forward(self):
        """Apply all pending forward migrations."""
        db_connection = connections[self.db_alias]
        executor = MigrationExecutor(db_connection)
        plan = executor.migration_plan(executor.loader.graph.leaf_nodes())

        if not plan:
            self.stdout.write(self.style.SUCCESS(
                '\n  No pending migrations. Database is up to date.'
            ))
            return

        # Display pending migrations
        self.stdout.write(self.style.MIGRATE_HEADING(
            f'\n  Found {len(plan)} pending migration(s):'
        ))
        for migration, backward in plan:
            direction = 'BACKWARD' if backward else 'FORWARD'
            self.stdout.write(f'    [{direction}] {migration.app_label}.{migration.name}')

        # Dangerous operation detection
        if not self.skip_dangerous_check:
            dangerous = self._detect_dangerous_operations(plan)
            if dangerous:
                self.stdout.write(self.style.WARNING(
                    '\n  WARNING: Potentially dangerous operations detected:'
                ))
                for app_label, name, operations in dangerous:
                    self.stdout.write(self.style.WARNING(
                        f'    {app_label}.{name}:'
                    ))
                    for op in operations:
                        self.stdout.write(self.style.ERROR(f'      - {op}'))

                if self.dry_run:
                    self.stdout.write(self.style.WARNING(
                        '\n  Dry run: dangerous operations noted but not blocked.'
                    ))
                else:
                    self.stdout.write(self.style.WARNING(
                        '\n  Proceeding with caution. Use --skip-dangerous-check to suppress.'
                    ))

        if self.dry_run:
            self.stdout.write(self.style.WARNING(
                '\n  DRY RUN: No migrations were applied.'
            ))
            self._log_migrations(plan, dry_run=True)
            return

        # Apply migrations one by one with logging
        total = len(plan)
        success_count = 0
        fail_count = 0

        for idx, (migration, backward) in enumerate(plan, 1):
            app_label = migration.app_label
            name = migration.name
            direction = 'backward' if backward else 'forward'
            is_dangerous = not self.skip_dangerous_check and self._is_migration_dangerous(
                app_label, name
            )

            self.stdout.write(
                f'\n  [{idx}/{total}] Applying {app_label}.{name} ({direction})...'
            )

            log_entry = self._create_log_entry(
                app_label=app_label,
                migration_name=name,
                direction=direction,
                is_dangerous=is_dangerous,
            )

            start_time = time.monotonic()
            try:
                # Apply this single migration by targeting its node
                call_command(
                    'migrate',
                    app_label,
                    name,
                    database=self.db_alias,
                    verbosity=0,
                    no_input=True,
                )
                elapsed_ms = int((time.monotonic() - start_time) * 1000)
                self._update_log_success(log_entry, elapsed_ms)
                success_count += 1
                self.stdout.write(self.style.SUCCESS(
                    f'    OK ({elapsed_ms}ms)'
                ))

            except Exception as exc:
                elapsed_ms = int((time.monotonic() - start_time) * 1000)
                self._update_log_failure(log_entry, elapsed_ms, str(exc))
                fail_count += 1
                self.stdout.write(self.style.ERROR(
                    f'    FAILED ({elapsed_ms}ms): {exc}'
                ))
                # Stop on first failure to prevent cascading errors
                self.stdout.write(self.style.ERROR(
                    f'\n  Migration halted. {success_count} succeeded, '
                    f'{fail_count} failed, {total - idx} remaining.'
                ))
                raise CommandError(
                    f'Migration {app_label}.{name} failed: {exc}'
                )

        self._print_summary(success_count, fail_count, total)

    # ─── Rollback ─────────────────────────────────────────────────

    def _handle_rollback(self):
        """Rollback a specific app to a given migration."""
        app_label, target_migration = self.rollback

        # Validate the app exists
        try:
            apps.get_app_config(app_label)
        except LookupError:
            raise CommandError(f'App "{app_label}" not found.')

        # Validate the target migration exists
        loader = MigrationLoader(connections[self.db_alias])
        if (app_label, target_migration) not in loader.graph.nodes:
            # Try partial match
            matches = [
                key for key in loader.graph.nodes
                if key[0] == app_label and target_migration in key[1]
            ]
            if len(matches) == 1:
                target_migration = matches[0][1]
                self.stdout.write(
                    f'  Matched partial name to: {target_migration}'
                )
            elif len(matches) > 1:
                names = ', '.join(m[1] for m in matches)
                raise CommandError(
                    f'Ambiguous migration name "{target_migration}". '
                    f'Matches: {names}'
                )
            else:
                raise CommandError(
                    f'Migration "{target_migration}" not found for app "{app_label}".'
                )

        self.stdout.write(self.style.WARNING(
            f'\n  Rolling back {app_label} to {target_migration}...'
        ))

        if self.dry_run:
            self.stdout.write(self.style.WARNING(
                '  DRY RUN: No rollback was performed.'
            ))
            return

        log_entry = self._create_log_entry(
            app_label=app_label,
            migration_name=target_migration,
            direction='backward',
            is_dangerous=True,
        )

        start_time = time.monotonic()
        try:
            call_command(
                'migrate',
                app_label,
                target_migration,
                database=self.db_alias,
                verbosity=self.verbosity,
                no_input=True,
            )
            elapsed_ms = int((time.monotonic() - start_time) * 1000)
            self._update_log_success(log_entry, elapsed_ms)
            self.stdout.write(self.style.SUCCESS(
                f'  Rollback complete ({elapsed_ms}ms).'
            ))
        except Exception as exc:
            elapsed_ms = int((time.monotonic() - start_time) * 1000)
            self._update_log_failure(log_entry, elapsed_ms, str(exc))
            raise CommandError(f'Rollback failed: {exc}')

    # ─── Dangerous operation detection ────────────────────────────

    def _detect_dangerous_operations(self, plan):
        """
        Inspect migration operations for potentially destructive changes.

        Returns a list of (app_label, name, [operation_descriptions]).
        """
        dangerous = []
        for migration, backward in plan:
            ops = self._get_dangerous_ops(migration)
            if ops:
                dangerous.append((migration.app_label, migration.name, ops))
        return dangerous

    def _get_dangerous_ops(self, migration):
        """Extract dangerous operations from a migration object."""
        dangerous_ops = []
        for operation in migration.operations:
            op_type = type(operation).__name__

            if op_type == 'DeleteModel':
                dangerous_ops.append(
                    f'DELETE MODEL: {operation.name} (table will be dropped)'
                )
            elif op_type == 'RemoveField':
                dangerous_ops.append(
                    f'REMOVE FIELD: {operation.model_name}.{operation.name} '
                    f'(column will be dropped)'
                )
            elif op_type == 'RenameModel':
                dangerous_ops.append(
                    f'RENAME MODEL: {operation.old_name} -> {operation.new_name}'
                )
            elif op_type == 'RenameField':
                dangerous_ops.append(
                    f'RENAME FIELD: {operation.model_name}.'
                    f'{operation.old_name} -> {operation.new_name}'
                )
            elif op_type == 'AlterField':
                dangerous_ops.append(
                    f'ALTER FIELD: {operation.model_name}.{operation.name} '
                    f'(type or constraints may change)'
                )
            elif op_type == 'RunSQL':
                sql_str = str(getattr(operation, 'sql', ''))
                sql_upper = sql_str.upper()
                if any(kw in sql_upper for kw in [
                    'DROP TABLE', 'DROP COLUMN', 'TRUNCATE', 'DELETE FROM',
                    'ALTER TABLE', 'DROP INDEX',
                ]):
                    snippet = sql_str[:120].replace('\n', ' ')
                    dangerous_ops.append(
                        f'RAW SQL: {snippet}...'
                    )
            elif op_type == 'RunPython':
                # Flag RunPython as informational, not blocking
                code_name = getattr(operation.code, '__name__', 'anonymous')
                dangerous_ops.append(
                    f'RUN PYTHON: {code_name} (data migration - review manually)'
                )

        return dangerous_ops

    def _is_migration_dangerous(self, app_label, migration_name):
        """Check if a specific migration contains dangerous operations."""
        loader = MigrationLoader(connections[self.db_alias])
        key = (app_label, migration_name)
        if key in loader.graph.nodes:
            migration = loader.graph.nodes[key]
            return bool(self._get_dangerous_ops(migration))
        return False

    # ─── Advisory locking ─────────────────────────────────────────

    def _acquire_advisory_lock(self):
        """
        Acquire a PostgreSQL advisory lock to prevent concurrent migrations.

        For non-PostgreSQL databases (e.g. SQLite in dev), always returns True.
        """
        db_engine = connections[self.db_alias].vendor
        if db_engine != 'postgresql':
            if self.verbosity >= 2:
                self.stdout.write(
                    f'  Advisory lock skipped (engine: {db_engine}).'
                )
            return True

        with connection.cursor() as cursor:
            cursor.execute(
                'SELECT pg_try_advisory_lock(%s)',
                [ADVISORY_LOCK_ID],
            )
            acquired = cursor.fetchone()[0]

        if acquired:
            if self.verbosity >= 2:
                self.stdout.write('  Advisory lock acquired.')
        else:
            self.stdout.write(self.style.ERROR(
                '  Could not acquire advisory lock.'
            ))
        return acquired

    def _release_advisory_lock(self):
        """Release the PostgreSQL advisory lock."""
        db_engine = connections[self.db_alias].vendor
        if db_engine != 'postgresql':
            return

        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    'SELECT pg_advisory_unlock(%s)',
                    [ADVISORY_LOCK_ID],
                )
            if self.verbosity >= 2:
                self.stdout.write('  Advisory lock released.')
        except Exception:
            # Lock is released when the connection closes anyway
            pass

    # ─── Audit logging ────────────────────────────────────────────

    def _create_log_entry(self, app_label, migration_name, direction, is_dangerous=False):
        """
        Create a MigrationLog entry in PENDING status.

        If the MigrationLog table does not exist yet (e.g. initial deploy),
        returns None and logging is silently skipped.
        """
        try:
            from apps.core.migration_log import MigrationLog

            entry = MigrationLog.objects.create(
                app_name=app_label,
                migration_name=migration_name,
                direction=direction,
                status=MigrationLog.Status.RUNNING,
                applied_by=self.applied_by,
                server_hostname=self.hostname,
                is_dangerous=is_dangerous,
                dry_run=self.dry_run,
            )
            return entry
        except Exception:
            # Table may not exist during initial migration
            return None

    def _update_log_success(self, entry, elapsed_ms):
        """Mark a log entry as successful."""
        if entry is None:
            return
        try:
            entry.status = 'success'
            entry.completed_at = timezone.now()
            entry.duration_ms = elapsed_ms
            entry.save(update_fields=['status', 'completed_at', 'duration_ms'])
        except Exception:
            pass

    def _update_log_failure(self, entry, elapsed_ms, error_message):
        """Mark a log entry as failed."""
        if entry is None:
            return
        try:
            entry.status = 'failed'
            entry.completed_at = timezone.now()
            entry.duration_ms = elapsed_ms
            entry.error_message = str(error_message)[:5000]
            entry.save(update_fields=['status', 'completed_at', 'duration_ms', 'error_message'])
        except Exception:
            pass

    def _log_migrations(self, plan, dry_run=False):
        """Log all planned migrations as dry-run entries."""
        for migration, backward in plan:
            direction = 'backward' if backward else 'forward'
            self._create_log_entry(
                app_label=migration.app_label,
                migration_name=migration.name,
                direction=direction,
                is_dangerous=False,
            )

    # ─── Output helpers ───────────────────────────────────────────

    def _print_header(self):
        self.stdout.write('')
        self.stdout.write('=' * 60)
        self.stdout.write('  E-Menum Safe Migration Runner')
        self.stdout.write(f'  Host: {self.hostname}')
        self.stdout.write(f'  Database: {self.db_alias}')
        self.stdout.write(f'  Time: {timezone.now().isoformat()}')
        if self.dry_run:
            self.stdout.write(self.style.WARNING('  Mode: DRY RUN'))
        elif self.rollback:
            self.stdout.write(self.style.WARNING(
                f'  Mode: ROLLBACK {self.rollback[0]} -> {self.rollback[1]}'
            ))
        else:
            self.stdout.write('  Mode: FORWARD')
        self.stdout.write('=' * 60)

    def _print_summary(self, success, failed, total):
        self.stdout.write('')
        self.stdout.write('=' * 60)
        self.stdout.write(f'  Migration Summary')
        self.stdout.write(f'  Total: {total}  |  Success: {success}  |  Failed: {failed}')
        self.stdout.write('=' * 60)

        if failed == 0:
            self.stdout.write(self.style.SUCCESS(
                '\n  All migrations applied successfully.'
            ))
        else:
            self.stdout.write(self.style.ERROR(
                f'\n  {failed} migration(s) failed. Check logs for details.'
            ))
