"""
URL configuration for the Menu application.

This module defines URL patterns for:
- Theme management (CRUD)
- Menu management (CRUD + publish/unpublish)
- Category management (CRUD with nested support)
- Product management (CRUD with variants/modifiers)
- Allergen information (read-only, platform-level)

URL Structure:
    /api/v1/themes/
        GET /                    - List themes
        POST /                   - Create theme
        GET /<id>/               - Get theme details
        PUT/PATCH /<id>/         - Update theme
        DELETE /<id>/            - Soft delete theme
        POST /<id>/set-default/  - Set as default theme

    /api/v1/menus/
        GET /                    - List menus
        POST /                   - Create menu
        GET /<id>/               - Get menu details
        PUT/PATCH /<id>/         - Update menu
        DELETE /<id>/            - Soft delete menu
        POST /<id>/publish/      - Publish menu
        POST /<id>/unpublish/    - Unpublish menu
        POST /<id>/set-default/  - Set as default menu

    /api/v1/categories/
        GET /                    - List categories
        POST /                   - Create category
        GET /<id>/               - Get category details
        PUT/PATCH /<id>/         - Update category
        DELETE /<id>/            - Soft delete category

    /api/v1/products/
        GET /                    - List products
        POST /                   - Create product
        GET /<id>/               - Get product details
        PUT/PATCH /<id>/         - Update product
        DELETE /<id>/            - Soft delete product
        POST /<id>/toggle-featured/  - Toggle featured status
        POST /<id>/toggle-available/ - Toggle availability

    /api/v1/products/<id>/variants/
        GET /                    - List product variants
        POST /                   - Create variant
        GET /<variant_id>/       - Get variant details
        PUT/PATCH /<variant_id>/ - Update variant
        DELETE /<variant_id>/    - Soft delete variant

    /api/v1/products/<id>/modifiers/
        GET /                    - List product modifiers
        POST /                   - Create modifier
        GET /<modifier_id>/      - Get modifier details
        PUT/PATCH /<modifier_id>/ - Update modifier
        DELETE /<modifier_id>/   - Soft delete modifier

    /api/v1/allergens/
        GET /                    - List allergens (public)
        GET /<id>/               - Get allergen details (public)

Usage:
    In config/urls.py:
        path('api/v1/', include('apps.menu.urls')),

    Or for specific namespace:
        path('api/v1/', include(('apps.menu.urls', 'menu'), namespace='menu')),
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_nested import routers

from apps.menu.views import (
    ThemeViewSet,
    MenuViewSet,
    CategoryViewSet,
    ProductViewSet,
    ProductVariantViewSet,
    ProductModifierViewSet,
    AllergenViewSet,
)


app_name = 'menu'


# =============================================================================
# ROUTER CONFIGURATION
# =============================================================================

# Main router for top-level resources
router = DefaultRouter()
router.register(r'themes', ThemeViewSet, basename='theme')
router.register(r'menus', MenuViewSet, basename='menu')
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'products', ProductViewSet, basename='product')
router.register(r'allergens', AllergenViewSet, basename='allergen')

# Nested router for product variants and modifiers
products_router = routers.NestedDefaultRouter(router, r'products', lookup='product')
products_router.register(r'variants', ProductVariantViewSet, basename='product-variants')
products_router.register(r'modifiers', ProductModifierViewSet, basename='product-modifiers')


# =============================================================================
# URL PATTERNS
# =============================================================================

urlpatterns = [
    path('', include(router.urls)),
    path('', include(products_router.urls)),
]
