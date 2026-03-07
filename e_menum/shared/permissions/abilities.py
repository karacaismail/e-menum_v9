"""
CASL-like permission abilities system for E-Menum.

This module implements a CASL-inspired permission system for Django that provides:
- Ability building from user roles and permissions
- Attribute-based access control (ABAC) with conditions
- Role-based access control (RBAC) via Role/Permission models
- Integration with Django REST Framework permissions
- Multi-tenant (organization) scoped permission checking

Permission Format:
    Permissions follow the pattern: {resource}.{action}
    Examples: 'menu.view', 'menu.create', 'order.update', 'user.delete'

Role Scopes:
    - PLATFORM: System-wide roles (super_admin, admin, sales, support)
    - ORGANIZATION: Tenant-scoped roles (owner, manager, staff, viewer)

Usage:
    from shared.permissions.abilities import (
        build_ability_for_user,
        check_permission,
        HasOrganizationPermission,
    )

    # Build ability for a user
    ability = build_ability_for_user(user, organization)

    # Check permission
    if ability.can('create', 'menu'):
        # User can create menus

    # DRF permission class
    @permission_classes([HasOrganizationPermission('menu.create')])
    class MenuCreateView(APIView):
        ...

CASL Concepts Mapped to Django:
    - AbilityBuilder -> build_ability_for_user()
    - can() -> Ability.can()
    - subject -> Django model instance
    - conditions -> RolePermission.conditions (JSON field)
"""

import logging
import re
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union

from django.core.exceptions import PermissionDenied
from django.db.models import Model
from rest_framework import permissions
from rest_framework.request import Request

if TYPE_CHECKING:
    from apps.core.models import Organization, User


logger = logging.getLogger(__name__)


# Permission constants for common actions
class Actions:
    """Standard permission action constants."""
    VIEW = 'view'
    LIST = 'list'
    CREATE = 'create'
    UPDATE = 'update'
    DELETE = 'delete'
    MANAGE = 'manage'  # Full access to a resource
    PUBLISH = 'publish'
    EXPORT = 'export'
    IMPORT = 'import'


# Resource constants for common entities
class Resources:
    """Standard resource name constants."""
    ORGANIZATION = 'organization'
    USER = 'user'
    ROLE = 'role'
    PERMISSION = 'permission'
    MENU = 'menu'
    CATEGORY = 'category'
    PRODUCT = 'product'
    ORDER = 'order'
    TABLE = 'table'
    QRCODE = 'qrcode'
    CUSTOMER = 'customer'
    SUBSCRIPTION = 'subscription'
    ANALYTICS = 'analytics'
    MEDIA = 'media'
    BRANCH = 'branch'
    THEME = 'theme'


@dataclass
class Rule:
    """
    A single permission rule with optional conditions.

    Represents a permission grant (can) or denial (cannot) with optional
    ABAC conditions for fine-grained access control.

    Attributes:
        action: The action being permitted/denied (e.g., 'create', 'view')
        resource: The resource type (e.g., 'menu', 'order')
        inverted: If True, this is a 'cannot' rule; otherwise 'can'
        conditions: Dict of conditions for ABAC (e.g., {'organization_id': '${user.organization_id}'})
        fields: Optional list of fields this rule applies to
        reason: Optional reason for the rule (useful for denials)
    """
    action: str
    resource: str
    inverted: bool = False
    conditions: Dict[str, Any] = field(default_factory=dict)
    fields: Optional[List[str]] = None
    reason: Optional[str] = None

    def matches_action(self, action: str) -> bool:
        """Check if this rule matches the given action."""
        return self.action == action or self.action == 'manage'

    def matches_resource(self, resource: str) -> bool:
        """Check if this rule matches the given resource."""
        return self.resource == resource or self.resource == 'all'


