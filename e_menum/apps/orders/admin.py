"""
Django Admin configuration for the Orders application.

This module defines admin interfaces for order models:
- Zone
- Table
- QRCode
- QRScan
- Order
- OrderItem
- ServiceRequest

All admin classes implement multi-tenant filtering where applicable.
Soft-deleted records are filtered out by default in all applicable models.
"""

from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from modeltranslation.admin import TabbedTranslationAdmin

from apps.orders.models import (
    Order,
    OrderItem,
    QRCode,
    QRScan,
    ServiceRequest,
    Table,
    Zone,
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


class TableInline(admin.TabularInline):
    """Inline admin for tables within a zone."""

    model = Table
    extra = 0
    show_change_link = True
    fields = ["name", "number", "status", "capacity", "is_active", "sort_order"]
    readonly_fields = []
    ordering = ["sort_order", "number", "name"]

    def get_queryset(self, request):
        """Filter out soft-deleted tables."""
        qs = super().get_queryset(request)
        return qs.filter(deleted_at__isnull=True)


class OrderItemInline(admin.TabularInline):
    """Inline admin for order items within an order."""

    model = OrderItem
    extra = 0
    show_change_link = True
    fields = [
        "product",
        "variant",
        "quantity",
        "unit_price",
        "total_price",
        "status",
        "is_gift",
    ]
    readonly_fields = ["total_price"]
    ordering = ["created_at"]

    def get_queryset(self, request):
        """Filter out soft-deleted order items."""
        qs = super().get_queryset(request)
        return qs.filter(deleted_at__isnull=True)


class QRCodeInline(admin.TabularInline):
    """Inline admin for QR codes linked to a table."""

    model = QRCode
    fk_name = "table"
    extra = 0
    show_change_link = True
    fields = ["name", "code", "type", "is_active", "scan_count"]
    readonly_fields = ["code", "scan_count"]
    ordering = ["-created_at"]

    def get_queryset(self, request):
        """Filter out soft-deleted QR codes."""
        qs = super().get_queryset(request)
        return qs.filter(deleted_at__isnull=True)


# =============================================================================
# Zone Admin
# =============================================================================


@admin.register(Zone)
class ZoneAdmin(EMenumPermissionMixin, SoftDeleteAdminMixin, TabbedTranslationAdmin):
    """
    Admin interface for Zone management.

    Provides comprehensive management of restaurant zones/sections including:
    - Zone properties (outdoor, smoking, reservable)
    - Color and icon customization
    - Table count display
    - Capacity management

    Note: Soft-deleted zones are hidden by default.
    """

    list_display = [
        "name",
        "organization",
        "color_preview",
        "table_count_display",
        "capacity",
        "zone_flags",
        "is_active",
        "sort_order",
        "created_at",
    ]
    list_filter = [
        "is_active",
        "is_outdoor",
        "is_smoking_allowed",
        "is_reservable",
        "organization",
        "created_at",
    ]
    search_fields = ["name", "slug", "description", "organization__name"]
    readonly_fields = ["id", "created_at", "updated_at", "deleted_at"]
    ordering = ["organization", "sort_order", "name"]
    date_hierarchy = "created_at"
    list_per_page = 25
    prepopulated_fields = {"slug": ("name",)}
    autocomplete_fields = ["organization", "branch"]
    inlines = [TableInline]

    fieldsets = (
        (
            None,
            {
                "fields": (
                    "id",
                    "organization",
                    "branch",
                    "name",
                    "slug",
                    "description",
                ),
                "description": _("Basic zone information"),
            },
        ),
        (
            _("Appearance"),
            {
                "fields": ("color", "icon"),
                "description": _("Visual identification for the zone"),
            },
        ),
        (
            _("Capacity & Characteristics"),
            {
                "fields": (
                    "capacity",
                    "is_outdoor",
                    "is_smoking_allowed",
                    "is_reservable",
                ),
            },
        ),
        (
            _("Status & Order"),
            {
                "fields": ("is_active", "sort_order"),
            },
        ),
        (
            _("Settings"),
            {
                "fields": ("settings",),
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

    def color_preview(self, obj):
        """Display color swatch for the zone."""
        return format_html(
            '<span style="display: inline-block; width: 24px; height: 24px; '
            'background-color: {}; border: 1px solid #ccc; border-radius: 4px;" '
            'title="{}"></span>',
            obj.color,
            obj.color,
        )

    color_preview.short_description = _("Color")

    def table_count_display(self, obj):
        """Display the number of active tables."""
        count = obj.table_count
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            "#28a745" if count > 0 else "#6c757d",
            count,
        )

    table_count_display.short_description = _("Tables")

    def zone_flags(self, obj):
        """Display zone characteristic flags as badges."""
        flags = []
        if obj.is_outdoor:
            flags.append(
                format_html(
                    '<span style="background-color: #17a2b8; color: white; padding: 2px 6px; '
                    'border-radius: 3px; font-size: 10px; margin-right: 4px;">{}</span>',
                    _("Outdoor"),
                )
            )
        if obj.is_smoking_allowed:
            flags.append(
                format_html(
                    '<span style="background-color: #6c757d; color: white; padding: 2px 6px; '
                    'border-radius: 3px; font-size: 10px; margin-right: 4px;">{}</span>',
                    _("Smoking"),
                )
            )
        if obj.is_reservable:
            flags.append(
                format_html(
                    '<span style="background-color: #28a745; color: white; padding: 2px 6px; '
                    'border-radius: 3px; font-size: 10px;">{}</span>',
                    _("Reservable"),
                )
            )
        if flags:
            return format_html("".join([str(f) for f in flags]))
        return format_html('<span style="color: #6c757d;">-</span>')

    zone_flags.short_description = _("Flags")

    actions = ["activate_zones", "deactivate_zones"]

    @admin.action(description=_("Activate selected zones"))
    def activate_zones(self, request, queryset):
        """Bulk action to activate selected zones."""
        count = queryset.update(is_active=True)
        self.message_user(
            request, _("%(count)d zone(s) have been activated.") % {"count": count}
        )

    @admin.action(description=_("Deactivate selected zones"))
    def deactivate_zones(self, request, queryset):
        """Bulk action to deactivate selected zones."""
        count = queryset.update(is_active=False)
        self.message_user(
            request, _("%(count)d zone(s) have been deactivated.") % {"count": count}
        )


# =============================================================================
# Table Admin
# =============================================================================


@admin.register(Table)
class TableAdmin(EMenumPermissionMixin, SoftDeleteAdminMixin, TabbedTranslationAdmin):
    """
    Admin interface for Table management.

    Provides comprehensive management of restaurant tables including:
    - Status tracking (available, occupied, reserved)
    - Capacity management
    - Floor plan positioning
    - QR code linking

    Note: Soft-deleted tables are hidden by default.
    """

    list_display = [
        "name",
        "zone",
        "status_badge",
        "capacity",
        "is_vip_badge",
        "is_active",
        "sort_order",
        "created_at",
    ]
    list_filter = [
        "status",
        "is_active",
        "is_vip",
        "zone",
        "zone__organization",
        "created_at",
    ]
    search_fields = [
        "name",
        "slug",
        "number",
        "zone__name",
        "zone__organization__name",
        "notes",
    ]
    readonly_fields = ["id", "created_at", "updated_at", "deleted_at"]
    ordering = ["zone", "sort_order", "number", "name"]
    date_hierarchy = "created_at"
    list_per_page = 25
    prepopulated_fields = {"slug": ("name",)}
    autocomplete_fields = ["organization", "zone", "branch"]
    inlines = [QRCodeInline]

    fieldsets = (
        (
            None,
            {
                "fields": (
                    "id",
                    "organization",
                    "zone",
                    "branch",
                    "name",
                    "number",
                    "slug",
                ),
                "description": _("Basic table information"),
            },
        ),
        (
            _("Capacity"),
            {
                "fields": ("capacity", "min_capacity"),
            },
        ),
        (
            _("Status"),
            {
                "fields": ("status", "is_active", "is_vip"),
            },
        ),
        (
            _("Floor Plan"),
            {
                "fields": ("position_x", "position_y", "shape"),
                "classes": ("collapse",),
                "description": _("Position and shape for floor plan visualization"),
            },
        ),
        (
            _("Display"),
            {
                "fields": ("sort_order", "notes"),
            },
        ),
        (
            _("Settings"),
            {
                "fields": ("settings",),
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
        """Display table status with color-coded badge."""
        colors = {
            "available": "#28a745",
            "occupied": "#dc3545",
            "reserved": "#ffc107",
            "cleaning": "#17a2b8",
            "maintenance": "#6c757d",
        }
        text_colors = {
            "reserved": "#000",
        }
        color = colors.get(obj.status, "#6c757d")
        text_color = text_colors.get(obj.status, "#fff")
        return format_html(
            '<span style="background-color: {}; color: {}; padding: 3px 10px; '
            'border-radius: 3px; font-size: 11px; font-weight: bold;">{}</span>',
            color,
            text_color,
            obj.get_status_display(),
        )

    status_badge.short_description = _("Status")
    status_badge.admin_order_field = "status"

    def is_vip_badge(self, obj):
        """Display VIP badge if table is VIP."""
        if obj.is_vip:
            return format_html(
                '<span style="background-color: #ffc107; color: #000; padding: 2px 8px; '
                'border-radius: 3px; font-size: 10px; font-weight: bold;">VIP</span>'
            )
        return format_html('<span style="color: #6c757d;">-</span>')

    is_vip_badge.short_description = _("VIP")
    is_vip_badge.admin_order_field = "is_vip"

    actions = [
        "set_available",
        "set_occupied",
        "set_reserved",
        "activate_tables",
        "deactivate_tables",
    ]

    @admin.action(description=_("Set as available"))
    def set_available(self, request, queryset):
        """Bulk action to set tables as available."""
        count = queryset.update(status="available")
        self.message_user(
            request,
            _("%(count)d table(s) have been set to available.") % {"count": count},
        )

    @admin.action(description=_("Set as occupied"))
    def set_occupied(self, request, queryset):
        """Bulk action to set tables as occupied."""
        count = queryset.update(status="occupied")
        self.message_user(
            request,
            _("%(count)d table(s) have been set to occupied.") % {"count": count},
        )

    @admin.action(description=_("Set as reserved"))
    def set_reserved(self, request, queryset):
        """Bulk action to set tables as reserved."""
        count = queryset.update(status="reserved")
        self.message_user(
            request,
            _("%(count)d table(s) have been set to reserved.") % {"count": count},
        )

    @admin.action(description=_("Activate selected tables"))
    def activate_tables(self, request, queryset):
        """Bulk action to activate selected tables."""
        count = queryset.update(is_active=True)
        self.message_user(
            request, _("%(count)d table(s) have been activated.") % {"count": count}
        )

    @admin.action(description=_("Deactivate selected tables"))
    def deactivate_tables(self, request, queryset):
        """Bulk action to deactivate selected tables."""
        count = queryset.update(is_active=False)
        self.message_user(
            request, _("%(count)d table(s) have been deactivated.") % {"count": count}
        )


# =============================================================================
# QRCode Admin
# =============================================================================


@admin.register(QRCode)
class QRCodeAdmin(EMenumPermissionMixin, SoftDeleteAdminMixin, TabbedTranslationAdmin):
    """
    Admin interface for QRCode management.

    Provides comprehensive management of QR codes including:
    - Type management (menu, table, campaign)
    - Scan analytics display
    - Expiration tracking
    - Link management

    Note: Soft-deleted QR codes are hidden by default.
    """

    list_display = [
        "name",
        "code",
        "type_badge",
        "organization",
        "table",
        "scan_stats",
        "is_active",
        "is_expired_badge",
        "created_at",
    ]
    list_filter = [
        "type",
        "is_active",
        "organization",
        "created_at",
        "expires_at",
    ]
    search_fields = ["name", "code", "organization__name", "table__name", "menu__name"]
    readonly_fields = [
        "id",
        "code",
        "scan_count",
        "unique_scan_count",
        "last_scanned_at",
        "created_at",
        "updated_at",
        "deleted_at",
    ]
    ordering = ["-created_at"]
    date_hierarchy = "created_at"
    list_per_page = 25
    autocomplete_fields = ["organization", "branch", "menu", "table"]

    fieldsets = (
        (
            None,
            {
                "fields": (
                    "id",
                    "organization",
                    "branch",
                    "name",
                    "code",
                    "description",
                ),
                "description": _("Basic QR code information"),
            },
        ),
        (
            _("Type & Links"),
            {
                "fields": ("type", "menu", "table"),
                "description": _("QR code type and linked entities"),
            },
        ),
        (
            _("URLs"),
            {
                "fields": ("short_url", "qr_image_url", "redirect_url"),
                "classes": ("collapse",),
            },
        ),
        (
            _("Status"),
            {
                "fields": ("is_active", "expires_at"),
            },
        ),
        (
            _("Analytics"),
            {
                "fields": ("scan_count", "unique_scan_count", "last_scanned_at"),
                "description": _("QR code scan statistics (read-only)"),
            },
        ),
        (
            _("Settings & Metadata"),
            {
                "fields": ("settings", "metadata"),
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

    def type_badge(self, obj):
        """Display QR type with color-coded badge."""
        colors = {
            "menu": "#28a745",
            "table": "#17a2b8",
            "campaign": "#ffc107",
        }
        text_colors = {
            "campaign": "#000",
        }
        color = colors.get(obj.type, "#6c757d")
        text_color = text_colors.get(obj.type, "#fff")
        return format_html(
            '<span style="background-color: {}; color: {}; padding: 3px 10px; '
            'border-radius: 3px; font-size: 11px; font-weight: bold;">{}</span>',
            color,
            text_color,
            obj.get_type_display(),
        )

    type_badge.short_description = _("Type")
    type_badge.admin_order_field = "type"

    def scan_stats(self, obj):
        """Display scan statistics."""
        return format_html(
            '<span title="Total scans / Unique scans"><strong>{}</strong> / {}</span>',
            obj.scan_count,
            obj.unique_scan_count,
        )

    scan_stats.short_description = _("Scans (Total/Unique)")

    def is_expired_badge(self, obj):
        """Display expiration status."""
        if obj.is_expired:
            return format_html(
                '<span style="background-color: #dc3545; color: white; padding: 2px 8px; '
                'border-radius: 3px; font-size: 10px; font-weight: bold;">{}</span>',
                _("Expired"),
            )
        if obj.expires_at:
            return format_html(
                '<span style="color: #28a745;">{}</span>',
                obj.expires_at.strftime("%Y-%m-%d"),
            )
        return format_html('<span style="color: #6c757d;">-</span>')

    is_expired_badge.short_description = _("Expires")

    actions = ["activate_qrcodes", "deactivate_qrcodes"]

    @admin.action(description=_("Activate selected QR codes"))
    def activate_qrcodes(self, request, queryset):
        """Bulk action to activate selected QR codes."""
        count = queryset.update(is_active=True)
        self.message_user(
            request, _("%(count)d QR code(s) have been activated.") % {"count": count}
        )

    @admin.action(description=_("Deactivate selected QR codes"))
    def deactivate_qrcodes(self, request, queryset):
        """Bulk action to deactivate selected QR codes."""
        count = queryset.update(is_active=False)
        self.message_user(
            request, _("%(count)d QR code(s) have been deactivated.") % {"count": count}
        )


# =============================================================================
# QRScan Admin (Read-only analytics)
# =============================================================================


@admin.register(QRScan)
class QRScanAdmin(EMenumPermissionMixin, admin.ModelAdmin):
    """
    Admin interface for QRScan analytics (read-only).

    Provides read-only access to QR scan analytics including:
    - Device information
    - Location data
    - Timestamp tracking

    Note: QRScan records are append-only for analytics integrity.
    """

    list_display = [
        "qr_code",
        "scanned_at",
        "device_badge",
        "browser",
        "location_display",
        "is_unique",
    ]
    list_filter = [
        "device_type",
        "browser",
        "os",
        "country",
        "is_unique",
        "organization",
        "scanned_at",
    ]
    search_fields = ["qr_code__code", "qr_code__name", "ip_address", "city", "country"]
    readonly_fields = [
        "id",
        "qr_code",
        "organization",
        "scanned_at",
        "ip_address",
        "user_agent",
        "session_id",
        "device_type",
        "browser",
        "os",
        "country",
        "city",
        "region",
        "latitude",
        "longitude",
        "referer",
        "is_unique",
        "customer",
        "metadata",
        "created_at",
        "updated_at",
    ]
    ordering = ["-scanned_at"]
    date_hierarchy = "scanned_at"
    list_per_page = 50

    fieldsets = (
        (
            None,
            {
                "fields": ("id", "qr_code", "organization", "scanned_at"),
            },
        ),
        (
            _("Device Information"),
            {
                "fields": ("device_type", "browser", "os", "user_agent"),
            },
        ),
        (
            _("Network"),
            {
                "fields": ("ip_address", "session_id", "referer"),
            },
        ),
        (
            _("Location"),
            {
                "fields": ("country", "city", "region", "latitude", "longitude"),
            },
        ),
        (
            _("Tracking"),
            {
                "fields": ("is_unique", "customer"),
            },
        ),
        (
            _("Metadata"),
            {
                "fields": ("metadata",),
                "classes": ("collapse",),
            },
        ),
        (
            _("Timestamps"),
            {
                "fields": ("created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )

    def has_add_permission(self, request):
        """Disable adding QRScan records manually."""
        return False

    def has_change_permission(self, request, obj=None):
        """Disable editing QRScan records."""
        return False

    def has_delete_permission(self, request, obj=None):
        """Disable deleting QRScan records (analytics integrity)."""
        return False

    def device_badge(self, obj):
        """Display device type with icon/badge."""
        icons = {
            "mobile": "📱",
            "tablet": "📱",
            "desktop": "💻",
        }
        icon = icons.get(obj.device_type, "❓")
        return format_html(
            '{} <span style="color: #6c757d;">{}</span>',
            icon,
            obj.device_type or _("Unknown"),
        )

    device_badge.short_description = _("Device")

    def location_display(self, obj):
        """Display location information."""
        if obj.has_location:
            parts = []
            if obj.city:
                parts.append(obj.city)
            if obj.country:
                parts.append(obj.country)
            return ", ".join(parts) if parts else "-"
        return format_html('<span style="color: #6c757d;">-</span>')

    location_display.short_description = _("Location")


# =============================================================================
# Order Admin
# =============================================================================


@admin.register(Order)
class OrderAdmin(EMenumPermissionMixin, SoftDeleteAdminMixin, admin.ModelAdmin):
    """
    Admin interface for Order management.

    Provides comprehensive management of customer orders including:
    - Status workflow management
    - Payment tracking
    - Financial summary
    - Item management via inline

    Note: Soft-deleted orders are hidden by default.
    """

    list_display = [
        "order_number",
        "organization",
        "status_badge",
        "type_badge",
        "payment_badge",
        "total_display",
        "table",
        "item_count_display",
        "created_at",
    ]
    list_filter = [
        "status",
        "type",
        "payment_status",
        "payment_method",
        "organization",
        "created_at",
    ]
    search_fields = [
        "order_number",
        "organization__name",
        "table__name",
        "customer__first_name",
        "customer__last_name",
        "notes",
    ]
    readonly_fields = [
        "id",
        "order_number",
        "created_at",
        "updated_at",
        "deleted_at",
        "placed_at",
        "confirmed_at",
        "preparing_at",
        "ready_at",
        "delivered_at",
        "completed_at",
        "cancelled_at",
    ]
    ordering = ["-created_at"]
    date_hierarchy = "created_at"
    list_per_page = 25
    autocomplete_fields = [
        "organization",
        "branch",
        "table",
        "customer",
        "placed_by",
        "assigned_to",
    ]
    inlines = [OrderItemInline]

    fieldsets = (
        (
            None,
            {
                "fields": ("id", "order_number", "organization", "branch"),
                "description": _("Order identification"),
            },
        ),
        (
            _("Status"),
            {
                "fields": ("status", "type"),
            },
        ),
        (
            _("Customer & Table"),
            {
                "fields": ("customer", "table", "guest_count", "customer_info"),
            },
        ),
        (
            _("Payment"),
            {
                "fields": ("payment_status", "payment_method"),
            },
        ),
        (
            _("Financial"),
            {
                "fields": (
                    "subtotal",
                    "tax_amount",
                    "discount_amount",
                    "tip_amount",
                    "total_amount",
                    "currency",
                ),
            },
        ),
        (
            _("Notes"),
            {
                "fields": ("notes", "special_instructions"),
                "classes": ("collapse",),
            },
        ),
        (
            _("Delivery"),
            {
                "fields": ("delivery_address",),
                "classes": ("collapse",),
            },
        ),
        (
            _("Staff"),
            {
                "fields": ("placed_by", "assigned_to"),
            },
        ),
        (
            _("Workflow Timestamps"),
            {
                "fields": (
                    "placed_at",
                    "confirmed_at",
                    "preparing_at",
                    "ready_at",
                    "delivered_at",
                    "completed_at",
                    "cancelled_at",
                    "cancel_reason",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            _("Metadata"),
            {
                "fields": ("metadata",),
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
        """Display order status with color-coded badge."""
        colors = {
            "pending": "#ffc107",
            "confirmed": "#17a2b8",
            "preparing": "#fd7e14",
            "ready": "#28a745",
            "delivered": "#6f42c1",
            "completed": "#28a745",
            "cancelled": "#dc3545",
        }
        text_colors = {
            "pending": "#000",
        }
        color = colors.get(obj.status, "#6c757d")
        text_color = text_colors.get(obj.status, "#fff")
        return format_html(
            '<span style="background-color: {}; color: {}; padding: 3px 10px; '
            'border-radius: 3px; font-size: 11px; font-weight: bold;">{}</span>',
            color,
            text_color,
            obj.get_status_display(),
        )

    status_badge.short_description = _("Status")
    status_badge.admin_order_field = "status"

    def type_badge(self, obj):
        """Display order type with badge."""
        colors = {
            "dine_in": "#17a2b8",
            "takeaway": "#ffc107",
            "delivery": "#28a745",
        }
        text_colors = {
            "takeaway": "#000",
        }
        color = colors.get(obj.type, "#6c757d")
        text_color = text_colors.get(obj.type, "#fff")
        return format_html(
            '<span style="background-color: {}; color: {}; padding: 3px 10px; '
            'border-radius: 3px; font-size: 11px; font-weight: bold;">{}</span>',
            color,
            text_color,
            obj.get_type_display(),
        )

    type_badge.short_description = _("Type")
    type_badge.admin_order_field = "type"

    def payment_badge(self, obj):
        """Display payment status with badge."""
        colors = {
            "pending": "#ffc107",
            "partial": "#fd7e14",
            "paid": "#28a745",
            "refunded": "#6f42c1",
            "failed": "#dc3545",
        }
        text_colors = {
            "pending": "#000",
        }
        color = colors.get(obj.payment_status, "#6c757d")
        text_color = text_colors.get(obj.payment_status, "#fff")
        return format_html(
            '<span style="background-color: {}; color: {}; padding: 3px 10px; '
            'border-radius: 3px; font-size: 11px; font-weight: bold;">{}</span>',
            color,
            text_color,
            obj.get_payment_status_display(),
        )

    payment_badge.short_description = _("Payment")
    payment_badge.admin_order_field = "payment_status"

    def total_display(self, obj):
        """Display formatted total amount."""
        currency_symbols = {
            "TRY": "₺",
            "USD": "$",
            "EUR": "€",
            "GBP": "£",
        }
        symbol = currency_symbols.get(obj.currency, obj.currency)
        formatted = f"{obj.total_amount:,.2f}"
        return format_html(
            '<span style="font-weight: bold; color: #28a745;">{}{}</span>',
            symbol,
            formatted,
        )

    total_display.short_description = _("Total")
    total_display.admin_order_field = "total_amount"

    def item_count_display(self, obj):
        """Display number of items."""
        count = obj.item_count
        return format_html(
            '<span style="color: {};">{}</span>',
            "#28a745" if count > 0 else "#6c757d",
            count,
        )

    item_count_display.short_description = _("Items")

    actions = [
        "confirm_orders",
        "start_preparing",
        "mark_ready",
        "mark_completed",
        "cancel_orders",
    ]

    @admin.action(description=_("Confirm selected orders"))
    def confirm_orders(self, request, queryset):
        """Bulk action to confirm pending orders."""
        count = 0
        for order in queryset.filter(status="pending"):
            try:
                order.confirm()
                count += 1
            except ValueError:
                pass
        self.message_user(
            request, _("%(count)d order(s) have been confirmed.") % {"count": count}
        )

    @admin.action(description=_("Start preparing selected orders"))
    def start_preparing(self, request, queryset):
        """Bulk action to start preparing confirmed orders."""
        count = 0
        for order in queryset.filter(status="confirmed"):
            try:
                order.start_preparation()
                count += 1
            except ValueError:
                pass
        self.message_user(
            request,
            _("%(count)d order(s) have started preparation.") % {"count": count},
        )

    @admin.action(description=_("Mark selected orders as ready"))
    def mark_ready(self, request, queryset):
        """Bulk action to mark preparing orders as ready."""
        count = 0
        for order in queryset.filter(status="preparing"):
            try:
                order.mark_ready()
                count += 1
            except ValueError:
                pass
        self.message_user(
            request,
            _("%(count)d order(s) have been marked as ready.") % {"count": count},
        )

    @admin.action(description=_("Mark selected orders as completed"))
    def mark_completed(self, request, queryset):
        """Bulk action to complete orders."""
        count = 0
        for order in queryset.filter(status__in=["ready", "delivered"]):
            try:
                order.complete()
                count += 1
            except ValueError:
                pass
        self.message_user(
            request, _("%(count)d order(s) have been completed.") % {"count": count}
        )

    @admin.action(description=_("Cancel selected orders"))
    def cancel_orders(self, request, queryset):
        """Bulk action to cancel orders."""
        count = 0
        for order in queryset.exclude(status__in=["completed", "cancelled"]):
            try:
                order.cancel(reason="Cancelled via admin")
                count += 1
            except ValueError:
                pass
        self.message_user(
            request, _("%(count)d order(s) have been cancelled.") % {"count": count}
        )


# =============================================================================
# OrderItem Admin
# =============================================================================


@admin.register(OrderItem)
class OrderItemAdmin(EMenumPermissionMixin, SoftDeleteAdminMixin, admin.ModelAdmin):
    """
    Admin interface for OrderItem management.

    Provides management of individual order line items including:
    - Product and variant tracking
    - Status workflow
    - Pricing and modifiers

    Note: Soft-deleted items are hidden by default.
    """

    list_display = [
        "display_name_formatted",
        "order",
        "quantity",
        "price_display",
        "status_badge",
        "is_gift_badge",
        "created_at",
    ]
    list_filter = [
        "status",
        "is_gift",
        "order__organization",
        "created_at",
    ]
    search_fields = [
        "order__order_number",
        "product__name",
        "variant__name",
        "notes",
    ]
    readonly_fields = [
        "id",
        "total_price",
        "created_at",
        "updated_at",
        "deleted_at",
        "prepared_at",
        "delivered_at",
        "cancelled_at",
    ]
    ordering = ["order", "created_at"]
    list_per_page = 50
    autocomplete_fields = ["order", "product", "variant"]

    fieldsets = (
        (
            None,
            {
                "fields": ("id", "order", "product", "variant"),
            },
        ),
        (
            _("Quantity & Pricing"),
            {
                "fields": ("quantity", "unit_price", "total_price", "currency"),
            },
        ),
        (
            _("Status"),
            {
                "fields": ("status", "is_gift"),
            },
        ),
        (
            _("Modifiers & Notes"),
            {
                "fields": ("modifiers", "notes"),
                "classes": ("collapse",),
            },
        ),
        (
            _("Workflow Timestamps"),
            {
                "fields": (
                    "prepared_at",
                    "delivered_at",
                    "cancelled_at",
                    "cancel_reason",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            _("Metadata"),
            {
                "fields": ("metadata",),
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

    def display_name_formatted(self, obj):
        """Display product name with variant."""
        return obj.display_name

    display_name_formatted.short_description = _("Product")

    def price_display(self, obj):
        """Display formatted total price."""
        return format_html(
            '<span style="font-weight: bold;">{}</span>', obj.formatted_total_price
        )

    price_display.short_description = _("Total")
    price_display.admin_order_field = "total_price"

    def status_badge(self, obj):
        """Display item status with color-coded badge."""
        colors = {
            "pending": "#ffc107",
            "preparing": "#fd7e14",
            "ready": "#28a745",
            "delivered": "#6f42c1",
            "cancelled": "#dc3545",
        }
        text_colors = {
            "pending": "#000",
        }
        color = colors.get(obj.status, "#6c757d")
        text_color = text_colors.get(obj.status, "#fff")
        return format_html(
            '<span style="background-color: {}; color: {}; padding: 3px 10px; '
            'border-radius: 3px; font-size: 11px; font-weight: bold;">{}</span>',
            color,
            text_color,
            obj.get_status_display(),
        )

    status_badge.short_description = _("Status")
    status_badge.admin_order_field = "status"

    def is_gift_badge(self, obj):
        """Display gift badge if item is a gift."""
        if obj.is_gift:
            return format_html(
                '<span style="background-color: #e91e63; color: white; padding: 2px 8px; '
                'border-radius: 3px; font-size: 10px; font-weight: bold;">🎁 {}</span>',
                _("Gift"),
            )
        return format_html('<span style="color: #6c757d;">-</span>')

    is_gift_badge.short_description = _("Gift")

    actions = ["start_preparing", "mark_ready", "mark_delivered", "cancel_items"]

    @admin.action(description=_("Start preparing selected items"))
    def start_preparing(self, request, queryset):
        """Bulk action to start preparing pending items."""
        count = 0
        for item in queryset.filter(status="pending"):
            try:
                item.start_preparation()
                count += 1
            except ValueError:
                pass
        self.message_user(
            request, _("%(count)d item(s) have started preparation.") % {"count": count}
        )

    @admin.action(description=_("Mark selected items as ready"))
    def mark_ready(self, request, queryset):
        """Bulk action to mark preparing items as ready."""
        count = 0
        for item in queryset.filter(status="preparing"):
            try:
                item.mark_ready()
                count += 1
            except ValueError:
                pass
        self.message_user(
            request,
            _("%(count)d item(s) have been marked as ready.") % {"count": count},
        )

    @admin.action(description=_("Mark selected items as delivered"))
    def mark_delivered(self, request, queryset):
        """Bulk action to mark items as delivered."""
        count = 0
        for item in queryset.filter(status="ready"):
            try:
                item.deliver()
                count += 1
            except ValueError:
                pass
        self.message_user(
            request,
            _("%(count)d item(s) have been marked as delivered.") % {"count": count},
        )

    @admin.action(description=_("Cancel selected items"))
    def cancel_items(self, request, queryset):
        """Bulk action to cancel items."""
        count = 0
        for item in queryset.exclude(status__in=["delivered", "cancelled"]):
            try:
                item.cancel(reason="Cancelled via admin")
                count += 1
            except ValueError:
                pass
        self.message_user(
            request, _("%(count)d item(s) have been cancelled.") % {"count": count}
        )


# =============================================================================
# ServiceRequest Admin
# =============================================================================


@admin.register(ServiceRequest)
class ServiceRequestAdmin(
    EMenumPermissionMixin, SoftDeleteAdminMixin, admin.ModelAdmin
):
    """
    Admin interface for ServiceRequest management.

    Provides management of customer service requests including:
    - Request type tracking (waiter call, bill request, help)
    - Status workflow
    - Response time tracking
    - Staff assignment

    Note: Soft-deleted requests are hidden by default.
    """

    list_display = [
        "table",
        "type_badge",
        "status_badge",
        "priority_badge",
        "assigned_to",
        "response_time_display",
        "created_at",
    ]
    list_filter = [
        "type",
        "status",
        "priority",
        "organization",
        "created_at",
    ]
    search_fields = [
        "table__name",
        "message",
        "organization__name",
        "assigned_to__first_name",
        "assigned_to__last_name",
    ]
    readonly_fields = [
        "id",
        "response_time_seconds",
        "created_at",
        "updated_at",
        "deleted_at",
        "acknowledged_at",
        "completed_at",
        "cancelled_at",
    ]
    ordering = ["-created_at"]
    date_hierarchy = "created_at"
    list_per_page = 25
    autocomplete_fields = [
        "organization",
        "branch",
        "table",
        "order",
        "customer",
        "assigned_to",
    ]

    fieldsets = (
        (
            None,
            {
                "fields": ("id", "organization", "branch", "table", "order"),
            },
        ),
        (
            _("Request Details"),
            {
                "fields": ("type", "status", "priority", "message"),
            },
        ),
        (
            _("Assignment"),
            {
                "fields": ("customer", "assigned_to"),
            },
        ),
        (
            _("Workflow Timestamps"),
            {
                "fields": (
                    "acknowledged_at",
                    "completed_at",
                    "cancelled_at",
                    "cancel_reason",
                    "response_time_seconds",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            _("Metadata"),
            {
                "fields": ("metadata",),
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

    def type_badge(self, obj):
        """Display request type with badge."""
        colors = {
            "waiter_call": "#17a2b8",
            "bill_request": "#28a745",
            "help": "#ffc107",
            "other": "#6c757d",
        }
        text_colors = {
            "help": "#000",
        }
        color = colors.get(obj.type, "#6c757d")
        text_color = text_colors.get(obj.type, "#fff")
        return format_html(
            '<span style="background-color: {}; color: {}; padding: 3px 10px; '
            'border-radius: 3px; font-size: 11px; font-weight: bold;">{}</span>',
            color,
            text_color,
            obj.get_type_display(),
        )

    type_badge.short_description = _("Type")
    type_badge.admin_order_field = "type"

    def status_badge(self, obj):
        """Display status with color-coded badge."""
        colors = {
            "pending": "#ffc107",
            "in_progress": "#17a2b8",
            "completed": "#28a745",
            "cancelled": "#dc3545",
        }
        text_colors = {
            "pending": "#000",
        }
        color = colors.get(obj.status, "#6c757d")
        text_color = text_colors.get(obj.status, "#fff")
        return format_html(
            '<span style="background-color: {}; color: {}; padding: 3px 10px; '
            'border-radius: 3px; font-size: 11px; font-weight: bold;">{}</span>',
            color,
            text_color,
            obj.get_status_display(),
        )

    status_badge.short_description = _("Status")
    status_badge.admin_order_field = "status"

    def priority_badge(self, obj):
        """Display priority with visual indicator."""
        colors = {
            1: "#dc3545",  # Urgent
            2: "#fd7e14",  # High
            3: "#ffc107",  # Normal
            4: "#17a2b8",  # Low
            5: "#6c757d",  # Very low
        }
        labels = {
            1: _("Urgent"),
            2: _("High"),
            3: _("Normal"),
            4: _("Low"),
            5: _("Very Low"),
        }
        color = colors.get(obj.priority, "#6c757d")
        label = labels.get(obj.priority, obj.priority)
        text_color = "#000" if obj.priority == 3 else "#fff"
        return format_html(
            '<span style="background-color: {}; color: {}; padding: 2px 8px; '
            'border-radius: 3px; font-size: 10px; font-weight: bold;">{}</span>',
            color,
            text_color,
            label,
        )

    priority_badge.short_description = _("Priority")
    priority_badge.admin_order_field = "priority"

    def response_time_display(self, obj):
        """Display response time in human-readable format."""
        if obj.response_time_seconds is None:
            return format_html('<span style="color: #6c757d;">-</span>')

        seconds = obj.response_time_seconds
        if seconds < 60:
            return format_html(
                '<span style="color: #28a745;">{} {}</span>', seconds, _("sec")
            )
        elif seconds < 3600:
            minutes = seconds // 60
            return format_html(
                '<span style="color: #ffc107;">{} {}</span>', minutes, _("min")
            )
        else:
            hours = seconds // 3600
            return format_html(
                '<span style="color: #dc3545;">{} {}</span>', hours, _("hr")
            )

    response_time_display.short_description = _("Response Time")

    actions = ["acknowledge_requests", "complete_requests", "cancel_requests"]

    @admin.action(description=_("Acknowledge selected requests"))
    def acknowledge_requests(self, request, queryset):
        """Bulk action to acknowledge pending requests."""
        from django.utils import timezone

        count = queryset.filter(status="pending").update(
            status="in_progress", acknowledged_at=timezone.now()
        )
        self.message_user(
            request,
            _("%(count)d request(s) have been acknowledged.") % {"count": count},
        )

    @admin.action(description=_("Complete selected requests"))
    def complete_requests(self, request, queryset):
        """Bulk action to complete requests."""
        from django.utils import timezone

        count = queryset.filter(status="in_progress").update(
            status="completed", completed_at=timezone.now()
        )
        self.message_user(
            request, _("%(count)d request(s) have been completed.") % {"count": count}
        )

    @admin.action(description=_("Cancel selected requests"))
    def cancel_requests(self, request, queryset):
        """Bulk action to cancel requests."""
        from django.utils import timezone

        count = queryset.exclude(status__in=["completed", "cancelled"]).update(
            status="cancelled",
            cancelled_at=timezone.now(),
            cancel_reason="Cancelled via admin",
        )
        self.message_user(
            request, _("%(count)d request(s) have been cancelled.") % {"count": count}
        )
