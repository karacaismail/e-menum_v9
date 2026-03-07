"""
Base view classes for E-Menum Django REST Framework.

This module provides base view classes that implement common
functionality required across all DRF views:

- BaseTenantViewSet: ViewSet with automatic organization filtering
- BaseTenantAPIView: APIView with tenant context injection
- SoftDeleteMixin: Implements soft delete instead of hard delete

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
    from shared.views import BaseTenantViewSet

    class MenuViewSet(BaseTenantViewSet):
        queryset = Menu.objects.all()
        serializer_class = MenuSerializer
        permission_resource = 'menu'
"""

from shared.views.base import (
    # Pagination
    StandardPagination,
    # Mixins
    StandardResponseMixin,
    SoftDeleteMixin,
    TenantFilterMixin,
    # ViewSets
    BaseModelViewSet,
    BaseTenantViewSet,
    BaseReadOnlyViewSet,
    BaseTenantReadOnlyViewSet,
    # API Views
    BaseAPIView,
    BaseTenantAPIView,
)

__all__ = [
    # Pagination
    "StandardPagination",
    # Mixins
    "StandardResponseMixin",
    "SoftDeleteMixin",
    "TenantFilterMixin",
    # ViewSets
    "BaseModelViewSet",
    "BaseTenantViewSet",
    "BaseReadOnlyViewSet",
    "BaseTenantReadOnlyViewSet",
    # API Views
    "BaseAPIView",
    "BaseTenantAPIView",
]
