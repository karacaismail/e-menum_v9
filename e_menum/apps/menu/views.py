"""
Views for the Menu application.

This module provides ViewSets for menu-related models:
- ThemeViewSet: Menu styling customization CRUD
- MenuViewSet: Restaurant menu container CRUD
- CategoryViewSet: Product category CRUD with nested support
- ProductViewSet: Individual menu item CRUD
- ProductVariantViewSet: Size/portion options CRUD
- ProductModifierViewSet: Add-on options CRUD
- AllergenViewSet: Platform-level allergen list (read-only)

API Endpoints:
    /api/v1/themes/           - Theme CRUD
    /api/v1/menus/            - Menu CRUD
    /api/v1/categories/       - Category CRUD
    /api/v1/products/         - Product CRUD
    /api/v1/products/{id}/variants/    - Variant CRUD (nested)
    /api/v1/products/{id}/modifiers/   - Modifier CRUD (nested)
    /api/v1/allergens/        - Allergen list (read-only)

Multi-Tenancy:
    All ViewSets (except AllergenViewSet) use BaseTenantViewSet which
    automatically filters querysets by the current organization.

Critical Rules:
    - EVERY query MUST include organization filtering (handled by BaseTenantViewSet)
    - Use soft_delete() - never call delete() directly (handled by SoftDeleteMixin)
    - All responses follow E-Menum standard format (handled by StandardResponseMixin)
"""

import logging
from typing import Optional

from django.db import models
from django.db.models import Count, Prefetch
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from apps.menu.models import (
    Theme,
    Menu,
    Category,
    Product,
    ProductVariant,
    ProductModifier,
    Allergen,
    ProductAllergen,
    NutritionInfo,
)
from apps.menu.serializers import (
    # Theme
    ThemeListSerializer,
    ThemeDetailSerializer,
    ThemeCreateSerializer,
    ThemeUpdateSerializer,
    # Menu
    MenuListSerializer,
    MenuDetailSerializer,
    MenuCreateSerializer,
    MenuUpdateSerializer,
    # Category
    CategoryListSerializer,
    CategoryDetailSerializer,
    CategoryCreateSerializer,
    CategoryUpdateSerializer,
    # Product
    ProductListSerializer,
    ProductDetailSerializer,
    ProductCreateSerializer,
    ProductUpdateSerializer,
    # Related
    ProductVariantSerializer,
    ProductModifierSerializer,
    ProductAllergenSerializer,
    NutritionInfoSerializer,
    # Allergen
    AllergenListSerializer,
    AllergenDetailSerializer,
)
from shared.permissions.plan_enforcement import PlanEnforcementMixin
from shared.views.base import (
    BaseTenantViewSet,
    BaseReadOnlyViewSet,
    StandardResponseMixin,
    SoftDeleteMixin,
)


logger = logging.getLogger(__name__)


# =============================================================================
# THEME VIEWSET
# =============================================================================

class ThemeViewSet(BaseTenantViewSet):
    """
    ViewSet for theme management.

    Themes define the visual appearance of menus. Each organization can have
    multiple themes but only one can be set as default.

    API Endpoints:
        GET    /api/v1/themes/              - List organization themes
        POST   /api/v1/themes/              - Create a new theme
        GET    /api/v1/themes/{id}/         - Get theme details
        PUT    /api/v1/themes/{id}/         - Update theme
        PATCH  /api/v1/themes/{id}/         - Partial update theme
        DELETE /api/v1/themes/{id}/         - Soft delete theme
        POST   /api/v1/themes/{id}/set-default/  - Set as default theme

    Query Parameters:
        - is_active: Filter by active status (true/false)
        - search: Search by name

    Permissions:
        - Requires authentication
        - Requires organization membership
        - Requires theme.view, theme.create, theme.update, theme.delete permissions
    """

    queryset = Theme.objects.all()
    permission_resource = 'theme'

    def get_serializer_class(self):
        """Return the appropriate serializer based on action."""
        if self.action == 'list':
            return ThemeListSerializer
        elif self.action == 'create':
            return ThemeCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return ThemeUpdateSerializer
        return ThemeDetailSerializer

    def get_queryset(self):
        """
        Return themes filtered by organization with optional filters.
        """
        queryset = super().get_queryset()

        # Apply active filter if provided
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')

        # Apply search filter if provided
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(name__icontains=search)

        return queryset.order_by('-is_default', 'name')

    @action(detail=True, methods=['post'], url_path='set-default')
    def set_default(self, request, pk=None):
        """
        Set this theme as the default for the organization.

        POST /api/v1/themes/{id}/set-default/
            Response (200):
                {
                    "success": true,
                    "data": {
                        "message": "Theme set as default"
                    }
                }
        """
        theme = self.get_object()
        theme.set_as_default()

        return self.get_success_response({
            'message': str(_('Theme set as default'))
        })


