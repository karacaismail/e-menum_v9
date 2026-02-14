"""
Unit tests for core application models (Organization, User).

These tests verify model creation, field validation, properties, methods,
and soft delete functionality for the foundational models.

Run with:
    pytest tests/core/test_models.py -v
"""

import uuid
from datetime import timedelta

import pytest
from django.db import IntegrityError
from django.utils import timezone

from apps.core.choices import OrganizationStatus, UserStatus, RoleScope
from apps.core.models import (
    Organization,
    User,
    Branch,
    Role,
    Permission,
    Session,
    UserRole,
    RolePermission,
    AuditLog,
    SoftDeleteManager,
)
from tests.factories.core import (
    OrganizationFactory,
    UserFactory,
    AdminUserFactory,
    BranchFactory,
    RoleFactory,
    PermissionFactory,
    SessionFactory,
    UserRoleFactory,
    RolePermissionFactory,
    AuditLogFactory,
)


# =============================================================================
# ORGANIZATION MODEL TESTS
# =============================================================================


@pytest.mark.django_db
class TestOrganization:
    """Test cases for Organization model."""

    def test_create_organization(self):
        """Test creating an organization with required fields."""
        org = OrganizationFactory()

        assert org.id is not None
        assert isinstance(org.id, uuid.UUID)
        assert org.name is not None
        assert org.slug is not None
        assert org.email is not None
        assert org.status == OrganizationStatus.ACTIVE
        assert org.created_at is not None
        assert org.updated_at is not None
        assert org.deleted_at is None

    def test_create_organization_with_all_fields(self):
        """Test creating an organization with all optional fields."""
        org = OrganizationFactory(
            name="Cafe Istanbul",
            slug="cafe-istanbul",
            email="info@cafeistanbul.com",
            phone="+905321234567",
            logo="https://example.com/logo.png",
            settings={"theme": "dark", "currency": "TRY"},
            status=OrganizationStatus.ACTIVE,
        )

        assert org.name == "Cafe Istanbul"
        assert org.slug == "cafe-istanbul"
        assert org.email == "info@cafeistanbul.com"
        assert org.phone == "+905321234567"
        assert org.logo == "https://example.com/logo.png"
        assert org.settings == {"theme": "dark", "currency": "TRY"}
        assert org.status == OrganizationStatus.ACTIVE

    def test_organization_str_representation(self):
        """Test organization string representation."""
        org = OrganizationFactory(name="Test Restaurant")
        assert str(org) == "Test Restaurant"

    def test_organization_repr(self):
        """Test organization repr."""
        org = OrganizationFactory(name="Test Cafe")
        repr_str = repr(org)
        assert "Organization" in repr_str
        assert "Test Cafe" in repr_str
        assert str(org.id) in repr_str

    def test_organization_unique_slug(self):
        """Test that organization slugs must be unique."""
        OrganizationFactory(slug="unique-slug")

        with pytest.raises(IntegrityError):
            OrganizationFactory(slug="unique-slug")

    def test_organization_is_active_property(self):
        """Test is_active property returns True for active non-deleted orgs."""
        org = OrganizationFactory(status=OrganizationStatus.ACTIVE)
        assert org.is_active is True

        org.status = OrganizationStatus.SUSPENDED
        org.save()
        assert org.is_active is False

        org.status = OrganizationStatus.ACTIVE
        org.soft_delete()
        assert org.is_active is False

    def test_organization_is_on_trial_property(self):
        """Test is_on_trial property."""
        # No trial
        org = OrganizationFactory(trial_ends_at=None)
        assert org.is_on_trial is False

        # Active trial
        org.trial_ends_at = timezone.now() + timedelta(days=7)
        org.save()
        assert org.is_on_trial is True

        # Expired trial
        org.trial_ends_at = timezone.now() - timedelta(days=1)
        org.save()
        assert org.is_on_trial is False

    def test_organization_get_setting(self):
        """Test get_setting method retrieves settings correctly."""
        org = OrganizationFactory(settings={"theme": "dark", "currency": "TRY"})

        assert org.get_setting("theme") == "dark"
        assert org.get_setting("currency") == "TRY"
        assert org.get_setting("nonexistent") is None
        assert org.get_setting("nonexistent", "default") == "default"

    def test_organization_set_setting(self):
        """Test set_setting method updates settings correctly."""
        org = OrganizationFactory(settings={})

        org.set_setting("theme", "light")
        org.refresh_from_db()

        assert org.get_setting("theme") == "light"

    def test_organization_suspend(self):
        """Test suspend method changes status and records reason."""
        org = OrganizationFactory(status=OrganizationStatus.ACTIVE)

        org.suspend(reason="Unpaid bills")
        org.refresh_from_db()

        assert org.status == OrganizationStatus.SUSPENDED
        assert org.settings.get("suspension_reason") == "Unpaid bills"
        assert "suspended_at" in org.settings

    def test_organization_suspend_without_reason(self):
        """Test suspend method works without reason."""
        org = OrganizationFactory(status=OrganizationStatus.ACTIVE)

        org.suspend()
        org.refresh_from_db()

        assert org.status == OrganizationStatus.SUSPENDED
        assert "suspension_reason" not in org.settings

    def test_organization_activate(self):
        """Test activate method restores organization to active status."""
        org = OrganizationFactory(status=OrganizationStatus.ACTIVE)
        org.suspend(reason="Test suspension")
        org.refresh_from_db()

        org.activate()
        org.refresh_from_db()

        assert org.status == OrganizationStatus.ACTIVE
        assert "suspension_reason" not in org.settings
        assert "suspended_at" not in org.settings

    def test_organization_soft_delete(self):
        """Test soft_delete marks deleted_at but doesn't physically delete."""
        org = OrganizationFactory()
        org_id = org.id

        org.soft_delete()
        org.refresh_from_db()

        assert org.deleted_at is not None
        assert org.is_deleted is True
        # Verify record still exists in database
        assert Organization.all_objects.filter(id=org_id).exists()
        # But not in default queryset
        assert not Organization.objects.filter(id=org_id).exists()

    def test_organization_restore(self):
        """Test restore clears deleted_at and makes record active again."""
        org = OrganizationFactory()
        org.soft_delete()
        org.refresh_from_db()

        org.restore()
        org.refresh_from_db()

        assert org.deleted_at is None
        assert org.is_deleted is False
        assert Organization.objects.filter(id=org.id).exists()

    def test_organization_soft_delete_manager(self):
        """Test SoftDeleteManager filters out deleted records by default."""
        org1 = OrganizationFactory(name="Active Org")
        org2 = OrganizationFactory(name="Deleted Org")
        org2.soft_delete()

        # Default manager excludes deleted
        active_orgs = Organization.objects.all()
        assert org1 in active_orgs
        assert org2 not in active_orgs

        # all_objects includes deleted
        all_orgs = Organization.all_objects.all()
        assert org1 in all_orgs
        assert org2 in all_orgs

    def test_organization_timestamps(self):
        """Test that created_at and updated_at are managed automatically."""
        before_create = timezone.now()
        org = OrganizationFactory()
        after_create = timezone.now()

        assert before_create <= org.created_at <= after_create
        assert before_create <= org.updated_at <= after_create

        # Update and verify updated_at changes
        original_updated = org.updated_at
        org.name = "Updated Name"
        org.save()
        org.refresh_from_db()

        assert org.updated_at > original_updated


