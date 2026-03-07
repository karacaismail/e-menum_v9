"""
Comprehensive RBAC/ABAC permission tests for E-Menum.

This module tests:
A. Ability System (unit tests for each role's permissions)
B. Organization Isolation (multi-tenant permission boundary)
C. Role Assignment (UserRole lifecycle and combination)
D. Permission Decorators and Utilities
E. Plan-Based Gating (subscription feature gating)

The permission system is CASL-inspired:
- Rule(action, resource, inverted, conditions, fields, reason)
- Ability.can(action, resource, subject) / Ability.cannot(...)
- build_ability_for_user(user, organization) builds rules from DB
- Predefined builders: get_owner_abilities(), get_manager_abilities(), etc.

Roles:
  Organization-scoped: owner, manager, staff, viewer
  Platform-scoped: super_admin, admin, sales, support
"""

import uuid
from datetime import timedelta
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from django.core.exceptions import PermissionDenied
from django.utils import timezone

from apps.core.choices import RoleScope
from apps.core.models import (
    Organization,
    Permission,
    Role,
    RolePermission,
    User,
    UserRole,
)
from shared.permissions.abilities import (
    Ability,
    Actions,
    Resources,
    Rule,
    build_ability_for_user,
    check_permission,
    get_manager_abilities,
    get_owner_abilities,
    get_staff_abilities,
    get_viewer_abilities,
    permission_required,
    require_permission,
)


# =============================================================================
# Helper functions
# =============================================================================

def _perm(resource: str, action: str) -> Permission:
    """Get or create a Permission."""
    perm, _ = Permission.objects.get_or_create(
        resource=resource,
        action=action,
        defaults={
            'description': f'{action.title()} {resource}',
            'is_system': True,
        },
    )
    return perm


def _role(name: str, scope=RoleScope.ORGANIZATION) -> Role:
    """Get or create a Role (system, no org)."""
    role, _ = Role.objects.get_or_create(
        name=name,
        scope=scope,
        organization=None,
        defaults={
            'display_name': name.replace('_', ' ').title(),
            'description': f'System role: {name}',
            'is_system': True,
        },
    )
    return role


def _user(organization=None, **kwargs) -> User:
    """Create a test user."""
    defaults = {
        'email': f'u-{uuid.uuid4().hex[:8]}@test.com',
        'password': 'TestPass123!',
        'first_name': 'Test',
        'last_name': 'User',
        'status': 'ACTIVE',
        'organization': organization,
    }
    defaults.update(kwargs)
    password = defaults.pop('password')
    user = User(**defaults)
    user.set_password(password)
    user.save()
    return user


def _org(**kwargs) -> Organization:
    """Create a test organization."""
    defaults = {
        'name': f'Org-{uuid.uuid4().hex[:8]}',
        'slug': f'org-{uuid.uuid4().hex[:8]}',
        'email': f'org-{uuid.uuid4().hex[:6]}@test.com',
        'status': 'ACTIVE',
    }
    defaults.update(kwargs)
    return Organization.objects.create(**defaults)


def _assign(user: User, role: Role, org: Organization = None) -> UserRole:
    """Assign a role to a user."""
    ur, _ = UserRole.objects.get_or_create(
        user=user,
        role=role,
        organization=org,
    )
    return ur


def _grant(role: Role, resource: str, action: str, conditions=None) -> RolePermission:
    """Grant a permission to a role."""
    perm = _perm(resource, action)
    rp, _ = RolePermission.objects.get_or_create(
        role=role,
        permission=perm,
        defaults={'conditions': conditions or {}},
    )
    return rp


def _setup_role_with_permissions(
    role_name: str,
    scope: str,
    permission_map: dict,
    conditions: dict = None,
) -> Role:
    """
    Create a role and assign permissions from a {resource: [actions]} map.

    Args:
        role_name: Internal role name.
        scope: RoleScope value.
        permission_map: Dict of {resource: [action, ...]}.
        conditions: Optional conditions dict applied to each RolePermission.

    Returns:
        The created Role instance.
    """
    role = _role(role_name, scope)
    for resource, actions in permission_map.items():
        for action in actions:
            _grant(role, resource, action, conditions=conditions)
    return role


# =============================================================================
# Predefined permission maps (matching seed_roles.py configuration)
# =============================================================================

OWNER_PERMS = {
    'organization': ['view', 'update'],
    'user': ['manage'],
    'branch': ['manage'],
    'role': ['view', 'list'],
    'menu': ['manage'],
    'category': ['manage'],
    'product': ['manage'],
    'theme': ['manage'],
    'order': ['manage'],
    'table': ['manage'],
    'zone': ['manage'],
    'qr_code': ['manage'],
    'service_request': ['manage'],
    'customer': ['manage'],
    'feedback': ['manage'],
    'subscription': ['view', 'update'],
    'invoice': ['view', 'list', 'export'],
    'analytics': ['view', 'export'],
    'report': ['view', 'list', 'create', 'export'],
    'media': ['manage'],
    'notification': ['manage'],
    'audit_log': ['view', 'list'],
    'ai_generation': ['manage'],
    'settings': ['manage'],
}

MANAGER_PERMS = {
    'organization': ['view'],
    'user': ['view', 'list', 'create', 'update'],
    'branch': ['view', 'list'],
    'menu': ['manage'],
    'category': ['manage'],
    'product': ['manage'],
    'theme': ['view', 'list', 'update'],
    'order': ['manage'],
    'table': ['manage'],
    'zone': ['manage'],
    'qr_code': ['manage'],
    'service_request': ['manage'],
    'customer': ['view', 'list', 'update'],
    'feedback': ['view', 'list', 'manage'],
    'analytics': ['view'],
    'report': ['view', 'list', 'create'],
    'media': ['manage'],
    'notification': ['view', 'list', 'create'],
    'ai_generation': ['view', 'create'],
    'settings': ['view', 'update'],
}

STAFF_PERMS = {
    'organization': ['view'],
    'menu': ['view', 'list'],
    'category': ['view', 'list'],
    'product': ['view', 'list', 'update'],
    'order': ['view', 'list', 'create', 'update'],
    'table': ['view', 'list', 'update'],
    'zone': ['view', 'list'],
    'qr_code': ['view', 'list'],
    'service_request': ['view', 'list', 'create', 'update'],
    'customer': ['view', 'list', 'create'],
    'media': ['view', 'list', 'create'],
    'notification': ['view', 'list'],
}

