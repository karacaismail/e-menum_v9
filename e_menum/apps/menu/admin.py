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
from modeltranslation.admin import TabbedTranslationAdmin

from apps.menu.forms import CategoryAdminForm, ProductAdminForm
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
from shared.permissions.admin_permission_mixin import EMenumPermissionMixin


class SoftDeleteAdminMixin:
    """
    Mixin that filters out soft-deleted records in the admin queryset.

    Add this mixin to any ModelAdmin that manages a model with soft delete.
    """

    def get_queryset(self, request):
        """Filter out soft-deleted records by default."""
        qs = super().get_queryset(request)
        if hasattr(qs.model, "deleted_at"):
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
    fields = ["name", "slug", "is_active", "sort_order"]
    readonly_fields = ["slug"]
    ordering = ["sort_order", "name"]

    def get_queryset(self, request):
        """Filter out soft-deleted categories."""
        qs = super().get_queryset(request)
        return qs.filter(deleted_at__isnull=True)


class ProductInline(admin.TabularInline):
    """Inline admin for products within a category."""

    model = Product
    extra = 0
    show_change_link = True
    fields = ["name", "base_price", "is_active", "is_available", "sort_order"]
    readonly_fields = []
    ordering = ["sort_order", "name"]

    def get_queryset(self, request):
        """Filter out soft-deleted products."""
        qs = super().get_queryset(request)
        return qs.filter(deleted_at__isnull=True)


class ProductVariantInline(admin.TabularInline):
    """Inline admin for product variants."""

    model = ProductVariant
    extra = 0
    fields = ["name", "price", "is_default", "is_available", "sort_order"]
    ordering = ["sort_order", "name"]

    def get_queryset(self, request):
        """Filter out soft-deleted variants."""
        qs = super().get_queryset(request)
        return qs.filter(deleted_at__isnull=True)


class ProductModifierInline(admin.TabularInline):
    """Inline admin for product modifiers."""

    model = ProductModifier
    extra = 0
    fields = [
        "name",
        "price",
        "is_default",
        "is_required",
        "max_quantity",
        "sort_order",
    ]
    ordering = ["sort_order", "name"]

    def get_queryset(self, request):
        """Filter out soft-deleted modifiers."""
        qs = super().get_queryset(request)
        return qs.filter(deleted_at__isnull=True)


class ProductAllergenInline(admin.TabularInline):
    """Inline admin for product allergens."""

    model = ProductAllergen
    extra = 0
    fields = ["allergen", "severity", "notes"]
    autocomplete_fields = ["allergen"]

    def get_queryset(self, request):
        """Filter out soft-deleted product allergens."""
        qs = super().get_queryset(request)
        return qs.filter(deleted_at__isnull=True)


# =============================================================================
# Theme Admin
# =============================================================================


