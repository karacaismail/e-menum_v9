"""
DRF serializers for the Campaigns application.

Provides serializers for all campaign models using the
TenantModelSerializer base class for automatic organization
handling and standard response format.
"""

from rest_framework import serializers

from shared.serializers.base import TenantModelSerializer

from apps.campaigns.models import (
    Campaign,
    Coupon,
    CouponUsage,
    Referral,
)


class CampaignSerializer(TenantModelSerializer):
    """Serializer for Campaign model."""

    is_running = serializers.BooleanField(read_only=True)
    budget_remaining = serializers.DecimalField(
        max_digits=12, decimal_places=2, read_only=True,
    )
    has_usage_remaining = serializers.BooleanField(read_only=True)
    created_by_email = serializers.CharField(
        source='created_by.email', read_only=True, default=None,
    )

    class Meta:
        model = Campaign
        fields = [
            'id', 'organization_id', 'name', 'campaign_type', 'status',
            'description', 'start_date', 'end_date', 'budget', 'spent_amount',
            'target_audience', 'discount_value', 'discount_type',
            'min_order_amount', 'max_discount_amount', 'usage_limit',
            'usage_count', 'is_active', 'created_by', 'created_by_email',
            'is_running', 'budget_remaining', 'has_usage_remaining',
            'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'organization_id', 'usage_count', 'spent_amount',
            'created_by', 'created_by_email', 'is_running',
            'budget_remaining', 'has_usage_remaining',
            'created_at', 'updated_at',
        ]


class CouponSerializer(TenantModelSerializer):
    """Serializer for Coupon model."""

    is_valid = serializers.BooleanField(read_only=True)
    campaign_name = serializers.CharField(
        source='campaign.name', read_only=True, default=None,
    )

    class Meta:
        model = Coupon
        fields = [
            'id', 'organization_id', 'campaign', 'campaign_name', 'code',
            'discount_value', 'discount_type', 'min_order_amount',
            'max_uses', 'used_count', 'valid_from', 'valid_until',
            'is_active', 'is_valid',
            'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'organization_id', 'used_count', 'is_valid',
            'created_at', 'updated_at',
        ]


class CouponUsageSerializer(TenantModelSerializer):
    """Serializer for CouponUsage model."""

    coupon_code = serializers.CharField(source='coupon.code', read_only=True)

    class Meta:
        model = CouponUsage
        fields = [
            'id', 'organization_id', 'coupon', 'coupon_code', 'order',
            'customer', 'discount_applied', 'used_at',
            'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'organization_id', 'used_at', 'created_at', 'updated_at',
        ]


class ReferralSerializer(TenantModelSerializer):
    """Serializer for Referral model."""

    class Meta:
        model = Referral
        fields = [
            'id', 'organization_id', 'referrer', 'referred',
            'referral_code', 'reward_type', 'reward_value',
            'is_completed', 'completed_at',
            'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'organization_id', 'created_at', 'updated_at',
        ]
