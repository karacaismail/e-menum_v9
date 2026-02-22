"""
Factory Boy factories for core application models.

These factories provide easy-to-use object creation for testing.
They follow factory_boy best practices and integrate with pytest-django.

Usage:
    from tests.factories.core import OrganizationFactory, UserFactory

    # Create a single instance
    org = OrganizationFactory()

    # Create with custom attributes
    user = UserFactory(email="custom@example.com", first_name="John")

    # Create related objects
    user_with_org = UserFactory(organization=OrganizationFactory())

    # Build without saving to database
    org = OrganizationFactory.build()

    # Create batch
    users = UserFactory.create_batch(5)
"""

import uuid
from datetime import timedelta

import factory
from django.utils import timezone
from factory.django import DjangoModelFactory


class OrganizationFactory(DjangoModelFactory):
    """
    Factory for creating Organization instances.

    Creates an active organization with unique name and slug.

    Examples:
        org = OrganizationFactory()
        org = OrganizationFactory(name="Cafe Istanbul")
        org = OrganizationFactory(status="SUSPENDED")
    """

    class Meta:
        model = "core.Organization"
        skip_postgeneration_save = True

    name = factory.LazyAttribute(lambda o: f"Test Org {uuid.uuid4().hex[:8]}")
    slug = factory.LazyAttribute(lambda o: f"test-org-{uuid.uuid4().hex[:8]}")
    email = factory.LazyAttribute(lambda o: f"org-{uuid.uuid4().hex[:8]}@example.com")
    phone = factory.LazyAttribute(lambda o: f"+90532{uuid.uuid4().int % 10000000:07d}")
    status = "ACTIVE"
    settings = factory.LazyFunction(dict)

    @factory.lazy_attribute
    def logo(self):
        return None

    @factory.lazy_attribute
    def trial_ends_at(self):
        return None

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        """Override create to handle plan assignment."""
        # Remove plan from kwargs if present, we'll handle it separately
        plan = kwargs.pop("plan", None)

        obj = super()._create(model_class, *args, **kwargs)

        # Assign plan if provided and model has plan field
        if plan is not None and hasattr(obj, "plan"):
            obj.plan = plan
            obj.save(update_fields=["plan"])

        return obj


class OrganizationWithPlanFactory(OrganizationFactory):
    """
    Factory for creating Organization with a subscription plan.

    Note: Plan must be created separately or via PlanFactory (when available).
    """

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        """Create organization and assign a FREE plan."""
        from apps.subscriptions.models import Plan

        obj = super()._create(model_class, *args, **kwargs)

        # Get or create FREE plan
        plan, _ = Plan.objects.get_or_create(
            slug="free",
            defaults={
                "name": "Free",
                "tier": "FREE",
                "price_monthly": 0,
                "price_yearly": 0,
                "is_active": True,
                "is_default": True,
            },
        )

        if hasattr(obj, "plan"):
            obj.plan = plan
            obj.save(update_fields=["plan"])

        return obj


class UserFactory(DjangoModelFactory):
    """
    Factory for creating User instances.

    Creates an active user with unique email. Organization is optional.

    Examples:
        user = UserFactory()
        user = UserFactory(email="john@example.com")
        user = UserFactory(organization=OrganizationFactory())
    """

    class Meta:
        model = "core.User"
        skip_postgeneration_save = True

    email = factory.LazyAttribute(lambda o: f"user-{uuid.uuid4().hex[:8]}@example.com")
    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    status = "ACTIVE"
    is_staff = False
    is_superuser = False
    organization = None

    @factory.lazy_attribute
    def phone(self):
        return None

    @factory.lazy_attribute
    def avatar(self):
        return None

    @factory.lazy_attribute
    def email_verified_at(self):
        return None

    @factory.lazy_attribute
    def last_login_at(self):
        return None

    @factory.post_generation
    def password(self, create, extracted, **kwargs):
        """
        Set password for the user.

        If extracted is provided, use that as password.
        Otherwise, use a default test password.
        """
        password = extracted or "TestPassword123!"
        self.set_password(password)
        if create:
            self.save(update_fields=["password"])


class AdminUserFactory(UserFactory):
    """
    Factory for creating admin (superuser) instances.

    Creates a superuser with staff and superuser flags set to True.

    Examples:
        admin = AdminUserFactory()
        admin = AdminUserFactory(email="admin@example.com")
    """

    is_staff = True
    is_superuser = True
    email_verified_at = factory.LazyFunction(timezone.now)


