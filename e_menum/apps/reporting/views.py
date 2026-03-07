"""
DRF Views for the Reporting application.

ViewSets and APIViews:
    - ReportCatalogViewSet: Read-only report catalog
    - ReportExecutionViewSet: Execute and list reports
    - ReportScheduleViewSet: CRUD for report schedules
    - ReportFavoriteViewSet: CRUD for user favorites
    - DashboardMetricView: Dashboard KPIs
"""

import logging

from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated

from shared.permissions.drf_permissions import (
    IsTenantMember,
)
from shared.views.base import (
    BaseReadOnlyViewSet,
    BaseTenantAPIView,
    BaseTenantReadOnlyViewSet,
    BaseTenantViewSet,
)
from apps.reporting.models import (
    ReportDefinition,
    ReportExecution,
    ReportFavorite,
    ReportSchedule,
)
from apps.reporting.serializers import (
    DashboardMetricSerializer,
    ExecuteReportSerializer,
    ReportDefinitionSerializer,
    ReportExecutionDetailSerializer,
    ReportExecutionListSerializer,
    ReportFavoriteSerializer,
    ReportScheduleSerializer,
)

logger = logging.getLogger(__name__)


# =============================================================================
# REPORT CATALOG (Read-only)
# =============================================================================


class ReportCatalogViewSet(BaseReadOnlyViewSet):
    """
    Read-only viewset for the report catalog.

    GET /api/v1/reports/catalog/         - List all available reports
    GET /api/v1/reports/catalog/{id}/    - Get report definition details

    Filterable by: category, min_plan, is_active, requires_ai
    """

    queryset = ReportDefinition.objects.filter(is_active=True)
    serializer_class = ReportDefinitionSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["category", "min_plan", "is_periodic", "requires_ai"]
    search_fields = ["name", "description", "feature_key"]
    ordering_fields = ["category", "feature_key", "priority"]

    @action(detail=False, methods=["get"], url_path="by-category")
    def by_category(self, request):
        """
        Get reports grouped by category.

        GET /api/v1/reports/catalog/by-category/
        """
        from collections import defaultdict

        reports = self.get_queryset()
        grouped = defaultdict(list)

        for report in reports:
            serializer = self.get_serializer(report)
            grouped[report.category].append(serializer.data)

        return self.get_success_response(dict(grouped))


# =============================================================================
# REPORT EXECUTION
# =============================================================================


class ReportExecutionViewSet(BaseTenantReadOnlyViewSet):
    """
    ViewSet for executing reports and viewing execution history.

    GET  /api/v1/reports/executions/          - List executions
    GET  /api/v1/reports/executions/{id}/     - Get execution detail
    POST /api/v1/reports/run/                 - Execute a report (separate URL)
    """

    queryset = ReportExecution.objects.select_related(
        "report_definition",
        "requested_by",
    ).all()
    permission_resource = "reporting"
    filterset_fields = ["status", "report_definition__feature_key"]
    ordering_fields = ["created_at", "completed_at", "duration_ms"]

    def get_serializer_class(self):
        if self.action == "retrieve":
            return ReportExecutionDetailSerializer
        return ReportExecutionListSerializer


class RunReportView(BaseTenantAPIView):
    """
    Execute a report (sync or async).

    POST /api/v1/reports/run/
    {
        "feature_key": "RPT-SAL-001",
        "parameters": {"period": "DAILY", "date": "2026-01-15"},
        "export_format": "JSON",
        "async_execution": false
    }
    """

    permission_classes = [IsAuthenticated, IsTenantMember]

    def post(self, request):
        serializer = ExecuteReportSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        from apps.reporting.services.report_engine import ReportEngine

        engine = ReportEngine()
        org = self.require_organization()

        data = serializer.validated_data
        feature_key = data["feature_key"]
        parameters = data.get("parameters", {})
        export_format = data.get("export_format", "JSON")
        async_execution = data.get("async_execution", False)

        if async_execution:
            execution = engine.execute_report_async(
                org_id=str(org.id),
                feature_key=feature_key,
                parameters=parameters,
                user=request.user,
                export_format=export_format,
            )
            result_serializer = ReportExecutionListSerializer(execution)
            return self.get_success_response(
                result_serializer.data,
                status_code=status.HTTP_202_ACCEPTED,
                message="Report execution queued",
            )
        else:
            execution = engine.execute_report(
                org_id=str(org.id),
                feature_key=feature_key,
                parameters=parameters,
                user=request.user,
                export_format=export_format,
            )
            result_serializer = ReportExecutionDetailSerializer(execution)
            return self.get_success_response(result_serializer.data)


