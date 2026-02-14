"""
Permission classes and utilities for E-Menum authorization.

This module provides RBAC/ABAC permission handling similar to CASL,
enabling fine-grained access control across the application:

- HasOrganizationPermission: Check organization-scoped permissions
- HasPlatformPermission: Check platform-level permissions
- IsTenantMember: Verify user belongs to the current tenant
- IsOwnerOrReadOnly: Object-level ownership permission
- OrganizationScopedPermission: Action-based permission mapping
- ActionBasedPermission: Multi-permission requirements per action

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

    # Or use action-based permissions
    from shared.permissions import OrganizationScopedPermission

    class MenuViewSet(viewsets.ModelViewSet):
        permission_classes = [OrganizationScopedPermission]
        permission_resource = 'menu'

Integration with django-guardian:
    Object-level permissions are handled via django-guardian's
    ObjectPermissionBackend, configured in AUTHENTICATION_BACKENDS.

Factory Functions:
    - make_organization_permission: Create permission class for org-scoped checks
    - make_platform_permission: Create permission class for platform-level checks
    - make_composite_permission: Combine multiple permission classes
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

from shared.permissions.drf_permissions import (
    # Action-based permission classes
    OrganizationScopedPermission,
    ActionBasedPermission,
    # Factory functions
    make_organization_permission,
    make_platform_permission,
    make_composite_permission,
    # Utility functions
    get_action_permission_code,
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
    # DRF Permission classes (basic)
    'HasOrganizationPermission',
    'HasPlatformPermission',
    'IsTenantMember',
    'IsOwnerOrReadOnly',
    'IsAuthenticatedOrReadOnly',
    'AllowPublicRead',
    # DRF Permission classes (action-based)
    'OrganizationScopedPermission',
    'ActionBasedPermission',
    # Factory functions
    'make_organization_permission',
    'make_platform_permission',
    'make_composite_permission',
    # Utility functions
    'get_action_permission_code',
    # Decorators
    'permission_required',
    # Predefined abilities
    'get_owner_abilities',
    'get_manager_abilities',
    'get_staff_abilities',
    'get_viewer_abilities',
]
