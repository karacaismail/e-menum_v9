"""
Django Admin configuration for the Notifications application.

This module defines admin interfaces for notification models:
- Notification

All admin classes implement multi-tenant filtering where applicable.
"""

from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from apps.notifications.choices import NotificationPriority, NotificationStatus
from apps.notifications.models import Notification
from shared.permissions.admin_permission_mixin import EMenumPermissionMixin


@admin.register(Notification)
class NotificationAdmin(EMenumPermissionMixin, admin.ModelAdmin):
    """Admin interface for Notification management."""

    list_display = [
        "title_display",
        "organization",
        "user_display",
        "notification_type",
        "status_display",
        "priority_display",
        "channel",
        "sent_at",
        "read_at",
        "created_at",
    ]
    list_filter = [
        "notification_type",
        "status",
        "priority",
        "channel",
        "organization",
        "created_at",
        "sent_at",
        "read_at",
    ]
    search_fields = [
        "title",
        "message",
        "user__email",
        "user__first_name",
        "user__last_name",
        "organization__name",
    ]
    readonly_fields = [
        "id",
        "sent_at",
        "delivered_at",
        "read_at",
        "created_at",
        "updated_at",
    ]
    ordering = ["-created_at"]
    date_hierarchy = "created_at"
    raw_id_fields = ["user", "organization"]

    fieldsets = (
        (None, {"fields": ("id", "organization", "user")}),
        (
            _("Notification Content"),
            {"fields": ("title", "message", "action_url", "image_url")},
        ),
        (
            _("Classification"),
            {"fields": ("notification_type", "status", "priority", "channel")},
        ),
        (
            _("Timing"),
            {
                "fields": (
                    "scheduled_for",
                    "expires_at",
                    "sent_at",
                    "delivered_at",
                    "read_at",
                )
            },
        ),
        (_("Data"), {"fields": ("data", "metadata"), "classes": ("collapse",)}),
        (
            _("Timestamps"),
            {
                "fields": ("created_at", "updated_at", "deleted_at"),
                "classes": ("collapse",),
            },
        ),
    )

    def get_queryset(self, request):
        """Filter out soft-deleted notifications."""
        qs = super().get_queryset(request)
        return qs.filter(deleted_at__isnull=True)

    @admin.display(description=_("Title"))
    def title_display(self, obj):
        """Display truncated title."""
        max_length = 50
        if len(obj.title) > max_length:
            return f"{obj.title[:max_length]}..."
        return obj.title

    @admin.display(description=_("User"))
    def user_display(self, obj):
        """Display the user email or full name."""
        if obj.user:
            return obj.user.email
        return "-"

    @admin.display(description=_("Status"))
    def status_display(self, obj):
        """Display status with color coding."""
        color_map = {
            NotificationStatus.PENDING: "#9CA3AF",  # Gray
            NotificationStatus.SENT: "#3B82F6",  # Blue
            NotificationStatus.DELIVERED: "#10B981",  # Green
            NotificationStatus.READ: "#22C55E",  # Bright Green
            NotificationStatus.ARCHIVED: "#6B7280",  # Dark Gray
            NotificationStatus.FAILED: "#EF4444",  # Red
        }
        color = color_map.get(obj.status, "#6B7280")
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display(),
        )

    @admin.display(description=_("Priority"))
    def priority_display(self, obj):
        """Display priority with color coding."""
        color_map = {
            NotificationPriority.LOW: "#9CA3AF",  # Gray
            NotificationPriority.NORMAL: "#3B82F6",  # Blue
            NotificationPriority.HIGH: "#F59E0B",  # Amber
            NotificationPriority.URGENT: "#EF4444",  # Red
        }
        color = color_map.get(obj.priority, "#6B7280")
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_priority_display(),
        )

    actions = ["mark_as_read", "mark_as_sent", "archive_notifications"]

    @admin.action(description=_("Mark selected notifications as read"))
    def mark_as_read(self, request, queryset):
        """Mark selected notifications as read."""
        from django.utils import timezone

        count = queryset.update(status=NotificationStatus.READ, read_at=timezone.now())
        self.message_user(request, _(f"{count} notification(s) marked as read."))

    @admin.action(description=_("Mark selected notifications as sent"))
    def mark_as_sent(self, request, queryset):
        """Mark selected notifications as sent."""
        from django.utils import timezone

        count = queryset.update(status=NotificationStatus.SENT, sent_at=timezone.now())
        self.message_user(request, _(f"{count} notification(s) marked as sent."))

    @admin.action(description=_("Archive selected notifications"))
    def archive_notifications(self, request, queryset):
        """Archive selected notifications."""
        count = queryset.update(status=NotificationStatus.ARCHIVED)
        self.message_user(request, _(f"{count} notification(s) archived."))
