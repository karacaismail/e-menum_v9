"""
Django Admin configuration for the SEO Shield application.

This module defines admin interfaces for security models:
- BotWhitelist: Known legitimate bot definitions and verification
- IPRiskScore: Per-IP risk assessment and tracking
- RuleSet: Configurable security rule definitions
- BlockLog: Audit trail of shield actions taken

All admin classes implement:
- Rich display with color-coded badges and visual indicators
- Custom actions for IP management (whitelist/blacklist)
- Read-only BlockLog for audit compliance
- Dark theme compatible styling
"""

from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from apps.seo_shield.models import BlockLog, BotWhitelist, IPRiskScore, RuleSet
from shared.permissions.admin_permission_mixin import EMenumPermissionMixin


# =============================================================================
# HELPER UTILITIES
# =============================================================================


def _hex_to_rgb(hex_color: str) -> str:
    """Convert hex color to comma-separated RGB values for rgba() usage."""
    hex_color = hex_color.lstrip("#")
    r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
    return f"{r}, {g}, {b}"


# Color maps
ACTION_COLORS = {
    RuleSet.Action.BLOCK: "#ef4444",  # Red
    RuleSet.Action.CHALLENGE: "#f59e0b",  # Amber
    RuleSet.Action.LOG: "#3b82f6",  # Blue
    RuleSet.Action.THROTTLE: "#8b5cf6",  # Purple
}

BLOCK_ACTION_COLORS = {
    BlockLog.ActionTaken.BLOCKED: "#ef4444",
    BlockLog.ActionTaken.CHALLENGED: "#f59e0b",
    BlockLog.ActionTaken.THROTTLED: "#8b5cf6",
    BlockLog.ActionTaken.LOGGED: "#3b82f6",
}

VERIFICATION_COLORS = {
    BotWhitelist.VerificationMethod.DNS: "#22c55e",
    BotWhitelist.VerificationMethod.IP_RANGE: "#3b82f6",
    BotWhitelist.VerificationMethod.USER_AGENT: "#f59e0b",
}


# =============================================================================
# BOT WHITELIST ADMIN
# =============================================================================