@admin.register(Theme)
class ThemeAdmin(EMenumPermissionMixin, SoftDeleteAdminMixin, TabbedTranslationAdmin):
    """
    Admin interface for Theme management.

    Provides comprehensive management of menu themes including:
    - Color customization (with visual color picker)
    - Typography settings
    - Layout settings (grid columns, border radius, layout mode, dark mode)
    - Custom CSS
    - Default theme selection

    Note: Soft-deleted themes are hidden by default.
    """

    list_display = [
        "name",
        "organization",
        "color_preview",
        "layout_info",
        "is_default",
        "is_active",
        "created_at",
    ]
    list_filter = ["is_default", "is_active", "organization", "created_at"]
    search_fields = ["name", "slug", "organization__name"]
    readonly_fields = [
        "id",
        "created_at",
        "updated_at",
        "deleted_at",
        "color_picker_preview",
    ]
    ordering = ["-is_default", "name"]
    date_hierarchy = "created_at"
    list_per_page = 25
    prepopulated_fields = {"slug": ("name",)}

    fieldsets = (
        (
            None,
            {
                "fields": ("id", "organization", "name", "slug", "description"),
                "description": _("Basic theme information"),
            },
        ),
        (
            _("Colors"),
            {
                "fields": (
                    "color_picker_preview",
                    "primary_color",
                    "secondary_color",
                    "background_color",
                    "text_color",
                    "accent_color",
                ),
                "description": _(
                    "Theme color settings (hex format). Use the color swatches or type hex values."
                ),
            },
        ),
        (
            _("Typography"),
            {
                "fields": ("font_family", "heading_font_family"),
            },
        ),
        (
            _("Layout & Display"),
            {
                "fields": ("logo_position", "settings"),
                "description": _(
                    'Layout settings. Use the "settings" JSON field for: '
                    '"layout" (wide/boxed), "grid_columns" (2/3/4/6), '
                    '"border_radius" (0-24), "dark_mode" (true/false)'
                ),
            },
        ),
        (
            _("Advanced"),
            {
                "fields": ("custom_css",),
                "classes": ("collapse",),
                "description": _("Advanced customization options"),
            },
        ),
        (
            _("Status"),
            {
                "fields": ("is_default", "is_active"),
            },
        ),
        (
            _("Timestamps"),
            {
                "fields": ("created_at", "updated_at", "deleted_at"),
                "classes": ("collapse",),
            },
        ),
    )

    class Media:
        css = {
            "all": ("admin/css/theme-admin.css",),
        }

    def color_preview(self, obj):
        """Display color swatches for the theme."""
        return format_html(
            '<span style="display: inline-flex; gap: 3px;">'
            '<span style="display: inline-block; width: 18px; height: 18px; '
            "background-color: {}; border: 1px solid rgba(255,255,255,0.1); "
            'border-radius: 4px;" title="Primary"></span>'
            '<span style="display: inline-block; width: 18px; height: 18px; '
            "background-color: {}; border: 1px solid rgba(255,255,255,0.1); "
            'border-radius: 4px;" title="Secondary"></span>'
            '<span style="display: inline-block; width: 18px; height: 18px; '
            "background-color: {}; border: 1px solid rgba(255,255,255,0.1); "
            'border-radius: 4px;" title="Background"></span>'
            "</span>",
            obj.primary_color,
            obj.secondary_color,
            obj.background_color,
        )

    color_preview.short_description = _("Colors")

    def layout_info(self, obj):
        """Display layout settings summary."""
        settings = obj.settings or {}
        layout = settings.get("layout", "wide")
        grid = settings.get("grid_columns", 3)
        radius = settings.get("border_radius", 12)
        dark = settings.get("dark_mode", False)
        parts = [f"{layout}"]
        if grid != 3:
            parts.append(f"{grid}col")
        if radius != 12:
            parts.append(f"r{radius}")
        if dark:
            parts.append("dark")
        return format_html(
            '<span style="font-size: 11px; color: #94a3b8;">{}</span>',
            " · ".join(parts),
        )

    layout_info.short_description = _("Layout")

    def color_picker_preview(self, obj):
        """Display visual color picker preview with current colors."""
        primary = obj.primary_color if obj.pk else "#3B82F6"
        secondary = obj.secondary_color if obj.pk else "#10B981"
        bg = obj.background_color if obj.pk else "#FFFFFF"
        text = obj.text_color if obj.pk else "#1F2937"

        return format_html(
            '<div style="display: flex; gap: 12px; align-items: center; '
            "padding: 12px 16px; background: rgba(0,0,0,0.2); "
            'border-radius: 8px; border: 1px solid rgba(255,255,255,0.06);">'
            '<div style="text-align: center;">'
            '<div style="width: 40px; height: 40px; background: {}; '
            'border-radius: 8px; border: 2px solid rgba(255,255,255,0.1);"></div>'
            '<span style="font-size: 10px; color: #94a3b8; margin-top: 4px; display: block;">Primary</span>'
            "</div>"
            '<div style="text-align: center;">'
            '<div style="width: 40px; height: 40px; background: {}; '
            'border-radius: 8px; border: 2px solid rgba(255,255,255,0.1);"></div>'
            '<span style="font-size: 10px; color: #94a3b8; margin-top: 4px; display: block;">Secondary</span>'
            "</div>"
            '<div style="text-align: center;">'
            '<div style="width: 40px; height: 40px; background: {}; '
            'border-radius: 8px; border: 2px solid rgba(255,255,255,0.1);"></div>'
            '<span style="font-size: 10px; color: #94a3b8; margin-top: 4px; display: block;">Background</span>'
            "</div>"
            '<div style="text-align: center;">'
            '<div style="width: 40px; height: 40px; background: {}; '
            'border-radius: 8px; border: 2px solid rgba(255,255,255,0.1);"></div>'
            '<span style="font-size: 10px; color: #94a3b8; margin-top: 4px; display: block;">Text</span>'
            "</div>"
            "</div>",
            primary,
            secondary,
            bg,
            text,
        )

    color_picker_preview.short_description = _("Color Preview")

    actions = ["set_as_default", "activate_themes", "deactivate_themes"]

    @admin.action(description=_("Set as default theme"))
    def set_as_default(self, request, queryset):
        """Bulk action to set selected theme as default (uses first selected)."""
        if queryset.count() > 1:
            self.message_user(
                request,
                _("Please select only one theme to set as default."),
                level="warning",
            )
            return
        theme = queryset.first()
        if theme:
            theme.set_as_default()
            self.message_user(
                request, _("%(name)s has been set as default.") % {"name": theme.name}
            )

    @admin.action(description=_("Activate selected themes"))
    def activate_themes(self, request, queryset):
        """Bulk action to activate selected themes."""
        count = queryset.update(is_active=True)
        self.message_user(
            request, _("%(count)d theme(s) have been activated.") % {"count": count}
        )

    @admin.action(description=_("Deactivate selected themes"))
    def deactivate_themes(self, request, queryset):
        """Bulk action to deactivate selected themes."""
        count = queryset.update(is_active=False)
        self.message_user(
            request, _("%(count)d theme(s) have been deactivated.") % {"count": count}
        )


