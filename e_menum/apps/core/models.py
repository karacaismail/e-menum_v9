"""
Django ORM models for the Core application.

This module defines the foundational models for E-Menum:
- Organization: Multi-tenant root entity (tenant anchor)

Additional models to be added:
- User: Custom user model with organization membership
- Role: RBAC role definitions
- Permission: Granular resource.action permissions
- Session: JWT refresh token management
- Branch: Multi-location support
- AuditLog: System-wide audit logging

Critical Rules:
- Every query MUST include organization_id for tenant isolation
- All entities use soft delete (deleted_at timestamp)
- No physical deletions allowed (use soft_delete method)
"""

import uuid

from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.core.choices import OrganizationStatus


class SoftDeleteManager(models.Manager):
    """
    Custom manager that filters out soft-deleted records by default.

    Usage:
        Menu.objects.all()  # Returns only non-deleted menus
        Menu.all_objects.all()  # Returns ALL menus including deleted
    """

    def get_queryset(self):
        """Return only non-deleted records."""
        return super().get_queryset().filter(deleted_at__isnull=True)


class SoftDeleteMixin(models.Model):
    """
    Mixin providing soft delete functionality.

    Adds:
    - deleted_at: Timestamp when record was soft-deleted
    - soft_delete(): Method to mark record as deleted
    - restore(): Method to restore a soft-deleted record
    - is_deleted: Property to check deletion status
    """

    deleted_at = models.DateTimeField(
        null=True,
        blank=True,
        db_index=True,
        verbose_name=_('Deleted at'),
        help_text=_('Timestamp when record was soft-deleted (null = active)')
    )

    class Meta:
        abstract = True

    def soft_delete(self):
        """
        Mark this record as deleted.

        Sets deleted_at to current timestamp. Does NOT physically delete.
        This is the ONLY way records should be "deleted" in E-Menum.
        """
        self.deleted_at = timezone.now()
        self.save(update_fields=['deleted_at'])

    def restore(self):
        """
        Restore a soft-deleted record.

        Clears the deleted_at timestamp, making the record active again.
        """
        self.deleted_at = None
        self.save(update_fields=['deleted_at'])

    @property
    def is_deleted(self) -> bool:
        """Check if this record has been soft-deleted."""
        return self.deleted_at is not None


class TimeStampedMixin(models.Model):
    """
    Mixin providing created_at and updated_at timestamps.

    - created_at: Automatically set on creation
    - updated_at: Automatically updated on each save
    """

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Created at'),
        help_text=_('Timestamp when record was created')
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_('Updated at'),
        help_text=_('Timestamp when record was last updated')
    )

    class Meta:
        abstract = True


class Organization(TimeStampedMixin, SoftDeleteMixin, models.Model):
    """
    Organization model - the tenant root for multi-tenancy.

    This is the anchor entity for E-Menum's multi-tenant architecture.
    All business data (menus, products, orders, etc.) belongs to an Organization.

    Critical Rules:
    - EVERY query on tenant-scoped data MUST filter by organization_id
    - Never expose data from one organization to another
    - Use soft_delete() - never call delete() directly

    Attributes:
        id: UUID primary key (ensures global uniqueness)
        name: Display name of the organization
        slug: URL-friendly unique identifier
        email: Primary contact email
        phone: Optional contact phone
        logo: Optional logo URL
        settings: JSON field for flexible configuration
        status: Organization lifecycle status (ACTIVE, SUSPENDED, DELETED)
        plan: Optional foreign key to subscription Plan
        trial_ends_at: When the trial period ends (null if not on trial)

    Usage:
        # Create organization
        org = Organization.objects.create(
            name="Cafe Istanbul",
            slug="cafe-istanbul",
            email="info@cafeistanbul.com",
            settings={"theme": "dark", "currency": "TRY"}
        )

        # Query with tenant filtering (ALWAYS required!)
        menus = Menu.objects.filter(organization=org)

        # Soft delete (NEVER use delete())
        org.soft_delete()
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name=_('ID'),
        help_text=_('Unique identifier (UUID)')
    )

    name = models.CharField(
        max_length=255,
        verbose_name=_('Name'),
        help_text=_('Display name of the organization')
    )

    slug = models.SlugField(
        unique=True,
        max_length=100,
        verbose_name=_('Slug'),
        help_text=_('URL-friendly unique identifier')
    )

    email = models.EmailField(
        verbose_name=_('Email'),
        help_text=_('Primary contact email for the organization')
    )

    phone = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name=_('Phone'),
        help_text=_('Contact phone number')
    )

    logo = models.URLField(
        blank=True,
        null=True,
        max_length=500,
        verbose_name=_('Logo URL'),
        help_text=_('URL to organization logo image')
    )

    settings = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_('Settings'),
        help_text=_('Organization-specific settings (JSON)')
    )

    status = models.CharField(
        max_length=20,
        choices=OrganizationStatus.choices,
        default=OrganizationStatus.ACTIVE,
        db_index=True,
        verbose_name=_('Status'),
        help_text=_('Organization lifecycle status')
    )

    # Foreign key to Plan - will be linked when subscriptions app is created
    # Using string reference to avoid circular imports
    plan = models.ForeignKey(
        'subscriptions.Plan',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='organizations',
        verbose_name=_('Plan'),
        help_text=_('Current subscription plan')
    )

    trial_ends_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Trial ends at'),
        help_text=_('When trial period ends (null if not on trial)')
    )

    # Managers
    objects = SoftDeleteManager()  # Default: excludes soft-deleted
    all_objects = models.Manager()  # Includes ALL records

    class Meta:
        db_table = 'organizations'
        verbose_name = _('Organization')
        verbose_name_plural = _('Organizations')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'deleted_at'], name='org_status_deleted_idx'),
            models.Index(fields=['slug'], name='org_slug_idx'),
        ]

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return f"<Organization(id={self.id}, name='{self.name}', status={self.status})>"

    @property
    def is_active(self) -> bool:
        """Check if organization is active and not deleted."""
        return self.status == OrganizationStatus.ACTIVE and not self.is_deleted

    @property
    def is_on_trial(self) -> bool:
        """Check if organization is currently on trial."""
        if self.trial_ends_at is None:
            return False
        return timezone.now() < self.trial_ends_at

    def get_setting(self, key: str, default=None):
        """
        Get a value from organization settings.

        Args:
            key: The setting key to retrieve
            default: Default value if key not found

        Returns:
            The setting value or default
        """
        return self.settings.get(key, default)

    def set_setting(self, key: str, value) -> None:
        """
        Set a value in organization settings.

        Args:
            key: The setting key
            value: The value to set
        """
        self.settings[key] = value
        self.save(update_fields=['settings', 'updated_at'])

    def suspend(self, reason: str = None) -> None:
        """
        Suspend the organization.

        Args:
            reason: Optional reason for suspension (stored in settings)
        """
        self.status = OrganizationStatus.SUSPENDED
        if reason:
            self.settings['suspension_reason'] = reason
            self.settings['suspended_at'] = timezone.now().isoformat()
        self.save(update_fields=['status', 'settings', 'updated_at'])

    def activate(self) -> None:
        """Reactivate a suspended organization."""
        self.status = OrganizationStatus.ACTIVE
        self.settings.pop('suspension_reason', None)
        self.settings.pop('suspended_at', None)
        self.save(update_fields=['status', 'settings', 'updated_at'])
