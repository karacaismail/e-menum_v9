"""
Django ORM models for the Inventory application.

This module defines the inventory-related models for E-Menum:
- Supplier: Vendor/supplier information for procurement
- InventoryItem: Tracked inventory items with stock levels
- StockMovement: Audit trail for all stock changes
- PurchaseOrder: Purchase orders to suppliers
- PurchaseOrderItem: Line items within purchase orders
- Recipe: Recipes linking menu products to inventory ingredients
- RecipeIngredient: Individual ingredients within a recipe

Critical Rules:
- Every query MUST include organization_id for tenant isolation
- All entities use soft delete (deleted_at timestamp)
- No physical deletions allowed (use soft_delete method)
"""

import uuid

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.models import (
    Organization,
    SoftDeleteManager,
    SoftDeleteMixin,
    TimeStampedMixin,
)
from apps.inventory.choices import (
    MovementType,
    PurchaseOrderStatus,
    UnitType,
)


class Supplier(TimeStampedMixin, SoftDeleteMixin, models.Model):
    """
    Supplier model - vendor information for inventory procurement.

    Tracks supplier details including contact information, tax ID,
    rating, and activity status for procurement workflows.

    Critical Rules:
    - EVERY query MUST filter by organization (multi-tenant isolation)
    - Use soft_delete() - never call delete() directly
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name=_('ID'),
        help_text=_('Unique identifier (UUID)'),
    )

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='suppliers',
        verbose_name=_('Organization'),
        help_text=_('Organization this supplier belongs to'),
    )

    name = models.CharField(
        max_length=255,
        verbose_name=_('Name'),
        help_text=_('Supplier company name'),
    )

    contact_person = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name=_('Contact person'),
        help_text=_('Primary contact person at the supplier'),
    )

    email = models.EmailField(
        blank=True,
        null=True,
        verbose_name=_('Email'),
        help_text=_('Supplier contact email'),
    )

    phone = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name=_('Phone'),
        help_text=_('Supplier contact phone'),
    )

    address = models.TextField(
        blank=True,
        null=True,
        verbose_name=_('Address'),
        help_text=_('Supplier full address'),
    )

    tax_id = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name=_('Tax ID'),
        help_text=_('Supplier tax identification number'),
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name=_('Is active'),
        help_text=_('Whether this supplier is currently active'),
    )

    rating = models.PositiveSmallIntegerField(
        default=3,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name=_('Rating'),
        help_text=_('Supplier rating from 1 to 5'),
    )

    notes = models.TextField(
        blank=True,
        null=True,
        verbose_name=_('Notes'),
        help_text=_('Additional notes about the supplier'),
    )

    # Managers
    objects = SoftDeleteManager()
    all_objects = models.Manager()

    class Meta:
        db_table = 'suppliers'
        verbose_name = _('Supplier')
        verbose_name_plural = _('Suppliers')
        ordering = ['name']
        indexes = [
            models.Index(
                fields=['organization', 'deleted_at'],
                name='supplier_org_deleted_idx',
            ),
            models.Index(
                fields=['organization', 'is_active'],
                name='supplier_org_active_idx',
            ),
        ]

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return f"<Supplier(id={self.id}, name='{self.name}')>"


class InventoryItem(TimeStampedMixin, SoftDeleteMixin, models.Model):
    """
    InventoryItem model - tracked inventory items with stock levels.

    Represents raw materials, ingredients, or consumables tracked in
    the inventory system. Each item has current stock, min/max levels,
    cost per unit, and an optional supplier link.

    Critical Rules:
    - EVERY query MUST filter by organization (multi-tenant isolation)
    - Use soft_delete() - never call delete() directly
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name=_('ID'),
        help_text=_('Unique identifier (UUID)'),
    )

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='inventory_items',
        verbose_name=_('Organization'),
        help_text=_('Organization this inventory item belongs to'),
    )

    name = models.CharField(
        max_length=255,
        verbose_name=_('Name'),
        help_text=_('Name of the inventory item'),
    )

    sku = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name=_('SKU'),
        help_text=_('Stock Keeping Unit code'),
    )

    category = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name=_('Category'),
        help_text=_('Item category (e.g., Dairy, Produce, Meat)'),
    )

    unit_type = models.CharField(
        max_length=10,
        choices=UnitType.choices,
        default=UnitType.PIECE,
        verbose_name=_('Unit type'),
        help_text=_('Unit of measurement for this item'),
    )

    current_stock = models.DecimalField(
        max_digits=12,
        decimal_places=3,
        default=0,
        verbose_name=_('Current stock'),
        help_text=_('Current stock quantity in the specified unit'),
    )

    min_stock_level = models.DecimalField(
        max_digits=12,
        decimal_places=3,
        default=0,
        verbose_name=_('Minimum stock level'),
        help_text=_('Minimum stock threshold before alert'),
    )

    max_stock_level = models.DecimalField(
        max_digits=12,
        decimal_places=3,
        default=0,
        verbose_name=_('Maximum stock level'),
        help_text=_('Maximum recommended stock level'),
    )

    cost_per_unit = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name=_('Cost per unit'),
        help_text=_('Cost per unit in the base currency'),
    )

    supplier = models.ForeignKey(
        Supplier,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='inventory_items',
        verbose_name=_('Supplier'),
        help_text=_('Primary supplier for this item'),
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name=_('Is active'),
        help_text=_('Whether this inventory item is actively tracked'),
    )

    # Managers
    objects = SoftDeleteManager()
    all_objects = models.Manager()

    class Meta:
        db_table = 'inventory_items'
        verbose_name = _('Inventory Item')
        verbose_name_plural = _('Inventory Items')
        ordering = ['name']
        indexes = [
            models.Index(
                fields=['organization', 'deleted_at'],
                name='invitem_org_deleted_idx',
            ),
            models.Index(
                fields=['organization', 'is_active'],
                name='invitem_org_active_idx',
            ),
            models.Index(
                fields=['organization', 'category'],
                name='invitem_org_category_idx',
            ),
            models.Index(
                fields=['organization', 'sku'],
                name='invitem_org_sku_idx',
            ),
        ]

    def __str__(self) -> str:
        return f"{self.name} ({self.current_stock} {self.unit_type})"

    def __repr__(self) -> str:
        return f"<InventoryItem(id={self.id}, name='{self.name}', stock={self.current_stock})>"

    @property
    def stock_value(self):
        """Calculate total value of current stock."""
        return self.current_stock * self.cost_per_unit

    @property
    def is_low_stock(self) -> bool:
        """Check if stock is below minimum level."""
        return self.current_stock <= self.min_stock_level

    @property
    def is_excess_stock(self) -> bool:
        """Check if stock exceeds maximum level."""
        if self.max_stock_level <= 0:
            return False
        return self.current_stock > self.max_stock_level


