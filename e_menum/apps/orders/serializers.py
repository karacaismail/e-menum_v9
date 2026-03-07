"""
Serializers for the Orders application.

This module provides DRF serializers for all order-related models:
- ZoneSerializer: Table zones/sections within a restaurant
- TableSerializer: Physical restaurant tables
- QRCodeSerializer: QR codes for menus and tables
- QRScanSerializer: QR code scan analytics (read-only)
- OrderSerializer: Customer orders with transaction details
- OrderItemSerializer: Individual order line items
- ServiceRequestSerializer: Waiter calls and service requests

API Response Format:
    All serializers work with the E-Menum standard response format:
    {
        "success": true,
        "data": {...}
    }

Multi-Tenancy:
    All tenant-scoped serializers use TenantModelSerializer which
    auto-injects organization from request context.

Critical Rules:
    - Use TenantModelSerializer for tenant-scoped models
    - Never expose deleted_at field in public API responses
    - Always validate cross-tenant references
"""

from typing import Dict, List, Optional

from django.db import transaction
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from apps.orders.models import (
    Zone,
    Table,
    QRCode,
    QRScan,
    Order,
    OrderItem,
    ServiceRequest,
)
from apps.orders.choices import (
    TableStatus,
    QRCodeType,
    OrderStatus,
    OrderType,
)
from shared.serializers.base import (
    TenantModelSerializer,
    MinimalSerializer,
)


# =============================================================================
# MINIMAL SERIALIZERS (For nested representations)
# =============================================================================


class ZoneMinimalSerializer(MinimalSerializer):
    """Minimal zone serializer for nested representations."""

    class Meta:
        model = Zone
        fields = ["id", "name", "slug", "color", "is_active"]


class TableMinimalSerializer(MinimalSerializer):
    """Minimal table serializer for nested representations."""

    class Meta:
        model = Table
        fields = ["id", "name", "slug", "number", "capacity", "status", "is_active"]


class QRCodeMinimalSerializer(MinimalSerializer):
    """Minimal QR code serializer for nested representations."""

    class Meta:
        model = QRCode
        fields = ["id", "code", "name", "type", "is_active"]


class OrderMinimalSerializer(MinimalSerializer):
    """Minimal order serializer for nested representations."""

    class Meta:
        model = Order
        fields = ["id", "order_number", "status", "type", "total_amount", "currency"]


# =============================================================================
# ZONE SERIALIZERS
# =============================================================================


class ZoneListSerializer(TenantModelSerializer):
    """
    Serializer for zone list view.

    Returns a simplified view of zones suitable for listing.
    """

    table_count = serializers.SerializerMethodField(
        help_text=_("Number of tables in this zone")
    )
    available_table_count = serializers.SerializerMethodField(
        help_text=_("Number of available tables in this zone")
    )

    class Meta:
        model = Zone
        fields = [
            "id",
            "name",
            "slug",
            "description",
            "color",
            "icon",
            "capacity",
            "is_active",
            "is_outdoor",
            "is_smoking_allowed",
            "is_reservable",
            "sort_order",
            "organization_id",
            "created_at",
            "updated_at",
            "table_count",
            "available_table_count",
        ]
        read_only_fields = [
            "organization_id",
            "created_at",
            "updated_at",
            "table_count",
            "available_table_count",
        ]

    def get_table_count(self, obj) -> int:
        """Get the number of active tables in this zone."""
        return obj.tables.filter(deleted_at__isnull=True).count()

    def get_available_table_count(self, obj) -> int:
        """Get the number of available tables in this zone."""
        return obj.tables.filter(
            deleted_at__isnull=True, status=TableStatus.AVAILABLE
        ).count()


class ZoneDetailSerializer(TenantModelSerializer):
    """
    Serializer for zone detail view.

    Returns full zone information including tables.
    """

    tables = TableMinimalSerializer(many=True, read_only=True)
    table_count = serializers.SerializerMethodField()
    available_table_count = serializers.SerializerMethodField()
    occupied_table_count = serializers.SerializerMethodField()

    class Meta:
        model = Zone
        fields = [
            "id",
            "name",
            "slug",
            "description",
            "color",
            "icon",
            "capacity",
            "is_active",
            "is_outdoor",
            "is_smoking_allowed",
            "is_reservable",
            "sort_order",
            "settings",
            "organization_id",
            "created_at",
            "updated_at",
            "tables",
            "table_count",
            "available_table_count",
            "occupied_table_count",
        ]
        read_only_fields = [
            "organization_id",
            "created_at",
            "updated_at",
            "tables",
            "table_count",
            "available_table_count",
            "occupied_table_count",
        ]

    def get_table_count(self, obj) -> int:
        return obj.tables.filter(deleted_at__isnull=True).count()

    def get_available_table_count(self, obj) -> int:
        return obj.tables.filter(
            deleted_at__isnull=True, status=TableStatus.AVAILABLE
        ).count()

    def get_occupied_table_count(self, obj) -> int:
        return obj.tables.filter(
            deleted_at__isnull=True, status=TableStatus.OCCUPIED
        ).count()


