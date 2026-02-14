"""
Permission classes and utilities for E-Menum authorization.

This module provides RBAC/ABAC permission handling similar to CASL,
enabling fine-grained access control across the application:

- HasOrganizationPermission: Check organization-scoped permissions
- HasPlatformPermission: Check platform-level permissions
- IsTenantMember: Verify user belongs to the current tenant
- IsOwnerOrReadOnly: Object-level ownership permission

Permission Format:
    Permissions follow the pattern: {resource}.{action}
    Examples: 'menu.view', 'menu.create', 'order.update', 'user.delete'

Role Scopes:
    - PLATFORM: System-wide roles (super_admin, admin, sales, support)
    - ORGANIZATION: Tenant-scoped roles (owner, manager, staff, viewer)

Usage:
    from rest_framework.decorators import permission_classes
    from shared.permissions import HasOrganizationPermission

    @permission_classes([HasOrganizationPermission('menu.view')])
    class MenuViewSet(viewsets.ModelViewSet):
        ...

Integration with django-guardian:
    Object-level permissions are handled via django-guardian's
    ObjectPermissionBackend, configured in AUTHENTICATION_BACKENDS.
"""

from shared.permissions.abilities import (
    # Core classes
    Rule,
    Ability,
    Actions,
    Resources,
    # Builder functions
    build_ability_for_user,
    check_permission,
    require_permission,
    # DRF Permission classes
    HasOrganizationPermission,
    HasPlatformPermission,
    IsTenantMember,
    IsOwnerOrReadOnly,
    IsAuthenticatedOrReadOnly,
    AllowPublicRead,
    # Decorators
    permission_required,
    # Predefined abilities
    get_owner_abilities,
    get_manager_abilities,
    get_staff_abilities,
    get_viewer_abilities,
)


__all__ = [
    # Core classes
    'Rule',
    'Ability',
    'Actions',
    'Resources',
    # Builder functions
    'build_ability_for_user',
    'check_permission',
    'require_permission',
    # DRF Permission classes
    'HasOrganizationPermission',
    'HasPlatformPermission',
    'IsTenantMember',
    'IsOwnerOrReadOnly',
    'IsAuthenticatedOrReadOnly',
    'AllowPublicRead',
    # Decorators
    'permission_required',
    # Predefined abilities
    'get_owner_abilities',
    'get_manager_abilities',
    'get_staff_abilities',
    'get_viewer_abilities',
]