class StaffUserFactory(UserFactory):
    """
    Factory for creating staff users (Django admin access).

    Examples:
        staff = StaffUserFactory()
    """

    is_staff = True
    is_superuser = False


class InvitedUserFactory(UserFactory):
    """
    Factory for creating invited users who haven't completed registration.

    Examples:
        invited = InvitedUserFactory()
    """

    status = "INVITED"
    email_verified_at = None


class BranchFactory(DjangoModelFactory):
    """
    Factory for creating Branch instances.

    Creates an active branch within an organization.

    Examples:
        branch = BranchFactory(organization=OrganizationFactory())
        branch = BranchFactory(name="Downtown", is_main=True)
    """

    class Meta:
        model = "core.Branch"
        skip_postgeneration_save = True

    organization = factory.SubFactory(OrganizationFactory)
    name = factory.LazyAttribute(lambda o: f"Branch {uuid.uuid4().hex[:6]}")
    slug = factory.LazyAttribute(lambda o: f"branch-{uuid.uuid4().hex[:8]}")
    address = factory.Faker("street_address")
    city = factory.Faker("city")
    district = factory.LazyAttribute(lambda o: f"District {uuid.uuid4().hex[:4]}")
    postal_code = factory.Faker("postcode")
    country = "TR"
    phone = factory.LazyAttribute(lambda o: f"+90532{uuid.uuid4().int % 10000000:07d}")
    email = factory.LazyAttribute(lambda o: f"branch-{uuid.uuid4().hex[:6]}@example.com")
    timezone = "Europe/Istanbul"
    status = "ACTIVE"
    is_main = False
    settings = factory.LazyFunction(dict)
    operating_hours = factory.LazyFunction(dict)

    @factory.lazy_attribute
    def latitude(self):
        return None

    @factory.lazy_attribute
    def longitude(self):
        return None


class MainBranchFactory(BranchFactory):
    """
    Factory for creating a main/headquarters branch.

    Examples:
        main_branch = MainBranchFactory(organization=org)
    """

    is_main = True
    name = factory.LazyAttribute(lambda o: f"Main Branch {uuid.uuid4().hex[:6]}")


class RoleFactory(DjangoModelFactory):
    """
    Factory for creating Role instances.

    Creates organization-scoped roles by default.

    Examples:
        role = RoleFactory(name="custom_role")
        platform_role = RoleFactory(scope="PLATFORM", organization=None)
    """

    class Meta:
        model = "core.Role"
        skip_postgeneration_save = True

    name = factory.LazyAttribute(lambda o: f"role_{uuid.uuid4().hex[:8]}")
    display_name = factory.LazyAttribute(lambda o: f"Role {uuid.uuid4().hex[:6]}")
    description = factory.Faker("sentence")
    scope = "ORGANIZATION"
    is_system = False
    organization = None


class PlatformRoleFactory(RoleFactory):
    """
    Factory for creating platform-scoped roles.

    Examples:
        admin_role = PlatformRoleFactory(name="admin")
    """

    scope = "PLATFORM"
    organization = None


class SystemRoleFactory(RoleFactory):
    """
    Factory for creating system (predefined) roles.

    Examples:
        owner_role = SystemRoleFactory(name="owner")
    """

    is_system = True


class PermissionFactory(DjangoModelFactory):
    """
    Factory for creating Permission instances.

    Creates permissions following the resource.action pattern.

    Examples:
        perm = PermissionFactory(resource="menu", action="create")
        view_perm = PermissionFactory(resource="order", action="view")
    """

    class Meta:
        model = "core.Permission"
        skip_postgeneration_save = True

    resource = factory.Iterator(["menu", "order", "product", "category", "user"])
    action = factory.Iterator(["view", "create", "update", "delete"])
    description = factory.LazyAttribute(
        lambda o: f"{o.action.title()} {o.resource} permission"
    )
    is_system = False


class SystemPermissionFactory(PermissionFactory):
    """
    Factory for creating system (predefined) permissions.

    Examples:
        sys_perm = SystemPermissionFactory(resource="user", action="manage")
    """

    is_system = True


class SessionFactory(DjangoModelFactory):
    """
    Factory for creating Session (JWT refresh token) instances.

    Creates an active session for a user.

    Examples:
        session = SessionFactory(user=UserFactory())
        session = SessionFactory(user=user, expires_at=timezone.now() + timedelta(days=30))
    """

    class Meta:
        model = "core.Session"
        skip_postgeneration_save = True

    user = factory.SubFactory(UserFactory)
    refresh_token = factory.LazyAttribute(lambda o: f"token_{uuid.uuid4().hex}")
    user_agent = factory.Faker("user_agent")
    ip_address = factory.Faker("ipv4")
    status = "ACTIVE"

    @factory.lazy_attribute
    def expires_at(self):
        return timezone.now() + timedelta(days=7)

    @factory.lazy_attribute
    def revoked_at(self):
        return None

    @factory.lazy_attribute
    def revoke_reason(self):
        return None


