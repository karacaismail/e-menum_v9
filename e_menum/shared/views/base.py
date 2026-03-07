"""
Base view classes for E-Menum Django REST Framework.

This module provides base view classes that implement common functionality
required across all DRF views in the E-Menum platform.

View Classes:
    - StandardResponseMixin: Formats all responses in E-Menum standard format
    - SoftDeleteMixin: Implements soft delete instead of hard delete
    - TenantFilterMixin: Automatically filters querysets by organization
    - BaseModelViewSet: Full-featured viewset with standard response format
    - BaseTenantViewSet: ViewSet with automatic tenant filtering
    - BaseReadOnlyViewSet: Read-only viewset for public/reference data

Response Format:
    All API responses follow the E-Menum standard format:

    Success:
        {
            "success": true,
            "data": {...}
        }

    Success with pagination:
        {
            "success": true,
            "data": [...],
            "meta": {
                "page": 1,
                "per_page": 20,
                "total": 150,
                "total_pages": 8
            }
        }

    Error:
        {
            "success": false,
            "error": {
                "code": "ERROR_CODE",
                "message": "Human readable message",
                "details": {...}
            }
        }

Multi-Tenancy Pattern:
    Every query MUST include organization filtering:

    # CORRECT
    def get_queryset(self):
        return Menu.objects.filter(
            organization=self.request.organization,
            deleted_at__isnull=True
        )

    # INCORRECT - SECURITY VIOLATION
    def get_queryset(self):
        return Menu.objects.all()  # Exposes ALL tenant data!

Soft Delete Pattern:
    Never use hard deletes:

    # CORRECT (soft delete)
    def perform_destroy(self, instance):
        instance.soft_delete()

    # INCORRECT
    def perform_destroy(self, instance):
        instance.delete()  # Physical deletion FORBIDDEN

Usage:
    from shared.views.base import BaseTenantViewSet

    class MenuViewSet(BaseTenantViewSet):
        queryset = Menu.objects.all()
        serializer_class = MenuSerializer
        permission_resource = 'menu'
"""

import logging
from typing import Any, Dict, List, Optional, TYPE_CHECKING

from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from rest_framework import status, viewsets
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated

from shared.permissions.drf_permissions import (
    OrganizationScopedPermission,
    IsTenantMember,
)
from shared.utils.exceptions import (
    AppException,
    ErrorCodes,
    ResourceNotFoundException,
)

if TYPE_CHECKING:
    from apps.core.models import Organization


logger = logging.getLogger(__name__)


# =============================================================================
# PAGINATION
# =============================================================================

class StandardPagination(PageNumberPagination):
    """
    Standard pagination class with E-Menum response format.

    Configuration:
        - page_size: Default items per page (20)
        - page_size_query_param: URL param to override page size ('per_page')
        - max_page_size: Maximum allowed page size (100)
        - page_query_param: URL param for page number ('page')

    Response format includes meta information:
        {
            "success": true,
            "data": [...],
            "meta": {
                "page": 1,
                "per_page": 20,
                "total": 150,
                "total_pages": 8
            }
        }
    """

    page_size = 20
    page_size_query_param = 'per_page'
    max_page_size = 100
    page_query_param = 'page'

    def get_paginated_response(self, data: List) -> Response:
        """
        Return paginated response with E-Menum standard format.

        Args:
            data: The serialized page data

        Returns:
            Response: Formatted paginated response
        """
        return Response({
            'success': True,
            'data': data,
            'meta': {
                'page': self.page.number,
                'per_page': self.get_page_size(self.request),
                'total': self.page.paginator.count,
                'total_pages': self.page.paginator.num_pages,
            }
        })

    def get_paginated_response_schema(self, schema: Dict) -> Dict:
        """
        Return the OpenAPI schema for paginated responses.

        Args:
            schema: The base response schema

        Returns:
            Dict: The paginated response schema
        """
        return {
            'type': 'object',
            'properties': {
                'success': {
                    'type': 'boolean',
                    'default': True,
                },
                'data': schema,
                'meta': {
                    'type': 'object',
                    'properties': {
                        'page': {'type': 'integer'},
                        'per_page': {'type': 'integer'},
                        'total': {'type': 'integer'},
                        'total_pages': {'type': 'integer'},
                    }
                }
            }
        }


# =============================================================================
# RESPONSE MIXINS
# =============================================================================