# =============================================================================
# MENU VIEWSET
# =============================================================================

class MenuViewSet(PlanEnforcementMixin, BaseTenantViewSet):
    """
    ViewSet for menu management.

    Menus are the primary container for organizing a restaurant's offerings.
    Each organization can have multiple menus (e.g., breakfast, lunch, dinner).

    API Endpoints:
        GET    /api/v1/menus/               - List organization menus
        POST   /api/v1/menus/               - Create a new menu
        GET    /api/v1/menus/{id}/          - Get menu details
        PUT    /api/v1/menus/{id}/          - Update menu
        PATCH  /api/v1/menus/{id}/          - Partial update menu
        DELETE /api/v1/menus/{id}/          - Soft delete menu
        POST   /api/v1/menus/{id}/publish/  - Publish menu
        POST   /api/v1/menus/{id}/unpublish/ - Unpublish menu
        POST   /api/v1/menus/{id}/set-default/ - Set as default menu

    Query Parameters:
        - is_published: Filter by published status (true/false)
        - search: Search by name

    Permissions:
        - Requires authentication
        - Requires organization membership
        - Requires menu.view, menu.create, menu.update, menu.delete permissions

    Plan Enforcement:
        - Create action checks 'max_menus' limit from subscription plan
    """

    queryset = Menu.objects.all()
    permission_resource = 'menu'

    # Plan enforcement: limit menu creation per plan
    plan_limit_key = 'max_menus'
    plan_limit_model = Menu

    def get_serializer_class(self):
        """Return the appropriate serializer based on action."""
        if self.action == 'list':
            return MenuListSerializer
        elif self.action == 'create':
            return MenuCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return MenuUpdateSerializer
        return MenuDetailSerializer

    def get_queryset(self):
        """
        Return menus filtered by organization with optional filters.
        """
        queryset = super().get_queryset()

        # Optimize with select_related
        queryset = queryset.select_related('theme')

        # Prefetch categories for category_count
        queryset = queryset.prefetch_related(
            Prefetch(
                'categories',
                queryset=Category.objects.filter(deleted_at__isnull=True)
            )
        )

        # Apply published filter if provided
        is_published = self.request.query_params.get('is_published')
        if is_published is not None:
            queryset = queryset.filter(is_published=is_published.lower() == 'true')

        # Apply search filter if provided
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(name__icontains=search)

        return queryset.order_by('sort_order', 'name')

    @action(detail=True, methods=['post'])
    def publish(self, request, pk=None):
        """
        Publish the menu, making it visible to customers.

        POST /api/v1/menus/{id}/publish/
            Response (200):
                {
                    "success": true,
                    "data": {
                        "message": "Menu published",
                        "published_at": "2024-01-15T12:00:00Z"
                    }
                }
        """
        menu = self.get_object()
        menu.publish()

        return self.get_success_response({
            'message': str(_('Menu published')),
            'published_at': menu.published_at.isoformat() if menu.published_at else None
        })

    @action(detail=True, methods=['post'])
    def unpublish(self, request, pk=None):
        """
        Unpublish the menu, hiding it from customers.

        POST /api/v1/menus/{id}/unpublish/
            Response (200):
                {
                    "success": true,
                    "data": {
                        "message": "Menu unpublished"
                    }
                }
        """
        menu = self.get_object()
        menu.unpublish()

        return self.get_success_response({
            'message': str(_('Menu unpublished'))
        })

    @action(detail=True, methods=['post'], url_path='set-default')
    def set_default(self, request, pk=None):
        """
        Set this menu as the default for the organization.

        POST /api/v1/menus/{id}/set-default/
            Response (200):
                {
                    "success": true,
                    "data": {
                        "message": "Menu set as default"
                    }
                }
        """
        menu = self.get_object()
        menu.set_as_default()

        return self.get_success_response({
            'message': str(_('Menu set as default'))
        })