VIEWER_PERMS = {
    'organization': ['view'],
    'user': ['view', 'list'],
    'branch': ['view', 'list'],
    'menu': ['view', 'list'],
    'category': ['view', 'list'],
    'product': ['view', 'list'],
    'theme': ['view', 'list'],
    'order': ['view', 'list'],
    'table': ['view', 'list'],
    'zone': ['view', 'list'],
    'qr_code': ['view', 'list'],
    'customer': ['view', 'list'],
    'feedback': ['view', 'list'],
    'media': ['view', 'list'],
    'analytics': ['view'],
    'report': ['view', 'list'],
    'notification': ['view', 'list'],
}

SUPER_ADMIN_PERMS = {
    'organization': ['manage'],
    'user': ['manage'],
    'branch': ['manage'],
    'role': ['manage'],
    'menu': ['manage'],
    'category': ['manage'],
    'product': ['manage'],
    'theme': ['manage'],
    'order': ['manage'],
    'table': ['manage'],
    'zone': ['manage'],
    'qr_code': ['manage'],
    'service_request': ['manage'],
    'customer': ['manage'],
    'feedback': ['manage'],
    'subscription': ['manage'],
    'invoice': ['view', 'list', 'create', 'update', 'export'],
    'plan': ['manage'],
    'analytics': ['view', 'export'],
    'report': ['view', 'list', 'create', 'export'],
    'media': ['manage'],
    'notification': ['manage'],
    'audit_log': ['view', 'list', 'export'],
    'ai_generation': ['manage'],
    'ticket': ['manage'],
    'lead': ['manage'],
    'settings': ['manage'],
}


# =============================================================================
# A. Ability System Tests
# =============================================================================

@pytest.mark.django_db
class TestOwnerAbilities:
    """A1. Owner can manage all resources within the organization."""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.org = _org()
        self.role = _setup_role_with_permissions(
            'owner', RoleScope.ORGANIZATION, OWNER_PERMS,
            conditions={'organization_id': '${user.organization_id}'},
        )
        self.user = _user(organization=self.org)
        _assign(self.user, self.role, self.org)
        self.ability = build_ability_for_user(self.user, self.org)

    def test_owner_can_manage_menu(self):
        assert self.ability.can('manage', 'menu')
        assert self.ability.can('view', 'menu')
        assert self.ability.can('create', 'menu')
        assert self.ability.can('update', 'menu')
        assert self.ability.can('delete', 'menu')

    def test_owner_can_manage_product(self):
        assert self.ability.can('manage', 'product')

    def test_owner_can_manage_order(self):
        assert self.ability.can('manage', 'order')

    def test_owner_can_manage_table(self):
        assert self.ability.can('manage', 'table')

    def test_owner_can_manage_qr_code(self):
        assert self.ability.can('manage', 'qr_code')

    def test_owner_can_manage_customer(self):
        assert self.ability.can('manage', 'customer')

    def test_owner_can_view_analytics(self):
        assert self.ability.can('view', 'analytics')

    def test_owner_can_export_analytics(self):
        assert self.ability.can('export', 'analytics')

    def test_owner_can_manage_theme(self):
        assert self.ability.can('manage', 'theme')

    def test_owner_can_manage_settings(self):
        assert self.ability.can('manage', 'settings')

    def test_owner_can_manage_media(self):
        assert self.ability.can('manage', 'media')

    def test_owner_can_view_update_organization(self):
        assert self.ability.can('view', 'organization')
        assert self.ability.can('update', 'organization')

    def test_owner_cannot_delete_organization(self):
        """Owner cannot delete the organization (not granted)."""
        assert self.ability.cannot('delete', 'organization')

    def test_owner_can_manage_user(self):
        assert self.ability.can('manage', 'user')

    def test_owner_can_manage_ai_generation(self):
        assert self.ability.can('manage', 'ai_generation')

    def test_owner_can_view_subscription(self):
        assert self.ability.can('view', 'subscription')
        assert self.ability.can('update', 'subscription')

    def test_owner_cannot_manage_subscription(self):
        """Owner can view/update subscription but not full manage."""
        assert self.ability.cannot('manage', 'subscription')

    def test_owner_can_manage_feedback(self):
        assert self.ability.can('manage', 'feedback')


@pytest.mark.django_db
class TestManagerAbilities:
    """A2. Manager can manage menus/orders/themes but NOT delete org or manage billing."""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.org = _org()
        self.role = _setup_role_with_permissions(
            'manager', RoleScope.ORGANIZATION, MANAGER_PERMS,
            conditions={'organization_id': '${user.organization_id}'},
        )
        self.user = _user(organization=self.org)
        _assign(self.user, self.role, self.org)
        self.ability = build_ability_for_user(self.user, self.org)

    def test_manager_can_manage_menu(self):
        assert self.ability.can('manage', 'menu')
        assert self.ability.can('create', 'menu')
        assert self.ability.can('update', 'menu')
        assert self.ability.can('delete', 'menu')

    def test_manager_can_manage_order(self):
        assert self.ability.can('manage', 'order')

    def test_manager_can_manage_category(self):
        assert self.ability.can('manage', 'category')

    def test_manager_can_manage_product(self):
        assert self.ability.can('manage', 'product')

    def test_manager_can_manage_table(self):
        assert self.ability.can('manage', 'table')

    def test_manager_can_manage_qr_code(self):
        assert self.ability.can('manage', 'qr_code')

    def test_manager_can_manage_media(self):
        assert self.ability.can('manage', 'media')

    def test_manager_can_view_analytics(self):
        assert self.ability.can('view', 'analytics')

    def test_manager_cannot_export_analytics(self):
        """Manager has analytics.view but NOT analytics.export."""
        assert self.ability.cannot('export', 'analytics')

    def test_manager_can_view_update_theme(self):
        assert self.ability.can('view', 'theme')
        assert self.ability.can('update', 'theme')

    def test_manager_cannot_delete_organization(self):
        assert self.ability.cannot('delete', 'organization')

    def test_manager_cannot_manage_subscription(self):
        assert self.ability.cannot('manage', 'subscription')

    def test_manager_cannot_view_subscription(self):
        assert self.ability.cannot('view', 'subscription')

    def test_manager_can_view_customer(self):
        assert self.ability.can('view', 'customer')
        assert self.ability.can('update', 'customer')

    def test_manager_cannot_delete_customer(self):
        assert self.ability.cannot('delete', 'customer')

    def test_manager_can_create_ai_generation(self):
        assert self.ability.can('create', 'ai_generation')
        assert self.ability.can('view', 'ai_generation')

    def test_manager_cannot_manage_ai_generation(self):
        assert self.ability.cannot('manage', 'ai_generation')

    def test_manager_can_create_user(self):
        """Manager can create/update staff users."""
        assert self.ability.can('create', 'user')
        assert self.ability.can('update', 'user')

    def test_manager_cannot_delete_user(self):
        assert self.ability.cannot('delete', 'user')

    def test_manager_cannot_manage_role(self):
        """Manager has no role permissions."""
        assert self.ability.cannot('view', 'role')
        assert self.ability.cannot('manage', 'role')