class StandardResponseMixin:
    """
    Mixin that wraps all responses in E-Menum standard format.

    Features:
    - Wraps successful responses in {"success": true, "data": ...}
    - Handles paginated responses with meta information
    - Provides helper methods for consistent response formatting

    Usage:
        class MyViewSet(StandardResponseMixin, viewsets.ModelViewSet):
            ...

        # Or use BaseModelViewSet which includes this mixin
    """

    def get_success_response(
        self,
        data: Any,
        status_code: int = status.HTTP_200_OK,
        message: str = None
    ) -> Response:
        """
        Create a success response in standard format.

        Args:
            data: The response data
            status_code: HTTP status code (default: 200)
            message: Optional success message

        Returns:
            Response: Formatted success response
        """
        response_data = {
            'success': True,
            'data': data,
        }
        if message:
            response_data['message'] = message

        return Response(response_data, status=status_code)

    def get_error_response(
        self,
        code: str,
        message: str,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        details: Dict = None
    ) -> Response:
        """
        Create an error response in standard format.

        Args:
            code: Error code from ErrorCodes
            message: Human-readable error message
            status_code: HTTP status code (default: 400)
            details: Additional error details

        Returns:
            Response: Formatted error response
        """
        response_data = {
            'success': False,
            'error': {
                'code': code,
                'message': str(message),
            }
        }
        if details:
            response_data['error']['details'] = details

        return Response(response_data, status=status_code)

    def get_created_response(self, data: Any, message: str = None) -> Response:
        """
        Create a 201 Created response.

        Args:
            data: The created resource data
            message: Optional success message

        Returns:
            Response: Formatted 201 response
        """
        return self.get_success_response(
            data,
            status_code=status.HTTP_201_CREATED,
            message=message or str(_('Resource created successfully'))
        )

    def get_no_content_response(self) -> Response:
        """
        Create a 204 No Content response.

        Returns:
            Response: Empty 204 response
        """
        return Response(status=status.HTTP_204_NO_CONTENT)

    def get_deleted_response(self, message: str = None) -> Response:
        """
        Create a success response for delete operations.

        Args:
            message: Optional success message

        Returns:
            Response: Formatted delete success response
        """
        return self.get_success_response(
            data={'deleted': True},
            message=message or str(_('Resource deleted successfully'))
        )

    def finalize_response(self, request, response, *args, **kwargs):
        """
        Wrap the response in standard format if not already wrapped.

        Args:
            request: The request object
            response: The response object
            *args: Additional arguments
            **kwargs: Additional keyword arguments

        Returns:
            Response: The finalized response
        """
        # Call parent's finalize_response first
        response = super().finalize_response(request, response, *args, **kwargs)

        # Don't modify error responses (they're already handled by exception handler)
        if response.status_code >= 400:
            return response

        # Don't modify responses that are already wrapped
        if isinstance(response.data, dict) and 'success' in response.data:
            return response

        # Don't modify empty responses (204 No Content)
        if response.status_code == status.HTTP_204_NO_CONTENT:
            return response

        # Wrap the response data
        response.data = {
            'success': True,
            'data': response.data,
        }

        return response


# =============================================================================
# SOFT DELETE MIXIN
# =============================================================================

class SoftDeleteMixin:
    """
    Mixin that implements soft delete instead of hard delete.

    Features:
    - Overrides perform_destroy to use soft_delete()
    - Filters out soft-deleted records in get_queryset
    - Provides restore action for restoring deleted records

    Usage:
        class MenuViewSet(SoftDeleteMixin, viewsets.ModelViewSet):
            ...

    Critical Rule:
        NEVER use hard delete (instance.delete()). Always soft delete.
    """

    def get_queryset(self):
        """
        Return queryset filtered to exclude soft-deleted records.

        The base queryset should use a SoftDeleteManager that already
        filters deleted records, but this is an additional safety check.

        Returns:
            QuerySet: Filtered queryset
        """
        queryset = super().get_queryset()

        # Filter out soft-deleted records if the model has deleted_at
        if hasattr(queryset.model, 'deleted_at'):
            queryset = queryset.filter(deleted_at__isnull=True)

        return queryset

    def perform_destroy(self, instance: models.Model) -> None:
        """
        Soft delete the instance instead of hard delete.

        Args:
            instance: The model instance to delete
        """
        if hasattr(instance, 'soft_delete'):
            instance.soft_delete()
            logger.info(
                "Soft deleted %s: id=%s",
                instance.__class__.__name__,
                instance.pk
            )
        elif hasattr(instance, 'deleted_at'):
            instance.deleted_at = timezone.now()
            instance.save(update_fields=['deleted_at'])
            logger.info(
                "Soft deleted (manual) %s: id=%s",
                instance.__class__.__name__,
                instance.pk
            )
        else:
            # Fallback to hard delete only if model doesn't support soft delete
            logger.warning(
                "Model %s does not support soft delete, using hard delete",
                instance.__class__.__name__
            )
            instance.delete()

    def destroy(self, request: Request, *args, **kwargs) -> Response:
        """
        Handle DELETE request with soft delete and standard response.

        Args:
            request: The request object
            *args: Additional arguments
            **kwargs: Additional keyword arguments

        Returns:
            Response: Success response
        """
        instance = self.get_object()
        self.perform_destroy(instance)
        return self.get_deleted_response()


