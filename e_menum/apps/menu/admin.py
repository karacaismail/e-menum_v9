"""
Django Admin configuration for the Menu application.

This module defines admin interfaces for menu models:
- Menu
- Category
- Product
- ProductVariant
- ProductModifier
- Allergen
- Theme
- ProductAllergen
- NutritionInfo

All admin classes implement multi-tenant filtering where applicable.
Soft-deleted records are filtered out by default in all applicable models.
"""

from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from apps.menu.models import (
    Allergen,
    Category,
    Menu,
    NutritionInfo,
    Product,
    ProductAllergen,
    ProductModifier,
    ProductVariant,
    Theme,
)


class SoftDeleteAdminMixin:
    """
    Mixin that filters out soft-deleted records in the admin queryset.

    Add this mixin to any ModelAdmin that manages a model with soft delete.
    """

    def get_queryset(self, request):
        """Filter out soft-deleted records by default."""
        qs = super().get_queryset(request)
        if hasattr(qs.model, 'deleted_at'):
            return qs.filter(deleted_at__isnull=True)
        return qs


# =============================================================================
# Inline Admin Classes
# =============================================================================


class CategoryInline(admin.TabularInline):
    """Inline admin for categories within a menu."""

    model = Category
    extra = 0
    show_change_link = True
    fields = ['name', 'slug', 'is_active', 'sort_order']
    readonly_fields = ['slug']
    ordering = ['sort_order', 'name']

    def get_queryset(self, request):
        """Filter out soft-deleted categories."""
        qs = super().get_queryset(request)
        return qs.filter(deleted_at__isnull=True)


class ProductInline(admin.TabularInline):
    """Inline admin for products within a category."""

    model = Product
    extra = 0
    show_change_link = True
    fields = ['name', 'base_price', 'is_active', 'is_available', 'sort_order']
    readonly_fields = []
    ordering = ['sort_order', 'name']

    def get_queryset(self, request):
        """Filter out soft-deleted products."""
        qs = super().get_queryset(request)
        return qs.filter(deleted_at__isnull=True)


class ProductVariantInline(admin.TabularInline):
    """Inline admin for product variants."""

    model = ProductVariant
    extra = 0
    fields = ['name', 'price', 'is_default', 'is_available', 'sort_order']
    ordering = ['sort_order', 'name']

    def get_queryset(self, request):
        """Filter out soft-deleted variants."""
        qs = super().get_queryset(request)
        return qs.filter(deleted_at__isnull=True)


class ProductModifierInline(admin.TabularInline):
    """Inline admin for product modifiers."""

    model = ProductModifier
    extra = 0
    fields = ['name', 'price', 'is_default', 'is_required', 'max_quantity', 'sort_order']
    ordering = ['sort_order', 'name']

    def get_queryset(self, request):
        """Filter out soft-deleted modifiers."""
        qs = super().get_queryset(request)
        return qs.filter(deleted_at__isnull=True)


class ProductAllergenInline(admin.TabularInline):
    """Inline admin for product allergens."""

    model = ProductAllergen
    extra = 0
    fields = ['allergen', 'severity', 'notes']
    autocomplete_fields = ['allergen']

    def get_queryset(self, request):
        """Filter out soft-deleted product allergens."""
        qs = super().get_queryset(request)
        return qs.filter(deleted_at__isnull=True)


# =============================================================================
# Theme Admin
# =============================================================================


