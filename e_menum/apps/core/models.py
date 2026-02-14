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

from apps.core.choices import (
    AuditAction,
    BranchStatus,
    OrganizationStatus,
    PermissionAction,
    RoleScope,
    SessionStatus,
    UserStatus,
)


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

    # TODO: Add plan FK when subscriptions app is created (subtask-6-*)
    # This FK will be added in migration 0002_add_organization_plan.py
    # after subscriptions.Plan model exists
    #
    # plan = models.ForeignKey(
    #     'subscriptions.Plan',
    #     on_delete=models.SET_NULL,
    #     null=True,
    #     blank=True,
    #     related_name='organizations',
    #     verbose_name=_('Plan'),
    #     help_text=_('Current subscription plan')
    # )

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


class Branch(TimeStampedMixin, SoftDeleteMixin, models.Model):
    """
    Branch model - represents physical locations within an organization.

    Supports multi-location businesses with hierarchical structure.
    Each branch can have its own settings, operating hours, and staff.

    Attributes:
        id: UUID primary key
        organization: FK to parent Organization (tenant isolation)
        name: Display name of the branch
        slug: URL-friendly identifier (unique within organization)
        address: Full street address
        city: City name
        district: District/neighborhood
        postal_code: Postal/ZIP code
        country: Country code (default: TR)
        phone: Branch contact phone
        email: Branch contact email
        latitude: GPS latitude for mapping
        longitude: GPS longitude for mapping
        timezone: Branch timezone (default: Europe/Istanbul)
        settings: JSON field for branch-specific configuration
        operating_hours: JSON field for daily operating hours
        status: Branch lifecycle status (ACTIVE, INACTIVE, SUSPENDED)
        is_main: Whether this is the main/headquarters branch

    Usage:
        # Create a branch
        branch = Branch.objects.create(
            organization=org,
            name="Kadıköy Şubesi",
            slug="kadikoy",
            address="Caferağa Mah. Moda Cad. No:42",
            city="Istanbul",
            district="Kadıköy"
        )

        # Query branches for organization (ALWAYS filter by organization!)
        branches = Branch.objects.filter(organization=org)
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name=_('ID'),
        help_text=_('Unique identifier (UUID)')
    )

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='branches',
        verbose_name=_('Organization'),
        help_text=_('Organization this branch belongs to')
    )

    name = models.CharField(
        max_length=255,
        verbose_name=_('Name'),
        help_text=_('Display name of the branch')
    )

    slug = models.SlugField(
        max_length=100,
        verbose_name=_('Slug'),
        help_text=_('URL-friendly identifier (unique within organization)')
    )

    address = models.TextField(
        blank=True,
        null=True,
        verbose_name=_('Address'),
        help_text=_('Full street address')
    )

    city = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name=_('City'),
        help_text=_('City name')
    )

    district = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name=_('District'),
        help_text=_('District or neighborhood')
    )

    postal_code = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name=_('Postal code'),
        help_text=_('Postal or ZIP code')
    )

    country = models.CharField(
        max_length=2,
        default='TR',
        verbose_name=_('Country'),
        help_text=_('Country code (ISO 3166-1 alpha-2)')
    )

    phone = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name=_('Phone'),
        help_text=_('Branch contact phone number')
    )

    email = models.EmailField(
        blank=True,
        null=True,
        verbose_name=_('Email'),
        help_text=_('Branch contact email')
    )

    latitude = models.DecimalField(
        max_digits=10,
        decimal_places=7,
        blank=True,
        null=True,
        verbose_name=_('Latitude'),
        help_text=_('GPS latitude coordinate')
    )

    longitude = models.DecimalField(
        max_digits=10,
        decimal_places=7,
        blank=True,
        null=True,
        verbose_name=_('Longitude'),
        help_text=_('GPS longitude coordinate')
    )

    timezone = models.CharField(
        max_length=50,
        default='Europe/Istanbul',
        verbose_name=_('Timezone'),
        help_text=_('Branch timezone (IANA format)')
    )

    settings = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_('Settings'),
        help_text=_('Branch-specific settings (JSON)')
    )

    operating_hours = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_('Operating hours'),
        help_text=_('Daily operating hours (JSON)')
    )

    status = models.CharField(
        max_length=20,
        choices=BranchStatus.choices,
        default=BranchStatus.ACTIVE,
        db_index=True,
        verbose_name=_('Status'),
        help_text=_('Branch lifecycle status')
    )

    is_main = models.BooleanField(
        default=False,
        verbose_name=_('Is main branch'),
        help_text=_('Whether this is the main/headquarters branch')
    )

    # Managers
    objects = SoftDeleteManager()  # Default: excludes soft-deleted
    all_objects = models.Manager()  # Includes ALL records

    class Meta:
        db_table = 'branches'
        verbose_name = _('Branch')
        verbose_name_plural = _('Branches')
        ordering = ['-is_main', 'name']
        unique_together = [['organization', 'slug']]
        indexes = [
            models.Index(fields=['organization', 'status'], name='branch_org_status_idx'),
            models.Index(fields=['organization', 'deleted_at'], name='branch_org_deleted_idx'),
        ]

    def __str__(self) -> str:
        return f"{self.name} ({self.organization.name})"

    def __repr__(self) -> str:
        return f"<Branch(id={self.id}, name='{self.name}', org='{self.organization.name}')>"

    @property
    def is_active(self) -> bool:
        """Check if branch is active and not deleted."""
        return self.status == BranchStatus.ACTIVE and not self.is_deleted

    @property
    def full_address(self) -> str:
        """Return the full formatted address."""
        parts = [self.address, self.district, self.city, self.postal_code, self.country]
        return ', '.join(p for p in parts if p)

    def get_setting(self, key: str, default=None):
        """Get a value from branch settings."""
        return self.settings.get(key, default)

    def set_setting(self, key: str, value) -> None:
        """Set a value in branch settings."""
        self.settings[key] = value
        self.save(update_fields=['settings', 'updated_at'])


class Role(TimeStampedMixin, models.Model):
    """
    Role model - defines RBAC roles for the system.

    Roles can be either platform-scoped (super_admin, admin, sales, support)
    or organization-scoped (owner, manager, staff, viewer).

    System roles (is_system=True) are predefined and cannot be modified.
    Custom roles can be created per organization.

    Attributes:
        id: UUID primary key
        name: Internal role identifier (e.g., 'owner', 'manager')
        display_name: Human-readable name (e.g., 'Organization Owner')
        description: Detailed description of the role
        scope: PLATFORM or ORGANIZATION scope
        is_system: Whether this is a predefined system role
        organization: FK to Organization (null for platform roles)
        permissions: M2M relationship to Permission via RolePermission

    Usage:
        # Get all organization-scoped roles
        org_roles = Role.objects.filter(scope=RoleScope.ORGANIZATION)

        # Create custom role for organization
        role = Role.objects.create(
            name='inventory_manager',
            display_name='Inventory Manager',
            description='Can manage inventory and stock levels',
            scope=RoleScope.ORGANIZATION,
            organization=org
        )
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name=_('ID'),
        help_text=_('Unique identifier (UUID)')
    )

    name = models.CharField(
        max_length=50,
        verbose_name=_('Name'),
        help_text=_('Internal role identifier (lowercase, underscore-separated)')
    )

    display_name = models.CharField(
        max_length=100,
        verbose_name=_('Display name'),
        help_text=_('Human-readable role name')
    )

    description = models.TextField(
        blank=True,
        null=True,
        verbose_name=_('Description'),
        help_text=_('Detailed description of the role and its capabilities')
    )

    scope = models.CharField(
        max_length=20,
        choices=RoleScope.choices,
        default=RoleScope.ORGANIZATION,
        db_index=True,
        verbose_name=_('Scope'),
        help_text=_('Role scope (PLATFORM or ORGANIZATION)')
    )

    is_system = models.BooleanField(
        default=False,
        verbose_name=_('Is system role'),
        help_text=_('System roles are predefined and cannot be modified')
    )

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='roles',
        verbose_name=_('Organization'),
        help_text=_('Organization for org-scoped roles (null for platform roles)')
    )

    permissions = models.ManyToManyField(
        'Permission',
        through='RolePermission',
        related_name='roles',
        verbose_name=_('Permissions'),
        help_text=_('Permissions granted to this role')
    )

    class Meta:
        db_table = 'roles'
        verbose_name = _('Role')
        verbose_name_plural = _('Roles')
        ordering = ['scope', 'name']
        unique_together = [['name', 'scope', 'organization']]
        indexes = [
            models.Index(fields=['scope'], name='role_scope_idx'),
            models.Index(fields=['organization', 'scope'], name='role_org_scope_idx'),
        ]

    def __str__(self) -> str:
        if self.organization:
            return f"{self.display_name} ({self.organization.name})"
        return f"{self.display_name} (Platform)"

    def __repr__(self) -> str:
        return f"<Role(id={self.id}, name='{self.name}', scope={self.scope})>"

    @property
    def is_platform_role(self) -> bool:
        """Check if this is a platform-scoped role."""
        return self.scope == RoleScope.PLATFORM

    @property
    def is_organization_role(self) -> bool:
        """Check if this is an organization-scoped role."""
        return self.scope == RoleScope.ORGANIZATION


