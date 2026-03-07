# Migration generated for MigrationLog model
# This table tracks all migration operations performed by the safe_migrate command.

import uuid

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0004_organization_plan_organization_subscription"),
    ]

    operations = [
        migrations.CreateModel(
            name="MigrationLog",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                (
                    "app_name",
                    models.CharField(
                        db_index=True,
                        help_text='Django app label (e.g. "core", "menu").',
                        max_length=100,
                    ),
                ),
                (
                    "migration_name",
                    models.CharField(
                        help_text="Migration file name without .py extension.",
                        max_length=255,
                    ),
                ),
                (
                    "direction",
                    models.CharField(
                        choices=[("forward", "Forward"), ("backward", "Backward")],
                        default="forward",
                        max_length=10,
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("pending", "Pending"),
                            ("running", "Running"),
                            ("success", "Success"),
                            ("failed", "Failed"),
                            ("skipped", "Skipped"),
                        ],
                        default="pending",
                        max_length=20,
                    ),
                ),
                ("started_at", models.DateTimeField(auto_now_add=True)),
                ("completed_at", models.DateTimeField(blank=True, null=True)),
                (
                    "duration_ms",
                    models.IntegerField(
                        blank=True,
                        help_text="Elapsed time in milliseconds.",
                        null=True,
                    ),
                ),
                ("error_message", models.TextField(blank=True, default="")),
                (
                    "applied_by",
                    models.CharField(
                        default="system",
                        help_text="User or process that triggered the migration.",
                        max_length=100,
                    ),
                ),
                (
                    "server_hostname",
                    models.CharField(
                        blank=True,
                        default="",
                        help_text="Hostname of the server that ran the migration.",
                        max_length=255,
                    ),
                ),
                (
                    "is_dangerous",
                    models.BooleanField(
                        default=False,
                        help_text="True if the migration was flagged as potentially dangerous.",
                    ),
                ),
                (
                    "dry_run",
                    models.BooleanField(
                        default=False,
                        help_text="True if this was a dry-run execution (no actual changes).",
                    ),
                ),
            ],
            options={
                "verbose_name": "Migration Log",
                "verbose_name_plural": "Migration Logs",
                "db_table": "core_migration_log",
                "ordering": ["-started_at"],
            },
        ),
        migrations.AddIndex(
            model_name="migrationlog",
            index=models.Index(
                fields=["app_name", "migration_name"],
                name="idx_miglog_app_migration",
            ),
        ),
        migrations.AddIndex(
            model_name="migrationlog",
            index=models.Index(
                fields=["status"],
                name="idx_miglog_status",
            ),
        ),
        migrations.AddIndex(
            model_name="migrationlog",
            index=models.Index(
                fields=["started_at"],
                name="idx_miglog_started",
            ),
        ),
    ]