@admin.register(Theme)
class ThemeAdmin(SoftDeleteAdminMixin, admin.ModelAdmin):
    """
    Admin interface for Theme management.

    Provides comprehensive management of menu themes including:
    - Color customization
    - Typography settings
    - Custom CSS
    - Default theme selection

    Note: Soft-deleted themes are hidden by default.
    """

    list_display = [
        'name',
        'organization',
        'color_preview',
        'is_default',
        'is_active',
        'created_at',
    ]
    list_filter = ['is_default', 'is_active', 'organization', 'created_at']
    search_fields = ['name', 'slug', 'organization__name']
    readonly_fields = ['id', 'created_at', 'updated_at', 'deleted_at']
    ordering = ['-is_default', 'name']
    date_hierarchy = 'created_at'
    list_per_page = 25
    prepopulated_fields = {'slug': ('name',)}

    fieldsets = (
        (None, {
            'fields': ('id', 'organization', 'name', 'slug', 'description'),
            'description': _('Basic theme information')
        }),
        (_('Colors'), {
            'fields': (
                'primary_color',
                'secondary_color',
                'background_color',
                'text_color',
                'accent_color',
            ),
            'description': _('Theme color settings (hex format)')
        }),
        (_('Typography'), {
            'fields': ('font_family', 'heading_font_family'),
        }),
        (_('Layout'), {
            'fields': ('logo_position',),
        }),
        (_('Advanced'), {
            'fields': ('custom_css', 'settings'),
            'classes': ('collapse',),
            'description': _('Advanced customization options')
        }),
        (_('Status'), {
            'fields': ('is_default', 'is_active'),
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at', 'deleted_at'),
            'classes': ('collapse',),
        }),
    )

    def color_preview(self, obj):
        """Display color swatches for the theme."""
        return format_html(
            '<span style="display: inline-block; width: 20px; height: 20px; '
            'background-color: {}; border: 1px solid #ccc; margin-right: 4px;" '
            'title="Primary"></span>'
            '<span style="display: inline-block; width: 20px; height: 20px; '
            'background-color: {}; border: 1px solid #ccc; margin-right: 4px;" '
            'title="Secondary"></span>'
            '<span style="display: inline-block; width: 20px; height: 20px; '
            'background-color: {}; border: 1px solid #ccc;" '
            'title="Background"></span>',
            obj.primary_color,
            obj.secondary_color,
            obj.background_color
        )
    color_preview.short_description = _('Colors')

    actions = ['set_as_default', 'activate_themes', 'deactivate_themes']

    @admin.action(description=_('Set as default theme'))
    def set_as_default(self, request, queryset):
        """Bulk action to set selected theme as default (uses first selected)."""
        if queryset.count() > 1:
            self.message_user(
                request,
                _('Please select only one theme to set as default.'),
                level='warning'
            )
            return
        theme = queryset.first()
        if theme:
            theme.set_as_default()
            self.message_user(
                request,
                _('%(name)s has been set as default.') % {'name': theme.name}
            )

    @admin.action(description=_('Activate selected themes'))
    def activate_themes(self, request, queryset):
        """Bulk action to activate selected themes."""
        count = queryset.update(is_active=True)
        self.message_user(
            request,
            _('%(count)d theme(s) have been activated.') % {'count': count}
        )

    @admin.action(description=_('Deactivate selected themes'))
    def deactivate_themes(self, request, queryset):
        """Bulk action to deactivate selected themes."""
        count = queryset.update(is_active=False)
        self.message_user(
            request,
            _('%(count)d theme(s) have been deactivated.') % {'count': count}
        )


# =============================================================================
# Menu Admin
# =============================================================================


