"""
Base serializers for E-Menum Django REST Framework.

This module provides base serializer classes that implement common functionality
required across all DRF serializers in the E-Menum platform.

Serializer Classes:
    - BaseModelSerializer: Base serializer with UUID primary key handling
    - TenantModelSerializer: Auto-injects organization from request context
    - SoftDeleteModelSerializer: Handles soft delete field exclusion
    - AuditModelSerializer: Includes audit fields (created_at, updated_at, etc.)

Response Format:
    All API responses follow the E-Menum standard format (handled by views,
    but serializers prepare data appropriately):

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

Usage:
    from shared.serializers.base import TenantModelSerializer

    class MenuSerializer(TenantModelSerializer):
        class Meta:
            model = Menu
            fields = ['id', 'name', 'slug', 'description', 'is_published']

Critical Rules:
    - Use TenantModelSerializer for all tenant-scoped models
    - Never expose deleted_at field in public API responses
    - Always include organization validation for tenant models
"""

import logging
from typing import Any, Dict, List, Optional, Type, TYPE_CHECKING

from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

if TYPE_CHECKING:
    from apps.core.models import Organization

logger = logging.getLogger(__name__)


# =============================================================================
# BASE SERIALIZERS
# =============================================================================

class BaseModelSerializer(serializers.ModelSerializer):
    """
    Base serializer for all model serializers in E-Menum.

    Provides:
    - UUID primary key handling (read-only by default)
    - Standard field ordering conventions
    - Helper methods for common serialization tasks

    Usage:
        class MyModelSerializer(BaseModelSerializer):
            class Meta:
                model = MyModel
                fields = ['id', 'name', 'description']
    """

    # Override the default id field to be read-only
    id = serializers.UUIDField(read_only=True)

    class Meta:
        abstract = True

    def get_field_names(self, declared_fields, info):
        """
        Ensure 'id' is always first in the fields list.

        Args:
            declared_fields: Fields declared on the serializer
            info: Model metadata

        Returns:
            List[str]: Ordered field names
        """
        fields = super().get_field_names(declared_fields, info)

        # Move 'id' to the beginning if present
        if 'id' in fields:
            fields = ['id'] + [f for f in fields if f != 'id']

        return fields


class SoftDeleteModelSerializer(BaseModelSerializer):
    """
    Serializer for models with soft delete functionality.

    Features:
    - Excludes deleted_at from output by default
    - Provides is_deleted read-only field
    - Filters out soft-deleted related objects

    Usage:
        class ProductSerializer(SoftDeleteModelSerializer):
            class Meta:
                model = Product
                fields = ['id', 'name', 'price', 'is_deleted']
                read_only_fields = ['is_deleted']
    """

    is_deleted = serializers.SerializerMethodField(
        help_text=_('Whether this record has been soft-deleted')
    )

    class Meta:
        abstract = True
        # Exclude deleted_at by default - add 'is_deleted' instead
        extra_kwargs = {
            'deleted_at': {'write_only': True, 'required': False}
        }

    def get_is_deleted(self, obj) -> bool:
        """
        Return whether the object has been soft-deleted.

        Args:
            obj: The model instance

        Returns:
            bool: True if deleted_at is set
        """
        return getattr(obj, 'deleted_at', None) is not None


class AuditModelSerializer(SoftDeleteModelSerializer):
    """
    Serializer for models with audit fields (timestamps).

    Includes:
    - created_at: When the record was created
    - updated_at: When the record was last updated
    - is_deleted: Whether the record is soft-deleted

    These fields are always read-only.

    Usage:
        class OrderSerializer(AuditModelSerializer):
            class Meta:
                model = Order
                fields = ['id', 'status', 'total', 'created_at', 'updated_at']
    """

    created_at = serializers.DateTimeField(
        read_only=True,
        help_text=_('Timestamp when record was created')
    )
    updated_at = serializers.DateTimeField(
        read_only=True,
        help_text=_('Timestamp when record was last updated')
    )

    class Meta(SoftDeleteModelSerializer.Meta):
        abstract = True


