"""
Serializers for the Menu application.

This module provides DRF serializers for all menu-related models:
- ThemeSerializer: Menu styling customization
- MenuSerializer: Restaurant menu containers
- CategorySerializer: Product categories with nested support
- ProductSerializer: Individual menu items
- ProductVariantSerializer: Size/portion options
- ProductModifierSerializer: Add-on options
- AllergenSerializer: Platform-level allergen definitions
- ProductAllergenSerializer: Product-allergen relationships
- NutritionInfoSerializer: Nutritional data per product

API Response Format:
    All serializers work with the E-Menum standard response format:
    {
        "success": true,
        "data": {...}
    }

Multi-Tenancy:
    All tenant-scoped serializers (Menu, Category, Product, etc.) use
    TenantModelSerializer which auto-injects organization from request context.

Critical Rules:
    - Use TenantModelSerializer for tenant-scoped models
    - Never expose deleted_at field in public API responses
    - Always validate cross-tenant references
"""


from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

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
from shared.serializers.base import (
    TenantModelSerializer,
    SoftDeleteModelSerializer,
    MinimalSerializer,
)


# =============================================================================
# MINIMAL SERIALIZERS (For nested representations)
# =============================================================================

class ThemeMinimalSerializer(MinimalSerializer):
    """Minimal theme serializer for nested representations."""

    class Meta:
        model = Theme
        fields = ['id', 'name', 'slug', 'primary_color', 'is_default']


class MenuMinimalSerializer(MinimalSerializer):
    """Minimal menu serializer for nested representations."""

    class Meta:
        model = Menu
        fields = ['id', 'name', 'slug', 'is_published', 'is_default']


class CategoryMinimalSerializer(MinimalSerializer):
    """Minimal category serializer for nested representations."""

    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'is_active', 'sort_order']


class ProductMinimalSerializer(MinimalSerializer):
    """Minimal product serializer for nested representations."""

    class Meta:
        model = Product
        fields = ['id', 'name', 'slug', 'base_price', 'currency', 'is_active', 'is_available']


class AllergenMinimalSerializer(MinimalSerializer):
    """Minimal allergen serializer for nested representations."""

    class Meta:
        model = Allergen
        fields = ['id', 'name', 'code', 'icon']


# =============================================================================
# THEME SERIALIZERS
# =============================================================================