class Permission(TimeStampedMixin, models.Model):
    """
    Permission model - defines granular resource.action permissions.

    Permissions follow the resource.action pattern (e.g., 'menu.create', 'order.view').
    They are used with CASL-like permission checking for fine-grained access control.

    Attributes:
        id: UUID primary key
        resource: Resource name (e.g., 'menu', 'order', 'user')
        action: Action type (e.g., 'view', 'create', 'update', 'delete')
        description: Human-readable description of the permission
        is_system: Whether this is a predefined system permission

    Usage:
        # Create a permission
        perm = Permission.objects.create(
            resource='menu',
            action=PermissionAction.CREATE,
            description='Create new menus'
        )

        # Check if role has permission
        has_perm = role.permissions.filter(resource='menu', action='create').exists()
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name=_('ID'),
        help_text=_('Unique identifier (UUID)')
    )

    resource = models.CharField(
        max_length=50,
        verbose_name=_('Resource'),
        help_text=_('Resource name (e.g., menu, order, user)')
    )

    action = models.CharField(
        max_length=20,
        choices=PermissionAction.choices,
        verbose_name=_('Action'),
        help_text=_('Action type (view, create, update, delete, etc.)')
    )

    description = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name=_('Description'),
        help_text=_('Human-readable description of the permission')
    )

    is_system = models.BooleanField(
        default=False,
        verbose_name=_('Is system permission'),
        help_text=_('System permissions are predefined and cannot be deleted')
    )

    class Meta:
        db_table = 'permissions'
        verbose_name = _('Permission')
        verbose_name_plural = _('Permissions')
        ordering = ['resource', 'action']
        unique_together = [['resource', 'action']]
        indexes = [
            models.Index(fields=['resource'], name='permission_resource_idx'),
            models.Index(fields=['resource', 'action'], name='permission_res_action_idx'),
        ]

    def __str__(self) -> str:
        return f"{self.resource}.{self.action}"

    def __repr__(self) -> str:
        return f"<Permission(id={self.id}, resource='{self.resource}', action='{self.action}')>"

    @property
    def code(self) -> str:
        """Return the permission code (resource.action format)."""
        return f"{self.resource}.{self.action}"


class Session(TimeStampedMixin, models.Model):
    """
    Session model - manages JWT refresh tokens for user sessions.

    Each session represents an active login with a refresh token.
    Sessions can be revoked for security (logout, password change).

    Attributes:
        id: UUID primary key
        user: FK to User who owns this session
        refresh_token: Hashed refresh token
        user_agent: Browser/client user agent string
        ip_address: Client IP address
        expires_at: When the session expires
        status: Session status (ACTIVE, EXPIRED, REVOKED)
        revoked_at: When the session was revoked (if applicable)
        revoke_reason: Reason for revocation

    Usage:
        # Create a session
        session = Session.objects.create(
            user=user,
            refresh_token=hashed_token,
            user_agent=request.META.get('HTTP_USER_AGENT'),
            ip_address=get_client_ip(request),
            expires_at=timezone.now() + timedelta(days=7)
        )

        # Revoke a session (logout)
        session.revoke(reason='User logged out')

        # Revoke all sessions for a user (security)
        Session.objects.filter(user=user, status='ACTIVE').update(
            status='REVOKED',
            revoked_at=timezone.now()
        )
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name=_('ID'),
        help_text=_('Unique identifier (UUID)')
    )

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='sessions',
        verbose_name=_('User'),
        help_text=_('User who owns this session')
    )

    refresh_token = models.CharField(
        max_length=500,
        verbose_name=_('Refresh token'),
        help_text=_('Hashed refresh token')
    )

    user_agent = models.TextField(
        blank=True,
        null=True,
        verbose_name=_('User agent'),
        help_text=_('Browser/client user agent string')
    )

    ip_address = models.GenericIPAddressField(
        blank=True,
        null=True,
        verbose_name=_('IP address'),
        help_text=_('Client IP address')
    )

    expires_at = models.DateTimeField(
        verbose_name=_('Expires at'),
        help_text=_('When the session/refresh token expires')
    )

    status = models.CharField(
        max_length=20,
        choices=SessionStatus.choices,
        default=SessionStatus.ACTIVE,
        db_index=True,
        verbose_name=_('Status'),
        help_text=_('Session status')
    )

    revoked_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Revoked at'),
        help_text=_('When the session was revoked')
    )

    revoke_reason = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name=_('Revoke reason'),
        help_text=_('Reason for session revocation')
    )

    class Meta:
        db_table = 'sessions'
        verbose_name = _('Session')
        verbose_name_plural = _('Sessions')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status'], name='session_user_status_idx'),
            models.Index(fields=['refresh_token'], name='session_token_idx'),
            models.Index(fields=['expires_at'], name='session_expires_idx'),
        ]

    def __str__(self) -> str:
        return f"Session for {self.user.email} ({self.status})"

    def __repr__(self) -> str:
        return f"<Session(id={self.id}, user='{self.user.email}', status={self.status})>"

    @property
    def is_active(self) -> bool:
        """Check if session is active and not expired."""
        if self.status != SessionStatus.ACTIVE:
            return False
        return timezone.now() < self.expires_at

    @property
    def is_expired(self) -> bool:
        """Check if session has expired."""
        return timezone.now() >= self.expires_at

    def revoke(self, reason: str = None) -> None:
        """
        Revoke this session.

        Args:
            reason: Optional reason for revocation
        """
        self.status = SessionStatus.REVOKED
        self.revoked_at = timezone.now()
        if reason:
            self.revoke_reason = reason
        self.save(update_fields=['status', 'revoked_at', 'revoke_reason', 'updated_at'])

    def mark_expired(self) -> None:
        """Mark this session as expired."""
        self.status = SessionStatus.EXPIRED
        self.save(update_fields=['status', 'updated_at'])