# =============================================================================
# Menu Admin
# =============================================================================


@admin.register(Menu)
class MenuAdmin(EMenumPermissionMixin, SoftDeleteAdminMixin, TabbedTranslationAdmin):
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
        "name",
        "organization",
        "status_badge",
        "is_default",
        "category_count",
        "theme",
        "storefront_link",
        "created_at",
    ]
    list_filter = ["is_published", "is_default", "organization", "created_at"]
    search_fields = ["name", "slug", "description", "organization__name"]
    readonly_fields = ["id", "created_at", "updated_at", "deleted_at", "published_at"]
    ordering = ["-is_default", "sort_order", "name"]
    date_hierarchy = "created_at"
    list_per_page = 25
    prepopulated_fields = {"slug": ("name",)}
    autocomplete_fields = ["organization", "theme"]
    inlines = [CategoryInline]

    fieldsets = (
        (
            None,
            {
                "fields": ("id", "organization", "name", "slug", "description"),
                "description": _("Basic menu information"),
            },
        ),
        (
            _("Publication"),
            {
                "fields": ("is_published", "published_at", "is_default"),
                "description": _("Control menu visibility and default status"),
            },
        ),
        (
            _("Styling"),
            {
                "fields": ("theme",),
            },
        ),
        (
            _("Settings"),
            {
                "fields": ("sort_order", "settings"),
                "classes": ("collapse",),
            },
        ),
        (
            _("Timestamps"),
            {
                "fields": ("created_at", "updated_at", "deleted_at"),
                "classes": ("collapse",),
            },
        ),
    )

    def status_badge(self, obj):
        """Display publication status with color-coded badge."""
        if obj.is_published:
            return format_html(
                '<span style="background-color: #28a745; color: white; padding: 3px 10px; '
                'border-radius: 3px; font-size: 11px; font-weight: bold;">{}</span>',
                _("Published"),
            )
        return format_html(
            '<span style="background-color: #6c757d; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-size: 11px; font-weight: bold;">{}</span>',
            _("Draft"),
        )

    status_badge.short_description = _("Status")
    status_badge.admin_order_field = "is_published"

    def category_count(self, obj):
        """Display the number of active categories."""
        count = obj.category_count
        return format_html(
            '<span style="color: {};">{}</span>',
            "#28a745" if count > 0 else "#6c757d",
            count,
        )

    category_count.short_description = _("Categories")

    def storefront_link(self, obj):
        """Display link to the menu's public storefront page."""
        if obj.is_published:
            url = f"/m/{obj.slug}/"
            return format_html(
                '<a href="{}" target="_blank" style="display: inline-flex; align-items: center; '
                'gap: 4px; color: #818cf8; text-decoration: none; font-weight: 500;" '
                'title="Open storefront">'
                '<i class="ph ph-storefront" style="font-size: 16px;"></i> '
                '<span style="font-size: 12px;">View</span></a>',
                url,
            )
        return format_html(
            '<span style="color: #6c757d; font-size: 12px;">Draft</span>'
        )

    storefront_link.short_description = _("Storefront")

    def change_view(self, request, object_id, form_url="", extra_context=None):
        """Add storefront URL to change form context."""
        extra_context = extra_context or {}
        obj = self.get_object(request, object_id)
        if obj and obj.is_published:
            extra_context["storefront_url"] = f"/m/{obj.slug}/"
        return super().change_view(request, object_id, form_url, extra_context)

    actions = ["publish_menus", "unpublish_menus", "set_as_default"]

    @admin.action(description=_("Publish selected menus"))
    def publish_menus(self, request, queryset):
        """Bulk action to publish selected menus."""
        for menu in queryset:
            menu.publish()
        self.message_user(
            request,
            _("%(count)d menu(s) have been published.") % {"count": queryset.count()},
        )

    @admin.action(description=_("Unpublish selected menus"))
    def unpublish_menus(self, request, queryset):
        """Bulk action to unpublish selected menus."""
        for menu in queryset:
            menu.unpublish()
        self.message_user(
            request,
            _("%(count)d menu(s) have been unpublished.") % {"count": queryset.count()},
        )

    @admin.action(description=_("Set as default menu"))
    def set_as_default(self, request, queryset):
        """Bulk action to set selected menu as default (uses first selected)."""
        if queryset.count() > 1:
            self.message_user(
                request,
                _("Please select only one menu to set as default."),
                level="warning",
            )
            return
        menu = queryset.first()
        if menu:
            menu.set_as_default()
            self.message_user(
                request, _("%(name)s has been set as default.") % {"name": menu.name}
            )


