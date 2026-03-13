"""
Django Admin configuration for the SEO application.

This module defines admin interfaces for SEO models:
- AuthorProfile: Author profiles for structured data and E-E-A-T
- Redirect: URL redirect management (301/302/307/308)
- BrokenLink: Broken link detection and tracking
- TXTFileConfig: Dynamic robots.txt, humans.txt, etc.
- PSEOTemplate: Programmatic SEO page templates
- PSEOPage: Generated programmatic SEO pages

All admin classes implement:
- Rich display with color-coded badges and visual indicators
- Inline editing for related models
- Custom actions for lifecycle management
- Dark theme compatible styling
"""

from django.contrib import admin
from django.utils import timezone
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from apps.seo.models import (
    AuthorProfile,
    BrokenLink,
    CoreWebVitalsSnapshot,
    CrawlReport,
    CrawlReportStatus,
    NotFound404Log,
    PSEOPage,
    PSEOTemplate,
    Redirect,
    RedirectType,
    SchemaOrgType,
    TrackingIntegration,
    TXTFileConfig,
)
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
REDIRECT_TYPE_COLORS = {
    RedirectType.PERMANENT: "#22c55e",  # Green
    RedirectType.TEMPORARY: "#f59e0b",  # Amber
    RedirectType.TEMPORARY_STRICT: "#f59e0b",  # Amber
    RedirectType.PERMANENT_STRICT: "#22c55e",  # Green
}

SCHEMA_TYPE_COLORS = {
    SchemaOrgType.LOCAL_BUSINESS: "#3b82f6",
    SchemaOrgType.RESTAURANT: "#22c55e",
    SchemaOrgType.CAFE_OR_COFFEE_SHOP: "#f59e0b",
    SchemaOrgType.BAR_OR_PUB: "#8b5cf6",
    SchemaOrgType.FOOD_ESTABLISHMENT: "#0ea5e9",
}


# =============================================================================
# AUTHOR PROFILE ADMIN
# =============================================================================