class ZoneCreateSerializer(TenantModelSerializer):
    """Serializer for creating a new zone."""

    class Meta:
        model = Zone
        fields = [
            "name",
            "slug",
            "description",
            "color",
            "icon",
            "capacity",
            "is_active",
            "is_outdoor",
            "is_smoking_allowed",
            "is_reservable",
            "sort_order",
            "settings",
        ]

    def validate_slug(self, value: str) -> str:
        """Validate slug uniqueness within organization."""
        request = self.context.get("request")
        organization = getattr(request, "organization", None) if request else None

        if organization:
            existing = Zone.objects.filter(
                organization=organization, slug=value, deleted_at__isnull=True
            ).exists()
            if existing:
                raise ValidationError(_("A zone with this slug already exists."))

        return value


class ZoneUpdateSerializer(TenantModelSerializer):
    """Serializer for updating an existing zone."""

    class Meta:
        model = Zone
        fields = [
            "name",
            "slug",
            "description",
            "color",
            "icon",
            "capacity",
            "is_active",
            "is_outdoor",
            "is_smoking_allowed",
            "is_reservable",
            "sort_order",
            "settings",
        ]

    def validate_slug(self, value: str) -> str:
        """Validate slug uniqueness within organization (excluding current zone)."""
        request = self.context.get("request")
        organization = getattr(request, "organization", None) if request else None
        instance = self.instance

        if organization and instance:
            existing = (
                Zone.objects.filter(
                    organization=organization, slug=value, deleted_at__isnull=True
                )
                .exclude(pk=instance.pk)
                .exists()
            )
            if existing:
                raise ValidationError(_("A zone with this slug already exists."))

        return value


# =============================================================================
# TABLE SERIALIZERS
# =============================================================================