@admin.register(Menu)
class MenuAdmin(SoftDeleteAdminMixin, admin.ModelAdmin):
    """
    Admin interface for Menu management.

    Provides comprehensive management of restaurant menus including:
    - Publication status
    - Default menu selection
    - Theme assignment
    - Category overview via inline

    Note: Soft-deleted menus are hidden by default.
    """

    list_display = [
        'name',
        'organization',
        'status_badge',
        'is_default',
        'category_count',
        'theme',
        'created_at',
    ]
    list_filter = ['is_published', 'is_default', 'organization', 'created_at']
    search_fields = ['name', 'slug', 'description', 'organization__name']
    readonly_fields = ['id', 'created_at', 'updated_at', 'deleted_at', 'published_at']
    ordering = ['-is_default', 'sort_order', 'name']
    date_hierarchy = 'created_at'
    list_per_page = 25
    prepopulated_fields = {'slug': ('name',)}
    autocomplete_fields = ['organization', 'theme']
    inlines = [CategoryInline]

    fieldsets = (
        (None, {
            'fields': ('id', 'organization', 'name', 'slug', 'description'),
            'description': _('Basic menu information')
        }),
        (_('Publication'), {
            'fields': ('is_published', 'published_at', 'is_default'),
            'description': _('Control menu visibility and default status')
        }),
        (_('Styling'), {
            'fields': ('theme',),
        }),
        (_('Settings'), {
            'fields': ('sort_order', 'settings'),
            'classes': ('collapse',),
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at', 'deleted_at'),
            'classes': ('collapse',),
        }),
    )

    def status_badge(self, obj):
        """Display publication status with color-coded badge."""
        if obj.is_published:
            return format_html(
                '<span style="background-color: #28a745; color: white; padding: 3px 10px; '
                'border-radius: 3px; font-size: 11px; font-weight: bold;">{}</span>',
                _('Published')
            )
        return format_html(
            '<span style="background-color: #6c757d; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-size: 11px; font-weight: bold;">{}</span>',
            _('Draft')
        )
    status_badge.short_description = _('Status')
    status_badge.admin_order_field = 'is_published'

    def category_count(self, obj):
        """Display the number of active categories."""
        count = obj.category_count
        return format_html(
            '<span style="color: {};">{}</span>',
            '#28a745' if count > 0 else '#6c757d',
            count
        )
    category_count.short_description = _('Categories')

    actions = ['publish_menus', 'unpublish_menus', 'set_as_default']

    @admin.action(description=_('Publish selected menus'))
    def publish_menus(self, request, queryset):
        """Bulk action to publish selected menus."""
        for menu in queryset:
            menu.publish()
        self.message_user(
            request,
            _('%(count)d menu(s) have been published.') % {'count': queryset.count()}
        )

    @admin.action(description=_('Unpublish selected menus'))
    def unpublish_menus(self, request, queryset):
        """Bulk action to unpublish selected menus."""
        for menu in queryset:
            menu.unpublish()
        self.message_user(
            request,
            _('%(count)d menu(s) have been unpublished.') % {'count': queryset.count()}
        )

    @admin.action(description=_('Set as default menu'))
    def set_as_default(self, request, queryset):
        """Bulk action to set selected menu as default (uses first selected)."""
        if queryset.count() > 1:
            self.message_user(
                request,
                _('Please select only one menu to set as default.'),
                level='warning'
            )
            return
        menu = queryset.first()
        if menu:
            menu.set_as_default()
            self.message_user(
                request,
                _('%(name)s has been set as default.') % {'name': menu.name}
            )


# =============================================================================
# Category Admin
# =============================================================================


