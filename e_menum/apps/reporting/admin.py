"""
Django Admin configuration for the Reporting application.
"""

from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from apps.reporting.models import (
    ReportDefinition,
    ReportExecution,
    ReportFavorite,
    ReportSchedule,
)
from shared.permissions.admin_permission_mixin import EMenumPermissionMixin


@admin.register(ReportDefinition)
class ReportDefinitionAdmin(EMenumPermissionMixin, admin.ModelAdmin):
    """Admin for report catalog."""

    list_display = [
        'feature_key', 'name', 'category', 'priority',
        'min_plan', 'ai_model', 'credit_cost', 'is_active',
    ]
    list_filter = ['category', 'priority', 'min_plan', 'ai_model', 'is_active', 'requires_ai']
    search_fields = ['feature_key', 'name', 'description']
    ordering = ['category', 'feature_key']
    readonly_fields = ['id', 'created_at', 'updated_at']


@admin.register(ReportExecution)
class ReportExecutionAdmin(EMenumPermissionMixin, admin.ModelAdmin):
    """Admin for report execution records."""

    list_display = [
        'id_short', 'feature_key', 'organization_name',
        'status', 'duration_ms', 'credits_consumed', 'created_at',
    ]
    list_filter = ['status', 'report_definition__category']
    search_fields = ['report_definition__feature_key', 'organization__name']
    ordering = ['-created_at']
    readonly_fields = [
        'id', 'result_data', 'error_message',
        'started_at', 'completed_at', 'duration_ms',
        'credits_consumed', 'ai_model_used', 'ai_tokens_used',
        'celery_task_id', 'created_at', 'updated_at',
    ]
    raw_id_fields = ['organization', 'requested_by', 'report_definition', 'schedule']

    def id_short(self, obj):
        return str(obj.id)[:8]
    id_short.short_description = 'ID'

    def feature_key(self, obj):
        return obj.report_definition.feature_key
    feature_key.short_description = 'Report'

    def organization_name(self, obj):
        return obj.organization.name if obj.organization else '-'
    organization_name.short_description = 'Organization'


@admin.register(ReportSchedule)
class ReportScheduleAdmin(EMenumPermissionMixin, admin.ModelAdmin):
    """Admin for report schedules."""

    list_display = [
        'name', 'feature_key', 'organization_name',
        'frequency', 'is_active', 'next_run_at', 'run_count',
    ]
    list_filter = ['frequency', 'is_active']
    search_fields = ['name', 'report_definition__feature_key', 'organization__name']
    ordering = ['next_run_at']
    readonly_fields = [
        'id', 'last_run_at', 'run_count', 'failure_count',
        'created_at', 'updated_at',
    ]
    raw_id_fields = ['organization', 'created_by', 'report_definition']

    def feature_key(self, obj):
        return obj.report_definition.feature_key
    feature_key.short_description = 'Report'

    def organization_name(self, obj):
        return obj.organization.name if obj.organization else '-'
    organization_name.short_description = 'Organization'


@admin.register(ReportFavorite)
class ReportFavoriteAdmin(EMenumPermissionMixin, admin.ModelAdmin):
    """Admin for report favorites."""

    list_display = ['user', 'feature_key', 'custom_name', 'display_order']
    search_fields = ['user__email', 'report_definition__feature_key']
    raw_id_fields = ['organization', 'user', 'report_definition']

    def feature_key(self, obj):
        return obj.report_definition.feature_key
    feature_key.short_description = 'Report'
