"""
DRF Serializers for the Reporting application.

Serializers:
    - ReportDefinitionSerializer: Report catalog (read-only)
    - ReportExecutionSerializer: Execution records
    - ReportScheduleSerializer: Schedule management
    - ReportFavoriteSerializer: User favorites
    - ExecuteReportSerializer: Input for report execution
"""

from rest_framework import serializers
from django.utils.translation import gettext_lazy as _

from shared.serializers.base import (
    BaseModelSerializer,
    TenantModelSerializer,
)
from apps.reporting.models import (
    ReportDefinition,
    ReportExecution,
    ReportFavorite,
    ReportSchedule,
)


# =============================================================================
# REPORT DEFINITION (Read-only catalog)
# =============================================================================

class ReportDefinitionSerializer(BaseModelSerializer):
    """
    Serializer for report catalog entries.
    Read-only - report definitions are managed via admin/seeds.
    """

    is_handler_registered = serializers.SerializerMethodField(
        help_text=_('Whether a handler is registered for this report'),
    )

    class Meta:
        model = ReportDefinition
        fields = [
            'id', 'feature_key', 'name', 'description', 'category',
            'priority', 'ai_model', 'credit_cost', 'min_plan',
            'default_parameters', 'supported_formats', 'supported_dimensions',
            'is_active', 'is_periodic', 'requires_ai',
            'is_handler_registered',
            'created_at', 'updated_at',
        ]
        read_only_fields = fields

    def get_is_handler_registered(self, obj) -> bool:
        from apps.reporting.services.report_engine import handler_registry
        return handler_registry.is_registered(obj.feature_key)


# =============================================================================
# REPORT EXECUTION
# =============================================================================

class ReportExecutionListSerializer(TenantModelSerializer):
    """
    Serializer for listing report executions (compact view).
    """

    feature_key = serializers.CharField(
        source='report_definition.feature_key',
        read_only=True,
    )
    report_name = serializers.CharField(
        source='report_definition.name',
        read_only=True,
    )
    requested_by_email = serializers.EmailField(
        source='requested_by.email',
        read_only=True,
        default=None,
    )

    class Meta:
        model = ReportExecution
        fields = [
            'id', 'feature_key', 'report_name', 'status',
            'requested_by_email', 'started_at', 'completed_at',
            'duration_ms', 'credits_consumed', 'export_format',
            'created_at',
        ]
        read_only_fields = fields


class ReportExecutionDetailSerializer(TenantModelSerializer):
    """
    Serializer for report execution detail (includes result_data).
    """

    feature_key = serializers.CharField(
        source='report_definition.feature_key',
        read_only=True,
    )
    report_name = serializers.CharField(
        source='report_definition.name',
        read_only=True,
    )
    report_category = serializers.CharField(
        source='report_definition.category',
        read_only=True,
    )
    requested_by_email = serializers.EmailField(
        source='requested_by.email',
        read_only=True,
        default=None,
    )

    class Meta:
        model = ReportExecution
        fields = [
            'id', 'feature_key', 'report_name', 'report_category',
            'status', 'parameters', 'result_data', 'error_message',
            'requested_by_email', 'started_at', 'completed_at',
            'duration_ms', 'credits_consumed', 'ai_model_used',
            'ai_tokens_used', 'export_format', 'export_file_url',
            'celery_task_id', 'created_at', 'updated_at',
        ]
        read_only_fields = fields


# =============================================================================
# EXECUTE REPORT INPUT
# =============================================================================

class ExecuteReportSerializer(serializers.Serializer):
    """
    Input serializer for executing a report.
    """

    feature_key = serializers.CharField(
        max_length=50,
        help_text=_('Report feature key (e.g., RPT-SAL-001)'),
    )
    parameters = serializers.DictField(
        required=False,
        default=dict,
        help_text=_('Report parameters'),
    )
    export_format = serializers.ChoiceField(
        choices=['JSON', 'PDF', 'EXCEL', 'CSV'],
        required=False,
        default='JSON',
        help_text=_('Export format'),
    )
    async_execution = serializers.BooleanField(
        required=False,
        default=False,
        help_text=_('Whether to execute asynchronously'),
    )


# =============================================================================
# REPORT SCHEDULE
# =============================================================================

class ReportScheduleSerializer(TenantModelSerializer):
    """
    Serializer for report schedule CRUD.
    """

    feature_key = serializers.CharField(
        source='report_definition.feature_key',
        read_only=True,
    )
    report_name = serializers.CharField(
        source='report_definition.name',
        read_only=True,
    )

    class Meta:
        model = ReportSchedule
        fields = [
            'id', 'feature_key', 'report_name',
            'report_definition', 'name', 'frequency',
            'trigger_time', 'trigger_day_of_week', 'trigger_day_of_month',
            'parameters', 'delivery_channels', 'delivery_emails',
            'delivery_webhook_url', 'export_format',
            'is_active', 'next_run_at', 'last_run_at',
            'run_count', 'failure_count',
            'organization', 'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'feature_key', 'report_name',
            'next_run_at', 'last_run_at', 'run_count',
            'failure_count', 'organization', 'created_at', 'updated_at',
        ]

    def create(self, validated_data):
        """Create schedule and calculate next run."""
        from apps.reporting.services.scheduler_service import SchedulerService

        instance = super().create(validated_data)

        scheduler = SchedulerService()
        instance.next_run_at = scheduler.calculate_next_run(instance)
        instance.save(update_fields=['next_run_at'])

        return instance


# =============================================================================
# REPORT FAVORITE
# =============================================================================

class ReportFavoriteSerializer(TenantModelSerializer):
    """
    Serializer for user report favorites.
    """

    feature_key = serializers.CharField(
        source='report_definition.feature_key',
        read_only=True,
    )
    report_name = serializers.CharField(
        source='report_definition.name',
        read_only=True,
    )
    report_category = serializers.CharField(
        source='report_definition.category',
        read_only=True,
    )

    class Meta:
        model = ReportFavorite
        fields = [
            'id', 'feature_key', 'report_name', 'report_category',
            'report_definition', 'custom_name', 'custom_parameters',
            'display_order', 'organization', 'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'feature_key', 'report_name', 'report_category',
            'organization', 'created_at', 'updated_at',
        ]


# =============================================================================
# DASHBOARD METRICS
# =============================================================================

class DashboardMetricSerializer(serializers.Serializer):
    """
    Serializer for dashboard KPI metrics response.
    """

    metric_type = serializers.CharField()
    value = serializers.DecimalField(max_digits=14, decimal_places=2)
    previous_value = serializers.DecimalField(
        max_digits=14, decimal_places=2, allow_null=True,
    )
    change_percent = serializers.DecimalField(
        max_digits=7, decimal_places=2, allow_null=True,
    )
    period_type = serializers.CharField()
    period_start = serializers.DateField()
    period_end = serializers.DateField()
