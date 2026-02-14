"""
Django ORM models for the Orders application.

This module defines the order-related models for E-Menum:
- Zone: Table groupings/sections within a restaurant (e.g., Garden, Indoor, VIP)
- Table: Physical restaurant tables with status tracking
- QRCode: Generated QR codes for menus/tables with scan analytics
- QRScan: QR code scan tracking for analytics (device info, geolocation)

Additional models to be added in subsequent subtasks:
- Order: Customer orders with full transaction details
- OrderItem: Individual line items within orders
- ServiceRequest: Waiter call/service requests from tables

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
from apps.orders.choices import QRCodeType, TableStatus


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
