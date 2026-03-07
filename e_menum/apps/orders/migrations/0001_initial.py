# Generated manually for E-Menum Orders Module
# This migration creates all order-related models

import uuid
from decimal import Decimal
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    """
    Initial migration for the orders module.

    Creates:
    - Zone: Table groupings/sections within a restaurant
    - Table: Physical restaurant tables with status tracking
    - QRCode: Generated QR codes for menus/tables with scan analytics
    - QRScan: QR code scan tracking for analytics
    - Order: Customer orders with full transaction details and status workflow
    - OrderItem: Individual line items within orders
    - ServiceRequest: Waiter call/service requests from tables
    """

    initial = True

    dependencies = [
        ("core", "0001_initial"),
        ("menu", "0001_initial"),
    ]

    operations = [
        # 1. Zone model (table groupings/sections)
        migrations.CreateModel(
            name="Zone",
            fields=[
                (
                    "created_at",
                    models.DateTimeField(
                        auto_now_add=True,
                        help_text="Timestamp when record was created",
                        verbose_name="Created at",
                    ),
                ),
                (
                    "updated_at",
                    models.DateTimeField(
                        auto_now=True,
                        help_text="Timestamp when record was last updated",
                        verbose_name="Updated at",
                    ),
                ),
                (
                    "deleted_at",
                    models.DateTimeField(
                        blank=True,
                        db_index=True,
                        help_text="Timestamp when record was soft-deleted (null = active)",
                        null=True,
                        verbose_name="Deleted at",
                    ),
                ),
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        help_text="Unique identifier (UUID)",
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "name",
                    models.CharField(
                        help_text="Display name of the zone (e.g., Garden, VIP Section)",
                        max_length=100,
                        verbose_name="Name",
                    ),
                ),
                (
                    "slug",
                    models.SlugField(
                        help_text="URL-friendly identifier (unique within organization)",
                        max_length=100,
                        verbose_name="Slug",
                    ),
                ),
                (
                    "description",
                    models.TextField(
                        blank=True,
                        help_text="Optional description of the zone and its characteristics",
                        null=True,
                        verbose_name="Description",
                    ),
                ),
                (
                    "color",
                    models.CharField(
                        default="#3B82F6",
                        help_text="Hex color code for visual identification (e.g., #3B82F6)",
                        max_length=7,
                        verbose_name="Color",
                    ),
                ),
                (
                    "icon",
                    models.CharField(
                        blank=True,
                        help_text="Icon name or URL for zone representation in UI",
                        max_length=100,
                        null=True,
                        verbose_name="Icon",
                    ),
                ),
                (
                    "capacity",
                    models.PositiveIntegerField(
                        blank=True,
                        help_text="Maximum number of guests the zone can accommodate",
                        null=True,
                        verbose_name="Capacity",
                    ),
                ),
                (
                    "is_active",
                    models.BooleanField(
                        db_index=True,
                        default=True,
                        help_text="Whether the zone is available for seating",
                        verbose_name="Is active",
                    ),
                ),
                (
                    "is_smoking_allowed",
                    models.BooleanField(
                        default=False,
                        help_text="Whether smoking is permitted in this zone",
                        verbose_name="Is smoking allowed",
                    ),
                ),
                (
                    "is_outdoor",
                    models.BooleanField(
                        default=False,
                        help_text="Whether the zone is located outdoors",
                        verbose_name="Is outdoor",
                    ),
                ),
                (
                    "is_reservable",
                    models.BooleanField(
                        default=True,
                        help_text="Whether tables in this zone can be reserved",
                        verbose_name="Is reservable",
                    ),
                ),
                (
                    "sort_order",
                    models.PositiveIntegerField(
                        default=0,
                        help_text="Display order for zones (lower numbers appear first)",
                        verbose_name="Sort order",
                    ),
                ),
                (
                    "settings",
                    models.JSONField(
                        blank=True,
                        default=dict,
                        help_text="Zone-specific settings (JSON)",
                        verbose_name="Settings",
                    ),
                ),
                (
                    "organization",
                    models.ForeignKey(
                        help_text="Organization this zone belongs to",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="zones",
                        to="core.organization",
                        verbose_name="Organization",
                    ),
                ),
                (
                    "branch",
                    models.ForeignKey(
                        blank=True,
                        help_text="Branch this zone belongs to (optional for single-location)",
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="zones",
                        to="core.branch",
                        verbose_name="Branch",
                    ),
                ),
            ],
            options={
                "verbose_name": "Zone",
                "verbose_name_plural": "Zones",
                "db_table": "zones",
                "ordering": ["sort_order", "name"],
            },
        ),
        migrations.AddConstraint(
            model_name="zone",
            constraint=models.UniqueConstraint(
                fields=["organization", "slug"], name="zone_org_slug_uniq"
            ),
        ),
        migrations.AddIndex(
            model_name="zone",
            index=models.Index(
                fields=["organization", "is_active"], name="zone_org_active_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="zone",
            index=models.Index(
                fields=["organization", "deleted_at"], name="zone_org_deleted_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="zone",
            index=models.Index(
                fields=["organization", "branch"], name="zone_org_branch_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="zone",
            index=models.Index(
                fields=["organization", "sort_order"], name="zone_org_sort_idx"
            ),
        ),
        # 2. Table model (physical restaurant tables)
        migrations.CreateModel(
            name="Table",
            fields=[
                (
                    "created_at",
                    models.DateTimeField(
                        auto_now_add=True,
                        help_text="Timestamp when record was created",
                        verbose_name="Created at",
                    ),
                ),
                (
                    "updated_at",
                    models.DateTimeField(
                        auto_now=True,
                        help_text="Timestamp when record was last updated",
                        verbose_name="Updated at",
                    ),
                ),
                (
                    "deleted_at",
                    models.DateTimeField(
                        blank=True,
                        db_index=True,
                        help_text="Timestamp when record was soft-deleted (null = active)",
                        null=True,
                        verbose_name="Deleted at",
                    ),
                ),
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        help_text="Unique identifier (UUID)",
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "name",
                    models.CharField(
                        help_text='Display name/number of the table (e.g., "Table 1", "A-12")',
                        max_length=50,
                        verbose_name="Name",
                    ),
                ),
                (
                    "number",
                    models.PositiveIntegerField(
                        blank=True,
                        help_text="Numeric table number for ordering and quick reference",
                        null=True,
                        verbose_name="Number",
                    ),
                ),
                (
                    "slug",
                    models.SlugField(
                        help_text="URL-friendly identifier (unique within organization)",
                        max_length=50,
                        verbose_name="Slug",
                    ),
                ),
                (
                    "capacity",
                    models.PositiveSmallIntegerField(
                        default=4,
                        help_text="Maximum number of guests the table can seat",
                        verbose_name="Capacity",
                    ),
                ),
                (
                    "min_capacity",
                    models.PositiveSmallIntegerField(
                        default=1,
                        help_text="Minimum number of guests required for reservation",
                        verbose_name="Minimum capacity",
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("AVAILABLE", "Available"),
                            ("OCCUPIED", "Occupied"),
                            ("RESERVED", "Reserved"),
                        ],
                        db_index=True,
                        default="AVAILABLE",
                        help_text="Current table status (available, occupied, reserved)",
                        max_length=20,
                        verbose_name="Status",
                    ),
                ),
                (
                    "is_active",
                    models.BooleanField(
                        db_index=True,
                        default=True,
                        help_text="Whether the table is available for use (can be disabled for maintenance)",
                        verbose_name="Is active",
                    ),
                ),
                (
                    "is_vip",
                    models.BooleanField(
                        default=False,
                        help_text="Whether this is a VIP/premium table",
                        verbose_name="Is VIP",
                    ),
                ),
                (
                    "position_x",
                    models.PositiveIntegerField(
                        blank=True,
                        help_text="X coordinate for floor plan visualization",
                        null=True,
                        verbose_name="Position X",
                    ),
                ),
                (
                    "position_y",
                    models.PositiveIntegerField(
                        blank=True,
                        help_text="Y coordinate for floor plan visualization",
                        null=True,
                        verbose_name="Position Y",
                    ),
                ),
                (
                    "shape",
                    models.CharField(
                        default="rectangle",
                        help_text="Table shape for visualization (round, square, rectangle)",
                        max_length=20,
                        verbose_name="Shape",
                    ),
                ),
                (
                    "sort_order",
                    models.PositiveIntegerField(
                        default=0,
                        help_text="Display order within the zone (lower numbers appear first)",
                        verbose_name="Sort order",
                    ),
                ),
                (
                    "notes",
                    models.TextField(
                        blank=True,
                        help_text='Staff notes about the table (e.g., "near window", "wheelchair accessible")',
                        null=True,
                        verbose_name="Notes",
                    ),
                ),
                (
                    "settings",
                    models.JSONField(
                        blank=True,
                        default=dict,
                        help_text="Table-specific settings (JSON)",
                        verbose_name="Settings",
                    ),
                ),
                (
                    "organization",
                    models.ForeignKey(
                        help_text="Organization this table belongs to",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="tables",
                        to="core.organization",
                        verbose_name="Organization",
                    ),
                ),
                (
                    "zone",
                    models.ForeignKey(
                        help_text="Zone/section this table belongs to",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="tables",
                        to="orders.zone",
                        verbose_name="Zone",
                    ),
                ),
                (
                    "branch",
                    models.ForeignKey(
                        blank=True,
                        help_text="Branch this table belongs to (optional for single-location)",
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="tables",
                        to="core.branch",
                        verbose_name="Branch",
                    ),
                ),
            ],
            options={
                "verbose_name": "Table",
                "verbose_name_plural": "Tables",
                "db_table": "tables",
                "ordering": ["zone", "sort_order", "number", "name"],
            },
        ),
        migrations.AddConstraint(
            model_name="table",
            constraint=models.UniqueConstraint(
                fields=["organization", "slug"], name="table_org_slug_uniq"
            ),
        ),
        migrations.AddIndex(
            model_name="table",
            index=models.Index(
                fields=["organization", "status"], name="table_org_status_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="table",
            index=models.Index(
                fields=["organization", "is_active"], name="table_org_active_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="table",
            index=models.Index(
                fields=["organization", "deleted_at"], name="table_org_deleted_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="table",
            index=models.Index(
                fields=["organization", "zone"], name="table_org_zone_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="table",
            index=models.Index(
                fields=["organization", "branch"], name="table_org_branch_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="table",
            index=models.Index(fields=["zone", "status"], name="table_zone_status_idx"),
        ),
        migrations.AddIndex(
            model_name="table",
            index=models.Index(
                fields=["zone", "sort_order"], name="table_zone_sort_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="table",
            index=models.Index(
                fields=["organization", "number"], name="table_org_number_idx"
            ),
        ),
        # 3. QRCode model (generated QR codes for menus/tables)
        migrations.CreateModel(
            name="QRCode",
            fields=[
                (
                    "created_at",
                    models.DateTimeField(
                        auto_now_add=True,
                        help_text="Timestamp when record was created",
                        verbose_name="Created at",
                    ),
                ),
                (
                    "updated_at",
                    models.DateTimeField(
                        auto_now=True,
                        help_text="Timestamp when record was last updated",
                        verbose_name="Updated at",
                    ),
                ),
                (
                    "deleted_at",
                    models.DateTimeField(
                        blank=True,
                        db_index=True,
                        help_text="Timestamp when record was soft-deleted (null = active)",
                        null=True,
                        verbose_name="Deleted at",
                    ),
                ),
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        help_text="Unique identifier (UUID)",
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "type",
                    models.CharField(
                        choices=[
                            ("MENU", "Menu"),
                            ("TABLE", "Table"),
                            ("CAMPAIGN", "Campaign"),
                        ],
                        db_index=True,
                        default="MENU",
                        help_text="Type of QR code (MENU, TABLE, CAMPAIGN)",
                        max_length=20,
                        verbose_name="Type",
                    ),
                ),
                (
                    "code",
                    models.CharField(
                        help_text="Unique code/slug for the QR code URL (unique within organization)",
                        max_length=100,
                        verbose_name="Code",
                    ),
                ),
                (
                    "name",
                    models.CharField(
                        help_text="Display name for the QR code",
                        max_length=100,
                        verbose_name="Name",
                    ),
                ),
                (
                    "description",
                    models.TextField(
                        blank=True,
                        help_text="Optional description of the QR code purpose",
                        null=True,
                        verbose_name="Description",
                    ),
                ),
                (
                    "short_url",
                    models.URLField(
                        blank=True,
                        help_text="Generated short URL for QR scanning",
                        max_length=500,
                        null=True,
                        verbose_name="Short URL",
                    ),
                ),
                (
                    "qr_image_url",
                    models.URLField(
                        blank=True,
                        help_text="URL to the generated QR code image",
                        max_length=500,
                        null=True,
                        verbose_name="QR image URL",
                    ),
                ),
                (
                    "redirect_url",
                    models.URLField(
                        blank=True,
                        help_text="Custom redirect URL (overrides default behavior)",
                        max_length=500,
                        null=True,
                        verbose_name="Redirect URL",
                    ),
                ),
                (
                    "is_active",
                    models.BooleanField(
                        db_index=True,
                        default=True,
                        help_text="Whether the QR code is active and scannable",
                        verbose_name="Is active",
                    ),
                ),
                (
                    "expires_at",
                    models.DateTimeField(
                        blank=True,
                        help_text="Optional expiration date for the QR code",
                        null=True,
                        verbose_name="Expires at",
                    ),
                ),
                (
                    "scan_count",
                    models.PositiveIntegerField(
                        default=0,
                        help_text="Total number of scans (cached counter)",
                        verbose_name="Scan count",
                    ),
                ),
                (
                    "unique_scan_count",
                    models.PositiveIntegerField(
                        default=0,
                        help_text="Number of unique device scans (cached counter)",
                        verbose_name="Unique scan count",
                    ),
                ),
                (
                    "last_scanned_at",
                    models.DateTimeField(
                        blank=True,
                        help_text="Timestamp of the most recent scan",
                        null=True,
                        verbose_name="Last scanned at",
                    ),
                ),
                (
                    "settings",
                    models.JSONField(
                        blank=True,
                        default=dict,
                        help_text="QR code-specific settings (JSON)",
                        verbose_name="Settings",
                    ),
                ),
                (
                    "metadata",
                    models.JSONField(
                        blank=True,
                        default=dict,
                        help_text="Custom metadata (campaign info, tracking params, etc.)",
                        verbose_name="Metadata",
                    ),
                ),
                (
                    "organization",
                    models.ForeignKey(
                        help_text="Organization this QR code belongs to",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="qr_codes",
                        to="core.organization",
                        verbose_name="Organization",
                    ),
                ),
                (
                    "branch",
                    models.ForeignKey(
                        blank=True,
                        help_text="Branch this QR code belongs to (optional for single-location)",
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="qr_codes",
                        to="core.branch",
                        verbose_name="Branch",
                    ),
                ),
                (
                    "menu",
                    models.ForeignKey(
                        blank=True,
                        help_text="Menu this QR code links to (for MENU type)",
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="qr_codes",
                        to="menu.menu",
                        verbose_name="Menu",
                    ),
                ),
                (
                    "table",
                    models.ForeignKey(
                        blank=True,
                        help_text="Table this QR code is associated with (for TABLE type)",
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="qr_codes",
                        to="orders.table",
                        verbose_name="Table",
                    ),
                ),
            ],
            options={
                "verbose_name": "QR Code",
                "verbose_name_plural": "QR Codes",
                "db_table": "qr_codes",
                "ordering": ["-created_at"],
            },
        ),
        migrations.AddConstraint(
            model_name="qrcode",
            constraint=models.UniqueConstraint(
                fields=["organization", "code"], name="qrcode_org_code_uniq"
            ),
        ),
        migrations.AddIndex(
            model_name="qrcode",
            index=models.Index(
                fields=["organization", "type"], name="qrcode_org_type_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="qrcode",
            index=models.Index(
                fields=["organization", "is_active"], name="qrcode_org_active_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="qrcode",
            index=models.Index(
                fields=["organization", "deleted_at"], name="qrcode_org_deleted_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="qrcode",
            index=models.Index(
                fields=["organization", "branch"], name="qrcode_org_branch_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="qrcode",
            index=models.Index(
                fields=["organization", "menu"], name="qrcode_org_menu_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="qrcode",
            index=models.Index(
                fields=["organization", "table"], name="qrcode_org_table_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="qrcode",
            index=models.Index(
                fields=["organization", "expires_at"], name="qrcode_org_expires_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="qrcode",
            index=models.Index(fields=["code"], name="qrcode_code_idx"),
        ),
        # 4. QRScan model (QR code scan tracking for analytics)
        # Note: QRScan does NOT have soft delete (analytics data is append-only)
        migrations.CreateModel(
            name="QRScan",
            fields=[
                (
                    "created_at",
                    models.DateTimeField(
                        auto_now_add=True,
                        help_text="Timestamp when record was created",
                        verbose_name="Created at",
                    ),
                ),
                (
                    "updated_at",
                    models.DateTimeField(
                        auto_now=True,
                        help_text="Timestamp when record was last updated",
                        verbose_name="Updated at",
                    ),
                ),
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        help_text="Unique identifier (UUID)",
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "scanned_at",
                    models.DateTimeField(
                        auto_now_add=True,
                        db_index=True,
                        help_text="Timestamp when the scan occurred",
                        verbose_name="Scanned at",
                    ),
                ),
                (
                    "ip_address",
                    models.GenericIPAddressField(
                        blank=True,
                        help_text="IP address of the scanner",
                        null=True,
                        verbose_name="IP address",
                    ),
                ),
                (
                    "user_agent",
                    models.TextField(
                        blank=True,
                        help_text="Full user agent string",
                        null=True,
                        verbose_name="User agent",
                    ),
                ),
                (
                    "session_id",
                    models.CharField(
                        blank=True,
                        db_index=True,
                        help_text="Session identifier for tracking unique visits",
                        max_length=255,
                        null=True,
                        verbose_name="Session ID",
                    ),
                ),
                (
                    "device_type",
                    models.CharField(
                        blank=True,
                        help_text="Device type (mobile, tablet, desktop)",
                        max_length=20,
                        null=True,
                        verbose_name="Device type",
                    ),
                ),
                (
                    "browser",
                    models.CharField(
                        blank=True,
                        help_text="Browser name (e.g., Chrome, Safari, Firefox)",
                        max_length=100,
                        null=True,
                        verbose_name="Browser",
                    ),
                ),
                (
                    "os",
                    models.CharField(
                        blank=True,
                        help_text="Operating system (e.g., iOS, Android, Windows)",
                        max_length=100,
                        null=True,
                        verbose_name="Operating system",
                    ),
                ),
                (
                    "country",
                    models.CharField(
                        blank=True,
                        help_text="Two-letter country code (ISO 3166-1 alpha-2)",
                        max_length=2,
                        null=True,
                        verbose_name="Country",
                    ),
                ),
                (
                    "city",
                    models.CharField(
                        blank=True,
                        help_text="City from IP geolocation",
                        max_length=100,
                        null=True,
                        verbose_name="City",
                    ),
                ),
                (
                    "region",
                    models.CharField(
                        blank=True,
                        help_text="Region/state from IP geolocation",
                        max_length=100,
                        null=True,
                        verbose_name="Region",
                    ),
                ),
                (
                    "latitude",
                    models.DecimalField(
                        blank=True,
                        decimal_places=6,
                        help_text="Latitude coordinate from geolocation",
                        max_digits=9,
                        null=True,
                        verbose_name="Latitude",
                    ),
                ),
                (
                    "longitude",
                    models.DecimalField(
                        blank=True,
                        decimal_places=6,
                        help_text="Longitude coordinate from geolocation",
                        max_digits=9,
                        null=True,
                        verbose_name="Longitude",
                    ),
                ),
                (
                    "referer",
                    models.URLField(
                        blank=True,
                        help_text="HTTP referer header",
                        max_length=1000,
                        null=True,
                        verbose_name="Referer",
                    ),
                ),
                (
                    "is_unique",
                    models.BooleanField(
                        default=True,
                        help_text="Whether this was a unique visit (first from this device/session)",
                        verbose_name="Is unique",
                    ),
                ),
                (
                    "metadata",
                    models.JSONField(
                        blank=True,
                        default=dict,
                        help_text="Additional tracking data (UTM params, custom fields, etc.)",
                        verbose_name="Metadata",
                    ),
                ),
                (
                    "qr_code",
                    models.ForeignKey(
                        help_text="QR code that was scanned",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="scans",
                        to="orders.qrcode",
                        verbose_name="QR Code",
                    ),
                ),
                (
                    "organization",
                    models.ForeignKey(
                        help_text="Organization this scan belongs to (denormalized)",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="qr_scans",
                        to="core.organization",
                        verbose_name="Organization",
                    ),
                ),
            ],
            options={
                "verbose_name": "QR Scan",
                "verbose_name_plural": "QR Scans",
                "db_table": "qr_scans",
                "ordering": ["-scanned_at"],
            },
        ),
        migrations.AddIndex(
            model_name="qrscan",
            index=models.Index(
                fields=["organization", "scanned_at"], name="qrscan_org_scanned_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="qrscan",
            index=models.Index(
                fields=["organization", "qr_code"], name="qrscan_org_qrcode_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="qrscan",
            index=models.Index(
                fields=["qr_code", "scanned_at"], name="qrscan_qrcode_scanned_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="qrscan",
            index=models.Index(
                fields=["organization", "device_type"], name="qrscan_org_device_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="qrscan",
            index=models.Index(
                fields=["organization", "country"], name="qrscan_org_country_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="qrscan",
            index=models.Index(fields=["ip_address"], name="qrscan_ip_idx"),
        ),
        migrations.AddIndex(
            model_name="qrscan",
            index=models.Index(fields=["session_id"], name="qrscan_session_idx"),
        ),
        # 5. Order model (customer orders with transaction details)
        migrations.CreateModel(
            name="Order",
            fields=[
                (
                    "created_at",
                    models.DateTimeField(
                        auto_now_add=True,
                        help_text="Timestamp when record was created",
                        verbose_name="Created at",
                    ),
                ),
                (
                    "updated_at",
                    models.DateTimeField(
                        auto_now=True,
                        help_text="Timestamp when record was last updated",
                        verbose_name="Updated at",
                    ),
                ),
                (
                    "deleted_at",
                    models.DateTimeField(
                        blank=True,
                        db_index=True,
                        help_text="Timestamp when record was soft-deleted (null = active)",
                        null=True,
                        verbose_name="Deleted at",
                    ),
                ),
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        help_text="Unique identifier (UUID)",
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "order_number",
                    models.CharField(
                        help_text="Human-readable order number (e.g., ORD-2024-0001)",
                        max_length=50,
                        verbose_name="Order number",
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("PENDING", "Pending"),
                            ("CONFIRMED", "Confirmed"),
                            ("PREPARING", "Preparing"),
                            ("READY", "Ready"),
                            ("DELIVERED", "Delivered"),
                            ("COMPLETED", "Completed"),
                            ("CANCELLED", "Cancelled"),
                        ],
                        db_index=True,
                        default="PENDING",
                        help_text="Current order status",
                        max_length=20,
                        verbose_name="Status",
                    ),
                ),
                (
                    "type",
                    models.CharField(
                        choices=[
                            ("DINE_IN", "Dine In"),
                            ("TAKEAWAY", "Takeaway"),
                            ("DELIVERY", "Delivery"),
                        ],
                        db_index=True,
                        default="DINE_IN",
                        help_text="Order type (dine-in, takeaway, delivery)",
                        max_length=20,
                        verbose_name="Type",
                    ),
                ),
                (
                    "payment_status",
                    models.CharField(
                        choices=[
                            ("PENDING", "Pending"),
                            ("PARTIAL", "Partial"),
                            ("PAID", "Paid"),
                            ("REFUNDED", "Refunded"),
                            ("FAILED", "Failed"),
                        ],
                        db_index=True,
                        default="PENDING",
                        help_text="Current payment status",
                        max_length=20,
                        verbose_name="Payment status",
                    ),
                ),
                (
                    "payment_method",
                    models.CharField(
                        blank=True,
                        choices=[
                            ("CASH", "Cash"),
                            ("CREDIT_CARD", "Credit Card"),
                            ("DEBIT_CARD", "Debit Card"),
                            ("ONLINE", "Online"),
                            ("WALLET", "Wallet"),
                            ("OTHER", "Other"),
                        ],
                        help_text="Payment method used",
                        max_length=20,
                        null=True,
                        verbose_name="Payment method",
                    ),
                ),
                (
                    "subtotal",
                    models.DecimalField(
                        decimal_places=2,
                        default=Decimal("0"),
                        help_text="Sum of all items before tax and discount",
                        max_digits=10,
                        verbose_name="Subtotal",
                    ),
                ),
                (
                    "tax_amount",
                    models.DecimalField(
                        decimal_places=2,
                        default=Decimal("0"),
                        help_text="Total tax amount",
                        max_digits=10,
                        verbose_name="Tax amount",
                    ),
                ),
                (
                    "discount_amount",
                    models.DecimalField(
                        decimal_places=2,
                        default=Decimal("0"),
                        help_text="Total discount applied",
                        max_digits=10,
                        verbose_name="Discount amount",
                    ),
                ),
                (
                    "tip_amount",
                    models.DecimalField(
                        decimal_places=2,
                        default=Decimal("0"),
                        help_text="Tip/gratuity amount",
                        max_digits=10,
                        verbose_name="Tip amount",
                    ),
                ),
                (
                    "total_amount",
                    models.DecimalField(
                        decimal_places=2,
                        default=Decimal("0"),
                        help_text="Final total (subtotal + tax - discount + tip)",
                        max_digits=10,
                        verbose_name="Total amount",
                    ),
                ),
                (
                    "currency",
                    models.CharField(
                        default="TRY",
                        help_text="Currency code (ISO 4217)",
                        max_length=3,
                        verbose_name="Currency",
                    ),
                ),
                (
                    "guest_count",
                    models.PositiveSmallIntegerField(
                        default=1,
                        help_text="Number of guests (for dine-in orders)",
                        verbose_name="Guest count",
                    ),
                ),
                (
                    "notes",
                    models.TextField(
                        blank=True,
                        help_text="Staff/kitchen notes about the order",
                        null=True,
                        verbose_name="Notes",
                    ),
                ),
                (
                    "special_instructions",
                    models.TextField(
                        blank=True,
                        help_text="Customer special instructions or requests",
                        null=True,
                        verbose_name="Special instructions",
                    ),
                ),
                (
                    "customer_info",
                    models.JSONField(
                        blank=True,
                        default=dict,
                        help_text="Guest customer details: name, phone, email",
                        verbose_name="Customer info",
                    ),
                ),
                (
                    "delivery_address",
                    models.JSONField(
                        blank=True,
                        default=dict,
                        help_text="Delivery address details: street, city, postal_code, etc.",
                        verbose_name="Delivery address",
                    ),
                ),
                (
                    "placed_at",
                    models.DateTimeField(
                        blank=True,
                        help_text="Timestamp when order was placed",
                        null=True,
                        verbose_name="Placed at",
                    ),
                ),
                (
                    "confirmed_at",
                    models.DateTimeField(
                        blank=True,
                        help_text="Timestamp when order was confirmed by staff",
                        null=True,
                        verbose_name="Confirmed at",
                    ),
                ),
                (
                    "preparing_at",
                    models.DateTimeField(
                        blank=True,
                        help_text="Timestamp when order preparation started",
                        null=True,
                        verbose_name="Preparing at",
                    ),
                ),
                (
                    "ready_at",
                    models.DateTimeField(
                        blank=True,
                        help_text="Timestamp when order was ready",
                        null=True,
                        verbose_name="Ready at",
                    ),
                ),
                (
                    "delivered_at",
                    models.DateTimeField(
                        blank=True,
                        help_text="Timestamp when order was delivered to customer",
                        null=True,
                        verbose_name="Delivered at",
                    ),
                ),
                (
                    "completed_at",
                    models.DateTimeField(
                        blank=True,
                        help_text="Timestamp when order was completed",
                        null=True,
                        verbose_name="Completed at",
                    ),
                ),
                (
                    "cancelled_at",
                    models.DateTimeField(
                        blank=True,
                        help_text="Timestamp when order was cancelled",
                        null=True,
                        verbose_name="Cancelled at",
                    ),
                ),
                (
                    "cancel_reason",
                    models.TextField(
                        blank=True,
                        help_text="Reason for order cancellation",
                        null=True,
                        verbose_name="Cancel reason",
                    ),
                ),
                (
                    "metadata",
                    models.JSONField(
                        blank=True,
                        default=dict,
                        help_text="Additional order data (source, promo codes, etc.)",
                        verbose_name="Metadata",
                    ),
                ),
                (
                    "organization",
                    models.ForeignKey(
                        help_text="Organization this order belongs to",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="orders",
                        to="core.organization",
                        verbose_name="Organization",
                    ),
                ),
                (
                    "branch",
                    models.ForeignKey(
                        blank=True,
                        help_text="Branch this order belongs to (optional for single-location)",
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="orders",
                        to="core.branch",
                        verbose_name="Branch",
                    ),
                ),
                (
                    "table",
                    models.ForeignKey(
                        blank=True,
                        help_text="Table associated with this order (for dine-in)",
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="orders",
                        to="orders.table",
                        verbose_name="Table",
                    ),
                ),
                (
                    "placed_by",
                    models.ForeignKey(
                        blank=True,
                        help_text="Staff member who placed the order",
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="placed_orders",
                        to="core.user",
                        verbose_name="Placed by",
                    ),
                ),
                (
                    "assigned_to",
                    models.ForeignKey(
                        blank=True,
                        help_text="Staff member assigned to handle this order",
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="assigned_orders",
                        to="core.user",
                        verbose_name="Assigned to",
                    ),
                ),
            ],
            options={
                "verbose_name": "Order",
                "verbose_name_plural": "Orders",
                "db_table": "orders",
                "ordering": ["-created_at"],
            },
        ),
        migrations.AddConstraint(
            model_name="order",
            constraint=models.UniqueConstraint(
                fields=["organization", "order_number"], name="order_org_number_uniq"
            ),
        ),
        migrations.AddIndex(
            model_name="order",
            index=models.Index(
                fields=["organization", "status"], name="order_org_status_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="order",
            index=models.Index(
                fields=["organization", "type"], name="order_org_type_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="order",
            index=models.Index(
                fields=["organization", "payment_status"],
                name="order_org_pay_status_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="order",
            index=models.Index(
                fields=["organization", "deleted_at"], name="order_org_deleted_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="order",
            index=models.Index(
                fields=["organization", "branch"], name="order_org_branch_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="order",
            index=models.Index(
                fields=["organization", "table"], name="order_org_table_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="order",
            index=models.Index(
                fields=["organization", "placed_at"], name="order_org_placed_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="order",
            index=models.Index(
                fields=["organization", "order_number"], name="order_org_number_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="order",
            index=models.Index(
                fields=["table", "status"], name="order_table_status_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="order",
            index=models.Index(
                fields=["assigned_to", "status"], name="order_assigned_status_idx"
            ),
        ),
        # 6. OrderItem model (individual line items within orders)
        migrations.CreateModel(
            name="OrderItem",
            fields=[
                (
                    "created_at",
                    models.DateTimeField(
                        auto_now_add=True,
                        help_text="Timestamp when record was created",
                        verbose_name="Created at",
                    ),
                ),
                (
                    "updated_at",
                    models.DateTimeField(
                        auto_now=True,
                        help_text="Timestamp when record was last updated",
                        verbose_name="Updated at",
                    ),
                ),
                (
                    "deleted_at",
                    models.DateTimeField(
                        blank=True,
                        db_index=True,
                        help_text="Timestamp when record was soft-deleted (null = active)",
                        null=True,
                        verbose_name="Deleted at",
                    ),
                ),
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        help_text="Unique identifier (UUID)",
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "quantity",
                    models.PositiveIntegerField(
                        default=1,
                        help_text="Number of items ordered",
                        verbose_name="Quantity",
                    ),
                ),
                (
                    "unit_price",
                    models.DecimalField(
                        decimal_places=2,
                        help_text="Price per unit at time of order (captured, not referenced)",
                        max_digits=10,
                        verbose_name="Unit price",
                    ),
                ),
                (
                    "total_price",
                    models.DecimalField(
                        decimal_places=2,
                        help_text="Total price (unit_price * quantity + modifier costs)",
                        max_digits=10,
                        verbose_name="Total price",
                    ),
                ),
                (
                    "currency",
                    models.CharField(
                        default="TRY",
                        help_text="Currency code (ISO 4217)",
                        max_length=3,
                        verbose_name="Currency",
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("PENDING", "Pending"),
                            ("PREPARING", "Preparing"),
                            ("READY", "Ready"),
                            ("DELIVERED", "Delivered"),
                            ("CANCELLED", "Cancelled"),
                        ],
                        db_index=True,
                        default="PENDING",
                        help_text="Current item status",
                        max_length=20,
                        verbose_name="Status",
                    ),
                ),
                (
                    "modifiers",
                    models.JSONField(
                        blank=True,
                        default=list,
                        help_text="JSON snapshot of selected modifiers with prices at order time",
                        verbose_name="Modifiers",
                    ),
                ),
                (
                    "notes",
                    models.TextField(
                        blank=True,
                        help_text="Customer notes/special instructions for this item",
                        null=True,
                        verbose_name="Notes",
                    ),
                ),
                (
                    "is_gift",
                    models.BooleanField(
                        default=False,
                        help_text="Whether this item is a complimentary gift (zero charge)",
                        verbose_name="Is gift",
                    ),
                ),
                (
                    "prepared_at",
                    models.DateTimeField(
                        blank=True,
                        help_text="Timestamp when item preparation completed",
                        null=True,
                        verbose_name="Prepared at",
                    ),
                ),
                (
                    "delivered_at",
                    models.DateTimeField(
                        blank=True,
                        help_text="Timestamp when item was delivered to customer",
                        null=True,
                        verbose_name="Delivered at",
                    ),
                ),
                (
                    "cancelled_at",
                    models.DateTimeField(
                        blank=True,
                        help_text="Timestamp when item was cancelled",
                        null=True,
                        verbose_name="Cancelled at",
                    ),
                ),
                (
                    "cancel_reason",
                    models.TextField(
                        blank=True,
                        help_text="Reason for item cancellation",
                        null=True,
                        verbose_name="Cancel reason",
                    ),
                ),
                (
                    "metadata",
                    models.JSONField(
                        blank=True,
                        default=dict,
                        help_text="Additional item data (JSON)",
                        verbose_name="Metadata",
                    ),
                ),
                (
                    "order",
                    models.ForeignKey(
                        help_text="Order this item belongs to",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="items",
                        to="orders.order",
                        verbose_name="Order",
                    ),
                ),
                (
                    "product",
                    models.ForeignKey(
                        blank=True,
                        help_text="Product ordered (reference, may be soft-deleted)",
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="order_items",
                        to="menu.product",
                        verbose_name="Product",
                    ),
                ),
                (
                    "variant",
                    models.ForeignKey(
                        blank=True,
                        help_text="Product variant selected (e.g., Large, Small)",
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="order_items",
                        to="menu.productvariant",
                        verbose_name="Variant",
                    ),
                ),
            ],
            options={
                "verbose_name": "Order Item",
                "verbose_name_plural": "Order Items",
                "db_table": "order_items",
                "ordering": ["created_at"],
            },
        ),
        migrations.AddIndex(
            model_name="orderitem",
            index=models.Index(
                fields=["order", "status"], name="orderitem_order_status_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="orderitem",
            index=models.Index(
                fields=["order", "deleted_at"], name="orderitem_order_deleted_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="orderitem",
            index=models.Index(fields=["product"], name="orderitem_product_idx"),
        ),
        migrations.AddIndex(
            model_name="orderitem",
            index=models.Index(fields=["status"], name="orderitem_status_idx"),
        ),
        # 7. ServiceRequest model (waiter call/service requests from tables)
        migrations.CreateModel(
            name="ServiceRequest",
            fields=[
                (
                    "created_at",
                    models.DateTimeField(
                        auto_now_add=True,
                        help_text="Timestamp when record was created",
                        verbose_name="Created at",
                    ),
                ),
                (
                    "updated_at",
                    models.DateTimeField(
                        auto_now=True,
                        help_text="Timestamp when record was last updated",
                        verbose_name="Updated at",
                    ),
                ),
                (
                    "deleted_at",
                    models.DateTimeField(
                        blank=True,
                        db_index=True,
                        help_text="Timestamp when record was soft-deleted (null = active)",
                        null=True,
                        verbose_name="Deleted at",
                    ),
                ),
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        help_text="Unique identifier (UUID)",
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "type",
                    models.CharField(
                        choices=[
                            ("WAITER_CALL", "Waiter Call"),
                            ("BILL_REQUEST", "Bill Request"),
                            ("HELP", "Help"),
                            ("OTHER", "Other"),
                        ],
                        db_index=True,
                        default="WAITER_CALL",
                        help_text="Type of service request",
                        max_length=20,
                        verbose_name="Type",
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("PENDING", "Pending"),
                            ("IN_PROGRESS", "In Progress"),
                            ("COMPLETED", "Completed"),
                            ("CANCELLED", "Cancelled"),
                        ],
                        db_index=True,
                        default="PENDING",
                        help_text="Current request status",
                        max_length=20,
                        verbose_name="Status",
                    ),
                ),
                (
                    "message",
                    models.TextField(
                        blank=True,
                        help_text="Optional customer message or notes",
                        null=True,
                        verbose_name="Message",
                    ),
                ),
                (
                    "priority",
                    models.PositiveSmallIntegerField(
                        default=3,
                        help_text="Priority level 1-5 (1 is highest priority)",
                        verbose_name="Priority",
                    ),
                ),
                (
                    "acknowledged_at",
                    models.DateTimeField(
                        blank=True,
                        help_text="Timestamp when request was acknowledged by staff",
                        null=True,
                        verbose_name="Acknowledged at",
                    ),
                ),
                (
                    "completed_at",
                    models.DateTimeField(
                        blank=True,
                        help_text="Timestamp when request was completed",
                        null=True,
                        verbose_name="Completed at",
                    ),
                ),
                (
                    "cancelled_at",
                    models.DateTimeField(
                        blank=True,
                        help_text="Timestamp when request was cancelled",
                        null=True,
                        verbose_name="Cancelled at",
                    ),
                ),
                (
                    "cancel_reason",
                    models.TextField(
                        blank=True,
                        help_text="Reason for request cancellation",
                        null=True,
                        verbose_name="Cancel reason",
                    ),
                ),
                (
                    "response_time_seconds",
                    models.PositiveIntegerField(
                        blank=True,
                        help_text="Time to first response in seconds",
                        null=True,
                        verbose_name="Response time",
                    ),
                ),
                (
                    "metadata",
                    models.JSONField(
                        blank=True,
                        default=dict,
                        help_text="Additional request data (JSON)",
                        verbose_name="Metadata",
                    ),
                ),
                (
                    "organization",
                    models.ForeignKey(
                        help_text="Organization this request belongs to",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="service_requests",
                        to="core.organization",
                        verbose_name="Organization",
                    ),
                ),
                (
                    "branch",
                    models.ForeignKey(
                        blank=True,
                        help_text="Branch this request belongs to (optional for single-location)",
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="service_requests",
                        to="core.branch",
                        verbose_name="Branch",
                    ),
                ),
                (
                    "table",
                    models.ForeignKey(
                        help_text="Table making this request",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="service_requests",
                        to="orders.table",
                        verbose_name="Table",
                    ),
                ),
                (
                    "order",
                    models.ForeignKey(
                        blank=True,
                        help_text="Related order (if applicable)",
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="service_requests",
                        to="orders.order",
                        verbose_name="Order",
                    ),
                ),
                (
                    "assigned_to",
                    models.ForeignKey(
                        blank=True,
                        help_text="Staff member assigned to handle this request",
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="assigned_service_requests",
                        to="core.user",
                        verbose_name="Assigned to",
                    ),
                ),
            ],
            options={
                "verbose_name": "Service Request",
                "verbose_name_plural": "Service Requests",
                "db_table": "service_requests",
                "ordering": ["priority", "-created_at"],
            },
        ),
        migrations.AddIndex(
            model_name="servicerequest",
            index=models.Index(
                fields=["organization", "status"], name="svcreq_org_status_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="servicerequest",
            index=models.Index(
                fields=["organization", "type"], name="svcreq_org_type_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="servicerequest",
            index=models.Index(
                fields=["organization", "deleted_at"], name="svcreq_org_deleted_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="servicerequest",
            index=models.Index(
                fields=["organization", "branch"], name="svcreq_org_branch_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="servicerequest",
            index=models.Index(
                fields=["table", "status"], name="svcreq_table_status_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="servicerequest",
            index=models.Index(
                fields=["assigned_to", "status"], name="svcreq_assigned_status_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="servicerequest",
            index=models.Index(
                fields=["organization", "priority", "status"],
                name="svcreq_org_priority_idx",
            ),
        ),
    ]
