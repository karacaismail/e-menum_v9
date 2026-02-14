"""
Django ORM models for the Orders application.

This module defines the order-related models for E-Menum:
- Zone: Table groupings/sections within a restaurant (e.g., Garden, Indoor, VIP)
- Table: Physical restaurant tables with status tracking

Additional models to be added in subsequent subtasks:
- QRCode: Generated QR codes for menus/tables
- QRScan: QR code scan tracking for analytics
- Order: Customer orders with full transaction details
- OrderItem: Individual line items within orders
- ServiceRequest: Waiter call/service requests from tables

Critical Rules:
- Every query MUST include organization_id for tenant isolation
- All entities use soft delete (deleted_at timestamp)
- No physical deletions allowed (use soft_delete method)
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
from apps.orders.choices import TableStatus


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