class TableListSerializer(TenantModelSerializer):
    """Serializer for table list view."""

    zone = ZoneMinimalSerializer(read_only=True)

    class Meta:
        model = Table
        fields = [
            "id",
            "name",
            "number",
            "slug",
            "zone",
            "capacity",
            "min_capacity",
            "status",
            "is_active",
            "is_vip",
            "shape",
            "sort_order",
            "organization_id",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["organization_id", "created_at", "updated_at"]


class TableDetailSerializer(TenantModelSerializer):
    """Serializer for table detail view."""

    zone = ZoneMinimalSerializer(read_only=True)
    zone_id = serializers.UUIDField(
        write_only=True, required=False, help_text=_("Zone UUID this table belongs to")
    )
    qr_codes = QRCodeMinimalSerializer(many=True, read_only=True)
    active_orders = serializers.SerializerMethodField(
        help_text=_("Active orders at this table")
    )

    class Meta:
        model = Table
        fields = [
            "id",
            "name",
            "number",
            "slug",
            "zone",
            "zone_id",
            "capacity",
            "min_capacity",
            "status",
            "is_active",
            "is_vip",
            "position_x",
            "position_y",
            "shape",
            "sort_order",
            "notes",
            "settings",
            "organization_id",
            "created_at",
            "updated_at",
            "qr_codes",
            "active_orders",
        ]
        read_only_fields = [
            "organization_id",
            "created_at",
            "updated_at",
            "qr_codes",
            "active_orders",
        ]

    def get_active_orders(self, obj) -> List[Dict]:
        """Get active orders at this table."""
        active_statuses = [
            OrderStatus.PENDING,
            OrderStatus.CONFIRMED,
            OrderStatus.PREPARING,
            OrderStatus.READY,
            OrderStatus.DELIVERED,
        ]
        orders = obj.orders.filter(
            deleted_at__isnull=True, status__in=active_statuses
        ).order_by("-created_at")[:5]
        return OrderMinimalSerializer(orders, many=True).data


class TableCreateSerializer(TenantModelSerializer):
    """Serializer for creating a new table."""

    zone_id = serializers.UUIDField(
        required=True, help_text=_("Zone UUID this table belongs to")
    )

    class Meta:
        model = Table
        fields = [
            "name",
            "number",
            "slug",
            "zone_id",
            "capacity",
            "min_capacity",
            "status",
            "is_active",
            "is_vip",
            "position_x",
            "position_y",
            "shape",
            "sort_order",
            "notes",
            "settings",
        ]

    def validate_zone_id(self, value):
        """Validate zone belongs to the same organization."""
        request = self.context.get("request")
        organization = getattr(request, "organization", None) if request else None

        if organization:
            try:
                zone = Zone.objects.get(
                    id=value, organization=organization, deleted_at__isnull=True
                )
                return zone
            except Zone.DoesNotExist:
                raise ValidationError(_("Zone not found."))

        raise ValidationError(_("Organization context required."))

    def validate_slug(self, value: str) -> str:
        """Validate slug uniqueness within organization."""
        request = self.context.get("request")
        organization = getattr(request, "organization", None) if request else None

        if organization:
            existing = Table.objects.filter(
                organization=organization, slug=value, deleted_at__isnull=True
            ).exists()
            if existing:
                raise ValidationError(_("A table with this slug already exists."))

        return value

    def create(self, validated_data):
        """Create table with zone handling."""
        zone = validated_data.pop("zone_id")
        validated_data["zone"] = zone
        return super().create(validated_data)


class TableUpdateSerializer(TenantModelSerializer):
    """Serializer for updating an existing table."""

    zone_id = serializers.UUIDField(
        required=False, help_text=_("Zone UUID this table belongs to")
    )

    class Meta:
        model = Table
        fields = [
            "name",
            "number",
            "slug",
            "zone_id",
            "capacity",
            "min_capacity",
            "status",
            "is_active",
            "is_vip",
            "position_x",
            "position_y",
            "shape",
            "sort_order",
            "notes",
            "settings",
        ]

    def validate_zone_id(self, value):
        """Validate zone belongs to the same organization."""
        request = self.context.get("request")
        organization = getattr(request, "organization", None) if request else None

        if organization:
            try:
                zone = Zone.objects.get(
                    id=value, organization=organization, deleted_at__isnull=True
                )
                return zone
            except Zone.DoesNotExist:
                raise ValidationError(_("Zone not found."))

        return value

    def validate_slug(self, value: str) -> str:
        """Validate slug uniqueness within organization (excluding current table)."""
        request = self.context.get("request")
        organization = getattr(request, "organization", None) if request else None
        instance = self.instance

        if organization and instance:
            existing = (
                Table.objects.filter(
                    organization=organization, slug=value, deleted_at__isnull=True
                )
                .exclude(pk=instance.pk)
                .exists()
            )
            if existing:
                raise ValidationError(_("A table with this slug already exists."))

        return value

    def update(self, instance, validated_data):
        """Update table with zone handling."""
        zone = validated_data.pop("zone_id", None)
        if zone is not None:
            validated_data["zone"] = zone
        return super().update(instance, validated_data)


# =============================================================================
# QR CODE SERIALIZERS
# =============================================================================


class QRCodeListSerializer(TenantModelSerializer):
    """Serializer for QR code list view."""

    menu = serializers.SerializerMethodField()
    table = TableMinimalSerializer(read_only=True)

    class Meta:
        model = QRCode
        fields = [
            "id",
            "code",
            "name",
            "type",
            "menu",
            "table",
            "short_url",
            "qr_image_url",
            "is_active",
            "expires_at",
            "scan_count",
            "unique_scan_count",
            "last_scanned_at",
            "organization_id",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "organization_id",
            "created_at",
            "updated_at",
            "scan_count",
            "unique_scan_count",
            "last_scanned_at",
        ]

    def get_menu(self, obj) -> Optional[Dict]:
        """Get minimal menu info if linked."""
        if obj.menu:
            return {
                "id": str(obj.menu.id),
                "name": obj.menu.name,
                "slug": obj.menu.slug,
            }
        return None


class QRCodeDetailSerializer(TenantModelSerializer):
    """Serializer for QR code detail view."""

    menu = serializers.SerializerMethodField()
    table = TableMinimalSerializer(read_only=True)
    menu_id = serializers.UUIDField(
        write_only=True,
        required=False,
        allow_null=True,
        help_text=_("Menu UUID to link this QR code to"),
    )
    table_id = serializers.UUIDField(
        write_only=True,
        required=False,
        allow_null=True,
        help_text=_("Table UUID to link this QR code to"),
    )

    class Meta:
        model = QRCode
        fields = [
            "id",
            "code",
            "name",
            "description",
            "type",
            "menu",
            "menu_id",
            "table",
            "table_id",
            "short_url",
            "qr_image_url",
            "redirect_url",
            "is_active",
            "expires_at",
            "scan_count",
            "unique_scan_count",
            "last_scanned_at",
            "settings",
            "metadata",
            "organization_id",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "organization_id",
            "created_at",
            "updated_at",
            "scan_count",
            "unique_scan_count",
            "last_scanned_at",
        ]

    def get_menu(self, obj) -> Optional[Dict]:
        """Get minimal menu info if linked."""
        if obj.menu:
            return {
                "id": str(obj.menu.id),
                "name": obj.menu.name,
                "slug": obj.menu.slug,
            }
        return None


class QRCodeCreateSerializer(TenantModelSerializer):
    """Serializer for creating a new QR code."""

    menu_id = serializers.UUIDField(
        required=False,
        allow_null=True,
        help_text=_("Menu UUID to link this QR code to"),
    )
    table_id = serializers.UUIDField(
        required=False,
        allow_null=True,
        help_text=_("Table UUID to link this QR code to"),
    )

    class Meta:
        model = QRCode
        fields = [
            "code",
            "name",
            "description",
            "type",
            "menu_id",
            "table_id",
            "short_url",
            "qr_image_url",
            "redirect_url",
            "is_active",
            "expires_at",
            "settings",
            "metadata",
        ]

    def validate_code(self, value: str) -> str:
        """Validate code uniqueness within organization."""
        request = self.context.get("request")
        organization = getattr(request, "organization", None) if request else None

        if organization:
            existing = QRCode.objects.filter(
                organization=organization, code=value, deleted_at__isnull=True
            ).exists()
            if existing:
                raise ValidationError(_("A QR code with this code already exists."))

        return value

    def validate_menu_id(self, value):
        """Validate menu belongs to the same organization."""
        if value is None:
            return None

        request = self.context.get("request")
        organization = getattr(request, "organization", None) if request else None

        if organization:
            from apps.menu.models import Menu

            try:
                menu = Menu.objects.get(
                    id=value, organization=organization, deleted_at__isnull=True
                )
                return menu
            except Menu.DoesNotExist:
                raise ValidationError(_("Menu not found."))

        return value

    def validate_table_id(self, value):
        """Validate table belongs to the same organization."""
        if value is None:
            return None

        request = self.context.get("request")
        organization = getattr(request, "organization", None) if request else None

        if organization:
            try:
                table = Table.objects.get(
                    id=value, organization=organization, deleted_at__isnull=True
                )
                return table
            except Table.DoesNotExist:
                raise ValidationError(_("Table not found."))

        return value

    def validate(self, attrs):
        """Validate QR code type matches linked entity."""
        attrs = super().validate(attrs)

        qr_type = attrs.get("type", QRCodeType.MENU)
        attrs.get("menu_id")
        table = attrs.get("table_id")

        if qr_type == QRCodeType.TABLE and not table:
            raise ValidationError(
                {"table_id": _("Table is required for TABLE type QR codes.")}
            )

        return attrs

    def create(self, validated_data):
        """Create QR code with menu/table handling."""
        menu = validated_data.pop("menu_id", None)
        table = validated_data.pop("table_id", None)

        if menu:
            validated_data["menu"] = menu
        if table:
            validated_data["table"] = table

        return super().create(validated_data)


class QRCodeUpdateSerializer(TenantModelSerializer):
    """Serializer for updating an existing QR code."""

    menu_id = serializers.UUIDField(
        required=False,
        allow_null=True,
        help_text=_("Menu UUID to link this QR code to"),
    )
    table_id = serializers.UUIDField(
        required=False,
        allow_null=True,
        help_text=_("Table UUID to link this QR code to"),
    )

    class Meta:
        model = QRCode
        fields = [
            "code",
            "name",
            "description",
            "type",
            "menu_id",
            "table_id",
            "short_url",
            "qr_image_url",
            "redirect_url",
            "is_active",
            "expires_at",
            "settings",
            "metadata",
        ]

    def validate_code(self, value: str) -> str:
        """Validate code uniqueness within organization (excluding current QR code)."""
        request = self.context.get("request")
        organization = getattr(request, "organization", None) if request else None
        instance = self.instance

        if organization and instance:
            existing = (
                QRCode.objects.filter(
                    organization=organization, code=value, deleted_at__isnull=True
                )
                .exclude(pk=instance.pk)
                .exists()
            )
            if existing:
                raise ValidationError(_("A QR code with this code already exists."))

        return value

    def validate_menu_id(self, value):
        """Validate menu belongs to the same organization."""
        if value is None:
            return None

        request = self.context.get("request")
        organization = getattr(request, "organization", None) if request else None

        if organization:
            from apps.menu.models import Menu

            try:
                menu = Menu.objects.get(
                    id=value, organization=organization, deleted_at__isnull=True
                )
                return menu
            except Menu.DoesNotExist:
                raise ValidationError(_("Menu not found."))

        return value

    def validate_table_id(self, value):
        """Validate table belongs to the same organization."""
        if value is None:
            return None

        request = self.context.get("request")
        organization = getattr(request, "organization", None) if request else None

        if organization:
            try:
                table = Table.objects.get(
                    id=value, organization=organization, deleted_at__isnull=True
                )
                return table
            except Table.DoesNotExist:
                raise ValidationError(_("Table not found."))

        return value

    def update(self, instance, validated_data):
        """Update QR code with menu/table handling."""
        menu = validated_data.pop("menu_id", None)
        table = validated_data.pop("table_id", None)

        if menu is not None:
            validated_data["menu"] = menu
        if table is not None:
            validated_data["table"] = table

        return super().update(instance, validated_data)


# =============================================================================
# QR SCAN SERIALIZERS (Read-only analytics)
# =============================================================================


class QRScanSerializer(TenantModelSerializer):
    """Serializer for QR scan analytics (read-only)."""

    qr_code = QRCodeMinimalSerializer(read_only=True)

    class Meta:
        model = QRScan
        fields = [
            "id",
            "qr_code",
            "scanned_at",
            "ip_address",
            "device_type",
            "browser",
            "os",
            "country",
            "city",
            "is_unique",
            "created_at",
        ]
        read_only_fields = "__all__"


# =============================================================================
# ORDER SERIALIZERS
# =============================================================================


class OrderItemSerializer(TenantModelSerializer):
    """Serializer for order items (inline in order detail)."""

    product_name = serializers.SerializerMethodField()
    variant_name = serializers.SerializerMethodField()

    class Meta:
        model = OrderItem
        fields = [
            "id",
            "product",
            "product_name",
            "variant",
            "variant_name",
            "quantity",
            "unit_price",
            "total_price",
            "currency",
            "status",
            "modifiers",
            "notes",
            "is_gift",
            "prepared_at",
            "delivered_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "created_at",
            "updated_at",
            "product_name",
            "variant_name",
        ]

    def get_product_name(self, obj) -> str:
        """Get product name."""
        return obj.product.name if obj.product else _("Deleted Product")

    def get_variant_name(self, obj) -> Optional[str]:
        """Get variant name if available."""
        return obj.variant.name if obj.variant else None


class OrderListSerializer(TenantModelSerializer):
    """Serializer for order list view."""

    table = TableMinimalSerializer(read_only=True)
    item_count = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            "id",
            "order_number",
            "status",
            "type",
            "payment_status",
            "payment_method",
            "table",
            "subtotal",
            "tax_amount",
            "discount_amount",
            "total_amount",
            "currency",
            "guest_count",
            "placed_at",
            "item_count",
            "organization_id",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["organization_id", "created_at", "updated_at", "item_count"]

    def get_item_count(self, obj) -> int:
        """Get the number of items in this order."""
        return obj.items.filter(deleted_at__isnull=True).count()


class OrderDetailSerializer(TenantModelSerializer):
    """Serializer for order detail view."""

    table = TableMinimalSerializer(read_only=True)
    table_id = serializers.UUIDField(
        write_only=True,
        required=False,
        allow_null=True,
        help_text=_("Table UUID for dine-in orders"),
    )
    items = OrderItemSerializer(many=True, read_only=True)
    item_count = serializers.SerializerMethodField()
    item_quantity = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            "id",
            "order_number",
            "status",
            "type",
            "payment_status",
            "payment_method",
            "table",
            "table_id",
            "customer",
            "subtotal",
            "tax_amount",
            "discount_amount",
            "tip_amount",
            "total_amount",
            "currency",
            "guest_count",
            "notes",
            "special_instructions",
            "customer_info",
            "delivery_address",
            "placed_at",
            "confirmed_at",
            "preparing_at",
            "ready_at",
            "delivered_at",
            "completed_at",
            "cancelled_at",
            "cancel_reason",
            "placed_by",
            "assigned_to",
            "metadata",
            "items",
            "item_count",
            "item_quantity",
            "organization_id",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "organization_id",
            "created_at",
            "updated_at",
            "items",
            "item_count",
            "item_quantity",
            "placed_at",
            "confirmed_at",
            "preparing_at",
            "ready_at",
            "delivered_at",
            "completed_at",
            "cancelled_at",
        ]

    def get_item_count(self, obj) -> int:
        return obj.items.filter(deleted_at__isnull=True).count()

    def get_item_quantity(self, obj) -> int:
        from django.db.models import Sum

        result = obj.items.filter(deleted_at__isnull=True).aggregate(
            total=Sum("quantity")
        )
        return result["total"] or 0