@dataclass
class Ability:
    """
    Represents a user's permission abilities.

    This class holds all the permission rules for a user and provides
    methods to check if the user can perform actions on resources.

    Similar to CASL's Ability class, it supports:
    - Simple permission checks: can('view', 'menu')
    - Subject-based checks: can('update', 'menu', menu_instance)
    - Condition evaluation for ABAC

    Attributes:
        user: The user these abilities belong to
        organization: The organization context (if any)
        rules: List of permission rules
        _permission_cache: Cache of permission check results

    Usage:
        ability = build_ability_for_user(user, organization)

        # Simple check
        if ability.can('create', 'menu'):
            ...

        # Check with subject instance
        if ability.can('update', 'menu', menu_instance):
            ...
    """
    user: 'User'
    organization: Optional['Organization'] = None
    rules: List[Rule] = field(default_factory=list)
    _permission_cache: Dict[str, bool] = field(default_factory=dict)

    def can(
        self,
        action: str,
        resource: Union[str, Model],
        subject: Optional[Model] = None
    ) -> bool:
        """
        Check if the user can perform an action on a resource.

        Args:
            action: The action to check (e.g., 'create', 'view', 'update')
            resource: Resource type string or model instance
            subject: Optional model instance for object-level checks

        Returns:
            bool: True if the user can perform the action, False otherwise

        Examples:
            ability.can('view', 'menu')  # Check resource permission
            ability.can('update', 'menu', menu_instance)  # Check object permission
            ability.can('delete', menu_instance)  # Infer resource from instance
        """
        # If resource is a model instance, extract resource name and use as subject
        if isinstance(resource, Model):
            subject = resource
            resource = self._get_resource_name(resource)

        # Check cache first
        cache_key = f"{action}:{resource}:{id(subject) if subject else 'none'}"
        if cache_key in self._permission_cache:
            return self._permission_cache[cache_key]

        # Superuser has all permissions
        if self.user and self.user.is_superuser:
            self._permission_cache[cache_key] = True
            return True

        # Check rules
        result = self._check_rules(action, resource, subject)
        self._permission_cache[cache_key] = result
        return result

    def cannot(
        self,
        action: str,
        resource: Union[str, Model],
        subject: Optional[Model] = None
    ) -> bool:
        """
        Check if the user cannot perform an action on a resource.

        This is the inverse of can() for readability.

        Args:
            action: The action to check
            resource: Resource type string or model instance
            subject: Optional model instance for object-level checks

        Returns:
            bool: True if the user cannot perform the action
        """
        return not self.can(action, resource, subject)

    def _check_rules(
        self,
        action: str,
        resource: str,
        subject: Optional[Model] = None
    ) -> bool:
        """
        Check permission rules for a given action and resource.

        Rules are checked in order. The last matching rule wins.
        This allows for deny-override patterns.

        Args:
            action: The action to check
            resource: The resource type
            subject: Optional model instance

        Returns:
            bool: True if permission is granted
        """
        result = False

        for rule in self.rules:
            if not rule.matches_action(action):
                continue
            if not rule.matches_resource(resource):
                continue

            # Check conditions if present
            if rule.conditions and subject:
                if not self._check_conditions(rule.conditions, subject):
                    continue

            # Rule matches - update result based on inverted flag
            result = not rule.inverted

        return result

    def _check_conditions(
        self,
        conditions: Dict[str, Any],
        subject: Model
    ) -> bool:
        """
        Evaluate ABAC conditions against a subject instance.

        Conditions support:
        - Direct value matching: {'status': 'active'}
        - User attribute substitution: {'organization_id': '${user.organization_id}'}
        - Organization attribute substitution: {'organization_id': '${organization.id}'}

        Args:
            conditions: Dict of conditions to check
            subject: Model instance to check against

        Returns:
            bool: True if all conditions match
        """
        for field_name, expected_value in conditions.items():
            # Handle variable substitution
            if isinstance(expected_value, str) and expected_value.startswith('${'):
                expected_value = self._resolve_variable(expected_value)

            # Get actual value from subject
            actual_value = getattr(subject, field_name, None)

            # Handle foreign key IDs
            if hasattr(actual_value, 'id'):
                actual_value = actual_value.id

            # Compare values (handle UUID comparison)
            if str(actual_value) != str(expected_value):
                return False

        return True

    def _resolve_variable(self, variable: str) -> Any:
        """
        Resolve a variable expression like ${user.organization_id}.

        Supported variables:
        - ${user.*}: User attributes
        - ${organization.*}: Organization attributes

        Args:
            variable: Variable expression string

        Returns:
            The resolved value
        """
        # Extract variable path: ${user.organization_id} -> user.organization_id
        match = re.match(r'\$\{(.+)\}', variable)
        if not match:
            return variable

        path = match.group(1)
        parts = path.split('.')

        if parts[0] == 'user' and self.user:
            obj = self.user
            for part in parts[1:]:
                obj = getattr(obj, part, None)
                if obj is None:
                    return None
            return obj.id if hasattr(obj, 'id') else obj

        elif parts[0] == 'organization' and self.organization:
            obj = self.organization
            for part in parts[1:]:
                obj = getattr(obj, part, None)
                if obj is None:
                    return None
            return obj.id if hasattr(obj, 'id') else obj

        return None

    def _get_resource_name(self, instance: Model) -> str:
        """
        Extract resource name from a model instance.

        Args:
            instance: Django model instance

        Returns:
            str: Resource name (lowercase model name)
        """
        return instance._meta.model_name

    def add_rule(self, rule: Rule) -> None:
        """Add a permission rule to this ability."""
        self.rules.append(rule)
        # Clear cache when rules change
        self._permission_cache.clear()

    def get_permitted_fields(self, action: str, resource: str) -> Optional[List[str]]:
        """
        Get the list of fields the user can access for a given action/resource.

        Args:
            action: The action being performed
            resource: The resource type

        Returns:
            List of field names, or None if all fields are permitted
        """
        permitted = None

        for rule in self.rules:
            if not rule.matches_action(action):
                continue
            if not rule.matches_resource(resource):
                continue
            if rule.inverted:
                continue

            if rule.fields:
                if permitted is None:
                    permitted = []
                permitted.extend(rule.fields)

        return list(set(permitted)) if permitted else None