# =============================================================================
# USER MODEL TESTS
# =============================================================================


@pytest.mark.django_db
class TestUser:
    """Test cases for User model."""

    def test_create_user(self):
        """Test creating a user with required fields."""
        user = UserFactory()

        assert user.id is not None
        assert isinstance(user.id, uuid.UUID)
        assert user.email is not None
        assert user.first_name is not None
        assert user.last_name is not None
        assert user.status == UserStatus.ACTIVE
        assert user.is_staff is False
        assert user.is_superuser is False
        assert user.created_at is not None
        assert user.updated_at is not None
        assert user.deleted_at is None

    def test_create_user_with_all_fields(self):
        """Test creating a user with all optional fields."""
        org = OrganizationFactory()
        user = UserFactory(
            email="john.doe@example.com",
            first_name="John",
            last_name="Doe",
            phone="+905321234567",
            avatar="https://example.com/avatar.png",
            status=UserStatus.ACTIVE,
            organization=org,
        )

        assert user.email == "john.doe@example.com"
        assert user.first_name == "John"
        assert user.last_name == "Doe"
        assert user.phone == "+905321234567"
        assert user.avatar == "https://example.com/avatar.png"
        assert user.organization == org

    def test_create_user_with_password(self):
        """Test that password is hashed correctly."""
        user = UserFactory(password="SecurePassword123!")

        assert user.password != "SecurePassword123!"
        assert user.check_password("SecurePassword123!")

    def test_create_superuser(self):
        """Test creating a superuser."""
        admin = AdminUserFactory()

        assert admin.is_staff is True
        assert admin.is_superuser is True
        assert admin.status == UserStatus.ACTIVE

    def test_user_str_representation(self):
        """Test user string representation."""
        user = UserFactory(email="test@example.com")
        assert str(user) == "test@example.com"

    def test_user_repr(self):
        """Test user repr."""
        user = UserFactory(email="repr@example.com")
        repr_str = repr(user)
        assert "User" in repr_str
        assert "repr@example.com" in repr_str
        assert str(user.id) in repr_str

    def test_user_unique_email(self):
        """Test that user emails must be unique."""
        UserFactory(email="unique@example.com")

        with pytest.raises(IntegrityError):
            UserFactory(email="unique@example.com")

    def test_user_full_name_property(self):
        """Test full_name property returns first and last name combined."""
        user = UserFactory(first_name="John", last_name="Doe")
        assert user.full_name == "John Doe"

    def test_user_get_full_name(self):
        """Test get_full_name method (Django AbstractBaseUser interface)."""
        user = UserFactory(first_name="Jane", last_name="Smith")
        assert user.get_full_name() == "Jane Smith"

    def test_user_get_short_name(self):
        """Test get_short_name method (Django AbstractBaseUser interface)."""
        user = UserFactory(first_name="Jane", last_name="Smith")
        assert user.get_short_name() == "Jane"

    def test_user_is_active_user_property(self):
        """Test is_active_user property returns True for active non-deleted users."""
        user = UserFactory(status=UserStatus.ACTIVE)
        assert user.is_active_user is True

        user.status = UserStatus.SUSPENDED
        user.save()
        assert user.is_active_user is False

        user.status = UserStatus.ACTIVE
        user.soft_delete()
        assert user.is_active_user is False

    def test_user_is_email_verified_property(self):
        """Test is_email_verified property."""
        user = UserFactory(email_verified_at=None)
        assert user.is_email_verified is False

        user.email_verified_at = timezone.now()
        user.save()
        assert user.is_email_verified is True

    def test_user_verify_email(self):
        """Test verify_email method sets verification timestamp."""
        user = UserFactory(email_verified_at=None)
        before_verify = timezone.now()

        user.verify_email()
        user.refresh_from_db()

        assert user.email_verified_at is not None
        assert user.email_verified_at >= before_verify

    def test_user_record_login(self):
        """Test record_login method sets last_login_at timestamp."""
        user = UserFactory(last_login_at=None)
        before_login = timezone.now()

        user.record_login()
        user.refresh_from_db()

        assert user.last_login_at is not None
        assert user.last_login_at >= before_login

    def test_user_suspend(self):
        """Test suspend method changes user status to SUSPENDED."""
        user = UserFactory(status=UserStatus.ACTIVE)

        user.suspend()
        user.refresh_from_db()

        assert user.status == UserStatus.SUSPENDED

    def test_user_activate(self):
        """Test activate method restores user to ACTIVE status."""
        user = UserFactory(status=UserStatus.SUSPENDED)

        user.activate()
        user.refresh_from_db()

        assert user.status == UserStatus.ACTIVE

    def test_user_soft_delete(self):
        """Test soft_delete marks deleted_at but doesn't physically delete."""
        user = UserFactory()
        user_id = user.id

        user.soft_delete()
        user.refresh_from_db()

        assert user.deleted_at is not None
        assert user.is_deleted is True
        # Verify we can still fetch with all_objects
        assert User.all_objects.filter(id=user_id).exists()

    def test_user_restore(self):
        """Test restore clears deleted_at."""
        user = UserFactory()
        user.soft_delete()
        user.refresh_from_db()

        user.restore()
        user.refresh_from_db()

        assert user.deleted_at is None
        assert user.is_deleted is False

    def test_user_with_organization(self):
        """Test user can be associated with an organization."""
        org = OrganizationFactory()
        user = UserFactory(organization=org)

        assert user.organization == org
        assert user in org.users.all()

    def test_user_without_organization(self):
        """Test user can exist without organization (platform user)."""
        user = UserFactory(organization=None)

        assert user.organization is None

    def test_user_manager_create_user(self):
        """Test UserManager.create_user method."""
        user = User.objects.create_user(
            email="manager_test@example.com",
            password="TestPassword123!",
            first_name="Manager",
            last_name="Test",
        )

        assert user.email == "manager_test@example.com"
        assert user.check_password("TestPassword123!")
        assert user.is_staff is False
        assert user.is_superuser is False

    def test_user_manager_create_user_without_email_raises(self):
        """Test UserManager.create_user raises error without email."""
        with pytest.raises(ValueError, match="Email"):
            User.objects.create_user(
                email="",
                password="TestPassword123!",
                first_name="Test",
                last_name="User",
            )

    def test_user_manager_create_superuser(self):
        """Test UserManager.create_superuser method."""
        admin = User.objects.create_superuser(
            email="admin_manager_test@example.com",
            password="AdminPassword123!",
            first_name="Admin",
            last_name="Test",
        )

        assert admin.is_staff is True
        assert admin.is_superuser is True
        assert admin.status == UserStatus.ACTIVE

    def test_user_manager_create_superuser_without_is_staff_raises(self):
        """Test UserManager.create_superuser raises error without is_staff."""
        with pytest.raises(ValueError, match="is_staff"):
            User.objects.create_superuser(
                email="admin_fail@example.com",
                password="AdminPassword123!",
                first_name="Admin",
                last_name="Test",
                is_staff=False,
            )

    def test_user_manager_create_superuser_without_is_superuser_raises(self):
        """Test UserManager.create_superuser raises error without is_superuser."""
        with pytest.raises(ValueError, match="is_superuser"):
            User.objects.create_superuser(
                email="admin_fail2@example.com",
                password="AdminPassword123!",
                first_name="Admin",
                last_name="Test",
                is_superuser=False,
            )

    def test_user_email_normalization(self):
        """Test that email is normalized on create."""
        user = User.objects.create_user(
            email="Test.User@EXAMPLE.COM",
            password="TestPassword123!",
            first_name="Test",
            last_name="User",
        )

        # Domain should be lowercased
        assert user.email == "Test.User@example.com"

    def test_user_timestamps(self):
        """Test that created_at and updated_at are managed automatically."""
        before_create = timezone.now()
        user = UserFactory()
        after_create = timezone.now()

        assert before_create <= user.created_at <= after_create
        assert before_create <= user.updated_at <= after_create


