"""
Django admin configuration for the Campaigns application.

Registers all campaign models with the Django admin site,
providing list displays, filters, and search capabilities.
"""

from django.contrib import admin

from apps.campaigns.models import (
    Campaign,
    Coupon,
    CouponUsage,
    Referral,
)
from shared.permissions.admin_permission_mixin import EMenumPermissionMixin


@admin.register(Campaign)
class CampaignAdmin(EMenumPermissionMixin, admin.ModelAdmin):
    list_display = [
        "name",
        "campaign_type",
        "status",
        "discount_value",
        "discount_type",
        "start_date",
        "end_date",
        "usage_count",
        "is_active",
        "organization",
    ]
    list_filter = [
        "status",
        "campaign_type",
        "discount_type",
        "is_active",
        "organization",
    ]
    search_fields = ["name", "description"]
    raw_id_fields = ["organization", "created_by"]
    readonly_fields = ["id", "created_at", "updated_at", "deleted_at"]


@admin.register(Coupon)
class CouponAdmin(EMenumPermissionMixin, admin.ModelAdmin):
    list_display = [
        "code",
        "campaign",
        "discount_value",
        "discount_type",
        "max_uses",
        "used_count",
        "valid_from",
        "valid_until",
        "is_active",
        "organization",
    ]
    list_filter = ["discount_type", "is_active", "organization"]
    search_fields = ["code"]
    raw_id_fields = ["organization", "campaign"]
    readonly_fields = ["id", "created_at", "updated_at", "deleted_at"]


@admin.register(CouponUsage)
class CouponUsageAdmin(EMenumPermissionMixin, admin.ModelAdmin):
    list_display = [
        "coupon",
        "order",
        "customer",
        "discount_applied",
        "used_at",
        "organization",
    ]
    list_filter = ["organization"]
    search_fields = ["coupon__code"]
    raw_id_fields = ["organization", "coupon", "order", "customer"]
    readonly_fields = ["id", "created_at", "updated_at"]


@admin.register(Referral)
class ReferralAdmin(EMenumPermissionMixin, admin.ModelAdmin):
    list_display = [
        "referral_code",
        "referrer",
        "referred",
        "reward_type",
        "reward_value",
        "is_completed",
        "completed_at",
        "organization",
    ]
    list_filter = ["is_completed", "reward_type", "organization"]
    search_fields = ["referral_code"]
    raw_id_fields = ["organization", "referrer", "referred"]
    readonly_fields = ["id", "created_at", "updated_at", "deleted_at"]