@pytest.mark.django_db
class TestStaffAbilities:
    """A3. Staff can view/create orders, view menus, update tables, limited access."""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.org = _org()
        self.role = _setup_role_with_permissions(
            'staff', RoleScope.ORGANIZATION, STAFF_PERMS,
            conditions={'organization_id': '${user.organization_id}'},
        )
        self.user = _user(organization=self.org)
        _assign(self.user, self.role, self.org)
        self.ability = build_ability_for_user(self.user, self.org)

    def test_staff_can_view_menu(self):
        assert self.ability.can('view', 'menu')
        assert self.ability.can('list', 'menu')

    def test_staff_can_view_product(self):
        assert self.ability.can('view', 'product')
        assert self.ability.can('list', 'product')

    def test_staff_can_update_product(self):
        """Staff can update product availability."""
        assert self.ability.can('update', 'product')

    def test_staff_can_create_order(self):
        assert self.ability.can('create', 'order')

    def test_staff_can_view_order(self):
        assert self.ability.can('view', 'order')
        assert self.ability.can('list', 'order')

    def test_staff_can_update_order(self):
        assert self.ability.can('update', 'order')

    def test_staff_can_update_table(self):
        assert self.ability.can('view', 'table')
        assert self.ability.can('update', 'table')

    def test_staff_cannot_create_menu(self):
        assert self.ability.cannot('create', 'menu')

    def test_staff_cannot_delete_anything(self):
        assert self.ability.cannot('delete', 'menu')
        assert self.ability.cannot('delete', 'order')
        assert self.ability.cannot('delete', 'product')
        assert self.ability.cannot('delete', 'table')

    def test_staff_cannot_view_analytics(self):
        assert self.ability.cannot('view', 'analytics')

    def test_staff_cannot_manage_menu(self):
        assert self.ability.cannot('manage', 'menu')

    def test_staff_cannot_manage_order(self):
        assert self.ability.cannot('manage', 'order')

    def test_staff_cannot_manage_table(self):
        """Staff can update tables but not full manage."""
        assert self.ability.cannot('manage', 'table')

    def test_staff_cannot_view_subscription(self):
        assert self.ability.cannot('view', 'subscription')

    def test_staff_cannot_view_settings(self):
        assert self.ability.cannot('view', 'settings')

    def test_staff_can_create_service_request(self):
        assert self.ability.can('create', 'service_request')
        assert self.ability.can('update', 'service_request')

    def test_staff_can_view_media(self):
        assert self.ability.can('view', 'media')
        assert self.ability.can('list', 'media')
        assert self.ability.can('create', 'media')

    def test_staff_cannot_delete_media(self):
        assert self.ability.cannot('delete', 'media')


@pytest.mark.django_db
class TestViewerAbilities:
    """A4. Viewer can only view/list, cannot create/update/delete."""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.org = _org()
        self.role = _setup_role_with_permissions(
            'viewer', RoleScope.ORGANIZATION, VIEWER_PERMS,
            conditions={'organization_id': '${user.organization_id}'},
        )
        self.user = _user(organization=self.org)
        _assign(self.user, self.role, self.org)
        self.ability = build_ability_for_user(self.user, self.org)

    def test_viewer_can_view_menu(self):
        assert self.ability.can('view', 'menu')
        assert self.ability.can('list', 'menu')

    def test_viewer_can_view_product(self):
        assert self.ability.can('view', 'product')
        assert self.ability.can('list', 'product')

    def test_viewer_can_view_order(self):
        assert self.ability.can('view', 'order')
        assert self.ability.can('list', 'order')

    def test_viewer_can_view_table(self):
        assert self.ability.can('view', 'table')
        assert self.ability.can('list', 'table')

    def test_viewer_can_view_analytics(self):
        assert self.ability.can('view', 'analytics')

    def test_viewer_cannot_create_anything(self):
        assert self.ability.cannot('create', 'menu')
        assert self.ability.cannot('create', 'product')
        assert self.ability.cannot('create', 'order')
        assert self.ability.cannot('create', 'table')
        assert self.ability.cannot('create', 'category')

    def test_viewer_cannot_update_anything(self):
        assert self.ability.cannot('update', 'menu')
        assert self.ability.cannot('update', 'product')
        assert self.ability.cannot('update', 'order')
        assert self.ability.cannot('update', 'table')

    def test_viewer_cannot_delete_anything(self):
        assert self.ability.cannot('delete', 'menu')
        assert self.ability.cannot('delete', 'product')
        assert self.ability.cannot('delete', 'order')
        assert self.ability.cannot('delete', 'table')

    def test_viewer_cannot_manage_anything(self):
        assert self.ability.cannot('manage', 'menu')
        assert self.ability.cannot('manage', 'order')
        assert self.ability.cannot('manage', 'product')
        assert self.ability.cannot('manage', 'table')

    def test_viewer_cannot_export(self):
        assert self.ability.cannot('export', 'analytics')
        assert self.ability.cannot('export', 'order')

    def test_viewer_can_view_media(self):
        assert self.ability.can('view', 'media')
        assert self.ability.can('list', 'media')

    def test_viewer_cannot_create_media(self):
        assert self.ability.cannot('create', 'media')

    def test_viewer_can_view_customer(self):
        assert self.ability.can('view', 'customer')
        assert self.ability.can('list', 'customer')

    def test_viewer_cannot_update_customer(self):
        assert self.ability.cannot('update', 'customer')

    def test_viewer_cannot_view_settings(self):
        assert self.ability.cannot('view', 'settings')

    def test_viewer_cannot_view_subscription(self):
        assert self.ability.cannot('view', 'subscription')