# =============================================================================
# BRANCH MODEL TESTS
# =============================================================================


@pytest.mark.django_db
class TestBranch:
    """Test cases for Branch model."""

    def test_create_branch(self):
        """Test creating a branch with required fields."""
        org = OrganizationFactory()
        branch = BranchFactory(organization=org)

        assert branch.id is not None
        assert branch.organization == org
        assert branch.name is not None
        assert branch.slug is not None
        assert branch.status == "ACTIVE"
        assert branch.is_main is False

    def test_branch_str_representation(self):
        """Test branch string representation."""
        org = OrganizationFactory(name="Test Org")
        branch = BranchFactory(organization=org, name="Downtown Branch")
        assert str(branch) == "Downtown Branch (Test Org)"

    def test_branch_is_active_property(self):
        """Test is_active property."""
        branch = BranchFactory(status="ACTIVE")
        assert branch.is_active is True

        branch.status = "INACTIVE"
        branch.save()
        assert branch.is_active is False

    def test_branch_full_address_property(self):
        """Test full_address property returns formatted address."""
        branch = BranchFactory(
            address="123 Main St",
            district="Downtown",
            city="Istanbul",
            postal_code="34000",
            country="TR",
        )

        expected = "123 Main St, Downtown, Istanbul, 34000, TR"
        assert branch.full_address == expected

    def test_branch_soft_delete(self):
        """Test branch soft delete functionality."""
        branch = BranchFactory()
        branch_id = branch.id

        branch.soft_delete()
        branch.refresh_from_db()

        assert branch.deleted_at is not None
        assert branch.is_deleted is True
        assert Branch.all_objects.filter(id=branch_id).exists()
        assert not Branch.objects.filter(id=branch_id).exists()