def build_ability_for_user(
    user: 'User',
    organization: Optional['Organization'] = None
) -> Ability:
    """
    Build an Ability instance for a user based on their roles and permissions.

    This function queries the user's roles (both platform and organization-scoped)
    and builds a comprehensive ability object for permission checking.

    Args:
        user: The user to build abilities for
        organization: Optional organization context for org-scoped permissions

    Returns:
        Ability: The user's ability instance

    Usage:
        ability = build_ability_for_user(request.user, request.organization)
        if ability.can('create', 'menu'):
            # User can create menus in this organization
    """
    # Lazy import to avoid circular imports
    from apps.core.models import RolePermission, UserRole

    ability = Ability(user=user, organization=organization)

    if not user or not user.is_authenticated:
        return ability

    # Get user's role assignments

    # If organization context exists, include org-scoped roles
    if organization:
        # Get both platform roles and org-specific roles
        from django.db.models import Q
        user_roles = UserRole.objects.filter(
            Q(user=user, organization__isnull=True) |  # Platform roles
            Q(user=user, organization=organization)   # Org roles
        ).select_related('role')
    else:
        # Only platform roles
        user_roles = UserRole.objects.filter(
            user=user,
            organization__isnull=True
        ).select_related('role')

    # Collect all role IDs
    role_ids = [ur.role_id for ur in user_roles if ur.is_active]

    if not role_ids:
        logger.debug("No active roles found for user %s", user.email)
        return ability

    # Get all permissions for these roles
    role_permissions = RolePermission.objects.filter(
        role_id__in=role_ids
    ).select_related('permission')

    # Build rules from permissions
    for rp in role_permissions:
        perm = rp.permission
        rule = Rule(
            action=perm.action,
            resource=perm.resource,
            conditions=rp.conditions if rp.conditions else {}
        )
        ability.add_rule(rule)

    logger.debug(
        "Built ability for user %s with %d rules",
        user.email,
        len(ability.rules)
    )

    return ability


def check_permission(
    user: 'User',
    permission_code: str,
    organization: Optional['Organization'] = None,
    subject: Optional[Model] = None
) -> bool:
    """
    Simple utility function to check if a user has a specific permission.

    This is a convenience function that builds an ability and checks
    a single permission in one call.

    Args:
        user: The user to check
        permission_code: Permission in 'resource.action' format (e.g., 'menu.create')
        organization: Optional organization context
        subject: Optional model instance for object-level checks

    Returns:
        bool: True if the user has the permission

    Usage:
        if check_permission(request.user, 'menu.create', request.organization):
            # User can create menus

    Raises:
        ValueError: If permission_code format is invalid
    """
    if '.' not in permission_code:
        raise ValueError(
            f"Invalid permission code format: '{permission_code}'. "
            f"Expected format: 'resource.action' (e.g., 'menu.create')"
        )

    resource, action = permission_code.rsplit('.', 1)
    ability = build_ability_for_user(user, organization)
    return ability.can(action, resource, subject)


def require_permission(
    user: 'User',
    permission_code: str,
    organization: Optional['Organization'] = None,
    subject: Optional[Model] = None
) -> None:
    """
    Require that a user has a specific permission, raising PermissionDenied if not.

    This is useful for imperative permission checks in views.

    Args:
        user: The user to check
        permission_code: Permission in 'resource.action' format
        organization: Optional organization context
        subject: Optional model instance for object-level checks

    Raises:
        PermissionDenied: If the user does not have the permission

    Usage:
        def my_view(request):
            require_permission(request.user, 'menu.delete', request.organization, menu)
            # Only reaches here if permission granted
            menu.soft_delete()
    """
    if not check_permission(user, permission_code, organization, subject):
        raise PermissionDenied(
            f"Permission denied: {permission_code}"
        )