@admin.register(Category)
class CategoryAdmin(SoftDeleteAdminMixin, admin.ModelAdmin):
    """
    Admin interface for Category management.

    Provides comprehensive management of menu categories including:
    - Hierarchical structure (parent categories)
    - Product count display
    - Active/inactive status
    - Sort order management

    Note: Soft-deleted categories are hidden by default.
    """

    list_display = [
        'name',
        'menu',
        'parent',
        'product_count_display',
        'is_active',
        'sort_order',
        'created_at',
    ]
    list_filter = ['is_active', 'menu', 'menu__organization', 'created_at']
    search_fields = ['name', 'slug', 'description', 'menu__name', 'menu__organization__name']
    readonly_fields = ['id', 'created_at', 'updated_at', 'deleted_at']
    ordering = ['menu', 'sort_order', 'name']
    date_hierarchy = 'created_at'
    list_per_page = 25
    prepopulated_fields = {'slug': ('name',)}
    autocomplete_fields = ['organization', 'menu', 'parent']
    inlines = [ProductInline]

    fieldsets = (
        (None, {
            'fields': ('id', 'organization', 'menu', 'name', 'slug', 'description'),
            'description': _('Basic category information')
        }),
        (_('Hierarchy'), {
            'fields': ('parent',),
            'description': _('Optional parent category for nested structure')
        }),
        (_('Display'), {
            'fields': ('image', 'is_active', 'sort_order'),
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at', 'deleted_at'),
            'classes': ('collapse',),
        }),
    )

    def product_count_display(self, obj):
        """Display the number of active products."""
        count = obj.product_count
        return format_html(
            '<span style="color: {};">{}</span>',
            '#28a745' if count > 0 else '#6c757d',
            count
        )
    product_count_display.short_description = _('Products')

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """Filter parent category options to same menu and exclude self."""
        if db_field.name == "parent":
            # Get the object being edited
            if hasattr(request, '_obj_') and request._obj_:
                kwargs['queryset'] = Category.objects.filter(
                    menu=request._obj_.menu,
                    deleted_at__isnull=True
                ).exclude(pk=request._obj_.pk)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def get_form(self, request, obj=None, **kwargs):
        """Store the object for use in formfield_for_foreignkey."""
        request._obj_ = obj
        return super().get_form(request, obj, **kwargs)

    actions = ['activate_categories', 'deactivate_categories']

    @admin.action(description=_('Activate selected categories'))
    def activate_categories(self, request, queryset):
        """Bulk action to activate selected categories."""
        count = queryset.update(is_active=True)
        self.message_user(
            request,
            _('%(count)d category(ies) have been activated.') % {'count': count}
        )

    @admin.action(description=_('Deactivate selected categories'))
    def deactivate_categories(self, request, queryset):
        """Bulk action to deactivate selected categories."""
        count = queryset.update(is_active=False)
        self.message_user(
            request,
            _('%(count)d category(ies) have been deactivated.') % {'count': count}
        )


# =============================================================================
# Product Admin
# =============================================================================


