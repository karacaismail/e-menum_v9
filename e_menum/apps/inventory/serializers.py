"""
DRF serializers for the Inventory application.

Provides serializers for all inventory models using the
TenantModelSerializer base class for automatic organization
handling and standard response format.
"""

from rest_framework import serializers

from shared.serializers.base import TenantModelSerializer

from apps.inventory.models import (
    InventoryItem,
    PurchaseOrder,
    PurchaseOrderItem,
    Recipe,
    RecipeIngredient,
    StockMovement,
    Supplier,
)


class SupplierSerializer(TenantModelSerializer):
    """Serializer for Supplier model."""

    class Meta:
        model = Supplier
        fields = [
            "id",
            "organization_id",
            "name",
            "contact_person",
            "email",
            "phone",
            "address",
            "tax_id",
            "is_active",
            "rating",
            "notes",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "organization_id", "created_at", "updated_at"]


class InventoryItemSerializer(TenantModelSerializer):
    """Serializer for InventoryItem model."""

    supplier_name = serializers.CharField(
        source="supplier.name", read_only=True, default=None
    )
    stock_value = serializers.DecimalField(
        max_digits=14,
        decimal_places=2,
        read_only=True,
    )
    is_low_stock = serializers.BooleanField(read_only=True)

    class Meta:
        model = InventoryItem
        fields = [
            "id",
            "organization_id",
            "name",
            "sku",
            "category",
            "unit_type",
            "current_stock",
            "min_stock_level",
            "max_stock_level",
            "cost_per_unit",
            "supplier",
            "supplier_name",
            "is_active",
            "stock_value",
            "is_low_stock",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "organization_id",
            "stock_value",
            "is_low_stock",
            "created_at",
            "updated_at",
        ]


class StockMovementSerializer(TenantModelSerializer):
    """Serializer for StockMovement model."""

    inventory_item_name = serializers.CharField(
        source="inventory_item.name",
        read_only=True,
    )
    created_by_email = serializers.CharField(
        source="created_by.email",
        read_only=True,
        default=None,
    )

    class Meta:
        model = StockMovement
        fields = [
            "id",
            "organization_id",
            "inventory_item",
            "inventory_item_name",
            "movement_type",
            "quantity",
            "unit_cost",
            "total_cost",
            "reference_number",
            "notes",
            "created_by",
            "created_by_email",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "organization_id",
            "created_by",
            "created_by_email",
            "created_at",
            "updated_at",
        ]


class PurchaseOrderItemSerializer(TenantModelSerializer):
    """Serializer for PurchaseOrderItem model."""

    inventory_item_name = serializers.CharField(
        source="inventory_item.name",
        read_only=True,
    )

    class Meta:
        model = PurchaseOrderItem
        fields = [
            "id",
            "purchase_order",
            "inventory_item",
            "inventory_item_name",
            "quantity_ordered",
            "quantity_received",
            "unit_cost",
            "total_cost",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class PurchaseOrderSerializer(TenantModelSerializer):
    """Serializer for PurchaseOrder model."""

    supplier_name = serializers.CharField(source="supplier.name", read_only=True)
    items = PurchaseOrderItemSerializer(many=True, read_only=True)
    created_by_email = serializers.CharField(
        source="created_by.email",
        read_only=True,
        default=None,
    )
    approved_by_email = serializers.CharField(
        source="approved_by.email",
        read_only=True,
        default=None,
    )

    class Meta:
        model = PurchaseOrder
        fields = [
            "id",
            "organization_id",
            "supplier",
            "supplier_name",
            "order_number",
            "status",
            "order_date",
            "expected_delivery",
            "actual_delivery",
            "subtotal",
            "tax_amount",
            "total_amount",
            "notes",
            "created_by",
            "created_by_email",
            "approved_by",
            "approved_by_email",
            "items",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "organization_id",
            "created_by",
            "created_by_email",
            "approved_by_email",
            "created_at",
            "updated_at",
        ]


class RecipeIngredientSerializer(TenantModelSerializer):
    """Serializer for RecipeIngredient model."""

    inventory_item_name = serializers.CharField(
        source="inventory_item.name",
        read_only=True,
    )
    effective_quantity = serializers.DecimalField(
        max_digits=12,
        decimal_places=3,
        read_only=True,
    )

    class Meta:
        model = RecipeIngredient
        fields = [
            "id",
            "recipe",
            "inventory_item",
            "inventory_item_name",
            "quantity_required",
            "unit_type",
            "waste_percentage",
            "effective_quantity",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "effective_quantity", "created_at", "updated_at"]


class RecipeSerializer(TenantModelSerializer):
    """Serializer for Recipe model."""

    product_name = serializers.CharField(source="product.name", read_only=True)
    ingredients = RecipeIngredientSerializer(many=True, read_only=True)

    class Meta:
        model = Recipe
        fields = [
            "id",
            "organization_id",
            "product",
            "product_name",
            "name",
            "description",
            "yield_quantity",
            "yield_unit",
            "preparation_time_minutes",
            "is_active",
            "ingredients",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "organization_id", "created_at", "updated_at"]
