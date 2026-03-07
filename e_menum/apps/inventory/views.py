"""
DRF ViewSets for the Inventory application.

Provides ViewSets for all inventory models using BaseTenantViewSet
for automatic organization filtering, soft delete, and standard
response format.

Critical Rules:
- All ViewSets use BaseTenantViewSet (automatic org filtering)
- StockMovement is read-only via BaseTenantReadOnlyViewSet
"""

from shared.views.base import BaseTenantViewSet, BaseTenantReadOnlyViewSet

from apps.inventory.models import (
    InventoryItem,
    PurchaseOrder,
    PurchaseOrderItem,
    Recipe,
    RecipeIngredient,
    StockMovement,
    Supplier,
)
from apps.inventory.serializers import (
    InventoryItemSerializer,
    PurchaseOrderItemSerializer,
    PurchaseOrderSerializer,
    RecipeIngredientSerializer,
    RecipeSerializer,
    StockMovementSerializer,
    SupplierSerializer,
)


class SupplierViewSet(BaseTenantViewSet):
    """ViewSet for Supplier CRUD operations."""

    queryset = Supplier.objects.all()
    serializer_class = SupplierSerializer
    permission_resource = "inventory"


class InventoryItemViewSet(BaseTenantViewSet):
    """ViewSet for InventoryItem CRUD operations."""

    queryset = InventoryItem.objects.select_related("supplier").all()
    serializer_class = InventoryItemSerializer
    permission_resource = "inventory"


class StockMovementViewSet(BaseTenantReadOnlyViewSet):
    """Read-only ViewSet for StockMovement records (audit trail)."""

    queryset = StockMovement.objects.select_related(
        "inventory_item",
        "created_by",
    ).all()
    serializer_class = StockMovementSerializer
    permission_resource = "inventory"


class PurchaseOrderViewSet(BaseTenantViewSet):
    """ViewSet for PurchaseOrder CRUD operations."""

    queryset = (
        PurchaseOrder.objects.select_related(
            "supplier",
            "created_by",
            "approved_by",
        )
        .prefetch_related("items__inventory_item")
        .all()
    )
    serializer_class = PurchaseOrderSerializer
    permission_resource = "inventory"

    def perform_create(self, serializer):
        """Auto-set created_by from request user."""
        organization = self.require_organization()
        serializer.save(
            organization=organization,
            created_by=self.request.user,
        )


class PurchaseOrderItemViewSet(BaseTenantViewSet):
    """ViewSet for PurchaseOrderItem CRUD operations."""

    queryset = PurchaseOrderItem.objects.select_related(
        "purchase_order",
        "inventory_item",
    ).all()
    serializer_class = PurchaseOrderItemSerializer
    permission_resource = "inventory"

    def get_queryset(self):
        """Filter by parent purchase order's organization."""
        qs = super().get_queryset()
        organization = self.get_organization()
        if organization:
            qs = qs.filter(purchase_order__organization=organization)
        return qs


class RecipeViewSet(BaseTenantViewSet):
    """ViewSet for Recipe CRUD operations."""

    queryset = (
        Recipe.objects.select_related("product")
        .prefetch_related(
            "ingredients__inventory_item",
        )
        .all()
    )
    serializer_class = RecipeSerializer
    permission_resource = "inventory"


class RecipeIngredientViewSet(BaseTenantViewSet):
    """ViewSet for RecipeIngredient CRUD operations."""

    queryset = RecipeIngredient.objects.select_related(
        "recipe",
        "inventory_item",
    ).all()
    serializer_class = RecipeIngredientSerializer
    permission_resource = "inventory"

    def get_queryset(self):
        """Filter by parent recipe's organization."""
        qs = super().get_queryset()
        organization = self.get_organization()
        if organization:
            qs = qs.filter(recipe__organization=organization)
        return qs
