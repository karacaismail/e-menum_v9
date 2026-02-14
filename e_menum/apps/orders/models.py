"""
Django ORM models for the Orders application.

This module defines the order-related models for E-Menum:
- Zone: Table groupings/sections within a restaurant (e.g., Garden, Indoor, VIP)
- Table: Physical restaurant tables with status tracking
- QRCode: Generated QR codes for menus/tables with scan analytics
- QRScan: QR code scan tracking for analytics (device info, geolocation)
- Order: Customer orders with full transaction details and status workflow
- OrderItem: Individual line items within orders with modifiers and status tracking
- ServiceRequest: Waiter call/service requests from tables with priority system

Critical Rules:
- Every query MUST include organization_id for tenant isolation
- All entities use soft delete (deleted_at timestamp) except QRScan
- No physical deletions allowed (use soft_delete method)
- QRScan records are append-only for analytics integrity
"""

import uuid

from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.models import (
    Branch,
    Organization,
    SoftDeleteManager,
    SoftDeleteMixin,
    TimeStampedMixin,
)
from apps.menu.models import Menu
from apps.orders.choices import (
    OrderItemStatus,
    OrderStatus,
    OrderType,
    PaymentMethod,
    PaymentStatus,
    QRCodeType,
    ServiceRequestStatus,
    ServiceRequestType,
    TableStatus,
)


class Zone(TimeStampedMixin, SoftDeleteMixin, models.Model):
    """
    Zone model - represents table groupings/sections within a restaurant.

    Zones help organize tables into logical areas like "Garden", "Indoor",
    "VIP Section", "Terrace", "Bar Area", etc. This allows staff to manage
    sections and customers to choose preferred seating areas.

    Critical Rules:
    - EVERY query MUST filter by organization (multi-tenant isolation)
    - Use soft_delete() - never call delete() directly
    - Zone slugs must be unique within an organization

    Attributes:
        id: UUID primary key (ensures global uniqueness)
        organization: FK to parent Organization (tenant isolation)
        branch: Optional FK to Branch for multi-location support
        name: Display name of the zone (e.g., "Garden", "VIP Section")
        slug: URL-friendly identifier (unique within organization)
        description: Optional description of the zone
        color: Hex color code for visual identification in UI
        icon: Optional icon name or URL for zone representation
        capacity: Maximum number of guests the zone can accommodate
        is_active: Whether the zone is available for seating
        is_smoking_allowed: Whether smoking is permitted in the zone
        is_outdoor: Whether the zone is outdoors
        is_reservable: Whether tables in this zone can be reserved
        sort_order: Display order for zones
        settings: JSON field for additional zone-specific settings

    Usage:
        # Create a zone
        garden_zone = Zone.objects.create(
            organization=org,
            name="Garden",
            slug="garden",
            description="Beautiful outdoor seating area",
            color="#22C55E",
            capacity=40,
            is_outdoor=True,
            is_smoking_allowed=True
        )

        # Query zones for organization (ALWAYS filter by organization!)
        zones = Zone.objects.filter(organization=org)

        # Get active zones
        active_zones = Zone.objects.filter(organization=org, is_active=True)

        # Get outdoor zones
        outdoor_zones = Zone.objects.filter(
            organization=org,
            is_outdoor=True,
            is_active=True
        )

        # Soft delete zone (NEVER use delete())
        zone.soft_delete()
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name=_('ID'),
        help_text=_('Unique identifier (UUID)')
    )

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='zones',
        verbose_name=_('Organization'),
        help_text=_('Organization this zone belongs to')
    )

    branch = models.ForeignKey(
        Branch,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='zones',
        verbose_name=_('Branch'),
        help_text=_('Branch this zone belongs to (optional for single-location)')
    )

    name = models.CharField(
        max_length=100,
        verbose_name=_('Name'),
        help_text=_('Display name of the zone (e.g., Garden, VIP Section)')
    )

    slug = models.SlugField(
        max_length=100,
        verbose_name=_('Slug'),
        help_text=_('URL-friendly identifier (unique within organization)')
    )

    description = models.TextField(
        blank=True,
        null=True,
        verbose_name=_('Description'),
        help_text=_('Optional description of the zone and its characteristics')
    )

    # Visual identification
    color = models.CharField(
        max_length=7,
        default='#3B82F6',
        verbose_name=_('Color'),
        help_text=_('Hex color code for visual identification (e.g., #3B82F6)')
    )

    icon = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name=_('Icon'),
        help_text=_('Icon name or URL for zone representation in UI')
    )

    # Capacity
    capacity = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name=_('Capacity'),
        help_text=_('Maximum number of guests the zone can accommodate')
    )

    # Status and characteristics
    is_active = models.BooleanField(
        default=True,
        db_index=True,
        verbose_name=_('Is active'),
        help_text=_('Whether the zone is available for seating')
    )

    is_smoking_allowed = models.BooleanField(
        default=False,
        verbose_name=_('Is smoking allowed'),
        help_text=_('Whether smoking is permitted in this zone')
    )

    is_outdoor = models.BooleanField(
        default=False,
        verbose_name=_('Is outdoor'),
        help_text=_('Whether the zone is located outdoors')
    )

    is_reservable = models.BooleanField(
        default=True,
        verbose_name=_('Is reservable'),
        help_text=_('Whether tables in this zone can be reserved')
    )

    # Ordering
    sort_order = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Sort order'),
        help_text=_('Display order for zones (lower numbers appear first)')
    )

    # Additional settings
    settings = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_('Settings'),
        help_text=_('Zone-specific settings (JSON)')
    )

    # Managers
    objects = SoftDeleteManager()  # Default: excludes soft-deleted
    all_objects = models.Manager()  # Includes ALL records

    class Meta:
        db_table = 'zones'
        verbose_name = _('Zone')
        verbose_name_plural = _('Zones')
        ordering = ['sort_order', 'name']
        unique_together = [['organization', 'slug']]
        indexes = [
            models.Index(fields=['organization', 'is_active'], name='zone_org_active_idx'),
            models.Index(fields=['organization', 'deleted_at'], name='zone_org_deleted_idx'),
            models.Index(fields=['organization', 'branch'], name='zone_org_branch_idx'),
            models.Index(fields=['organization', 'sort_order'], name='zone_org_sort_idx'),
        ]

    def __str__(self) -> str:
        return f"{self.name} ({self.organization.name})"

    def __repr__(self) -> str:
        return f"<Zone(id={self.id}, name='{self.name}', org='{self.organization.name}')>"

    @property
    def is_available(self) -> bool:
        """Check if zone is active and not deleted."""
        return self.is_active and not self.is_deleted

    @property
    def table_count(self) -> int:
        """Return the number of active tables in this zone."""
        return self.tables.filter(deleted_at__isnull=True).count()

    @property
    def available_table_count(self) -> int:
        """Return the number of available tables in this zone."""
        return self.tables.filter(
            deleted_at__isnull=True,
            status=TableStatus.AVAILABLE
        ).count()

    @property
    def occupied_table_count(self) -> int:
        """Return the number of occupied tables in this zone."""
        return self.tables.filter(
            deleted_at__isnull=True,
            status=TableStatus.OCCUPIED
        ).count()

    def get_setting(self, key: str, default=None):
        """
        Get a value from zone settings.

        Args:
            key: The setting key to retrieve
            default: Default value if key not found

        Returns:
            The setting value or default
        """
        return self.settings.get(key, default)

    def set_setting(self, key: str, value) -> None:
        """
        Set a value in zone settings.

        Args:
            key: The setting key
            value: The value to set
        """
        self.settings[key] = value
        self.save(update_fields=['settings', 'updated_at'])

    def activate(self) -> None:
        """Activate the zone for seating."""
        self.is_active = True
        self.save(update_fields=['is_active', 'updated_at'])

    def deactivate(self) -> None:
        """Deactivate the zone (not available for seating)."""
        self.is_active = False
        self.save(update_fields=['is_active', 'updated_at'])

    def get_tables(self, status: str = None):
        """
        Get tables in this zone, optionally filtered by status.

        Args:
            status: Optional TableStatus value to filter by

        Returns:
            QuerySet of Table objects
        """
        qs = self.tables.filter(deleted_at__isnull=True)
        if status:
            qs = qs.filter(status=status)
        return qs.order_by('sort_order', 'name')


class Table(TimeStampedMixin, SoftDeleteMixin, models.Model):
    """
    Table model - represents physical restaurant tables.

    Tables are the basic seating units within zones. Each table has a status
    (available, occupied, reserved), capacity, and can be associated with
    QR codes for digital menu access.

    Critical Rules:
    - EVERY query MUST filter by organization (multi-tenant isolation)
    - Use soft_delete() - never call delete() directly
    - Table names/numbers should be unique within an organization

    Attributes:
        id: UUID primary key (ensures global uniqueness)
        organization: FK to parent Organization (tenant isolation)
        zone: FK to parent Zone (table grouping)
        branch: Optional FK to Branch for multi-location support
        name: Display name/number of the table (e.g., "Table 1", "A-12")
        number: Optional numeric table number for ordering
        slug: URL-friendly identifier (unique within organization)
        capacity: Number of guests the table can seat
        min_capacity: Minimum number of guests for reservation
        status: Current table status (AVAILABLE, OCCUPIED, RESERVED)
        is_active: Whether the table is available for use
        is_vip: Whether this is a VIP/premium table
        position_x: X coordinate for floor plan visualization
        position_y: Y coordinate for floor plan visualization
        shape: Table shape for visualization (round, square, rectangle)
        sort_order: Display order within the zone
        notes: Staff notes about the table
        settings: JSON field for additional table-specific settings

    Usage:
        # Create a table
        table = Table.objects.create(
            organization=org,
            zone=garden_zone,
            name="Table 1",
            number=1,
            slug="table-1",
            capacity=4,
            status=TableStatus.AVAILABLE
        )

        # Query tables for organization (ALWAYS filter by organization!)
        tables = Table.objects.filter(organization=org)

        # Get available tables
        available = Table.objects.filter(
            organization=org,
            status=TableStatus.AVAILABLE
        )

        # Get tables in a zone
        zone_tables = Table.objects.filter(
            organization=org,
            zone=garden_zone
        )

        # Change table status
        table.set_status(TableStatus.OCCUPIED)

        # Soft delete table (NEVER use delete())
        table.soft_delete()
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name=_('ID'),
        help_text=_('Unique identifier (UUID)')
    )

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='tables',
        verbose_name=_('Organization'),
        help_text=_('Organization this table belongs to')
    )

    zone = models.ForeignKey(
        Zone,
        on_delete=models.CASCADE,
        related_name='tables',
        verbose_name=_('Zone'),
        help_text=_('Zone/section this table belongs to')
    )

    branch = models.ForeignKey(
        Branch,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='tables',
        verbose_name=_('Branch'),
        help_text=_('Branch this table belongs to (optional for single-location)')
    )

    # Identification
    name = models.CharField(
        max_length=50,
        verbose_name=_('Name'),
        help_text=_('Display name/number of the table (e.g., "Table 1", "A-12")')
    )

    number = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name=_('Number'),
        help_text=_('Numeric table number for ordering and quick reference')
    )

    slug = models.SlugField(
        max_length=50,
        verbose_name=_('Slug'),
        help_text=_('URL-friendly identifier (unique within organization)')
    )

    # Capacity
    capacity = models.PositiveSmallIntegerField(
        default=4,
        verbose_name=_('Capacity'),
        help_text=_('Maximum number of guests the table can seat')
    )

    min_capacity = models.PositiveSmallIntegerField(
        default=1,
        verbose_name=_('Minimum capacity'),
        help_text=_('Minimum number of guests required for reservation')
    )

    # Status
    status = models.CharField(
        max_length=20,
        choices=TableStatus.choices,
        default=TableStatus.AVAILABLE,
        db_index=True,
        verbose_name=_('Status'),
        help_text=_('Current table status (available, occupied, reserved)')
    )

    is_active = models.BooleanField(
        default=True,
        db_index=True,
        verbose_name=_('Is active'),
        help_text=_('Whether the table is available for use (can be disabled for maintenance)')
    )

    is_vip = models.BooleanField(
        default=False,
        verbose_name=_('Is VIP'),
        help_text=_('Whether this is a VIP/premium table')
    )

    # Floor plan positioning (for visual table layout)
    position_x = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name=_('Position X'),
        help_text=_('X coordinate for floor plan visualization')
    )

    position_y = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name=_('Position Y'),
        help_text=_('Y coordinate for floor plan visualization')
    )

    shape = models.CharField(
        max_length=20,
        default='rectangle',
        verbose_name=_('Shape'),
        help_text=_('Table shape for visualization (round, square, rectangle)')
    )

    # Ordering
    sort_order = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Sort order'),
        help_text=_('Display order within the zone (lower numbers appear first)')
    )

    # Notes
    notes = models.TextField(
        blank=True,
        null=True,
        verbose_name=_('Notes'),
        help_text=_('Staff notes about the table (e.g., "near window", "wheelchair accessible")')
    )

    # Additional settings
    settings = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_('Settings'),
        help_text=_('Table-specific settings (JSON)')
    )

    # Managers
    objects = SoftDeleteManager()  # Default: excludes soft-deleted
    all_objects = models.Manager()  # Includes ALL records

    class Meta:
        db_table = 'tables'
        verbose_name = _('Table')
        verbose_name_plural = _('Tables')
        ordering = ['zone', 'sort_order', 'number', 'name']
        unique_together = [['organization', 'slug']]
        indexes = [
            models.Index(fields=['organization', 'status'], name='table_org_status_idx'),
            models.Index(fields=['organization', 'is_active'], name='table_org_active_idx'),
            models.Index(fields=['organization', 'deleted_at'], name='table_org_deleted_idx'),
            models.Index(fields=['organization', 'zone'], name='table_org_zone_idx'),
            models.Index(fields=['organization', 'branch'], name='table_org_branch_idx'),
            models.Index(fields=['zone', 'status'], name='table_zone_status_idx'),
            models.Index(fields=['zone', 'sort_order'], name='table_zone_sort_idx'),
            models.Index(fields=['organization', 'number'], name='table_org_number_idx'),
        ]

    def __str__(self) -> str:
        return f"{self.name} ({self.zone.name})"

    def __repr__(self) -> str:
        return f"<Table(id={self.id}, name='{self.name}', zone='{self.zone.name}', status={self.status})>"

    @property
    def is_available(self) -> bool:
        """Check if table is available for seating."""
        return (
            self.status == TableStatus.AVAILABLE
            and self.is_active
            and not self.is_deleted
        )

    @property
    def is_occupied(self) -> bool:
        """Check if table is currently occupied."""
        return self.status == TableStatus.OCCUPIED

    @property
    def is_reserved(self) -> bool:
        """Check if table is reserved."""
        return self.status == TableStatus.RESERVED

    @property
    def is_usable(self) -> bool:
        """Check if table can be used (active and not deleted)."""
        return self.is_active and not self.is_deleted

    @property
    def display_name(self) -> str:
        """Return display name with zone context."""
        return f"{self.zone.name} - {self.name}"

    def set_status(self, status: str) -> None:
        """
        Set the table status.

        Args:
            status: TableStatus value (AVAILABLE, OCCUPIED, RESERVED)
        """
        if status not in TableStatus.values:
            raise ValueError(f"Invalid status: {status}. Must be one of {TableStatus.values}")
        self.status = status
        self.save(update_fields=['status', 'updated_at'])

    def set_available(self) -> None:
        """Set the table as available for seating."""
        self.set_status(TableStatus.AVAILABLE)

    def set_occupied(self) -> None:
        """Set the table as occupied by guests."""
        self.set_status(TableStatus.OCCUPIED)

    def set_reserved(self) -> None:
        """Set the table as reserved for a future booking."""
        self.set_status(TableStatus.RESERVED)

    def activate(self) -> None:
        """Activate the table for use."""
        self.is_active = True
        self.save(update_fields=['is_active', 'updated_at'])

    def deactivate(self) -> None:
        """Deactivate the table (not available for use)."""
        self.is_active = False
        self.save(update_fields=['is_active', 'updated_at'])

    def update_position(self, x: int, y: int) -> None:
        """
        Update the table position for floor plan.

        Args:
            x: X coordinate
            y: Y coordinate
        """
        self.position_x = x
        self.position_y = y
        self.save(update_fields=['position_x', 'position_y', 'updated_at'])

    def get_setting(self, key: str, default=None):
        """
        Get a value from table settings.

        Args:
            key: The setting key to retrieve
            default: Default value if key not found

        Returns:
            The setting value or default
        """
        return self.settings.get(key, default)

    def set_setting(self, key: str, value) -> None:
        """
        Set a value in table settings.

        Args:
            key: The setting key
            value: The value to set
        """
        self.settings[key] = value
        self.save(update_fields=['settings', 'updated_at'])

    def can_seat(self, guest_count: int) -> bool:
        """
        Check if the table can accommodate the given number of guests.

        Args:
            guest_count: Number of guests to seat

        Returns:
            True if table can accommodate the guests
        """
        return self.min_capacity <= guest_count <= self.capacity

    def move_to_zone(self, new_zone: Zone) -> None:
        """
        Move this table to a different zone.

        Args:
            new_zone: The zone to move the table to

        Raises:
            ValueError: If the new zone belongs to a different organization
        """
        if new_zone.organization_id != self.organization_id:
            raise ValueError("Cannot move table to a zone in a different organization")
        self.zone = new_zone
        self.save(update_fields=['zone', 'updated_at'])