class StockMovement(TimeStampedMixin, SoftDeleteMixin, models.Model):
    """
    StockMovement model - audit trail for all inventory stock changes.

    Records every stock change (purchase, sale, waste, adjustment,
    transfer, return) with quantity, cost, and reference information.

    Critical Rules:
    - EVERY query MUST filter by organization (multi-tenant isolation)
    - Use soft_delete() - never call delete() directly
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name=_('ID'),
        help_text=_('Unique identifier (UUID)'),
    )

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='stock_movements',
        verbose_name=_('Organization'),
        help_text=_('Organization this movement belongs to'),
    )

    inventory_item = models.ForeignKey(
        InventoryItem,
        on_delete=models.CASCADE,
        related_name='movements',
        verbose_name=_('Inventory item'),
        help_text=_('The inventory item affected by this movement'),
    )

    movement_type = models.CharField(
        max_length=20,
        choices=MovementType.choices,
        verbose_name=_('Movement type'),
        help_text=_('Type of stock movement'),
    )

    quantity = models.DecimalField(
        max_digits=12,
        decimal_places=3,
        verbose_name=_('Quantity'),
        help_text=_('Quantity moved (positive for additions, negative for removals)'),
    )

    unit_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name=_('Unit cost'),
        help_text=_('Cost per unit at the time of movement'),
    )

    total_cost = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name=_('Total cost'),
        help_text=_('Total cost of this movement'),
    )

    reference_number = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name=_('Reference number'),
        help_text=_('External reference number (invoice, PO, etc.)'),
    )

    notes = models.TextField(
        blank=True,
        null=True,
        verbose_name=_('Notes'),
        help_text=_('Additional notes about this movement'),
    )

    created_by = models.ForeignKey(
        'core.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='stock_movements',
        verbose_name=_('Created by'),
        help_text=_('User who created this movement'),
    )

    # Managers
    objects = SoftDeleteManager()
    all_objects = models.Manager()

    class Meta:
        db_table = 'stock_movements'
        verbose_name = _('Stock Movement')
        verbose_name_plural = _('Stock Movements')
        ordering = ['-created_at']
        indexes = [
            models.Index(
                fields=['organization', 'deleted_at'],
                name='stockmov_org_deleted_idx',
            ),
            models.Index(
                fields=['organization', 'movement_type'],
                name='stockmov_org_type_idx',
            ),
            models.Index(
                fields=['inventory_item', 'created_at'],
                name='stockmov_item_created_idx',
            ),
        ]

    def __str__(self) -> str:
        return f"{self.movement_type}: {self.quantity} of {self.inventory_item.name}"

    def __repr__(self) -> str:
        return (
            f"<StockMovement(id={self.id}, type={self.movement_type}, "
            f"qty={self.quantity})>"
        )


class PurchaseOrder(TimeStampedMixin, SoftDeleteMixin, models.Model):
    """
    PurchaseOrder model - purchase orders to suppliers.

    Represents procurement orders with lifecycle tracking (draft,
    submitted, approved, received, cancelled), financial totals,
    and audit trail.

    Critical Rules:
    - EVERY query MUST filter by organization (multi-tenant isolation)
    - Use soft_delete() - never call delete() directly
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name=_('ID'),
        help_text=_('Unique identifier (UUID)'),
    )

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='purchase_orders',
        verbose_name=_('Organization'),
        help_text=_('Organization this purchase order belongs to'),
    )

    supplier = models.ForeignKey(
        Supplier,
        on_delete=models.CASCADE,
        related_name='purchase_orders',
        verbose_name=_('Supplier'),
        help_text=_('Supplier for this purchase order'),
    )

    order_number = models.CharField(
        max_length=50,
        verbose_name=_('Order number'),
        help_text=_('Unique order reference number'),
    )

    status = models.CharField(
        max_length=20,
        choices=PurchaseOrderStatus.choices,
        default=PurchaseOrderStatus.DRAFT,
        db_index=True,
        verbose_name=_('Status'),
        help_text=_('Current status of the purchase order'),
    )

    order_date = models.DateField(
        verbose_name=_('Order date'),
        help_text=_('Date the order was placed'),
    )

    expected_delivery = models.DateField(
        blank=True,
        null=True,
        verbose_name=_('Expected delivery'),
        help_text=_('Expected delivery date'),
    )

    actual_delivery = models.DateField(
        blank=True,
        null=True,
        verbose_name=_('Actual delivery'),
        help_text=_('Actual delivery date'),
    )

    subtotal = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name=_('Subtotal'),
        help_text=_('Total before tax'),
    )

    tax_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name=_('Tax amount'),
        help_text=_('Total tax amount'),
    )

    total_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name=_('Total amount'),
        help_text=_('Total order amount including tax'),
    )

    notes = models.TextField(
        blank=True,
        null=True,
        verbose_name=_('Notes'),
        help_text=_('Additional notes for this purchase order'),
    )

    created_by = models.ForeignKey(
        'core.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_purchase_orders',
        verbose_name=_('Created by'),
        help_text=_('User who created this purchase order'),
    )

    approved_by = models.ForeignKey(
        'core.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_purchase_orders',
        verbose_name=_('Approved by'),
        help_text=_('User who approved this purchase order'),
    )

    # Managers
    objects = SoftDeleteManager()
    all_objects = models.Manager()

    class Meta:
        db_table = 'purchase_orders'
        verbose_name = _('Purchase Order')
        verbose_name_plural = _('Purchase Orders')
        ordering = ['-order_date']
        indexes = [
            models.Index(
                fields=['organization', 'deleted_at'],
                name='po_org_deleted_idx',
            ),
            models.Index(
                fields=['organization', 'status'],
                name='po_org_status_idx',
            ),
            models.Index(
                fields=['organization', 'supplier'],
                name='po_org_supplier_idx',
            ),
        ]

    def __str__(self) -> str:
        return f"PO-{self.order_number} ({self.status})"

    def __repr__(self) -> str:
        return f"<PurchaseOrder(id={self.id}, number='{self.order_number}', status={self.status})>"


