"""
Dashboard admin configuration.

Registers DashboardInsight and UserPreference models
in Django admin with appropriate list displays and filters.
"""

from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from apps.dashboard.models import DashboardInsight, UserPreference
from shared.permissions.admin_permission_mixin import EMenumPermissionMixin


@admin.register(DashboardInsight)
class DashboardInsightAdmin(EMenumPermissionMixin, admin.ModelAdmin):
    """Admin configuration for DashboardInsight model."""

    list_display = [
        "title",
        "type",
        "priority",
        "is_active",
        "metric_value",
        "expires_at",
        "created_at",
    ]
    list_filter = ["type", "is_active", "created_at"]
    list_editable = ["priority", "is_active"]
    search_fields = ["title", "body"]
    ordering = ["-priority", "-created_at"]
    readonly_fields = ["id", "created_at", "updated_at"]
    list_per_page = 25

    fieldsets = (
        (
            None,
            {
                "fields": ("type", "title", "body", "priority", "is_active"),
            },
        ),
        (
            _("Action"),
            {
                "fields": ("action_label", "action_url"),
            },
        ),
        (
            _("Metric"),
            {
                "fields": ("metric_value", "metric_label"),
            },
        ),
        (
            _("Scheduling"),
            {
                "fields": ("expires_at",),
            },
        ),
        (
            _("System"),
            {
                "classes": ("collapse",),
                "fields": ("id", "created_at", "updated_at"),
            },
        ),
    )


@admin.register(UserPreference)
class UserPreferenceAdmin(EMenumPermissionMixin, admin.ModelAdmin):
    """Admin configuration for UserPreference model."""

    list_display = ["user", "key", "created_at", "updated_at"]
    list_filter = ["key", "created_at"]
    search_fields = ["user__username", "user__email", "key"]
    readonly_fields = ["id", "created_at", "updated_at"]
    raw_id_fields = ["user"]