class OrderCreateSerializer(TenantModelSerializer):
    """Serializer for creating a new order."""

    table_id = serializers.UUIDField(
        required=False, allow_null=True, help_text=_("Table UUID for dine-in orders")
    )
    items = serializers.ListField(
        child=serializers.DictField(),
        required=False,
        write_only=True,
        help_text=_("List of order items to create with the order"),
    )

    class Meta:
        model = Order
        fields = [
            "order_number",
            "type",
            "table_id",
            "customer",
            "guest_count",
            "notes",
            "special_instructions",
            "customer_info",
            "delivery_address",
            "metadata",
            "items",
        ]

    def validate_order_number(self, value: str) -> str:
        """Validate order number uniqueness within organization."""
        request = self.context.get("request")
        organization = getattr(request, "organization", None) if request else None

        if organization:
            existing = Order.objects.filter(
                organization=organization, order_number=value, deleted_at__isnull=True
            ).exists()
            if existing:
                raise ValidationError(_("An order with this number already exists."))

        return value

    def validate_table_id(self, value):
        """Validate table belongs to the same organization."""
        if value is None:
            return None

        request = self.context.get("request")
        organization = getattr(request, "organization", None) if request else None

        if organization:
            try:
                table = Table.objects.get(
                    id=value, organization=organization, deleted_at__isnull=True
                )
                return table
            except Table.DoesNotExist:
                raise ValidationError(_("Table not found."))

        return value

    def validate(self, attrs):
        """Validate order type matches table presence."""
        attrs = super().validate(attrs)

        order_type = attrs.get("type", OrderType.DINE_IN)
        table = attrs.get("table_id")

        if order_type == OrderType.DINE_IN and not table:
            raise ValidationError(
                {"table_id": _("Table is required for dine-in orders.")}
            )

        if order_type == OrderType.DELIVERY:
            delivery_address = attrs.get("delivery_address", {})
            if not delivery_address:
                raise ValidationError(
                    {
                        "delivery_address": _(
                            "Delivery address is required for delivery orders."
                        )
                    }
                )

        return attrs

    @transaction.atomic
    def create(self, validated_data):
        """Create order with table handling and optional items."""

        table = validated_data.pop("table_id", None)
        items_data = validated_data.pop("items", [])

        if table:
            validated_data["table"] = table

        # Set placed_at timestamp
        validated_data["placed_at"] = timezone.now()

        order = super().create(validated_data)

        # Create order items if provided
        for item_data in items_data:
            OrderItem.objects.create(order=order, **item_data)

        # Recalculate totals
        order.calculate_totals()

        return order