# =============================================================================
# TENANT FILTER MIXIN
# =============================================================================

class TenantFilterMixin:
    """
    Mixin that automatically filters querysets by organization.

    Features:
    - Filters queryset to current organization from request context
    - Auto-injects organization on create operations
    - Validates organization consistency on updates

    Usage:
        class MenuViewSet(TenantFilterMixin, viewsets.ModelViewSet):
            ...

    Critical Rule:
        EVERY query on tenant-scoped data MUST filter by organization.
    """

    def get_organization(self) -> Optional['Organization']:
        """
        Get the current organization from request context.

        Returns:
            Organization or None: The current organization
        """
        return getattr(self.request, 'organization', None)

    def require_organization(self) -> 'Organization':
        """
        Get the current organization or raise an exception.

        Returns:
            Organization: The current organization

        Raises:
            AppException: If no organization context
        """
        organization = self.get_organization()
        if not organization:
            raise AppException(
                code=ErrorCodes.FORBIDDEN_TENANT_MISMATCH,
                message=str(_('Organization context is required')),
                status_code=status.HTTP_403_FORBIDDEN
            )
        return organization

    def get_queryset(self):
        """
        Return queryset filtered to the current organization.

        Returns:
            QuerySet: Organization-filtered queryset

        Raises:
            AppException: If no organization context
        """
        queryset = super().get_queryset()

        # Check if model has organization field
        if not hasattr(queryset.model, 'organization'):
            return queryset

        organization = self.get_organization()

        if organization:
            queryset = queryset.filter(organization=organization)
            logger.debug(
                "Filtered queryset for organization: %s",
                organization.id
            )
        else:
            # If no organization context, return empty queryset for safety
            # This prevents accidental data leaks
            logger.warning(
                "No organization context for %s, returning empty queryset",
                self.__class__.__name__
            )
            queryset = queryset.none()

        return queryset

    def perform_create(self, serializer) -> None:
        """
        Create a new instance with organization auto-injected.

        Args:
            serializer: The serializer instance
        """
        organization = self.require_organization()
        serializer.save(organization=organization)
        logger.info(
            "Created %s for organization %s",
            serializer.instance.__class__.__name__,
            organization.id
        )

    def perform_update(self, serializer) -> None:
        """
        Update an instance, validating organization consistency.

        Args:
            serializer: The serializer instance
        """
        instance = serializer.instance
        organization = self.get_organization()

        # Validate organization hasn't changed
        if hasattr(instance, 'organization_id') and organization:
            if str(instance.organization_id) != str(organization.id):
                raise AppException(
                    code=ErrorCodes.FORBIDDEN_TENANT_MISMATCH,
                    message=str(_('Cannot update resource from different organization')),
                    status_code=status.HTTP_403_FORBIDDEN
                )

        serializer.save()
        logger.info(
            "Updated %s: id=%s, organization=%s",
            instance.__class__.__name__,
            instance.pk,
            organization.id if organization else 'N/A'
        )


# =============================================================================
# BASE VIEWSETS
# =============================================================================

class BaseModelViewSet(StandardResponseMixin, SoftDeleteMixin, viewsets.ModelViewSet):
    """
    Base ViewSet with standard response format and soft delete.

    Features:
    - All responses wrapped in E-Menum standard format
    - Soft delete implementation (no hard deletes)
    - Standard pagination

    This is the base class for all model viewsets that don't need
    tenant filtering (e.g., platform-level resources).

    Usage:
        class PlanViewSet(BaseModelViewSet):
            queryset = Plan.objects.all()
            serializer_class = PlanSerializer
            permission_classes = [IsAdminUser]
    """

    pagination_class = StandardPagination