class PurchaseOrderItem(TimeStampedMixin, SoftDeleteMixin, models.Model):
    """
    PurchaseOrderItem model - line items within purchase orders.

    Tracks ordered and received quantities with cost per unit for
    each inventory item in a purchase order.

    Critical Rules:
    - EVERY query MUST filter by organization via purchase_order
    - Use soft_delete() - never call delete() directly
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name=_('ID'),
        help_text=_('Unique identifier (UUID)'),
    )

    purchase_order = models.ForeignKey(
        PurchaseOrder,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name=_('Purchase order'),
        help_text=_('Parent purchase order'),
    )

    inventory_item = models.ForeignKey(
        InventoryItem,
        on_delete=models.CASCADE,
        related_name='purchase_order_items',
        verbose_name=_('Inventory item'),
        help_text=_('The inventory item being ordered'),
    )

    quantity_ordered = models.DecimalField(
        max_digits=12,
        decimal_places=3,
        verbose_name=_('Quantity ordered'),
        help_text=_('Quantity ordered from supplier'),
    )

    quantity_received = models.DecimalField(
        max_digits=12,
        decimal_places=3,
        default=0,
        verbose_name=_('Quantity received'),
        help_text=_('Quantity actually received'),
    )

    unit_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=_('Unit cost'),
        help_text=_('Cost per unit'),
    )

    total_cost = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name=_('Total cost'),
        help_text=_('Total line item cost'),
    )

    # Managers
    objects = SoftDeleteManager()
    all_objects = models.Manager()

    class Meta:
        db_table = 'purchase_order_items'
        verbose_name = _('Purchase Order Item')
        verbose_name_plural = _('Purchase Order Items')
        ordering = ['id']
        indexes = [
            models.Index(
                fields=['purchase_order'],
                name='poitem_po_idx',
            ),
        ]

    def __str__(self) -> str:
        return f"{self.inventory_item.name} x {self.quantity_ordered}"

    def __repr__(self) -> str:
        return (
            f"<PurchaseOrderItem(id={self.id}, item='{self.inventory_item.name}', "
            f"qty={self.quantity_ordered})>"
        )


class Recipe(TimeStampedMixin, SoftDeleteMixin, models.Model):
    """
    Recipe model - recipes linking menu products to inventory ingredients.

    Defines how much of each inventory item is needed to produce a
    menu product. Used for cost calculation and inventory deductions.

    Critical Rules:
    - EVERY query MUST filter by organization (multi-tenant isolation)
    - Use soft_delete() - never call delete() directly
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name=_('ID'),
        help_text=_('Unique identifier (UUID)'),
    )

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='recipes',
        verbose_name=_('Organization'),
        help_text=_('Organization this recipe belongs to'),
    )

    product = models.ForeignKey(
        'menu.Product',
        on_delete=models.CASCADE,
        related_name='recipes',
        verbose_name=_('Product'),
        help_text=_('Menu product this recipe produces'),
    )

    name = models.CharField(
        max_length=255,
        verbose_name=_('Name'),
        help_text=_('Recipe name'),
    )

    description = models.TextField(
        blank=True,
        null=True,
        verbose_name=_('Description'),
        help_text=_('Recipe description or preparation instructions'),
    )

    yield_quantity = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        default=1,
        verbose_name=_('Yield quantity'),
        help_text=_('Number of portions/units this recipe produces'),
    )

    yield_unit = models.CharField(
        max_length=10,
        choices=UnitType.choices,
        default=UnitType.PIECE,
        verbose_name=_('Yield unit'),
        help_text=_('Unit of measurement for the yield'),
    )

    preparation_time_minutes = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Preparation time (minutes)'),
        help_text=_('Estimated preparation time in minutes'),
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name=_('Is active'),
        help_text=_('Whether this recipe is currently in use'),
    )

    # Managers
    objects = SoftDeleteManager()
    all_objects = models.Manager()

    class Meta:
        db_table = 'recipes'
        verbose_name = _('Recipe')
        verbose_name_plural = _('Recipes')
        ordering = ['name']
        indexes = [
            models.Index(
                fields=['organization', 'deleted_at'],
                name='recipe_org_deleted_idx',
            ),
            models.Index(
                fields=['organization', 'product'],
                name='recipe_org_product_idx',
            ),
        ]

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return f"<Recipe(id={self.id}, name='{self.name}')>"