# =============================================================================
# CATEGORY VIEWSET
# =============================================================================

class CategoryViewSet(PlanEnforcementMixin, BaseTenantViewSet):
    """
    ViewSet for category management.

    Categories organize products within a menu. They support hierarchical
    structure through self-referential parent relationship.

    API Endpoints:
        GET    /api/v1/categories/          - List organization categories
        POST   /api/v1/categories/          - Create a new category
        GET    /api/v1/categories/{id}/     - Get category details
        PUT    /api/v1/categories/{id}/     - Update category
        PATCH  /api/v1/categories/{id}/     - Partial update category
        DELETE /api/v1/categories/{id}/     - Soft delete category

    Query Parameters:
        - menu_id: Filter by menu
        - parent_id: Filter by parent category (null for root categories)
        - is_active: Filter by active status (true/false)
        - search: Search by name

    Permissions:
        - Requires authentication
        - Requires organization membership
        - Requires category.view, category.create, category.update, category.delete permissions

    Plan Enforcement:
        - Create action checks 'max_categories' limit from subscription plan
    """

    queryset = Category.objects.all()
    permission_resource = 'category'

    # Plan enforcement: limit category creation per plan
    plan_limit_key = 'max_categories'
    plan_limit_model = Category

    def get_serializer_class(self):
        """Return the appropriate serializer based on action."""
        if self.action == 'list':
            return CategoryListSerializer
        elif self.action == 'create':
            return CategoryCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return CategoryUpdateSerializer
        return CategoryDetailSerializer

    def get_queryset(self):
        """
        Return categories filtered by organization with optional filters.
        """
        queryset = super().get_queryset()

        # Optimize with select_related
        queryset = queryset.select_related('menu', 'parent')

        # Filter by menu if provided
        menu_id = self.request.query_params.get('menu_id')
        if menu_id:
            queryset = queryset.filter(menu_id=menu_id)

        # Filter by parent (null for root categories)
        parent_id = self.request.query_params.get('parent_id')
        if parent_id is not None:
            if parent_id.lower() == 'null' or parent_id == '':
                queryset = queryset.filter(parent__isnull=True)
            else:
                queryset = queryset.filter(parent_id=parent_id)

        # Apply active filter if provided
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')

        # Apply search filter if provided
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(name__icontains=search)

        return queryset.order_by('sort_order', 'name')


# =============================================================================
# PRODUCT VIEWSET
# =============================================================================

