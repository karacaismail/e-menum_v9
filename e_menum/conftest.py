"""
Pytest configuration and fixtures for E-Menum Django project.

This module contains shared fixtures used across all test modules.
Fixtures follow pytest-django best practices for Django project testing.
"""

import uuid
from typing import Any, Generator

import pytest
from django.test import Client
from rest_framework.test import APIClient


@pytest.fixture(scope="session")
def django_db_setup(django_db_setup, django_db_blocker):
    """
    Configure test database setup.

    This fixture runs once per test session and sets up the database
    with any required initial data.
    """
    with django_db_blocker.unblock():
        # Import here to avoid import errors before Django setup
        from apps.subscriptions.models import Plan, Feature
        from apps.core.models import Role

        # Create default plans if they don't exist
        plans_data = [
            {
                "slug": "free",
                "name": "Free",
                "tier": "FREE",
                "description": "Free tier for small businesses",
                "price_monthly": 0,
                "price_yearly": 0,
                "is_active": True,
                "is_default": True,
            },
            {
                "slug": "starter",
                "name": "Starter",
                "tier": "STARTER",
                "description": "Starter plan for growing businesses",
                "price_monthly": 2000,
                "price_yearly": 20000,
                "is_active": True,
            },
        ]

        for plan_data in plans_data:
            Plan.objects.get_or_create(
                slug=plan_data["slug"],
                defaults=plan_data
            )

        # Create default roles if they don't exist
        roles_data = [
            {"name": "owner", "display_name": "Owner", "scope": "ORGANIZATION", "is_system": True},
            {"name": "manager", "display_name": "Manager", "scope": "ORGANIZATION", "is_system": True},
            {"name": "staff", "display_name": "Staff", "scope": "ORGANIZATION", "is_system": True},
            {"name": "super_admin", "display_name": "Super Admin", "scope": "PLATFORM", "is_system": True},
        ]

        for role_data in roles_data:
            Role.objects.get_or_create(
                name=role_data["name"],
                scope=role_data["scope"],
                organization=None,
                defaults=role_data
            )


# =============================================================================
# CLIENT FIXTURES
# =============================================================================

@pytest.fixture
def client() -> Client:
    """
    Return a Django test client.

    Use for testing Django views that render templates.
    """
    return Client()


@pytest.fixture
def api_client() -> APIClient:
    """
    Return a DRF API test client.

    Use for testing REST API endpoints.
    """
    return APIClient()


@pytest.fixture
def authenticated_api_client(api_client: APIClient, user) -> APIClient:
    """
    Return an authenticated DRF API test client.

    The client is authenticated with the user fixture.
    """
    api_client.force_authenticate(user=user)
    return api_client


# =============================================================================
# USER FIXTURES
# =============================================================================

@pytest.fixture
@pytest.mark.django_db
def user(db):
    """
    Create and return a test user.

    Returns a basic active user without organization association.
    """
    from apps.core.models import User

    return User.objects.create_user(
        email=f"testuser_{uuid.uuid4().hex[:8]}@example.com",
        password="TestPassword123!",
        first_name="Test",
        last_name="User",
        status="ACTIVE",
    )


@pytest.fixture
@pytest.mark.django_db
def admin_user(db):
    """
    Create and return a Django admin user (superuser).
    """
    from apps.core.models import User

    return User.objects.create_superuser(
        email=f"admin_{uuid.uuid4().hex[:8]}@example.com",
        password="AdminPassword123!",
        first_name="Admin",
        last_name="User",
    )


@pytest.fixture
@pytest.mark.django_db
def staff_user(db, organization):
    """
    Create and return a staff user associated with an organization.
    """
    from apps.core.models import User

    return User.objects.create_user(
        email=f"staff_{uuid.uuid4().hex[:8]}@example.com",
        password="StaffPassword123!",
        first_name="Staff",
        last_name="User",
        status="ACTIVE",
        organization=organization,
    )


# =============================================================================
# ORGANIZATION FIXTURES
# =============================================================================

@pytest.fixture
@pytest.mark.django_db
def organization(db):
    """
    Create and return a test organization.

    Returns an active organization with FREE plan.
    """
    from apps.core.models import Organization
    from apps.subscriptions.models import Plan

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
        }
    )

    return Organization.objects.create(
        name=f"Test Organization {uuid.uuid4().hex[:8]}",
        slug=f"test-org-{uuid.uuid4().hex[:8]}",
        email="org@example.com",
        status="ACTIVE",
        plan=plan,
    )


@pytest.fixture
@pytest.mark.django_db
def organization_with_owner(db, organization):
    """
    Create an organization with an owner user.

    Returns tuple of (organization, owner_user).
    """
    from apps.core.models import User, Role, UserRole

    owner = User.objects.create_user(
        email=f"owner_{uuid.uuid4().hex[:8]}@example.com",
        password="OwnerPassword123!",
        first_name="Organization",
        last_name="Owner",
        status="ACTIVE",
        organization=organization,
    )

    # Assign owner role
    owner_role = Role.objects.filter(name="owner", scope="ORGANIZATION").first()
    if owner_role:
        UserRole.objects.get_or_create(
            user=owner,
            role=owner_role,
            organization=organization,
        )

    return organization, owner


# =============================================================================
# MENU FIXTURES
# =============================================================================

@pytest.fixture
@pytest.mark.django_db
def menu(db, organization):
    """
    Create and return a test menu.
    """
    from apps.menu.models import Menu

    return Menu.objects.create(
        organization=organization,
        name="Test Menu",
        slug=f"test-menu-{uuid.uuid4().hex[:8]}",
        description="A test menu for testing purposes",
        is_published=True,
        is_default=True,
    )