class RecipeIngredient(TimeStampedMixin, SoftDeleteMixin, models.Model):
    """
    RecipeIngredient model - individual ingredients within a recipe.

    Links a recipe to specific inventory items with the required
    quantity and waste percentage for cost and stock calculations.

    Critical Rules:
    - EVERY query MUST filter by organization via recipe
    - Use soft_delete() - never call delete() directly
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name=_('ID'),
        help_text=_('Unique identifier (UUID)'),
    )

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='ingredients',
        verbose_name=_('Recipe'),
        help_text=_('Parent recipe'),
    )

    inventory_item = models.ForeignKey(
        InventoryItem,
        on_delete=models.CASCADE,
        related_name='recipe_ingredients',
        verbose_name=_('Inventory item'),
        help_text=_('The inventory item used as ingredient'),
    )

    quantity_required = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        verbose_name=_('Quantity required'),
        help_text=_('Amount of this ingredient required per recipe yield'),
    )

    unit_type = models.CharField(
        max_length=10,
        choices=UnitType.choices,
        default=UnitType.G,
        verbose_name=_('Unit type'),
        help_text=_('Unit of measurement for this ingredient'),
    )

    waste_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name=_('Waste percentage'),
        help_text=_('Expected waste percentage (0-100)'),
    )

    # Managers
    objects = SoftDeleteManager()
    all_objects = models.Manager()

    class Meta:
        db_table = 'recipe_ingredients'
        verbose_name = _('Recipe Ingredient')
        verbose_name_plural = _('Recipe Ingredients')
        ordering = ['id']
        indexes = [
            models.Index(
                fields=['recipe'],
                name='recipeing_recipe_idx',
            ),
        ]

    def __str__(self) -> str:
        return f"{self.inventory_item.name}: {self.quantity_required} {self.unit_type}"

    def __repr__(self) -> str:
        return (
            f"<RecipeIngredient(id={self.id}, item='{self.inventory_item.name}', "
            f"qty={self.quantity_required})>"
        )

    @property
    def effective_quantity(self):
        """Calculate quantity needed including waste."""
        waste_multiplier = 1 + (self.waste_percentage / 100)
        return self.quantity_required * waste_multiplier
