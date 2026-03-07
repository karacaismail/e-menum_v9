"""
Django admin configuration for the Inventory application.

Registers all inventory models with the Django admin site,
providing list displays, filters, and search capabilities.
"""

from django.contrib import admin

from apps.inventory.models import (
    InventoryItem,
    PurchaseOrder,
    PurchaseOrderItem,
    Recipe,
    RecipeIngredient,
    StockMovement,
    Supplier,
)
from shared.permissions.admin_permission_mixin import EMenumPermissionMixin


@admin.register(Supplier)
class SupplierAdmin(EMenumPermissionMixin, admin.ModelAdmin):
    list_display = [
        "name",
        "contact_person",
        "email",
        "phone",
        "rating",
        "is_active",
        "organization",
    ]
    list_filter = ["is_active", "rating", "organization"]
    search_fields = ["name", "contact_person", "email", "tax_id"]
    raw_id_fields = ["organization"]
    readonly_fields = ["id", "created_at", "updated_at", "deleted_at"]


@admin.register(InventoryItem)
class InventoryItemAdmin(EMenumPermissionMixin, admin.ModelAdmin):
    list_display = [
        "name",
        "sku",
        "category",
        "unit_type",
        "current_stock",
        "min_stock_level",
        "cost_per_unit",
        "is_active",
        "organization",
    ]
    list_filter = ["is_active", "unit_type", "category", "organization"]
    search_fields = ["name", "sku", "category"]
    raw_id_fields = ["organization", "supplier"]
    readonly_fields = ["id", "created_at", "updated_at", "deleted_at"]


@admin.register(StockMovement)
class StockMovementAdmin(EMenumPermissionMixin, admin.ModelAdmin):
    list_display = [
        "inventory_item",
        "movement_type",
        "quantity",
        "unit_cost",
        "total_cost",
        "reference_number",
        "created_by",
        "created_at",
    ]
    list_filter = ["movement_type", "organization"]
    search_fields = ["reference_number", "notes", "inventory_item__name"]
    raw_id_fields = ["organization", "inventory_item", "created_by"]
    readonly_fields = ["id", "created_at", "updated_at", "deleted_at"]


@admin.register(PurchaseOrder)
class PurchaseOrderAdmin(EMenumPermissionMixin, admin.ModelAdmin):
    list_display = [
        "order_number",
        "supplier",
        "status",
        "order_date",
        "expected_delivery",
        "total_amount",
        "organization",
    ]
    list_filter = ["status", "organization"]
    search_fields = ["order_number", "supplier__name", "notes"]
    raw_id_fields = ["organization", "supplier", "created_by", "approved_by"]
    readonly_fields = ["id", "created_at", "updated_at", "deleted_at"]


@admin.register(PurchaseOrderItem)
class PurchaseOrderItemAdmin(EMenumPermissionMixin, admin.ModelAdmin):
    list_display = [
        "purchase_order",
        "inventory_item",
        "quantity_ordered",
        "quantity_received",
        "unit_cost",
        "total_cost",
    ]
    list_filter = ["purchase_order__status"]
    search_fields = ["inventory_item__name", "purchase_order__order_number"]
    raw_id_fields = ["purchase_order", "inventory_item"]
    readonly_fields = ["id", "created_at", "updated_at", "deleted_at"]


@admin.register(Recipe)
class RecipeAdmin(EMenumPermissionMixin, admin.ModelAdmin):
    list_display = [
        "name",
        "product",
        "yield_quantity",
        "yield_unit",
        "preparation_time_minutes",
        "is_active",
        "organization",
    ]
    list_filter = ["is_active", "organization"]
    search_fields = ["name", "description", "product__name"]
    raw_id_fields = ["organization", "product"]
    readonly_fields = ["id", "created_at", "updated_at", "deleted_at"]


@admin.register(RecipeIngredient)
class RecipeIngredientAdmin(EMenumPermissionMixin, admin.ModelAdmin):
    list_display = [
        "recipe",
        "inventory_item",
        "quantity_required",
        "unit_type",
        "waste_percentage",
    ]
    list_filter = ["unit_type"]
    search_fields = ["recipe__name", "inventory_item__name"]
    raw_id_fields = ["recipe", "inventory_item"]
    readonly_fields = ["id", "created_at", "updated_at", "deleted_at"]
