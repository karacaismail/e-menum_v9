"""
URL configuration for the Reporting application.

URL Structure:
    /api/v1/reports/catalog/              - Report catalog (read-only)
    /api/v1/reports/catalog/by-category/  - Reports grouped by category
    /api/v1/reports/run/                  - Execute a report
    /api/v1/reports/executions/           - Execution history
    /api/v1/reports/executions/{id}/      - Execution detail
    /api/v1/reports/executions/{id}/export/ - Export execution result
    /api/v1/reports/schedules/            - Schedule management
    /api/v1/reports/favorites/            - User favorites
    /api/v1/dashboard/metrics/            - Dashboard KPIs

    F4 Innovation:
    /api/v1/reports/chat/                 - Conversational analytics
    /api/v1/reports/credits/              - Credit balance & usage
    /api/v1/reports/voice/                - Voice query
    /api/v1/reports/export/advanced/      - Advanced export (white-label, BI)
    /api/v1/reports/benchmarks/           - Industry benchmark comparison
    /api/v1/reports/ai/models/            - AI model info
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from apps.reporting.views import (
    AdvancedExportView,
    AIModelInfoView,
    BenchmarkComparisonView,
    ConversationalView,
    CreditBalanceView,
    DashboardMetricView,
    ExportReportView,
    ReportCatalogViewSet,
    ReportExecutionViewSet,
    ReportFavoriteViewSet,
    ReportScheduleViewSet,
    RunReportView,
    VoiceQueryView,
)

router = DefaultRouter()
router.register(r'reports/catalog', ReportCatalogViewSet, basename='report-catalog')
router.register(r'reports/executions', ReportExecutionViewSet, basename='report-execution')
router.register(r'reports/schedules', ReportScheduleViewSet, basename='report-schedule')
router.register(r'reports/favorites', ReportFavoriteViewSet, basename='report-favorite')

urlpatterns = [
    # Router-based URLs
    path('', include(router.urls)),

    # Custom action URLs
    path(
        'reports/run/',
        RunReportView.as_view(),
        name='report-run',
    ),
    path(
        'reports/executions/<uuid:execution_id>/export/',
        ExportReportView.as_view(),
        name='report-export',
    ),

    # Dashboard
    path(
        'dashboard/metrics/',
        DashboardMetricView.as_view(),
        name='dashboard-metrics',
    ),

    # ─── F4 Innovation Features ───────────────────────────
    # Conversational analytics
    path(
        'reports/chat/',
        ConversationalView.as_view(),
        name='report-chat',
    ),

    # Credit balance & usage
    path(
        'reports/credits/',
        CreditBalanceView.as_view(),
        name='report-credits',
    ),

    # Voice query
    path(
        'reports/voice/',
        VoiceQueryView.as_view(),
        name='report-voice',
    ),

    # Advanced export (white-label PDF, BI formats)
    path(
        'reports/export/advanced/',
        AdvancedExportView.as_view(),
        name='report-export-advanced',
    ),

    # Industry benchmark comparison
    path(
        'reports/benchmarks/',
        BenchmarkComparisonView.as_view(),
        name='report-benchmarks',
    ),

    # AI model information
    path(
        'reports/ai/models/',
        AIModelInfoView.as_view(),
        name='report-ai-models',
    ),
]
