"""
Base view classes for E-Menum Django REST Framework.

This module provides base view classes that implement common
functionality required across all DRF views:

- TenantViewSet: ViewSet with automatic organization filtering
- TenantAPIView: APIView with tenant context injection
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
        instance.deleted_at = timezone.now()
        instance.save()

    # INCORRECT
    def perform_destroy(self, instance):
        instance.delete()  # Physical deletion FORBIDDEN

Usage:
    from shared.views import TenantViewSet

    class MenuViewSet(TenantViewSet):
        queryset = Menu.objects.all()
        serializer_class = MenuSerializer
"""

# View classes will be implemented in separate files
# and exported here for clean imports

__all__ = []