# =============================================================================
# ROLE MODEL TESTS
# =============================================================================


@pytest.mark.django_db
class TestRole:
    """Test cases for Role model."""

    def test_create_role(self):
        """Test creating a role with required fields."""
        role = RoleFactory()

        assert role.id is not None
        assert role.name is not None
        assert role.display_name is not None
        assert role.scope == RoleScope.ORGANIZATION
        assert role.is_system is False

    def test_role_str_representation(self):
        """Test role string representation."""
        org = OrganizationFactory(name="Test Org")
        role = RoleFactory(display_name="Manager", organization=org)
        assert str(role) == "Manager (Test Org)"

        # Platform role
        platform_role = RoleFactory(
            display_name="Super Admin",
            scope=RoleScope.PLATFORM,
            organization=None,
        )
        assert str(platform_role) == "Super Admin (Platform)"

    def test_role_is_platform_role_property(self):
        """Test is_platform_role property."""
        platform_role = RoleFactory(scope=RoleScope.PLATFORM)
        assert platform_role.is_platform_role is True
        assert platform_role.is_organization_role is False

    def test_role_is_organization_role_property(self):
        """Test is_organization_role property."""
        org_role = RoleFactory(scope=RoleScope.ORGANIZATION)
        assert org_role.is_organization_role is True
        assert org_role.is_platform_role is False