class ProductViewSet(PlanEnforcementMixin, BaseTenantViewSet):
    """
    ViewSet for product management.

    Products are the core menu items that customers view and order.
    Each product belongs to a category.

    API Endpoints:
        GET    /api/v1/products/            - List organization products
        POST   /api/v1/products/            - Create a new product
        GET    /api/v1/products/{id}/       - Get product details
        PUT    /api/v1/products/{id}/       - Update product
        PATCH  /api/v1/products/{id}/       - Partial update product
        DELETE /api/v1/products/{id}/       - Soft delete product
        POST   /api/v1/products/{id}/toggle-featured/ - Toggle featured status
        POST   /api/v1/products/{id}/toggle-available/ - Toggle availability

    Query Parameters:
        - category_id: Filter by category
        - menu_id: Filter by menu (via category)
        - is_active: Filter by active status
        - is_available: Filter by availability
        - is_featured: Filter by featured status
        - is_chef_recommended: Filter by chef recommendation
        - search: Search by name
        - tags: Filter by tag (comma-separated)

    Permissions:
        - Requires authentication
        - Requires organization membership
        - Requires product.view, product.create, product.update, product.delete permissions

    Plan Enforcement:
        - Create action checks 'max_products' limit from subscription plan
    """

    queryset = Product.objects.all()
    permission_resource = 'product'

    # Plan enforcement: limit product creation per plan
    plan_limit_key = 'max_products'
    plan_limit_model = Product

    def get_serializer_class(self):
        """Return the appropriate serializer based on action."""
        if self.action == 'list':
            return ProductListSerializer
        elif self.action == 'create':
            return ProductCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return ProductUpdateSerializer
        return ProductDetailSerializer

    def get_queryset(self):
        """
        Return products filtered by organization with optional filters.
        """
        queryset = super().get_queryset()

        # Optimize with select_related and prefetch_related
        queryset = queryset.select_related('category', 'category__menu')

        # For detail view, prefetch related data
        if self.action == 'retrieve':
            queryset = queryset.prefetch_related(
                Prefetch(
                    'variants',
                    queryset=ProductVariant.objects.filter(deleted_at__isnull=True)
                        .order_by('sort_order', 'name')
                ),
                Prefetch(
                    'modifiers',
                    queryset=ProductModifier.objects.filter(deleted_at__isnull=True)
                        .order_by('sort_order', 'name')
                ),
                Prefetch(
                    'product_allergens',
                    queryset=ProductAllergen.objects.filter(deleted_at__isnull=True)
                        .select_related('allergen')
                ),
            )

        # Filter by category if provided
        category_id = self.request.query_params.get('category_id')
        if category_id:
            queryset = queryset.filter(category_id=category_id)

        # Filter by menu if provided (via category)
        menu_id = self.request.query_params.get('menu_id')
        if menu_id:
            queryset = queryset.filter(category__menu_id=menu_id)

        # Apply boolean filters
        for param in ['is_active', 'is_available', 'is_featured', 'is_chef_recommended']:
            value = self.request.query_params.get(param)
            if value is not None:
                queryset = queryset.filter(**{param: value.lower() == 'true'})

        # Apply search filter if provided
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                models.Q(name__icontains=search) |
                models.Q(description__icontains=search) |
                models.Q(short_description__icontains=search)
            )

        # Apply tag filter if provided
        tags = self.request.query_params.get('tags')
        if tags:
            tag_list = [t.strip().lower() for t in tags.split(',')]
            for tag in tag_list:
                queryset = queryset.filter(tags__contains=[tag])

        return queryset.order_by('sort_order', 'name')

    @action(detail=True, methods=['post'], url_path='toggle-featured')
    def toggle_featured(self, request, pk=None):
        """
        Toggle the featured status of the product.

        POST /api/v1/products/{id}/toggle-featured/
            Response (200):
                {
                    "success": true,
                    "data": {
                        "is_featured": true
                    }
                }
        """
        product = self.get_object()
        is_featured = product.toggle_featured()

        return self.get_success_response({
            'is_featured': is_featured
        })

    @action(detail=True, methods=['post'], url_path='toggle-available')
    def toggle_available(self, request, pk=None):
        """
        Toggle the availability status of the product.

        POST /api/v1/products/{id}/toggle-available/
            Response (200):
                {
                    "success": true,
                    "data": {
                        "is_available": false
                    }
                }
        """
        product = self.get_object()
        product.is_available = not product.is_available
        product.save(update_fields=['is_available', 'updated_at'])

        return self.get_success_response({
            'is_available': product.is_available
        })


# =============================================================================
# NESTED VIEWSETS (Variants, Modifiers)
# =============================================================================