@admin.register(BotWhitelist)
class BotWhitelistAdmin(EMenumPermissionMixin, admin.ModelAdmin):
    """
    Admin interface for BotWhitelist management.

    Manages known legitimate bot definitions (Googlebot, Bingbot, etc.)
    with configurable verification methods (DNS, IP range, User-Agent).
    """

    list_display = [
        "name_display",
        "verification_method_badge",
        "dns_domain_display",
        "is_active_badge",
        "last_verified",
    ]
    list_filter = ["verification_method", "is_active"]
    search_fields = ["name", "dns_domain", "user_agent_pattern"]
    readonly_fields = ["id", "last_verified", "created_at", "updated_at"]
    ordering = ["name"]
    list_per_page = 30

    fieldsets = (
        (None, {"fields": ("id", "name", "user_agent_pattern", "is_active")}),
        (
            _("Verification"),
            {
                "fields": ("verification_method", "dns_domain", "ip_ranges"),
                "description": _(
                    "DNS: Reverse DNS lookup + forward DNS confirmation. "
                    "IP Range: CIDR block matching. "
                    "User-Agent: Pattern matching only."
                ),
            },
        ),
        (
            _("Status"),
            {
                "fields": ("last_verified",),
            },
        ),
        (
            _("Timestamps"),
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    def name_display(self, obj):
        """Bot name with icon."""
        return format_html(
            '<span style="display:inline-flex;align-items:center;gap:4px;'
            'font-weight:600;color:#e2e8f0;">'
            '<i class="ph ph-robot"></i> {}</span>',
            obj.name,
        )

    name_display.short_description = _("Bot Name")
    name_display.admin_order_field = "name"

    def verification_method_badge(self, obj):
        """Color-coded verification method badge."""
        color = VERIFICATION_COLORS.get(obj.verification_method, "#94a3b8")
        icons = {
            BotWhitelist.VerificationMethod.DNS: "globe",
            BotWhitelist.VerificationMethod.IP_RANGE: "map-pin",
            BotWhitelist.VerificationMethod.USER_AGENT: "identification-card",
        }
        icon = icons.get(obj.verification_method, "question")
        return format_html(
            '<span style="display:inline-flex;align-items:center;gap:3px;'
            "padding:2px 8px;border-radius:4px;font-size:11px;font-weight:600;"
            'background:rgba({},0.12);color:{};">'
            '<i class="ph ph-{}"></i> {}</span>',
            _hex_to_rgb(color),
            color,
            icon,
            obj.get_verification_method_display(),
        )

    verification_method_badge.short_description = _("Method")
    verification_method_badge.admin_order_field = "verification_method"

    def dns_domain_display(self, obj):
        """DNS domain in code style."""
        if not obj.dns_domain:
            return format_html('<span style="color:#6b7280;">—</span>')
        return format_html(
            '<code style="background:rgba(99,102,241,0.08);color:#a5b4fc;'
            'padding:2px 8px;border-radius:4px;font-size:11px;">{}</code>',
            obj.dns_domain,
        )

    dns_domain_display.short_description = _("DNS Domain")
    dns_domain_display.admin_order_field = "dns_domain"

    def is_active_badge(self, obj):
        """Active status badge."""
        if obj.is_active:
            return format_html(
                '<span style="color:#22c55e;">'
                '<i class="ph-fill ph-check-circle"></i> Active</span>'
            )
        return format_html(
            '<span style="color:#6b7280;">'
            '<i class="ph ph-x-circle"></i> Inactive</span>'
        )

    is_active_badge.short_description = _("Active")
    is_active_badge.admin_order_field = "is_active"


# =============================================================================
# IP RISK SCORE ADMIN
# =============================================================================


@admin.register(IPRiskScore)
class IPRiskScoreAdmin(EMenumPermissionMixin, admin.ModelAdmin):
    """
    Admin interface for IPRiskScore management.

    Displays per-IP risk assessments with signal breakdowns, request
    counters, and whitelist/blacklist status. Supports bulk IP management.
    """

    list_display = [
        "ip_address_display",
        "risk_score_badge",
        "total_requests",
        "blocked_requests",
        "is_whitelisted_badge",
        "is_blacklisted_badge",
        "country_code_display",
        "last_seen",
    ]
    list_filter = ["is_whitelisted", "is_blacklisted"]
    search_fields = ["ip_address", "notes", "asn"]
    readonly_fields = [
        "id",
        "first_seen",
        "last_seen",
        "created_at",
        "updated_at",
    ]
    ordering = ["-risk_score"]
    list_per_page = 50

    fieldsets = (
        (None, {"fields": ("id", "ip_address", "risk_score")}),
        (
            _("Signals"),
            {
                "fields": ("signals",),
                "description": _(
                    "Signal breakdown: {rate_limit: 0-100, header_anomaly: 0-100, "
                    "path_pattern: 0-100, ua_anomaly: 0-100, robots_violation: 0-100}"
                ),
            },
        ),
        (
            _("Request Counters"),
            {
                "fields": ("total_requests", "blocked_requests"),
            },
        ),
        (
            _("Status"),
            {
                "fields": ("is_whitelisted", "is_blacklisted"),
            },
        ),
        (
            _("Geo & Network"),
            {
                "fields": ("country_code", "asn"),
            },
        ),
        (
            _("Timeline"),
            {
                "fields": ("first_seen", "last_seen"),
            },
        ),
        (
            _("Notes"),
            {
                "fields": ("notes",),
            },
        ),
        (
            _("Timestamps"),
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    def ip_address_display(self, obj):
        """IP address in monospace."""
        return format_html(
            '<code style="background:rgba(99,102,241,0.08);color:#a5b4fc;'
            'padding:2px 8px;border-radius:4px;font-size:12px;font-weight:600;">{}</code>',
            obj.ip_address,
        )

    ip_address_display.short_description = _("IP Address")
    ip_address_display.admin_order_field = "ip_address"

    def risk_score_badge(self, obj):
        """
        Color-coded risk score badge.

        Green for < 30, yellow for < 60, red for >= 60.
        """
        score = obj.risk_score
        if score >= 60:
            color = "#ef4444"
            icon = "warning"
        elif score >= 30:
            color = "#f59e0b"
            icon = "warning-circle"
        else:
            color = "#22c55e"
            icon = "check-circle"
        return format_html(
            '<span style="display:inline-flex;align-items:center;gap:3px;'
            "padding:2px 8px;border-radius:4px;font-size:11px;font-weight:700;"
            'background:rgba({},0.12);color:{};">'
            '<i class="ph ph-{}"></i> {}/100</span>',
            _hex_to_rgb(color),
            color,
            icon,
            score,
        )

    risk_score_badge.short_description = _("Risk Score")
    risk_score_badge.admin_order_field = "risk_score"

    def is_whitelisted_badge(self, obj):
        """Whitelisted status badge."""
        if obj.is_whitelisted:
            return format_html(
                '<span style="color:#22c55e;font-size:11px;">'
                '<i class="ph-fill ph-shield-check"></i> Yes</span>'
            )
        return format_html('<span style="color:#6b7280;font-size:11px;">—</span>')

    is_whitelisted_badge.short_description = _("Whitelisted")
    is_whitelisted_badge.admin_order_field = "is_whitelisted"

    def is_blacklisted_badge(self, obj):
        """Blacklisted status badge."""
        if obj.is_blacklisted:
            return format_html(
                '<span style="color:#ef4444;font-size:11px;">'
                '<i class="ph-fill ph-prohibit"></i> Yes</span>'
            )
        return format_html('<span style="color:#6b7280;font-size:11px;">—</span>')

    is_blacklisted_badge.short_description = _("Blacklisted")
    is_blacklisted_badge.admin_order_field = "is_blacklisted"

    def country_code_display(self, obj):
        """Country code display."""
        if not obj.country_code:
            return format_html('<span style="color:#6b7280;">—</span>')
        return format_html(
            '<span style="font-weight:600;color:#94a3b8;">{}</span>',
            obj.country_code.upper(),
        )

    country_code_display.short_description = _("Country")
    country_code_display.admin_order_field = "country_code"

    # Custom actions
    actions = ["whitelist_ips", "blacklist_ips", "reset_scores"]

    @admin.action(description=_("Whitelist selected IPs"))
    def whitelist_ips(self, request, queryset):
        updated = queryset.update(
            is_whitelisted=True,
            is_blacklisted=False,
        )
        self.message_user(request, _("%d IP(s) whitelisted.") % updated)

    @admin.action(description=_("Blacklist selected IPs"))
    def blacklist_ips(self, request, queryset):
        updated = queryset.update(
            is_blacklisted=True,
            is_whitelisted=False,
        )
        self.message_user(request, _("%d IP(s) blacklisted.") % updated)

    @admin.action(description=_("Reset risk scores to 0"))
    def reset_scores(self, request, queryset):
        updated = queryset.update(
            risk_score=0,
            signals={},
        )
        self.message_user(request, _("%d IP risk score(s) reset.") % updated)


# =============================================================================
# RULE SET ADMIN
# =============================================================================


@admin.register(RuleSet)
class RuleSetAdmin(EMenumPermissionMixin, admin.ModelAdmin):
    """
    Admin interface for RuleSet management.

    Manages configurable security rule definitions with priority ordering,
    action types (block/challenge/log/throttle), and match counting.
    """

    list_display = [
        "name_display",
        "action_badge",
        "priority_display",
        "is_active_badge",
        "match_count_display",
    ]
    list_filter = ["action", "is_active"]
    search_fields = ["name", "description"]
    readonly_fields = ["id", "match_count", "created_at", "updated_at"]
    ordering = ["priority"]
    list_per_page = 30

    fieldsets = (
        (None, {"fields": ("id", "name", "description", "is_active")}),
        (
            _("Rule Configuration"),
            {
                "fields": ("rules", "action", "priority"),
                "description": _(
                    "Rules: JSON list of rule definitions. "
                    "Lower priority value = higher priority. "
                    "Action determines what happens when rules match."
                ),
            },
        ),
        (
            _("Statistics"),
            {
                "fields": ("match_count",),
            },
        ),
        (
            _("Timestamps"),
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).filter(deleted_at__isnull=True)

    def name_display(self, obj):
        """Rule set name with icon."""
        return format_html(
            '<span style="display:inline-flex;align-items:center;gap:4px;'
            'font-weight:600;color:#e2e8f0;">'
            '<i class="ph ph-shield-warning"></i> {}</span>',
            obj.name,
        )

    name_display.short_description = _("Name")
    name_display.admin_order_field = "name"

    def action_badge(self, obj):
        """Color-coded action badge."""
        color = ACTION_COLORS.get(obj.action, "#94a3b8")
        icons = {
            RuleSet.Action.BLOCK: "prohibit",
            RuleSet.Action.CHALLENGE: "shield-warning",
            RuleSet.Action.LOG: "note",
            RuleSet.Action.THROTTLE: "speedometer",
        }
        icon = icons.get(obj.action, "question")
        return format_html(
            '<span style="display:inline-flex;align-items:center;gap:3px;'
            "padding:2px 8px;border-radius:4px;font-size:11px;font-weight:600;"
            'background:rgba({},0.12);color:{};">'
            '<i class="ph ph-{}"></i> {}</span>',
            _hex_to_rgb(color),
            color,
            icon,
            obj.get_action_display(),
        )

    action_badge.short_description = _("Action")
    action_badge.admin_order_field = "action"

    def priority_display(self, obj):
        """Priority with visual indicator."""
        if obj.priority <= 10:
            color = "#ef4444"
            label = "Critical"
        elif obj.priority <= 50:
            color = "#f59e0b"
            label = "High"
        elif obj.priority <= 100:
            color = "#3b82f6"
            label = "Normal"
        else:
            color = "#6b7280"
            label = "Low"
        return format_html(
            '<span style="color:{};font-weight:600;">{}</span>'
            '<br><span style="color:#6b7280;font-size:10px;">{}</span>',
            color,
            obj.priority,
            label,
        )

    priority_display.short_description = _("Priority")
    priority_display.admin_order_field = "priority"

    def is_active_badge(self, obj):
        """Active status badge."""
        if obj.is_active:
            return format_html(
                '<span style="color:#22c55e;">'
                '<i class="ph-fill ph-check-circle"></i> Active</span>'
            )
        return format_html(
            '<span style="color:#6b7280;">'
            '<i class="ph ph-x-circle"></i> Inactive</span>'
        )

    is_active_badge.short_description = _("Active")
    is_active_badge.admin_order_field = "is_active"

    def match_count_display(self, obj):
        """Match count with visual indicator."""
        if obj.match_count == 0:
            return format_html('<span style="color:#6b7280;">0</span>')
        color = (
            "#ef4444"
            if obj.match_count > 1000
            else "#f59e0b"
            if obj.match_count > 100
            else "#94a3b8"
        )
        return format_html(
            '<span style="color:{};font-weight:600;">{}</span>',
            color,
            obj.match_count,
        )

    match_count_display.short_description = _("Matches")
    match_count_display.admin_order_field = "match_count"


# =============================================================================
# BLOCK LOG ADMIN
# =============================================================================


@admin.register(BlockLog)
class BlockLogAdmin(EMenumPermissionMixin, admin.ModelAdmin):
    """
    Admin interface for BlockLog viewing.

    Read-only audit trail of all shield actions taken against requests.
    No add or change permissions -- this is a pure log viewer.
    """

    list_display = [
        "ip_address_display",
        "path_short",
        "method_badge",
        "reason_badge",
        "risk_score_display",
        "action_taken_badge",
        "country_code_display",
        "created_at",
    ]
    list_filter = ["reason", "action_taken", "method"]
    search_fields = ["ip_address", "path", "user_agent"]
    readonly_fields = [
        "id",
        "ip_address",
        "user_agent",
        "path",
        "method",
        "reason",
        "risk_score",
        "signals",
        "rule",
        "action_taken",
        "response_code",
        "country_code",
        "created_at",
        "updated_at",
    ]
    ordering = ["-created_at"]
    list_per_page = 50
    date_hierarchy = "created_at"

    fieldsets = (
        (None, {"fields": ("id", "ip_address", "method", "path")}),
        (
            _("Request Details"),
            {
                "fields": ("user_agent", "country_code"),
            },
        ),
        (
            _("Shield Decision"),
            {
                "fields": (
                    "reason",
                    "risk_score",
                    "signals",
                    "rule",
                    "action_taken",
                    "response_code",
                ),
            },
        ),
        (
            _("Timestamps"),
            {
                "fields": ("created_at", "updated_at"),
            },
        ),
    )

    def has_add_permission(self, request):
        """Block logs are system-generated. No manual creation allowed."""
        return False

    def has_change_permission(self, request, obj=None):
        """Block logs are immutable audit records."""
        return False

    def has_delete_permission(self, request, obj=None):
        """Block logs should not be deleted from admin."""
        return False

    def ip_address_display(self, obj):
        """IP address in monospace."""
        return format_html(
            '<code style="background:rgba(99,102,241,0.08);color:#a5b4fc;'
            'padding:2px 6px;border-radius:3px;font-size:11px;">{}</code>',
            obj.ip_address,
        )

    ip_address_display.short_description = _("IP Address")
    ip_address_display.admin_order_field = "ip_address"

    def path_short(self, obj):
        """Truncated request path."""
        path = obj.path
        display = path[:50] + "..." if len(path) > 50 else path
        return format_html(
            '<span style="color:#94a3b8;font-size:12px;" title="{}">{}</span>',
            path,
            display,
        )

    path_short.short_description = _("Path")
    path_short.admin_order_field = "path"

    def method_badge(self, obj):
        """HTTP method badge."""
        method_colors = {
            "GET": "#22c55e",
            "POST": "#3b82f6",
            "PUT": "#f59e0b",
            "PATCH": "#f59e0b",
            "DELETE": "#ef4444",
            "HEAD": "#6b7280",
            "OPTIONS": "#6b7280",
        }
        color = method_colors.get(obj.method.upper(), "#94a3b8")
        return format_html(
            '<span style="padding:1px 6px;border-radius:3px;font-size:10px;'
            'font-weight:700;background:rgba({},0.12);color:{};">{}</span>',
            _hex_to_rgb(color),
            color,
            obj.method.upper(),
        )

    method_badge.short_description = _("Method")
    method_badge.admin_order_field = "method"

    def reason_badge(self, obj):
        """Reason badge."""
        reason_colors = {
            "rate_limit": "#f59e0b",
            "bot_impersonation": "#ef4444",
            "header_anomaly": "#8b5cf6",
            "path_pattern": "#0ea5e9",
            "ua_anomaly": "#ec4899",
            "robots_violation": "#6b7280",
            "blacklisted": "#ef4444",
            "rule_match": "#3b82f6",
        }
        color = reason_colors.get(obj.reason, "#94a3b8")
        display = obj.reason.replace("_", " ").title()
        return format_html(
            '<span style="padding:2px 8px;border-radius:4px;font-size:10px;'
            'font-weight:600;background:rgba({},0.12);color:{};">{}</span>',
            _hex_to_rgb(color),
            color,
            display,
        )

    reason_badge.short_description = _("Reason")
    reason_badge.admin_order_field = "reason"

    def risk_score_display(self, obj):
        """Risk score with color."""
        score = obj.risk_score
        if score >= 60:
            color = "#ef4444"
        elif score >= 30:
            color = "#f59e0b"
        else:
            color = "#22c55e"
        return format_html(
            '<span style="color:{};font-weight:600;">{}</span>',
            color,
            score,
        )

    risk_score_display.short_description = _("Score")
    risk_score_display.admin_order_field = "risk_score"

    def action_taken_badge(self, obj):
        """Color-coded action taken badge."""
        color = BLOCK_ACTION_COLORS.get(obj.action_taken, "#94a3b8")
        icons = {
            BlockLog.ActionTaken.BLOCKED: "prohibit",
            BlockLog.ActionTaken.CHALLENGED: "shield-warning",
            BlockLog.ActionTaken.THROTTLED: "speedometer",
            BlockLog.ActionTaken.LOGGED: "note",
        }
        icon = icons.get(obj.action_taken, "question")
        return format_html(
            '<span style="display:inline-flex;align-items:center;gap:3px;'
            "padding:2px 8px;border-radius:4px;font-size:11px;font-weight:600;"
            'background:rgba({},0.12);color:{};">'
            '<i class="ph ph-{}"></i> {}</span>',
            _hex_to_rgb(color),
            color,
            icon,
            obj.get_action_taken_display(),
        )

    action_taken_badge.short_description = _("Action")
    action_taken_badge.admin_order_field = "action_taken"

    def country_code_display(self, obj):
        """Country code display."""
        if not obj.country_code:
            return format_html('<span style="color:#6b7280;">—</span>')
        return format_html(
            '<span style="font-weight:600;color:#94a3b8;">{}</span>',
            obj.country_code.upper(),
        )

    country_code_display.short_description = _("Country")
    country_code_display.admin_order_field = "country_code"
