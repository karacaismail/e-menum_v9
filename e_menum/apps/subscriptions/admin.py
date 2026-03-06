"""
Django Admin configuration for the Subscriptions application.

This module defines admin interfaces for subscription models:
- Feature: Platform-level capability definitions
- Plan: Subscription tiers (FREE → ENTERPRISE)
- PlanFeature: Plan-Feature junction with plan-specific config
- Subscription: Organization-Plan billing lifecycle
- Invoice: Billing records and payment tracking
- OrganizationUsage: Resource usage per tenant

All admin classes implement:
- Rich display with color-coded badges and visual indicators
- Inline editing for related models
- Custom actions for lifecycle management
- Soft-delete awareness (filters out deleted_at records)
- Dark theme compatible styling
"""

import io

from django.contrib import admin
from django.db.models import Count, Q
from django.utils import timezone
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from apps.subscriptions.choices import (
    BillingPeriod,
    FeatureType,
    InvoiceStatus,
    PlanTier,
    SubscriptionStatus,
)
from apps.subscriptions.models import (
    Feature,
    FeaturePermission,
    Invoice,
    OrganizationUsage,
    Plan,
    PlanFeature,
    Subscription,
)
from apps.website.models import PlanDisplayFeature
from shared.permissions.admin_permission_mixin import EMenumPermissionMixin


# =============================================================================
# HELPER UTILITIES
# =============================================================================

def _hex_to_rgb(hex_color: str) -> str:
    """Convert hex color to comma-separated RGB values for rgba() usage."""
    hex_color = hex_color.lstrip('#')
    r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
    return f"{r}, {g}, {b}"


# Color maps
TIER_COLORS = {
    PlanTier.FREE: '#94a3b8',        # Slate
    PlanTier.STARTER: '#3b82f6',     # Blue
    PlanTier.GROWTH: '#22c55e',      # Green
    PlanTier.PROFESSIONAL: '#8b5cf6', # Purple
    PlanTier.ENTERPRISE: '#f59e0b',  # Amber
}

TIER_ICONS = {
    PlanTier.FREE: 'leaf',
    PlanTier.STARTER: 'rocket-launch',
    PlanTier.GROWTH: 'trend-up',
    PlanTier.PROFESSIONAL: 'crown',
    PlanTier.ENTERPRISE: 'buildings',
}

STATUS_COLORS = {
    SubscriptionStatus.TRIALING: '#0ea5e9',   # Sky
    SubscriptionStatus.ACTIVE: '#22c55e',      # Green
    SubscriptionStatus.PAST_DUE: '#f59e0b',   # Amber
    SubscriptionStatus.CANCELLED: '#ef4444',   # Red
    SubscriptionStatus.EXPIRED: '#6b7280',     # Gray
    SubscriptionStatus.SUSPENDED: '#dc2626',   # Dark Red
}

INVOICE_STATUS_COLORS = {
    InvoiceStatus.DRAFT: '#94a3b8',
    InvoiceStatus.PENDING: '#f59e0b',
    InvoiceStatus.PAID: '#22c55e',
    InvoiceStatus.VOID: '#6b7280',
    InvoiceStatus.REFUNDED: '#8b5cf6',
    InvoiceStatus.UNCOLLECTIBLE: '#ef4444',
}

FEATURE_TYPE_COLORS = {
    FeatureType.BOOLEAN: '#3b82f6',
    FeatureType.LIMIT: '#f59e0b',
    FeatureType.USAGE: '#8b5cf6',
}


# =============================================================================
# INLINE ADMIN CLASSES
# =============================================================================

class PlanFeatureInline(admin.TabularInline):
    """Inline editor for PlanFeature (shown inside PlanAdmin)."""
    model = PlanFeature
    extra = 0
    min_num = 0
    autocomplete_fields = ['feature']
    fields = ['feature', 'is_enabled', 'value', 'sort_order']
    ordering = ['sort_order', 'feature__name']

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('feature')


class PlanDisplayFeatureInline(admin.TabularInline):
    """
    Inline editor for PlanDisplayFeature (marketing bullet points on pricing cards).

    These are the user-facing feature descriptions shown on the pricing page,
    separate from the technical PlanFeature junction table.
    """
    model = PlanDisplayFeature
    extra = 1
    fields = ['text', 'is_highlighted', 'sort_order', 'is_active']
    ordering = ['sort_order']
    verbose_name = _('Display Feature (Pricing Card)')
    verbose_name_plural = _('Display Features (Pricing Card)')


class SubscriptionInvoiceInline(admin.TabularInline):
    """Inline viewer for Invoices (shown inside SubscriptionAdmin)."""
    model = Invoice
    extra = 0
    max_num = 0  # Read-only: don't allow adding inline
    fields = ['invoice_number', 'status', 'amount_total', 'due_date', 'paid_at']
    readonly_fields = ['invoice_number', 'status', 'amount_total', 'due_date', 'paid_at']
    ordering = ['-created_at']
    show_change_link = True

    def get_queryset(self, request):
        return super().get_queryset(request).filter(deleted_at__isnull=True)

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class OrganizationUsageInline(admin.TabularInline):
    """Inline viewer for usage records (shown inside SubscriptionAdmin)."""
    model = OrganizationUsage
    extra = 0
    max_num = 0
    fields = ['feature', 'current_usage', 'usage_limit', 'usage_bar']
    readonly_fields = ['feature', 'current_usage', 'usage_limit', 'usage_bar']
    ordering = ['feature__category', 'feature__sort_order']
    fk_name = 'organization'
    show_change_link = False

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('feature')

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def usage_bar(self, obj):
        """Visual progress bar for usage."""
        if obj.usage_limit == -1 or obj.usage_limit == 0:
            return format_html(
                '<span style="color: #22c55e; font-size: 11px;">'
                '<i class="ph ph-infinity"></i> Unlimited</span>'
            )
        pct = min(100, (obj.current_usage / obj.usage_limit) * 100) if obj.usage_limit > 0 else 0
        color = '#22c55e' if pct < 70 else '#f59e0b' if pct < 90 else '#ef4444'
        pct_str = '{:.0f}'.format(pct)
        return format_html(
            '<div style="display:flex;align-items:center;gap:6px;">'
            '<div style="width:80px;height:6px;background:rgba(148,163,184,0.1);border-radius:3px;">'
            '<div style="width:{}%;height:100%;background:{};border-radius:3px;"></div></div>'
            '<span style="color:{};font-size:11px;font-weight:600;">{}%</span></div>',
            pct_str, color, color, pct_str,
        )
    usage_bar.short_description = _('Usage')


# =============================================================================
# FEATURE PERMISSION INLINE
# =============================================================================

class FeaturePermissionInline(admin.TabularInline):
    """Inline for managing permissions gated by a feature."""
    model = FeaturePermission
    extra = 1
    autocomplete_fields = ['permission']
    verbose_name = _('Gated Permission')
    verbose_name_plural = _('Gated Permissions')


# =============================================================================
# FEATURE ADMIN
# =============================================================================