class ProductVariantViewSet(StandardResponseMixin, SoftDeleteMixin, viewsets.ModelViewSet):
    """
    ViewSet for product variant management.

    Variants are nested under products and inherit organization context.

    API Endpoints:
        GET    /api/v1/products/{product_id}/variants/       - List variants
        POST   /api/v1/products/{product_id}/variants/       - Create variant
        GET    /api/v1/products/{product_id}/variants/{id}/  - Get variant
        PUT    /api/v1/products/{product_id}/variants/{id}/  - Update variant
        DELETE /api/v1/products/{product_id}/variants/{id}/  - Soft delete variant
    """

    serializer_class = ProductVariantSerializer
    permission_classes = [IsAuthenticated]

    def get_product(self):
        """Get the parent product and validate organization."""
        product_id = self.kwargs.get('product_pk')
        organization = getattr(self.request, 'organization', None)

        if not organization:
            return None

        try:
            return Product.objects.get(
                id=product_id,
                organization=organization,
                deleted_at__isnull=True
            )
        except Product.DoesNotExist:
            return None

    def get_queryset(self):
        """Return variants for the parent product."""
        product = self.get_product()
        if not product:
            return ProductVariant.objects.none()

        return ProductVariant.objects.filter(
            product=product,
            deleted_at__isnull=True
        ).order_by('sort_order', 'name')

    def perform_create(self, serializer):
        """Create variant linked to the parent product."""
        product = self.get_product()
        if not product:
            from rest_framework.exceptions import NotFound
            raise NotFound(_('Product not found'))
        serializer.save(product=product)


class ProductModifierViewSet(StandardResponseMixin, SoftDeleteMixin, viewsets.ModelViewSet):
    """
    ViewSet for product modifier management.

    Modifiers are nested under products and inherit organization context.

    API Endpoints:
        GET    /api/v1/products/{product_id}/modifiers/       - List modifiers
        POST   /api/v1/products/{product_id}/modifiers/       - Create modifier
        GET    /api/v1/products/{product_id}/modifiers/{id}/  - Get modifier
        PUT    /api/v1/products/{product_id}/modifiers/{id}/  - Update modifier
        DELETE /api/v1/products/{product_id}/modifiers/{id}/  - Soft delete modifier
    """

    serializer_class = ProductModifierSerializer
    permission_classes = [IsAuthenticated]

    def get_product(self):
        """Get the parent product and validate organization."""
        product_id = self.kwargs.get('product_pk')
        organization = getattr(self.request, 'organization', None)

        if not organization:
            return None

        try:
            return Product.objects.get(
                id=product_id,
                organization=organization,
                deleted_at__isnull=True
            )
        except Product.DoesNotExist:
            return None

    def get_queryset(self):
        """Return modifiers for the parent product."""
        product = self.get_product()
        if not product:
            return ProductModifier.objects.none()

        return ProductModifier.objects.filter(
            product=product,
            deleted_at__isnull=True
        ).order_by('sort_order', 'name')

    def perform_create(self, serializer):
        """Create modifier linked to the parent product."""
        product = self.get_product()
        if not product:
            from rest_framework.exceptions import NotFound
            raise NotFound(_('Product not found'))
        serializer.save(product=product)


# =============================================================================
# ALLERGEN VIEWSET (Platform-level, read-only)
# =============================================================================

class AllergenViewSet(BaseReadOnlyViewSet):
    """
    ViewSet for allergen information (read-only).

    Allergens are platform-level definitions, not tenant-specific.

    API Endpoints:
        GET    /api/v1/allergens/           - List all allergens
        GET    /api/v1/allergens/{id}/      - Get allergen details

    Query Parameters:
        - is_active: Filter by active status (true/false)
        - search: Search by name or code

    Permissions:
        - AllowAny (public endpoint for menu display)
    """

    queryset = Allergen.objects.filter(deleted_at__isnull=True)
    permission_classes = [AllowAny]

    def get_serializer_class(self):
        """Return the appropriate serializer based on action."""
        if self.action == 'list':
            return AllergenListSerializer
        return AllergenDetailSerializer

    def get_queryset(self):
        """Return allergens with optional filters."""
        queryset = super().get_queryset()

        # Apply active filter if provided
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')

        # Apply search filter if provided
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                models.Q(name__icontains=search) |
                models.Q(code__icontains=search)
            )

        return queryset.order_by('sort_order', 'name')


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    'ThemeViewSet',
    'MenuViewSet',
    'CategoryViewSet',
    'ProductViewSet',
    'ProductVariantViewSet',
    'ProductModifierViewSet',
    'AllergenViewSet',
]