@pytest.mark.django_db
class TestSuperAdminAbilities:
    """A5. Superuser (is_superuser=True) bypasses all permission checks."""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.org = _org()
        self.superuser = User.objects.create_superuser(
            email=f'super-{uuid.uuid4().hex[:8]}@test.com',
            password='SuperPass123!',
            first_name='Super',
            last_name='Admin',
        )
        self.ability = build_ability_for_user(self.superuser, self.org)

    def test_superuser_can_manage_everything(self):
        """Superuser flag bypasses all rule checks."""
        assert self.ability.can('manage', 'menu')
        assert self.ability.can('manage', 'order')
        assert self.ability.can('manage', 'product')
        assert self.ability.can('manage', 'table')
        assert self.ability.can('manage', 'organization')
        assert self.ability.can('manage', 'subscription')
        assert self.ability.can('manage', 'user')
        assert self.ability.can('manage', 'settings')

    def test_superuser_can_delete_anything(self):
        assert self.ability.can('delete', 'organization')
        assert self.ability.can('delete', 'user')
        assert self.ability.can('delete', 'menu')

    def test_superuser_can_access_any_resource(self):
        """Even resources that are not defined get True for superuser."""
        assert self.ability.can('view', 'nonexistent_resource')
        assert self.ability.can('manage', 'anything')

    def test_superuser_can_access_without_rules(self):
        """Superuser has zero explicit rules but still passes all checks."""
        # The ability may have no rules at all, but is_superuser overrides.
        fresh_ability = Ability(user=self.superuser, organization=self.org)
        assert fresh_ability.can('create', 'menu')
        assert fresh_ability.can('delete', 'organization')


@pytest.mark.django_db
class TestNoRoleAbilities:
    """A6. User with no roles has no permissions whatsoever."""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.org = _org()
        self.user = _user(organization=self.org)
        # No role assignment
        self.ability = build_ability_for_user(self.user, self.org)

    def test_no_role_cannot_view_menu(self):
        assert self.ability.cannot('view', 'menu')

    def test_no_role_cannot_create_order(self):
        assert self.ability.cannot('create', 'order')

    def test_no_role_cannot_manage_anything(self):
        assert self.ability.cannot('manage', 'menu')
        assert self.ability.cannot('manage', 'order')
        assert self.ability.cannot('manage', 'product')

    def test_no_role_has_empty_rules(self):
        assert len(self.ability.rules) == 0

    def test_no_role_cannot_view_analytics(self):
        assert self.ability.cannot('view', 'analytics')

    def test_no_role_cannot_view_settings(self):
        assert self.ability.cannot('view', 'settings')


# =============================================================================
# B. Organization Isolation Tests
# =============================================================================

@pytest.mark.django_db
class TestOrganizationIsolation:
    """B7. User from Org A cannot access Org B resources via conditions."""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.org_a = _org(name='Org Alpha')
        self.org_b = _org(name='Org Beta')

        # Create owner role with org-scoped conditions
        self.owner_role = _setup_role_with_permissions(
            'owner', RoleScope.ORGANIZATION, OWNER_PERMS,
            conditions={'organization_id': '${user.organization_id}'},
        )

        # User belongs to Org A
        self.user_a = _user(organization=self.org_a)
        _assign(self.user_a, self.owner_role, self.org_a)

    def test_user_can_access_own_org(self):
        """User from Org A can access Org A."""
        ability = build_ability_for_user(self.user_a, self.org_a)
        assert ability.can('manage', 'menu')

    def test_user_cannot_access_other_org_via_build_ability(self):
        """When built with Org B context, user from Org A has no org-scoped roles."""
        ability_b = build_ability_for_user(self.user_a, self.org_b)
        # User has no UserRole with organization=org_b, so no rules.
        assert ability_b.cannot('view', 'menu')
        assert ability_b.cannot('manage', 'menu')

    def test_condition_check_blocks_cross_org_subject(self):
        """Condition-based subject check blocks cross-tenant access."""
        _ability = build_ability_for_user(self.user_a, self.org_a)

        # Create a mock subject belonging to Org B
        subject_b = SimpleNamespace(organization_id=self.org_b.id)
        subject_a = SimpleNamespace(organization_id=self.org_a.id)

        # Only rules with conditions will trigger subject checks.
        # Since all rules from build_ability_for_user have conditions from
        # the RolePermission table, subject checks apply when a subject
        # is passed.

        # Build a manual ability with condition-bearing rules to verify
        manual_ability = Ability(user=self.user_a, organization=self.org_a)
        manual_ability.add_rule(Rule(
            action='manage',
            resource='menu',
            conditions={'organization_id': str(self.org_a.id)},
        ))

        assert manual_ability.can('manage', 'menu', subject_a)
        assert manual_ability.cannot('manage', 'menu', subject_b)


@pytest.mark.django_db
class TestCrossOrgPermissionDenied:
    """B8. Explicitly verify cross-tenant denial."""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.org_a = _org(name='Org Gamma')
        self.org_b = _org(name='Org Delta')

        self.owner_role = _setup_role_with_permissions(
            'owner', RoleScope.ORGANIZATION, OWNER_PERMS,
            conditions={'organization_id': '${user.organization_id}'},
        )

        self.user_a = _user(organization=self.org_a)
        _assign(self.user_a, self.owner_role, self.org_a)

        self.user_b = _user(organization=self.org_b)
        _assign(self.user_b, self.owner_role, self.org_b)

    def test_user_a_denied_in_org_b_context(self):
        ability = build_ability_for_user(self.user_a, self.org_b)
        assert ability.cannot('view', 'menu')
        assert ability.cannot('manage', 'order')

    def test_user_b_denied_in_org_a_context(self):
        ability = build_ability_for_user(self.user_b, self.org_a)
        assert ability.cannot('view', 'menu')
        assert ability.cannot('manage', 'order')

    def test_user_a_allowed_in_org_a_context(self):
        ability = build_ability_for_user(self.user_a, self.org_a)
        assert ability.can('manage', 'menu')

    def test_user_b_allowed_in_org_b_context(self):
        ability = build_ability_for_user(self.user_b, self.org_b)
        assert ability.can('manage', 'menu')

    def test_check_permission_utility_cross_org(self):
        """check_permission also enforces org isolation."""
        # Owner in Org A
        assert check_permission(self.user_a, 'menu.manage', self.org_a)
        # Denied in Org B (no role assignment for org_b)
        assert not check_permission(self.user_a, 'menu.manage', self.org_b)


# =============================================================================
# C. Role Assignment Tests
# =============================================================================