class OrderUpdateSerializer(TenantModelSerializer):
    """Serializer for updating an existing order."""

    table_id = serializers.UUIDField(
        required=False, allow_null=True, help_text=_("Table UUID for dine-in orders")
    )

    class Meta:
        model = Order
        fields = [
            "type",
            "table_id",
            "guest_count",
            "notes",
            "special_instructions",
            "customer_info",
            "delivery_address",
            "tax_amount",
            "discount_amount",
            "tip_amount",
            "metadata",
        ]

    def validate_table_id(self, value):
        """Validate table belongs to the same organization."""
        if value is None:
            return None

        request = self.context.get("request")
        organization = getattr(request, "organization", None) if request else None

        if organization:
            try:
                table = Table.objects.get(
                    id=value, organization=organization, deleted_at__isnull=True
                )
                return table
            except Table.DoesNotExist:
                raise ValidationError(_("Table not found."))

        return value

    def update(self, instance, validated_data):
        """Update order with table handling."""
        table = validated_data.pop("table_id", None)
        if table is not None:
            validated_data["table"] = table

        instance = super().update(instance, validated_data)

        # Recalculate totals if financial fields changed
        if any(
            f in validated_data for f in ["tax_amount", "discount_amount", "tip_amount"]
        ):
            instance.calculate_totals()

        return instance


