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

# Permission classes will be implemented in separate files
# and exported here for clean imports

__all__ = []
