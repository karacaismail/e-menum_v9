"""Django Admin configuration for the accounts app (support tickets)."""

from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from .support_models import SupportTicket, TicketComment, TicketStatus


class TicketCommentInline(admin.TabularInline):
    """Inline admin for ticket comments."""

    model = TicketComment
    extra = 1
    fields = ("author", "message", "is_internal", "created_at")
    readonly_fields = ("created_at",)
    ordering = ("created_at",)


@admin.register(SupportTicket)
class SupportTicketAdmin(admin.ModelAdmin):
    """
    Admin interface for managing support tickets (helpdesk).

    Platform admins use this to view, assign, and resolve tickets
    created by restaurant owners.
    """

    list_display = (
        "short_id",
        "subject",
        "organization_name",
        "status_badge",
        "priority_badge",
        "category",
        "assigned_to",
        "created_at",
    )
    list_filter = ("status", "priority", "category", "created_at")
    search_fields = (
        "subject",
        "description",
        "organization__name",
        "created_by__email",
    )
    list_editable = ("category",)
    readonly_fields = ("id", "created_by", "organization", "created_at", "updated_at")
    raw_id_fields = ("assigned_to",)
    inlines = [TicketCommentInline]
    ordering = ("-created_at",)
    list_per_page = 25

    fieldsets = (
        (
            None,
            {
                "fields": ("id", "subject", "description"),
            },
        ),
        (
            _("Tenant"),
            {
                "fields": ("organization", "created_by"),
            },
        ),
        (
            _("Status & Assignment"),
            {
                "fields": (
                    "status",
                    "priority",
                    "category",
                    "assigned_to",
                    "resolved_at",
                ),
            },
        ),
        (
            _("Metadata"),
            {
                "fields": ("metadata", "created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )

    def short_id(self, obj):
        return f"#{str(obj.id)[:8]}"

    short_id.short_description = _("ID")

    def organization_name(self, obj):
        return obj.organization.name if obj.organization else "-"

    organization_name.short_description = _("Organization")

    def status_badge(self, obj):
        colors = {
            TicketStatus.OPEN: "#3b82f6",
            TicketStatus.IN_PROGRESS: "#eab308",
            TicketStatus.RESOLVED: "#22c55e",
            TicketStatus.CLOSED: "#6b7280",
        }
        color = colors.get(obj.status, "#6b7280")
        return format_html(
            '<span style="background:{}; color:white; padding:2px 8px; '
            'border-radius:9999px; font-size:11px; font-weight:600;">{}</span>',
            color,
            obj.get_status_display(),
        )

    status_badge.short_description = _("Status")

    def priority_badge(self, obj):
        colors = {
            "LOW": "#9ca3af",
            "MEDIUM": "#3b82f6",
            "HIGH": "#f97316",
            "URGENT": "#ef4444",
        }
        color = colors.get(obj.priority, "#9ca3af")
        return format_html(
            '<span style="color:{}; font-weight:600; font-size:12px;">{}</span>',
            color,
            obj.get_priority_display(),
        )

    priority_badge.short_description = _("Priority")

    def get_queryset(self, request):
        """Include soft-deleted filter."""
        qs = super().get_queryset(request)
        return qs.filter(deleted_at__isnull=True).select_related(
            "organization",
            "created_by",
            "assigned_to",
        )

    def save_model(self, request, obj, form, change):
        """Auto-set resolved_at when status changes to RESOLVED."""
        if change and obj.status == TicketStatus.RESOLVED and not obj.resolved_at:
            from django.utils import timezone

            obj.resolved_at = timezone.now()
        super().save_model(request, obj, form, change)


@admin.register(TicketComment)
class TicketCommentAdmin(admin.ModelAdmin):
    """Admin interface for ticket comments (read-only listing)."""

    list_display = ("ticket", "author", "short_message", "is_internal", "created_at")
    list_filter = ("is_internal", "created_at")
    search_fields = ("message", "author__email", "ticket__subject")
    readonly_fields = ("ticket", "author", "created_at")
    ordering = ("-created_at",)
    list_per_page = 50

    def short_message(self, obj):
        return obj.message[:100] + "..." if len(obj.message) > 100 else obj.message

    short_message.short_description = _("Message")