@admin.register(AuthorProfile)
class AuthorProfileAdmin(EMenumPermissionMixin, admin.ModelAdmin):
    """
    Admin interface for AuthorProfile management.

    Manages author profiles used for blog post attribution,
    structured data (JSON-LD Person), and E-E-A-T signals.
    """

    list_display = [
        "user_display",
        "bio_snippet",
        "expertise_display",
        "is_verified_badge",
        "created_at",
    ]
    list_filter = ["is_verified"]
    search_fields = ["user__email", "user__first_name", "user__last_name", "bio"]
    autocomplete_fields = ["user"]
    readonly_fields = ["id", "created_at", "updated_at"]
    ordering = ["-created_at"]
    list_per_page = 30

    fieldsets = (
        (None, {"fields": ("id", "user", "bio", "avatar")}),
        (_("Online Presence"), {"fields": ("website", "social_links")}),
        (_("Expertise & Verification"), {"fields": ("expertise", "is_verified")}),
        (
            _("Timestamps"),
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .filter(deleted_at__isnull=True)
            .select_related("user")
        )

    def user_display(self, obj):
        """User name with email."""
        full_name = obj.user.get_full_name()
        email = obj.user.email
        if full_name:
            return format_html(
                '<span style="font-weight:600;color:#e2e8f0;">{}</span>'
                '<br><span style="color:#6b7280;font-size:11px;">{}</span>',
                full_name,
                email,
            )
        return format_html(
            '<span style="font-weight:600;color:#e2e8f0;">{}</span>',
            email,
        )

    user_display.short_description = _("User")
    user_display.admin_order_field = "user__email"

    def bio_snippet(self, obj):
        """Truncated bio preview."""
        if not obj.bio:
            return format_html('<span style="color:#6b7280;">—</span>')
        snippet = obj.bio[:80] + "..." if len(obj.bio) > 80 else obj.bio
        return format_html(
            '<span style="color:#94a3b8;font-size:12px;">{}</span>',
            snippet,
        )

    bio_snippet.short_description = _("Bio")

    def expertise_display(self, obj):
        """Display expertise tags."""
        if not obj.expertise:
            return format_html('<span style="color:#6b7280;">—</span>')
        tags = []
        for item in obj.expertise[:3]:
            tags.append(
                format_html(
                    '<span style="display:inline-block;padding:1px 6px;border-radius:3px;'
                    "font-size:10px;font-weight:600;background:rgba(59,130,246,0.1);"
                    'color:#3b82f6;margin-right:3px;">{}</span>',
                    item,
                )
            )
        extra = len(obj.expertise) - 3
        if extra > 0:
            tags.append(
                format_html(
                    '<span style="color:#6b7280;font-size:10px;">+{}</span>',
                    extra,
                )
            )
        return format_html("".join(str(t) for t in tags))

    expertise_display.short_description = _("Expertise")

    def is_verified_badge(self, obj):
        """Verified status badge."""
        if obj.is_verified:
            return format_html(
                '<span style="display:inline-flex;align-items:center;gap:3px;'
                "padding:2px 8px;border-radius:4px;font-size:11px;font-weight:600;"
                'background:rgba(34,197,94,0.12);color:#22c55e;">'
                '<i class="ph ph-seal-check"></i> Verified</span>'
            )
        return format_html(
            '<span style="color:#6b7280;font-size:11px;">'
            '<i class="ph ph-seal"></i> Unverified</span>'
        )

    is_verified_badge.short_description = _("Verified")
    is_verified_badge.admin_order_field = "is_verified"


# =============================================================================
# REDIRECT ADMIN
# =============================================================================


@admin.register(Redirect)
class RedirectAdmin(EMenumPermissionMixin, admin.ModelAdmin):
    """
    Admin interface for Redirect management.

    Manages URL redirect rules with support for 301/302/307/308 redirects.
    Tracks hit count and last hit timestamp for analytics.
    """

    list_display = [
        "source_path",
        "target_path",
        "redirect_type_badge",
        "is_active_badge",
        "hit_count_display",
        "last_hit",
    ]
    list_filter = ["redirect_type", "is_active"]
    search_fields = ["source_path", "target_path", "note"]
    readonly_fields = ["id", "hit_count", "last_hit", "created_at", "updated_at"]
    autocomplete_fields = ["created_by"]
    ordering = ["-created_at"]
    list_per_page = 50

    fieldsets = (
        (None, {"fields": ("id", "source_path", "target_path", "redirect_type")}),
        (_("Status"), {"fields": ("is_active",)}),
        (
            _("Statistics"),
            {
                "fields": ("hit_count", "last_hit"),
            },
        ),
        (
            _("Notes"),
            {
                "fields": ("note", "created_by"),
                "classes": ("collapse",),
            },
        ),
        (
            _("Timestamps"),
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .filter(deleted_at__isnull=True)
            .select_related("created_by")
        )

    def redirect_type_badge(self, obj):
        """Color-coded redirect type badge."""
        color = REDIRECT_TYPE_COLORS.get(obj.redirect_type, "#94a3b8")
        return format_html(
            '<span style="display:inline-flex;align-items:center;gap:3px;'
            "padding:2px 8px;border-radius:4px;font-size:11px;font-weight:600;"
            'background:rgba({},0.12);color:{};">{}</span>',
            _hex_to_rgb(color),
            color,
            obj.get_redirect_type_display(),
        )

    redirect_type_badge.short_description = _("Type")
    redirect_type_badge.admin_order_field = "redirect_type"

    def is_active_badge(self, obj):
        """Active status badge."""
        if obj.is_active:
            return format_html(
                '<span style="color:#22c55e;">'
                '<i class="ph-fill ph-check-circle"></i> Active</span>'
            )
        return format_html(
            '<span style="color:#ef4444;opacity:0.6;">'
            '<i class="ph ph-x-circle"></i> Inactive</span>'
        )

    is_active_badge.short_description = _("Active")
    is_active_badge.admin_order_field = "is_active"

    def hit_count_display(self, obj):
        """Hit count with visual indicator."""
        if obj.hit_count == 0:
            return format_html('<span style="color:#6b7280;">0</span>')
        color = (
            "#22c55e"
            if obj.hit_count > 100
            else "#f59e0b"
            if obj.hit_count > 10
            else "#94a3b8"
        )
        return format_html(
            '<span style="color:{};font-weight:600;">{}</span>',
            color,
            obj.hit_count,
        )

    hit_count_display.short_description = _("Hits")
    hit_count_display.admin_order_field = "hit_count"

    # Custom actions
    actions = ["activate_redirects", "deactivate_redirects"]

    @admin.action(description=_("Activate selected redirects"))
    def activate_redirects(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, _("%d redirect(s) activated.") % updated)

    @admin.action(description=_("Deactivate selected redirects"))
    def deactivate_redirects(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, _("%d redirect(s) deactivated.") % updated)


# =============================================================================
# BROKEN LINK ADMIN
# =============================================================================


@admin.register(BrokenLink)
class BrokenLinkAdmin(EMenumPermissionMixin, admin.ModelAdmin):
    """
    Admin interface for BrokenLink tracking.

    Displays detected broken links across the site with status codes,
    check counts, and resolution tracking. Supports bulk resolution.
    """

    list_display = [
        "source_url_short",
        "target_url_short",
        "status_code_badge",
        "check_count",
        "is_resolved_badge",
        "last_checked",
    ]
    list_filter = ["is_resolved", "status_code"]
    search_fields = ["source_url", "target_url", "link_text"]
    readonly_fields = [
        "id",
        "first_detected",
        "last_checked",
        "check_count",
        "created_at",
        "updated_at",
    ]
    ordering = ["-first_detected"]
    list_per_page = 50
    date_hierarchy = "first_detected"

    fieldsets = (
        (None, {"fields": ("id", "source_url", "target_url", "status_code")}),
        (_("Context"), {"fields": ("source_page", "link_text")}),
        (
            _("Tracking"),
            {
                "fields": ("first_detected", "last_checked", "check_count"),
            },
        ),
        (
            _("Resolution"),
            {
                "fields": ("is_resolved", "resolved_at"),
            },
        ),
        (
            _("Timestamps"),
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    def source_url_short(self, obj):
        """Truncated source URL."""
        url = obj.source_url
        display = url[:60] + "..." if len(url) > 60 else url
        return format_html(
            '<span style="color:#94a3b8;font-size:12px;" title="{}">{}</span>',
            url,
            display,
        )

    source_url_short.short_description = _("Source URL")
    source_url_short.admin_order_field = "source_url"

    def target_url_short(self, obj):
        """Truncated target URL."""
        url = obj.target_url
        display = url[:60] + "..." if len(url) > 60 else url
        return format_html(
            '<span style="color:#e2e8f0;font-size:12px;" title="{}">{}</span>',
            url,
            display,
        )

    target_url_short.short_description = _("Target URL")
    target_url_short.admin_order_field = "target_url"

    def status_code_badge(self, obj):
        """Color-coded HTTP status code badge."""
        code = obj.status_code
        if code == 0:
            color = "#6b7280"
            label = "Timeout"
        elif 400 <= code < 500:
            color = "#f59e0b"
            label = str(code)
        elif code >= 500:
            color = "#ef4444"
            label = str(code)
        else:
            color = "#94a3b8"
            label = str(code)
        return format_html(
            '<span style="display:inline-flex;align-items:center;gap:3px;'
            "padding:2px 8px;border-radius:4px;font-size:11px;font-weight:600;"
            'background:rgba({},0.12);color:{};">{}</span>',
            _hex_to_rgb(color),
            color,
            label,
        )

    status_code_badge.short_description = _("Status")
    status_code_badge.admin_order_field = "status_code"

    def is_resolved_badge(self, obj):
        """Resolved status badge."""
        if obj.is_resolved:
            return format_html(
                '<span style="color:#22c55e;font-size:11px;">'
                '<i class="ph-fill ph-check-circle"></i> Resolved</span>'
            )
        return format_html(
            '<span style="color:#ef4444;font-size:11px;">'
            '<i class="ph ph-warning-circle"></i> Broken</span>'
        )

    is_resolved_badge.short_description = _("Status")
    is_resolved_badge.admin_order_field = "is_resolved"

    # Custom actions
    actions = ["mark_as_resolved"]

    @admin.action(description=_("Mark selected as resolved"))
    def mark_as_resolved(self, request, queryset):
        now = timezone.now()
        updated = queryset.filter(is_resolved=False).update(
            is_resolved=True,
            resolved_at=now,
        )
        self.message_user(request, _("%d broken link(s) marked as resolved.") % updated)


# =============================================================================
# TXT FILE CONFIG ADMIN
# =============================================================================


@admin.register(TXTFileConfig)
class TXTFileConfigAdmin(EMenumPermissionMixin, admin.ModelAdmin):
    """
    Admin interface for TXTFileConfig management.

    Manages dynamically served TXT files (robots.txt, humans.txt,
    security.txt, ads.txt, llms.txt).
    """

    list_display = [
        "file_type_display",
        "is_active_badge",
        "auto_generate_badge",
        "last_generated",
        "content_preview",
    ]
    list_filter = ["file_type", "is_active", "auto_generate"]
    readonly_fields = ["id", "last_generated", "created_at", "updated_at"]
    ordering = ["file_type"]
    list_per_page = 20

    fieldsets = (
        (None, {"fields": ("id", "file_type", "is_active", "auto_generate")}),
        (
            _("Content"),
            {
                "fields": ("content",),
                "description": _(
                    "Raw text content for the file. Ignored when auto_generate is enabled."
                ),
            },
        ),
        (
            _("Generation"),
            {
                "fields": ("last_generated",),
            },
        ),
        (
            _("Timestamps"),
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    def file_type_display(self, obj):
        """File type with icon."""
        icons = {
            "robots": "robot",
            "humans": "user",
            "security": "shield-check",
            "ads": "megaphone",
            "llms": "brain",
        }
        icon = icons.get(obj.file_type, "file-text")
        return format_html(
            '<span style="display:inline-flex;align-items:center;gap:4px;'
            'font-weight:600;color:#e2e8f0;">'
            '<i class="ph ph-{}"></i> {}</span>',
            icon,
            obj.get_file_type_display(),
        )

    file_type_display.short_description = _("File Type")
    file_type_display.admin_order_field = "file_type"

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

    def auto_generate_badge(self, obj):
        """Auto-generate status badge."""
        if obj.auto_generate:
            return format_html(
                '<span style="color:#3b82f6;font-size:11px;">'
                '<i class="ph ph-arrows-clockwise"></i> Auto</span>'
            )
        return format_html(
            '<span style="color:#94a3b8;font-size:11px;">'
            '<i class="ph ph-pencil-simple"></i> Manual</span>'
        )

    auto_generate_badge.short_description = _("Mode")
    auto_generate_badge.admin_order_field = "auto_generate"

    def content_preview(self, obj):
        """Truncated content preview."""
        if not obj.content:
            return format_html('<span style="color:#6b7280;">—</span>')
        snippet = obj.content[:60] + "..." if len(obj.content) > 60 else obj.content
        return format_html(
            '<code style="color:#94a3b8;font-size:11px;">{}</code>',
            snippet,
        )

    content_preview.short_description = _("Content")


# =============================================================================
# PSEO TEMPLATE ADMIN
# =============================================================================


@admin.register(PSEOTemplate)
class PSEOTemplateAdmin(EMenumPermissionMixin, admin.ModelAdmin):
    """
    Admin interface for PSEOTemplate management.

    Manages programmatic SEO page templates with variable placeholders,
    schema.org type selection, and quality thresholds.
    """

    list_display = [
        "name",
        "slug_template_display",
        "schema_type_badge",
        "is_active_badge",
        "quality_threshold_display",
        "page_count",
    ]
    list_filter = ["schema_type", "is_active"]
    search_fields = ["name", "slug_template", "title_template"]
    readonly_fields = ["id", "created_at", "updated_at"]
    ordering = ["-created_at"]
    list_per_page = 30

    fieldsets = (
        (None, {"fields": ("id", "name", "slug_template", "is_active")}),
        (
            _("Templates"),
            {
                "fields": (
                    "title_template",
                    "description_template",
                    "content_template",
                ),
                "description": _(
                    "Use {sehir} and {sektor} as placeholders. "
                    'Example: "{sehir}-{sektor}-qr-menu"'
                ),
            },
        ),
        (
            _("Schema & Quality"),
            {
                "fields": ("schema_type", "quality_threshold"),
            },
        ),
        (
            _("Timestamps"),
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    def get_queryset(self, request):
        from django.db.models import Count, Q

        return (
            super()
            .get_queryset(request)
            .filter(deleted_at__isnull=True)
            .annotate(
                _page_count=Count(
                    "pages",
                    filter=Q(pages__deleted_at__isnull=True),
                )
            )
        )

    def slug_template_display(self, obj):
        """Slug template in code style."""
        return format_html(
            '<code style="background:rgba(99,102,241,0.08);color:#a5b4fc;'
            'padding:2px 8px;border-radius:4px;font-size:11px;">{}</code>',
            obj.slug_template,
        )

    slug_template_display.short_description = _("Slug Pattern")
    slug_template_display.admin_order_field = "slug_template"

    def schema_type_badge(self, obj):
        """Color-coded schema type badge."""
        color = SCHEMA_TYPE_COLORS.get(obj.schema_type, "#94a3b8")
        return format_html(
            '<span style="padding:2px 8px;border-radius:4px;font-size:11px;'
            'font-weight:600;background:rgba({},0.12);color:{};">{}</span>',
            _hex_to_rgb(color),
            color,
            obj.get_schema_type_display(),
        )

    schema_type_badge.short_description = _("Schema")
    schema_type_badge.admin_order_field = "schema_type"

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

    def quality_threshold_display(self, obj):
        """Quality threshold with color indicator."""
        threshold = obj.quality_threshold
        if threshold >= 80:
            color = "#22c55e"
        elif threshold >= 50:
            color = "#f59e0b"
        else:
            color = "#ef4444"
        return format_html(
            '<span style="color:{};font-weight:600;">{}</span>',
            color,
            threshold,
        )

    quality_threshold_display.short_description = _("Min Quality")
    quality_threshold_display.admin_order_field = "quality_threshold"

    def page_count(self, obj):
        """Number of generated pages."""
        count = getattr(obj, "_page_count", 0)
        color = "#22c55e" if count > 0 else "#6b7280"
        return format_html(
            '<span style="color:{};font-weight:600;">'
            '<i class="ph ph-files"></i> {}</span>',
            color,
            count,
        )

    page_count.short_description = _("Pages")
    page_count.admin_order_field = "_page_count"


# =============================================================================
# PSEO PAGE ADMIN
# =============================================================================


@admin.register(PSEOPage)
class PSEOPageAdmin(EMenumPermissionMixin, admin.ModelAdmin):
    """
    Admin interface for PSEOPage management.

    Manages generated programmatic SEO pages with quality scoring,
    publication control, and view count tracking.
    """

    list_display = [
        "slug_display",
        "rendered_title_short",
        "quality_score_badge",
        "is_published_badge",
        "view_count_display",
        "published_at",
    ]
    list_filter = ["is_published", "template"]
    search_fields = ["slug", "rendered_title", "rendered_description"]
    autocomplete_fields = ["template"]
    readonly_fields = [
        "id",
        "quality_score",
        "view_count",
        "created_at",
        "updated_at",
    ]
    ordering = ["-created_at"]
    list_per_page = 50

    fieldsets = (
        (None, {"fields": ("id", "template", "slug")}),
        (
            _("Rendered Content"),
            {
                "fields": (
                    "rendered_title",
                    "rendered_description",
                    "rendered_content",
                ),
            },
        ),
        (
            _("Variables"),
            {
                "fields": ("variables",),
                "classes": ("collapse",),
            },
        ),
        (
            _("Publication"),
            {
                "fields": ("is_published", "published_at"),
            },
        ),
        (
            _("Quality & Stats"),
            {
                "fields": ("quality_score", "view_count"),
            },
        ),
        (
            _("SEO Meta"),
            {
                "fields": (
                    "meta_title",
                    "meta_description",
                    "meta_keywords",
                    "focus_keyword",
                    "canonical_url",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            _("Open Graph"),
            {
                "fields": ("og_title", "og_description", "og_image", "og_type"),
                "classes": ("collapse",),
            },
        ),
        (
            _("Twitter Card"),
            {
                "fields": (
                    "twitter_card",
                    "twitter_title",
                    "twitter_description",
                    "twitter_image",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            _("Robots & Sitemap"),
            {
                "fields": (
                    "robots_index",
                    "robots_follow",
                    "robots_extra",
                    "sitemap_include",
                    "sitemap_priority",
                    "sitemap_changefreq",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            _("Structured Data & Analysis"),
            {
                "fields": (
                    "structured_data",
                    "seo_score",
                    "seo_suggestions",
                    "last_seo_analysis",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            _("Timestamps"),
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .filter(deleted_at__isnull=True)
            .select_related("template")
        )

    def slug_display(self, obj):
        """Slug in code style."""
        return format_html(
            '<code style="background:rgba(99,102,241,0.08);color:#a5b4fc;'
            'padding:2px 8px;border-radius:4px;font-size:11px;">{}</code>',
            obj.slug,
        )

    slug_display.short_description = _("Slug")
    slug_display.admin_order_field = "slug"

    def rendered_title_short(self, obj):
        """Truncated rendered title."""
        title = obj.rendered_title or obj.slug
        display = title[:50] + "..." if len(title) > 50 else title
        return format_html(
            '<span style="color:#e2e8f0;font-size:12px;" title="{}">{}</span>',
            title,
            display,
        )

    rendered_title_short.short_description = _("Title")
    rendered_title_short.admin_order_field = "rendered_title"

    def quality_score_badge(self, obj):
        """
        Color-coded quality score badge.

        Green for >= 80, yellow for >= 50, red for < 50.
        """
        score = obj.quality_score
        if score >= 80:
            color = "#22c55e"
            icon = "check-circle"
        elif score >= 50:
            color = "#f59e0b"
            icon = "warning"
        else:
            color = "#ef4444"
            icon = "x-circle"
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

    quality_score_badge.short_description = _("Quality")
    quality_score_badge.admin_order_field = "quality_score"

    def is_published_badge(self, obj):
        """Published status badge."""
        if obj.is_published:
            return format_html(
                '<span style="color:#22c55e;font-size:11px;">'
                '<i class="ph-fill ph-globe"></i> Published</span>'
            )
        return format_html(
            '<span style="color:#6b7280;font-size:11px;">'
            '<i class="ph ph-eye-slash"></i> Draft</span>'
        )

    is_published_badge.short_description = _("Status")
    is_published_badge.admin_order_field = "is_published"

    def view_count_display(self, obj):
        """View count with visual indicator."""
        if obj.view_count == 0:
            return format_html('<span style="color:#6b7280;">0</span>')
        color = (
            "#22c55e"
            if obj.view_count > 1000
            else "#f59e0b"
            if obj.view_count > 100
            else "#94a3b8"
        )
        return format_html(
            '<span style="color:{};font-weight:600;">'
            '<i class="ph ph-eye"></i> {}</span>',
            color,
            obj.view_count,
        )

    view_count_display.short_description = _("Views")
    view_count_display.admin_order_field = "view_count"

    # Custom actions
    actions = ["publish_pages", "unpublish_pages"]

    @admin.action(description=_("Publish selected pages"))
    def publish_pages(self, request, queryset):
        now = timezone.now()
        # Only publish pages that are not already published
        updated = queryset.filter(is_published=False).update(
            is_published=True,
            published_at=now,
        )
        self.message_user(request, _("%d page(s) published.") % updated)

    @admin.action(description=_("Unpublish selected pages"))
    def unpublish_pages(self, request, queryset):
        updated = queryset.filter(is_published=True).update(
            is_published=False,
        )
        self.message_user(request, _("%d page(s) unpublished.") % updated)


# =============================================================================
# 404 LOG ADMIN
# =============================================================================

CRAWL_STATUS_COLORS = {
    CrawlReportStatus.RUNNING: "#3b82f6",  # Blue
    CrawlReportStatus.COMPLETED: "#22c55e",  # Green
    CrawlReportStatus.FAILED: "#ef4444",  # Red
}


@admin.register(NotFound404Log)
class NotFound404LogAdmin(EMenumPermissionMixin, admin.ModelAdmin):
    """
    Admin interface for 404 error tracking.

    Displays aggregated 404 logs with hit counts, referer info,
    and a custom action to create redirects from common 404 paths.
    """

    list_display = [
        "path_display",
        "hit_count_badge",
        "date",
        "last_referer_short",
        "last_ip",
    ]
    list_filter = ["date"]
    search_fields = ["path", "last_referer"]
    readonly_fields = [
        "id",
        "path",
        "date",
        "hit_count",
        "last_user_agent",
        "last_referer",
        "last_ip",
        "created_at",
        "updated_at",
    ]
    ordering = ["-hit_count", "-date"]
    list_per_page = 50
    date_hierarchy = "date"

    fieldsets = (
        (None, {"fields": ("id", "path", "date", "hit_count")}),
        (
            _("Request Details"),
            {
                "fields": ("last_user_agent", "last_referer", "last_ip"),
            },
        ),
        (
            _("Timestamps"),
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def path_display(self, obj):
        """Path in code style."""
        return format_html(
            '<code style="background:rgba(239,68,68,0.08);color:#fca5a5;'
            'padding:2px 8px;border-radius:4px;font-size:11px;">{}</code>',
            obj.path,
        )

    path_display.short_description = _("Path")
    path_display.admin_order_field = "path"

    def hit_count_badge(self, obj):
        """Hit count with color-coded severity."""
        count = obj.hit_count
        if count >= 100:
            color = "#ef4444"
        elif count >= 10:
            color = "#f59e0b"
        else:
            color = "#94a3b8"
        return format_html(
            '<span style="display:inline-flex;align-items:center;gap:3px;'
            "padding:2px 8px;border-radius:4px;font-size:11px;font-weight:700;"
            'background:rgba({},0.12);color:{};">{}</span>',
            _hex_to_rgb(color),
            color,
            count,
        )

    hit_count_badge.short_description = _("Hits")
    hit_count_badge.admin_order_field = "hit_count"

    def last_referer_short(self, obj):
        """Truncated referer URL."""
        if not obj.last_referer:
            return format_html('<span style="color:#6b7280;">—</span>')
        url = obj.last_referer
        display = url[:50] + "..." if len(url) > 50 else url
        return format_html(
            '<span style="color:#94a3b8;font-size:12px;" title="{}">{}</span>',
            url,
            display,
        )

    last_referer_short.short_description = _("Referer")

    # Custom actions
    actions = ["create_redirects"]

    @admin.action(description=_("Create redirect for selected 404 paths"))
    def create_redirects(self, request, queryset):
        """Create Redirect objects for selected 404 paths pointing to /."""
        created = 0
        for log_entry in queryset:
            _, was_created = Redirect.objects.get_or_create(
                source_path=log_entry.path,
                defaults={
                    "target_path": "/",
                    "redirect_type": 301,
                    "is_active": True,
                    "note": f"Auto-created from 404 log ({log_entry.hit_count} hits)",
                    "created_by": request.user,
                },
            )
            if was_created:
                created += 1
        self.message_user(
            request,
            _("%d redirect(s) created. Edit target paths as needed.") % created,
        )


# =============================================================================
# CRAWL REPORT ADMIN
# =============================================================================


@admin.register(CrawlReport)
class CrawlReportAdmin(EMenumPermissionMixin, admin.ModelAdmin):
    """
    Admin interface for CrawlReport viewing.

    Displays broken link crawl results with status badges
    and link statistics. All fields are read-only.
    """

    list_display = [
        "started_at",
        "status_badge",
        "total_pages",
        "broken_count_display",
        "redirected_count",
        "healthy_count",
        "finished_at",
    ]
    list_filter = ["status"]
    readonly_fields = [
        "id",
        "started_at",
        "finished_at",
        "total_pages",
        "total_links",
        "broken_count",
        "redirected_count",
        "healthy_count",
        "status",
        "error_message",
        "created_at",
        "updated_at",
    ]
    ordering = ["-started_at"]
    list_per_page = 30

    fieldsets = (
        (None, {"fields": ("id", "status", "started_at", "finished_at")}),
        (
            _("Statistics"),
            {
                "fields": (
                    "total_pages",
                    "total_links",
                    "broken_count",
                    "redirected_count",
                    "healthy_count",
                ),
            },
        ),
        (
            _("Error"),
            {
                "fields": ("error_message",),
                "classes": ("collapse",),
            },
        ),
        (
            _("Timestamps"),
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def status_badge(self, obj):
        """Color-coded crawl status badge."""
        color = CRAWL_STATUS_COLORS.get(obj.status, "#94a3b8")
        icons = {
            "running": "spinner",
            "completed": "check-circle",
            "failed": "x-circle",
        }
        icon = icons.get(obj.status, "circle")
        return format_html(
            '<span style="display:inline-flex;align-items:center;gap:3px;'
            "padding:2px 8px;border-radius:4px;font-size:11px;font-weight:600;"
            'background:rgba({},0.12);color:{};">'
            '<i class="ph ph-{}"></i> {}</span>',
            _hex_to_rgb(color),
            color,
            icon,
            obj.get_status_display(),
        )

    status_badge.short_description = _("Status")
    status_badge.admin_order_field = "status"

    def broken_count_display(self, obj):
        """Broken link count with color indicator."""
        count = obj.broken_count
        if count == 0:
            return format_html('<span style="color:#22c55e;font-weight:600;">0</span>')
        color = "#ef4444" if count >= 10 else "#f59e0b"
        return format_html(
            '<span style="color:{};font-weight:700;">{}</span>',
            color,
            count,
        )

    broken_count_display.short_description = _("Broken")
    broken_count_display.admin_order_field = "broken_count"


# =============================================================================
# TRACKING INTEGRATION ADMIN
# =============================================================================


PLATFORM_COLORS = {
    "gtm": "#4285F4",
    "ga4": "#E37400",
    "meta_pixel": "#1877F2",
    "tiktok_pixel": "#000000",
    "linkedin_insight": "#0A66C2",
    "twitter_pixel": "#1DA1F2",
    "hotjar": "#FF3C00",
    "clarity": "#5C2D91",
    "custom_head": "#6B7280",
    "custom_body": "#6B7280",
}


@admin.register(TrackingIntegration)
class TrackingIntegrationAdmin(EMenumPermissionMixin, admin.ModelAdmin):
    """Admin interface for managing tracking pixel integrations."""

    list_display = [
        "name",
        "platform_badge",
        "tracking_id",
        "position",
        "status_badge",
        "updated_at",
    ]
    list_filter = ["platform", "is_active", "position"]
    search_fields = ["name", "tracking_id"]
    list_editable = ["is_active"] if False else []  # Read-only list

    fieldsets = [
        (
            _("Integration Details"),
            {
                "fields": ("name", "platform", "tracking_id", "is_active"),
            },
        ),
        (
            _("Script Configuration"),
            {
                "fields": ("position", "custom_script"),
                "classes": ("collapse",),
                "description": _(
                    "Custom script is only used for 'Custom Head/Body' platforms."
                ),
            },
        ),
        (
            _("Environment"),
            {
                "fields": ("environments",),
                "classes": ("collapse",),
                "description": _(
                    "Restrict to specific environments. "
                    'Leave empty for all. Example: ["production"]'
                ),
            },
        ),
    ]

    def platform_badge(self, obj):
        """Colored badge showing the platform name."""
        color = PLATFORM_COLORS.get(obj.platform, "#6B7280")
        return format_html(
            '<span style="display:inline-flex;align-items:center;gap:3px;'
            "padding:2px 8px;border-radius:4px;font-size:11px;font-weight:600;"
            'background:rgba({},0.12);color:{};">{}</span>',
            _hex_to_rgb(color),
            color,
            obj.get_platform_display(),
        )

    platform_badge.short_description = _("Platform")
    platform_badge.admin_order_field = "platform"

    def status_badge(self, obj):
        """Active/Inactive status badge."""
        if obj.is_active:
            return format_html(
                '<span style="display:inline-flex;align-items:center;gap:3px;'
                "padding:2px 8px;border-radius:4px;font-size:11px;font-weight:600;"
                'background:rgba(34,197,94,0.12);color:#22c55e;">'
                '<i class="ph ph-check-circle"></i> Active</span>'
            )
        return format_html(
            '<span style="display:inline-flex;align-items:center;gap:3px;'
            "padding:2px 8px;border-radius:4px;font-size:11px;font-weight:600;"
            'background:rgba(107,114,128,0.12);color:#6B7280;">'
            '<i class="ph ph-minus-circle"></i> Inactive</span>'
        )

    status_badge.short_description = _("Status")
    status_badge.admin_order_field = "is_active"


# =============================================================================
# CORE WEB VITALS ADMIN
# =============================================================================


@admin.register(CoreWebVitalsSnapshot)
class CoreWebVitalsSnapshotAdmin(EMenumPermissionMixin, admin.ModelAdmin):
    """Read-only admin for Core Web Vitals measurement history."""

    list_display = [
        "url_short",
        "performance_score_badge",
        "lcp_display",
        "cls_display",
        "inp_display",
        "source",
        "measured_at",
    ]
    list_filter = ["source", "measured_at"]
    search_fields = ["url"]
    ordering = ["-measured_at"]
    date_hierarchy = "measured_at"

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def url_short(self, obj):
        """Truncated URL for list display."""
        url = obj.url
        if len(url) > 60:
            url = url[:57] + "..."
        return url

    url_short.short_description = _("URL")
    url_short.admin_order_field = "url"

    def performance_score_badge(self, obj):
        """Color-coded performance score."""
        score = obj.performance_score
        if score is None:
            return format_html('<span style="color:#6B7280;">N/A</span>')
        if score >= 90:
            color = "#22c55e"
        elif score >= 50:
            color = "#f59e0b"
        else:
            color = "#ef4444"
        return format_html(
            '<span style="font-weight:700;font-size:14px;color:{};">{}</span>',
            color,
            score,
        )

    performance_score_badge.short_description = _("Score")
    performance_score_badge.admin_order_field = "performance_score"

    def lcp_display(self, obj):
        """LCP with color rating."""
        if obj.lcp is None:
            return "—"
        colors = {"good": "#22c55e", "needs-improvement": "#f59e0b", "poor": "#ef4444"}
        color = colors.get(obj.lcp_rating, "#6B7280")
        return format_html('<span style="color:{};">{:.0f}ms</span>', color, obj.lcp)

    lcp_display.short_description = _("LCP")
    lcp_display.admin_order_field = "lcp"

    def cls_display(self, obj):
        """CLS with color rating."""
        if obj.cls is None:
            return "—"
        colors = {"good": "#22c55e", "needs-improvement": "#f59e0b", "poor": "#ef4444"}
        color = colors.get(obj.cls_rating, "#6B7280")
        return format_html('<span style="color:{};">{:.3f}</span>', color, obj.cls)

    cls_display.short_description = _("CLS")
    cls_display.admin_order_field = "cls"

    def inp_display(self, obj):
        """INP with color rating."""
        if obj.inp is None:
            return "—"
        colors = {"good": "#22c55e", "needs-improvement": "#f59e0b", "poor": "#ef4444"}
        color = colors.get(obj.inp_rating, "#6B7280")
        return format_html('<span style="color:{};">{:.0f}ms</span>', color, obj.inp)

    inp_display.short_description = _("INP")
    inp_display.admin_order_field = "inp"
