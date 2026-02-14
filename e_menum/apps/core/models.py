"""
Django ORM models for the Core application.

This module defines the foundational models for E-Menum:
- Organization: Multi-tenant root entity (tenant anchor)
- User: Custom user model with organization membership (email-based auth)

Additional models to be added:
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

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.core.choices import OrganizationStatus, UserStatus


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


class UserManager(BaseUserManager):
    """
    Custom manager for User model with email-based authentication.

    This manager provides methods for creating regular users and superusers
    using email as the unique identifier instead of username.

    Usage:
        # Create regular user
        user = User.objects.create_user(
            email='user@example.com',
            password='securepassword',
            first_name='John',
            last_name='Doe'
        )

        # Create superuser
        admin = User.objects.create_superuser(
            email='admin@example.com',
            password='adminpassword',
            first_name='Admin',
            last_name='User'
        )
    """

    def create_user(self, email, password=None, **extra_fields):
        """
        Create and save a regular user with the given email and password.

        Args:
            email: User's email address (required, used as username)
            password: User's password (optional, but recommended)
            **extra_fields: Additional fields for the User model

        Returns:
            User: The created user instance

        Raises:
            ValueError: If email is not provided
        """
        if not email:
            raise ValueError(_('The Email field must be set'))
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """
        Create and save a superuser with the given email and password.

        Sets is_staff and is_superuser to True, and status to ACTIVE.

        Args:
            email: Superuser's email address (required)
            password: Superuser's password (optional, but recommended)
            **extra_fields: Additional fields for the User model

        Returns:
            User: The created superuser instance

        Raises:
            ValueError: If is_staff or is_superuser is not True
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('status', UserStatus.ACTIVE)

        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Superuser must have is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superuser must have is_superuser=True.'))

        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin, TimeStampedMixin, SoftDeleteMixin):
    """
    Custom User model with email-based authentication and optional organization membership.

    This model replaces Django's default User model to support:
    - Email as the primary identifier (instead of username)
    - Optional organization membership for multi-tenant architecture
    - Soft delete functionality
    - Integration with Django admin and django-guardian

    Critical Rules:
    - Use email for authentication (USERNAME_FIELD = 'email')
    - Organization membership is optional (system users may not belong to any org)
    - Use soft_delete() - never call delete() directly

    Attributes:
        id: UUID primary key (ensures global uniqueness)
        email: Unique email address (used as username)
        first_name: User's first name
        last_name: User's last name
        avatar: Optional URL to user's avatar image
        phone: Optional contact phone number
        status: User lifecycle status (ACTIVE, INVITED, SUSPENDED)
        is_staff: Required for Django admin access
        is_superuser: Required for full system access (from PermissionsMixin)
        email_verified_at: When email was verified (null if not verified)
        last_login_at: Timestamp of last successful login
        organization: Optional FK to Organization for tenant membership

    Usage:
        # Create a user
        user = User.objects.create_user(
            email='user@example.com',
            password='securepassword',
            first_name='John',
            last_name='Doe',
            organization=org
        )

        # Check if user is active
        if user.is_active_user:
            # Allow access

        # Soft delete user (NEVER use delete())
        user.soft_delete()
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name=_('ID'),
        help_text=_('Unique identifier (UUID)')
    )

    email = models.EmailField(
        unique=True,
        verbose_name=_('Email'),
        help_text=_('Email address (used as username for authentication)')
    )

    first_name = models.CharField(
        max_length=100,
        verbose_name=_('First name'),
        help_text=_("User's first name")
    )

    last_name = models.CharField(
        max_length=100,
        verbose_name=_('Last name'),
        help_text=_("User's last name")
    )

    avatar = models.URLField(
        blank=True,
        null=True,
        max_length=500,
        verbose_name=_('Avatar URL'),
        help_text=_("URL to user's avatar image")
    )

    phone = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name=_('Phone'),
        help_text=_('Contact phone number')
    )

    status = models.CharField(
        max_length=20,
        choices=UserStatus.choices,
        default=UserStatus.ACTIVE,
        db_index=True,
        verbose_name=_('Status'),
        help_text=_('User account status')
    )

    is_staff = models.BooleanField(
        default=False,
        verbose_name=_('Staff status'),
        help_text=_('Designates whether the user can log into Django admin.')
    )

    email_verified_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Email verified at'),
        help_text=_('Timestamp when email was verified (null if not verified)')
    )

    last_login_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Last login at'),
        help_text=_('Timestamp of last successful login')
    )

    # Organization membership - optional for system/platform users
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='users',
        verbose_name=_('Organization'),
        help_text=_('Organization this user belongs to (null for platform users)')
    )

    # Use custom manager
    objects = UserManager()

    # Required for AbstractBaseUser
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    class Meta:
        db_table = 'users'
        verbose_name = _('User')
        verbose_name_plural = _('Users')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['organization', 'status'], name='user_org_status_idx'),
            models.Index(fields=['organization', 'deleted_at'], name='user_org_deleted_idx'),
            models.Index(fields=['email'], name='user_email_idx'),
        ]

    def __str__(self) -> str:
        return self.email

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email='{self.email}', status={self.status})>"

    @property
    def full_name(self) -> str:
        """Return the user's full name."""
        return f'{self.first_name} {self.last_name}'.strip()

    @property
    def is_active_user(self) -> bool:
        """Check if user is active and not deleted."""
        return self.status == UserStatus.ACTIVE and not self.is_deleted

    @property
    def is_email_verified(self) -> bool:
        """Check if user's email has been verified."""
        return self.email_verified_at is not None

    def get_full_name(self) -> str:
        """
        Return the first_name plus the last_name, with a space in between.

        Required by Django's AbstractBaseUser interface.
        """
        return self.full_name

    def get_short_name(self) -> str:
        """
        Return the short name for the user.

        Required by Django's AbstractBaseUser interface.
        """
        return self.first_name

    def verify_email(self) -> None:
        """Mark the user's email as verified."""
        self.email_verified_at = timezone.now()
        self.save(update_fields=['email_verified_at', 'updated_at'])

    def record_login(self) -> None:
        """Record the timestamp of a successful login."""
        self.last_login_at = timezone.now()
        self.save(update_fields=['last_login_at', 'updated_at'])

    def suspend(self, reason: str = None) -> None:
        """
        Suspend the user account.

        Args:
            reason: Optional reason for suspension
        """
        self.status = UserStatus.SUSPENDED
        self.save(update_fields=['status', 'updated_at'])

    def activate(self) -> None:
        """Activate a suspended or invited user account."""
        self.status = UserStatus.ACTIVE
        self.save(update_fields=['status', 'updated_at'])