# =============================================================================
# PERMISSION MODEL TESTS
# =============================================================================


@pytest.mark.django_db
class TestPermission:
    """Test cases for Permission model."""

    def test_create_permission(self):
        """Test creating a permission with required fields."""
        perm = PermissionFactory(resource="menu", action="create")

        assert perm.id is not None
        assert perm.resource == "menu"
        assert perm.action == "create"
        assert perm.is_system is False

    def test_permission_str_representation(self):
        """Test permission string representation."""
        perm = PermissionFactory(resource="order", action="view")
        assert str(perm) == "order.view"

    def test_permission_code_property(self):
        """Test code property returns resource.action format."""
        perm = PermissionFactory(resource="product", action="delete")
        assert perm.code == "product.delete"

    def test_permission_unique_resource_action(self):
        """Test that resource-action combination must be unique."""
        PermissionFactory(resource="menu", action="create")

        with pytest.raises(IntegrityError):
            PermissionFactory(resource="menu", action="create")


# =============================================================================
# SESSION MODEL TESTS
# =============================================================================


@pytest.mark.django_db
class TestSession:
    """Test cases for Session model."""

    def test_create_session(self):
        """Test creating a session with required fields."""
        user = UserFactory()
        session = SessionFactory(user=user)

        assert session.id is not None
        assert session.user == user
        assert session.refresh_token is not None
        assert session.status == "ACTIVE"
        assert session.expires_at is not None

    def test_session_is_active_property(self):
        """Test is_active property."""
        session = SessionFactory(
            status="ACTIVE",
            expires_at=timezone.now() + timedelta(days=1),
        )
        assert session.is_active is True

        # Expired session
        session.expires_at = timezone.now() - timedelta(hours=1)
        session.save()
        assert session.is_active is False

    def test_session_is_expired_property(self):
        """Test is_expired property."""
        session = SessionFactory(
            expires_at=timezone.now() + timedelta(days=1),
        )
        assert session.is_expired is False

        session.expires_at = timezone.now() - timedelta(hours=1)
        session.save()
        assert session.is_expired is True

    def test_session_revoke(self):
        """Test revoke method updates status and records revocation."""
        session = SessionFactory(status="ACTIVE")
        before_revoke = timezone.now()

        session.revoke(reason="User logged out")
        session.refresh_from_db()

        assert session.status == "REVOKED"
        assert session.revoked_at is not None
        assert session.revoked_at >= before_revoke
        assert session.revoke_reason == "User logged out"

    def test_session_mark_expired(self):
        """Test mark_expired method updates status."""
        session = SessionFactory(status="ACTIVE")

        session.mark_expired()
        session.refresh_from_db()

        assert session.status == "EXPIRED"