@admin.register(Product)
class ProductAdmin(SoftDeleteAdminMixin, admin.ModelAdmin):
    """
    Admin interface for Product management.

    Provides comprehensive management of menu products including:
    - Pricing and availability
    - Featured and chef recommended flags
    - Variants, modifiers, and allergens via inlines
    - Tag management

    Note: Soft-deleted products are hidden by default.
    """

    list_display = [
        'name',
        'category',
        'price_display',
        'availability_badge',
        'is_featured',
        'is_chef_recommended',
        'sort_order',
        'created_at',
    ]
    list_filter = [
        'is_active',
        'is_available',
        'is_featured',
        'is_chef_recommended',
        'category__menu',
        'category__menu__organization',
        'created_at',
    ]
    search_fields = [
        'name',
        'slug',
        'description',
        'category__name',
        'category__menu__name',
        'category__menu__organization__name',
    ]
    readonly_fields = ['id', 'created_at', 'updated_at', 'deleted_at']
    ordering = ['category', 'sort_order', 'name']
    date_hierarchy = 'created_at'
    list_per_page = 25
    prepopulated_fields = {'slug': ('name',)}
    autocomplete_fields = ['organization', 'category']
    inlines = [ProductVariantInline, ProductModifierInline, ProductAllergenInline]

    fieldsets = (
        (None, {
            'fields': ('id', 'organization', 'category', 'name', 'slug'),
            'description': _('Basic product information')
        }),
        (_('Description'), {
            'fields': ('short_description', 'description'),
        }),
        (_('Pricing'), {
            'fields': ('base_price', 'currency'),
        }),
        (_('Images'), {
            'fields': ('image', 'gallery'),
            'classes': ('collapse',),
        }),
        (_('Availability & Status'), {
            'fields': ('is_active', 'is_available', 'is_featured', 'is_chef_recommended'),
        }),
        (_('Attributes'), {
            'fields': ('preparation_time', 'calories', 'spicy_level', 'tags'),
            'classes': ('collapse',),
        }),
        (_('Display'), {
            'fields': ('sort_order',),
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at', 'deleted_at'),
            'classes': ('collapse',),
        }),
    )

    def price_display(self, obj):
        """Display formatted price."""
        return format_html(
            '<span style="font-weight: bold; color: #28a745;">{}</span>',
            obj.formatted_price
        )
    price_display.short_description = _('Price')
    price_display.admin_order_field = 'base_price'

    def availability_badge(self, obj):
        """Display availability with color-coded badge."""
        if not obj.is_active:
            return format_html(
                '<span style="background-color: #6c757d; color: white; padding: 3px 10px; '
                'border-radius: 3px; font-size: 11px; font-weight: bold;">{}</span>',
                _('Inactive')
            )
        if obj.is_available:
            return format_html(
                '<span style="background-color: #28a745; color: white; padding: 3px 10px; '
                'border-radius: 3px; font-size: 11px; font-weight: bold;">{}</span>',
                _('Available')
            )
        return format_html(
            '<span style="background-color: #dc3545; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-size: 11px; font-weight: bold;">{}</span>',
            _('Out of Stock')
        )
    availability_badge.short_description = _('Availability')
    availability_badge.admin_order_field = 'is_available'

    actions = [
        'make_available',
        'make_unavailable',
        'toggle_featured',
        'toggle_chef_recommended',
    ]

    @admin.action(description=_('Mark as available'))
    def make_available(self, request, queryset):
        """Bulk action to mark products as available."""
        count = queryset.update(is_available=True)
        self.message_user(
            request,
            _('%(count)d product(s) have been marked as available.') % {'count': count}
        )

    @admin.action(description=_('Mark as out of stock'))
    def make_unavailable(self, request, queryset):
        """Bulk action to mark products as unavailable."""
        count = queryset.update(is_available=False)
        self.message_user(
            request,
            _('%(count)d product(s) have been marked as out of stock.') % {'count': count}
        )

    @admin.action(description=_('Toggle featured status'))
    def toggle_featured(self, request, queryset):
        """Bulk action to toggle featured status."""
        for product in queryset:
            product.toggle_featured()
        self.message_user(
            request,
            _('Featured status has been toggled for %(count)d product(s).') % {
                'count': queryset.count()
            }
        )

    @admin.action(description=_('Toggle chef recommended'))
    def toggle_chef_recommended(self, request, queryset):
        """Bulk action to toggle chef recommended status."""
        for product in queryset:
            product.toggle_chef_recommended()
        self.message_user(
            request,
            _('Chef recommended status has been toggled for %(count)d product(s).') % {
                'count': queryset.count()
            }
        )


# =============================================================================
# Allergen Admin (Platform-level)
# =============================================================================