# =============================================================================
# Category Admin
# =============================================================================


@admin.register(Category)
class CategoryAdmin(
    EMenumPermissionMixin, SoftDeleteAdminMixin, TabbedTranslationAdmin
):
    """
    Admin interface for Category management.

    Provides comprehensive management of menu categories including:
    - Hierarchical structure (parent categories)
    - Product count display
    - Active/inactive status
    - Sort order management

    Note: Soft-deleted categories are hidden by default.
    """

    form = CategoryAdminForm

    list_display = [
        "name",
        "menu",
        "parent",
        "product_count_display",
        "is_active",
        "sort_order",
        "created_at",
    ]
    list_filter = ["is_active", "menu", "menu__organization", "created_at"]
    search_fields = [
        "name",
        "slug",
        "description",
        "menu__name",
        "menu__organization__name",
    ]
    readonly_fields = ["id", "created_at", "updated_at", "deleted_at"]
    ordering = ["menu", "sort_order", "name"]
    date_hierarchy = "created_at"
    list_per_page = 25
    prepopulated_fields = {"slug": ("name",)}
    autocomplete_fields = ["organization", "menu", "parent"]
    inlines = [ProductInline]

    fieldsets = (
        (
            None,
            {
                "fields": ("id", "organization", "menu", "name", "slug", "description"),
                "description": _("Basic category information"),
            },
        ),
        (
            _("Hierarchy"),
            {
                "fields": ("parent",),
                "description": _("Optional parent category for nested structure"),
            },
        ),
        (
            _("Display"),
            {
                "fields": ("image", "icon", "is_active", "sort_order"),
            },
        ),
        (
            _("Timestamps"),
            {
                "fields": ("created_at", "updated_at", "deleted_at"),
                "classes": ("collapse",),
            },
        ),
    )

    def product_count_display(self, obj):
        """Display the number of active products."""
        count = obj.product_count
        return format_html(
            '<span style="color: {};">{}</span>',
            "#28a745" if count > 0 else "#6c757d",
            count,
        )

    product_count_display.short_description = _("Products")

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """Filter parent category options to same menu and exclude self."""
        if db_field.name == "parent":
            # Get the object being edited
            if hasattr(request, "_obj_") and request._obj_:
                kwargs["queryset"] = Category.objects.filter(
                    menu=request._obj_.menu, deleted_at__isnull=True
                ).exclude(pk=request._obj_.pk)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def get_form(self, request, obj=None, **kwargs):
        """Store the object for use in formfield_for_foreignkey."""
        request._obj_ = obj
        return super().get_form(request, obj, **kwargs)

    actions = ["activate_categories", "deactivate_categories"]

    @admin.action(description=_("Activate selected categories"))
    def activate_categories(self, request, queryset):
        """Bulk action to activate selected categories."""
        count = queryset.update(is_active=True)
        self.message_user(
            request,
            _("%(count)d category(ies) have been activated.") % {"count": count},
        )

    @admin.action(description=_("Deactivate selected categories"))
    def deactivate_categories(self, request, queryset):
        """Bulk action to deactivate selected categories."""
        count = queryset.update(is_active=False)
        self.message_user(
            request,
            _("%(count)d category(ies) have been deactivated.") % {"count": count},
        )


