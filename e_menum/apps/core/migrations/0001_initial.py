# Generated manually for E-Menum Core Module
# This migration creates all core models for the multi-tenant architecture

import uuid
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):
    """
    Initial migration for the core module.

    Creates:
    - Organization: Multi-tenant root entity
    - User: Custom user model with email-based auth
    - Branch: Multi-location support
    - Role: RBAC role definitions
    - Permission: Granular resource.action permissions
    - Session: JWT refresh token management
    - UserRole: User-Role junction with scoping
    - RolePermission: Role-Permission junction with conditions
    - AuditLog: System-wide audit logging
    """

    initial = True

    dependencies = [
        ("auth", "0012_alter_user_first_name_max_length"),
    ]

    operations = [
        # 1. Permission model (no FKs to other core models)
        migrations.CreateModel(
            name="Permission",
            fields=[
                (
                    "created_at",
                    models.DateTimeField(
                        auto_now_add=True,
                        help_text="Timestamp when record was created",
                        verbose_name="Created at",
                    ),
                ),
                (
                    "updated_at",
                    models.DateTimeField(
                        auto_now=True,
                        help_text="Timestamp when record was last updated",
                        verbose_name="Updated at",
                    ),
                ),
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        help_text="Unique identifier (UUID)",
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "resource",
                    models.CharField(
                        help_text="Resource name (e.g., menu, order, user)",
                        max_length=50,
                        verbose_name="Resource",
                    ),
                ),
                (
                    "action",
                    models.CharField(
                        choices=[
                            ("view", "View"),
                            ("create", "Create"),
                            ("update", "Update"),
                            ("delete", "Delete"),
                            ("manage", "Manage"),
                            ("publish", "Publish"),
                            ("export", "Export"),
                            ("import", "Import"),
                        ],
                        help_text="Action type (view, create, update, delete, etc.)",
                        max_length=20,
                        verbose_name="Action",
                    ),
                ),
                (
                    "description",
                    models.CharField(
                        blank=True,
                        help_text="Human-readable description of the permission",
                        max_length=255,
                        null=True,
                        verbose_name="Description",
                    ),
                ),
                (
                    "is_system",
                    models.BooleanField(
                        default=False,
                        help_text="System permissions are predefined and cannot be deleted",
                        verbose_name="Is system permission",
                    ),
                ),
            ],
            options={
                "verbose_name": "Permission",
                "verbose_name_plural": "Permissions",
                "db_table": "permissions",
                "ordering": ["resource", "action"],
            },
        ),
        # Add unique_together and indexes for Permission
        migrations.AddConstraint(
            model_name="permission",
            constraint=models.UniqueConstraint(
                fields=["resource", "action"], name="permission_resource_action_uniq"
            ),
        ),
        migrations.AddIndex(
            model_name="permission",
            index=models.Index(fields=["resource"], name="permission_resource_idx"),
        ),
        migrations.AddIndex(
            model_name="permission",
            index=models.Index(
                fields=["resource", "action"], name="permission_res_action_idx"
            ),
        ),
        # 2. Organization model (tenant root)
        migrations.CreateModel(
            name="Organization",
            fields=[
                (
                    "created_at",
                    models.DateTimeField(
                        auto_now_add=True,
                        help_text="Timestamp when record was created",
                        verbose_name="Created at",
                    ),
                ),
                (
                    "updated_at",
                    models.DateTimeField(
                        auto_now=True,
                        help_text="Timestamp when record was last updated",
                        verbose_name="Updated at",
                    ),
                ),
                (
                    "deleted_at",
                    models.DateTimeField(
                        blank=True,
                        db_index=True,
                        help_text="Timestamp when record was soft-deleted (null = active)",
                        null=True,
                        verbose_name="Deleted at",
                    ),
                ),
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        help_text="Unique identifier (UUID)",
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "name",
                    models.CharField(
                        help_text="Display name of the organization",
                        max_length=255,
                        verbose_name="Name",
                    ),
                ),
                (
                    "slug",
                    models.SlugField(
                        help_text="URL-friendly unique identifier",
                        max_length=100,
                        unique=True,
                        verbose_name="Slug",
                    ),
                ),
                (
                    "email",
                    models.EmailField(
                        help_text="Primary contact email for the organization",
                        max_length=254,
                        verbose_name="Email",
                    ),
                ),
                (
                    "phone",
                    models.CharField(
                        blank=True,
                        help_text="Contact phone number",
                        max_length=20,
                        null=True,
                        verbose_name="Phone",
                    ),
                ),
                (
                    "logo",
                    models.URLField(
                        blank=True,
                        help_text="URL to organization logo image",
                        max_length=500,
                        null=True,
                        verbose_name="Logo URL",
                    ),
                ),
                (
                    "settings",
                    models.JSONField(
                        blank=True,
                        default=dict,
                        help_text="Organization-specific settings (JSON)",
                        verbose_name="Settings",
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("ACTIVE", "Active"),
                            ("SUSPENDED", "Suspended"),
                            ("DELETED", "Deleted"),
                            ("PENDING", "Pending Approval"),
                        ],
                        db_index=True,
                        default="ACTIVE",
                        help_text="Organization lifecycle status",
                        max_length=20,
                        verbose_name="Status",
                    ),
                ),
                (
                    "trial_ends_at",
                    models.DateTimeField(
                        blank=True,
                        help_text="When trial period ends (null if not on trial)",
                        null=True,
                        verbose_name="Trial ends at",
                    ),
                ),
                # Note: plan FK to subscriptions.Plan will be added in a separate migration
                # after the subscriptions app is created (see 0002_add_organization_plan.py)
            ],
            options={
                "verbose_name": "Organization",
                "verbose_name_plural": "Organizations",
                "db_table": "organizations",
                "ordering": ["-created_at"],
            },
        ),
        migrations.AddIndex(
            model_name="organization",
            index=models.Index(
                fields=["status", "deleted_at"], name="org_status_deleted_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="organization",
            index=models.Index(fields=["slug"], name="org_slug_idx"),
        ),
        # 3. User model (custom user with email auth)
        migrations.CreateModel(
            name="User",
            fields=[
                ("password", models.CharField(max_length=128, verbose_name="password")),
                (
                    "last_login",
                    models.DateTimeField(
                        blank=True, null=True, verbose_name="last login"
                    ),
                ),
                (
                    "is_superuser",
                    models.BooleanField(
                        default=False,
                        help_text="Designates that this user has all permissions without explicitly assigning them.",
                        verbose_name="superuser status",
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(
                        auto_now_add=True,
                        help_text="Timestamp when record was created",
                        verbose_name="Created at",
                    ),
                ),
                (
                    "updated_at",
                    models.DateTimeField(
                        auto_now=True,
                        help_text="Timestamp when record was last updated",
                        verbose_name="Updated at",
                    ),
                ),
                (
                    "deleted_at",
                    models.DateTimeField(
                        blank=True,
                        db_index=True,
                        help_text="Timestamp when record was soft-deleted (null = active)",
                        null=True,
                        verbose_name="Deleted at",
                    ),
                ),
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        help_text="Unique identifier (UUID)",
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "email",
                    models.EmailField(
                        help_text="Email address (used as username for authentication)",
                        max_length=254,
                        unique=True,
                        verbose_name="Email",
                    ),
                ),
                (
                    "first_name",
                    models.CharField(
                        help_text="User's first name",
                        max_length=100,
                        verbose_name="First name",
                    ),
                ),
                (
                    "last_name",
                    models.CharField(
                        help_text="User's last name",
                        max_length=100,
                        verbose_name="Last name",
                    ),
                ),
                (
                    "avatar",
                    models.URLField(
                        blank=True,
                        help_text="URL to user's avatar image",
                        max_length=500,
                        null=True,
                        verbose_name="Avatar URL",
                    ),
                ),
                (
                    "phone",
                    models.CharField(
                        blank=True,
                        help_text="Contact phone number",
                        max_length=20,
                        null=True,
                        verbose_name="Phone",
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("ACTIVE", "Active"),
                            ("INVITED", "Invited"),
                            ("SUSPENDED", "Suspended"),
                            ("DELETED", "Deleted"),
                        ],
                        db_index=True,
                        default="ACTIVE",
                        help_text="User account status",
                        max_length=20,
                        verbose_name="Status",
                    ),
                ),
                (
                    "is_staff",
                    models.BooleanField(
                        default=False,
                        help_text="Designates whether the user can log into Django admin.",
                        verbose_name="Staff status",
                    ),
                ),
                (
                    "email_verified_at",
                    models.DateTimeField(
                        blank=True,
                        help_text="Timestamp when email was verified (null if not verified)",
                        null=True,
                        verbose_name="Email verified at",
                    ),
                ),
                (
                    "last_login_at",
                    models.DateTimeField(
                        blank=True,
                        help_text="Timestamp of last successful login",
                        null=True,
                        verbose_name="Last login at",
                    ),
                ),
                (
                    "groups",
                    models.ManyToManyField(
                        blank=True,
                        help_text="The groups this user belongs to. A user will get all permissions granted to each of their groups.",
                        related_name="user_set",
                        related_query_name="user",
                        to="auth.group",
                        verbose_name="groups",
                    ),
                ),
                (
                    "user_permissions",
                    models.ManyToManyField(
                        blank=True,
                        help_text="Specific permissions for this user.",
                        related_name="user_set",
                        related_query_name="user",
                        to="auth.permission",
                        verbose_name="user permissions",
                    ),
                ),
                (
                    "organization",
                    models.ForeignKey(
                        blank=True,
                        help_text="Organization this user belongs to (null for platform users)",
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="users",
                        to="core.organization",
                        verbose_name="Organization",
                    ),
                ),
            ],
            options={
                "verbose_name": "User",
                "verbose_name_plural": "Users",
                "db_table": "users",
                "ordering": ["-created_at"],
            },
        ),
        migrations.AddIndex(
            model_name="user",
            index=models.Index(
                fields=["organization", "status"], name="user_org_status_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="user",
            index=models.Index(
                fields=["organization", "deleted_at"], name="user_org_deleted_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="user",
            index=models.Index(fields=["email"], name="user_email_idx"),
        ),
        # 4. Branch model (multi-location support)
        migrations.CreateModel(
            name="Branch",
            fields=[
                (
                    "created_at",
                    models.DateTimeField(
                        auto_now_add=True,
                        help_text="Timestamp when record was created",
                        verbose_name="Created at",
                    ),
                ),
                (
                    "updated_at",
                    models.DateTimeField(
                        auto_now=True,
                        help_text="Timestamp when record was last updated",
                        verbose_name="Updated at",
                    ),
                ),
                (
                    "deleted_at",
                    models.DateTimeField(
                        blank=True,
                        db_index=True,
                        help_text="Timestamp when record was soft-deleted (null = active)",
                        null=True,
                        verbose_name="Deleted at",
                    ),
                ),
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        help_text="Unique identifier (UUID)",
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "name",
                    models.CharField(
                        help_text="Display name of the branch",
                        max_length=255,
                        verbose_name="Name",
                    ),
                ),
                (
                    "slug",
                    models.SlugField(
                        help_text="URL-friendly identifier (unique within organization)",
                        max_length=100,
                        verbose_name="Slug",
                    ),
                ),
                (
                    "address",
                    models.TextField(
                        blank=True,
                        help_text="Full street address",
                        null=True,
                        verbose_name="Address",
                    ),
                ),
                (
                    "city",
                    models.CharField(
                        blank=True,
                        help_text="City name",
                        max_length=100,
                        null=True,
                        verbose_name="City",
                    ),
                ),
                (
                    "district",
                    models.CharField(
                        blank=True,
                        help_text="District or neighborhood",
                        max_length=100,
                        null=True,
                        verbose_name="District",
                    ),
                ),
                (
                    "postal_code",
                    models.CharField(
                        blank=True,
                        help_text="Postal or ZIP code",
                        max_length=20,
                        null=True,
                        verbose_name="Postal code",
                    ),
                ),
                (
                    "country",
                    models.CharField(
                        default="TR",
                        help_text="Country code (ISO 3166-1 alpha-2)",
                        max_length=2,
                        verbose_name="Country",
                    ),
                ),
                (
                    "phone",
                    models.CharField(
                        blank=True,
                        help_text="Branch contact phone number",
                        max_length=20,
                        null=True,
                        verbose_name="Phone",
                    ),
                ),
                (
                    "email",
                    models.EmailField(
                        blank=True,
                        help_text="Branch contact email",
                        max_length=254,
                        null=True,
                        verbose_name="Email",
                    ),
                ),
                (
                    "latitude",
                    models.DecimalField(
                        blank=True,
                        decimal_places=7,
                        help_text="GPS latitude coordinate",
                        max_digits=10,
                        null=True,
                        verbose_name="Latitude",
                    ),
                ),
                (
                    "longitude",
                    models.DecimalField(
                        blank=True,
                        decimal_places=7,
                        help_text="GPS longitude coordinate",
                        max_digits=10,
                        null=True,
                        verbose_name="Longitude",
                    ),
                ),
                (
                    "timezone",
                    models.CharField(
                        default="Europe/Istanbul",
                        help_text="Branch timezone (IANA format)",
                        max_length=50,
                        verbose_name="Timezone",
                    ),
                ),
                (
                    "settings",
                    models.JSONField(
                        blank=True,
                        default=dict,
                        help_text="Branch-specific settings (JSON)",
                        verbose_name="Settings",
                    ),
                ),
                (
                    "operating_hours",
                    models.JSONField(
                        blank=True,
                        default=dict,
                        help_text="Daily operating hours (JSON)",
                        verbose_name="Operating hours",
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("ACTIVE", "Active"),
                            ("INACTIVE", "Inactive"),
                            ("SUSPENDED", "Suspended"),
                        ],
                        db_index=True,
                        default="ACTIVE",
                        help_text="Branch lifecycle status",
                        max_length=20,
                        verbose_name="Status",
                    ),
                ),
                (
                    "is_main",
                    models.BooleanField(
                        default=False,
                        help_text="Whether this is the main/headquarters branch",
                        verbose_name="Is main branch",
                    ),
                ),
                (
                    "organization",
                    models.ForeignKey(
                        help_text="Organization this branch belongs to",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="branches",
                        to="core.organization",
                        verbose_name="Organization",
                    ),
                ),
            ],
            options={
                "verbose_name": "Branch",
                "verbose_name_plural": "Branches",
                "db_table": "branches",
                "ordering": ["-is_main", "name"],
            },
        ),
        migrations.AddConstraint(
            model_name="branch",
            constraint=models.UniqueConstraint(
                fields=["organization", "slug"], name="branch_org_slug_uniq"
            ),
        ),
        migrations.AddIndex(
            model_name="branch",
            index=models.Index(
                fields=["organization", "status"], name="branch_org_status_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="branch",
            index=models.Index(
                fields=["organization", "deleted_at"], name="branch_org_deleted_idx"
            ),
        ),
        # 5. Role model (RBAC role definitions)
        migrations.CreateModel(
            name="Role",
            fields=[
                (
                    "created_at",
                    models.DateTimeField(
                        auto_now_add=True,
                        help_text="Timestamp when record was created",
                        verbose_name="Created at",
                    ),
                ),
                (
                    "updated_at",
                    models.DateTimeField(
                        auto_now=True,
                        help_text="Timestamp when record was last updated",
                        verbose_name="Updated at",
                    ),
                ),
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        help_text="Unique identifier (UUID)",
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "name",
                    models.CharField(
                        help_text="Internal role identifier (lowercase, underscore-separated)",
                        max_length=50,
                        verbose_name="Name",
                    ),
                ),
                (
                    "display_name",
                    models.CharField(
                        help_text="Human-readable role name",
                        max_length=100,
                        verbose_name="Display name",
                    ),
                ),
                (
                    "description",
                    models.TextField(
                        blank=True,
                        help_text="Detailed description of the role and its capabilities",
                        null=True,
                        verbose_name="Description",
                    ),
                ),
                (
                    "scope",
                    models.CharField(
                        choices=[
                            ("PLATFORM", "Platform"),
                            ("ORGANIZATION", "Organization"),
                        ],
                        db_index=True,
                        default="ORGANIZATION",
                        help_text="Role scope (PLATFORM or ORGANIZATION)",
                        max_length=20,
                        verbose_name="Scope",
                    ),
                ),
                (
                    "is_system",
                    models.BooleanField(
                        default=False,
                        help_text="System roles are predefined and cannot be modified",
                        verbose_name="Is system role",
                    ),
                ),
                (
                    "organization",
                    models.ForeignKey(
                        blank=True,
                        help_text="Organization for org-scoped roles (null for platform roles)",
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="roles",
                        to="core.organization",
                        verbose_name="Organization",
                    ),
                ),
            ],
            options={
                "verbose_name": "Role",
                "verbose_name_plural": "Roles",
                "db_table": "roles",
                "ordering": ["scope", "name"],
            },
        ),
        migrations.AddConstraint(
            model_name="role",
            constraint=models.UniqueConstraint(
                fields=["name", "scope", "organization"],
                name="role_name_scope_org_uniq",
            ),
        ),
        migrations.AddIndex(
            model_name="role",
            index=models.Index(fields=["scope"], name="role_scope_idx"),
        ),
        migrations.AddIndex(
            model_name="role",
            index=models.Index(
                fields=["organization", "scope"], name="role_org_scope_idx"
            ),
        ),
        # 6. Session model (JWT refresh token management)
        migrations.CreateModel(
            name="Session",
            fields=[
                (
                    "created_at",
                    models.DateTimeField(
                        auto_now_add=True,
                        help_text="Timestamp when record was created",
                        verbose_name="Created at",
                    ),
                ),
                (
                    "updated_at",
                    models.DateTimeField(
                        auto_now=True,
                        help_text="Timestamp when record was last updated",
                        verbose_name="Updated at",
                    ),
                ),
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        help_text="Unique identifier (UUID)",
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "refresh_token",
                    models.CharField(
                        help_text="Hashed refresh token",
                        max_length=500,
                        verbose_name="Refresh token",
                    ),
                ),
                (
                    "user_agent",
                    models.TextField(
                        blank=True,
                        help_text="Browser/client user agent string",
                        null=True,
                        verbose_name="User agent",
                    ),
                ),
                (
                    "ip_address",
                    models.GenericIPAddressField(
                        blank=True,
                        help_text="Client IP address",
                        null=True,
                        verbose_name="IP address",
                    ),
                ),
                (
                    "expires_at",
                    models.DateTimeField(
                        help_text="When the session/refresh token expires",
                        verbose_name="Expires at",
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("ACTIVE", "Active"),
                            ("EXPIRED", "Expired"),
                            ("REVOKED", "Revoked"),
                        ],
                        db_index=True,
                        default="ACTIVE",
                        help_text="Session status",
                        max_length=20,
                        verbose_name="Status",
                    ),
                ),
                (
                    "revoked_at",
                    models.DateTimeField(
                        blank=True,
                        help_text="When the session was revoked",
                        null=True,
                        verbose_name="Revoked at",
                    ),
                ),
                (
                    "revoke_reason",
                    models.CharField(
                        blank=True,
                        help_text="Reason for session revocation",
                        max_length=255,
                        null=True,
                        verbose_name="Revoke reason",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        help_text="User who owns this session",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="sessions",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="User",
                    ),
                ),
            ],
            options={
                "verbose_name": "Session",
                "verbose_name_plural": "Sessions",
                "db_table": "sessions",
                "ordering": ["-created_at"],
            },
        ),
        migrations.AddIndex(
            model_name="session",
            index=models.Index(
                fields=["user", "status"], name="session_user_status_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="session",
            index=models.Index(fields=["refresh_token"], name="session_token_idx"),
        ),
        migrations.AddIndex(
            model_name="session",
            index=models.Index(fields=["expires_at"], name="session_expires_idx"),
        ),
        # 7. RolePermission junction table
        migrations.CreateModel(
            name="RolePermission",
            fields=[
                (
                    "created_at",
                    models.DateTimeField(
                        auto_now_add=True,
                        help_text="Timestamp when record was created",
                        verbose_name="Created at",
                    ),
                ),
                (
                    "updated_at",
                    models.DateTimeField(
                        auto_now=True,
                        help_text="Timestamp when record was last updated",
                        verbose_name="Updated at",
                    ),
                ),
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        help_text="Unique identifier (UUID)",
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "conditions",
                    models.JSONField(
                        blank=True,
                        default=dict,
                        help_text="CASL-like conditions for fine-grained access control",
                        verbose_name="Conditions",
                    ),
                ),
                (
                    "permission",
                    models.ForeignKey(
                        help_text="Permission granted to the role",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="role_permissions",
                        to="core.permission",
                        verbose_name="Permission",
                    ),
                ),
                (
                    "role",
                    models.ForeignKey(
                        help_text="Role that has this permission",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="role_permissions",
                        to="core.role",
                        verbose_name="Role",
                    ),
                ),
            ],
            options={
                "verbose_name": "Role Permission",
                "verbose_name_plural": "Role Permissions",
                "db_table": "role_permissions",
                "ordering": ["role", "permission"],
            },
        ),
        migrations.AddConstraint(
            model_name="rolepermission",
            constraint=models.UniqueConstraint(
                fields=["role", "permission"], name="roleperm_role_perm_uniq"
            ),
        ),
        migrations.AddIndex(
            model_name="rolepermission",
            index=models.Index(fields=["role"], name="roleperm_role_idx"),
        ),
        migrations.AddIndex(
            model_name="rolepermission",
            index=models.Index(fields=["permission"], name="roleperm_perm_idx"),
        ),
        # Add M2M relationship to Role (permissions through RolePermission)
        migrations.AddField(
            model_name="role",
            name="permissions",
            field=models.ManyToManyField(
                help_text="Permissions granted to this role",
                related_name="roles",
                through="core.RolePermission",
                to="core.permission",
                verbose_name="Permissions",
            ),
        ),
        # 8. UserRole junction table
        migrations.CreateModel(
            name="UserRole",
            fields=[
                (
                    "created_at",
                    models.DateTimeField(
                        auto_now_add=True,
                        help_text="Timestamp when record was created",
                        verbose_name="Created at",
                    ),
                ),
                (
                    "updated_at",
                    models.DateTimeField(
                        auto_now=True,
                        help_text="Timestamp when record was last updated",
                        verbose_name="Updated at",
                    ),
                ),
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        help_text="Unique identifier (UUID)",
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "expires_at",
                    models.DateTimeField(
                        blank=True,
                        help_text="Optional expiration for temporary role assignments",
                        null=True,
                        verbose_name="Expires at",
                    ),
                ),
                (
                    "branch",
                    models.ForeignKey(
                        blank=True,
                        help_text="Optional branch-level restriction",
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="user_roles",
                        to="core.branch",
                        verbose_name="Branch",
                    ),
                ),
                (
                    "granted_by",
                    models.ForeignKey(
                        blank=True,
                        help_text="User who granted this role",
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="granted_roles",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Granted by",
                    ),
                ),
                (
                    "organization",
                    models.ForeignKey(
                        blank=True,
                        help_text="Organization scope for this role assignment",
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="user_roles",
                        to="core.organization",
                        verbose_name="Organization",
                    ),
                ),
                (
                    "role",
                    models.ForeignKey(
                        help_text="Role assigned to the user",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="user_roles",
                        to="core.role",
                        verbose_name="Role",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        help_text="User who has this role",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="user_roles",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="User",
                    ),
                ),
            ],
            options={
                "verbose_name": "User Role",
                "verbose_name_plural": "User Roles",
                "db_table": "user_roles",
                "ordering": ["-created_at"],
            },
        ),
        migrations.AddConstraint(
            model_name="userrole",
            constraint=models.UniqueConstraint(
                fields=["user", "role", "organization", "branch"],
                name="userrole_user_role_org_branch_uniq",
            ),
        ),
        migrations.AddIndex(
            model_name="userrole",
            index=models.Index(
                fields=["user", "organization"], name="userrole_user_org_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="userrole",
            index=models.Index(
                fields=["organization", "role"], name="userrole_org_role_idx"
            ),
        ),
        # 9. AuditLog model (system-wide audit logging)
        migrations.CreateModel(
            name="AuditLog",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        help_text="Unique identifier (UUID)",
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "action",
                    models.CharField(
                        choices=[
                            ("CREATE", "Create"),
                            ("UPDATE", "Update"),
                            ("DELETE", "Delete"),
                            ("LOGIN", "Login"),
                            ("LOGOUT", "Logout"),
                            ("VIEW", "View"),
                            ("EXPORT", "Export"),
                            ("IMPORT", "Import"),
                            ("PUBLISH", "Publish"),
                            ("UNPUBLISH", "Unpublish"),
                            ("ACTIVATE", "Activate"),
                            ("DEACTIVATE", "Deactivate"),
                            ("SUSPEND", "Suspend"),
                            ("RESTORE", "Restore"),
                        ],
                        db_index=True,
                        help_text="Type of action performed",
                        max_length=30,
                        verbose_name="Action",
                    ),
                ),
                (
                    "resource",
                    models.CharField(
                        db_index=True,
                        help_text="Resource type affected (e.g., menu, order, user)",
                        max_length=50,
                        verbose_name="Resource",
                    ),
                ),
                (
                    "resource_id",
                    models.CharField(
                        blank=True,
                        db_index=True,
                        help_text="ID of the affected resource",
                        max_length=100,
                        null=True,
                        verbose_name="Resource ID",
                    ),
                ),
                (
                    "description",
                    models.TextField(
                        blank=True,
                        help_text="Human-readable description of the action",
                        null=True,
                        verbose_name="Description",
                    ),
                ),
                (
                    "old_values",
                    models.JSONField(
                        blank=True,
                        default=dict,
                        help_text="JSON snapshot of values before the change",
                        verbose_name="Old values",
                    ),
                ),
                (
                    "new_values",
                    models.JSONField(
                        blank=True,
                        default=dict,
                        help_text="JSON snapshot of values after the change",
                        verbose_name="New values",
                    ),
                ),
                (
                    "ip_address",
                    models.GenericIPAddressField(
                        blank=True,
                        help_text="Client IP address",
                        null=True,
                        verbose_name="IP address",
                    ),
                ),
                (
                    "user_agent",
                    models.TextField(
                        blank=True,
                        help_text="Client user agent string",
                        null=True,
                        verbose_name="User agent",
                    ),
                ),
                (
                    "metadata",
                    models.JSONField(
                        blank=True,
                        default=dict,
                        help_text="Additional context data (JSON)",
                        verbose_name="Metadata",
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(
                        auto_now_add=True,
                        db_index=True,
                        help_text="Timestamp when the action occurred",
                        verbose_name="Created at",
                    ),
                ),
                (
                    "organization",
                    models.ForeignKey(
                        blank=True,
                        help_text="Organization context for this audit log (null for platform-level actions)",
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="audit_logs",
                        to="core.organization",
                        verbose_name="Organization",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        blank=True,
                        help_text="User who performed the action (null for system actions)",
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="audit_logs",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="User",
                    ),
                ),
            ],
            options={
                "verbose_name": "Audit Log",
                "verbose_name_plural": "Audit Logs",
                "db_table": "audit_logs",
                "ordering": ["-created_at"],
            },
        ),
        migrations.AddIndex(
            model_name="auditlog",
            index=models.Index(
                fields=["organization", "created_at"], name="audit_org_created_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="auditlog",
            index=models.Index(
                fields=["user", "created_at"], name="audit_user_created_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="auditlog",
            index=models.Index(
                fields=["resource", "resource_id"], name="audit_resource_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="auditlog",
            index=models.Index(
                fields=["action", "created_at"], name="audit_action_created_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="auditlog",
            index=models.Index(
                fields=["organization", "action", "created_at"],
                name="audit_org_action_idx",
            ),
        ),
    ]
