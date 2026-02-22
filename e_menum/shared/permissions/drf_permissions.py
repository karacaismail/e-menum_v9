"""
Django REST Framework permission classes for E-Menum authorization.

This module provides DRF-specific permission classes that integrate with
E-Menum's CASL-like permission system for organization-scoped access control.

Permission Classes:
    - HasOrganizationPermission: Check organization-scoped permissions
    - HasPlatformPermission: Check platform-level permissions
    - IsTenantMember: Verify user belongs to the current tenant
    - IsOwnerOrReadOnly: Object-level ownership permission
    - IsAuthenticatedOrReadOnly: Standard authenticated-or-read-only
    - AllowPublicRead: Allow public read access
    - OrganizationScopedPermission: Factory for action-specific permissions

Permission Format:
    Permissions follow the pattern: {resource}.{action}
    Examples: 'menu.view', 'menu.create', 'order.update', 'user.delete'

Usage:
    from shared.permissions.drf_permissions import HasOrganizationPermission

    # Simple permission check
    class MenuViewSet(viewsets.ModelViewSet):
        permission_classes = [HasOrganizationPermission('menu.manage')]

    # Action-specific permissions
    class MenuViewSet(viewsets.ModelViewSet):
        permission_classes = [OrganizationScopedPermission]

        # Define per-action permissions
        action_permissions = {
            'list': 'menu.view',
            'retrieve': 'menu.view',
            'create': 'menu.create',
            'update': 'menu.update',
            'destroy': 'menu.delete',
        }

    # Factory pattern for quick permission classes
    MenuViewPermission = make_organization_permission('menu.view')
    MenuManagePermission = make_organization_permission('menu.manage')
"""

import logging
from typing import TYPE_CHECKING, Dict, List, Optional, Type, Union

from rest_framework import permissions
from rest_framework.request import Request
from rest_framework.views import APIView

from shared.permissions.abilities import (
    # Core permission checking
    build_ability_for_user,
    check_permission,
    require_permission,
    # Already implemented DRF classes
    AllowPublicRead,
    HasOrganizationPermission,
    HasPlatformPermission,
    IsAuthenticatedOrReadOnly,
    IsOwnerOrReadOnly,
    IsTenantMember,
)

if TYPE_CHECKING:
    from apps.core.models import Organization, User


logger = logging.getLogger(__name__)


# =============================================================================
# Re-export core permission classes for convenience
# =============================================================================

# These are re-exported from abilities.py for cleaner imports
__all__ = [
    # Core DRF permission classes
    'HasOrganizationPermission',
    'HasPlatformPermission',
    'IsTenantMember',
    'IsOwnerOrReadOnly',
    'IsAuthenticatedOrReadOnly',
    'AllowPublicRead',
    # Action-based permission classes
    'OrganizationScopedPermission',
    'ActionBasedPermission',
    # Factory functions
    'make_organization_permission',
    'make_platform_permission',
    'make_composite_permission',
    # Utility functions
    'get_action_permission_code',
]


# =============================================================================
# Action-Based Permission Classes
# =============================================================================