@admin.register(Allergen)
class AllergenAdmin(SoftDeleteAdminMixin, admin.ModelAdmin):
    """
    Admin interface for Allergen management.

    Allergens are platform-level (not tenant-specific) and are used
    across all organizations to maintain consistency.

    Note: Soft-deleted allergens are hidden by default.
    """

    list_display = [
        'name',
        'code_display',
        'icon_preview',
        'is_active',
        'sort_order',
    ]
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'slug', 'code', 'description']
    readonly_fields = ['id', 'created_at', 'updated_at', 'deleted_at']
    ordering = ['sort_order', 'name']
    list_per_page = 25
    prepopulated_fields = {'slug': ('name',)}

    fieldsets = (
        (None, {
            'fields': ('id', 'name', 'slug', 'code'),
            'description': _('Basic allergen information')
        }),
        (_('Display'), {
            'fields': ('icon', 'description', 'sort_order'),
        }),
        (_('Status'), {
            'fields': ('is_active',),
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at', 'deleted_at'),
            'classes': ('collapse',),
        }),
    )

    def code_display(self, obj):
        """Display allergen code with styling."""
        return format_html(
            '<code style="background-color: #f1f1f1; padding: 2px 6px; '
            'border-radius: 3px; font-weight: bold;">{}</code>',
            obj.code
        )
    code_display.short_description = _('Code')
    code_display.admin_order_field = 'code'

    def icon_preview(self, obj):
        """Display icon preview if available."""
        if obj.icon:
            return format_html(
                '<img src="{}" style="width: 24px; height: 24px;" alt="{}"/>',
                obj.icon,
                obj.name
            )
        return format_html('<span style="color: #6c757d;">-</span>')
    icon_preview.short_description = _('Icon')

    actions = ['activate_allergens', 'deactivate_allergens']

    @admin.action(description=_('Activate selected allergens'))
    def activate_allergens(self, request, queryset):
        """Bulk action to activate selected allergens."""
        count = queryset.update(is_active=True)
        self.message_user(
            request,
            _('%(count)d allergen(s) have been activated.') % {'count': count}
        )

    @admin.action(description=_('Deactivate selected allergens'))
    def deactivate_allergens(self, request, queryset):
        """Bulk action to deactivate selected allergens."""
        count = queryset.update(is_active=False)
        self.message_user(
            request,
            _('%(count)d allergen(s) have been deactivated.') % {'count': count}
        )


# =============================================================================
# ProductVariant Admin
# =============================================================================


@admin.register(ProductVariant)
class ProductVariantAdmin(SoftDeleteAdminMixin, admin.ModelAdmin):
    """Admin interface for ProductVariant management."""

    list_display = [
        'name',
        'product',
        'price_display',
        'is_default',
        'is_available',
        'sort_order',
    ]
    list_filter = ['is_default', 'is_available', 'product__category__menu__organization']
    search_fields = ['name', 'product__name', 'product__category__name']
    readonly_fields = ['id', 'created_at', 'updated_at', 'deleted_at']
    ordering = ['product', 'sort_order', 'name']
    list_per_page = 50
    autocomplete_fields = ['product']

    fieldsets = (
        (None, {
            'fields': ('id', 'product', 'name'),
        }),
        (_('Pricing & Availability'), {
            'fields': ('price', 'is_default', 'is_available'),
        }),
        (_('Display'), {
            'fields': ('sort_order',),
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at', 'deleted_at'),
            'classes': ('collapse',),
        }),
    )

    def price_display(self, obj):
        """Display formatted price."""
        return format_html(
            '<span style="font-weight: bold;">{}</span>',
            obj.formatted_price
        )
    price_display.short_description = _('Price')
    price_display.admin_order_field = 'price'


# =============================================================================
# ProductModifier Admin
# =============================================================================


@admin.register(ProductModifier)
class ProductModifierAdmin(SoftDeleteAdminMixin, admin.ModelAdmin):
    """Admin interface for ProductModifier management."""

    list_display = [
        'name',
        'product',
        'price_display',
        'is_default',
        'is_required',
        'max_quantity',
        'sort_order',
    ]
    list_filter = ['is_default', 'is_required', 'product__category__menu__organization']
    search_fields = ['name', 'product__name', 'product__category__name']
    readonly_fields = ['id', 'created_at', 'updated_at', 'deleted_at']
    ordering = ['product', 'sort_order', 'name']
    list_per_page = 50
    autocomplete_fields = ['product']

    fieldsets = (
        (None, {
            'fields': ('id', 'product', 'name'),
        }),
        (_('Pricing & Behavior'), {
            'fields': ('price', 'is_default', 'is_required', 'max_quantity'),
        }),
        (_('Display'), {
            'fields': ('sort_order',),
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at', 'deleted_at'),
            'classes': ('collapse',),
        }),
    )

    def price_display(self, obj):
        """Display formatted price."""
        return format_html(
            '<span style="font-weight: bold;">{}</span>',
            obj.formatted_price
        )
    price_display.short_description = _('Price')
    price_display.admin_order_field = 'price'