class ExportReportView(BaseTenantAPIView):
    """
    Export an existing report execution to a file format.

    GET /api/v1/reports/executions/{id}/export/?format=EXCEL
    """

    permission_classes = [IsAuthenticated, IsTenantMember]

    def get(self, request, execution_id):
        from django.http import HttpResponse
        from apps.reporting.services.export_service import ExportService

        org = self.require_organization()

        try:
            execution = ReportExecution.objects.get(
                id=execution_id,
                organization=org,
                status="COMPLETED",
                deleted_at__isnull=True,
            )
        except ReportExecution.DoesNotExist:
            return self.get_error_response(
                code="EXECUTION_NOT_FOUND",
                message="Completed execution not found",
                status_code=status.HTTP_404_NOT_FOUND,
            )

        export_format = request.query_params.get("format", "EXCEL").upper()
        export_service = ExportService()

        try:
            file_bytes = export_service.export(execution.result_data, export_format)
        except ValueError as exc:
            return self.get_error_response(
                code="INVALID_FORMAT",
                message=str(exc),
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        content_types = {
            "JSON": "application/json",
            "CSV": "text/csv",
            "EXCEL": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "PDF": "application/pdf",
        }
        extensions = {
            "JSON": "json",
            "CSV": "csv",
            "EXCEL": "xlsx",
            "PDF": "pdf",
        }

        filename = (
            f"{execution.report_definition.feature_key}_"
            f"{timezone.now().strftime('%Y%m%d_%H%M')}"
            f".{extensions.get(export_format, 'dat')}"
        )

        response = HttpResponse(
            file_bytes,
            content_type=content_types.get(export_format, "application/octet-stream"),
        )
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response


# =============================================================================
# REPORT SCHEDULE
# =============================================================================


class ReportScheduleViewSet(BaseTenantViewSet):
    """
    CRUD for report schedules.

    GET    /api/v1/reports/schedules/          - List schedules
    POST   /api/v1/reports/schedules/          - Create schedule
    GET    /api/v1/reports/schedules/{id}/     - Get schedule detail
    PUT    /api/v1/reports/schedules/{id}/     - Update schedule
    DELETE /api/v1/reports/schedules/{id}/     - Delete schedule (soft)
    """

    queryset = ReportSchedule.objects.select_related(
        "report_definition",
    ).all()
    serializer_class = ReportScheduleSerializer
    permission_resource = "reporting"
    filterset_fields = ["frequency", "is_active", "report_definition__feature_key"]

    def perform_create(self, serializer):
        org = self.require_organization()
        serializer.save(
            organization=org,
            created_by=self.request.user,
        )


# =============================================================================
# REPORT FAVORITES
# =============================================================================


class ReportFavoriteViewSet(BaseTenantViewSet):
    """
    CRUD for user report favorites.

    GET    /api/v1/reports/favorites/          - List user favorites
    POST   /api/v1/reports/favorites/          - Add favorite
    DELETE /api/v1/reports/favorites/{id}/     - Remove favorite
    """

    queryset = ReportFavorite.objects.select_related(
        "report_definition",
    ).all()
    serializer_class = ReportFavoriteSerializer
    permission_resource = "reporting"

    def get_queryset(self):
        """Filter favorites to current user only."""
        qs = super().get_queryset()
        return qs.filter(user=self.request.user)

    def perform_create(self, serializer):
        org = self.require_organization()
        serializer.save(
            organization=org,
            user=self.request.user,
        )

    def perform_destroy(self, instance):
        """Favorites are hard-deleted (no soft delete)."""
        instance.delete()


# =============================================================================
# DASHBOARD METRICS
# =============================================================================


class DashboardMetricView(BaseTenantAPIView):
    """
    Dashboard KPI metrics endpoint.

    GET /api/v1/dashboard/metrics/?period=DAILY
    GET /api/v1/dashboard/metrics/?period=WEEKLY
    GET /api/v1/dashboard/metrics/?period=MONTHLY
    """

    permission_classes = [IsAuthenticated, IsTenantMember]

    def get(self, request):
        from apps.analytics.models import DashboardMetric

        org = self.require_organization()
        period = request.query_params.get("period", "DAILY").upper()

        metrics = DashboardMetric.objects.filter(
            organization=org,
            period_type=period,
            deleted_at__isnull=True,
        ).order_by("-period_start")[:10]

        serializer = DashboardMetricSerializer(metrics, many=True)
        return self.get_success_response(serializer.data)


# =============================================================================
# CONVERSATIONAL ANALYTICS (F4 Innovation)
# =============================================================================


class ConversationalView(BaseTenantAPIView):
    """
    Conversational analytics endpoint.

    POST /api/v1/reports/chat/
    {
        "message": "What was my revenue last week?",
        "session_id": null  // null to start new session, UUID to continue
    }

    Response:
    {
        "success": true,
        "data": {
            "session_id": "...",
            "message_id": "...",
            "answer": "Your revenue last week was ...",
            "data": {...},
            "visualization_hint": "bar",
            "intent": "query_revenue",
            "confidence": 0.85
        }
    }

    GET /api/v1/reports/chat/?session_id=...
    Returns session message history.

    DELETE /api/v1/reports/chat/?session_id=...
    Ends the conversation session.
    """

    permission_classes = [IsAuthenticated, IsTenantMember]

    def post(self, request):
        from apps.reporting.ai.conversational_service import (
            ConversationalAnalyticsService,
        )

        org = self.require_organization()
        message = request.data.get("message", "").strip()
        session_id = request.data.get("session_id", None)

        if not message:
            return self.get_error_response(
                code="EMPTY_MESSAGE",
                message="Message cannot be empty",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        service = ConversationalAnalyticsService()

        # Start new session if no session_id provided
        if not session_id:
            session_id = service.start_session(
                org_id=org.id,
                user=request.user,
            )

        # Process the message
        result = service.process_message(
            session_id=session_id,
            message=message,
        )

        return self.get_success_response(result)

    def get(self, request):
        from apps.reporting.ai.conversational_service import (
            ConversationalAnalyticsService,
        )

        session_id = request.query_params.get("session_id", "")

        if not session_id:
            return self.get_error_response(
                code="MISSING_SESSION_ID",
                message="session_id query parameter is required",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        service = ConversationalAnalyticsService()
        history = service.get_session_history(session_id)
        return self.get_success_response(history)

    def delete(self, request):
        from apps.reporting.ai.conversational_service import (
            ConversationalAnalyticsService,
        )

        session_id = request.query_params.get("session_id", "")

        if not session_id:
            return self.get_error_response(
                code="MISSING_SESSION_ID",
                message="session_id query parameter is required",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        service = ConversationalAnalyticsService()
        service.end_session(session_id)
        return self.get_success_response({"ended": True})


# =============================================================================
# CREDIT BALANCE (F4 Innovation)
# =============================================================================


class CreditBalanceView(BaseTenantAPIView):
    """
    Credit balance and usage endpoint.

    GET /api/v1/reports/credits/
    Returns the current credit balance.

    GET /api/v1/reports/credits/?start_date=2026-01-01&end_date=2026-01-31
    Returns credit balance with usage summary for the specified period.
    """

    permission_classes = [IsAuthenticated, IsTenantMember]

    def get(self, request):
        from apps.reporting.services.credit_service import CreditService

        org = self.require_organization()
        service = CreditService()

        start_date_str = request.query_params.get("start_date", "")
        end_date_str = request.query_params.get("end_date", "")

        start_date = None
        end_date = None

        if start_date_str:
            try:
                from datetime import date as date_type

                parts = start_date_str.split("-")
                start_date = date_type(int(parts[0]), int(parts[1]), int(parts[2]))
            except (ValueError, IndexError):
                return self.get_error_response(
                    code="INVALID_DATE",
                    message="start_date must be in YYYY-MM-DD format",
                    status_code=status.HTTP_400_BAD_REQUEST,
                )

        if end_date_str:
            try:
                from datetime import date as date_type

                parts = end_date_str.split("-")
                end_date = date_type(int(parts[0]), int(parts[1]), int(parts[2]))
            except (ValueError, IndexError):
                return self.get_error_response(
                    code="INVALID_DATE",
                    message="end_date must be in YYYY-MM-DD format",
                    status_code=status.HTTP_400_BAD_REQUEST,
                )

        usage_summary = service.get_usage_summary(
            org_id=org.id,
            start_date=start_date,
            end_date=end_date,
        )

        return self.get_success_response(usage_summary)


# =============================================================================
# VOICE QUERY (F4 Innovation)
# =============================================================================


class VoiceQueryView(BaseTenantAPIView):
    """
    Voice-based analytics query endpoint.

    POST /api/v1/reports/voice/
    Content-Type: multipart/form-data
    Body: audio (file), language (str, optional, default: 'tr')

    Response:
    {
        "success": true,
        "data": {
            "text_query": "What was my revenue last week?",
            "report_data": {...},
            "answer_text": "Your revenue last week was ...",
            "audio_response_url": "/media/tts_cache/.../tts_abc.mp3",
            "visualization_hint": "bar",
            "confidence": 0.85
        }
    }
    """

    permission_classes = [IsAuthenticated, IsTenantMember]

    def post(self, request):
        from apps.reporting.ai.voice_service import VoiceQueryService

        org = self.require_organization()

        audio_file = request.FILES.get("audio")
        if not audio_file:
            return self.get_error_response(
                code="MISSING_AUDIO",
                message='Audio file is required. Upload as "audio" field.',
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        language = request.data.get("language", "tr")

        try:
            audio_data = audio_file.read()
        except Exception as exc:
            logger.error("Failed to read audio file: %s", exc)
            return self.get_error_response(
                code="AUDIO_READ_ERROR",
                message="Failed to read audio file",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        service = VoiceQueryService()

        try:
            result = service.process_voice_query(
                org_id=org.id,
                audio_data=audio_data,
                user=request.user,
                language=language,
            )
        except Exception as exc:
            logger.error(
                "Voice query processing failed: org=%s error=%s",
                org.id,
                exc,
            )
            return self.get_error_response(
                code="VOICE_QUERY_ERROR",
                message=f"Voice query processing failed: {str(exc)}",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return self.get_success_response(result)


# =============================================================================
# ADVANCED EXPORT (F4 Innovation)
# =============================================================================


class AdvancedExportView(BaseTenantAPIView):
    """
    Advanced export endpoint for white-label PDF and BI tool formats.

    POST /api/v1/reports/export/advanced/
    {
        "execution_id": "uuid",
        "format": "white_label_pdf" | "powerbi" | "tableau",
        "branding": {  // optional, for white_label_pdf
            "logo_url": "https://...",
            "primary_color": "#2563EB",
            "company_name": "Cafe Istanbul"
        }
    }
    """

    permission_classes = [IsAuthenticated, IsTenantMember]

    def post(self, request):
        from django.http import HttpResponse
        from apps.reporting.services.advanced_export_service import (
            AdvancedExportService,
        )

        org = self.require_organization()

        execution_id = request.data.get("execution_id")
        export_format = request.data.get("format", "white_label_pdf")
        branding = request.data.get("branding", {})

        if not execution_id:
            return self.get_error_response(
                code="MISSING_EXECUTION_ID",
                message="execution_id is required",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        try:
            execution = ReportExecution.objects.get(
                id=execution_id,
                organization=org,
                status="COMPLETED",
                deleted_at__isnull=True,
            )
        except ReportExecution.DoesNotExist:
            return self.get_error_response(
                code="EXECUTION_NOT_FOUND",
                message="Completed execution not found",
                status_code=status.HTTP_404_NOT_FOUND,
            )

        service = AdvancedExportService()

        try:
            if export_format == "white_label_pdf":
                file_bytes = service.export_white_label_pdf(
                    execution.result_data,
                    branding,
                )
                content_type = "application/pdf"
                ext = "pdf"
            elif export_format in ("powerbi", "tableau"):
                file_bytes = service.export_to_bi_format(
                    execution.result_data,
                    export_format,
                )
                content_type = "application/json"
                ext = "json"
            else:
                return self.get_error_response(
                    code="INVALID_FORMAT",
                    message=(
                        f"Unsupported format: {export_format}. "
                        f"Supported: white_label_pdf, powerbi, tableau"
                    ),
                    status_code=status.HTTP_400_BAD_REQUEST,
                )
        except (ImportError, ValueError) as exc:
            return self.get_error_response(
                code="EXPORT_ERROR",
                message=str(exc),
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        filename = (
            f"{execution.report_definition.feature_key}_"
            f"{export_format}_{timezone.now().strftime('%Y%m%d_%H%M')}"
            f".{ext}"
        )

        response = HttpResponse(file_bytes, content_type=content_type)
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response


# =============================================================================
# BENCHMARK COMPARISON (F4 Innovation)
# =============================================================================


class BenchmarkComparisonView(BaseTenantAPIView):
    """
    Industry benchmark comparison endpoint.

    GET /api/v1/reports/benchmarks/?metric=daily_revenue&period=MONTHLY
    Returns comparison of org's metric against industry benchmark.

    GET /api/v1/reports/benchmarks/available/
    Returns list of available benchmark metrics.
    """

    permission_classes = [IsAuthenticated, IsTenantMember]

    def get(self, request):
        from apps.reporting.services.benchmark_service import BenchmarkService

        org = self.require_organization()
        service = BenchmarkService()

        metric_name = request.query_params.get("metric", "daily_revenue")
        period = request.query_params.get("period", "MONTHLY")

        comparison = service.compare_org_to_benchmark(
            org_id=org.id,
            metric_name=metric_name,
            period=period,
        )

        return self.get_success_response(comparison)


# =============================================================================
# AI MODEL INFO (F4 Innovation)
# =============================================================================


class AIModelInfoView(BaseTenantAPIView):
    """
    AI model information endpoint.

    GET /api/v1/reports/ai/models/
    Returns available AI models and their capabilities.
    """

    permission_classes = [IsAuthenticated, IsTenantMember]

    def get(self, request):
        from apps.reporting.ai.model_router import AIModelRouter

        router = AIModelRouter()
        models = router.get_available_models()
        return self.get_success_response(models)