# =============================================================================
# USER ROLE MODEL TESTS
# =============================================================================


@pytest.mark.django_db
class TestUserRole:
    """Test cases for UserRole model."""

    def test_create_user_role(self):
        """Test creating a user role assignment."""
        user = UserFactory()
        role = RoleFactory()
        org = OrganizationFactory()

        user_role = UserRoleFactory(user=user, role=role, organization=org)

        assert user_role.id is not None
        assert user_role.user == user
        assert user_role.role == role
        assert user_role.organization == org

    def test_user_role_is_active_property(self):
        """Test is_active property for permanent role."""
        user_role = UserRoleFactory(expires_at=None)
        assert user_role.is_active is True

    def test_user_role_is_active_temporary(self):
        """Test is_active property for temporary role."""
        user_role = UserRoleFactory(
            expires_at=timezone.now() + timedelta(days=1),
        )
        assert user_role.is_active is True

        # Expired
        user_role.expires_at = timezone.now() - timedelta(hours=1)
        user_role.save()
        assert user_role.is_active is False

    def test_user_role_is_expired_property(self):
        """Test is_expired property."""
        # Permanent role never expires
        user_role = UserRoleFactory(expires_at=None)
        assert user_role.is_expired is False

        # Active temporary role
        user_role.expires_at = timezone.now() + timedelta(days=1)
        user_role.save()
        assert user_role.is_expired is False

        # Expired temporary role
        user_role.expires_at = timezone.now() - timedelta(hours=1)
        user_role.save()
        assert user_role.is_expired is True


# =============================================================================
# ROLE PERMISSION MODEL TESTS
# =============================================================================


@pytest.mark.django_db
class TestRolePermission:
    """Test cases for RolePermission model."""

    def test_create_role_permission(self):
        """Test creating a role permission assignment."""
        role = RoleFactory()
        perm = PermissionFactory()

        role_perm = RolePermissionFactory(role=role, permission=perm)

        assert role_perm.id is not None
        assert role_perm.role == role
        assert role_perm.permission == perm
        assert role_perm.conditions == {}

    def test_role_permission_with_conditions(self):
        """Test role permission with CASL-like conditions."""
        role_perm = RolePermissionFactory(
            conditions={"organization_id": "${user.organization_id}"},
        )

        assert role_perm.conditions == {"organization_id": "${user.organization_id}"}