class QRCode(TimeStampedMixin, SoftDeleteMixin, models.Model):
    """
    QRCode model - generated QR codes for menus and tables.

    QR codes are the primary way customers access digital menus. Each QR code
    can be associated with a specific menu (MENU type), table (TABLE type),
    or used for marketing campaigns (CAMPAIGN type). QR codes track scan
    analytics through the related QRScan model.

    Critical Rules:
    - EVERY query MUST filter by organization (multi-tenant isolation)
    - Use soft_delete() - never call delete() directly
    - QR code slugs/codes must be unique within an organization

    Attributes:
        id: UUID primary key (ensures global uniqueness)
        organization: FK to parent Organization (tenant isolation)
        branch: Optional FK to Branch for multi-location support
        menu: Optional FK to Menu (for MENU type QR codes)
        table: Optional FK to Table (for TABLE type QR codes)
        type: Type of QR code (MENU, TABLE, CAMPAIGN)
        code: Unique code/slug for the QR code URL
        name: Display name for the QR code
        description: Optional description of the QR code purpose
        short_url: Generated short URL for QR scanning
        qr_image_url: URL to the generated QR code image
        redirect_url: Custom redirect URL (overrides default behavior)
        is_active: Whether the QR code is active and scannable
        expires_at: Optional expiration date for the QR code
        scan_count: Cached counter for total scans (denormalized for performance)
        unique_scan_count: Cached counter for unique device scans
        last_scanned_at: Timestamp of the most recent scan
        settings: JSON field for additional QR code settings
        metadata: JSON field for custom metadata (campaign info, etc.)

    Usage:
        # Create a menu QR code
        menu_qr = QRCode.objects.create(
            organization=org,
            menu=main_menu,
            type=QRCodeType.MENU,
            code="menu-main",
            name="Main Menu QR"
        )

        # Create a table QR code
        table_qr = QRCode.objects.create(
            organization=org,
            table=table_5,
            type=QRCodeType.TABLE,
            code="table-5",
            name="Table 5 QR"
        )

        # Query QR codes for organization (ALWAYS filter by organization!)
        qr_codes = QRCode.objects.filter(organization=org)

        # Get active QR codes
        active_qrs = QRCode.objects.filter(
            organization=org,
            is_active=True
        )

        # Soft delete QR code (NEVER use delete())
        qr_code.soft_delete()
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name=_('ID'),
        help_text=_('Unique identifier (UUID)')
    )

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='qr_codes',
        verbose_name=_('Organization'),
        help_text=_('Organization this QR code belongs to')
    )

    branch = models.ForeignKey(
        Branch,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='qr_codes',
        verbose_name=_('Branch'),
        help_text=_('Branch this QR code belongs to (optional for single-location)')
    )

    # Linked entities (based on type)
    menu = models.ForeignKey(
        Menu,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='qr_codes',
        verbose_name=_('Menu'),
        help_text=_('Menu this QR code links to (for MENU type)')
    )

    table = models.ForeignKey(
        'Table',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='qr_codes',
        verbose_name=_('Table'),
        help_text=_('Table this QR code is associated with (for TABLE type)')
    )

    # QR code type and identification
    type = models.CharField(
        max_length=20,
        choices=QRCodeType.choices,
        default=QRCodeType.MENU,
        db_index=True,
        verbose_name=_('Type'),
        help_text=_('Type of QR code (MENU, TABLE, CAMPAIGN)')
    )

    code = models.CharField(
        max_length=100,
        verbose_name=_('Code'),
        help_text=_('Unique code/slug for the QR code URL (unique within organization)')
    )

    name = models.CharField(
        max_length=100,
        verbose_name=_('Name'),
        help_text=_('Display name for the QR code')
    )

    description = models.TextField(
        blank=True,
        null=True,
        verbose_name=_('Description'),
        help_text=_('Optional description of the QR code purpose')
    )

    # URLs
    short_url = models.URLField(
        blank=True,
        null=True,
        max_length=500,
        verbose_name=_('Short URL'),
        help_text=_('Generated short URL for QR scanning')
    )

    qr_image_url = models.URLField(
        blank=True,
        null=True,
        max_length=500,
        verbose_name=_('QR image URL'),
        help_text=_('URL to the generated QR code image')
    )

    redirect_url = models.URLField(
        blank=True,
        null=True,
        max_length=500,
        verbose_name=_('Redirect URL'),
        help_text=_('Custom redirect URL (overrides default behavior)')
    )

    # Status
    is_active = models.BooleanField(
        default=True,
        db_index=True,
        verbose_name=_('Is active'),
        help_text=_('Whether the QR code is active and scannable')
    )

    expires_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name=_('Expires at'),
        help_text=_('Optional expiration date for the QR code')
    )

    # Analytics (denormalized for performance)
    scan_count = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Scan count'),
        help_text=_('Total number of scans (cached counter)')
    )

    unique_scan_count = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Unique scan count'),
        help_text=_('Number of unique device scans (cached counter)')
    )

    last_scanned_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name=_('Last scanned at'),
        help_text=_('Timestamp of the most recent scan')
    )

    # Additional settings and metadata
    settings = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_('Settings'),
        help_text=_('QR code-specific settings (JSON)')
    )

    metadata = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_('Metadata'),
        help_text=_('Custom metadata (campaign info, tracking params, etc.)')
    )

    # Managers
    objects = SoftDeleteManager()  # Default: excludes soft-deleted
    all_objects = models.Manager()  # Includes ALL records

    class Meta:
        db_table = 'qr_codes'
        verbose_name = _('QR Code')
        verbose_name_plural = _('QR Codes')
        ordering = ['-created_at']
        unique_together = [['organization', 'code']]
        indexes = [
            models.Index(fields=['organization', 'type'], name='qrcode_org_type_idx'),
            models.Index(fields=['organization', 'is_active'], name='qrcode_org_active_idx'),
            models.Index(fields=['organization', 'deleted_at'], name='qrcode_org_deleted_idx'),
            models.Index(fields=['organization', 'branch'], name='qrcode_org_branch_idx'),
            models.Index(fields=['organization', 'menu'], name='qrcode_org_menu_idx'),
            models.Index(fields=['organization', 'table'], name='qrcode_org_table_idx'),
            models.Index(fields=['organization', 'expires_at'], name='qrcode_org_expires_idx'),
            models.Index(fields=['code'], name='qrcode_code_idx'),
        ]

    def __str__(self) -> str:
        return f"{self.name} ({self.type})"

    def __repr__(self) -> str:
        return f"<QRCode(id={self.id}, code='{self.code}', type={self.type})>"

    @property
    def is_scannable(self) -> bool:
        """Check if QR code is active, not deleted, and not expired."""
        from django.utils import timezone
        if not self.is_active or self.is_deleted:
            return False
        if self.expires_at and self.expires_at < timezone.now():
            return False
        return True

    @property
    def is_expired(self) -> bool:
        """Check if QR code has expired."""
        from django.utils import timezone
        if self.expires_at is None:
            return False
        return self.expires_at < timezone.now()

    @property
    def target_url(self) -> str | None:
        """
        Get the target URL for this QR code.

        Returns the redirect_url if set, otherwise generates the default URL
        based on the QR code type.
        """
        if self.redirect_url:
            return self.redirect_url
        return self.short_url

    def get_setting(self, key: str, default=None):
        """
        Get a value from QR code settings.

        Args:
            key: The setting key to retrieve
            default: Default value if key not found

        Returns:
            The setting value or default
        """
        return self.settings.get(key, default)

    def set_setting(self, key: str, value) -> None:
        """
        Set a value in QR code settings.

        Args:
            key: The setting key
            value: The value to set
        """
        self.settings[key] = value
        self.save(update_fields=['settings', 'updated_at'])

    def get_metadata(self, key: str, default=None):
        """
        Get a value from QR code metadata.

        Args:
            key: The metadata key to retrieve
            default: Default value if key not found

        Returns:
            The metadata value or default
        """
        return self.metadata.get(key, default)

    def set_metadata(self, key: str, value) -> None:
        """
        Set a value in QR code metadata.

        Args:
            key: The metadata key
            value: The value to set
        """
        self.metadata[key] = value
        self.save(update_fields=['metadata', 'updated_at'])

    def activate(self) -> None:
        """Activate the QR code for scanning."""
        self.is_active = True
        self.save(update_fields=['is_active', 'updated_at'])

    def deactivate(self) -> None:
        """Deactivate the QR code (stops working)."""
        self.is_active = False
        self.save(update_fields=['is_active', 'updated_at'])

    def increment_scan_count(self, is_unique: bool = False) -> None:
        """
        Increment the scan counters.

        Args:
            is_unique: Whether this is a unique device scan
        """
        from django.utils import timezone
        from django.db.models import F

        updates = {'scan_count': F('scan_count') + 1, 'last_scanned_at': timezone.now()}
        if is_unique:
            updates['unique_scan_count'] = F('unique_scan_count') + 1

        QRCode.objects.filter(pk=self.pk).update(**updates)

        # Refresh from database
        self.refresh_from_db(fields=['scan_count', 'unique_scan_count', 'last_scanned_at'])

    def record_scan(
        self,
        ip_address: str = None,
        user_agent: str = None,
        session_id: str = None,
        device_type: str = None,
        browser: str = None,
        os: str = None,
        country: str = None,
        city: str = None,
        referer: str = None,
        metadata: dict = None
    ) -> 'QRScan':
        """
        Record a scan of this QR code.

        Creates a QRScan record and updates scan counters.

        Args:
            ip_address: IP address of the scanner
            user_agent: Browser user agent string
            session_id: Session identifier for tracking unique visits
            device_type: Device type (mobile, tablet, desktop)
            browser: Browser name
            os: Operating system
            country: Country code from geolocation
            city: City from geolocation
            referer: HTTP referer header
            metadata: Additional metadata

        Returns:
            The created QRScan instance
        """
        # Check if this is a unique scan (based on session_id or ip_address)
        is_unique = True
        if session_id or ip_address:
            existing = QRScan.objects.filter(
                qr_code=self,
            )
            if session_id:
                existing = existing.filter(session_id=session_id)
            elif ip_address:
                existing = existing.filter(ip_address=ip_address)
            is_unique = not existing.exists()

        # Create the scan record
        scan = QRScan.objects.create(
            qr_code=self,
            organization=self.organization,
            ip_address=ip_address,
            user_agent=user_agent,
            session_id=session_id,
            device_type=device_type,
            browser=browser,
            os=os,
            country=country,
            city=city,
            referer=referer,
            metadata=metadata or {},
        )

        # Update counters
        self.increment_scan_count(is_unique=is_unique)

        return scan


class QRScan(TimeStampedMixin, models.Model):
    """
    QRScan model - QR code scan tracking for analytics.

    Each time a QR code is scanned, a QRScan record is created to track
    analytics data including device information, location, and timestamps.
    This enables detailed analytics on QR code usage patterns.

    Note: QRScan uses a regular models.Manager instead of SoftDeleteManager
    because scan records should be retained for analytics even after
    soft-deleting the related QR code.

    Critical Rules:
    - EVERY query MUST filter by organization (multi-tenant isolation)
    - Scan records are append-only (no updates or deletes for data integrity)
    - IP addresses should be hashed or anonymized for privacy compliance

    Attributes:
        id: UUID primary key (ensures global uniqueness)
        qr_code: FK to the scanned QRCode
        organization: FK to Organization (denormalized for faster queries)
        scanned_at: Timestamp when the scan occurred
        ip_address: IP address of the scanner (consider privacy)
        user_agent: Full user agent string
        session_id: Session identifier for tracking unique visits
        device_type: Device type (mobile, tablet, desktop)
        browser: Browser name (parsed from user agent)
        os: Operating system (parsed from user agent)
        country: Country code from IP geolocation
        city: City from IP geolocation
        region: Region/state from IP geolocation
        latitude: Latitude coordinate (optional, if available)
        longitude: Longitude coordinate (optional, if available)
        referer: HTTP referer header
        is_unique: Whether this was a unique visit (first from this device/session)
        customer: Optional FK to Customer if user is logged in
        metadata: JSON field for additional tracking data

    Usage:
        # Record a scan (typically done via QRCode.record_scan())
        scan = QRScan.objects.create(
            qr_code=qr_code,
            organization=qr_code.organization,
            ip_address="192.168.1.100",
            user_agent="Mozilla/5.0...",
            device_type="mobile",
            browser="Safari",
            os="iOS"
        )

        # Query scans for a QR code (ALWAYS filter by organization!)
        scans = QRScan.objects.filter(
            organization=org,
            qr_code=qr_code
        )

        # Get scan statistics for a time period
        from django.utils import timezone
        from datetime import timedelta

        last_week_scans = QRScan.objects.filter(
            organization=org,
            scanned_at__gte=timezone.now() - timedelta(days=7)
        ).count()

        # Get device type distribution
        device_stats = QRScan.objects.filter(
            organization=org
        ).values('device_type').annotate(
            count=models.Count('id')
        )
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name=_('ID'),
        help_text=_('Unique identifier (UUID)')
    )

    qr_code = models.ForeignKey(
        QRCode,
        on_delete=models.CASCADE,
        related_name='scans',
        verbose_name=_('QR Code'),
        help_text=_('QR code that was scanned')
    )

    # Denormalized for faster queries (avoid joining through qr_code)
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='qr_scans',
        verbose_name=_('Organization'),
        help_text=_('Organization this scan belongs to (denormalized)')
    )

    # Timestamp
    scanned_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        verbose_name=_('Scanned at'),
        help_text=_('Timestamp when the scan occurred')
    )

    # Network information
    ip_address = models.GenericIPAddressField(
        blank=True,
        null=True,
        verbose_name=_('IP address'),
        help_text=_('IP address of the scanner')
    )

    # User agent information
    user_agent = models.TextField(
        blank=True,
        null=True,
        verbose_name=_('User agent'),
        help_text=_('Full user agent string')
    )

    session_id = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        db_index=True,
        verbose_name=_('Session ID'),
        help_text=_('Session identifier for tracking unique visits')
    )

    # Parsed device information
    device_type = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name=_('Device type'),
        help_text=_('Device type (mobile, tablet, desktop)')
    )

    browser = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name=_('Browser'),
        help_text=_('Browser name (e.g., Chrome, Safari, Firefox)')
    )

    os = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name=_('Operating system'),
        help_text=_('Operating system (e.g., iOS, Android, Windows)')
    )

    # Geolocation data
    country = models.CharField(
        max_length=2,
        blank=True,
        null=True,
        verbose_name=_('Country'),
        help_text=_('Two-letter country code (ISO 3166-1 alpha-2)')
    )

    city = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name=_('City'),
        help_text=_('City from IP geolocation')
    )

    region = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name=_('Region'),
        help_text=_('Region/state from IP geolocation')
    )

    latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        blank=True,
        null=True,
        verbose_name=_('Latitude'),
        help_text=_('Latitude coordinate from geolocation')
    )

    longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        blank=True,
        null=True,
        verbose_name=_('Longitude'),
        help_text=_('Longitude coordinate from geolocation')
    )

    # HTTP context
    referer = models.URLField(
        blank=True,
        null=True,
        max_length=1000,
        verbose_name=_('Referer'),
        help_text=_('HTTP referer header')
    )

    # Tracking flags
    is_unique = models.BooleanField(
        default=True,
        verbose_name=_('Is unique'),
        help_text=_('Whether this was a unique visit (first from this device/session)')
    )

    # Optional customer link (if logged in)
    customer = models.ForeignKey(
        'customers.Customer',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='qr_scans',
        verbose_name=_('Customer'),
        help_text=_('Customer who scanned (if logged in)')
    )

    # Additional metadata
    metadata = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_('Metadata'),
        help_text=_('Additional tracking data (UTM params, custom fields, etc.)')
    )

    class Meta:
        db_table = 'qr_scans'
        verbose_name = _('QR Scan')
        verbose_name_plural = _('QR Scans')
        ordering = ['-scanned_at']
        indexes = [
            models.Index(fields=['organization', 'scanned_at'], name='qrscan_org_scanned_idx'),
            models.Index(fields=['organization', 'qr_code'], name='qrscan_org_qrcode_idx'),
            models.Index(fields=['qr_code', 'scanned_at'], name='qrscan_qrcode_scanned_idx'),
            models.Index(fields=['organization', 'device_type'], name='qrscan_org_device_idx'),
            models.Index(fields=['organization', 'country'], name='qrscan_org_country_idx'),
            models.Index(fields=['ip_address'], name='qrscan_ip_idx'),
            models.Index(fields=['session_id'], name='qrscan_session_idx'),
        ]

    def __str__(self) -> str:
        return f"Scan: {self.qr_code.code} at {self.scanned_at}"

    def __repr__(self) -> str:
        return f"<QRScan(id={self.id}, qr_code='{self.qr_code.code}', scanned_at={self.scanned_at})>"

    @property
    def is_mobile(self) -> bool:
        """Check if scan was from a mobile device."""
        return self.device_type == 'mobile'

    @property
    def is_tablet(self) -> bool:
        """Check if scan was from a tablet."""
        return self.device_type == 'tablet'

    @property
    def is_desktop(self) -> bool:
        """Check if scan was from a desktop."""
        return self.device_type == 'desktop'

    @property
    def has_location(self) -> bool:
        """Check if geolocation data is available."""
        return bool(self.country or self.city or (self.latitude and self.longitude))

    @property
    def location_display(self) -> str:
        """Get a human-readable location string."""
        parts = []
        if self.city:
            parts.append(self.city)
        if self.region:
            parts.append(self.region)
        if self.country:
            parts.append(self.country)
        return ', '.join(parts) if parts else _('Unknown')

    def get_metadata(self, key: str, default=None):
        """
        Get a value from scan metadata.

        Args:
            key: The metadata key to retrieve
            default: Default value if key not found

        Returns:
            The metadata value or default
        """
        return self.metadata.get(key, default)