class UserRole(TimeStampedMixin, models.Model):
    """
    UserRole model - junction table linking users to roles.

    This enables many-to-many relationships between users and roles,
    with optional organization and branch scoping.

    Attributes:
        id: UUID primary key
        user: FK to User
        role: FK to Role
        organization: FK to Organization (for org-scoped role assignments)
        branch: FK to Branch (for branch-level role restrictions)
        granted_by: FK to User who granted this role
        expires_at: Optional expiration for temporary role assignments

    Usage:
        # Assign a role to a user
        user_role = UserRole.objects.create(
            user=user,
            role=manager_role,
            organization=org,
            granted_by=admin_user
        )

        # Get all roles for a user in an organization
        user_roles = UserRole.objects.filter(
            user=user,
            organization=org
        ).select_related('role')
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name=_('ID'),
        help_text=_('Unique identifier (UUID)')
    )

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='user_roles',
        verbose_name=_('User'),
        help_text=_('User who has this role')
    )

    role = models.ForeignKey(
        Role,
        on_delete=models.CASCADE,
        related_name='user_roles',
        verbose_name=_('Role'),
        help_text=_('Role assigned to the user')
    )

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='user_roles',
        verbose_name=_('Organization'),
        help_text=_('Organization scope for this role assignment')
    )

    branch = models.ForeignKey(
        Branch,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='user_roles',
        verbose_name=_('Branch'),
        help_text=_('Optional branch-level restriction')
    )

    granted_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='granted_roles',
        verbose_name=_('Granted by'),
        help_text=_('User who granted this role')
    )

    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Expires at'),
        help_text=_('Optional expiration for temporary role assignments')
    )

    class Meta:
        db_table = 'user_roles'
        verbose_name = _('User Role')
        verbose_name_plural = _('User Roles')
        ordering = ['-created_at']
        unique_together = [['user', 'role', 'organization', 'branch']]
        indexes = [
            models.Index(fields=['user', 'organization'], name='userrole_user_org_idx'),
            models.Index(fields=['organization', 'role'], name='userrole_org_role_idx'),
        ]

    def __str__(self) -> str:
        scope = f" @ {self.organization.name}" if self.organization else " (Platform)"
        return f"{self.user.email} - {self.role.display_name}{scope}"

    def __repr__(self) -> str:
        return f"<UserRole(user='{self.user.email}', role='{self.role.name}')>"

    @property
    def is_active(self) -> bool:
        """Check if this role assignment is currently active."""
        if self.expires_at is None:
            return True
        return timezone.now() < self.expires_at

    @property
    def is_expired(self) -> bool:
        """Check if this role assignment has expired."""
        if self.expires_at is None:
            return False
        return timezone.now() >= self.expires_at


class RolePermission(TimeStampedMixin, models.Model):
    """
    RolePermission model - junction table linking roles to permissions.

    This enables many-to-many relationships between roles and permissions,
    with optional conditions for fine-grained access control.

    Attributes:
        id: UUID primary key
        role: FK to Role
        permission: FK to Permission
        conditions: JSON field for CASL-like conditional permissions

    Usage:
        # Grant a permission to a role
        role_perm = RolePermission.objects.create(
            role=manager_role,
            permission=menu_create_perm,
            conditions={'organization_id': '${user.organization_id}'}
        )

        # Get all permissions for a role
        perms = RolePermission.objects.filter(role=role).select_related('permission')
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name=_('ID'),
        help_text=_('Unique identifier (UUID)')
    )

    role = models.ForeignKey(
        Role,
        on_delete=models.CASCADE,
        related_name='role_permissions',
        verbose_name=_('Role'),
        help_text=_('Role that has this permission')
    )

    permission = models.ForeignKey(
        Permission,
        on_delete=models.CASCADE,
        related_name='role_permissions',
        verbose_name=_('Permission'),
        help_text=_('Permission granted to the role')
    )

    conditions = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_('Conditions'),
        help_text=_('CASL-like conditions for fine-grained access control')
    )

    class Meta:
        db_table = 'role_permissions'
        verbose_name = _('Role Permission')
        verbose_name_plural = _('Role Permissions')
        ordering = ['role', 'permission']
        unique_together = [['role', 'permission']]
        indexes = [
            models.Index(fields=['role'], name='roleperm_role_idx'),
            models.Index(fields=['permission'], name='roleperm_perm_idx'),
        ]

    def __str__(self) -> str:
        return f"{self.role.name} -> {self.permission.code}"

    def __repr__(self) -> str:
        return f"<RolePermission(role='{self.role.name}', perm='{self.permission.code}')>"