# =============================================================================
# SERVICE REQUEST SERIALIZERS
# =============================================================================


class ServiceRequestListSerializer(TenantModelSerializer):
    """Serializer for service request list view."""

    table = TableMinimalSerializer(read_only=True)

    class Meta:
        model = ServiceRequest
        fields = [
            "id",
            "table",
            "type",
            "status",
            "priority",
            "message",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["organization_id", "created_at", "updated_at"]


class ServiceRequestDetailSerializer(TenantModelSerializer):
    """Serializer for service request detail view."""

    table = TableMinimalSerializer(read_only=True)
    table_id = serializers.UUIDField(
        write_only=True,
        required=False,
        help_text=_("Table UUID for the service request"),
    )

    class Meta:
        model = ServiceRequest
        fields = [
            "id",
            "table",
            "table_id",
            "type",
            "status",
            "priority",
            "message",
            "acknowledged_at",
            "completed_at",
            "cancelled_at",
            "cancel_reason",
            "assigned_to",
            "metadata",
            "organization_id",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "organization_id",
            "created_at",
            "updated_at",
            "acknowledged_at",
            "completed_at",
            "cancelled_at",
        ]


class ServiceRequestCreateSerializer(TenantModelSerializer):
    """Serializer for creating a new service request."""

    table_id = serializers.UUIDField(
        required=True, help_text=_("Table UUID for the service request")
    )

    class Meta:
        model = ServiceRequest
        fields = [
            "table_id",
            "type",
            "priority",
            "message",
            "metadata",
        ]

    def validate_table_id(self, value):
        """Validate table belongs to the same organization."""
        request = self.context.get("request")
        organization = getattr(request, "organization", None) if request else None

        if organization:
            try:
                table = Table.objects.get(
                    id=value, organization=organization, deleted_at__isnull=True
                )
                return table
            except Table.DoesNotExist:
                raise ValidationError(_("Table not found."))

        raise ValidationError(_("Organization context required."))

    def create(self, validated_data):
        """Create service request with table handling."""
        table = validated_data.pop("table_id")
        validated_data["table"] = table
        return super().create(validated_data)


class ServiceRequestUpdateSerializer(TenantModelSerializer):
    """Serializer for updating an existing service request."""

    class Meta:
        model = ServiceRequest
        fields = [
            "status",
            "priority",
            "message",
            "metadata",
        ]


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Minimal serializers
    "ZoneMinimalSerializer",
    "TableMinimalSerializer",
    "QRCodeMinimalSerializer",
    "OrderMinimalSerializer",
    # Zone serializers
    "ZoneListSerializer",
    "ZoneDetailSerializer",
    "ZoneCreateSerializer",
    "ZoneUpdateSerializer",
    # Table serializers
    "TableListSerializer",
    "TableDetailSerializer",
    "TableCreateSerializer",
    "TableUpdateSerializer",
    # QR code serializers
    "QRCodeListSerializer",
    "QRCodeDetailSerializer",
    "QRCodeCreateSerializer",
    "QRCodeUpdateSerializer",
    # QR scan serializers
    "QRScanSerializer",
    # Order serializers
    "OrderListSerializer",
    "OrderDetailSerializer",
    "OrderCreateSerializer",
    "OrderUpdateSerializer",
    # Order item serializers
    "OrderItemSerializer",
    # Service request serializers
    "ServiceRequestListSerializer",
    "ServiceRequestDetailSerializer",
    "ServiceRequestCreateSerializer",
    "ServiceRequestUpdateSerializer",
]
