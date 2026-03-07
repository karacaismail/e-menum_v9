"""
Multi-tenant middleware for organization context injection.

This middleware is responsible for:
1. Extracting the current organization context from the request
2. Injecting the organization instance into request.organization
3. Providing tenant isolation for all subsequent request processing

Organization Resolution Order:
1. User's organization (from authenticated user's organization FK)
2. X-Organization-ID header (for multi-org users/admin)
3. Cookie (emenum_org_id) for session persistence
4. None for anonymous/public endpoints

Critical Rules:
- EVERY view handling tenant-scoped data MUST use request.organization
- NEVER query tenant data without organization filtering
- Public endpoints (menu display) may have request.organization = None

Usage:
    # In settings/base.py MIDDLEWARE list:
    MIDDLEWARE = [
        ...
        'django.contrib.auth.middleware.AuthenticationMiddleware',
        'shared.middleware.tenant.TenantMiddleware',  # Must be AFTER auth
        ...
    ]

    # In views:
    def get_queryset(self):
        if not request.organization:
            raise PermissionDenied("Organization context required")
        return Menu.objects.filter(organization=request.organization)
"""

import logging
from typing import TYPE_CHECKING, Optional
from uuid import UUID

from django.conf import settings
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.utils.deprecation import MiddlewareMixin
from django.utils.translation import gettext_lazy as _

if TYPE_CHECKING:
    from apps.core.models import Organization


logger = logging.getLogger(__name__)


class TenantMiddleware(MiddlewareMixin):
    """
    Middleware to inject organization (tenant) context into requests.

    This middleware runs after AuthenticationMiddleware and extracts the
    organization context for multi-tenant data isolation.

    Attributes:
        get_response: The next middleware/view callable in the chain

    Request Attributes Added:
        request.organization: The Organization instance or None
        request.organization_id: The organization UUID or None
        request.is_tenant_aware: Boolean indicating if tenant context exists

    Configuration Settings:
        EMENUM_TENANT_HEADER: Header name for org ID (default: X-Organization-ID)
        EMENUM_TENANT_COOKIE: Cookie name for org ID (default: emenum_org_id)
        EMENUM_TENANT_REQUIRED_PATHS: URL prefixes requiring tenant context

    Example:
        # Access organization in views:
        class MenuViewSet(viewsets.ModelViewSet):
            def get_queryset(self):
                if not self.request.organization:
                    return Menu.objects.none()
                return Menu.objects.filter(
                    organization=self.request.organization,
                    deleted_at__isnull=True
                )
    """

    # URL prefixes that allow anonymous/public access without tenant context
    PUBLIC_URL_PREFIXES = (
        "/admin/",
        "/health/",
        "/healthz/",
        "/api/v1/auth/",
        "/api/v1/public/",
        "/static/",
        "/media/",
        "/m/",  # Public menu display
    )

    # URL prefixes that REQUIRE tenant context
    TENANT_REQUIRED_PREFIXES = (
        "/api/v1/menus/",
        "/api/v1/categories/",
        "/api/v1/products/",
        "/api/v1/orders/",
        "/api/v1/tables/",
        "/api/v1/qr-codes/",
        "/api/v1/customers/",
        "/api/v1/analytics/",
    )

    def __init__(self, get_response):
        """
        Initialize the middleware.

        Args:
            get_response: The next middleware or view callable
        """
        self.get_response = get_response
        self._organization_cache = {}

    def __call__(self, request: HttpRequest) -> HttpResponse:
        """
        Process the request and inject organization context.

        Args:
            request: The incoming HTTP request

        Returns:
            HttpResponse: The response from the view/next middleware
        """
        # Initialize tenant context attributes
        request.organization = None
        request.organization_id = None
        request.is_tenant_aware = False

        # Skip tenant resolution for public URLs
        if self._is_public_url(request.path):
            return self.get_response(request)

        # Resolve organization context
        organization = self._resolve_organization(request)

        if organization:
            request.organization = organization
            request.organization_id = organization.id
            request.is_tenant_aware = True
            logger.debug(
                "Tenant context set: org_id=%s, org_name=%s",
                organization.id,
                organization.name,
            )
        else:
            # Check if tenant context is required for this path
            if self._requires_tenant_context(request.path):
                logger.warning(
                    "Tenant context required but not found: path=%s, user=%s",
                    request.path,
                    getattr(request, "user", "anonymous"),
                )
                return self._tenant_required_response()

        response = self.get_response(request)
        return response

    def _is_public_url(self, path: str) -> bool:
        """
        Check if the URL path allows public access without tenant context.

        Args:
            path: The request URL path

        Returns:
            bool: True if the path is public, False otherwise
        """
        return any(path.startswith(prefix) for prefix in self.PUBLIC_URL_PREFIXES)

    def _requires_tenant_context(self, path: str) -> bool:
        """
        Check if the URL path requires tenant context.

        Args:
            path: The request URL path

        Returns:
            bool: True if tenant context is required, False otherwise
        """
        return any(path.startswith(prefix) for prefix in self.TENANT_REQUIRED_PREFIXES)

    def _resolve_organization(self, request: HttpRequest) -> Optional["Organization"]:
        """
        Resolve the organization from the request using multiple sources.

        Resolution order:
        1. Authenticated user's organization
        2. X-Organization-ID header
        3. Organization cookie

        Args:
            request: The incoming HTTP request

        Returns:
            Organization or None: The resolved organization instance
        """
        organization = None

        # 1. Try to get from authenticated user's organization
        if hasattr(request, "user") and request.user.is_authenticated:
            user_org = getattr(request.user, "organization", None)
            if user_org:
                organization = user_org
                logger.debug("Organization resolved from user: %s", user_org.id)
                return organization

        # 2. Try to get from header (for admin/multi-org users)
        header_name = getattr(settings, "EMENUM_TENANT_HEADER", "X-Organization-ID")
        # Django converts headers to HTTP_X_ORGANIZATION_ID format
        django_header = f"HTTP_{header_name.upper().replace('-', '_')}"
        org_id_from_header = request.META.get(django_header)

        if org_id_from_header:
            organization = self._get_organization_by_id(org_id_from_header)
            if organization:
                logger.debug("Organization resolved from header: %s", organization.id)
                return organization
            else:
                logger.warning(
                    "Invalid organization ID in header: %s", org_id_from_header
                )

        # 3. Try to get from cookie
        cookie_name = getattr(settings, "EMENUM_TENANT_COOKIE", "emenum_org_id")
        org_id_from_cookie = request.COOKIES.get(cookie_name)

        if org_id_from_cookie:
            organization = self._get_organization_by_id(org_id_from_cookie)
            if organization:
                logger.debug("Organization resolved from cookie: %s", organization.id)
                return organization
            else:
                logger.warning(
                    "Invalid organization ID in cookie: %s", org_id_from_cookie
                )

        return None

    def _get_organization_by_id(self, org_id: str) -> Optional["Organization"]:
        """
        Retrieve an organization by its ID.

        Uses caching to reduce database queries for repeated requests.

        Args:
            org_id: The organization ID (string representation of UUID)

        Returns:
            Organization or None: The organization instance if found and active
        """
        # Lazy import to avoid circular imports
        from apps.core.models import Organization

        # Validate UUID format
        try:
            org_uuid = UUID(str(org_id))
        except (ValueError, AttributeError):
            logger.warning("Invalid organization ID format: %s", org_id)
            return None

        # Check cache first
        if org_uuid in self._organization_cache:
            return self._organization_cache[org_uuid]

        # Query database
        try:
            organization = Organization.objects.get(
                id=org_uuid,
                deleted_at__isnull=True,  # Soft delete check
                status="ACTIVE",  # Only active organizations
            )
            # Cache for future requests (within same request/worker)
            self._organization_cache[org_uuid] = organization
            return organization
        except Organization.DoesNotExist:
            logger.warning("Organization not found: %s", org_id)
            return None
        except Exception as e:
            logger.error("Error fetching organization %s: %s", org_id, str(e))
            return None

    def _tenant_required_response(self) -> JsonResponse:
        """
        Return a JSON error response when tenant context is required but missing.

        Returns:
            JsonResponse: 403 Forbidden response with error details
        """
        return JsonResponse(
            {
                "success": False,
                "error": {
                    "code": "TENANT_CONTEXT_REQUIRED",
                    "message": str(
                        _("Organization context is required for this request")
                    ),
                    "details": {
                        "hint": "Authenticate with a user belonging to an organization, "
                        "or provide X-Organization-ID header"
                    },
                },
            },
            status=403,
        )


