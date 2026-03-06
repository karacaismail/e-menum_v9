"""
MigrationLog model for tracking database migration operations.

This model records every migration applied by the safe_migrate command,
providing a complete audit trail of database schema changes in production.
It is intentionally kept in a separate file from core/models.py to avoid
circular imports and to clearly delineate infrastructure-level concerns.

Usage:
    - Automatically populated by the `safe_migrate` management command.
    - Queryable via Django admin or shell for migration history auditing.
    - Each record captures timing, status, direction, and error details.
"""

import socket
import uuid

from django.db import models
from django.utils import timezone


class MigrationLog(models.Model):
    """
    Audit log for database migration operations.

    Every migration applied through the safe_migrate command is recorded here
    with its status, timing, and any errors encountered. This provides an
    immutable history of schema changes for production debugging and compliance.
    """

    class Direction(models.TextChoices):
        FORWARD = 'forward', 'Forward'
        BACKWARD = 'backward', 'Backward'

    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        RUNNING = 'running', 'Running'
        SUCCESS = 'success', 'Success'
        FAILED = 'failed', 'Failed'
        SKIPPED = 'skipped', 'Skipped'

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    app_name = models.CharField(
        max_length=100,
        db_index=True,
        help_text='Django app label (e.g. "core", "menu").',
    )
    migration_name = models.CharField(
        max_length=255,
        help_text='Migration file name without .py extension.',
    )
    direction = models.CharField(
        max_length=10,
        choices=Direction.choices,
        default=Direction.FORWARD,
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    started_at = models.DateTimeField(
        auto_now_add=True,
    )
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
    )
    duration_ms = models.IntegerField(
        null=True,
        blank=True,
        help_text='Elapsed time in milliseconds.',
    )
    error_message = models.TextField(
        blank=True,
        default='',
    )
    applied_by = models.CharField(
        max_length=100,
        default='system',
        help_text='User or process that triggered the migration.',
    )
    server_hostname = models.CharField(
        max_length=255,
        blank=True,
        default='',
        help_text='Hostname of the server that ran the migration.',
    )
    is_dangerous = models.BooleanField(
        default=False,
        help_text='True if the migration was flagged as potentially dangerous.',
    )
    dry_run = models.BooleanField(
        default=False,
        help_text='True if this was a dry-run execution (no actual changes).',
    )

    class Meta:
        db_table = 'core_migration_log'
        ordering = ['-started_at']
        verbose_name = 'Migration Log'
        verbose_name_plural = 'Migration Logs'
        indexes = [
            models.Index(fields=['app_name', 'migration_name'], name='idx_miglog_app_migration'),
            models.Index(fields=['status'], name='idx_miglog_status'),
            models.Index(fields=['started_at'], name='idx_miglog_started'),
        ]

    def __str__(self):
        return f'{self.app_name}.{self.migration_name} [{self.status}]'

    def save(self, *args, **kwargs):
        if not self.server_hostname:
            self.server_hostname = socket.gethostname()
        super().save(*args, **kwargs)

    def mark_running(self):
        """Transition this log entry to running status."""
        self.status = self.Status.RUNNING
        self.save(update_fields=['status'])

    def mark_success(self):
        """Transition this log entry to success status with timing."""
        now = timezone.now()
        self.status = self.Status.SUCCESS
        self.completed_at = now
        if self.started_at:
            self.duration_ms = int((now - self.started_at).total_seconds() * 1000)
        self.save(update_fields=['status', 'completed_at', 'duration_ms'])

    def mark_failed(self, error_message: str):
        """Transition this log entry to failed status with error details."""
        now = timezone.now()
        self.status = self.Status.FAILED
        self.completed_at = now
        self.error_message = str(error_message)[:5000]  # Truncate very long errors
        if self.started_at:
            self.duration_ms = int((now - self.started_at).total_seconds() * 1000)
        self.save(update_fields=['status', 'completed_at', 'duration_ms', 'error_message'])
