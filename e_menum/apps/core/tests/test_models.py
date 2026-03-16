"""Tests for Core app models (User, Organization, Role)."""

import uuid

import pytest
from django.db import IntegrityError

from apps.core.models import Organization, Role, User, UserRole


@pytest.mark.django_db
class TestUserModel:
    """Tests for the User model."""

    def test_create_user(self):
        user = User.objects.create_user(
            email="test@example.com",
            password="SecurePass123!",
            first_name="John",
            last_name="Doe",
        )
        assert user.email == "test@example.com"
        assert user.check_password("SecurePass123!")
        assert user.is_active is True
        assert user.is_staff is False
        assert user.is_superuser is False

    def test_create_superuser(self):
        user = User.objects.create_superuser(
            email="admin@example.com",
            password="AdminPass123!",
        )
        assert user.is_staff is True
        assert user.is_superuser is True

    def test_user_email_unique(self):
        User.objects.create_user(email="dupe@example.com", password="pass123")
        with pytest.raises(IntegrityError):
            User.objects.create_user(email="dupe@example.com", password="pass456")

    def test_user_full_name(self):
        user = User.objects.create_user(
            email="name@example.com",
            password="pass123",
            first_name="Jane",
            last_name="Smith",
        )
        assert user.get_full_name() == "Jane Smith"

    def test_user_soft_delete(self):
        user = User.objects.create_user(email="delete@example.com", password="pass123")
        user.soft_delete()
        assert user.deleted_at is not None


@pytest.mark.django_db
class TestOrganizationModel:
    """Tests for the Organization model."""

    def test_create_organization(self, free_plan):
        org = Organization.objects.create(
            name="Test Restaurant",
            slug=f"test-rest-{uuid.uuid4().hex[:6]}",
            email="rest@example.com",
            status="ACTIVE",
            plan=free_plan,
        )
        assert org.name == "Test Restaurant"
        assert org.status == "ACTIVE"
        assert org.plan.tier == "FREE"

    def test_organization_soft_delete(self, organization):
        organization.soft_delete()
        assert organization.deleted_at is not None

    def test_organization_slug_unique(self, free_plan):
        Organization.objects.create(
            name="Org 1",
            slug="unique-slug",
            email="a@example.com",
            status="ACTIVE",
            plan=free_plan,
        )
        with pytest.raises(IntegrityError):
            Organization.objects.create(
                name="Org 2",
                slug="unique-slug",
                email="b@example.com",
                status="ACTIVE",
                plan=free_plan,
            )


@pytest.mark.django_db
class TestRoleModel:
    """Tests for the Role model."""

    def test_system_roles_exist(self):
        """Verify seed roles exist after db setup."""
        assert Role.objects.filter(name="owner", scope="ORGANIZATION").exists()
        assert Role.objects.filter(name="manager", scope="ORGANIZATION").exists()
        assert Role.objects.filter(name="staff", scope="ORGANIZATION").exists()
        assert Role.objects.filter(name="super_admin", scope="PLATFORM").exists()

    def test_assign_role_to_user(self, organization):
        user = User.objects.create_user(
            email=f"roletest_{uuid.uuid4().hex[:6]}@example.com",
            password="pass123",
            organization=organization,
        )
        owner_role = Role.objects.get(name="owner", scope="ORGANIZATION")
        ur = UserRole.objects.create(
            user=user,
            role=owner_role,
            organization=organization,
        )
        assert ur.user == user
        assert ur.role.name == "owner"


@pytest.mark.django_db
class TestMultiTenancy:
    """Tests for multi-tenancy isolation."""

    def test_users_scoped_to_org(self, make_organization, make_user):
        org1 = make_organization(name="Org A")
        org2 = make_organization(name="Org B")
        u1 = make_user(email="a@org.com", organization=org1)
        u2 = make_user(email="b@org.com", organization=org2)

        org1_users = User.objects.filter(organization=org1)
        org2_users = User.objects.filter(organization=org2)
        assert u1 in org1_users
        assert u2 not in org1_users
        assert u2 in org2_users