class BaseTenantViewSet(
    TenantFilterMixin,
    StandardResponseMixin,
    SoftDeleteMixin,
    viewsets.ModelViewSet
):
    """
    Base ViewSet for tenant-scoped resources.

    Features:
    - Automatic organization filtering on all queries
    - Auto-inject organization on create operations
    - Soft delete implementation
    - Standard response format
    - Standard pagination
    - Action-based permission checking

    Usage:
        class MenuViewSet(BaseTenantViewSet):
            queryset = Menu.objects.all()
            serializer_class = MenuSerializer
            permission_resource = 'menu'

            # Optional: Override action permissions
            action_permissions = {
                'list': 'menu.view',
                'retrieve': 'menu.view',
                'create': 'menu.create',
                'update': 'menu.update',
                'destroy': 'menu.delete',
            }

    Attributes:
        permission_resource: The resource name for permission checking
        action_permissions: Optional dict mapping actions to permission codes
    """

    pagination_class = StandardPagination
    permission_classes = [IsAuthenticated, IsTenantMember, OrganizationScopedPermission]
    permission_resource: Optional[str] = None

    def get_object(self):
        """
        Get the object, ensuring it belongs to the current organization.

        Returns:
            Model: The requested object

        Raises:
            Http404: If object not found or doesn't belong to organization
        """
        obj = super().get_object()

        # Additional organization validation
        organization = self.get_organization()
        if organization and hasattr(obj, 'organization_id'):
            if str(obj.organization_id) != str(organization.id):
                raise ResourceNotFoundException(
                    code=ErrorCodes.RESOURCE_NOT_FOUND,
                    message=str(_('Resource not found'))
                )

        return obj


class BaseReadOnlyViewSet(
    StandardResponseMixin,
    viewsets.ReadOnlyModelViewSet
):
    """
    Base ViewSet for read-only resources.

    Features:
    - List and retrieve actions only
    - Standard response format
    - Standard pagination

    Usage:
        class AllergenViewSet(BaseReadOnlyViewSet):
            queryset = Allergen.objects.all()
            serializer_class = AllergenSerializer
    """

    pagination_class = StandardPagination


class BaseTenantReadOnlyViewSet(
    TenantFilterMixin,
    StandardResponseMixin,
    viewsets.ReadOnlyModelViewSet
):
    """
    Base ViewSet for read-only tenant-scoped resources.

    Features:
    - Automatic organization filtering
    - List and retrieve actions only
    - Standard response format
    - Standard pagination

    Usage:
        class AuditLogViewSet(BaseTenantReadOnlyViewSet):
            queryset = AuditLog.objects.all()
            serializer_class = AuditLogSerializer
            permission_resource = 'audit_log'
    """

    pagination_class = StandardPagination
    permission_classes = [IsAuthenticated, IsTenantMember, OrganizationScopedPermission]
    permission_resource: Optional[str] = None


# =============================================================================
# BASE API VIEWS
# =============================================================================

class BaseAPIView(StandardResponseMixin, APIView):
    """
    Base APIView with standard response format.

    Usage:
        class HealthCheckView(BaseAPIView):
            permission_classes = [AllowAny]

            def get(self, request):
                return self.get_success_response({'status': 'healthy'})
    """

    pass


class BaseTenantAPIView(TenantFilterMixin, StandardResponseMixin, APIView):
    """
    Base APIView with tenant context.

    Usage:
        class OrganizationDashboardView(BaseTenantAPIView):
            permission_classes = [IsAuthenticated, IsTenantMember]

            def get(self, request):
                org = self.require_organization()
                stats = get_organization_stats(org)
                return self.get_success_response(stats)
    """

    permission_classes = [IsAuthenticated, IsTenantMember]


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Pagination
    'StandardPagination',
    # Mixins
    'StandardResponseMixin',
    'SoftDeleteMixin',
    'TenantFilterMixin',
    # ViewSets
    'BaseModelViewSet',
    'BaseTenantViewSet',
    'BaseReadOnlyViewSet',
    'BaseTenantReadOnlyViewSet',
    # API Views
    'BaseAPIView',
    'BaseTenantAPIView',
]