# =============================================================================
# ProductAllergen Admin
# =============================================================================


@admin.register(ProductAllergen)
class ProductAllergenAdmin(SoftDeleteAdminMixin, admin.ModelAdmin):
    """Admin interface for ProductAllergen (junction table) management."""

    list_display = [
        'product',
        'allergen',
        'severity_badge',
        'created_at',
    ]
    list_filter = ['severity', 'allergen', 'product__category__menu__organization']
    search_fields = ['product__name', 'allergen__name', 'notes']
    readonly_fields = ['id', 'created_at', 'updated_at', 'deleted_at']
    ordering = ['product', 'allergen']
    list_per_page = 50
    autocomplete_fields = ['product', 'allergen']

    fieldsets = (
        (None, {
            'fields': ('id', 'product', 'allergen'),
        }),
        (_('Details'), {
            'fields': ('severity', 'notes'),
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at', 'deleted_at'),
            'classes': ('collapse',),
        }),
    )

    def severity_badge(self, obj):
        """Display severity with color-coded badge."""
        colors = {
            'contains': '#dc3545',
            'may_contain': '#ffc107',
            'traces': '#17a2b8',
        }
        color = colors.get(obj.severity, '#6c757d')
        text_color = '#000' if obj.severity == 'may_contain' else '#fff'
        return format_html(
            '<span style="background-color: {}; color: {}; padding: 3px 10px; '
            'border-radius: 3px; font-size: 11px; font-weight: bold;">{}</span>',
            color,
            text_color,
            obj.get_severity_display()
        )
    severity_badge.short_description = _('Severity')
    severity_badge.admin_order_field = 'severity'


# =============================================================================
# NutritionInfo Admin
# =============================================================================


@admin.register(NutritionInfo)
class NutritionInfoAdmin(SoftDeleteAdminMixin, admin.ModelAdmin):
    """Admin interface for NutritionInfo management."""

    list_display = [
        'product',
        'serving_size',
        'calories',
        'macros_summary',
        'created_at',
    ]
    list_filter = ['product__category__menu__organization']
    search_fields = ['product__name', 'product__category__name']
    readonly_fields = ['id', 'created_at', 'updated_at', 'deleted_at']
    ordering = ['product']
    list_per_page = 50
    autocomplete_fields = ['product']

    fieldsets = (
        (None, {
            'fields': ('id', 'product'),
        }),
        (_('Serving Information'), {
            'fields': ('serving_size', 'serving_size_grams'),
        }),
        (_('Energy'), {
            'fields': ('calories',),
        }),
        (_('Macronutrients'), {
            'fields': ('protein', 'carbohydrates', 'sugar', 'fiber', 'fat', 'saturated_fat', 'trans_fat'),
        }),
        (_('Micronutrients'), {
            'fields': ('cholesterol', 'sodium', 'potassium', 'calcium', 'iron'),
            'classes': ('collapse',),
        }),
        (_('Vitamins'), {
            'fields': ('vitamin_a', 'vitamin_c'),
            'classes': ('collapse',),
        }),
        (_('Custom Nutrients'), {
            'fields': ('custom_nutrients',),
            'classes': ('collapse',),
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at', 'deleted_at'),
            'classes': ('collapse',),
        }),
    )

    def macros_summary(self, obj):
        """Display a summary of macronutrients."""
        parts = []
        if obj.protein:
            parts.append(f'P: {obj.protein}g')
        if obj.carbohydrates:
            parts.append(f'C: {obj.carbohydrates}g')
        if obj.fat:
            parts.append(f'F: {obj.fat}g')
        if parts:
            return ' | '.join(parts)
        return format_html('<span style="color: #6c757d;">-</span>')
    macros_summary.short_description = _('Macros')