class Order(TimeStampedMixin, SoftDeleteMixin, models.Model):
    """
    Order model - represents customer orders with full transaction details.

    Orders capture all aspects of customer transactions including items ordered,
    pricing details, payment status, and fulfillment workflow. Each order follows
    a defined status progression from PENDING through COMPLETED or CANCELLED.

    Status Workflow:
    PENDING → CONFIRMED → PREPARING → READY → DELIVERED → COMPLETED
                                                        ↘ CANCELLED (from any state)

    Critical Rules:
    - EVERY query MUST filter by organization (multi-tenant isolation)
    - Use soft_delete() - never call delete() directly
    - order_number should be unique within an organization
    - Status transitions should follow the defined workflow

    Attributes:
        id: UUID primary key (ensures global uniqueness)
        organization: FK to parent Organization (tenant isolation)
        branch: Optional FK to Branch for multi-location support
        table: Optional FK to Table (for dine-in orders)
        customer: Optional FK to Customer (for registered customers)
        order_number: Human-readable order number (e.g., "ORD-2024-0001")
        status: Current order status (PENDING, CONFIRMED, PREPARING, etc.)
        type: Order type (DINE_IN, TAKEAWAY, DELIVERY)
        payment_status: Payment status (PENDING, PARTIAL, PAID, etc.)
        payment_method: Payment method used (CASH, CREDIT_CARD, etc.)
        subtotal: Sum of all items before tax/discount
        tax_amount: Total tax amount
        discount_amount: Total discount applied
        tip_amount: Optional tip amount
        total_amount: Final total after all calculations
        currency: Currency code (default TRY)
        guest_count: Number of guests (for dine-in)
        notes: Staff/kitchen notes
        special_instructions: Customer special instructions
        customer_info: JSON field for guest customer details (name, phone, email)
        delivery_address: JSON field for delivery address details
        placed_at: Timestamp when order was placed
        confirmed_at: Timestamp when order was confirmed
        ready_at: Timestamp when order was ready
        delivered_at: Timestamp when order was delivered
        completed_at: Timestamp when order was completed
        cancelled_at: Timestamp when order was cancelled
        cancel_reason: Reason for cancellation
        placed_by: FK to User who placed the order (staff)
        assigned_to: FK to User assigned to handle the order
        metadata: JSON field for additional order data

    Usage:
        # Create a dine-in order
        order = Order.objects.create(
            organization=org,
            table=table_5,
            type=OrderType.DINE_IN,
            order_number="ORD-2024-0001",
            guest_count=4
        )

        # Create a delivery order
        order = Order.objects.create(
            organization=org,
            type=OrderType.DELIVERY,
            order_number="ORD-2024-0002",
            customer=customer,
            delivery_address={
                "street": "123 Main St",
                "city": "Istanbul",
                "postal_code": "34000"
            }
        )

        # Query orders for organization (ALWAYS filter by organization!)
        orders = Order.objects.filter(organization=org)

        # Get pending orders
        pending_orders = Order.objects.filter(
            organization=org,
            status=OrderStatus.PENDING
        )

        # Transition order status
        order.confirm()
        order.start_preparation()
        order.mark_ready()
        order.deliver()
        order.complete()

        # Soft delete order (NEVER use delete())
        order.soft_delete()
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name=_('ID'),
        help_text=_('Unique identifier (UUID)')
    )

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='orders',
        verbose_name=_('Organization'),
        help_text=_('Organization this order belongs to')
    )

    branch = models.ForeignKey(
        Branch,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='orders',
        verbose_name=_('Branch'),
        help_text=_('Branch this order belongs to (optional for single-location)')
    )

    table = models.ForeignKey(
        Table,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='orders',
        verbose_name=_('Table'),
        help_text=_('Table associated with this order (for dine-in)')
    )

    customer = models.ForeignKey(
        'customers.Customer',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='orders',
        verbose_name=_('Customer'),
        help_text=_('Customer who placed this order (if registered)')
    )

    # Order identification
    order_number = models.CharField(
        max_length=50,
        verbose_name=_('Order number'),
        help_text=_('Human-readable order number (e.g., ORD-2024-0001)')
    )

    # Status and type
    status = models.CharField(
        max_length=20,
        choices=OrderStatus.choices,
        default=OrderStatus.PENDING,
        db_index=True,
        verbose_name=_('Status'),
        help_text=_('Current order status')
    )

    type = models.CharField(
        max_length=20,
        choices=OrderType.choices,
        default=OrderType.DINE_IN,
        db_index=True,
        verbose_name=_('Type'),
        help_text=_('Order type (dine-in, takeaway, delivery)')
    )

    # Payment information
    payment_status = models.CharField(
        max_length=20,
        choices=PaymentStatus.choices,
        default=PaymentStatus.PENDING,
        db_index=True,
        verbose_name=_('Payment status'),
        help_text=_('Current payment status')
    )

    payment_method = models.CharField(
        max_length=20,
        choices=PaymentMethod.choices,
        blank=True,
        null=True,
        verbose_name=_('Payment method'),
        help_text=_('Payment method used')
    )

    # Financial details
    subtotal = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name=_('Subtotal'),
        help_text=_('Sum of all items before tax and discount')
    )

    tax_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name=_('Tax amount'),
        help_text=_('Total tax amount')
    )

    discount_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name=_('Discount amount'),
        help_text=_('Total discount applied')
    )

    tip_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name=_('Tip amount'),
        help_text=_('Tip/gratuity amount')
    )

    total_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name=_('Total amount'),
        help_text=_('Final total (subtotal + tax - discount + tip)')
    )

    currency = models.CharField(
        max_length=3,
        default='TRY',
        verbose_name=_('Currency'),
        help_text=_('Currency code (ISO 4217)')
    )

    # Guest information
    guest_count = models.PositiveSmallIntegerField(
        default=1,
        verbose_name=_('Guest count'),
        help_text=_('Number of guests (for dine-in orders)')
    )

    # Notes and instructions
    notes = models.TextField(
        blank=True,
        null=True,
        verbose_name=_('Notes'),
        help_text=_('Staff/kitchen notes about the order')
    )

    special_instructions = models.TextField(
        blank=True,
        null=True,
        verbose_name=_('Special instructions'),
        help_text=_('Customer special instructions or requests')
    )

    # Customer info (for guest checkout without registration)
    customer_info = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_('Customer info'),
        help_text=_('Guest customer details: name, phone, email')
    )

    # Delivery address (for delivery orders)
    delivery_address = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_('Delivery address'),
        help_text=_('Delivery address details: street, city, postal_code, etc.')
    )

    # Timestamps for workflow tracking
    placed_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name=_('Placed at'),
        help_text=_('Timestamp when order was placed')
    )

    confirmed_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name=_('Confirmed at'),
        help_text=_('Timestamp when order was confirmed by staff')
    )

    preparing_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name=_('Preparing at'),
        help_text=_('Timestamp when order preparation started')
    )

    ready_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name=_('Ready at'),
        help_text=_('Timestamp when order was ready')
    )

    delivered_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name=_('Delivered at'),
        help_text=_('Timestamp when order was delivered to customer')
    )

    completed_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name=_('Completed at'),
        help_text=_('Timestamp when order was completed')
    )

    cancelled_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name=_('Cancelled at'),
        help_text=_('Timestamp when order was cancelled')
    )

    cancel_reason = models.TextField(
        blank=True,
        null=True,
        verbose_name=_('Cancel reason'),
        help_text=_('Reason for order cancellation')
    )

    # Staff assignments
    placed_by = models.ForeignKey(
        'core.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='placed_orders',
        verbose_name=_('Placed by'),
        help_text=_('Staff member who placed the order')
    )

    assigned_to = models.ForeignKey(
        'core.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_orders',
        verbose_name=_('Assigned to'),
        help_text=_('Staff member assigned to handle this order')
    )

    # Additional metadata
    metadata = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_('Metadata'),
        help_text=_('Additional order data (source, promo codes, etc.)')
    )

    # Managers
    objects = SoftDeleteManager()  # Default: excludes soft-deleted
    all_objects = models.Manager()  # Includes ALL records

    class Meta:
        db_table = 'orders'
        verbose_name = _('Order')
        verbose_name_plural = _('Orders')
        ordering = ['-created_at']
        unique_together = [['organization', 'order_number']]
        indexes = [
            models.Index(fields=['organization', 'status'], name='order_org_status_idx'),
            models.Index(fields=['organization', 'type'], name='order_org_type_idx'),
            models.Index(fields=['organization', 'payment_status'], name='order_org_pay_status_idx'),
            models.Index(fields=['organization', 'deleted_at'], name='order_org_deleted_idx'),
            models.Index(fields=['organization', 'branch'], name='order_org_branch_idx'),
            models.Index(fields=['organization', 'table'], name='order_org_table_idx'),
            models.Index(fields=['organization', 'customer'], name='order_org_customer_idx'),
            models.Index(fields=['organization', 'placed_at'], name='order_org_placed_idx'),
            models.Index(fields=['organization', 'order_number'], name='order_org_number_idx'),
            models.Index(fields=['table', 'status'], name='order_table_status_idx'),
            models.Index(fields=['assigned_to', 'status'], name='order_assigned_status_idx'),
        ]

    def __str__(self) -> str:
        return f"Order {self.order_number} ({self.status})"

    def __repr__(self) -> str:
        return f"<Order(id={self.id}, number='{self.order_number}', status={self.status})>"

    @property
    def is_pending(self) -> bool:
        """Check if order is pending."""
        return self.status == OrderStatus.PENDING

    @property
    def is_confirmed(self) -> bool:
        """Check if order has been confirmed."""
        return self.status == OrderStatus.CONFIRMED

    @property
    def is_preparing(self) -> bool:
        """Check if order is being prepared."""
        return self.status == OrderStatus.PREPARING

    @property
    def is_ready(self) -> bool:
        """Check if order is ready."""
        return self.status == OrderStatus.READY

    @property
    def is_delivered(self) -> bool:
        """Check if order has been delivered."""
        return self.status == OrderStatus.DELIVERED

    @property
    def is_completed(self) -> bool:
        """Check if order is completed."""
        return self.status == OrderStatus.COMPLETED

    @property
    def is_cancelled(self) -> bool:
        """Check if order has been cancelled."""
        return self.status == OrderStatus.CANCELLED

    @property
    def is_active(self) -> bool:
        """Check if order is in an active state (not completed or cancelled)."""
        return self.status not in [OrderStatus.COMPLETED, OrderStatus.CANCELLED]

    @property
    def is_paid(self) -> bool:
        """Check if order has been fully paid."""
        return self.payment_status == PaymentStatus.PAID

    @property
    def is_dine_in(self) -> bool:
        """Check if order is dine-in type."""
        return self.type == OrderType.DINE_IN

    @property
    def is_takeaway(self) -> bool:
        """Check if order is takeaway type."""
        return self.type == OrderType.TAKEAWAY

    @property
    def is_delivery(self) -> bool:
        """Check if order is delivery type."""
        return self.type == OrderType.DELIVERY

    @property
    def customer_name(self) -> str:
        """Get customer name from customer object or customer_info."""
        if self.customer:
            return self.customer.full_name
        return self.customer_info.get('name', _('Guest'))

    @property
    def customer_phone(self) -> str | None:
        """Get customer phone from customer object or customer_info."""
        if self.customer:
            return self.customer.phone
        return self.customer_info.get('phone')

    @property
    def customer_email(self) -> str | None:
        """Get customer email from customer object or customer_info."""
        if self.customer:
            return self.customer.email
        return self.customer_info.get('email')

    @property
    def item_count(self) -> int:
        """Return the number of items in this order."""
        return self.items.filter(deleted_at__isnull=True).count()

    @property
    def item_quantity(self) -> int:
        """Return the total quantity of all items in this order."""
        from django.db.models import Sum
        result = self.items.filter(deleted_at__isnull=True).aggregate(
            total=Sum('quantity')
        )
        return result['total'] or 0

    def calculate_totals(self, save: bool = True) -> None:
        """
        Calculate and update order totals from items.

        This method recalculates subtotal based on order items,
        then calculates total_amount including tax, discount, and tip.

        Args:
            save: Whether to save the order after calculation
        """
        from django.db.models import Sum, F, DecimalField
        from django.db.models.functions import Coalesce
        from decimal import Decimal

        # Calculate subtotal from items
        result = self.items.filter(deleted_at__isnull=True).aggregate(
            subtotal=Coalesce(
                Sum(F('quantity') * F('unit_price'), output_field=DecimalField()),
                Decimal('0')
            )
        )
        self.subtotal = result['subtotal'] or Decimal('0')

        # Calculate total
        self.total_amount = (
            self.subtotal
            + self.tax_amount
            - self.discount_amount
            + self.tip_amount
        )

        if save:
            self.save(update_fields=[
                'subtotal', 'total_amount', 'updated_at'
            ])

    def set_status(self, status: str, timestamp_field: str = None) -> None:
        """
        Set the order status and optionally update a timestamp field.

        Args:
            status: OrderStatus value
            timestamp_field: Optional field name to update with current time
        """
        from django.utils import timezone

        if status not in OrderStatus.values:
            raise ValueError(f"Invalid status: {status}. Must be one of {OrderStatus.values}")

        self.status = status
        update_fields = ['status', 'updated_at']

        if timestamp_field:
            setattr(self, timestamp_field, timezone.now())
            update_fields.append(timestamp_field)

        self.save(update_fields=update_fields)

    def confirm(self) -> None:
        """Confirm the order (staff acknowledges it)."""
        if self.status != OrderStatus.PENDING:
            raise ValueError(f"Cannot confirm order with status {self.status}")
        self.set_status(OrderStatus.CONFIRMED, 'confirmed_at')

    def start_preparation(self) -> None:
        """Start preparing the order (kitchen/bar begins work)."""
        if self.status != OrderStatus.CONFIRMED:
            raise ValueError(f"Cannot start preparation for order with status {self.status}")
        self.set_status(OrderStatus.PREPARING, 'preparing_at')

    def mark_ready(self) -> None:
        """Mark the order as ready for pickup/delivery."""
        if self.status != OrderStatus.PREPARING:
            raise ValueError(f"Cannot mark ready order with status {self.status}")
        self.set_status(OrderStatus.READY, 'ready_at')

    def deliver(self) -> None:
        """Mark the order as delivered to customer."""
        if self.status != OrderStatus.READY:
            raise ValueError(f"Cannot deliver order with status {self.status}")
        self.set_status(OrderStatus.DELIVERED, 'delivered_at')

    def complete(self) -> None:
        """Complete the order (fully done and paid)."""
        if self.status not in [OrderStatus.READY, OrderStatus.DELIVERED]:
            raise ValueError(f"Cannot complete order with status {self.status}")
        self.set_status(OrderStatus.COMPLETED, 'completed_at')

    def cancel(self, reason: str = None) -> None:
        """
        Cancel the order.

        Args:
            reason: Optional reason for cancellation
        """
        from django.utils import timezone

        if self.status in [OrderStatus.COMPLETED, OrderStatus.CANCELLED]:
            raise ValueError(f"Cannot cancel order with status {self.status}")

        self.status = OrderStatus.CANCELLED
        self.cancelled_at = timezone.now()
        if reason:
            self.cancel_reason = reason
        self.save(update_fields=['status', 'cancelled_at', 'cancel_reason', 'updated_at'])

    def set_payment_status(self, status: str, method: str = None) -> None:
        """
        Set the payment status and optionally the payment method.

        Args:
            status: PaymentStatus value
            method: Optional PaymentMethod value
        """
        if status not in PaymentStatus.values:
            raise ValueError(f"Invalid payment status: {status}")

        self.payment_status = status
        update_fields = ['payment_status', 'updated_at']

        if method:
            if method not in PaymentMethod.values:
                raise ValueError(f"Invalid payment method: {method}")
            self.payment_method = method
            update_fields.append('payment_method')

        self.save(update_fields=update_fields)

    def mark_paid(self, method: str = None) -> None:
        """
        Mark the order as fully paid.

        Args:
            method: Optional payment method used
        """
        self.set_payment_status(PaymentStatus.PAID, method)

    def assign_to(self, user) -> None:
        """
        Assign the order to a staff member.

        Args:
            user: User to assign the order to
        """
        self.assigned_to = user
        self.save(update_fields=['assigned_to', 'updated_at'])

    def get_metadata(self, key: str, default=None):
        """
        Get a value from order metadata.

        Args:
            key: The metadata key to retrieve
            default: Default value if key not found

        Returns:
            The metadata value or default
        """
        return self.metadata.get(key, default)

    def set_metadata(self, key: str, value) -> None:
        """
        Set a value in order metadata.

        Args:
            key: The metadata key
            value: The value to set
        """
        self.metadata[key] = value
        self.save(update_fields=['metadata', 'updated_at'])

    def get_customer_info(self, key: str, default=None):
        """
        Get a value from customer_info.

        Args:
            key: The key to retrieve (name, phone, email)
            default: Default value if key not found

        Returns:
            The value or default
        """
        return self.customer_info.get(key, default)

    def set_customer_info(self, **kwargs) -> None:
        """
        Set customer info fields.

        Args:
            **kwargs: Key-value pairs to set (name, phone, email)
        """
        self.customer_info.update(kwargs)
        self.save(update_fields=['customer_info', 'updated_at'])

    def get_delivery_address(self, key: str = None, default=None):
        """
        Get delivery address or a specific field.

        Args:
            key: Optional key to retrieve from address
            default: Default value if key not found

        Returns:
            Full address dict or specific field value
        """
        if key:
            return self.delivery_address.get(key, default)
        return self.delivery_address

    def set_delivery_address(self, **kwargs) -> None:
        """
        Set delivery address fields.

        Args:
            **kwargs: Key-value pairs for address (street, city, postal_code, etc.)
        """
        self.delivery_address.update(kwargs)
        self.save(update_fields=['delivery_address', 'updated_at'])


class OrderItem(TimeStampedMixin, SoftDeleteMixin, models.Model):
    """
    OrderItem model - individual line items within orders.

    Each OrderItem represents a single product/variant ordered by a customer,
    including quantity, selected modifiers, pricing, and item-specific notes.
    OrderItems follow their own status workflow independent of the parent order.

    Status Workflow:
    PENDING → PREPARING → READY → DELIVERED
                                ↘ CANCELLED (from any state)

    Critical Rules:
    - EVERY query MUST filter by organization (via order lookup)
    - Use soft_delete() - never call delete() directly
    - Unit price should be captured at order time (not reference product price)
    - Modifiers are stored as JSON snapshot at order time

    Attributes:
        id: UUID primary key (ensures global uniqueness)
        order: FK to parent Order
        product: FK to Product ordered (for reference, may be soft-deleted)
        variant: Optional FK to ProductVariant selected
        quantity: Number of items ordered
        unit_price: Price per unit at time of order
        total_price: Calculated total (unit_price * quantity + modifiers)
        currency: Currency code (inherited from order)
        status: Current item status (PENDING, PREPARING, READY, DELIVERED, CANCELLED)
        modifiers: JSON snapshot of selected modifiers with prices
        notes: Customer notes/special instructions for this item
        is_gift: Whether this item is a complimentary gift
        prepared_at: Timestamp when item preparation completed
        delivered_at: Timestamp when item was delivered to customer
        cancelled_at: Timestamp when item was cancelled
        cancel_reason: Reason for cancellation
        metadata: JSON field for additional item data

    Usage:
        # Create an order item
        item = OrderItem.objects.create(
            order=order,
            product=pizza,
            variant=large_variant,
            quantity=2,
            unit_price=Decimal("199.90"),
            total_price=Decimal("399.80"),
            modifiers=[
                {"name": "Extra Cheese", "price": Decimal("15.00")}
            ],
            notes="No olives please"
        )

        # Query items for an order
        items = OrderItem.objects.filter(order=order)

        # Get pending items for kitchen
        pending_items = OrderItem.objects.filter(
            order__organization=org,
            status=OrderItemStatus.PENDING
        )

        # Update item status
        item.start_preparation()
        item.mark_ready()
        item.deliver()

        # Soft delete item (NEVER use delete())
        item.soft_delete()
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name=_('ID'),
        help_text=_('Unique identifier (UUID)')
    )

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name=_('Order'),
        help_text=_('Order this item belongs to')
    )

    product = models.ForeignKey(
        'menu.Product',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='order_items',
        verbose_name=_('Product'),
        help_text=_('Product ordered (reference, may be soft-deleted)')
    )

    variant = models.ForeignKey(
        'menu.ProductVariant',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='order_items',
        verbose_name=_('Variant'),
        help_text=_('Product variant selected (e.g., Large, Small)')
    )

    # Quantity and pricing
    quantity = models.PositiveIntegerField(
        default=1,
        verbose_name=_('Quantity'),
        help_text=_('Number of items ordered')
    )

    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=_('Unit price'),
        help_text=_('Price per unit at time of order (captured, not referenced)')
    )

    total_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=_('Total price'),
        help_text=_('Total price (unit_price * quantity + modifier costs)')
    )

    currency = models.CharField(
        max_length=3,
        default='TRY',
        verbose_name=_('Currency'),
        help_text=_('Currency code (ISO 4217)')
    )

    # Status
    status = models.CharField(
        max_length=20,
        choices=OrderItemStatus.choices,
        default=OrderItemStatus.PENDING,
        db_index=True,
        verbose_name=_('Status'),
        help_text=_('Current item status')
    )

    # Modifiers snapshot (stored at order time)
    modifiers = models.JSONField(
        default=list,
        blank=True,
        verbose_name=_('Modifiers'),
        help_text=_('JSON snapshot of selected modifiers with prices at order time')
    )

    # Notes and instructions
    notes = models.TextField(
        blank=True,
        null=True,
        verbose_name=_('Notes'),
        help_text=_('Customer notes/special instructions for this item')
    )

    # Gift flag
    is_gift = models.BooleanField(
        default=False,
        verbose_name=_('Is gift'),
        help_text=_('Whether this item is a complimentary gift (zero charge)')
    )

    # Workflow timestamps
    prepared_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name=_('Prepared at'),
        help_text=_('Timestamp when item preparation completed')
    )

    delivered_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name=_('Delivered at'),
        help_text=_('Timestamp when item was delivered to customer')
    )

    cancelled_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name=_('Cancelled at'),
        help_text=_('Timestamp when item was cancelled')
    )

    cancel_reason = models.TextField(
        blank=True,
        null=True,
        verbose_name=_('Cancel reason'),
        help_text=_('Reason for item cancellation')
    )

    # Additional metadata
    metadata = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_('Metadata'),
        help_text=_('Additional item data (JSON)')
    )

    # Managers
    objects = SoftDeleteManager()  # Default: excludes soft-deleted
    all_objects = models.Manager()  # Includes ALL records

    class Meta:
        db_table = 'order_items'
        verbose_name = _('Order Item')
        verbose_name_plural = _('Order Items')
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['order', 'status'], name='orderitem_order_status_idx'),
            models.Index(fields=['order', 'deleted_at'], name='orderitem_order_deleted_idx'),
            models.Index(fields=['product'], name='orderitem_product_idx'),
            models.Index(fields=['status'], name='orderitem_status_idx'),
        ]

    def __str__(self) -> str:
        product_name = self.product.name if self.product else _('Unknown Product')
        return f"{self.quantity}x {product_name}"

    def __repr__(self) -> str:
        product_name = self.product.name if self.product else 'Unknown'
        return f"<OrderItem(id={self.id}, product='{product_name}', qty={self.quantity}, status={self.status})>"

    @property
    def organization(self):
        """Get the organization this order item belongs to via order."""
        return self.order.organization

    @property
    def is_pending(self) -> bool:
        """Check if item is pending preparation."""
        return self.status == OrderItemStatus.PENDING

    @property
    def is_preparing(self) -> bool:
        """Check if item is being prepared."""
        return self.status == OrderItemStatus.PREPARING

    @property
    def is_ready(self) -> bool:
        """Check if item is ready for delivery."""
        return self.status == OrderItemStatus.READY

    @property
    def is_delivered(self) -> bool:
        """Check if item has been delivered."""
        return self.status == OrderItemStatus.DELIVERED

    @property
    def is_cancelled(self) -> bool:
        """Check if item has been cancelled."""
        return self.status == OrderItemStatus.CANCELLED

    @property
    def is_active(self) -> bool:
        """Check if item is in an active state (not delivered or cancelled)."""
        return self.status not in [OrderItemStatus.DELIVERED, OrderItemStatus.CANCELLED]

    @property
    def product_name(self) -> str:
        """Get the product name, handling deleted products."""
        if self.product:
            return self.product.name
        return self.metadata.get('product_name', _('Unknown Product'))

    @property
    def variant_name(self) -> str | None:
        """Get the variant name if applicable."""
        if self.variant:
            return self.variant.name
        return self.metadata.get('variant_name')

    @property
    def display_name(self) -> str:
        """Get display name including variant if applicable."""
        name = self.product_name
        if self.variant_name:
            name = f"{name} ({self.variant_name})"
        return name

    @property
    def formatted_unit_price(self) -> str:
        """Return formatted unit price with currency symbol."""
        currency_symbols = {
            'TRY': '₺',
            'USD': '$',
            'EUR': '€',
            'GBP': '£',
        }
        symbol = currency_symbols.get(self.currency, self.currency)
        return f"{symbol}{self.unit_price:,.2f}"

    @property
    def formatted_total_price(self) -> str:
        """Return formatted total price with currency symbol."""
        currency_symbols = {
            'TRY': '₺',
            'USD': '$',
            'EUR': '€',
            'GBP': '£',
        }
        symbol = currency_symbols.get(self.currency, self.currency)
        return f"{symbol}{self.total_price:,.2f}"

    @property
    def modifier_total(self):
        """Calculate total cost of all modifiers."""
        from decimal import Decimal
        total = Decimal('0')
        for modifier in self.modifiers:
            price = modifier.get('price', 0)
            qty = modifier.get('quantity', 1)
            total += Decimal(str(price)) * qty
        return total

    @property
    def has_modifiers(self) -> bool:
        """Check if item has any modifiers selected."""
        return bool(self.modifiers)

    @property
    def has_notes(self) -> bool:
        """Check if item has customer notes."""
        return bool(self.notes)

    def calculate_total(self, save: bool = True) -> None:
        """
        Calculate and update total price from unit price, quantity, and modifiers.

        Args:
            save: Whether to save the item after calculation
        """
        from decimal import Decimal
        base_total = self.unit_price * self.quantity
        modifier_cost = self.modifier_total * self.quantity
        self.total_price = base_total + modifier_cost

        if self.is_gift:
            self.total_price = Decimal('0')

        if save:
            self.save(update_fields=['total_price', 'updated_at'])

    def set_status(self, status: str, timestamp_field: str = None) -> None:
        """
        Set the item status and optionally update a timestamp field.

        Args:
            status: OrderItemStatus value
            timestamp_field: Optional field name to update with current time
        """
        from django.utils import timezone

        if status not in OrderItemStatus.values:
            raise ValueError(f"Invalid status: {status}. Must be one of {OrderItemStatus.values}")

        self.status = status
        update_fields = ['status', 'updated_at']

        if timestamp_field:
            setattr(self, timestamp_field, timezone.now())
            update_fields.append(timestamp_field)

        self.save(update_fields=update_fields)

    def start_preparation(self) -> None:
        """Start preparing the item (kitchen/bar begins work)."""
        if self.status != OrderItemStatus.PENDING:
            raise ValueError(f"Cannot start preparation for item with status {self.status}")
        self.set_status(OrderItemStatus.PREPARING)

    def mark_ready(self) -> None:
        """Mark the item as ready for delivery."""
        if self.status != OrderItemStatus.PREPARING:
            raise ValueError(f"Cannot mark ready item with status {self.status}")
        self.set_status(OrderItemStatus.READY, 'prepared_at')

    def deliver(self) -> None:
        """Mark the item as delivered to customer."""
        if self.status != OrderItemStatus.READY:
            raise ValueError(f"Cannot deliver item with status {self.status}")
        self.set_status(OrderItemStatus.DELIVERED, 'delivered_at')

    def cancel(self, reason: str = None) -> None:
        """
        Cancel the item.

        Args:
            reason: Optional reason for cancellation
        """
        from django.utils import timezone

        if self.status in [OrderItemStatus.DELIVERED, OrderItemStatus.CANCELLED]:
            raise ValueError(f"Cannot cancel item with status {self.status}")

        self.status = OrderItemStatus.CANCELLED
        self.cancelled_at = timezone.now()
        if reason:
            self.cancel_reason = reason
        self.save(update_fields=['status', 'cancelled_at', 'cancel_reason', 'updated_at'])

    def add_modifier(self, name: str, price, quantity: int = 1) -> None:
        """
        Add a modifier to the item.

        Args:
            name: Modifier name
            price: Modifier price
            quantity: Quantity of this modifier
        """
        from decimal import Decimal
        modifier = {
            'name': name,
            'price': str(Decimal(str(price))),
            'quantity': quantity
        }
        if not self.modifiers:
            self.modifiers = []
        self.modifiers.append(modifier)
        self.save(update_fields=['modifiers', 'updated_at'])

    def get_metadata(self, key: str, default=None):
        """
        Get a value from item metadata.

        Args:
            key: The metadata key to retrieve
            default: Default value if key not found

        Returns:
            The metadata value or default
        """
        return self.metadata.get(key, default)

    def set_metadata(self, key: str, value) -> None:
        """
        Set a value in item metadata.

        Args:
            key: The metadata key
            value: The value to set
        """
        self.metadata[key] = value
        self.save(update_fields=['metadata', 'updated_at'])


