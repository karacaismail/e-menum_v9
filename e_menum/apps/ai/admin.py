"""
Django Admin configuration for the AI application.

Provides admin interface for:
- AIGeneration: View generation history, credits used, status
"""

from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from apps.ai.forms import AIProviderConfigForm
from apps.ai.models import (
    AIGeneration,
    AIProviderConfig,
    GenerationStatus,
    GenerationType,
    ProviderCategory,
)
from shared.permissions.admin_permission_mixin import EMenumPermissionMixin


def _hex_to_rgb(hex_color: str) -> str:
    hex_color = hex_color.lstrip('#')
    r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
    return f"{r}, {g}, {b}"


TYPE_COLORS = {
    GenerationType.DESCRIPTION: '#3b82f6',
    GenerationType.SHORT_DESCRIPTION: '#0ea5e9',
    GenerationType.NAME_SUGGESTION: '#8b5cf6',
    GenerationType.SEO_TEXT: '#22c55e',
    GenerationType.TRANSLATION: '#f59e0b',
    GenerationType.IMAGE_SEARCH: '#ec4899',
    GenerationType.IMPROVE: '#06b6d4',
}

STATUS_COLORS = {
    GenerationStatus.PENDING: '#94a3b8',
    GenerationStatus.PROCESSING: '#f59e0b',
    GenerationStatus.COMPLETED: '#22c55e',
    GenerationStatus.FAILED: '#ef4444',
    GenerationStatus.CANCELLED: '#6b7280',
}