@pytest.mark.django_db
class TestUserRoleAssignment:
    """C9. Creating UserRole properly grants permissions."""

    def test_role_assignment_grants_permissions(self):
        org = _org()
        role = _setup_role_with_permissions(
            'staff', RoleScope.ORGANIZATION, STAFF_PERMS,
        )
        user = _user(organization=org)

        # Before assignment: no permissions
        ability_before = build_ability_for_user(user, org)
        assert ability_before.cannot('view', 'menu')

        # Assign the role
        _assign(user, role, org)

        # After assignment: has permissions
        ability_after = build_ability_for_user(user, org)
        assert ability_after.can('view', 'menu')
        assert ability_after.can('create', 'order')

    def test_role_assignment_creates_user_role_record(self):
        org = _org()
        role = _role('test_role')
        user = _user(organization=org)

        assert UserRole.objects.filter(user=user, role=role).count() == 0
        _assign(user, role, org)
        assert UserRole.objects.filter(user=user, role=role, organization=org).count() == 1

    def test_role_assignment_is_active_property(self):
        org = _org()
        role = _role('test_active_role')
        user = _user(organization=org)

        ur = _assign(user, role, org)
        assert ur.is_active is True
        assert ur.is_expired is False


@pytest.mark.django_db
class TestExpiredRoleAssignment:
    """C10. Expired UserRole should not grant permissions."""

    def test_expired_role_is_not_active(self):
        org = _org()
        role = _role('temp_role')
        user = _user(organization=org)

        ur = UserRole.objects.create(
            user=user,
            role=role,
            organization=org,
            expires_at=timezone.now() - timedelta(days=1),
        )

        assert ur.is_active is False
        assert ur.is_expired is True

    def test_expired_role_does_not_grant_permissions(self):
        """build_ability_for_user filters out expired role assignments."""
        org = _org()
        role = _setup_role_with_permissions(
            'temp_manager', RoleScope.ORGANIZATION, MANAGER_PERMS,
        )
        user = _user(organization=org)

        # Create expired assignment
        UserRole.objects.create(
            user=user,
            role=role,
            organization=org,
            expires_at=timezone.now() - timedelta(hours=1),
        )

        ability = build_ability_for_user(user, org)
        # Expired role should not grant anything
        assert ability.cannot('manage', 'menu')
        assert ability.cannot('create', 'order')

    def test_future_expiry_role_is_active(self):
        org = _org()
        role = _setup_role_with_permissions(
            'future_temp_role', RoleScope.ORGANIZATION, STAFF_PERMS,
        )
        user = _user(organization=org)

        ur = UserRole.objects.create(
            user=user,
            role=role,
            organization=org,
            expires_at=timezone.now() + timedelta(days=30),
        )

        assert ur.is_active is True
        ability = build_ability_for_user(user, org)
        assert ability.can('view', 'menu')

    def test_no_expiry_role_is_always_active(self):
        org = _org()
        role = _role('perm_role')
        user = _user(organization=org)

        ur = UserRole.objects.create(
            user=user,
            role=role,
            organization=org,
            expires_at=None,
        )

        assert ur.is_active is True
        assert ur.is_expired is False


@pytest.mark.django_db
class TestMultipleRoles:
    """C11. User with multiple roles gets combined abilities."""

    def test_combined_roles_union_permissions(self):
        """Owner + Viewer = union of both (owner already includes viewer)."""
        org = _org()
        owner_role = _setup_role_with_permissions(
            'owner', RoleScope.ORGANIZATION, OWNER_PERMS,
        )
        viewer_role = _setup_role_with_permissions(
            'viewer', RoleScope.ORGANIZATION, VIEWER_PERMS,
        )
        user = _user(organization=org)

        _assign(user, owner_role, org)
        _assign(user, viewer_role, org)

        ability = build_ability_for_user(user, org)
        # Has owner capabilities
        assert ability.can('manage', 'menu')
        assert ability.can('manage', 'order')
        # Also has viewer capabilities (subset of owner)
        assert ability.can('view', 'analytics')

    def test_staff_plus_manager_gets_manager_capabilities(self):
        """Staff + Manager combined gives all manager capabilities."""
        org = _org()
        staff_role = _setup_role_with_permissions(
            'staff', RoleScope.ORGANIZATION, STAFF_PERMS,
        )
        manager_role = _setup_role_with_permissions(
            'manager', RoleScope.ORGANIZATION, MANAGER_PERMS,
        )
        user = _user(organization=org)

        _assign(user, staff_role, org)
        _assign(user, manager_role, org)

        ability = build_ability_for_user(user, org)
        # Manager capabilities
        assert ability.can('manage', 'menu')
        assert ability.can('manage', 'order')
        # Staff capabilities preserved
        assert ability.can('create', 'order')
        assert ability.can('update', 'table')

    def test_viewer_plus_staff_can_create_orders(self):
        """Viewer alone cannot create, but viewer+staff can."""
        org = _org()
        viewer_role = _setup_role_with_permissions(
            'viewer', RoleScope.ORGANIZATION, VIEWER_PERMS,
        )
        staff_role = _setup_role_with_permissions(
            'staff', RoleScope.ORGANIZATION, STAFF_PERMS,
        )
        user = _user(organization=org)

        _assign(user, viewer_role, org)
        _assign(user, staff_role, org)

        ability = build_ability_for_user(user, org)
        assert ability.can('view', 'menu')
        assert ability.can('create', 'order')
        # analytics.view from viewer
        assert ability.can('view', 'analytics')


# =============================================================================
# D. Permission Decorator Tests
# =============================================================================