# =============================================================================
# Django REST Framework Permission Classes
# =============================================================================

class HasOrganizationPermission(permissions.BasePermission):
    """
    DRF permission class for organization-scoped permission checks.

    Verifies that the authenticated user has the required permission
    within their organization context.

    Usage:
        from rest_framework.decorators import permission_classes
        from shared.permissions.abilities import HasOrganizationPermission

        @permission_classes([HasOrganizationPermission('menu.view')])
        class MenuListView(APIView):
            def get(self, request):
                ...

        # Or in ViewSet
        class MenuViewSet(viewsets.ModelViewSet):
            permission_classes = [HasOrganizationPermission('menu.manage')]

    Attributes:
        permission_code: The permission to check in 'resource.action' format
        message: Custom error message (optional)
    """

    def __init__(self, permission_code: str = None, message: str = None):
        """
        Initialize the permission class.

        Args:
            permission_code: Permission in 'resource.action' format
            message: Custom error message
        """
        self.permission_code = permission_code
        if message:
            self.message = message

    def __call__(self, permission_code: str = None):
        """Allow using as @permission_classes([HasOrganizationPermission('menu.view')])."""
        if permission_code:
            self.permission_code = permission_code
        return self

    def has_permission(self, request: Request, view) -> bool:
        """
        Check if the request has permission.

        Args:
            request: The DRF request
            view: The view being accessed

        Returns:
            bool: True if permission is granted
        """
        # Allow if no permission code specified (use per-object permission only)
        if not self.permission_code:
            return True

        # Require authentication
        if not request.user or not request.user.is_authenticated:
            return False

        # Get organization context
        organization = getattr(request, 'organization', None)

        return check_permission(
            request.user,
            self.permission_code,
            organization
        )

    def has_object_permission(self, request: Request, view, obj) -> bool:
        """
        Check if the request has permission for a specific object.

        Args:
            request: The DRF request
            view: The view being accessed
            obj: The object being accessed

        Returns:
            bool: True if permission is granted
        """
        if not self.permission_code:
            return True

        if not request.user or not request.user.is_authenticated:
            return False

        organization = getattr(request, 'organization', None)

        return check_permission(
            request.user,
            self.permission_code,
            organization,
            subject=obj
        )


class HasPlatformPermission(permissions.BasePermission):
    """
    DRF permission class for platform-level permission checks.

    Verifies that the authenticated user has the required permission
    at the platform level (not organization-scoped).

    Used for system administration endpoints.

    Usage:
        @permission_classes([HasPlatformPermission('user.manage')])
        class PlatformUserView(APIView):
            ...
    """

    def __init__(self, permission_code: str = None, message: str = None):
        """
        Initialize the permission class.

        Args:
            permission_code: Permission in 'resource.action' format
            message: Custom error message
        """
        self.permission_code = permission_code
        if message:
            self.message = message

    def __call__(self, permission_code: str = None):
        """Allow decorator-style usage."""
        if permission_code:
            self.permission_code = permission_code
        return self

    def has_permission(self, request: Request, view) -> bool:
        """Check if the request has platform-level permission."""
        if not self.permission_code:
            return True

        if not request.user or not request.user.is_authenticated:
            return False

        # Platform permissions don't use organization context
        return check_permission(
            request.user,
            self.permission_code,
            organization=None
        )