class TenantContextMixin:
    """
    Mixin for views that require tenant context.

    Provides helper methods to access organization context safely.

    Usage:
        class MenuViewSet(TenantContextMixin, viewsets.ModelViewSet):
            def get_queryset(self):
                return Menu.objects.filter(
                    organization=self.get_organization()
                )
    """

    def get_organization(self) -> Optional["Organization"]:
        """
        Get the organization from the request.

        Returns:
            Organization or None: The current organization
        """
        return getattr(self.request, "organization", None)

    def get_organization_id(self) -> Optional[UUID]:
        """
        Get the organization ID from the request.

        Returns:
            UUID or None: The current organization ID
        """
        return getattr(self.request, "organization_id", None)

    def require_organization(self) -> "Organization":
        """
        Get the organization, raising an exception if not found.

        Returns:
            Organization: The current organization

        Raises:
            PermissionDenied: If no organization context exists
        """
        from django.core.exceptions import PermissionDenied

        organization = self.get_organization()
        if not organization:
            raise PermissionDenied(_("Organization context is required"))
        return organization


def get_current_organization(request: HttpRequest) -> Optional["Organization"]:
    """
    Utility function to get the current organization from a request.

    This is a convenience function for use outside of class-based views.

    Args:
        request: The HTTP request object

    Returns:
        Organization or None: The current organization if set

    Example:
        from shared.middleware.tenant import get_current_organization

        def my_view(request):
            org = get_current_organization(request)
            if org:
                # Do something with the organization
                ...
    """
    return getattr(request, "organization", None)


def set_current_organization(
    request: HttpRequest, organization: "Organization"
) -> None:
    """
    Utility function to manually set the organization context.

    This is useful for testing or special cases where organization
    context needs to be set programmatically.

    Args:
        request: The HTTP request object
        organization: The Organization instance to set

    Example:
        from shared.middleware.tenant import set_current_organization

        def my_admin_view(request):
            # Switch organization context for admin
            target_org = Organization.objects.get(slug='cafe-istanbul')
            set_current_organization(request, target_org)
    """
    request.organization = organization
    request.organization_id = organization.id if organization else None
    request.is_tenant_aware = organization is not None