# =============================================================================
# Product Admin
# =============================================================================


@admin.register(Product)
class ProductAdmin(EMenumPermissionMixin, SoftDeleteAdminMixin, TabbedTranslationAdmin):
    """
    Admin interface for Product management.

    Provides comprehensive management of menu products including:
    - Pricing and availability
    - Featured and chef recommended flags
    - Variants, modifiers, and allergens via inlines
    - Tag management
    - Inline AI description generation

    Note: Soft-deleted products are hidden by default.
    """

    form = ProductAdminForm
    change_form_template = "admin/menu/product/change_form.html"

    list_display = [
        "name",
        "category",
        "price_display",
        "availability_badge",
        "is_featured",
        "is_chef_recommended",
        "sort_order",
        "created_at",
    ]
    list_filter = [
        "is_active",
        "is_available",
        "is_featured",
        "is_chef_recommended",
        "category__menu",
        "category__menu__organization",
        "created_at",
    ]
    search_fields = [
        "name",
        "slug",
        "description",
        "category__name",
        "category__menu__name",
        "category__menu__organization__name",
    ]
    readonly_fields = ["id", "created_at", "updated_at", "deleted_at"]
    ordering = ["category", "sort_order", "name"]
    date_hierarchy = "created_at"
    list_per_page = 25
    prepopulated_fields = {"slug": ("name",)}
    autocomplete_fields = ["organization", "category"]
    inlines = [ProductVariantInline, ProductModifierInline, ProductAllergenInline]

    fieldsets = (
        (
            None,
            {
                "fields": ("id", "organization", "category", "name", "slug"),
                "description": _("Basic product information"),
            },
        ),
        (
            _("Description"),
            {
                "fields": ("short_description", "description"),
            },
        ),
        (
            _("Pricing"),
            {
                "fields": ("base_price", "currency", "discount_percentage"),
            },
        ),
        (
            _("Images"),
            {
                "fields": ("image", "gallery"),
            },
        ),
        (
            _("Availability & Status"),
            {
                "fields": (
                    "is_active",
                    "is_available",
                    "is_featured",
                    "is_chef_recommended",
                ),
            },
        ),
        (
            _("Attributes"),
            {
                "fields": (
                    "preparation_time",
                    "calories",
                    "spicy_level",
                    "rating",
                    "review_count",
                    "tags",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            _("Display"),
            {
                "fields": ("sort_order",),
            },
        ),
        (
            _("Timestamps"),
            {
                "fields": ("created_at", "updated_at", "deleted_at"),
                "classes": ("collapse",),
            },
        ),
    )

    def price_display(self, obj):
        """Display formatted price."""
        return format_html(
            '<span style="font-weight: bold; color: #28a745;">{}</span>',
            obj.formatted_price,
        )

    price_display.short_description = _("Price")
    price_display.admin_order_field = "base_price"

    def availability_badge(self, obj):
        """Display availability with color-coded badge."""
        if not obj.is_active:
            return format_html(
                '<span style="background-color: #6c757d; color: white; padding: 3px 10px; '
                'border-radius: 3px; font-size: 11px; font-weight: bold;">{}</span>',
                _("Inactive"),
            )
        if obj.is_available:
            return format_html(
                '<span style="background-color: #28a745; color: white; padding: 3px 10px; '
                'border-radius: 3px; font-size: 11px; font-weight: bold;">{}</span>',
                _("Available"),
            )
        return format_html(
            '<span style="background-color: #dc3545; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-size: 11px; font-weight: bold;">{}</span>',
            _("Out of Stock"),
        )

    availability_badge.short_description = _("Availability")
    availability_badge.admin_order_field = "is_available"

    def changeform_view(self, request, object_id=None, form_url="", extra_context=None):
        """Add product context for AI generate button in change form."""
        extra_context = extra_context or {}
        if object_id:
            obj = self.get_object(request, object_id)
            if obj:
                extra_context["product_name"] = obj.name
                extra_context["product_category"] = (
                    obj.category.name if obj.category else ""
                )
                extra_context["product_id"] = str(obj.pk)
                org = obj.organization or (
                    obj.category.menu.organization
                    if obj.category and obj.category.menu
                    else None
                )
                extra_context["org_id"] = str(org.pk) if org else ""
        return super().changeform_view(request, object_id, form_url, extra_context)

    actions = [
        "make_available",
        "make_unavailable",
        "toggle_featured",
        "toggle_chef_recommended",
        "ai_generate_descriptions",
    ]

    @admin.action(description=_("Mark as available"))
    def make_available(self, request, queryset):
        """Bulk action to mark products as available."""
        count = queryset.update(is_available=True)
        self.message_user(
            request,
            _("%(count)d product(s) have been marked as available.") % {"count": count},
        )

    @admin.action(description=_("Mark as out of stock"))
    def make_unavailable(self, request, queryset):
        """Bulk action to mark products as unavailable."""
        count = queryset.update(is_available=False)
        self.message_user(
            request,
            _("%(count)d product(s) have been marked as out of stock.")
            % {"count": count},
        )

    @admin.action(description=_("Toggle featured status"))
    def toggle_featured(self, request, queryset):
        """Bulk action to toggle featured status."""
        for product in queryset:
            product.toggle_featured()
        self.message_user(
            request,
            _("Featured status has been toggled for %(count)d product(s).")
            % {"count": queryset.count()},
        )

    @admin.action(description=_("Toggle chef recommended"))
    def toggle_chef_recommended(self, request, queryset):
        """Bulk action to toggle chef recommended status."""
        for product in queryset:
            product.toggle_chef_recommended()
        self.message_user(
            request,
            _("Chef recommended status has been toggled for %(count)d product(s).")
            % {"count": queryset.count()},
        )

    @admin.action(description=_("🤖 AI: Generate descriptions"))
    def ai_generate_descriptions(self, request, queryset):
        """Bulk action to generate AI descriptions for selected products."""
        from apps.ai.services import AIContentService
        from shared.permissions.plan_enforcement import (
            FeatureNotAvailable,
            PlanLimitExceeded,
        )

        service = AIContentService()
        success_count = 0
        error_count = 0

        for product in queryset:
            org = product.organization or (
                product.category.menu.organization
                if product.category and product.category.menu
                else None
            )
            if not org:
                error_count += 1
                continue

            try:
                result = service.generate_description(
                    organization=org,
                    user=request.user,
                    product_name=product.name,
                    category=product.category.name if product.category else "",
                    language="tr",
                    product=product,
                )
                # Apply generated description
                if result.get("description") and not product.description:
                    product.description = result["description"]
                if result.get("short_description") and not product.short_description:
                    product.short_description = result["short_description"]
                product.save(
                    update_fields=["description", "short_description", "updated_at"]
                )
                success_count += 1
            except FeatureNotAvailable:
                self.message_user(
                    request,
                    _(
                        "AI content generation is not available on your plan. Please upgrade."
                    ),
                    level="error",
                )
                return
            except PlanLimitExceeded:
                self.message_user(
                    request,
                    _("AI credit limit reached. %d product(s) generated before limit.")
                    % success_count,
                    level="warning",
                )
                return
            except Exception:
                error_count += 1

        msg = _("AI descriptions generated for %(success)d product(s).") % {
            "success": success_count
        }
        if error_count:
            msg += _(" %(errors)d failed.") % {"errors": error_count}
        self.message_user(
            request, msg, level="success" if error_count == 0 else "warning"
        )


# =============================================================================
# Allergen Admin (Platform-level)
# =============================================================================


@admin.register(Allergen)
class AllergenAdmin(
    EMenumPermissionMixin, SoftDeleteAdminMixin, TabbedTranslationAdmin
):
    """
    Admin interface for Allergen management.

    Allergens are platform-level (not tenant-specific) and are used
    across all organizations to maintain consistency.

    Note: Soft-deleted allergens are hidden by default.
    """

    list_display = [
        "name",
        "code_display",
        "icon_preview",
        "is_active",
        "sort_order",
    ]
    list_filter = ["is_active", "created_at"]
    search_fields = ["name", "slug", "code", "description"]
    readonly_fields = ["id", "created_at", "updated_at", "deleted_at"]
    ordering = ["sort_order", "name"]
    list_per_page = 25
    prepopulated_fields = {"slug": ("name",)}

    fieldsets = (
        (
            None,
            {
                "fields": ("id", "name", "slug", "code"),
                "description": _("Basic allergen information"),
            },
        ),
        (
            _("Display"),
            {
                "fields": ("icon", "description", "sort_order"),
            },
        ),
        (
            _("Status"),
            {
                "fields": ("is_active",),
            },
        ),
        (
            _("Timestamps"),
            {
                "fields": ("created_at", "updated_at", "deleted_at"),
                "classes": ("collapse",),
            },
        ),
    )

    def code_display(self, obj):
        """Display allergen code with styling."""
        return format_html(
            '<code style="background-color: #f1f1f1; padding: 2px 6px; '
            'border-radius: 3px; font-weight: bold;">{}</code>',
            obj.code,
        )

    code_display.short_description = _("Code")
    code_display.admin_order_field = "code"

    def icon_preview(self, obj):
        """Display icon preview if available."""
        if obj.icon:
            return format_html(
                '<img src="{}" style="width: 24px; height: 24px;" alt="{}"/>',
                obj.icon,
                obj.name,
            )
        return format_html('<span style="color: #6c757d;">-</span>')

    icon_preview.short_description = _("Icon")

    actions = ["activate_allergens", "deactivate_allergens"]

    @admin.action(description=_("Activate selected allergens"))
    def activate_allergens(self, request, queryset):
        """Bulk action to activate selected allergens."""
        count = queryset.update(is_active=True)
        self.message_user(
            request, _("%(count)d allergen(s) have been activated.") % {"count": count}
        )

    @admin.action(description=_("Deactivate selected allergens"))
    def deactivate_allergens(self, request, queryset):
        """Bulk action to deactivate selected allergens."""
        count = queryset.update(is_active=False)
        self.message_user(
            request,
            _("%(count)d allergen(s) have been deactivated.") % {"count": count},
        )


# =============================================================================
# ProductVariant Admin
# =============================================================================


@admin.register(ProductVariant)
class ProductVariantAdmin(
    EMenumPermissionMixin, SoftDeleteAdminMixin, TabbedTranslationAdmin
):
    """Admin interface for ProductVariant management."""

    list_display = [
        "name",
        "product",
        "price_display",
        "is_default",
        "is_available",
        "sort_order",
    ]
    list_filter = [
        "is_default",
        "is_available",
        "product__category__menu__organization",
    ]
    search_fields = ["name", "product__name", "product__category__name"]
    readonly_fields = ["id", "created_at", "updated_at", "deleted_at"]
    ordering = ["product", "sort_order", "name"]
    list_per_page = 50
    autocomplete_fields = ["product"]

    fieldsets = (
        (
            None,
            {
                "fields": ("id", "product", "name"),
            },
        ),
        (
            _("Pricing & Availability"),
            {
                "fields": ("price", "is_default", "is_available"),
            },
        ),
        (
            _("Display"),
            {
                "fields": ("sort_order",),
            },
        ),
        (
            _("Timestamps"),
            {
                "fields": ("created_at", "updated_at", "deleted_at"),
                "classes": ("collapse",),
            },
        ),
    )

    def price_display(self, obj):
        """Display formatted price."""
        return format_html(
            '<span style="font-weight: bold;">{}</span>', obj.formatted_price
        )

    price_display.short_description = _("Price")
    price_display.admin_order_field = "price"


# =============================================================================
# ProductModifier Admin
# =============================================================================


@admin.register(ProductModifier)
class ProductModifierAdmin(
    EMenumPermissionMixin, SoftDeleteAdminMixin, TabbedTranslationAdmin
):
    """Admin interface for ProductModifier management."""

    list_display = [
        "name",
        "product",
        "price_display",
        "is_default",
        "is_required",
        "max_quantity",
        "sort_order",
    ]
    list_filter = ["is_default", "is_required", "product__category__menu__organization"]
    search_fields = ["name", "product__name", "product__category__name"]
    readonly_fields = ["id", "created_at", "updated_at", "deleted_at"]
    ordering = ["product", "sort_order", "name"]
    list_per_page = 50
    autocomplete_fields = ["product"]

    fieldsets = (
        (
            None,
            {
                "fields": ("id", "product", "name"),
            },
        ),
        (
            _("Pricing & Behavior"),
            {
                "fields": ("price", "is_default", "is_required", "max_quantity"),
            },
        ),
        (
            _("Display"),
            {
                "fields": ("sort_order",),
            },
        ),
        (
            _("Timestamps"),
            {
                "fields": ("created_at", "updated_at", "deleted_at"),
                "classes": ("collapse",),
            },
        ),
    )

    def price_display(self, obj):
        """Display formatted price."""
        return format_html(
            '<span style="font-weight: bold;">{}</span>', obj.formatted_price
        )

    price_display.short_description = _("Price")
    price_display.admin_order_field = "price"


# =============================================================================
# ProductAllergen Admin
# =============================================================================


@admin.register(ProductAllergen)
class ProductAllergenAdmin(
    EMenumPermissionMixin, SoftDeleteAdminMixin, admin.ModelAdmin
):
    """Admin interface for ProductAllergen (junction table) management."""

    list_display = [
        "product",
        "allergen",
        "severity_badge",
        "created_at",
    ]
    list_filter = ["severity", "allergen", "product__category__menu__organization"]
    search_fields = ["product__name", "allergen__name", "notes"]
    readonly_fields = ["id", "created_at", "updated_at", "deleted_at"]
    ordering = ["product", "allergen"]
    list_per_page = 50
    autocomplete_fields = ["product", "allergen"]

    fieldsets = (
        (
            None,
            {
                "fields": ("id", "product", "allergen"),
            },
        ),
        (
            _("Details"),
            {
                "fields": ("severity", "notes"),
            },
        ),
        (
            _("Timestamps"),
            {
                "fields": ("created_at", "updated_at", "deleted_at"),
                "classes": ("collapse",),
            },
        ),
    )

    def severity_badge(self, obj):
        """Display severity with color-coded badge."""
        colors = {
            "contains": "#dc3545",
            "may_contain": "#ffc107",
            "traces": "#17a2b8",
        }
        color = colors.get(obj.severity, "#6c757d")
        text_color = "#000" if obj.severity == "may_contain" else "#fff"
        return format_html(
            '<span style="background-color: {}; color: {}; padding: 3px 10px; '
            'border-radius: 3px; font-size: 11px; font-weight: bold;">{}</span>',
            color,
            text_color,
            obj.get_severity_display(),
        )

    severity_badge.short_description = _("Severity")
    severity_badge.admin_order_field = "severity"


# =============================================================================
# NutritionInfo Admin
# =============================================================================


@admin.register(NutritionInfo)
class NutritionInfoAdmin(EMenumPermissionMixin, SoftDeleteAdminMixin, admin.ModelAdmin):
    """Admin interface for NutritionInfo management."""

    list_display = [
        "product",
        "serving_size",
        "calories",
        "macros_summary",
        "created_at",
    ]
    list_filter = ["product__category__menu__organization"]
    search_fields = ["product__name", "product__category__name"]
    readonly_fields = ["id", "created_at", "updated_at", "deleted_at"]
    ordering = ["product"]
    list_per_page = 50
    autocomplete_fields = ["product"]

    fieldsets = (
        (
            None,
            {
                "fields": ("id", "product"),
            },
        ),
        (
            _("Serving Information"),
            {
                "fields": ("serving_size", "serving_size_grams"),
            },
        ),
        (
            _("Energy"),
            {
                "fields": ("calories",),
            },
        ),
        (
            _("Macronutrients"),
            {
                "fields": (
                    "protein",
                    "carbohydrates",
                    "sugar",
                    "fiber",
                    "fat",
                    "saturated_fat",
                    "trans_fat",
                ),
            },
        ),
        (
            _("Micronutrients"),
            {
                "fields": ("cholesterol", "sodium", "potassium", "calcium", "iron"),
                "classes": ("collapse",),
            },
        ),
        (
            _("Vitamins"),
            {
                "fields": ("vitamin_a", "vitamin_c"),
                "classes": ("collapse",),
            },
        ),
        (
            _("Custom Nutrients"),
            {
                "fields": ("custom_nutrients",),
                "classes": ("collapse",),
            },
        ),
        (
            _("Timestamps"),
            {
                "fields": ("created_at", "updated_at", "deleted_at"),
                "classes": ("collapse",),
            },
        ),
    )

    def macros_summary(self, obj):
        """Display a summary of macronutrients."""
        parts = []
        if obj.protein:
            parts.append(f"P: {obj.protein}g")
        if obj.carbohydrates:
            parts.append(f"C: {obj.carbohydrates}g")
        if obj.fat:
            parts.append(f"F: {obj.fat}g")
        if parts:
            return " | ".join(parts)
        return format_html('<span style="color: #6c757d;">-</span>')

    macros_summary.short_description = _("Macros")