@pytest.mark.django_db
class TestPermissionRequiredDecorator:
    """D12. permission_required decorator allows/denies correctly."""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.org = _org()
        self.manager_role = _setup_role_with_permissions(
            'manager', RoleScope.ORGANIZATION, MANAGER_PERMS,
        )
        self.viewer_role = _setup_role_with_permissions(
            'viewer', RoleScope.ORGANIZATION, VIEWER_PERMS,
        )

    def test_decorator_allows_permitted_user(self):
        """Manager with menu.manage passes the decorator."""
        user = _user(organization=self.org)
        _assign(user, self.manager_role, self.org)

        @permission_required('menu.manage')
        def my_view(request):
            return 'ok'

        request = MagicMock()
        request.user = user
        request.organization = self.org

        assert my_view(request) == 'ok'

    def test_decorator_denies_unpermitted_user(self):
        """Viewer without menu.create is denied."""
        user = _user(organization=self.org)
        _assign(user, self.viewer_role, self.org)

        @permission_required('menu.create')
        def my_view(request):
            return 'ok'

        request = MagicMock()
        request.user = user
        request.organization = self.org

        with pytest.raises(PermissionDenied):
            my_view(request)

    def test_decorator_denies_user_with_no_roles(self):
        """User with no roles is denied for any permission."""
        user = _user(organization=self.org)

        @permission_required('menu.view')
        def my_view(request):
            return 'ok'

        request = MagicMock()
        request.user = user
        request.organization = self.org

        with pytest.raises(PermissionDenied):
            my_view(request)

    def test_decorator_allows_superuser(self):
        """Superuser always passes the decorator."""
        superuser = User.objects.create_superuser(
            email=f'su-{uuid.uuid4().hex[:8]}@test.com',
            password='SuperPass123!',
            first_name='Super',
            last_name='Admin',
        )

        @permission_required('organization.delete')
        def my_view(request):
            return 'ok'

        request = MagicMock()
        request.user = superuser
        request.organization = self.org

        assert my_view(request) == 'ok'


@pytest.mark.django_db
class TestCheckPermissionUtility:
    """D13. check_permission() returns correct bool for each role."""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.org = _org()
        self.owner_role = _setup_role_with_permissions(
            'owner', RoleScope.ORGANIZATION, OWNER_PERMS,
        )
        self.manager_role = _setup_role_with_permissions(
            'manager', RoleScope.ORGANIZATION, MANAGER_PERMS,
        )
        self.staff_role = _setup_role_with_permissions(
            'staff', RoleScope.ORGANIZATION, STAFF_PERMS,
        )
        self.viewer_role = _setup_role_with_permissions(
            'viewer', RoleScope.ORGANIZATION, VIEWER_PERMS,
        )

    def test_check_permission_owner(self):
        user = _user(organization=self.org)
        _assign(user, self.owner_role, self.org)

        assert check_permission(user, 'menu.manage', self.org) is True
        assert check_permission(user, 'order.manage', self.org) is True
        assert check_permission(user, 'settings.manage', self.org) is True

    def test_check_permission_manager(self):
        user = _user(organization=self.org)
        _assign(user, self.manager_role, self.org)

        assert check_permission(user, 'menu.manage', self.org) is True
        assert check_permission(user, 'subscription.manage', self.org) is False
        assert check_permission(user, 'organization.delete', self.org) is False

    def test_check_permission_staff(self):
        user = _user(organization=self.org)
        _assign(user, self.staff_role, self.org)

        assert check_permission(user, 'order.create', self.org) is True
        assert check_permission(user, 'menu.view', self.org) is True
        assert check_permission(user, 'menu.create', self.org) is False
        assert check_permission(user, 'analytics.view', self.org) is False

    def test_check_permission_viewer(self):
        user = _user(organization=self.org)
        _assign(user, self.viewer_role, self.org)

        assert check_permission(user, 'menu.view', self.org) is True
        assert check_permission(user, 'menu.create', self.org) is False
        assert check_permission(user, 'order.create', self.org) is False

    def test_check_permission_invalid_format(self):
        """Invalid permission code format raises ValueError."""
        user = _user(organization=self.org)
        with pytest.raises(ValueError, match="Invalid permission code format"):
            check_permission(user, 'invalid', self.org)

    def test_require_permission_raises(self):
        """require_permission raises PermissionDenied on failure."""
        user = _user(organization=self.org)
        _assign(user, self.viewer_role, self.org)

        with pytest.raises(PermissionDenied):
            require_permission(user, 'menu.create', self.org)

    def test_require_permission_passes(self):
        """require_permission does not raise when permission is granted."""
        user = _user(organization=self.org)
        _assign(user, self.owner_role, self.org)

        # Should not raise
        require_permission(user, 'menu.manage', self.org)

    def test_check_permission_unauthenticated_user(self):
        """Unauthenticated user (AnonymousUser-like) gets no permissions."""
        from django.contrib.auth.models import AnonymousUser
        anon = AnonymousUser()
        assert check_permission(anon, 'menu.view', self.org) is False


# =============================================================================
# E. Plan-Based Gating Tests
# =============================================================================