class ThemeListSerializer(TenantModelSerializer):
    """
    Serializer for theme list view.

    Returns a simplified view of themes suitable for listing.
    """

    class Meta:
        model = Theme
        fields = [
            'id',
            'name',
            'slug',
            'primary_color',
            'secondary_color',
            'is_default',
            'is_active',
            'organization_id',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['organization_id', 'created_at', 'updated_at']


class ThemeDetailSerializer(TenantModelSerializer):
    """
    Serializer for theme detail view.

    Returns full theme information including all styling options.
    """

    menu_count = serializers.SerializerMethodField(
        help_text=_('Number of menus using this theme')
    )

    class Meta:
        model = Theme
        fields = [
            'id',
            'name',
            'slug',
            'description',
            'primary_color',
            'secondary_color',
            'background_color',
            'text_color',
            'accent_color',
            'font_family',
            'heading_font_family',
            'logo_position',
            'custom_css',
            'settings',
            'is_default',
            'is_active',
            'organization_id',
            'created_at',
            'updated_at',
            'menu_count',
        ]
        read_only_fields = ['organization_id', 'created_at', 'updated_at', 'menu_count']

    def get_menu_count(self, obj) -> int:
        """Get the number of menus using this theme."""
        return obj.menus.filter(deleted_at__isnull=True).count()


class ThemeCreateSerializer(TenantModelSerializer):
    """
    Serializer for creating a new theme.
    """

    class Meta:
        model = Theme
        fields = [
            'name',
            'slug',
            'description',
            'primary_color',
            'secondary_color',
            'background_color',
            'text_color',
            'accent_color',
            'font_family',
            'heading_font_family',
            'logo_position',
            'custom_css',
            'settings',
            'is_default',
            'is_active',
        ]

    def validate_slug(self, value: str) -> str:
        """Validate slug uniqueness within organization."""
        request = self.context.get('request')
        organization = getattr(request, 'organization', None) if request else None

        if organization:
            existing = Theme.objects.filter(
                organization=organization,
                slug=value,
                deleted_at__isnull=True
            ).exists()
            if existing:
                raise ValidationError(_('A theme with this slug already exists.'))

        return value


class ThemeUpdateSerializer(TenantModelSerializer):
    """
    Serializer for updating an existing theme.
    """

    class Meta:
        model = Theme
        fields = [
            'name',
            'slug',
            'description',
            'primary_color',
            'secondary_color',
            'background_color',
            'text_color',
            'accent_color',
            'font_family',
            'heading_font_family',
            'logo_position',
            'custom_css',
            'settings',
            'is_default',
            'is_active',
        ]

    def validate_slug(self, value: str) -> str:
        """Validate slug uniqueness within organization (excluding current theme)."""
        request = self.context.get('request')
        organization = getattr(request, 'organization', None) if request else None
        instance = self.instance

        if organization and instance:
            existing = Theme.objects.filter(
                organization=organization,
                slug=value,
                deleted_at__isnull=True
            ).exclude(pk=instance.pk).exists()
            if existing:
                raise ValidationError(_('A theme with this slug already exists.'))

        return value


# =============================================================================
# MENU SERIALIZERS
# =============================================================================

class MenuListSerializer(TenantModelSerializer):
    """
    Serializer for menu list view.

    Returns a simplified view of menus suitable for listing.
    """

    theme = ThemeMinimalSerializer(read_only=True)
    category_count = serializers.IntegerField(
        source='category_count',
        read_only=True,
        help_text=_('Number of categories in this menu')
    )

    class Meta:
        model = Menu
        fields = [
            'id',
            'name',
            'slug',
            'description',
            'is_published',
            'is_default',
            'theme',
            'sort_order',
            'organization_id',
            'created_at',
            'updated_at',
            'category_count',
        ]
        read_only_fields = ['organization_id', 'created_at', 'updated_at', 'category_count']


class MenuDetailSerializer(TenantModelSerializer):
    """
    Serializer for menu detail view.

    Returns full menu information including theme and categories.
    """

    theme = ThemeMinimalSerializer(read_only=True)
    theme_id = serializers.UUIDField(
        write_only=True,
        required=False,
        allow_null=True,
        help_text=_('Theme UUID to associate with this menu')
    )
    categories = CategoryMinimalSerializer(many=True, read_only=True)
    category_count = serializers.SerializerMethodField(
        help_text=_('Number of categories in this menu')
    )

    class Meta:
        model = Menu
        fields = [
            'id',
            'name',
            'slug',
            'description',
            'is_published',
            'published_at',
            'is_default',
            'theme',
            'theme_id',
            'settings',
            'sort_order',
            'organization_id',
            'created_at',
            'updated_at',
            'categories',
            'category_count',
        ]
        read_only_fields = [
            'organization_id',
            'created_at',
            'updated_at',
            'published_at',
            'categories',
            'category_count',
        ]

    def get_category_count(self, obj) -> int:
        """Get the number of active categories."""
        return obj.categories.filter(deleted_at__isnull=True).count()


class MenuCreateSerializer(TenantModelSerializer):
    """
    Serializer for creating a new menu.
    """

    theme_id = serializers.UUIDField(
        required=False,
        allow_null=True,
        help_text=_('Theme UUID to associate with this menu')
    )

    class Meta:
        model = Menu
        fields = [
            'name',
            'slug',
            'description',
            'is_published',
            'is_default',
            'theme_id',
            'settings',
            'sort_order',
        ]

    def validate_slug(self, value: str) -> str:
        """Validate slug uniqueness within organization."""
        request = self.context.get('request')
        organization = getattr(request, 'organization', None) if request else None

        if organization:
            existing = Menu.objects.filter(
                organization=organization,
                slug=value,
                deleted_at__isnull=True
            ).exists()
            if existing:
                raise ValidationError(_('A menu with this slug already exists.'))

        return value

    def validate_theme_id(self, value):
        """Validate theme belongs to the same organization."""
        if value is None:
            return None

        request = self.context.get('request')
        organization = getattr(request, 'organization', None) if request else None

        if organization:
            try:
                theme = Theme.objects.get(
                    id=value,
                    organization=organization,
                    deleted_at__isnull=True
                )
                return theme
            except Theme.DoesNotExist:
                raise ValidationError(_('Theme not found.'))

        return value

    def create(self, validated_data):
        """Create menu with theme handling."""
        theme = validated_data.pop('theme_id', None)
        if theme:
            validated_data['theme'] = theme
        return super().create(validated_data)


class MenuUpdateSerializer(TenantModelSerializer):
    """
    Serializer for updating an existing menu.
    """

    theme_id = serializers.UUIDField(
        required=False,
        allow_null=True,
        help_text=_('Theme UUID to associate with this menu')
    )

    class Meta:
        model = Menu
        fields = [
            'name',
            'slug',
            'description',
            'is_published',
            'is_default',
            'theme_id',
            'settings',
            'sort_order',
        ]

    def validate_slug(self, value: str) -> str:
        """Validate slug uniqueness within organization (excluding current menu)."""
        request = self.context.get('request')
        organization = getattr(request, 'organization', None) if request else None
        instance = self.instance

        if organization and instance:
            existing = Menu.objects.filter(
                organization=organization,
                slug=value,
                deleted_at__isnull=True
            ).exclude(pk=instance.pk).exists()
            if existing:
                raise ValidationError(_('A menu with this slug already exists.'))

        return value

    def validate_theme_id(self, value):
        """Validate theme belongs to the same organization."""
        if value is None:
            return None

        request = self.context.get('request')
        organization = getattr(request, 'organization', None) if request else None

        if organization:
            try:
                theme = Theme.objects.get(
                    id=value,
                    organization=organization,
                    deleted_at__isnull=True
                )
                return theme
            except Theme.DoesNotExist:
                raise ValidationError(_('Theme not found.'))

        return value

    def update(self, instance, validated_data):
        """Update menu with theme handling."""
        theme = validated_data.pop('theme_id', None)
        if theme is not None:
            validated_data['theme'] = theme
        return super().update(instance, validated_data)


# =============================================================================
# CATEGORY SERIALIZERS
# =============================================================================

class CategoryListSerializer(TenantModelSerializer):
    """
    Serializer for category list view.
    """

    menu = MenuMinimalSerializer(read_only=True)
    parent = CategoryMinimalSerializer(read_only=True)
    product_count = serializers.SerializerMethodField(
        help_text=_('Number of products in this category')
    )

    class Meta:
        model = Category
        fields = [
            'id',
            'name',
            'slug',
            'description',
            'image',
            'menu',
            'parent',
            'is_active',
            'sort_order',
            'organization_id',
            'created_at',
            'updated_at',
            'product_count',
        ]
        read_only_fields = [
            'organization_id',
            'created_at',
            'updated_at',
            'product_count',
        ]

    def get_product_count(self, obj) -> int:
        """Get the number of active products in this category."""
        return obj.products.filter(deleted_at__isnull=True).count()


class CategoryDetailSerializer(TenantModelSerializer):
    """
    Serializer for category detail view.

    Returns full category information including children and products.
    """

    menu = MenuMinimalSerializer(read_only=True)
    menu_id = serializers.UUIDField(
        write_only=True,
        required=False,
        help_text=_('Menu UUID this category belongs to')
    )
    parent = CategoryMinimalSerializer(read_only=True)
    parent_id = serializers.UUIDField(
        write_only=True,
        required=False,
        allow_null=True,
        help_text=_('Parent category UUID for nested structure')
    )
    children = CategoryMinimalSerializer(many=True, read_only=True)
    products = ProductMinimalSerializer(many=True, read_only=True)
    product_count = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = [
            'id',
            'name',
            'slug',
            'description',
            'image',
            'menu',
            'menu_id',
            'parent',
            'parent_id',
            'is_active',
            'sort_order',
            'organization_id',
            'created_at',
            'updated_at',
            'children',
            'products',
            'product_count',
        ]
        read_only_fields = [
            'organization_id',
            'created_at',
            'updated_at',
            'children',
            'products',
            'product_count',
        ]

    def get_product_count(self, obj) -> int:
        """Get the number of active products in this category."""
        return obj.products.filter(deleted_at__isnull=True).count()


class CategoryCreateSerializer(TenantModelSerializer):
    """
    Serializer for creating a new category.
    """

    menu_id = serializers.UUIDField(
        required=True,
        help_text=_('Menu UUID this category belongs to')
    )
    parent_id = serializers.UUIDField(
        required=False,
        allow_null=True,
        help_text=_('Parent category UUID for nested structure')
    )

    class Meta:
        model = Category
        fields = [
            'name',
            'slug',
            'description',
            'image',
            'menu_id',
            'parent_id',
            'is_active',
            'sort_order',
        ]

    def validate_menu_id(self, value):
        """Validate menu belongs to the same organization."""
        request = self.context.get('request')
        organization = getattr(request, 'organization', None) if request else None

        if organization:
            try:
                menu = Menu.objects.get(
                    id=value,
                    organization=organization,
                    deleted_at__isnull=True
                )
                return menu
            except Menu.DoesNotExist:
                raise ValidationError(_('Menu not found.'))

        raise ValidationError(_('Organization context required.'))

    def validate_parent_id(self, value):
        """Validate parent category belongs to the same organization."""
        if value is None:
            return None

        request = self.context.get('request')
        organization = getattr(request, 'organization', None) if request else None

        if organization:
            try:
                parent = Category.objects.get(
                    id=value,
                    organization=organization,
                    deleted_at__isnull=True
                )
                return parent
            except Category.DoesNotExist:
                raise ValidationError(_('Parent category not found.'))

        return value

    def validate(self, attrs):
        """Validate cross-field constraints."""
        attrs = super().validate(attrs)

        menu = attrs.get('menu_id')
        parent = attrs.get('parent_id')
        slug = attrs.get('slug')

        # Validate parent belongs to the same menu
        if parent and menu:
            if parent.menu_id != menu.id:
                raise ValidationError({
                    'parent_id': _('Parent category must belong to the same menu.')
                })

        # Validate slug uniqueness within menu
        if menu and slug:
            existing = Category.objects.filter(
                menu=menu,
                slug=slug,
                deleted_at__isnull=True
            ).exists()
            if existing:
                raise ValidationError({
                    'slug': _('A category with this slug already exists in this menu.')
                })

        return attrs

    def create(self, validated_data):
        """Create category with menu and parent handling."""
        menu = validated_data.pop('menu_id')
        parent = validated_data.pop('parent_id', None)

        validated_data['menu'] = menu
        if parent:
            validated_data['parent'] = parent

        return super().create(validated_data)


class CategoryUpdateSerializer(TenantModelSerializer):
    """
    Serializer for updating an existing category.
    """

    parent_id = serializers.UUIDField(
        required=False,
        allow_null=True,
        help_text=_('Parent category UUID for nested structure')
    )

    class Meta:
        model = Category
        fields = [
            'name',
            'slug',
            'description',
            'image',
            'parent_id',
            'is_active',
            'sort_order',
        ]

    def validate_parent_id(self, value):
        """Validate parent category belongs to the same organization."""
        if value is None:
            return None

        request = self.context.get('request')
        organization = getattr(request, 'organization', None) if request else None
        instance = self.instance

        if organization:
            try:
                parent = Category.objects.get(
                    id=value,
                    organization=organization,
                    deleted_at__isnull=True
                )
                # Prevent circular reference
                if instance and str(parent.id) == str(instance.id):
                    raise ValidationError(_('Cannot set category as its own parent.'))
                return parent
            except Category.DoesNotExist:
                raise ValidationError(_('Parent category not found.'))

        return value

    def validate(self, attrs):
        """Validate cross-field constraints."""
        attrs = super().validate(attrs)

        instance = self.instance
        parent = attrs.get('parent_id')
        slug = attrs.get('slug')

        # Validate parent belongs to the same menu
        if parent and instance:
            if parent.menu_id != instance.menu_id:
                raise ValidationError({
                    'parent_id': _('Parent category must belong to the same menu.')
                })

        # Validate slug uniqueness within menu (excluding current)
        if instance and slug:
            existing = Category.objects.filter(
                menu=instance.menu,
                slug=slug,
                deleted_at__isnull=True
            ).exclude(pk=instance.pk).exists()
            if existing:
                raise ValidationError({
                    'slug': _('A category with this slug already exists in this menu.')
                })

        return attrs

    def update(self, instance, validated_data):
        """Update category with parent handling."""
        parent = validated_data.pop('parent_id', None)
        if parent is not None:
            validated_data['parent'] = parent
        return super().update(instance, validated_data)


# =============================================================================
# PRODUCT SERIALIZERS
# =============================================================================

class ProductVariantSerializer(TenantModelSerializer):
    """
    Serializer for product variants (inline in product detail).
    """

    class Meta:
        model = ProductVariant
        fields = [
            'id',
            'name',
            'price',
            'is_default',
            'is_available',
            'sort_order',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class ProductModifierSerializer(TenantModelSerializer):
    """
    Serializer for product modifiers (inline in product detail).
    """

    class Meta:
        model = ProductModifier
        fields = [
            'id',
            'name',
            'price',
            'is_default',
            'is_required',
            'max_quantity',
            'sort_order',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class ProductAllergenSerializer(serializers.ModelSerializer):
    """
    Serializer for product-allergen relationships.
    """

    allergen = AllergenMinimalSerializer(read_only=True)
    allergen_id = serializers.UUIDField(
        write_only=True,
        help_text=_('Allergen UUID')
    )

    class Meta:
        model = ProductAllergen
        fields = [
            'id',
            'allergen',
            'allergen_id',
            'severity',
            'notes',
        ]
        read_only_fields = ['id', 'allergen']


class NutritionInfoSerializer(serializers.ModelSerializer):
    """
    Serializer for product nutrition information.
    """

    class Meta:
        model = NutritionInfo
        fields = [
            'id',
            'serving_size',
            'serving_size_grams',
            'calories',
            'protein',
            'carbohydrates',
            'sugar',
            'fiber',
            'fat',
            'saturated_fat',
            'trans_fat',
            'cholesterol',
            'sodium',
            'potassium',
            'calcium',
            'iron',
            'vitamin_a',
            'vitamin_c',
            'custom_nutrients',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class ProductListSerializer(TenantModelSerializer):
    """
    Serializer for product list view.
    """

    category = CategoryMinimalSerializer(read_only=True)

    class Meta:
        model = Product
        fields = [
            'id',
            'name',
            'slug',
            'short_description',
            'base_price',
            'currency',
            'image',
            'category',
            'is_active',
            'is_available',
            'is_featured',
            'is_chef_recommended',
            'spicy_level',
            'sort_order',
            'organization_id',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['organization_id', 'created_at', 'updated_at']


class ProductDetailSerializer(TenantModelSerializer):
    """
    Serializer for product detail view.

    Returns full product information including variants, modifiers, allergens.
    """

    category = CategoryMinimalSerializer(read_only=True)
    category_id = serializers.UUIDField(
        write_only=True,
        required=False,
        help_text=_('Category UUID this product belongs to')
    )
    variants = ProductVariantSerializer(many=True, read_only=True)
    modifiers = ProductModifierSerializer(many=True, read_only=True)
    product_allergens = ProductAllergenSerializer(many=True, read_only=True)
    nutrition_info = NutritionInfoSerializer(read_only=True)

    class Meta:
        model = Product
        fields = [
            'id',
            'name',
            'slug',
            'description',
            'short_description',
            'base_price',
            'currency',
            'image',
            'gallery',
            'category',
            'category_id',
            'is_active',
            'is_available',
            'is_featured',
            'is_chef_recommended',
            'preparation_time',
            'calories',
            'spicy_level',
            'tags',
            'sort_order',
            'organization_id',
            'created_at',
            'updated_at',
            'variants',
            'modifiers',
            'product_allergens',
            'nutrition_info',
        ]
        read_only_fields = [
            'organization_id',
            'created_at',
            'updated_at',
            'variants',
            'modifiers',
            'product_allergens',
            'nutrition_info',
        ]


class ProductCreateSerializer(TenantModelSerializer):
    """
    Serializer for creating a new product.
    """

    category_id = serializers.UUIDField(
        required=True,
        help_text=_('Category UUID this product belongs to')
    )

    class Meta:
        model = Product
        fields = [
            'name',
            'slug',
            'description',
            'short_description',
            'base_price',
            'currency',
            'image',
            'gallery',
            'category_id',
            'is_active',
            'is_available',
            'is_featured',
            'is_chef_recommended',
            'preparation_time',
            'calories',
            'spicy_level',
            'tags',
            'sort_order',
        ]

    def validate_category_id(self, value):
        """Validate category belongs to the same organization."""
        request = self.context.get('request')
        organization = getattr(request, 'organization', None) if request else None

        if organization:
            try:
                category = Category.objects.get(
                    id=value,
                    organization=organization,
                    deleted_at__isnull=True
                )
                return category
            except Category.DoesNotExist:
                raise ValidationError(_('Category not found.'))

        raise ValidationError(_('Organization context required.'))

    def validate(self, attrs):
        """Validate cross-field constraints."""
        attrs = super().validate(attrs)

        category = attrs.get('category_id')
        slug = attrs.get('slug')

        # Validate slug uniqueness within category
        if category and slug:
            existing = Product.objects.filter(
                category=category,
                slug=slug,
                deleted_at__isnull=True
            ).exists()
            if existing:
                raise ValidationError({
                    'slug': _('A product with this slug already exists in this category.')
                })

        return attrs

    def create(self, validated_data):
        """Create product with category handling."""
        category = validated_data.pop('category_id')
        validated_data['category'] = category
        return super().create(validated_data)


class ProductUpdateSerializer(TenantModelSerializer):
    """
    Serializer for updating an existing product.
    """

    category_id = serializers.UUIDField(
        required=False,
        help_text=_('Category UUID this product belongs to')
    )

    class Meta:
        model = Product
        fields = [
            'name',
            'slug',
            'description',
            'short_description',
            'base_price',
            'currency',
            'image',
            'gallery',
            'category_id',
            'is_active',
            'is_available',
            'is_featured',
            'is_chef_recommended',
            'preparation_time',
            'calories',
            'spicy_level',
            'tags',
            'sort_order',
        ]

    def validate_category_id(self, value):
        """Validate category belongs to the same organization."""
        request = self.context.get('request')
        organization = getattr(request, 'organization', None) if request else None

        if organization:
            try:
                category = Category.objects.get(
                    id=value,
                    organization=organization,
                    deleted_at__isnull=True
                )
                return category
            except Category.DoesNotExist:
                raise ValidationError(_('Category not found.'))

        return value

    def validate(self, attrs):
        """Validate cross-field constraints."""
        attrs = super().validate(attrs)

        instance = self.instance
        category = attrs.get('category_id', instance.category if instance else None)
        slug = attrs.get('slug')

        # Validate slug uniqueness within category (excluding current)
        if instance and slug:
            existing = Product.objects.filter(
                category=category,
                slug=slug,
                deleted_at__isnull=True
            ).exclude(pk=instance.pk).exists()
            if existing:
                raise ValidationError({
                    'slug': _('A product with this slug already exists in this category.')
                })

        return attrs

    def update(self, instance, validated_data):
        """Update product with category handling."""
        category = validated_data.pop('category_id', None)
        if category is not None:
            validated_data['category'] = category
        return super().update(instance, validated_data)


# =============================================================================
# ALLERGEN SERIALIZERS (Platform-level, not tenant-scoped)
# =============================================================================

class AllergenListSerializer(SoftDeleteModelSerializer):
    """
    Serializer for allergen list view.

    Allergens are platform-level (not tenant-scoped).
    """

    class Meta:
        model = Allergen
        fields = [
            'id',
            'name',
            'slug',
            'code',
            'icon',
            'is_active',
            'sort_order',
        ]
        read_only_fields = ['id']


class AllergenDetailSerializer(SoftDeleteModelSerializer):
    """
    Serializer for allergen detail view.
    """

    class Meta:
        model = Allergen
        fields = [
            'id',
            'name',
            'slug',
            'code',
            'icon',
            'description',
            'is_active',
            'sort_order',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Minimal serializers
    'ThemeMinimalSerializer',
    'MenuMinimalSerializer',
    'CategoryMinimalSerializer',
    'ProductMinimalSerializer',
    'AllergenMinimalSerializer',
    # Theme serializers
    'ThemeListSerializer',
    'ThemeDetailSerializer',
    'ThemeCreateSerializer',
    'ThemeUpdateSerializer',
    # Menu serializers
    'MenuListSerializer',
    'MenuDetailSerializer',
    'MenuCreateSerializer',
    'MenuUpdateSerializer',
    # Category serializers
    'CategoryListSerializer',
    'CategoryDetailSerializer',
    'CategoryCreateSerializer',
    'CategoryUpdateSerializer',
    # Product serializers
    'ProductListSerializer',
    'ProductDetailSerializer',
    'ProductCreateSerializer',
    'ProductUpdateSerializer',
    # Related serializers
    'ProductVariantSerializer',
    'ProductModifierSerializer',
    'ProductAllergenSerializer',
    'NutritionInfoSerializer',
    # Allergen serializers
    'AllergenListSerializer',
    'AllergenDetailSerializer',
]
