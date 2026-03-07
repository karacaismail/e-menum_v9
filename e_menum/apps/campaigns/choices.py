"""
Enum choices for the Campaigns application.

Provides standardized choices for:
- CampaignType: Types of marketing campaigns
- CampaignStatus: Lifecycle statuses for campaigns
- DiscountType: How discounts are calculated (percentage vs fixed)
- DiscountScope: What the discount applies to
- CouponStatus: Lifecycle statuses for coupons
"""

from django.db import models
from django.utils.translation import gettext_lazy as _


class CampaignType(models.TextChoices):
    """Types of marketing campaigns."""

    DISCOUNT = "DISCOUNT", _("Discount")
    BOGO = "BOGO", _("Buy One Get One")
    FREE_ITEM = "FREE_ITEM", _("Free Item")
    BUNDLE = "BUNDLE", _("Bundle Deal")
    LOYALTY = "LOYALTY", _("Loyalty Reward")
    SEASONAL = "SEASONAL", _("Seasonal Promotion")
    FLASH_SALE = "FLASH_SALE", _("Flash Sale")
    REFERRAL = "REFERRAL", _("Referral Program")


class CampaignStatus(models.TextChoices):
    """Lifecycle statuses for campaigns."""

    DRAFT = "DRAFT", _("Draft")
    ACTIVE = "ACTIVE", _("Active")
    PAUSED = "PAUSED", _("Paused")
    COMPLETED = "COMPLETED", _("Completed")
    CANCELLED = "CANCELLED", _("Cancelled")


class DiscountType(models.TextChoices):
    """How discounts are calculated."""

    PERCENTAGE = "PERCENTAGE", _("Percentage")
    FIXED = "FIXED", _("Fixed Amount")


class DiscountScope(models.TextChoices):
    """What the discount applies to."""

    ORDER = "ORDER", _("Entire Order")
    PRODUCT = "PRODUCT", _("Specific Product")
    CATEGORY = "CATEGORY", _("Product Category")


class CouponStatus(models.TextChoices):
    """Lifecycle statuses for coupons."""

    ACTIVE = "ACTIVE", _("Active")
    USED = "USED", _("Used")
    EXPIRED = "EXPIRED", _("Expired")
    CANCELLED = "CANCELLED", _("Cancelled")