@admin.register(Feature)
class FeatureAdmin(EMenumPermissionMixin, admin.ModelAdmin):
    """
    Admin interface for Feature management.

    Features are platform-level capability definitions.
    Superadmin defines which features exist and their types.
    """

    list_display = [
        'code_display', 'name', 'type_badge', 'category_badge',
        'default_display', 'plan_count', 'is_active', 'sort_order',
    ]
    list_filter = ['feature_type', 'category', 'is_active']
    search_fields = ['code', 'name', 'description']
    readonly_fields = ['id', 'created_at', 'updated_at']
    ordering = ['category', 'sort_order', 'name']
    list_per_page = 50
    list_editable = ['sort_order', 'is_active']
    inlines = [FeaturePermissionInline]

    fieldsets = (
        (None, {
            'fields': ('id', 'code', 'name', 'description')
        }),
        (_('Type & Configuration'), {
            'fields': ('feature_type', 'default_value', 'category', 'sort_order')
        }),
        (_('Status'), {
            'fields': ('is_active', 'metadata')
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def get_fieldsets(self, request, obj=None):
        """Add 'Used By Plans' section only in full change view (not popup)."""
        fieldsets = list(super().get_fieldsets(request, obj))
        if not request.GET.get('_popup') and obj and obj.pk:
            # Insert before Timestamps
            fieldsets.insert(-1, (_('Used By Plans'), {
                'fields': ('plans_using',),
                'classes': ('collapse',),
            }))
        return fieldsets

    def get_readonly_fields(self, request, obj=None):
        """Include plans_using only in full change view (not popup)."""
        readonly = list(super().get_readonly_fields(request, obj))
        if not request.GET.get('_popup') and obj and obj.pk:
            if 'plans_using' not in readonly:
                readonly.append('plans_using')
        else:
            # Remove plans_using in popup context
            readonly = [f for f in readonly if f != 'plans_using']
        return readonly

    def get_queryset(self, request):
        return super().get_queryset(request).filter(
            deleted_at__isnull=True
        ).annotate(
            _plan_count=Count('plan_features')
        )

    def code_display(self, obj):
        """Feature code in monospace with dark theme."""
        return format_html(
            '<code style="background:rgba(99,102,241,0.08);color:#a5b4fc;'
            'padding:2px 8px;border-radius:4px;font-size:11px;font-weight:600;">{}</code>',
            obj.code,
        )
    code_display.short_description = _('Code')
    code_display.admin_order_field = 'code'

    def type_badge(self, obj):
        """Color-coded feature type badge."""
        color = FEATURE_TYPE_COLORS.get(obj.feature_type, '#94a3b8')
        icons = {
            FeatureType.BOOLEAN: 'toggle-right',
            FeatureType.LIMIT: 'hash',
            FeatureType.USAGE: 'chart-line-up',
        }
        icon = icons.get(obj.feature_type, 'question')
        return format_html(
            '<span style="display:inline-flex;align-items:center;gap:4px;'
            'padding:2px 8px;border-radius:4px;font-size:11px;font-weight:600;'
            'background:rgba({},0.12);color:{};">'
            '<i class="ph ph-{}"></i> {}</span>',
            _hex_to_rgb(color), color, icon, obj.get_feature_type_display(),
        )
    type_badge.short_description = _('Type')
    type_badge.admin_order_field = 'feature_type'

    def category_badge(self, obj):
        """Category badge."""
        cat_colors = {
            'menus': '#3b82f6', 'orders': '#22c55e', 'ai': '#8b5cf6',
            'analytics': '#f59e0b', 'branding': '#ec4899', 'support': '#0ea5e9',
            'integrations': '#06b6d4', 'general': '#94a3b8',
        }
        color = cat_colors.get(obj.category, '#94a3b8')
        return format_html(
            '<span style="padding:2px 8px;border-radius:4px;font-size:10px;font-weight:600;'
            'background:rgba({},0.1);color:{};">{}</span>',
            _hex_to_rgb(color), color, obj.category.title(),
        )
    category_badge.short_description = _('Category')
    category_badge.admin_order_field = 'category'

    def default_display(self, obj):
        """Show default value in a readable format."""
        if obj.is_boolean:
            enabled = obj.default_value.get('enabled', False)
            if enabled:
                return format_html('<span style="color:#22c55e;">✓ Enabled</span>')
            return format_html('<span style="color:#6b7280;">✗ Disabled</span>')
        elif obj.is_limit:
            limit = obj.default_value.get('limit', 0)
            if limit == -1:
                return format_html('<span style="color:#22c55e;">∞ Unlimited</span>')
            return format_html('<span style="color:#f59e0b;">{}</span>', limit)
        elif obj.is_usage:
            credits = obj.default_value.get('credits', 0)
            period = obj.default_value.get('reset_period', 'monthly')
            return format_html(
                '<span style="color:#8b5cf6;">{} / {}</span>',
                credits, period,
            )
        return '-'
    default_display.short_description = _('Default')

    def plan_count(self, obj):
        """Number of plans using this feature."""
        count = getattr(obj, '_plan_count', 0)
        return format_html(
            '<span style="color:{};font-weight:600;">{}</span>',
            '#22c55e' if count > 0 else '#6b7280', count,
        )
    plan_count.short_description = _('Plans')
    plan_count.admin_order_field = '_plan_count'

    def plans_using(self, obj):
        """Show which plans use this feature (readonly detail)."""
        plan_features = PlanFeature.objects.filter(
            feature=obj,
        ).select_related('plan').order_by('plan__sort_order')

        if not plan_features.exists():
            return format_html('<em style="color:#6b7280;">Not assigned to any plan</em>')

        rows = []
        for pf in plan_features:
            plan = pf.plan
            color = TIER_COLORS.get(plan.tier, '#94a3b8')
            enabled = '✓' if pf.is_enabled else '✗'
            enabled_color = '#22c55e' if pf.is_enabled else '#ef4444'
            # pf.value is a JSONField (dict) — must escape for format_html
            if pf.value:
                import json
                value_str = json.dumps(pf.value, ensure_ascii=False) if isinstance(pf.value, dict) else str(pf.value)
            else:
                value_str = '-'
            rows.append(format_html(
                '<tr>'
                '<td style="padding:4px 8px;"><span style="color:{};font-weight:600;">'
                '{}</span></td>'
                '<td style="padding:4px 8px;text-align:center;">'
                '<span style="color:{};">{}</span></td>'
                '<td style="padding:4px 8px;color:#94a3b8;font-size:11px;">{}</td>'
                '</tr>',
                color, plan.name, enabled_color, enabled, value_str,
            ))

        from django.utils.safestring import mark_safe
        table_html = (
            '<table style="border-collapse:collapse;">'
            '<thead><tr style="border-bottom:1px solid rgba(148,163,184,0.1);">'
            '<th style="padding:4px 8px;font-size:10px;color:#6b7280;text-align:left;">Plan</th>'
            '<th style="padding:4px 8px;font-size:10px;color:#6b7280;">Enabled</th>'
            '<th style="padding:4px 8px;font-size:10px;color:#6b7280;text-align:left;">Value</th>'
            '</tr></thead><tbody>'
        )
        table_html += ''.join(str(r) for r in rows)
        table_html += '</tbody></table>'
        return mark_safe(table_html)
    plans_using.short_description = _('Plans using this feature')


# =============================================================================
# PLAN ADMIN
# =============================================================================

@admin.register(Plan)
class PlanAdmin(EMenumPermissionMixin, admin.ModelAdmin):
    """
    Admin interface for Plan management.

    Plans define subscription tiers with pricing, limits, and features.
    This is the core configuration for the pricing table.
    """

    list_display = [
        'tier_badge', 'name', 'price_display', 'subscriber_count',
        'features_summary', 'trial_display', 'status_flags', 'sort_order',
    ]
    list_filter = ['tier', 'is_active', 'is_public', 'is_default']
    search_fields = ['name', 'slug', 'description']
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = [
        'id', 'created_at', 'updated_at',
        'pricing_card_preview', 'limits_overview', 'feature_flags_overview',
    ]
    ordering = ['sort_order', 'price_monthly']
    list_per_page = 20
    list_editable = ['sort_order']
    inlines = [PlanFeatureInline, PlanDisplayFeatureInline]

    fieldsets = (
        (None, {
            'fields': ('id', 'name', 'slug', 'tier', 'description', 'short_description')
        }),
        (_('Pricing'), {
            'fields': ('price_monthly', 'price_yearly', 'currency', 'trial_days')
        }),
        (_('Limits'), {
            'fields': ('limits', 'limits_overview'),
            'description': _(
                'JSON format: {"max_menus": 3, "max_products": 200, "max_qr_codes": 10, '
                '"max_users": 5, "max_branches": 1, "storage_mb": 500, "ai_credits_monthly": 100}. '
                'Use -1 for unlimited.'
            ),
        }),
        (_('Feature Flags'), {
            'fields': ('feature_flags', 'feature_flags_overview'),
            'description': _(
                'JSON format: {"ai_content_generation": true, "analytics_basic": true, '
                '"custom_domain": false, "api_access": false, ...}'
            ),
        }),
        (_('Display & Status'), {
            'fields': (
                'is_active', 'is_public', 'is_default', 'is_custom',
                'highlight_text', 'sort_order',
            )
        }),
        (_('Pricing Card Preview'), {
            'fields': ('pricing_card_preview',),
            'classes': ('collapse',),
        }),
        (_('Metadata'), {
            'fields': ('metadata',),
            'classes': ('collapse',),
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).filter(
            deleted_at__isnull=True
        ).annotate(
            _subscriber_count=Count(
                'subscriptions',
                filter=Q(
                    subscriptions__deleted_at__isnull=True,
                    subscriptions__status__in=[
                        SubscriptionStatus.ACTIVE,
                        SubscriptionStatus.TRIALING,
                    ]
                )
            )
        )

    def tier_badge(self, obj):
        """Color-coded tier badge with icon."""
        color = TIER_COLORS.get(obj.tier, '#94a3b8')
        icon = TIER_ICONS.get(obj.tier, 'star')
        return format_html(
            '<span style="display:inline-flex;align-items:center;gap:4px;'
            'padding:3px 10px;border-radius:6px;font-size:11px;font-weight:700;'
            'background:rgba({},0.12);color:{};">'
            '<i class="ph ph-{}"></i> {}</span>',
            _hex_to_rgb(color), color, icon, obj.get_tier_display(),
        )
    tier_badge.short_description = _('Tier')
    tier_badge.admin_order_field = 'tier'

    def price_display(self, obj):
        """Price display with monthly/yearly toggle info."""
        if obj.price_monthly == 0:
            return format_html(
                '<span style="color:#22c55e;font-weight:700;font-size:14px;">FREE</span>'
            )
        discount = obj.yearly_discount_percentage
        yearly_note = ''
        if discount > 0:
            yearly_note = format_html(
                '<br><span style="color:#22c55e;font-size:10px;">'
                '{}% off yearly</span>', discount,
            )
        return format_html(
            '<span style="color:#e2e8f0;font-weight:700;font-size:14px;">{}</span>'
            '<span style="color:#6b7280;font-size:10px;"> /ay</span>{}',
            obj.formatted_price_monthly, yearly_note,
        )
    price_display.short_description = _('Price')
    price_display.admin_order_field = 'price_monthly'

    def subscriber_count(self, obj):
        """Active subscriber count."""
        count = getattr(obj, '_subscriber_count', 0)
        color = '#22c55e' if count > 0 else '#6b7280'
        return format_html(
            '<span style="display:inline-flex;align-items:center;gap:4px;color:{};font-weight:600;">'
            '<i class="ph ph-users"></i> {}</span>',
            color, count,
        )
    subscriber_count.short_description = _('Subscribers')
    subscriber_count.admin_order_field = '_subscriber_count'

    def features_summary(self, obj):
        """Compact feature flag summary."""
        flags = obj.feature_flags or {}
        enabled = sum(1 for v in flags.values() if v)
        total = len(flags)
        limits = obj.limits or {}
        limit_count = len(limits)

        return format_html(
            '<span style="font-size:11px;">'
            '<span style="color:#22c55e;">{}/{} flags</span>'
            ' · <span style="color:#f59e0b;">{} limits</span></span>',
            enabled, total, limit_count,
        )
    features_summary.short_description = _('Features')

    def trial_display(self, obj):
        """Trial days display."""
        if obj.trial_days == 0:
            return format_html('<span style="color:#6b7280;">—</span>')
        return format_html(
            '<span style="color:#0ea5e9;font-weight:600;">{} gün</span>',
            obj.trial_days,
        )
    trial_display.short_description = _('Trial')

    def status_flags(self, obj):
        """Status flag icons."""
        flags = []
        if obj.is_active:
            flags.append('<span title="Active" style="color:#22c55e;"><i class="ph-fill ph-check-circle"></i></span>')
        else:
            flags.append('<span title="Inactive" style="color:#ef4444;"><i class="ph ph-x-circle"></i></span>')
        if obj.is_public:
            flags.append('<span title="Public" style="color:#3b82f6;"><i class="ph ph-eye"></i></span>')
        if obj.is_default:
            flags.append('<span title="Default" style="color:#f59e0b;"><i class="ph-fill ph-star"></i></span>')
        if obj.is_custom:
            flags.append('<span title="Custom" style="color:#8b5cf6;"><i class="ph ph-wrench"></i></span>')
        return format_html(
            '<span style="display:flex;gap:6px;font-size:16px;">{}</span>',
            format_html(' '.join(flags)),
        )
    status_flags.short_description = _('Status')

    def limits_overview(self, obj):
        """Visual overview of plan limits (readonly field)."""
        limits = obj.limits or {}
        if not limits:
            return format_html('<em style="color:#6b7280;">No limits configured</em>')

        labels = {
            'max_menus': ('fork-knife', 'Menus'),
            'max_products': ('package', 'Products'),
            'max_categories': ('folders', 'Categories'),
            'max_qr_codes': ('qr-code', 'QR Codes'),
            'max_users': ('users', 'Users'),
            'max_branches': ('map-pin', 'Branches'),
            'storage_mb': ('hard-drive', 'Storage (MB)'),
            'ai_credits_monthly': ('sparkle', 'AI Credits/mo'),
        }

        items = []
        for key, value in limits.items():
            icon, label = labels.get(key, ('question', key))
            if value == -1:
                val_html = '<span style="color:#22c55e;">∞</span>'
            else:
                val_html = f'<span style="color:#e2e8f0;font-weight:700;">{value}</span>'
            items.append(
                f'<div style="display:flex;align-items:center;gap:6px;padding:4px 0;">'
                f'<i class="ph ph-{icon}" style="color:#6b7280;"></i>'
                f'<span style="color:#94a3b8;font-size:12px;min-width:100px;">{label}</span>'
                f'{val_html}</div>'
            )
        return format_html(''.join(items))
    limits_overview.short_description = _('Limits (visual)')

    def feature_flags_overview(self, obj):
        """Visual overview of feature flags (readonly field)."""
        flags = obj.feature_flags or {}
        if not flags:
            return format_html('<em style="color:#6b7280;">No feature flags configured</em>')

        items = []
        for key, value in sorted(flags.items()):
            if value:
                icon = '<span style="color:#22c55e;"><i class="ph-fill ph-check-circle"></i></span>'
            else:
                icon = '<span style="color:#ef4444;opacity:0.5;"><i class="ph ph-x-circle"></i></span>'
            name = key.replace('_', ' ').title()
            items.append(
                f'<div style="display:flex;align-items:center;gap:6px;padding:2px 0;font-size:12px;">'
                f'{icon} <span style="color:#94a3b8;">{name}</span></div>'
            )
        return format_html(''.join(items))
    feature_flags_overview.short_description = _('Feature Flags (visual)')

    def pricing_card_preview(self, obj):
        """HTML preview of how the plan appears on the pricing page."""
        color = TIER_COLORS.get(obj.tier, '#94a3b8')
        icon = TIER_ICONS.get(obj.tier, 'star')

        # Build limits list
        limits_html = ''
        for key, value in (obj.limits or {}).items():
            label = key.replace('max_', '').replace('_', ' ').title()
            if key == 'storage_mb':
                label = 'Storage'
                val = f'{value} MB' if value != -1 else '∞'
            elif key == 'ai_credits_monthly':
                label = 'AI Credits'
                val = str(value) if value != -1 else '∞'
            elif value == -1:
                val = '∞ Unlimited'
            else:
                val = str(value)
            limits_html += f'<div style="padding:3px 0;color:#94a3b8;font-size:12px;display:flex;justify-content:space-between;"><span>{label}</span><span style="color:#e2e8f0;font-weight:600;">{val}</span></div>'

        # Build features list
        features_html = ''
        for key, value in sorted((obj.feature_flags or {}).items()):
            name = key.replace('_', ' ').title()
            check = '✓' if value else '✗'
            check_color = '#22c55e' if value else '#6b7280'
            features_html += f'<div style="padding:2px 0;font-size:11px;"><span style="color:{check_color};margin-right:4px;">{check}</span><span style="color:#94a3b8;">{name}</span></div>'

        highlight = ''
        if obj.highlight_text:
            highlight = f'<div style="position:absolute;top:-10px;right:12px;background:{color};color:#fff;padding:2px 10px;border-radius:10px;font-size:10px;font-weight:700;">{obj.highlight_text}</div>'

        return format_html(
            '<div style="position:relative;max-width:280px;background:rgba(15,18,25,0.8);'
            'border:1px solid rgba({rgb},0.3);border-radius:12px;padding:20px;'
            'font-family:system-ui;">'
            '{highlight}'
            '<div style="text-align:center;margin-bottom:12px;">'
            '<i class="ph ph-{icon}" style="font-size:24px;color:{color};"></i>'
            '<h3 style="color:{color};font-size:16px;margin:6px 0 2px;">{name}</h3>'
            '<div style="color:#e2e8f0;font-size:24px;font-weight:800;">{price}</div>'
            '<div style="color:#94a3b8;font-size:12px;margin-top:2px;">{yearly_info}</div>'
            '<div style="color:#6b7280;font-size:11px;">{short}</div>'
            '</div>'
            '<div style="border-top:1px solid rgba(148,163,184,0.1);padding-top:10px;margin-top:10px;">'
            '<div style="color:#6b7280;font-size:10px;text-transform:uppercase;margin-bottom:6px;">Limits</div>'
            '{limits}'
            '</div>'
            '<div style="border-top:1px solid rgba(148,163,184,0.1);padding-top:10px;margin-top:10px;">'
            '<div style="color:#6b7280;font-size:10px;text-transform:uppercase;margin-bottom:6px;">Features</div>'
            '{features}'
            '</div>'
            '</div>',
            rgb=_hex_to_rgb(color),
            highlight=format_html(highlight),
            icon=icon,
            color=color,
            name=obj.name,
            price=obj.formatted_price_monthly,
            yearly_info=(
                f'Yearly: {obj.formatted_price_yearly}/yr '
                f'(₺{obj.yearly_per_month}/mo, -{obj.yearly_discount_percentage}%)'
                if obj.price_yearly and obj.price_yearly > 0
                else ''
            ),
            short=obj.short_description or '',
            limits=format_html(limits_html),
            features=format_html(features_html),
        )
    pricing_card_preview.short_description = _('Pricing Card Preview')

    # Custom actions
    actions = ['make_active', 'make_inactive', 'set_as_default', 'duplicate_plan']

    @admin.action(description=_('Activate selected plans'))
    def make_active(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, _('%d plan(s) activated.') % updated)

    @admin.action(description=_('Deactivate selected plans'))
    def make_inactive(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, _('%d plan(s) deactivated.') % updated)

    @admin.action(description=_('Set as default plan'))
    def set_as_default(self, request, queryset):
        if queryset.count() != 1:
            self.message_user(request, _('Please select exactly one plan.'), level='error')
            return
        plan = queryset.first()
        plan.set_as_default()
        self.message_user(request, _('"%s" is now the default plan.') % plan.name)

    @admin.action(description=_('Duplicate selected plan'))
    def duplicate_plan(self, request, queryset):
        for plan in queryset:
            plan.pk = None
            plan.name = f'{plan.name} (Copy)'
            plan.slug = f'{plan.slug}-copy'
            plan.is_default = False
            plan.is_active = False
            plan.save()
        self.message_user(request, _('%d plan(s) duplicated.') % queryset.count())


# =============================================================================
# PLAN FEATURE ADMIN
# =============================================================================

@admin.register(PlanFeature)
class PlanFeatureAdmin(EMenumPermissionMixin, admin.ModelAdmin):
    """
    Admin interface for PlanFeature junction table.

    Manages the relationship between Plans and Features with
    plan-specific configuration values.
    """

    list_display = [
        'plan_display', 'feature_display', 'enabled_badge',
        'value_display', 'sort_order',
    ]
    list_filter = ['plan__tier', 'is_enabled', 'feature__feature_type', 'feature__category']
    search_fields = ['plan__name', 'feature__code', 'feature__name']
    autocomplete_fields = ['plan', 'feature']
    readonly_fields = ['id', 'created_at', 'updated_at']
    ordering = ['plan__sort_order', 'sort_order', 'feature__name']
    list_per_page = 50

    fieldsets = (
        (None, {
            'fields': ('id', 'plan', 'feature', 'is_enabled', 'value', 'sort_order')
        }),
        (_('Metadata'), {
            'fields': ('metadata',),
            'classes': ('collapse',),
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('plan', 'feature')

    def plan_display(self, obj):
        """Plan name with tier badge."""
        color = TIER_COLORS.get(obj.plan.tier, '#94a3b8')
        return format_html(
            '<span style="color:{};font-weight:600;">{}</span>',
            color, obj.plan.name,
        )
    plan_display.short_description = _('Plan')
    plan_display.admin_order_field = 'plan__sort_order'

    def feature_display(self, obj):
        """Feature code + type."""
        type_color = FEATURE_TYPE_COLORS.get(obj.feature.feature_type, '#94a3b8')
        return format_html(
            '<code style="background:rgba(99,102,241,0.08);color:#a5b4fc;'
            'padding:1px 6px;border-radius:3px;font-size:11px;">{}</code>'
            ' <span style="color:{};font-size:10px;">({})</span>',
            obj.feature.code, type_color, obj.feature.get_feature_type_display(),
        )
    feature_display.short_description = _('Feature')
    feature_display.admin_order_field = 'feature__code'

    def enabled_badge(self, obj):
        """Enabled/disabled badge."""
        if obj.is_enabled:
            return format_html(
                '<span style="color:#22c55e;"><i class="ph-fill ph-check-circle"></i> Enabled</span>'
            )
        return format_html(
            '<span style="color:#ef4444;opacity:0.6;"><i class="ph ph-x-circle"></i> Disabled</span>'
        )
    enabled_badge.short_description = _('Status')
    enabled_badge.admin_order_field = 'is_enabled'

    def value_display(self, obj):
        """Formatted value display."""
        value = obj.value
        if not value:
            return format_html('<span style="color:#6b7280;">—</span>')
        return format_html(
            '<code style="color:#94a3b8;font-size:11px;">{}</code>',
            str(value),
        )
    value_display.short_description = _('Value')


# =============================================================================
# SUBSCRIPTION ADMIN
# =============================================================================

@admin.register(Subscription)
class SubscriptionAdmin(EMenumPermissionMixin, admin.ModelAdmin):
    """
    Admin interface for Subscription management.

    Manages organization subscriptions with full lifecycle support:
    trial → active → past_due → cancelled/expired/suspended
    """

    list_display = [
        'organization_display', 'plan_badge', 'status_badge',
        'billing_display', 'period_display', 'trial_display',
        'payment_display',
    ]
    list_filter = ['status', 'plan__tier', 'billing_period', 'payment_method']
    search_fields = ['organization__name', 'organization__slug', 'plan__name']
    autocomplete_fields = ['organization', 'plan']
    readonly_fields = [
        'id', 'created_at', 'updated_at',
        'subscription_health', 'usage_summary',
    ]
    ordering = ['-created_at']
    list_per_page = 30
    date_hierarchy = 'created_at'
    inlines = [SubscriptionInvoiceInline]

    fieldsets = (
        (None, {
            'fields': ('id', 'organization', 'plan', 'status')
        }),
        (_('Subscription Health'), {
            'fields': ('subscription_health',),
        }),
        (_('Billing'), {
            'fields': ('billing_period', 'payment_method', 'current_price', 'currency')
        }),
        (_('Trial'), {
            'fields': ('trial_ends_at',),
        }),
        (_('Billing Period'), {
            'fields': ('current_period_start', 'current_period_end', 'next_billing_date')
        }),
        (_('Cancellation'), {
            'fields': ('cancelled_at', 'cancel_reason', 'cancel_at_period_end'),
            'classes': ('collapse',)
        }),
        (_('External Payment'), {
            'fields': ('external_subscription_id', 'external_customer_id', 'payment_details'),
            'classes': ('collapse',)
        }),
        (_('Metadata'), {
            'fields': ('metadata',),
            'classes': ('collapse',),
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).filter(
            deleted_at__isnull=True
        ).select_related('organization', 'plan')

    def organization_display(self, obj):
        """Organization name with link."""
        return format_html(
            '<span style="font-weight:600;color:#e2e8f0;">{}</span>',
            obj.organization.name,
        )
    organization_display.short_description = _('Organization')
    organization_display.admin_order_field = 'organization__name'

    def plan_badge(self, obj):
        """Plan tier badge."""
        color = TIER_COLORS.get(obj.plan.tier, '#94a3b8')
        icon = TIER_ICONS.get(obj.plan.tier, 'star')
        return format_html(
            '<span style="display:inline-flex;align-items:center;gap:3px;'
            'padding:2px 8px;border-radius:4px;font-size:11px;font-weight:600;'
            'background:rgba({},0.12);color:{};">'
            '<i class="ph ph-{}"></i> {}</span>',
            _hex_to_rgb(color), color, icon, obj.plan.name,
        )
    plan_badge.short_description = _('Plan')
    plan_badge.admin_order_field = 'plan__tier'

    def status_badge(self, obj):
        """Color-coded status badge."""
        color = STATUS_COLORS.get(obj.status, '#6b7280')
        icons = {
            SubscriptionStatus.TRIALING: 'hourglass-medium',
            SubscriptionStatus.ACTIVE: 'check-circle',
            SubscriptionStatus.PAST_DUE: 'warning',
            SubscriptionStatus.CANCELLED: 'x-circle',
            SubscriptionStatus.EXPIRED: 'clock-countdown',
            SubscriptionStatus.SUSPENDED: 'prohibit',
        }
        icon = icons.get(obj.status, 'question')
        return format_html(
            '<span style="display:inline-flex;align-items:center;gap:3px;'
            'padding:2px 8px;border-radius:4px;font-size:11px;font-weight:600;'
            'background:rgba({},0.12);color:{};">'
            '<i class="ph ph-{}"></i> {}</span>',
            _hex_to_rgb(color), color, icon, obj.get_status_display(),
        )
    status_badge.short_description = _('Status')
    status_badge.admin_order_field = 'status'

    def billing_display(self, obj):
        """Price and billing period."""
        period = 'mo' if obj.billing_period == BillingPeriod.MONTHLY else 'yr'
        return format_html(
            '<span style="color:#e2e8f0;font-weight:600;">{}</span>'
            '<span style="color:#6b7280;font-size:10px;"> /{}</span>',
            obj.formatted_price, period,
        )
    billing_display.short_description = _('Billing')

    def period_display(self, obj):
        """Current billing period dates."""
        if not obj.current_period_end:
            return format_html('<span style="color:#6b7280;">—</span>')
        now = timezone.now()
        remaining = (obj.current_period_end - now).days
        color = '#22c55e' if remaining > 7 else '#f59e0b' if remaining > 0 else '#ef4444'
        return format_html(
            '<span style="font-size:11px;color:#94a3b8;">'
            '{} → {}</span><br>'
            '<span style="color:{};font-size:10px;font-weight:600;">{} days left</span>',
            obj.current_period_start.strftime('%d/%m') if obj.current_period_start else '?',
            obj.current_period_end.strftime('%d/%m/%Y'),
            color, max(0, remaining),
        )
    period_display.short_description = _('Period')

    def trial_display(self, obj):
        """Trial status."""
        if not obj.is_trialing or not obj.trial_ends_at:
            return format_html('<span style="color:#6b7280;">—</span>')
        remaining = obj.trial_remaining_days
        color = '#0ea5e9' if remaining > 3 else '#f59e0b' if remaining > 0 else '#ef4444'
        return format_html(
            '<span style="color:{};font-weight:600;">{} gün kaldı</span>',
            color, remaining,
        )
    trial_display.short_description = _('Trial')

    def payment_display(self, obj):
        """Payment method indicator."""
        if not obj.payment_method:
            return format_html('<span style="color:#6b7280;">—</span>')
        icons = {
            'CREDIT_CARD': 'credit-card',
            'BANK_TRANSFER': 'bank',
            'IYZICO': 'credit-card',
            'OTHER': 'wallet',
        }
        icon = icons.get(obj.payment_method, 'wallet')
        return format_html(
            '<span style="color:#94a3b8;font-size:11px;">'
            '<i class="ph ph-{}"></i> {}</span>',
            icon, obj.get_payment_method_display(),
        )
    payment_display.short_description = _('Payment')

    def subscription_health(self, obj):
        """Visual subscription health card (readonly detail)."""
        color = STATUS_COLORS.get(obj.status, '#6b7280')
        plan_color = TIER_COLORS.get(obj.plan.tier, '#94a3b8')

        # Health indicators
        indicators = []
        if obj.is_valid:
            indicators.append(('check-circle', '#22c55e', 'Valid & Active'))
        else:
            indicators.append(('warning', '#ef4444', 'Not Valid'))

        if obj.is_trialing and obj.trial_ends_at:
            indicators.append(('hourglass-medium', '#0ea5e9', f'Trial: {obj.trial_remaining_days} days left'))

        if obj.cancel_at_period_end:
            indicators.append(('clock-countdown', '#f59e0b', 'Will cancel at period end'))

        if obj.current_period_end:
            days = (obj.current_period_end - timezone.now()).days
            if days < 0:
                indicators.append(('warning-circle', '#ef4444', f'Period expired {abs(days)} days ago'))
            elif days < 7:
                indicators.append(('warning', '#f59e0b', f'Period ends in {days} days'))

        indicator_html = ''.join(
            f'<div style="display:flex;align-items:center;gap:6px;padding:3px 0;">'
            f'<i class="ph ph-{i}" style="color:{c};"></i>'
            f'<span style="color:#94a3b8;font-size:12px;">{t}</span></div>'
            for i, c, t in indicators
        )

        return format_html(
            '<div style="max-width:400px;background:rgba(15,18,25,0.6);'
            'border:1px solid rgba({rgb},0.2);border-radius:8px;padding:16px;">'
            '<div style="display:flex;align-items:center;gap:8px;margin-bottom:10px;">'
            '<span style="display:inline-flex;align-items:center;gap:3px;padding:3px 10px;'
            'border-radius:6px;background:rgba({rgb},0.12);color:{color};font-weight:700;'
            'font-size:12px;">{status}</span>'
            '<span style="color:{plan_color};font-weight:600;">{plan}</span></div>'
            '{indicators}</div>',
            rgb=_hex_to_rgb(color), color=color,
            status=obj.get_status_display(),
            plan_color=plan_color, plan=obj.plan.name,
            indicators=format_html(indicator_html),
        )
    subscription_health.short_description = _('Health')

    def usage_summary(self, obj):
        """Usage summary for this organization (readonly field)."""
        usages = OrganizationUsage.objects.filter(
            organization=obj.organization,
        ).select_related('feature')

        if not usages.exists():
            return format_html('<em style="color:#6b7280;">No usage data</em>')

        rows = []
        for usage in usages:
            if usage.usage_limit == -1:
                pct = 0
                val = f'{usage.current_usage} / ∞'
            elif usage.usage_limit > 0:
                pct = min(100, (usage.current_usage / usage.usage_limit) * 100)
                val = f'{usage.current_usage} / {usage.usage_limit}'
            else:
                pct = 0
                val = f'{usage.current_usage} / 0'
            color = '#22c55e' if pct < 70 else '#f59e0b' if pct < 90 else '#ef4444'
            rows.append(format_html(
                '<tr>'
                '<td style="padding:3px 8px;color:#94a3b8;font-size:12px;">{}</td>'
                '<td style="padding:3px 8px;color:#e2e8f0;font-size:12px;text-align:right;">{}</td>'
                '<td style="padding:3px 8px;">'
                '<div style="width:60px;height:4px;background:rgba(148,163,184,0.1);border-radius:2px;">'
                '<div style="width:{}%;height:100%;background:{};border-radius:2px;"></div></div></td>'
                '</tr>',
                usage.feature.name, val, int(pct), color,
            ))
        from django.utils.safestring import mark_safe
        return mark_safe(
            '<table style="border-collapse:collapse;"><tbody>'
            + ''.join(str(r) for r in rows)
            + '</tbody></table>'
        )
    usage_summary.short_description = _('Usage Summary')

    # Custom actions
    actions = ['activate_subscriptions', 'suspend_subscriptions', 'expire_subscriptions']

    @admin.action(description=_('Activate selected subscriptions'))
    def activate_subscriptions(self, request, queryset):
        count = 0
        for sub in queryset:
            if sub.status != SubscriptionStatus.ACTIVE:
                sub.activate()
                count += 1
        self.message_user(request, _('%d subscription(s) activated.') % count)

    @admin.action(description=_('Suspend selected subscriptions'))
    def suspend_subscriptions(self, request, queryset):
        count = 0
        for sub in queryset:
            if sub.status != SubscriptionStatus.SUSPENDED:
                sub.suspend(reason='Admin action')
                count += 1
        self.message_user(request, _('%d subscription(s) suspended.') % count)

    @admin.action(description=_('Expire selected subscriptions'))
    def expire_subscriptions(self, request, queryset):
        count = 0
        for sub in queryset:
            sub.expire()
            count += 1
        self.message_user(request, _('%d subscription(s) expired.') % count)


# =============================================================================
# INVOICE ADMIN
# =============================================================================

@admin.register(Invoice)
class InvoiceAdmin(EMenumPermissionMixin, admin.ModelAdmin):
    """
    Admin interface for Invoice management.

    Manages billing records with lifecycle: DRAFT → PENDING → PAID.
    """

    list_display = [
        'invoice_number_display', 'organization_display', 'status_badge',
        'amount_display', 'due_date_display', 'paid_display',
        'period_display',
    ]
    list_filter = ['status', 'currency', 'created_at']
    search_fields = [
        'invoice_number', 'organization__name',
        'external_invoice_id', 'external_payment_id',
    ]
    autocomplete_fields = ['organization', 'subscription']
    readonly_fields = ['id', 'created_at', 'updated_at', 'invoice_summary']
    ordering = ['-created_at']
    list_per_page = 30
    date_hierarchy = 'created_at'

    fieldsets = (
        (None, {
            'fields': ('id', 'organization', 'subscription', 'invoice_number', 'status')
        }),
        (_('Invoice Summary'), {
            'fields': ('invoice_summary',),
        }),
        (_('Amounts'), {
            'fields': ('amount_subtotal', 'amount_tax', 'amount_total', 'amount_paid', 'amount_refunded', 'currency')
        }),
        (_('Dates'), {
            'fields': ('due_date', 'paid_at', 'period_start', 'period_end')
        }),
        (_('Details'), {
            'fields': ('description', 'line_items', 'billing_address'),
            'classes': ('collapse',),
        }),
        (_('External Payment'), {
            'fields': ('external_invoice_id', 'external_payment_id', 'payment_details', 'pdf_url'),
            'classes': ('collapse',)
        }),
        (_('Metadata'), {
            'fields': ('metadata',),
            'classes': ('collapse',),
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).filter(
            deleted_at__isnull=True
        ).select_related('organization', 'subscription', 'subscription__plan')

    def invoice_number_display(self, obj):
        """Invoice number in styled format."""
        return format_html(
            '<code style="background:rgba(99,102,241,0.08);color:#a5b4fc;'
            'padding:2px 8px;border-radius:4px;font-size:11px;font-weight:600;">{}</code>',
            obj.invoice_number,
        )
    invoice_number_display.short_description = _('#')
    invoice_number_display.admin_order_field = 'invoice_number'

    def organization_display(self, obj):
        """Organization name."""
        return format_html(
            '<span style="font-weight:600;color:#e2e8f0;">{}</span>',
            obj.organization.name,
        )
    organization_display.short_description = _('Organization')
    organization_display.admin_order_field = 'organization__name'

    def status_badge(self, obj):
        """Color-coded invoice status."""
        color = INVOICE_STATUS_COLORS.get(obj.status, '#6b7280')
        icons = {
            InvoiceStatus.DRAFT: 'note-pencil',
            InvoiceStatus.PENDING: 'clock',
            InvoiceStatus.PAID: 'check-circle',
            InvoiceStatus.VOID: 'prohibit',
            InvoiceStatus.REFUNDED: 'arrow-counter-clockwise',
            InvoiceStatus.UNCOLLECTIBLE: 'warning',
        }
        icon = icons.get(obj.status, 'question')
        return format_html(
            '<span style="display:inline-flex;align-items:center;gap:3px;'
            'padding:2px 8px;border-radius:4px;font-size:11px;font-weight:600;'
            'background:rgba({},0.12);color:{};">'
            '<i class="ph ph-{}"></i> {}</span>',
            _hex_to_rgb(color), color, icon, obj.get_status_display(),
        )
    status_badge.short_description = _('Status')
    status_badge.admin_order_field = 'status'

    def amount_display(self, obj):
        """Formatted amount with currency."""
        symbols = {'TRY': '₺', 'USD': '$', 'EUR': '€', 'GBP': '£'}
        symbol = symbols.get(obj.currency, obj.currency)
        # Format number first, then pass to format_html
        # (format_html doesn't support :,.2f on SafeString arguments)
        formatted_amount = '{:,.2f}'.format(float(obj.amount_total or 0))
        return format_html(
            '<span style="color:#e2e8f0;font-weight:700;font-size:13px;">{}{}</span>',
            symbol, formatted_amount,
        )
    amount_display.short_description = _('Total')
    amount_display.admin_order_field = 'amount_total'

    def due_date_display(self, obj):
        """Due date with overdue indicator."""
        if not obj.due_date:
            return format_html('<span style="color:#6b7280;">—</span>')
        now = timezone.now()
        is_overdue = obj.due_date < now and obj.status == InvoiceStatus.PENDING
        color = '#ef4444' if is_overdue else '#94a3b8'
        overdue_tag = ' <span style="color:#ef4444;font-size:9px;font-weight:700;">OVERDUE</span>' if is_overdue else ''
        return format_html(
            '<span style="color:{};font-size:12px;">{}</span>{}',
            color, obj.due_date.strftime('%d/%m/%Y'), format_html(overdue_tag),
        )
    due_date_display.short_description = _('Due Date')
    due_date_display.admin_order_field = 'due_date'

    def paid_display(self, obj):
        """Paid date."""
        if not obj.paid_at:
            return format_html('<span style="color:#6b7280;">—</span>')
        return format_html(
            '<span style="color:#22c55e;font-size:12px;">'
            '<i class="ph ph-check"></i> {}</span>',
            obj.paid_at.strftime('%d/%m/%Y'),
        )
    paid_display.short_description = _('Paid')
    paid_display.admin_order_field = 'paid_at'

    def period_display(self, obj):
        """Billing period covered."""
        if not obj.period_start or not obj.period_end:
            return format_html('<span style="color:#6b7280;">—</span>')
        return format_html(
            '<span style="color:#94a3b8;font-size:11px;">{} → {}</span>',
            obj.period_start.strftime('%d/%m'),
            obj.period_end.strftime('%d/%m/%Y'),
        )
    period_display.short_description = _('Period')

    def invoice_summary(self, obj):
        """Visual invoice summary card (readonly detail)."""
        color = INVOICE_STATUS_COLORS.get(obj.status, '#6b7280')
        symbols = {'TRY': '₺', 'USD': '$', 'EUR': '€', 'GBP': '£'}
        symbol = symbols.get(obj.currency, obj.currency)

        # Line items
        items_html = ''
        for item in (obj.line_items or []):
            desc = item.get('description', '—')
            qty = item.get('quantity', 1)
            unit_price = item.get('unit_price', 0)
            amount = item.get('amount', qty * unit_price)
            items_html += (
                f'<tr><td style="padding:3px 8px;color:#94a3b8;font-size:12px;">{desc}</td>'
                f'<td style="padding:3px 8px;color:#e2e8f0;font-size:12px;text-align:right;">'
                f'{symbol}{amount:,.2f}</td></tr>'
            )

        if not items_html:
            items_html = '<tr><td colspan="2" style="padding:3px 8px;color:#6b7280;font-size:12px;"><em>No line items</em></td></tr>'

        # Pre-format numbers (format_html doesn't support :,.2f on SafeString)
        subtotal_str = '{:,.2f}'.format(float(obj.amount_subtotal or 0))
        tax_str = '{:,.2f}'.format(float(obj.amount_tax or 0))
        total_str = '{:,.2f}'.format(float(obj.amount_total or 0))

        return format_html(
            '<div style="max-width:400px;background:rgba(15,18,25,0.6);'
            'border:1px solid rgba({rgb},0.2);border-radius:8px;padding:16px;">'
            '<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px;">'
            '<span style="color:#e2e8f0;font-weight:700;font-size:14px;">{number}</span>'
            '<span style="padding:2px 8px;border-radius:4px;background:rgba({rgb},0.12);'
            'color:{color};font-size:11px;font-weight:600;">{status}</span></div>'
            '<table style="width:100%;border-collapse:collapse;margin-bottom:8px;">{items}</table>'
            '<div style="border-top:1px solid rgba(148,163,184,0.1);padding-top:8px;">'
            '<div style="display:flex;justify-content:space-between;color:#94a3b8;font-size:12px;">'
            '<span>Subtotal</span><span>{symbol}{subtotal}</span></div>'
            '<div style="display:flex;justify-content:space-between;color:#94a3b8;font-size:12px;">'
            '<span>Tax</span><span>{symbol}{tax}</span></div>'
            '<div style="display:flex;justify-content:space-between;color:#e2e8f0;font-weight:700;'
            'font-size:14px;margin-top:4px;">'
            '<span>Total</span><span>{symbol}{total}</span></div></div></div>',
            rgb=_hex_to_rgb(color), color=color,
            number=obj.invoice_number,
            status=obj.get_status_display(),
            items=format_html(items_html),
            symbol=symbol,
            subtotal=subtotal_str,
            tax=tax_str,
            total=total_str,
        )
    invoice_summary.short_description = _('Summary')

    # Custom actions
    actions = ['mark_as_paid', 'mark_as_void', 'finalize_invoices', 'export_pdf']

    @admin.action(description=_('Mark as paid'))
    def mark_as_paid(self, request, queryset):
        count = 0
        for inv in queryset.filter(status=InvoiceStatus.PENDING):
            inv.status = InvoiceStatus.PAID
            inv.paid_at = timezone.now()
            inv.amount_paid = inv.amount_total
            inv.save(update_fields=['status', 'paid_at', 'amount_paid', 'updated_at'])
            count += 1
        self.message_user(request, _('%d invoice(s) marked as paid.') % count)

    @admin.action(description=_('Void selected invoices'))
    def mark_as_void(self, request, queryset):
        count = queryset.exclude(status=InvoiceStatus.PAID).update(status=InvoiceStatus.VOID)
        self.message_user(request, _('%d invoice(s) voided.') % count)

    @admin.action(description=_('Finalize (draft → pending)'))
    def finalize_invoices(self, request, queryset):
        count = queryset.filter(status=InvoiceStatus.DRAFT).update(status=InvoiceStatus.PENDING)
        self.message_user(request, _('%d invoice(s) finalized.') % count)

    @admin.action(description=_('Export PDF'))
    def export_pdf(self, request, queryset):
        """Export selected invoices as PDF. Single → direct PDF download,
        multiple → ZIP archive."""
        import zipfile
        from django.http import HttpResponse

        from apps.subscriptions.services.invoice_pdf import generate_invoice_pdf

        invoices = list(
            queryset.select_related(
                'organization', 'subscription', 'subscription__plan'
            )
        )

        if len(invoices) == 1:
            inv = invoices[0]
            pdf = generate_invoice_pdf(inv)
            if not pdf:
                self.message_user(
                    request,
                    _('PDF oluşturulamadı. xhtml2pdf kurulu olduğundan emin olun.'),
                    level='error',
                )
                return
            response = HttpResponse(pdf.read(), content_type='application/pdf')
            response['Content-Disposition'] = (
                f'attachment; filename="fatura-{inv.invoice_number}.pdf"'
            )
            return response

        # Multiple invoices → ZIP
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
            for inv in invoices:
                pdf = generate_invoice_pdf(inv)
                if pdf:
                    zf.writestr(f'fatura-{inv.invoice_number}.pdf', pdf.read())

        zip_buffer.seek(0)
        response = HttpResponse(zip_buffer.read(), content_type='application/zip')
        response['Content-Disposition'] = 'attachment; filename="faturalar.zip"'
        return response


# =============================================================================
# ORGANIZATION USAGE ADMIN
# =============================================================================

@admin.register(OrganizationUsage)
class OrganizationUsageAdmin(EMenumPermissionMixin, admin.ModelAdmin):
    """
    Admin interface for OrganizationUsage tracking.

    Shows resource consumption per organization against plan limits.
    """

    list_display = [
        'organization_display', 'feature_display', 'usage_bar',
        'current_usage', 'usage_limit', 'period_display', 'status_indicator',
    ]
    list_filter = ['feature__category', 'feature__feature_type']
    search_fields = ['organization__name', 'feature__code', 'feature__name']
    autocomplete_fields = ['organization', 'feature']
    readonly_fields = ['id', 'created_at', 'updated_at', 'last_reset_at', 'last_usage_at']
    ordering = ['organization__name', 'feature__category', 'feature__sort_order']
    list_per_page = 50

    fieldsets = (
        (None, {
            'fields': ('id', 'organization', 'feature')
        }),
        (_('Usage'), {
            'fields': ('current_usage', 'usage_limit')
        }),
        (_('Period'), {
            'fields': ('period_start', 'period_end', 'last_reset_at', 'last_usage_at')
        }),
        (_('Metadata'), {
            'fields': ('metadata',),
            'classes': ('collapse',),
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('organization', 'feature')

    def organization_display(self, obj):
        return format_html(
            '<span style="font-weight:600;color:#e2e8f0;">{}</span>',
            obj.organization.name,
        )
    organization_display.short_description = _('Organization')
    organization_display.admin_order_field = 'organization__name'

    def feature_display(self, obj):
        type_color = FEATURE_TYPE_COLORS.get(obj.feature.feature_type, '#94a3b8')
        return format_html(
            '<code style="color:#a5b4fc;font-size:11px;">{}</code>'
            ' <span style="color:{};font-size:10px;">({})</span>',
            obj.feature.code, type_color, obj.feature.get_feature_type_display(),
        )
    feature_display.short_description = _('Feature')
    feature_display.admin_order_field = 'feature__code'

    def usage_bar(self, obj):
        """Visual progress bar."""
        if obj.usage_limit == -1 or obj.usage_limit == 0:
            return format_html(
                '<span style="color:#22c55e;font-size:11px;">'
                '<i class="ph ph-infinity"></i> Unlimited</span>'
            )
        pct = min(100, (obj.current_usage / obj.usage_limit) * 100) if obj.usage_limit > 0 else 0
        color = '#22c55e' if pct < 70 else '#f59e0b' if pct < 90 else '#ef4444'
        pct_str = '{:.0f}'.format(pct)
        return format_html(
            '<div style="display:flex;align-items:center;gap:6px;">'
            '<div style="width:80px;height:6px;background:rgba(148,163,184,0.1);border-radius:3px;">'
            '<div style="width:{pct}%;height:100%;background:{color};border-radius:3px;"></div></div>'
            '<span style="color:{color};font-size:11px;font-weight:600;">{pct}%</span></div>',
            pct=pct_str, color=color,
        )
    usage_bar.short_description = _('Usage')

    def period_display(self, obj):
        if not obj.period_start or not obj.period_end:
            return format_html('<span style="color:#6b7280;">—</span>')
        return format_html(
            '<span style="color:#94a3b8;font-size:11px;">{} → {}</span>',
            obj.period_start.strftime('%d/%m'),
            obj.period_end.strftime('%d/%m/%Y'),
        )
    period_display.short_description = _('Period')

    def status_indicator(self, obj):
        """Over limit / within limit indicator."""
        if obj.usage_limit == -1:
            return format_html('<span style="color:#22c55e;font-size:11px;">✓ Unlimited</span>')
        if obj.usage_limit > 0 and obj.current_usage >= obj.usage_limit:
            return format_html(
                '<span style="color:#ef4444;font-weight:700;font-size:11px;">'
                '<i class="ph ph-warning"></i> LIMIT REACHED</span>'
            )
        return format_html('<span style="color:#22c55e;font-size:11px;">✓ OK</span>')
    status_indicator.short_description = _('Status')

    # Actions
    actions = ['reset_usage']

    @admin.action(description=_('Reset usage counters to 0'))
    def reset_usage(self, request, queryset):
        count = queryset.update(current_usage=0, last_reset_at=timezone.now())
        self.message_user(request, _('%d usage record(s) reset.') % count)


# =============================================================================
# FEATURE PERMISSION ADMIN
# =============================================================================

@admin.register(FeaturePermission)
class FeaturePermissionAdmin(EMenumPermissionMixin, admin.ModelAdmin):
    """Admin interface for Feature-Permission mappings."""
    list_display = ['feature_code', 'permission_display', 'created_at']
    list_filter = ['feature__category', 'feature__code']
    search_fields = ['feature__code', 'feature__name', 'permission__resource', 'permission__action']
    autocomplete_fields = ['feature', 'permission']
    readonly_fields = ['id', 'created_at', 'updated_at']
    list_per_page = 50

    def feature_code(self, obj):
        return format_html(
            '<code style="background:#1e293b;color:#38bdf8;padding:2px 6px;border-radius:4px;">{}</code>',
            obj.feature.code
        )
    feature_code.short_description = _('Feature')
    feature_code.admin_order_field = 'feature__code'

    def permission_display(self, obj):
        return format_html(
            '<code style="background:#1e293b;color:#a78bfa;padding:2px 6px;border-radius:4px;">{}.{}</code>',
            obj.permission.resource, obj.permission.action
        )
    permission_display.short_description = _('Permission')
    permission_display.admin_order_field = 'permission__resource'