class AuditLog(models.Model):
    """
    AuditLog model - system-wide audit logging for compliance and security.

    Captures all significant actions performed in the system, including who
    performed the action, what was changed, and when it happened.

    This is used for:
    - Security analysis and threat detection
    - Compliance reporting (KVKK/GDPR)
    - Debugging and troubleshooting
    - User activity tracking

    Attributes:
        id: UUID primary key
        organization: Optional FK to Organization (for tenant-scoped audits)
        user: FK to User who performed the action (null for system actions)
        action: Type of action performed (CREATE, UPDATE, DELETE, etc.)
        resource: Resource type affected (e.g., 'menu', 'order', 'user')
        resource_id: ID of the affected resource
        description: Human-readable description of the action
        old_values: JSON snapshot of values before the change
        new_values: JSON snapshot of values after the change
        ip_address: Client IP address
        user_agent: Client user agent string
        metadata: Additional context data (JSON)
        created_at: Timestamp when the action occurred

    Usage:
        # Log a create action
        AuditLog.objects.create(
            organization=org,
            user=request.user,
            action=AuditAction.CREATE,
            resource='menu',
            resource_id=str(menu.id),
            description='Created menu "Akşam Menüsü"',
            new_values={'name': 'Akşam Menüsü', 'is_published': False},
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT')
        )

        # Log an update action
        AuditLog.objects.create(
            organization=org,
            user=request.user,
            action=AuditAction.UPDATE,
            resource='product',
            resource_id=str(product.id),
            description='Updated product price',
            old_values={'price': '25.00'},
            new_values={'price': '30.00'},
            ip_address=get_client_ip(request)
        )

        # Query audit logs for an organization
        logs = AuditLog.objects.filter(
            organization=org,
            created_at__gte=start_date
        ).order_by('-created_at')

    Notes:
        - AuditLog records are NEVER deleted (no soft delete)
        - Retention policy: 2 years, then archive to cold storage
        - This model does NOT use SoftDeleteMixin intentionally
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name=_('ID'),
        help_text=_('Unique identifier (UUID)')
    )

    organization = models.ForeignKey(
        Organization,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_logs',
        verbose_name=_('Organization'),
        help_text=_('Organization context for this audit log (null for platform-level actions)')
    )

    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_logs',
        verbose_name=_('User'),
        help_text=_('User who performed the action (null for system actions)')
    )

    action = models.CharField(
        max_length=30,
        choices=AuditAction.choices,
        db_index=True,
        verbose_name=_('Action'),
        help_text=_('Type of action performed')
    )

    resource = models.CharField(
        max_length=50,
        db_index=True,
        verbose_name=_('Resource'),
        help_text=_('Resource type affected (e.g., menu, order, user)')
    )

    resource_id = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        db_index=True,
        verbose_name=_('Resource ID'),
        help_text=_('ID of the affected resource')
    )

    description = models.TextField(
        blank=True,
        null=True,
        verbose_name=_('Description'),
        help_text=_('Human-readable description of the action')
    )

    old_values = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_('Old values'),
        help_text=_('JSON snapshot of values before the change')
    )

    new_values = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_('New values'),
        help_text=_('JSON snapshot of values after the change')
    )

    ip_address = models.GenericIPAddressField(
        blank=True,
        null=True,
        verbose_name=_('IP address'),
        help_text=_('Client IP address')
    )

    user_agent = models.TextField(
        blank=True,
        null=True,
        verbose_name=_('User agent'),
        help_text=_('Client user agent string')
    )

    metadata = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_('Metadata'),
        help_text=_('Additional context data (JSON)')
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        verbose_name=_('Created at'),
        help_text=_('Timestamp when the action occurred')
    )

    class Meta:
        db_table = 'audit_logs'
        verbose_name = _('Audit Log')
        verbose_name_plural = _('Audit Logs')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['organization', 'created_at'], name='audit_org_created_idx'),
            models.Index(fields=['user', 'created_at'], name='audit_user_created_idx'),
            models.Index(fields=['resource', 'resource_id'], name='audit_resource_idx'),
            models.Index(fields=['action', 'created_at'], name='audit_action_created_idx'),
            models.Index(fields=['organization', 'action', 'created_at'], name='audit_org_action_idx'),
        ]

    def __str__(self) -> str:
        user_str = self.user.email if self.user else 'System'
        return f"[{self.action}] {self.resource} by {user_str}"

    def __repr__(self) -> str:
        return f"<AuditLog(id={self.id}, action={self.action}, resource='{self.resource}')>"

    @property
    def has_changes(self) -> bool:
        """Check if this audit log records any value changes."""
        return bool(self.old_values) or bool(self.new_values)

    @property
    def changed_fields(self) -> list:
        """Return list of field names that were changed."""
        old_keys = set(self.old_values.keys()) if self.old_values else set()
        new_keys = set(self.new_values.keys()) if self.new_values else set()
        return list(old_keys | new_keys)

    @classmethod
    def log_action(
        cls,
        action: str,
        resource: str,
        resource_id: str = None,
        user=None,
        organization=None,
        description: str = None,
        old_values: dict = None,
        new_values: dict = None,
        ip_address: str = None,
        user_agent: str = None,
        metadata: dict = None
    ) -> 'AuditLog':
        """
        Convenience method to create an audit log entry.

        Args:
            action: AuditAction value
            resource: Resource type (e.g., 'menu', 'order')
            resource_id: ID of the affected resource
            user: User who performed the action
            organization: Organization context
            description: Human-readable description
            old_values: Values before change
            new_values: Values after change
            ip_address: Client IP
            user_agent: Client user agent
            metadata: Additional context

        Returns:
            AuditLog: The created audit log entry
        """
        return cls.objects.create(
            action=action,
            resource=resource,
            resource_id=resource_id,
            user=user,
            organization=organization,
            description=description,
            old_values=old_values or {},
            new_values=new_values or {},
            ip_address=ip_address,
            user_agent=user_agent,
            metadata=metadata or {}
        )