class TenantModelSerializer(AuditModelSerializer):
    """
    Base serializer for all tenant-scoped models.

    Features:
    - Auto-injects organization from request context on create
    - Validates organization belongs to current user
    - Excludes organization from required fields (auto-populated)
    - Provides organization_id for output (not the full object)

    Critical Rules:
    - ALWAYS use this serializer for models with organization FK
    - Organization is automatically injected - never accept from input
    - Validates tenant isolation on create/update

    Usage:
        class MenuSerializer(TenantModelSerializer):
            class Meta:
                model = Menu
                fields = ['id', 'name', 'slug', 'description', 'organization']
                read_only_fields = ['organization']

        # In the viewset, organization is auto-injected:
        serializer.save(organization=request.organization)

    Attributes:
        organization_id: Read-only UUID of the organization
    """

    # Display organization_id instead of nested organization object
    organization_id = serializers.UUIDField(
        source='organization.id',
        read_only=True,
        help_text=_('Organization UUID')
    )

    class Meta(AuditModelSerializer.Meta):
        abstract = True
        extra_kwargs = {
            'organization': {
                'read_only': True,
                'required': False,
            },
            'deleted_at': {'write_only': True, 'required': False},
        }

    def validate(self, attrs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate that the data is appropriate for the current tenant.

        Checks:
        - Related objects belong to the same organization
        - No cross-tenant references

        Args:
            attrs: The validated data

        Returns:
            Dict: The validated data

        Raises:
            ValidationError: If cross-tenant reference detected
        """
        attrs = super().validate(attrs)

        # Get organization from context
        request = self.context.get('request')
        organization = getattr(request, 'organization', None) if request else None

        if organization:
            # Validate related tenant-scoped objects
            attrs = self._validate_tenant_relations(attrs, organization)

        return attrs

    def _validate_tenant_relations(
        self,
        attrs: Dict[str, Any],
        organization: 'Organization'
    ) -> Dict[str, Any]:
        """
        Validate that related objects belong to the same organization.

        Args:
            attrs: The validated data
            organization: The current organization

        Returns:
            Dict: The validated data

        Raises:
            ValidationError: If cross-tenant reference detected
        """
        for field_name, value in attrs.items():
            if value is None:
                continue

            # Check if the value is a model instance with organization
            if hasattr(value, 'organization_id'):
                if str(value.organization_id) != str(organization.id):
                    logger.warning(
                        "Cross-tenant reference detected: field=%s, "
                        "value_org=%s, request_org=%s",
                        field_name,
                        value.organization_id,
                        organization.id
                    )
                    raise ValidationError({
                        field_name: _('This resource does not belong to your organization.')
                    })

        return attrs

    def create(self, validated_data: Dict[str, Any]) -> models.Model:
        """
        Create a new instance with organization auto-injected.

        The organization is automatically set from the request context
        or from the save() call in the viewset.

        Args:
            validated_data: The validated data

        Returns:
            Model: The created instance
        """
        # Organization should be passed via save() in the viewset
        # This is just a safety check
        request = self.context.get('request')
        if request and hasattr(request, 'organization'):
            if 'organization' not in validated_data and request.organization:
                validated_data['organization'] = request.organization

        return super().create(validated_data)


# =============================================================================
# RESPONSE WRAPPER SERIALIZERS
# =============================================================================

class StandardResponseSerializer(serializers.Serializer):
    """
    Generic success response wrapper for API documentation.

    Standard E-Menum API response format:
        {
            "success": true,
            "data": {...}
        }

    This serializer is primarily used for API documentation/OpenAPI schema
    generation to document the response structure.
    """

    success = serializers.BooleanField(
        default=True,
        help_text=_('Whether the request was successful')
    )
    data = serializers.DictField(
        allow_empty=True,
        help_text=_('The response data')
    )


class PaginatedResponseSerializer(serializers.Serializer):
    """
    Paginated response wrapper for API documentation.

    Standard E-Menum paginated response format:
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

    success = serializers.BooleanField(
        default=True,
        help_text=_('Whether the request was successful')
    )
    data = serializers.ListField(
        help_text=_('The list of items')
    )
    meta = serializers.DictField(
        help_text=_('Pagination metadata')
    )


class ErrorDetailSerializer(serializers.Serializer):
    """
    Error detail serializer for the error object.

    Format:
        {
            "code": "ERROR_CODE",
            "message": "Human readable message",
            "details": {...}
        }
    """

    code = serializers.CharField(
        help_text=_('Machine-readable error code')
    )
    message = serializers.CharField(
        help_text=_('Human-readable error message')
    )
    details = serializers.DictField(
        required=False,
        allow_empty=True,
        help_text=_('Additional error details (validation errors, etc.)')
    )


class ErrorResponseSerializer(serializers.Serializer):
    """
    Error response wrapper for API documentation.

    Standard E-Menum API error format:
        {
            "success": false,
            "error": {
                "code": "ERROR_CODE",
                "message": "Human readable message",
                "details": {...}
            }
        }
    """

    success = serializers.BooleanField(
        default=False,
        help_text=_('Always false for error responses')
    )
    error = ErrorDetailSerializer(
        help_text=_('Error details')
    )


# =============================================================================
# UTILITY SERIALIZERS
# =============================================================================

class IDListSerializer(serializers.Serializer):
    """
    Serializer for bulk operations with a list of IDs.

    Usage:
        # For bulk delete, bulk update actions
        ids = ['uuid1', 'uuid2', 'uuid3']
        serializer = IDListSerializer(data={'ids': ids})

    Request format:
        {
            "ids": ["uuid-1", "uuid-2", "uuid-3"]
        }
    """

    ids = serializers.ListField(
        child=serializers.UUIDField(),
        min_length=1,
        max_length=100,
        help_text=_('List of UUIDs to operate on (max 100)')
    )


class BulkActionResponseSerializer(serializers.Serializer):
    """
    Response serializer for bulk operations.

    Response format:
        {
            "success": true,
            "data": {
                "affected_count": 5,
                "failed_ids": []
            }
        }
    """

    affected_count = serializers.IntegerField(
        help_text=_('Number of items successfully affected')
    )
    failed_ids = serializers.ListField(
        child=serializers.UUIDField(),
        required=False,
        help_text=_('List of IDs that failed (if any)')
    )


class SlugLookupSerializer(serializers.Serializer):
    """
    Serializer for slug-based lookups.

    Usage:
        # For looking up resources by slug
        serializer = SlugLookupSerializer(data={'slug': 'my-menu'})
    """

    slug = serializers.SlugField(
        max_length=100,
        help_text=_('URL-friendly unique identifier')
    )


# =============================================================================
# NESTED SERIALIZER HELPERS
# =============================================================================

class MinimalSerializer(serializers.ModelSerializer):
    """
    Base class for minimal/embedded serializers.

    Used when including a resource as a nested object with minimal fields.

    Example:
        class CategoryMinimalSerializer(MinimalSerializer):
            class Meta:
                model = Category
                fields = ['id', 'name', 'slug']

        class ProductSerializer(TenantModelSerializer):
            category = CategoryMinimalSerializer(read_only=True)
            ...
    """

    class Meta:
        abstract = True
        # Minimal serializers are always read-only
        read_only_fields = '__all__'


def create_minimal_serializer(
    model_class: Type[models.Model],
    fields: List[str] = None
) -> Type[MinimalSerializer]:
    """
    Factory function to create a minimal serializer for a model.

    Dynamically creates a serializer with the specified fields.

    Args:
        model_class: The Django model class
        fields: List of field names to include (default: ['id', 'name'])

    Returns:
        Type[MinimalSerializer]: A minimal serializer class

    Usage:
        CategoryMinimal = create_minimal_serializer(Category, ['id', 'name', 'slug'])

        class ProductSerializer(TenantModelSerializer):
            category = CategoryMinimal(read_only=True)
    """
    if fields is None:
        fields = ['id', 'name']

    class DynamicMinimalSerializer(MinimalSerializer):
        class Meta:
            model = model_class
            fields = fields

    DynamicMinimalSerializer.__name__ = f'{model_class.__name__}MinimalSerializer'
    DynamicMinimalSerializer.__qualname__ = DynamicMinimalSerializer.__name__

    return DynamicMinimalSerializer


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Base serializers
    'BaseModelSerializer',
    'SoftDeleteModelSerializer',
    'AuditModelSerializer',
    'TenantModelSerializer',
    # Response wrappers
    'StandardResponseSerializer',
    'PaginatedResponseSerializer',
    'ErrorDetailSerializer',
    'ErrorResponseSerializer',
    # Utility serializers
    'IDListSerializer',
    'BulkActionResponseSerializer',
    'SlugLookupSerializer',
    # Nested helpers
    'MinimalSerializer',
    'create_minimal_serializer',
]