@admin.register(AIGeneration)
class AIGenerationAdmin(EMenumPermissionMixin, admin.ModelAdmin):
    """Admin interface for AI Generation history."""

    list_display = [
        'type_badge', 'organization_display', 'user_display',
        'status_badge', 'input_preview', 'output_preview',
        'credits_display', 'model_display', 'created_at',
    ]
    list_filter = ['generation_type', 'status', 'model_used', 'created_at']
    search_fields = ['organization__name', 'user__email', 'input_text', 'output_text']
    readonly_fields = [
        'id', 'created_at', 'updated_at',
        'input_context', 'output_data',
        'tokens_input', 'tokens_output',
    ]
    ordering = ['-created_at']
    list_per_page = 30
    date_hierarchy = 'created_at'

    fieldsets = (
        (None, {
            'fields': ('id', 'organization', 'user', 'product', 'generation_type', 'status')
        }),
        (_('Input'), {
            'fields': ('input_text', 'input_context'),
        }),
        (_('Output'), {
            'fields': ('output_text', 'output_data'),
        }),
        (_('Cost'), {
            'fields': ('credits_used', 'model_used', 'tokens_input', 'tokens_output'),
        }),
        (_('Error'), {
            'fields': ('error_message',),
            'classes': ('collapse',),
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).filter(
            deleted_at__isnull=True
        ).select_related('organization', 'user', 'product')

    def type_badge(self, obj):
        color = TYPE_COLORS.get(obj.generation_type, '#94a3b8')
        icons = {
            GenerationType.DESCRIPTION: 'article',
            GenerationType.SHORT_DESCRIPTION: 'text-aa',
            GenerationType.NAME_SUGGESTION: 'lightbulb',
            GenerationType.SEO_TEXT: 'magnifying-glass',
            GenerationType.TRANSLATION: 'translate',
            GenerationType.IMAGE_SEARCH: 'image',
            GenerationType.IMPROVE: 'sparkle',
        }
        icon = icons.get(obj.generation_type, 'robot')
        return format_html(
            '<span style="display:inline-flex;align-items:center;gap:3px;'
            'padding:2px 8px;border-radius:4px;font-size:11px;font-weight:600;'
            'background:rgba({},0.12);color:{};">'
            '<i class="ph ph-{}"></i> {}</span>',
            _hex_to_rgb(color), color, icon, obj.get_generation_type_display(),
        )
    type_badge.short_description = _('Type')
    type_badge.admin_order_field = 'generation_type'

    def organization_display(self, obj):
        return format_html(
            '<span style="font-weight:600;color:#e2e8f0;">{}</span>',
            obj.organization.name,
        )
    organization_display.short_description = _('Organization')

    def user_display(self, obj):
        if not obj.user:
            return format_html('<span style="color:#6b7280;">System</span>')
        return format_html('<span style="color:#94a3b8;">{}</span>', obj.user.email)
    user_display.short_description = _('User')

    def status_badge(self, obj):
        color = STATUS_COLORS.get(obj.status, '#6b7280')
        return format_html(
            '<span style="padding:2px 8px;border-radius:4px;font-size:11px;font-weight:600;'
            'background:rgba({},0.12);color:{};">{}</span>',
            _hex_to_rgb(color), color, obj.get_status_display(),
        )
    status_badge.short_description = _('Status')
    status_badge.admin_order_field = 'status'

    def input_preview(self, obj):
        text = obj.input_text or ''
        if len(text) > 50:
            text = text[:50] + '...'
        return format_html('<span style="color:#94a3b8;font-size:12px;">{}</span>', text)
    input_preview.short_description = _('Input')

    def output_preview(self, obj):
        text = obj.output_text or ''
        if len(text) > 60:
            text = text[:60] + '...'
        if obj.status == GenerationStatus.COMPLETED:
            return format_html('<span style="color:#22c55e;font-size:12px;">{}</span>', text)
        elif obj.status == GenerationStatus.FAILED:
            err = obj.error_message or 'Error'
            return format_html('<span style="color:#ef4444;font-size:11px;">{}</span>', err[:50])
        return format_html('<span style="color:#6b7280;font-size:12px;">—</span>')
    output_preview.short_description = _('Output')

    def credits_display(self, obj):
        return format_html(
            '<span style="color:#f59e0b;font-weight:600;">'
            '<i class="ph ph-coins"></i> {}</span>',
            obj.credits_used,
        )
    credits_display.short_description = _('Credits')

    def model_display(self, obj):
        if not obj.model_used:
            return format_html('<span style="color:#6b7280;">—</span>')
        return format_html(
            '<code style="color:#a5b4fc;font-size:10px;">{}</code>',
            obj.model_used,
        )
    model_display.short_description = _('Model')

    def has_add_permission(self, request):
        return False  # Generations are created via API, not admin


# ─────────────────────────────────────────────────────────
# AI Provider Configuration Admin
# ─────────────────────────────────────────────────────────

CATEGORY_COLORS = {
    ProviderCategory.TEXT: '#3b82f6',    # Blue
    ProviderCategory.IMAGE: '#8b5cf6',   # Purple
}

CATEGORY_ICONS = {
    ProviderCategory.TEXT: 'text-aa',
    ProviderCategory.IMAGE: 'image',
}

PROVIDER_ICONS = {
    'openai': 'robot',
    'anthropic': 'brain',
    'gemini': 'diamond',
    'openai_dalle': 'paint-brush',
    'stability': 'mountain',
    'leonardo': 'palette',
    'midjourney': 'magic-wand',
    'runway': 'film-strip',
    'adobe_firefly': 'fire',
}

PROVIDER_COLORS = {
    'openai': '#10a37f',
    'anthropic': '#d4a574',
    'gemini': '#4285f4',
    'openai_dalle': '#10a37f',
    'stability': '#7c3aed',
    'leonardo': '#f59e0b',
    'midjourney': '#0ea5e9',
    'runway': '#ec4899',
    'adobe_firefly': '#ff4500',
}


@admin.register(AIProviderConfig)
class AIProviderConfigAdmin(EMenumPermissionMixin, admin.ModelAdmin):
    """
    Admin interface for AI Provider Configuration.

    Superuser-only access. Allows configuring text and image
    generation providers with encrypted API keys.
    """

    form = AIProviderConfigForm

    list_display = [
        'provider_badge', 'category_badge', 'name',
        'default_model_display', 'api_key_status',
        'default_badge', 'active_badge', 'priority', 'updated_at',
    ]
    list_filter = ['category', 'is_active', 'is_default', 'provider']
    search_fields = ['name', 'provider', 'default_model']
    ordering = ['category', 'priority']
    list_per_page = 20

    fieldsets = (
        (_('Provider'), {
            'fields': ('name', 'category', 'provider'),
        }),
        (_('Credentials'), {
            'fields': ('api_key', 'api_base_url'),
            'description': _('API credentials are encrypted at rest.'),
        }),
        (_('Model Configuration'), {
            'fields': ('default_model', 'settings'),
        }),
        (_('Status'), {
            'fields': ('is_active', 'is_default', 'priority'),
        }),
    )

    readonly_fields = ['id', 'created_at', 'updated_at']

    # ── Superuser-only access ──────────────────────────

    def has_module_permission(self, request):
        return request.user.is_superuser

    def has_view_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_add_permission(self, request):
        return request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser

    def get_queryset(self, request):
        return super().get_queryset(request).filter(deleted_at__isnull=True)

    # ── Custom display methods ─────────────────────────

    def provider_badge(self, obj):
        color = PROVIDER_COLORS.get(obj.provider, '#94a3b8')
        icon = PROVIDER_ICONS.get(obj.provider, 'robot')
        # Get display name from TextProvider or ImageProvider
        from apps.ai.models import ImageProvider, TextProvider
        display = obj.provider
        for choices in [TextProvider, ImageProvider]:
            for value, label in choices.choices:
                if value == obj.provider:
                    display = label
                    break
        return format_html(
            '<span style="display:inline-flex;align-items:center;gap:4px;'
            'padding:3px 10px;border-radius:4px;font-size:11px;font-weight:600;'
            'background:rgba({},0.12);color:{};">'
            '<i class="ph ph-{}"></i> {}</span>',
            _hex_to_rgb(color), color, icon, display,
        )
    provider_badge.short_description = _('Provider')
    provider_badge.admin_order_field = 'provider'

    def category_badge(self, obj):
        color = CATEGORY_COLORS.get(obj.category, '#94a3b8')
        icon = CATEGORY_ICONS.get(obj.category, 'robot')
        return format_html(
            '<span style="display:inline-flex;align-items:center;gap:3px;'
            'padding:2px 8px;border-radius:4px;font-size:11px;font-weight:600;'
            'background:rgba({},0.12);color:{};">'
            '<i class="ph ph-{}"></i> {}</span>',
            _hex_to_rgb(color), color, icon, obj.get_category_display(),
        )
    category_badge.short_description = _('Category')
    category_badge.admin_order_field = 'category'

    def api_key_status(self, obj):
        if obj.has_api_key:
            return format_html(
                '<span style="display:inline-flex;align-items:center;gap:4px;'
                'color:#22c55e;font-size:12px;">'
                '<i class="ph ph-lock-key"></i>'
                '<code style="color:#86efac;font-size:10px;letter-spacing:1px;">'
                '{}</code></span>',
                obj.api_key_masked,
            )
        return format_html(
            '<span style="display:inline-flex;align-items:center;gap:4px;'
            'color:#ef4444;font-size:12px;">'
            '<i class="ph ph-warning-circle"></i> {}</span>',
            _('Not configured'),
        )
    api_key_status.short_description = _('API Key')

    def active_badge(self, obj):
        if obj.is_active:
            return format_html(
                '<span style="color:#22c55e;">'
                '<i class="ph ph-check-circle"></i></span>'
            )
        return format_html(
            '<span style="color:#6b7280;">'
            '<i class="ph ph-minus-circle"></i></span>'
        )
    active_badge.short_description = _('Active')
    active_badge.admin_order_field = 'is_active'

    def default_badge(self, obj):
        if obj.is_default:
            return format_html(
                '<span style="display:inline-flex;align-items:center;gap:3px;'
                'color:#f59e0b;font-size:12px;font-weight:600;">'
                '<i class="ph ph-star-fill"></i> {}</span>',
                _('Default'),
            )
        return format_html('<span style="color:#6b7280;">—</span>')
    default_badge.short_description = _('Default')
    default_badge.admin_order_field = 'is_default'

    def default_model_display(self, obj):
        if not obj.default_model:
            return format_html('<span style="color:#6b7280;">—</span>')
        return format_html(
            '<code style="color:#a5b4fc;font-size:11px;">{}</code>',
            obj.default_model,
        )
    default_model_display.short_description = _('Model')