class ExpiredSessionFactory(SessionFactory):
    """
    Factory for creating expired sessions.

    Examples:
        expired = ExpiredSessionFactory(user=user)
    """

    status = "EXPIRED"

    @factory.lazy_attribute
    def expires_at(self):
        return timezone.now() - timedelta(days=1)


class RevokedSessionFactory(SessionFactory):
    """
    Factory for creating revoked sessions.

    Examples:
        revoked = RevokedSessionFactory(user=user, revoke_reason="Password changed")
    """

    status = "REVOKED"
    revoke_reason = "Session revoked by user"

    @factory.lazy_attribute
    def revoked_at(self):
        return timezone.now()


class UserRoleFactory(DjangoModelFactory):
    """
    Factory for creating UserRole (user-role assignment) instances.

    Assigns a role to a user within an organization context.

    Examples:
        user_role = UserRoleFactory(user=user, role=role, organization=org)
        temporary = UserRoleFactory(expires_at=timezone.now() + timedelta(days=30))
    """

    class Meta:
        model = "core.UserRole"
        skip_postgeneration_save = True

    user = factory.SubFactory(UserFactory)
    role = factory.SubFactory(RoleFactory)
    organization = factory.SubFactory(OrganizationFactory)
    branch = None
    granted_by = None

    @factory.lazy_attribute
    def expires_at(self):
        return None


class TemporaryUserRoleFactory(UserRoleFactory):
    """
    Factory for creating temporary role assignments with expiration.

    Examples:
        temp_role = TemporaryUserRoleFactory(user=user, role=role)
    """

    @factory.lazy_attribute
    def expires_at(self):
        return timezone.now() + timedelta(days=30)


class RolePermissionFactory(DjangoModelFactory):
    """
    Factory for creating RolePermission (role-permission assignment) instances.

    Links permissions to roles with optional conditions.

    Examples:
        role_perm = RolePermissionFactory(role=role, permission=perm)
        conditional = RolePermissionFactory(
            conditions={"organization_id": "${user.organization_id}"}
        )
    """

    class Meta:
        model = "core.RolePermission"
        skip_postgeneration_save = True

    role = factory.SubFactory(RoleFactory)
    permission = factory.SubFactory(PermissionFactory)
    conditions = factory.LazyFunction(dict)


class AuditLogFactory(DjangoModelFactory):
    """
    Factory for creating AuditLog instances.

    Creates audit entries for various actions.

    Examples:
        log = AuditLogFactory(action="CREATE", resource="menu")
        login_log = AuditLogFactory(
            action="LOGIN",
            resource="session",
            user=user
        )
    """

    class Meta:
        model = "core.AuditLog"
        skip_postgeneration_save = True

    organization = factory.SubFactory(OrganizationFactory)
    user = factory.SubFactory(UserFactory)
    action = "CREATE"
    resource = "menu"
    resource_id = factory.LazyAttribute(lambda o: str(uuid.uuid4()))
    description = factory.Faker("sentence")
    ip_address = factory.Faker("ipv4")
    user_agent = factory.Faker("user_agent")
    old_values = factory.LazyFunction(dict)
    new_values = factory.LazyFunction(dict)
    metadata = factory.LazyFunction(dict)


class SystemAuditLogFactory(AuditLogFactory):
    """
    Factory for creating system-level audit logs (no user).

    Examples:
        sys_log = SystemAuditLogFactory(action="BULK_UPDATE", resource="products")
    """

    user = None
    organization = None


class LoginAuditLogFactory(AuditLogFactory):
    """
    Factory for creating login audit logs.

    Examples:
        login_log = LoginAuditLogFactory(user=user)
    """

    action = "LOGIN"
    resource = "session"
    description = factory.LazyAttribute(lambda o: f"User logged in")


class UpdateAuditLogFactory(AuditLogFactory):
    """
    Factory for creating update audit logs with old/new values.

    Examples:
        update_log = UpdateAuditLogFactory(
            resource="product",
            old_values={"price": "25.00"},
            new_values={"price": "30.00"}
        )
    """

    action = "UPDATE"
    old_values = factory.LazyFunction(lambda: {"field": "old_value"})
    new_values = factory.LazyFunction(lambda: {"field": "new_value"})
