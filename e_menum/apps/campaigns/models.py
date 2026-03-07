"""
Django ORM models for the Campaigns application.

This module defines the campaign/promotion-related models for E-Menum:
- Campaign: Marketing campaigns with scheduling, budgeting, and targeting
- Coupon: Discount coupons with usage tracking
- CouponUsage: Audit trail for coupon redemptions
- Referral: Referral program tracking between customers

Critical Rules:
- Every query MUST include organization_id for tenant isolation
- All entities use soft delete (deleted_at timestamp) except CouponUsage
- No physical deletions allowed (use soft_delete method)
- CouponUsage records are append-only for audit integrity
"""

import uuid

from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.campaigns.choices import (
    CampaignStatus,
    CampaignType,
    DiscountType,
)
from apps.core.models import (
    Organization,
    SoftDeleteManager,
    SoftDeleteMixin,
    TimeStampedMixin,
)


class Campaign(TimeStampedMixin, SoftDeleteMixin, models.Model):
    """
    Campaign model - marketing campaigns with scheduling and targeting.

    Represents promotional campaigns with lifecycle management (draft,
    active, paused, completed, cancelled), budget tracking, discount
    configuration, and usage limits.

    Critical Rules:
    - EVERY query MUST filter by organization (multi-tenant isolation)
    - Use soft_delete() - never call delete() directly
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name=_("ID"),
        help_text=_("Unique identifier (UUID)"),
    )

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="campaigns",
        verbose_name=_("Organization"),
        help_text=_("Organization this campaign belongs to"),
    )

    name = models.CharField(
        max_length=255,
        verbose_name=_("Name"),
        help_text=_("Campaign name"),
    )

    campaign_type = models.CharField(
        max_length=20,
        choices=CampaignType.choices,
        verbose_name=_("Campaign type"),
        help_text=_("Type of marketing campaign"),
    )

    status = models.CharField(
        max_length=20,
        choices=CampaignStatus.choices,
        default=CampaignStatus.DRAFT,
        db_index=True,
        verbose_name=_("Status"),
        help_text=_("Current campaign status"),
    )

    description = models.TextField(
        blank=True,
        null=True,
        verbose_name=_("Description"),
        help_text=_("Campaign description"),
    )

    start_date = models.DateTimeField(
        verbose_name=_("Start date"),
        help_text=_("When the campaign starts"),
    )

    end_date = models.DateTimeField(
        verbose_name=_("End date"),
        help_text=_("When the campaign ends"),
    )

    budget = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name=_("Budget"),
        help_text=_("Total campaign budget"),
    )

    spent_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name=_("Spent amount"),
        help_text=_("Total amount spent/discounted so far"),
    )

    target_audience = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_("Target audience"),
        help_text=_("Targeting criteria (JSON)"),
    )

    discount_value = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name=_("Discount value"),
        help_text=_("Discount amount or percentage"),
    )

    discount_type = models.CharField(
        max_length=20,
        choices=DiscountType.choices,
        default=DiscountType.PERCENTAGE,
        verbose_name=_("Discount type"),
        help_text=_("How the discount is calculated"),
    )

    min_order_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name=_("Minimum order amount"),
        help_text=_("Minimum order amount to qualify"),
    )

    max_discount_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Maximum discount amount"),
        help_text=_("Cap on the discount amount (for percentage discounts)"),
    )

    usage_limit = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Usage limit"),
        help_text=_(
            "Maximum number of times this campaign can be used (0 = unlimited)"
        ),
    )

    usage_count = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Usage count"),
        help_text=_("Number of times this campaign has been used"),
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name=_("Is active"),
        help_text=_("Whether this campaign is enabled"),
    )

    created_by = models.ForeignKey(
        "core.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_campaigns",
        verbose_name=_("Created by"),
        help_text=_("User who created this campaign"),
    )

    # Managers
    objects = SoftDeleteManager()
    all_objects = models.Manager()

    class Meta:
        db_table = "campaigns"
        verbose_name = _("Campaign")
        verbose_name_plural = _("Campaigns")
        ordering = ["-start_date"]
        indexes = [
            models.Index(
                fields=["organization", "deleted_at"],
                name="campaign_org_deleted_idx",
            ),
            models.Index(
                fields=["organization", "status"],
                name="campaign_org_status_idx",
            ),
            models.Index(
                fields=["organization", "campaign_type"],
                name="campaign_org_type_idx",
            ),
            models.Index(
                fields=["start_date", "end_date"],
                name="campaign_date_range_idx",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.name} ({self.status})"

    def __repr__(self) -> str:
        return f"<Campaign(id={self.id}, name='{self.name}', status={self.status})>"

    @property
    def is_running(self) -> bool:
        """Check if campaign is currently running."""
        now = timezone.now()
        return (
            self.status == CampaignStatus.ACTIVE
            and self.start_date <= now <= self.end_date
            and not self.is_deleted
        )

    @property
    def budget_remaining(self):
        """Calculate remaining budget."""
        return self.budget - self.spent_amount

    @property
    def has_usage_remaining(self) -> bool:
        """Check if campaign has remaining uses."""
        if self.usage_limit == 0:
            return True  # Unlimited
        return self.usage_count < self.usage_limit


class Coupon(TimeStampedMixin, SoftDeleteMixin, models.Model):
    """
    Coupon model - discount coupons with usage tracking.

    Represents individual coupon codes that can be standalone or linked
    to a campaign. Tracks validity period and usage limits.

    Critical Rules:
    - EVERY query MUST filter by organization (multi-tenant isolation)
    - Coupon codes are unique within an organization
    - Use soft_delete() - never call delete() directly
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name=_("ID"),
        help_text=_("Unique identifier (UUID)"),
    )

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="coupons",
        verbose_name=_("Organization"),
        help_text=_("Organization this coupon belongs to"),
    )

    campaign = models.ForeignKey(
        Campaign,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="coupons",
        verbose_name=_("Campaign"),
        help_text=_("Campaign this coupon is linked to (optional)"),
    )

    code = models.CharField(
        max_length=50,
        verbose_name=_("Coupon code"),
        help_text=_("Unique coupon code within the organization"),
    )

    discount_value = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=_("Discount value"),
        help_text=_("Discount amount or percentage"),
    )

    discount_type = models.CharField(
        max_length=20,
        choices=DiscountType.choices,
        default=DiscountType.PERCENTAGE,
        verbose_name=_("Discount type"),
        help_text=_("How the discount is calculated"),
    )

    min_order_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name=_("Minimum order amount"),
        help_text=_("Minimum order amount to apply coupon"),
    )

    max_uses = models.PositiveIntegerField(
        default=1,
        verbose_name=_("Maximum uses"),
        help_text=_("Maximum number of times this coupon can be used"),
    )

    used_count = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Used count"),
        help_text=_("Number of times this coupon has been redeemed"),
    )

    valid_from = models.DateTimeField(
        verbose_name=_("Valid from"),
        help_text=_("When the coupon becomes valid"),
    )

    valid_until = models.DateTimeField(
        verbose_name=_("Valid until"),
        help_text=_("When the coupon expires"),
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name=_("Is active"),
        help_text=_("Whether this coupon is currently active"),
    )

    # Managers
    objects = SoftDeleteManager()
    all_objects = models.Manager()

    class Meta:
        db_table = "coupons"
        verbose_name = _("Coupon")
        verbose_name_plural = _("Coupons")
        ordering = ["-created_at"]
        unique_together = [["organization", "code"]]
        indexes = [
            models.Index(
                fields=["organization", "deleted_at"],
                name="coupon_org_deleted_idx",
            ),
            models.Index(
                fields=["organization", "code"],
                name="coupon_org_code_idx",
            ),
            models.Index(
                fields=["valid_from", "valid_until"],
                name="coupon_validity_idx",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.code} ({self.discount_value} {self.discount_type})"

    def __repr__(self) -> str:
        return f"<Coupon(id={self.id}, code='{self.code}')>"

    @property
    def is_valid(self) -> bool:
        """Check if coupon is currently valid and has uses remaining."""
        now = timezone.now()
        return (
            self.is_active
            and self.valid_from <= now <= self.valid_until
            and self.used_count < self.max_uses
            and not self.is_deleted
        )


class CouponUsage(TimeStampedMixin, models.Model):
    """
    CouponUsage model - audit trail for coupon redemptions.

    Records every coupon redemption with the order, customer, and
    discount amount applied. Append-only for audit integrity.

    Critical Rules:
    - EVERY query MUST filter by organization (multi-tenant isolation)
    - CouponUsage records are NEVER deleted (no soft delete)
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name=_("ID"),
        help_text=_("Unique identifier (UUID)"),
    )

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="coupon_usages",
        verbose_name=_("Organization"),
        help_text=_("Organization this usage belongs to"),
    )

    coupon = models.ForeignKey(
        Coupon,
        on_delete=models.CASCADE,
        related_name="usages",
        verbose_name=_("Coupon"),
        help_text=_("The coupon that was redeemed"),
    )

    order = models.ForeignKey(
        "orders.Order",
        on_delete=models.CASCADE,
        related_name="coupon_usages",
        verbose_name=_("Order"),
        help_text=_("The order where the coupon was applied"),
    )

    customer = models.ForeignKey(
        "customers.Customer",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="coupon_usages",
        verbose_name=_("Customer"),
        help_text=_("The customer who redeemed the coupon"),
    )

    discount_applied = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=_("Discount applied"),
        help_text=_("Actual discount amount applied to the order"),
    )

    used_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Used at"),
        help_text=_("When the coupon was redeemed"),
    )

    class Meta:
        db_table = "coupon_usages"
        verbose_name = _("Coupon Usage")
        verbose_name_plural = _("Coupon Usages")
        ordering = ["-used_at"]
        indexes = [
            models.Index(
                fields=["organization", "used_at"],
                name="couponusage_org_used_idx",
            ),
            models.Index(
                fields=["coupon", "used_at"],
                name="couponusage_coupon_used_idx",
            ),
        ]

    def __str__(self) -> str:
        return f"Coupon {self.coupon.code} used on order {self.order_id}"

    def __repr__(self) -> str:
        return f"<CouponUsage(id={self.id}, coupon='{self.coupon.code}')>"


class Referral(TimeStampedMixin, SoftDeleteMixin, models.Model):
    """
    Referral model - referral program tracking between customers.

    Tracks referrals between customers with reward configuration
    and completion status.

    Critical Rules:
    - EVERY query MUST filter by organization (multi-tenant isolation)
    - Use soft_delete() - never call delete() directly
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name=_("ID"),
        help_text=_("Unique identifier (UUID)"),
    )

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="referrals",
        verbose_name=_("Organization"),
        help_text=_("Organization this referral belongs to"),
    )

    referrer = models.ForeignKey(
        "customers.Customer",
        on_delete=models.CASCADE,
        related_name="referrals_made",
        verbose_name=_("Referrer"),
        help_text=_("Customer who made the referral"),
    )

    referred = models.ForeignKey(
        "customers.Customer",
        on_delete=models.CASCADE,
        related_name="referrals_received",
        verbose_name=_("Referred"),
        help_text=_("Customer who was referred"),
    )

    referral_code = models.CharField(
        max_length=50,
        verbose_name=_("Referral code"),
        help_text=_("Unique referral code used"),
    )

    reward_type = models.CharField(
        max_length=20,
        choices=DiscountType.choices,
        default=DiscountType.FIXED,
        verbose_name=_("Reward type"),
        help_text=_("How the referral reward is calculated"),
    )

    reward_value = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name=_("Reward value"),
        help_text=_("Value of the referral reward"),
    )

    is_completed = models.BooleanField(
        default=False,
        verbose_name=_("Is completed"),
        help_text=_("Whether the referral reward has been fulfilled"),
    )

    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Completed at"),
        help_text=_("When the referral was completed"),
    )

    # Managers
    objects = SoftDeleteManager()
    all_objects = models.Manager()

    class Meta:
        db_table = "referrals"
        verbose_name = _("Referral")
        verbose_name_plural = _("Referrals")
        ordering = ["-created_at"]
        indexes = [
            models.Index(
                fields=["organization", "deleted_at"],
                name="referral_org_deleted_idx",
            ),
            models.Index(
                fields=["organization", "referral_code"],
                name="referral_org_code_idx",
            ),
        ]

    def __str__(self) -> str:
        return f"Referral {self.referral_code} (completed={self.is_completed})"

    def __repr__(self) -> str:
        return f"<Referral(id={self.id}, code='{self.referral_code}')>"
