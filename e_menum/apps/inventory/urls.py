"""
URL configuration for the Inventory application.

Uses DRF router for automatic URL generation from ViewSets.
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.inventory.views import (
    InventoryItemViewSet,
    PurchaseOrderItemViewSet,
    PurchaseOrderViewSet,
    RecipeIngredientViewSet,
    RecipeViewSet,
    StockMovementViewSet,
    SupplierViewSet,
)

router = DefaultRouter()
router.register(r'suppliers', SupplierViewSet, basename='supplier')
router.register(r'items', InventoryItemViewSet, basename='inventory-item')
router.register(r'movements', StockMovementViewSet, basename='stock-movement')
router.register(r'purchase-orders', PurchaseOrderViewSet, basename='purchase-order')
router.register(r'purchase-order-items', PurchaseOrderItemViewSet, basename='purchase-order-item')
router.register(r'recipes', RecipeViewSet, basename='recipe')
router.register(r'recipe-ingredients', RecipeIngredientViewSet, basename='recipe-ingredient')

app_name = 'inventory'

urlpatterns = [
    path('', include(router.urls)),
]