class ServiceRequest(TimeStampedMixin, SoftDeleteMixin, models.Model):
    """
    ServiceRequest model - waiter call/service requests from tables.

    ServiceRequests enable customers to request assistance from staff without
    leaving their table. Common request types include calling a waiter,
    requesting the bill, or asking for help with the menu.

    Status Workflow:
    PENDING → IN_PROGRESS → COMPLETED
                          ↘ CANCELLED (from any state)

    Critical Rules:
    - EVERY query MUST filter by organization (multi-tenant isolation)
    - Use soft_delete() - never call delete() directly
    - Requests should be acknowledged promptly (track response time)

    Attributes:
        id: UUID primary key (ensures global uniqueness)
        organization: FK to parent Organization (tenant isolation)
        branch: Optional FK to Branch for multi-location support
        table: FK to Table making the request
        order: Optional FK to related Order
        customer: Optional FK to Customer if logged in
        type: Type of request (WAITER_CALL, BILL_REQUEST, HELP, OTHER)
        status: Current status (PENDING, IN_PROGRESS, COMPLETED, CANCELLED)
        message: Optional customer message/notes
        priority: Priority level (1-5, where 1 is highest)
        assigned_to: FK to User (staff) assigned to handle request
        acknowledged_at: Timestamp when request was acknowledged
        completed_at: Timestamp when request was completed
        cancelled_at: Timestamp when request was cancelled
        cancel_reason: Reason for cancellation
        response_time_seconds: Time to first response in seconds
        metadata: JSON field for additional request data

    Usage:
        # Create a waiter call request
        request = ServiceRequest.objects.create(
            organization=org,
            table=table_5,
            type=ServiceRequestType.WAITER_CALL,
            message="Need help with the menu"
        )

        # Create a bill request
        bill_request = ServiceRequest.objects.create(
            organization=org,
            table=table_5,
            order=active_order,
            type=ServiceRequestType.BILL_REQUEST
        )

        # Query pending requests for organization (ALWAYS filter by organization!)
        pending = ServiceRequest.objects.filter(
            organization=org,
            status=ServiceRequestStatus.PENDING
        )

        # Assign and acknowledge request
        request.acknowledge(staff_user)

        # Complete the request
        request.complete()

        # Soft delete request (NEVER use delete())
        request.soft_delete()
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name=_('ID'),
        help_text=_('Unique identifier (UUID)')
    )

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='service_requests',
        verbose_name=_('Organization'),
        help_text=_('Organization this request belongs to')
    )

    branch = models.ForeignKey(
        Branch,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='service_requests',
        verbose_name=_('Branch'),
        help_text=_('Branch this request belongs to (optional for single-location)')
    )

    table = models.ForeignKey(
        Table,
        on_delete=models.CASCADE,
        related_name='service_requests',
        verbose_name=_('Table'),
        help_text=_('Table making this request')
    )

    order = models.ForeignKey(
        Order,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='service_requests',
        verbose_name=_('Order'),
        help_text=_('Related order (if applicable)')
    )

    customer = models.ForeignKey(
        'customers.Customer',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='service_requests',
        verbose_name=_('Customer'),
        help_text=_('Customer who made this request (if logged in)')
    )

    # Request type and status
    type = models.CharField(
        max_length=20,
        choices=ServiceRequestType.choices,
        default=ServiceRequestType.WAITER_CALL,
        db_index=True,
        verbose_name=_('Type'),
        help_text=_('Type of service request')
    )

    status = models.CharField(
        max_length=20,
        choices=ServiceRequestStatus.choices,
        default=ServiceRequestStatus.PENDING,
        db_index=True,
        verbose_name=_('Status'),
        help_text=_('Current request status')
    )

    # Message and priority
    message = models.TextField(
        blank=True,
        null=True,
        verbose_name=_('Message'),
        help_text=_('Optional customer message or notes')
    )

    priority = models.PositiveSmallIntegerField(
        default=3,
        verbose_name=_('Priority'),
        help_text=_('Priority level 1-5 (1 is highest priority)')
    )

    # Staff assignment
    assigned_to = models.ForeignKey(
        'core.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_service_requests',
        verbose_name=_('Assigned to'),
        help_text=_('Staff member assigned to handle this request')
    )

    # Workflow timestamps
    acknowledged_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name=_('Acknowledged at'),
        help_text=_('Timestamp when request was acknowledged by staff')
    )

    completed_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name=_('Completed at'),
        help_text=_('Timestamp when request was completed')
    )

    cancelled_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name=_('Cancelled at'),
        help_text=_('Timestamp when request was cancelled')
    )

    cancel_reason = models.TextField(
        blank=True,
        null=True,
        verbose_name=_('Cancel reason'),
        help_text=_('Reason for request cancellation')
    )

    # Performance metrics
    response_time_seconds = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name=_('Response time'),
        help_text=_('Time to first response in seconds')
    )

    # Additional metadata
    metadata = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_('Metadata'),
        help_text=_('Additional request data (JSON)')
    )

    # Managers
    objects = SoftDeleteManager()  # Default: excludes soft-deleted
    all_objects = models.Manager()  # Includes ALL records

    class Meta:
        db_table = 'service_requests'
        verbose_name = _('Service Request')
        verbose_name_plural = _('Service Requests')
        ordering = ['priority', '-created_at']
        indexes = [
            models.Index(fields=['organization', 'status'], name='svcreq_org_status_idx'),
            models.Index(fields=['organization', 'type'], name='svcreq_org_type_idx'),
            models.Index(fields=['organization', 'deleted_at'], name='svcreq_org_deleted_idx'),
            models.Index(fields=['organization', 'branch'], name='svcreq_org_branch_idx'),
            models.Index(fields=['table', 'status'], name='svcreq_table_status_idx'),
            models.Index(fields=['assigned_to', 'status'], name='svcreq_assigned_status_idx'),
            models.Index(fields=['organization', 'priority', 'status'], name='svcreq_org_priority_idx'),
        ]

    def __str__(self) -> str:
        return f"{self.get_type_display()} - {self.table.name} ({self.status})"

    def __repr__(self) -> str:
        return f"<ServiceRequest(id={self.id}, type={self.type}, table='{self.table.name}', status={self.status})>"

    @property
    def is_pending(self) -> bool:
        """Check if request is pending."""
        return self.status == ServiceRequestStatus.PENDING

    @property
    def is_in_progress(self) -> bool:
        """Check if request is being handled."""
        return self.status == ServiceRequestStatus.IN_PROGRESS

    @property
    def is_completed(self) -> bool:
        """Check if request is completed."""
        return self.status == ServiceRequestStatus.COMPLETED

    @property
    def is_cancelled(self) -> bool:
        """Check if request has been cancelled."""
        return self.status == ServiceRequestStatus.CANCELLED

    @property
    def is_active(self) -> bool:
        """Check if request is in an active state (not completed or cancelled)."""
        return self.status not in [ServiceRequestStatus.COMPLETED, ServiceRequestStatus.CANCELLED]

    @property
    def is_waiter_call(self) -> bool:
        """Check if this is a waiter call request."""
        return self.type == ServiceRequestType.WAITER_CALL

    @property
    def is_bill_request(self) -> bool:
        """Check if this is a bill request."""
        return self.type == ServiceRequestType.BILL_REQUEST

    @property
    def is_help_request(self) -> bool:
        """Check if this is a help request."""
        return self.type == ServiceRequestType.HELP

    @property
    def is_high_priority(self) -> bool:
        """Check if request has high priority (1 or 2)."""
        return self.priority <= 2

    @property
    def has_message(self) -> bool:
        """Check if request has a message."""
        return bool(self.message)

    @property
    def is_assigned(self) -> bool:
        """Check if request is assigned to a staff member."""
        return self.assigned_to is not None

    @property
    def wait_time_seconds(self) -> int | None:
        """
        Calculate current wait time in seconds.

        Returns:
            Seconds since request was created, or None if already completed
        """
        from django.utils import timezone

        if self.status in [ServiceRequestStatus.COMPLETED, ServiceRequestStatus.CANCELLED]:
            return None

        delta = timezone.now() - self.created_at
        return int(delta.total_seconds())

    @property
    def wait_time_display(self) -> str:
        """Get human-readable wait time."""
        seconds = self.wait_time_seconds
        if seconds is None:
            return _('Completed')

        if seconds < 60:
            return _('Just now')
        elif seconds < 3600:
            minutes = seconds // 60
            return _('%(minutes)d min ago') % {'minutes': minutes}
        else:
            hours = seconds // 3600
            return _('%(hours)d hr ago') % {'hours': hours}

    def set_status(self, status: str, timestamp_field: str = None) -> None:
        """
        Set the request status and optionally update a timestamp field.

        Args:
            status: ServiceRequestStatus value
            timestamp_field: Optional field name to update with current time
        """
        from django.utils import timezone

        if status not in ServiceRequestStatus.values:
            raise ValueError(f"Invalid status: {status}. Must be one of {ServiceRequestStatus.values}")

        self.status = status
        update_fields = ['status', 'updated_at']

        if timestamp_field:
            setattr(self, timestamp_field, timezone.now())
            update_fields.append(timestamp_field)

        self.save(update_fields=update_fields)

    def acknowledge(self, user=None) -> None:
        """
        Acknowledge the request (staff begins handling it).

        Args:
            user: Optional staff member to assign
        """
        from django.utils import timezone

        if self.status != ServiceRequestStatus.PENDING:
            raise ValueError(f"Cannot acknowledge request with status {self.status}")

        self.status = ServiceRequestStatus.IN_PROGRESS
        self.acknowledged_at = timezone.now()

        # Calculate response time
        delta = self.acknowledged_at - self.created_at
        self.response_time_seconds = int(delta.total_seconds())

        update_fields = ['status', 'acknowledged_at', 'response_time_seconds', 'updated_at']

        if user:
            self.assigned_to = user
            update_fields.append('assigned_to')

        self.save(update_fields=update_fields)

    def complete(self) -> None:
        """Complete the request (fulfilled)."""
        if self.status not in [ServiceRequestStatus.PENDING, ServiceRequestStatus.IN_PROGRESS]:
            raise ValueError(f"Cannot complete request with status {self.status}")
        self.set_status(ServiceRequestStatus.COMPLETED, 'completed_at')

    def cancel(self, reason: str = None) -> None:
        """
        Cancel the request.

        Args:
            reason: Optional reason for cancellation
        """
        from django.utils import timezone

        if self.status in [ServiceRequestStatus.COMPLETED, ServiceRequestStatus.CANCELLED]:
            raise ValueError(f"Cannot cancel request with status {self.status}")

        self.status = ServiceRequestStatus.CANCELLED
        self.cancelled_at = timezone.now()
        if reason:
            self.cancel_reason = reason
        self.save(update_fields=['status', 'cancelled_at', 'cancel_reason', 'updated_at'])

    def assign_to(self, user) -> None:
        """
        Assign the request to a staff member.

        Args:
            user: User to assign the request to
        """
        self.assigned_to = user
        self.save(update_fields=['assigned_to', 'updated_at'])

    def set_priority(self, priority: int) -> None:
        """
        Set the request priority.

        Args:
            priority: Priority level 1-5 (1 is highest)

        Raises:
            ValueError: If priority is not between 1 and 5
        """
        if not 1 <= priority <= 5:
            raise ValueError("Priority must be between 1 and 5")
        self.priority = priority
        self.save(update_fields=['priority', 'updated_at'])

    def get_metadata(self, key: str, default=None):
        """
        Get a value from request metadata.

        Args:
            key: The metadata key to retrieve
            default: Default value if key not found

        Returns:
            The metadata value or default
        """
        return self.metadata.get(key, default)

    def set_metadata(self, key: str, value) -> None:
        """
        Set a value in request metadata.

        Args:
            key: The metadata key
            value: The value to set
        """
        self.metadata[key] = value
        self.save(update_fields=['metadata', 'updated_at'])