class OrganizationScopedPermission(permissions.BasePermission):
    """
    DRF permission class with action-based permission mapping.

    Provides flexible permission checking based on the current ViewSet action,
    supporting different permissions for list, retrieve, create, update, delete.

    This class reads `action_permissions` from the view to determine which
    permission code to check for each action.

    Attributes:
        default_resource: Default resource name if not specified in view
        default_action_map: Default action-to-permission mapping

    View Attributes Used:
        action_permissions: Dict[str, str] mapping actions to permission codes
        permission_resource: The resource name (e.g., 'menu', 'order')

    Usage:
        class MenuViewSet(viewsets.ModelViewSet):
            permission_classes = [OrganizationScopedPermission]

            # Option 1: Explicit action permissions
            action_permissions = {
                'list': 'menu.view',
                'retrieve': 'menu.view',
                'create': 'menu.create',
                'update': 'menu.update',
                'partial_update': 'menu.update',
                'destroy': 'menu.delete',
                'publish': 'menu.publish',  # Custom action
            }

            # Option 2: Just specify resource, use default action mapping
            permission_resource = 'menu'
    """

    message = "You do not have permission to perform this action."

    # Default mapping from DRF actions to permission action names
    DEFAULT_ACTION_MAP = {
        'list': 'view',
        'retrieve': 'view',
        'create': 'create',
        'update': 'update',
        'partial_update': 'update',
        'destroy': 'delete',
    }

    def has_permission(self, request: Request, view: APIView) -> bool:
        """
        Check if the request has permission based on the view action.

        Args:
            request: The DRF request
            view: The view being accessed

        Returns:
            bool: True if permission is granted
        """
        # Require authentication
        if not request.user or not request.user.is_authenticated:
            return False

        # Superusers have all permissions
        if request.user.is_superuser:
            return True

        # Get the permission code for this action
        permission_code = self._get_permission_code(view)

        if not permission_code:
            # No permission defined for this action - deny by default
            logger.warning(
                "No permission defined for action '%s' on view '%s'",
                getattr(view, 'action', 'unknown'),
                view.__class__.__name__
            )
            return False

        # Get organization context
        organization = getattr(request, 'organization', None)

        # Check permission
        has_perm = check_permission(
            request.user,
            permission_code,
            organization
        )

        if not has_perm:
            logger.debug(
                "Permission denied: user=%s, permission=%s, org=%s",
                request.user.email,
                permission_code,
                organization.id if organization else None
            )

        return has_perm

    def has_object_permission(self, request: Request, view: APIView, obj) -> bool:
        """
        Check object-level permission.

        Args:
            request: The DRF request
            view: The view being accessed
            obj: The object being accessed

        Returns:
            bool: True if permission is granted
        """
        if not request.user or not request.user.is_authenticated:
            return False

        if request.user.is_superuser:
            return True

        permission_code = self._get_permission_code(view)

        if not permission_code:
            return False

        organization = getattr(request, 'organization', None)

        # Verify object belongs to the same organization
        if hasattr(obj, 'organization_id'):
            obj_org_id = obj.organization_id
            if organization and str(obj_org_id) != str(organization.id):
                logger.warning(
                    "Object organization mismatch: obj_org=%s, request_org=%s",
                    obj_org_id,
                    organization.id
                )
                return False

        return check_permission(
            request.user,
            permission_code,
            organization,
            subject=obj
        )

    def _get_permission_code(self, view: APIView) -> Optional[str]:
        """
        Get the permission code for the current view action.

        Args:
            view: The view being accessed

        Returns:
            str or None: The permission code to check
        """
        action = getattr(view, 'action', None)

        # Try explicit action_permissions first
        action_permissions = getattr(view, 'action_permissions', {})
        if action and action in action_permissions:
            return action_permissions[action]

        # Fall back to resource-based permission
        resource = getattr(view, 'permission_resource', None)
        if resource and action:
            permission_action = self.DEFAULT_ACTION_MAP.get(action, action)
            return f"{resource}.{permission_action}"

        return None


class ActionBasedPermission(permissions.BasePermission):
    """
    Permission class that supports multiple permission requirements per action.

    Similar to OrganizationScopedPermission but supports requiring ALL or ANY
    of multiple permissions for an action.

    View Attributes Used:
        action_permission_map: Dict[str, Dict] with permission configuration

    Usage:
        class SensitiveViewSet(viewsets.ModelViewSet):
            permission_classes = [ActionBasedPermission]

            action_permission_map = {
                'create': {
                    'permissions': ['menu.create', 'organization.manage'],
                    'operator': 'all',  # Require ALL permissions
                },
                'destroy': {
                    'permissions': ['menu.delete'],
                    'operator': 'any',  # Require ANY permission
                },
            }
    """

    message = "You do not have the required permissions."

    def has_permission(self, request: Request, view: APIView) -> bool:
        """Check if request has the required permissions for the action."""
        if not request.user or not request.user.is_authenticated:
            return False

        if request.user.is_superuser:
            return True

        action = getattr(view, 'action', None)
        if not action:
            return True

        permission_map = getattr(view, 'action_permission_map', {})
        action_config = permission_map.get(action)

        if not action_config:
            return True  # No specific permissions required

        permissions_list = action_config.get('permissions', [])
        operator = action_config.get('operator', 'all')
        organization = getattr(request, 'organization', None)

        if operator == 'all':
            return all(
                check_permission(request.user, perm, organization)
                for perm in permissions_list
            )
        else:  # 'any'
            return any(
                check_permission(request.user, perm, organization)
                for perm in permissions_list
            )


# =============================================================================
# Factory Functions
# =============================================================================

def make_organization_permission(
    permission_code: str,
    message: str = None
) -> Type[permissions.BasePermission]:
    """
    Factory function to create an organization-scoped permission class.

    Creates a permission class that checks for a specific permission code
    within the organization context.

    Args:
        permission_code: The permission to check (e.g., 'menu.create')
        message: Optional custom error message

    Returns:
        Type[BasePermission]: A permission class

    Usage:
        MenuViewPermission = make_organization_permission('menu.view')
        MenuCreatePermission = make_organization_permission(
            'menu.create',
            message='You cannot create menus'
        )

        class MenuViewSet(viewsets.ModelViewSet):
            permission_classes = [MenuViewPermission]
    """

    class DynamicOrganizationPermission(permissions.BasePermission):
        """Dynamically created organization permission class."""

        def __init__(self):
            self.permission_code = permission_code
            if message:
                self.message = message

        def has_permission(self, request: Request, view: APIView) -> bool:
            if not request.user or not request.user.is_authenticated:
                return False

            if request.user.is_superuser:
                return True

            organization = getattr(request, 'organization', None)
            return check_permission(
                request.user,
                self.permission_code,
                organization
            )

        def has_object_permission(self, request: Request, view: APIView, obj) -> bool:
            if not request.user or not request.user.is_authenticated:
                return False

            if request.user.is_superuser:
                return True

            organization = getattr(request, 'organization', None)
            return check_permission(
                request.user,
                self.permission_code,
                organization,
                subject=obj
            )

    # Set a descriptive name
    DynamicOrganizationPermission.__name__ = f'HasPermission_{permission_code.replace(".", "_")}'
    DynamicOrganizationPermission.__qualname__ = DynamicOrganizationPermission.__name__

    return DynamicOrganizationPermission