@pytest.fixture
@pytest.mark.django_db
def category(db, organization, menu):
    """
    Create and return a test category.
    """
    from apps.menu.models import Category

    return Category.objects.create(
        organization=organization,
        menu=menu,
        name="Test Category",
        slug=f"test-category-{uuid.uuid4().hex[:8]}",
        description="A test category",
        is_active=True,
    )


@pytest.fixture
@pytest.mark.django_db
def product(db, organization, category):
    """
    Create and return a test product.
    """
    from apps.menu.models import Product
    from decimal import Decimal

    return Product.objects.create(
        organization=organization,
        category=category,
        name="Test Product",
        slug=f"test-product-{uuid.uuid4().hex[:8]}",
        description="A delicious test product",
        base_price=Decimal("29.99"),
        currency="TRY",
        is_active=True,
        is_available=True,
    )


# =============================================================================
# ORDER FIXTURES
# =============================================================================

@pytest.fixture
@pytest.mark.django_db
def zone(db, organization):
    """
    Create and return a test zone.
    """
    from apps.orders.models import Zone

    return Zone.objects.create(
        organization=organization,
        name="Main Hall",
        slug=f"main-hall-{uuid.uuid4().hex[:8]}",
        description="Main dining area",
        is_active=True,
    )


@pytest.fixture
@pytest.mark.django_db
def table(db, organization, zone):
    """
    Create and return a test table.
    """
    from apps.orders.models import Table

    return Table.objects.create(
        organization=organization,
        zone=zone,
        name="Table 1",
        number="1",
        capacity=4,
        status="AVAILABLE",
    )


# =============================================================================
# SUBSCRIPTION FIXTURES
# =============================================================================

@pytest.fixture
@pytest.mark.django_db
def free_plan(db):
    """
    Create and return the FREE plan.
    """
    from apps.subscriptions.models import Plan

    plan, _ = Plan.objects.get_or_create(
        slug="free",
        defaults={
            "name": "Free",
            "tier": "FREE",
            "description": "Free tier",
            "price_monthly": 0,
            "price_yearly": 0,
            "is_active": True,
            "is_default": True,
        }
    )
    return plan


@pytest.fixture
@pytest.mark.django_db
def starter_plan(db):
    """
    Create and return the STARTER plan.
    """
    from apps.subscriptions.models import Plan
    from decimal import Decimal

    plan, _ = Plan.objects.get_or_create(
        slug="starter",
        defaults={
            "name": "Starter",
            "tier": "STARTER",
            "description": "Starter plan for growing businesses",
            "price_monthly": Decimal("2000.00"),
            "price_yearly": Decimal("20000.00"),
            "is_active": True,
        }
    )
    return plan


# =============================================================================
# UTILITY FIXTURES
# =============================================================================

@pytest.fixture
def make_user(db):
    """
    Factory fixture to create multiple users with custom attributes.

    Usage:
        def test_something(make_user):
            user1 = make_user(email="user1@example.com")
            user2 = make_user(email="user2@example.com", first_name="Custom")
    """
    from apps.core.models import User

    def _make_user(**kwargs):
        defaults = {
            "email": f"user_{uuid.uuid4().hex[:8]}@example.com",
            "password": "TestPassword123!",
            "first_name": "Test",
            "last_name": "User",
            "status": "ACTIVE",
        }
        defaults.update(kwargs)
        password = defaults.pop("password")
        user = User(**defaults)
        user.set_password(password)
        user.save()
        return user

    return _make_user


@pytest.fixture
def make_organization(db):
    """
    Factory fixture to create multiple organizations with custom attributes.

    Usage:
        def test_something(make_organization):
            org1 = make_organization(name="Org 1")
            org2 = make_organization(name="Org 2")
    """
    from apps.core.models import Organization
    from apps.subscriptions.models import Plan

    def _make_organization(**kwargs):
        # Ensure FREE plan exists
        plan, _ = Plan.objects.get_or_create(
            slug="free",
            defaults={
                "name": "Free",
                "tier": "FREE",
                "price_monthly": 0,
                "price_yearly": 0,
                "is_active": True,
                "is_default": True,
            }
        )

        defaults = {
            "name": f"Organization {uuid.uuid4().hex[:8]}",
            "slug": f"org-{uuid.uuid4().hex[:8]}",
            "email": "org@example.com",
            "status": "ACTIVE",
            "plan": plan,
        }
        defaults.update(kwargs)
        return Organization.objects.create(**defaults)

    return _make_organization


# =============================================================================
# REQUEST CONTEXT FIXTURES
# =============================================================================

@pytest.fixture
def api_request_factory():
    """
    Return a DRF APIRequestFactory instance.

    Useful for testing serializers and views directly without HTTP.
    """
    from rest_framework.test import APIRequestFactory
    return APIRequestFactory()


@pytest.fixture
def mock_request(api_request_factory, user, organization):
    """
    Create a mock request with user and organization context.

    Useful for testing views that require tenant context.
    """
    request = api_request_factory.get("/")
    request.user = user
    request.organization = organization
    return request


# =============================================================================
# DATABASE HELPERS
# =============================================================================

@pytest.fixture
def clear_cache():
    """
    Clear Django cache after each test.
    """
    from django.core.cache import cache

    yield
    cache.clear()


@pytest.fixture(autouse=False)
def enable_db_logging(settings, caplog):
    """
    Enable database query logging for debugging.

    Usage:
        @pytest.mark.usefixtures("enable_db_logging")
        def test_with_db_logging():
            ...
    """
    import logging
    settings.DEBUG = True
    logging.getLogger("django.db.backends").setLevel(logging.DEBUG)
    yield
    settings.DEBUG = False