# =============================================================================
# AUDIT LOG MODEL TESTS
# =============================================================================


@pytest.mark.django_db
class TestAuditLog:
    """Test cases for AuditLog model."""

    def test_create_audit_log(self):
        """Test creating an audit log entry."""
        log = AuditLogFactory()

        assert log.id is not None
        assert log.action is not None
        assert log.resource is not None
        assert log.created_at is not None

    def test_audit_log_str_representation(self):
        """Test audit log string representation."""
        user = UserFactory(email="auditor@example.com")
        log = AuditLogFactory(action="CREATE", resource="menu", user=user)
        assert "[CREATE]" in str(log)
        assert "menu" in str(log)
        assert "auditor@example.com" in str(log)

    def test_audit_log_system_action(self):
        """Test audit log for system actions (no user)."""
        log = AuditLogFactory(user=None, action="BULK_UPDATE", resource="products")
        assert "System" in str(log)

    def test_audit_log_has_changes_property(self):
        """Test has_changes property."""
        log = AuditLogFactory(old_values={}, new_values={})
        assert log.has_changes is False

        log.old_values = {"price": "25.00"}
        log.save()
        assert log.has_changes is True

    def test_audit_log_changed_fields_property(self):
        """Test changed_fields property."""
        log = AuditLogFactory(
            old_values={"price": "25.00", "name": "Old Name"},
            new_values={"price": "30.00", "description": "New desc"},
        )

        changed = log.changed_fields
        assert "price" in changed
        assert "name" in changed
        assert "description" in changed

    def test_audit_log_class_method(self):
        """Test AuditLog.log_action class method."""
        user = UserFactory()
        org = OrganizationFactory()

        log = AuditLog.log_action(
            action="CREATE",
            resource="menu",
            resource_id="test-id-123",
            user=user,
            organization=org,
            description="Created a new menu",
            new_values={"name": "Test Menu"},
            ip_address="127.0.0.1",
        )

        assert log.id is not None
        assert log.action == "CREATE"
        assert log.resource == "menu"
        assert log.resource_id == "test-id-123"
        assert log.user == user
        assert log.organization == org
        assert log.new_values == {"name": "Test Menu"}


# =============================================================================
# SOFT DELETE MANAGER TESTS
# =============================================================================


@pytest.mark.django_db
class TestSoftDeleteManager:
    """Test cases for SoftDeleteManager."""

    def test_manager_excludes_deleted_by_default(self):
        """Test that default manager excludes soft-deleted records."""
        org1 = OrganizationFactory()
        org2 = OrganizationFactory()
        org2.soft_delete()

        # Default queryset excludes deleted
        orgs = Organization.objects.all()
        assert org1 in orgs
        assert org2 not in orgs

    def test_all_objects_includes_deleted(self):
        """Test that all_objects manager includes soft-deleted records."""
        org1 = OrganizationFactory()
        org2 = OrganizationFactory()
        org2.soft_delete()

        # all_objects includes everything
        orgs = Organization.all_objects.all()
        assert org1 in orgs
        assert org2 in orgs

    def test_manager_filter_works_correctly(self):
        """Test that filter operations work with soft delete manager."""
        org1 = OrganizationFactory(name="Active Org")
        org2 = OrganizationFactory(name="Deleted Org")
        org2.soft_delete()

        # Filter should only find active
        result = Organization.objects.filter(name__contains="Org")
        assert org1 in result
        assert org2 not in result

    def test_manager_count_excludes_deleted(self):
        """Test that count excludes soft-deleted records."""
        initial_count = Organization.objects.count()
        org = OrganizationFactory()
        assert Organization.objects.count() == initial_count + 1

        org.soft_delete()
        assert Organization.objects.count() == initial_count
        assert Organization.all_objects.count() == initial_count + 1