def make_platform_permission(
    permission_code: str,
    message: str = None
) -> Type[permissions.BasePermission]:
    """
    Factory function to create a platform-level permission class.

    Creates a permission class that checks for a specific permission code
    at the platform level (not organization-scoped).

    Args:
        permission_code: The permission to check (e.g., 'user.manage')
        message: Optional custom error message

    Returns:
        Type[BasePermission]: A permission class

    Usage:
        UserManagePermission = make_platform_permission('user.manage')

        class PlatformUserView(APIView):
            permission_classes = [UserManagePermission]
    """

    class DynamicPlatformPermission(permissions.BasePermission):
        """Dynamically created platform permission class."""

        def __init__(self):
            self.permission_code = permission_code
            if message:
                self.message = message

        def has_permission(self, request: Request, view: APIView) -> bool:
            if not request.user or not request.user.is_authenticated:
                return False

            if request.user.is_superuser:
                return True

            # Platform permissions don't use organization context
            return check_permission(
                request.user,
                self.permission_code,
                organization=None
            )

    # Set a descriptive name
    DynamicPlatformPermission.__name__ = f'HasPlatformPermission_{permission_code.replace(".", "_")}'
    DynamicPlatformPermission.__qualname__ = DynamicPlatformPermission.__name__

    return DynamicPlatformPermission


def make_composite_permission(
    permission_classes: List[Type[permissions.BasePermission]],
    operator: str = 'all'
) -> Type[permissions.BasePermission]:
    """
    Factory function to create a composite permission from multiple classes.

    Combines multiple permission classes with AND (all) or OR (any) logic.

    Args:
        permission_classes: List of permission classes to combine
        operator: 'all' (AND) or 'any' (OR)

    Returns:
        Type[BasePermission]: A composite permission class

    Usage:
        # Require ALL permissions
        StrictPermission = make_composite_permission([
            IsTenantMember,
            make_organization_permission('menu.manage'),
        ], operator='all')

        # Require ANY permission
        FlexiblePermission = make_composite_permission([
            make_organization_permission('menu.view'),
            make_platform_permission('admin.view'),
        ], operator='any')
    """

    class CompositePermission(permissions.BasePermission):
        """Dynamically created composite permission class."""

        message = "Permission check failed."

        def has_permission(self, request: Request, view: APIView) -> bool:
            results = [
                perm().has_permission(request, view)
                for perm in permission_classes
            ]

            if operator == 'all':
                return all(results)
            return any(results)

        def has_object_permission(self, request: Request, view: APIView, obj) -> bool:
            results = [
                perm().has_object_permission(request, view, obj)
                for perm in permission_classes
            ]

            if operator == 'all':
                return all(results)
            return any(results)

    # Set a descriptive name
    class_names = [cls.__name__ for cls in permission_classes]
    op_symbol = " & " if operator == 'all' else " | "
    CompositePermission.__name__ = f'Composite({op_symbol.join(class_names)})'
    CompositePermission.__qualname__ = CompositePermission.__name__

    return CompositePermission


# =============================================================================
# Utility Functions
# =============================================================================

def get_action_permission_code(
    resource: str,
    action: str,
    action_map: Dict[str, str] = None
) -> str:
    """
    Generate a permission code from resource and action.

    Maps DRF action names to standard permission action names.

    Args:
        resource: The resource name (e.g., 'menu', 'order')
        action: The DRF action name (e.g., 'list', 'create')
        action_map: Optional custom action mapping

    Returns:
        str: The permission code (e.g., 'menu.view')

    Usage:
        code = get_action_permission_code('menu', 'list')  # 'menu.view'
        code = get_action_permission_code('menu', 'create')  # 'menu.create'
    """
    default_map = {
        'list': 'view',
        'retrieve': 'view',
        'create': 'create',
        'update': 'update',
        'partial_update': 'update',
        'destroy': 'delete',
    }

    mapping = {**default_map, **(action_map or {})}
    permission_action = mapping.get(action, action)

    return f"{resource}.{permission_action}"


# =============================================================================
# Convenience Aliases
# =============================================================================

# Common permission class aliases for quick access
IsAuthenticated = permissions.IsAuthenticated
IsAdminUser = permissions.IsAdminUser
AllowAny = permissions.AllowAny