class IsTenantMember(permissions.BasePermission):
    """
    DRF permission class that verifies user belongs to the current tenant.

    This ensures that a user can only access resources within their
    organization context.

    Usage:
        class MenuViewSet(viewsets.ModelViewSet):
            permission_classes = [IsTenantMember]
    """
    message = "You must be a member of this organization to access this resource."

    def has_permission(self, request: Request, view) -> bool:
        """
        Check if user belongs to the request's organization context.

        Args:
            request: The DRF request
            view: The view being accessed

        Returns:
            bool: True if user is a member of the organization
        """
        if not request.user or not request.user.is_authenticated:
            return False

        # Superusers can access any organization
        if request.user.is_superuser:
            return True

        # Get organization context
        organization = getattr(request, 'organization', None)
        if not organization:
            return False

        # Check if user belongs to this organization
        user_org = getattr(request.user, 'organization', None)
        if user_org and user_org.id == organization.id:
            return True

        # Check if user has any role in this organization
        from apps.core.models import UserRole
        return UserRole.objects.filter(
            user=request.user,
            organization=organization
        ).exists()


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    DRF permission class for object-level ownership checks.

    Allows read access to any authenticated user, but write access
    only to the object's owner.

    The owner field can be configured via the owner_field attribute.

    Usage:
        class FeedbackViewSet(viewsets.ModelViewSet):
            permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]
    """
    message = "You can only modify your own objects."
    owner_field = 'created_by'  # Default field name for owner

    def has_object_permission(self, request: Request, view, obj) -> bool:
        """
        Check object ownership for write operations.

        Args:
            request: The DRF request
            view: The view being accessed
            obj: The object being accessed

        Returns:
            bool: True if read access or user is owner
        """
        # Read permissions are allowed for any authenticated user
        if request.method in permissions.SAFE_METHODS:
            return True

        # Superusers can modify anything
        if request.user.is_superuser:
            return True

        # Check ownership
        owner_field = getattr(view, 'owner_field', self.owner_field)
        owner = getattr(obj, owner_field, None)

        if owner is None:
            # No owner field, deny by default
            return False

        # Compare owner ID with request user
        owner_id = owner.id if hasattr(owner, 'id') else owner
        return str(owner_id) == str(request.user.id)


class IsAuthenticatedOrReadOnly(permissions.BasePermission):
    """
    DRF permission class allowing read access to anyone, write to authenticated users.

    Similar to DRF's built-in IsAuthenticatedOrReadOnly but with E-Menum's
    standard error message format.
    """
    message = "Authentication is required to perform this action."

    def has_permission(self, request: Request, view) -> bool:
        """Allow read to anyone, write to authenticated users."""
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and request.user.is_authenticated


class AllowPublicRead(permissions.BasePermission):
    """
    DRF permission class allowing public read access to resources.

    Used for public-facing endpoints like menu display.

    Usage:
        class PublicMenuViewSet(viewsets.ReadOnlyModelViewSet):
            permission_classes = [AllowPublicRead]
    """

    def has_permission(self, request: Request, view) -> bool:
        """Allow all read operations."""
        return request.method in permissions.SAFE_METHODS


# =============================================================================
# Permission Decorators
# =============================================================================

def permission_required(permission_code: str):
    """
    Decorator for function-based views requiring a specific permission.

    Usage:
        from shared.permissions.abilities import permission_required

        @permission_required('menu.create')
        def create_menu(request):
            ...
    """
    def decorator(view_func):
        def wrapped_view(request, *args, **kwargs):
            organization = getattr(request, 'organization', None)
            if not check_permission(request.user, permission_code, organization):
                raise PermissionDenied(f"Permission denied: {permission_code}")
            return view_func(request, *args, **kwargs)
        return wrapped_view
    return decorator


# =============================================================================
# Predefined Role Abilities
# =============================================================================

def get_owner_abilities() -> List[Rule]:
    """
    Get the default abilities for the 'owner' role.

    Owner has full access to all organization resources.

    Returns:
        List of permission rules
    """
    return [
        Rule(action='manage', resource='all', conditions={'organization_id': '${user.organization_id}'}),
    ]


def get_manager_abilities() -> List[Rule]:
    """
    Get the default abilities for the 'manager' role.

    Manager can manage most resources except billing and user roles.

    Returns:
        List of permission rules
    """
    return [
        Rule(action='manage', resource='menu'),
        Rule(action='manage', resource='category'),
        Rule(action='manage', resource='product'),
        Rule(action='manage', resource='order'),
        Rule(action='manage', resource='table'),
        Rule(action='manage', resource='qrcode'),
        Rule(action='manage', resource='theme'),
        Rule(action='view', resource='analytics'),
        Rule(action='view', resource='customer'),
        Rule(action='update', resource='customer'),
        Rule(action='view', resource='user'),
    ]


def get_staff_abilities() -> List[Rule]:
    """
    Get the default abilities for the 'staff' role.

    Staff can take orders and manage tables.

    Returns:
        List of permission rules
    """
    return [
        Rule(action='view', resource='menu'),
        Rule(action='view', resource='category'),
        Rule(action='view', resource='product'),
        Rule(action='create', resource='order'),
        Rule(action='view', resource='order'),
        Rule(action='update', resource='order'),
        Rule(action='view', resource='table'),
        Rule(action='update', resource='table'),
    ]


def get_viewer_abilities() -> List[Rule]:
    """
    Get the default abilities for the 'viewer' role.

    Viewer has read-only access to dashboard data.

    Returns:
        List of permission rules
    """
    return [
        Rule(action='view', resource='menu'),
        Rule(action='view', resource='category'),
        Rule(action='view', resource='product'),
        Rule(action='view', resource='order'),
        Rule(action='view', resource='table'),
        Rule(action='view', resource='analytics'),
    ]


# =============================================================================
# Exports
# =============================================================================

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