@pytest.mark.django_db
class TestPlanBasedRestriction:
    """E14. If feature is disabled by plan, permission denied even if role allows."""

    def _setup_plan_gating(self):
        """Set up feature-permission gating infrastructure."""
        from apps.subscriptions.choices import FeatureType
        from apps.subscriptions.models import (
            Feature,
            FeaturePermission,
        )

        # Create a feature
        feature, _ = Feature.objects.get_or_create(
            code='ai_content_generation_test',
            defaults={
                'name': 'AI Content Generation Test',
                'description': 'Test feature for AI',
                'feature_type': FeatureType.BOOLEAN,
                'default_value': {'enabled': False},
                'category': 'ai',
                'sort_order': 0,
            },
        )

        # Create the gated permission
        permission = _perm('ai_generation', 'create')

        # Create the gate
        FeaturePermission.objects.get_or_create(
            feature=feature,
            permission=permission,
        )

        # Create a role that grants this permission
        role = _setup_role_with_permissions(
            'ai_test_manager', RoleScope.ORGANIZATION,
            {'ai_generation': ['create'], 'menu': ['manage']},
        )

        return feature, permission, role

    def test_free_plan_blocks_gated_permission(self):
        """Feature disabled on Free plan blocks the permission."""
        from apps.subscriptions.choices import PlanTier, SubscriptionStatus
        from apps.subscriptions.models import Plan, PlanFeature, Subscription

        feature, perm, role = self._setup_plan_gating()

        # Create free plan with feature DISABLED
        free_plan, _ = Plan.objects.get_or_create(
            slug='free-gating-test',
            defaults={
                'name': 'Free Gating Test',
                'tier': PlanTier.FREE,
                'price_monthly': Decimal('0.00'),
                'price_yearly': Decimal('0.00'),
                'is_active': True,
            },
        )
        PlanFeature.objects.get_or_create(
            plan=free_plan,
            feature=feature,
            defaults={'value': {'enabled': False}, 'is_enabled': False, 'sort_order': 0},
        )

        org = _org()
        sub = Subscription.objects.create(
            organization=org,
            plan=free_plan,
            status=SubscriptionStatus.ACTIVE,
            billing_period='MONTHLY',
            current_price=Decimal('0.00'),
            currency='TRY',
        )
        org.subscription = sub
        org.save()

        user = _user(organization=org)
        _assign(user, role, org)

        ability = build_ability_for_user(user, org)
        # ai_generation.create is gated by ai_content_generation_test which is disabled
        assert ability.cannot('create', 'ai_generation')
        # menu.manage is NOT gated, so it should still work
        assert ability.can('manage', 'menu')

    def test_paid_plan_allows_gated_permission(self):
        """Feature enabled on paid plan allows the permission."""
        from apps.subscriptions.choices import PlanTier, SubscriptionStatus
        from apps.subscriptions.models import Plan, PlanFeature, Subscription

        feature, perm, role = self._setup_plan_gating()

        pro_plan, _ = Plan.objects.get_or_create(
            slug=f'pro-gating-test-{uuid.uuid4().hex[:6]}',
            defaults={
                'name': 'Professional Gating Test',
                'tier': PlanTier.PROFESSIONAL,
                'price_monthly': Decimal('6000.00'),
                'price_yearly': Decimal('60000.00'),
                'is_active': True,
            },
        )
        PlanFeature.objects.get_or_create(
            plan=pro_plan,
            feature=feature,
            defaults={'value': {'enabled': True}, 'is_enabled': True, 'sort_order': 0},
        )

        org = _org()
        sub = Subscription.objects.create(
            organization=org,
            plan=pro_plan,
            status=SubscriptionStatus.ACTIVE,
            billing_period='MONTHLY',
            current_price=Decimal('6000.00'),
            currency='TRY',
        )
        org.subscription = sub
        org.save()

        user = _user(organization=org)
        _assign(user, role, org)

        ability = build_ability_for_user(user, org)
        assert ability.can('create', 'ai_generation')

    def test_superuser_bypasses_plan_gating(self):
        """Superuser bypasses plan-based feature gating."""
        from apps.subscriptions.choices import PlanTier, SubscriptionStatus
        from apps.subscriptions.models import Plan, PlanFeature, Subscription

        feature, perm, role = self._setup_plan_gating()

        free_plan, _ = Plan.objects.get_or_create(
            slug='free-super-gating',
            defaults={
                'name': 'Free Super Gating',
                'tier': PlanTier.FREE,
                'price_monthly': Decimal('0.00'),
                'price_yearly': Decimal('0.00'),
                'is_active': True,
            },
        )
        PlanFeature.objects.get_or_create(
            plan=free_plan,
            feature=feature,
            defaults={'value': {'enabled': False}, 'is_enabled': False, 'sort_order': 0},
        )

        org = _org()
        sub = Subscription.objects.create(
            organization=org,
            plan=free_plan,
            status=SubscriptionStatus.ACTIVE,
            billing_period='MONTHLY',
            current_price=Decimal('0.00'),
            currency='TRY',
        )
        org.subscription = sub
        org.save()

        superuser = User.objects.create_superuser(
            email=f'su-plan-{uuid.uuid4().hex[:8]}@test.com',
            password='SuperPass123!',
            first_name='Super',
            last_name='Admin',
        )

        ability = build_ability_for_user(superuser, org)
        # Superuser bypasses everything
        assert ability.can('create', 'ai_generation')

    def test_non_gated_permission_unaffected_by_plan(self):
        """Permissions not linked via FeaturePermission are unaffected."""
        from apps.subscriptions.choices import PlanTier, SubscriptionStatus
        from apps.subscriptions.models import Plan, PlanFeature, Subscription

        feature, perm, role = self._setup_plan_gating()

        free_plan, _ = Plan.objects.get_or_create(
            slug='free-nongated-test',
            defaults={
                'name': 'Free NonGated',
                'tier': PlanTier.FREE,
                'price_monthly': Decimal('0.00'),
                'price_yearly': Decimal('0.00'),
                'is_active': True,
            },
        )
        PlanFeature.objects.get_or_create(
            plan=free_plan,
            feature=feature,
            defaults={'value': {'enabled': False}, 'is_enabled': False, 'sort_order': 0},
        )

        org = _org()
        sub = Subscription.objects.create(
            organization=org,
            plan=free_plan,
            status=SubscriptionStatus.ACTIVE,
            billing_period='MONTHLY',
            current_price=Decimal('0.00'),
            currency='TRY',
        )
        org.subscription = sub
        org.save()

        user = _user(organization=org)
        _assign(user, role, org)

        ability = build_ability_for_user(user, org)
        # ai_generation.create blocked by plan
        assert ability.cannot('create', 'ai_generation')
        # menu.manage is not gated by any feature -> allowed
        assert ability.can('manage', 'menu')


# =============================================================================
# Additional Edge Case Tests
# =============================================================================

@pytest.mark.django_db
class TestAbilityRuleResolution:
    """Tests for CASL-like rule resolution mechanics."""

    def test_manage_action_matches_any_action(self):
        """A 'manage' action rule matches any specific action."""
        ability = Ability(user=None)
        ability.add_rule(Rule(action='manage', resource='menu'))

        assert ability.can('view', 'menu')
        assert ability.can('create', 'menu')
        assert ability.can('update', 'menu')
        assert ability.can('delete', 'menu')
        assert ability.can('publish', 'menu')

    def test_all_resource_matches_any_resource(self):
        """A rule with resource='all' matches any resource."""
        ability = Ability(user=None)
        ability.add_rule(Rule(action='view', resource='all'))

        assert ability.can('view', 'menu')
        assert ability.can('view', 'order')
        assert ability.can('view', 'settings')
        # But not other actions
        assert ability.cannot('create', 'menu')

    def test_manage_all_matches_everything(self):
        """action=manage + resource=all matches any action on any resource."""
        ability = Ability(user=None)
        ability.add_rule(Rule(action='manage', resource='all'))

        assert ability.can('create', 'menu')
        assert ability.can('delete', 'order')
        assert ability.can('export', 'analytics')

    def test_last_matching_rule_wins(self):
        """When multiple rules match, the last one determines the outcome."""
        ability = Ability(user=None)
        ability.add_rule(Rule(action='view', resource='menu'))  # can
        ability.add_rule(Rule(action='view', resource='menu', inverted=True))  # cannot

        # Last rule (cannot) wins
        assert ability.cannot('view', 'menu')

    def test_cannot_then_can_re_enables(self):
        """A 'can' rule after 'cannot' re-enables the permission."""
        ability = Ability(user=None)
        ability.add_rule(Rule(action='view', resource='menu', inverted=True))
        ability.add_rule(Rule(action='view', resource='menu'))

        assert ability.can('view', 'menu')

    def test_cache_cleared_on_add_rule(self):
        """Adding a rule clears the permission cache."""
        ability = Ability(user=None)
        ability.add_rule(Rule(action='view', resource='menu'))
        assert ability.can('view', 'menu')

        # Cache populated
        assert len(ability._permission_cache) > 0

        # Adding a new rule clears cache
        ability.add_rule(Rule(action='view', resource='menu', inverted=True))
        assert len(ability._permission_cache) == 0

        # New check uses the new rule set
        assert ability.cannot('view', 'menu')

    def test_get_permitted_fields(self):
        """get_permitted_fields returns field list from rules with fields."""
        ability = Ability(user=None)
        ability.add_rule(Rule(
            action='view',
            resource='user',
            fields=['email', 'first_name'],
        ))
        ability.add_rule(Rule(
            action='view',
            resource='user',
            fields=['last_name'],
        ))

        fields = ability.get_permitted_fields('view', 'user')
        assert set(fields) == {'email', 'first_name', 'last_name'}

    def test_get_permitted_fields_none_when_no_field_rules(self):
        """Returns None when no rules have field restrictions."""
        ability = Ability(user=None)
        ability.add_rule(Rule(action='view', resource='menu'))

        fields = ability.get_permitted_fields('view', 'menu')
        assert fields is None


