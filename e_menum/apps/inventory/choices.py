"""
Enum choices for the Inventory application.

Provides standardized choices for:
- MovementType: Types of stock movements (purchase, sale, waste, etc.)
- StockLevel: Stock level classifications
- UnitType: Units of measurement for inventory items
- PurchaseOrderStatus: Lifecycle statuses for purchase orders
"""

from django.db import models
from django.utils.translation import gettext_lazy as _


class MovementType(models.TextChoices):
    """Types of inventory stock movements."""

    PURCHASE = "PURCHASE", _("Purchase")
    SALE = "SALE", _("Sale")
    WASTE = "WASTE", _("Waste")
    ADJUSTMENT = "ADJUSTMENT", _("Adjustment")
    TRANSFER = "TRANSFER", _("Transfer")
    RETURN = "RETURN", _("Return")


class StockLevel(models.TextChoices):
    """Stock level classifications for inventory monitoring."""

    CRITICAL = "CRITICAL", _("Critical")
    LOW = "LOW", _("Low")
    NORMAL = "NORMAL", _("Normal")
    EXCESS = "EXCESS", _("Excess")


class UnitType(models.TextChoices):
    """Units of measurement for inventory items."""

    KG = "KG", _("Kilogram")
    G = "G", _("Gram")
    L = "L", _("Liter")
    ML = "ML", _("Milliliter")
    PIECE = "PIECE", _("Piece")
    PACK = "PACK", _("Pack")
    BOX = "BOX", _("Box")


class PurchaseOrderStatus(models.TextChoices):
    """Lifecycle statuses for purchase orders."""

    DRAFT = "DRAFT", _("Draft")
    SUBMITTED = "SUBMITTED", _("Submitted")
    APPROVED = "APPROVED", _("Approved")
    RECEIVED = "RECEIVED", _("Received")
    CANCELLED = "CANCELLED", _("Cancelled")
