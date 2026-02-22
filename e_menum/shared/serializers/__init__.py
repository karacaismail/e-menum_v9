"""
Base serializers for E-Menum Django REST Framework.

This module provides base serializer classes that implement
common functionality required across all DRF serializers:

- TenantModelSerializer: Auto-injects organization from request context
- SoftDeleteModelSerializer: Handles soft delete field exclusion
- AuditModelSerializer: Includes audit fields (created_at, updated_at, etc.)

Response Format:
    All API responses follow the standard format:

    Success:
        {
            "success": True,
            "data": {...}
        }

    Success with pagination:
        {
            "success": True,
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
            "success": False,
            "error": {
                "code": "ERROR_CODE",
                "message": "Human readable message",
                "details": {...}
            }
        }

Usage:
    from shared.serializers import TenantModelSerializer

    class MenuSerializer(TenantModelSerializer):
        class Meta:
            model = Menu
            fields = ['id', 'name', 'slug', ...]
"""

from shared.serializers.base import (
    # Base serializers
    BaseModelSerializer,
    SoftDeleteModelSerializer,
    AuditModelSerializer,
    TenantModelSerializer,
    # Response wrappers
    StandardResponseSerializer,
    PaginatedResponseSerializer,
    ErrorDetailSerializer,
    ErrorResponseSerializer,
    # Utility serializers
    IDListSerializer,
    BulkActionResponseSerializer,
    SlugLookupSerializer,
    # Nested helpers
    MinimalSerializer,
    create_minimal_serializer,
)

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