@pytest.mark.django_db
class TestPredefinedAbilityBuilders:
    """Tests for get_owner_abilities(), get_manager_abilities(), etc."""

    def test_get_owner_abilities_returns_manage_all(self):
        rules = get_owner_abilities()
        assert len(rules) == 1
        assert rules[0].action == 'manage'
        assert rules[0].resource == 'all'
        assert 'organization_id' in rules[0].conditions

    def test_get_manager_abilities_includes_menu_manage(self):
        rules = get_manager_abilities()
        menu_manage = [r for r in rules if r.resource == 'menu' and r.action == 'manage']
        assert len(menu_manage) == 1

    def test_get_manager_abilities_includes_analytics_view(self):
        rules = get_manager_abilities()
        analytics_view = [r for r in rules if r.resource == 'analytics' and r.action == 'view']
        assert len(analytics_view) == 1

    def test_get_staff_abilities_includes_order_create(self):
        rules = get_staff_abilities()
        order_create = [r for r in rules if r.resource == 'order' and r.action == 'create']
        assert len(order_create) == 1

    def test_get_staff_abilities_does_not_include_menu_create(self):
        rules = get_staff_abilities()
        menu_create = [r for r in rules if r.resource == 'menu' and r.action == 'create']
        assert len(menu_create) == 0

    def test_get_viewer_abilities_read_only(self):
        rules = get_viewer_abilities()
        for rule in rules:
            assert rule.action in ('view', 'list'), (
                f"Viewer should only have view/list, found: {rule.action} on {rule.resource}"
            )

    def test_get_viewer_abilities_no_inverted_rules(self):
        rules = get_viewer_abilities()
        inverted = [r for r in rules if r.inverted]
        assert len(inverted) == 0

    def test_predefined_abilities_direct_usage(self):
        """Predefined rules can be added directly to an Ability."""
        ability = Ability(user=None)
        for rule in get_staff_abilities():
            ability.add_rule(rule)

        assert ability.can('view', 'menu')
        assert ability.can('create', 'order')
        assert ability.cannot('create', 'menu')
        assert ability.cannot('delete', 'order')


@pytest.mark.django_db
class TestRuleDataclass:
    """Tests for the Rule dataclass behavior."""

    def test_rule_matches_action_exact(self):
        rule = Rule(action='create', resource='menu')
        assert rule.matches_action('create')
        assert not rule.matches_action('delete')

    def test_rule_matches_action_manage(self):
        """manage action matches any action."""
        rule = Rule(action='manage', resource='menu')
        assert rule.matches_action('create')
        assert rule.matches_action('delete')
        assert rule.matches_action('view')
        assert rule.matches_action('manage')

    def test_rule_matches_resource_exact(self):
        rule = Rule(action='create', resource='menu')
        assert rule.matches_resource('menu')
        assert not rule.matches_resource('order')

    def test_rule_matches_resource_all(self):
        """resource 'all' matches any resource."""
        rule = Rule(action='create', resource='all')
        assert rule.matches_resource('menu')
        assert rule.matches_resource('order')
        assert rule.matches_resource('settings')

    def test_rule_default_values(self):
        rule = Rule(action='view', resource='menu')
        assert rule.inverted is False
        assert rule.conditions == {}
        assert rule.fields is None
        assert rule.reason is None

    def test_inverted_rule(self):
        rule = Rule(action='view', resource='menu', inverted=True)
        assert rule.inverted is True

    def test_rule_with_conditions(self):
        rule = Rule(
            action='view',
            resource='menu',
            conditions={'organization_id': '${user.organization_id}'},
        )
        assert 'organization_id' in rule.conditions

    def test_rule_with_reason(self):
        rule = Rule(
            action='create',
            resource='ai_generation',
            inverted=True,
            reason='Feature not included in plan',
        )
        assert rule.reason == 'Feature not included in plan'


@pytest.mark.django_db
class TestActionsAndResourcesConstants:
    """Tests for the Actions and Resources constant classes."""

    def test_standard_actions_exist(self):
        assert Actions.VIEW == 'view'
        assert Actions.LIST == 'list'
        assert Actions.CREATE == 'create'
        assert Actions.UPDATE == 'update'
        assert Actions.DELETE == 'delete'
        assert Actions.MANAGE == 'manage'
        assert Actions.PUBLISH == 'publish'
        assert Actions.EXPORT == 'export'
        assert Actions.IMPORT == 'import'

    def test_standard_resources_exist(self):
        assert Resources.ORGANIZATION == 'organization'
        assert Resources.USER == 'user'
        assert Resources.MENU == 'menu'
        assert Resources.PRODUCT == 'product'
        assert Resources.ORDER == 'order'
        assert Resources.TABLE == 'table'
        assert Resources.QRCODE == 'qrcode'
        assert Resources.CUSTOMER == 'customer'
        assert Resources.ANALYTICS == 'analytics'
        assert Resources.THEME == 'theme'
        assert Resources.MEDIA == 'media'
        assert Resources.SUBSCRIPTION == 'subscription'
