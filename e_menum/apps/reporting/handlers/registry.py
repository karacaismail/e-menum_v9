"""
Handler registry - imports all report handlers to trigger registration.

This module is imported during Django app ready() to ensure all
handlers are registered with the ReportEngine handler registry
via the @register_handler decorator.

Handler registration map:
    RPT-SAL-001 -> RevenueReportHandler
    RPT-SAL-009 -> TopSellersHandler
    RPT-ORD-001 -> OrderAnalysisHandler
    RPT-CUS-001 -> CustomerOverviewHandler
    RPT-MNU-001 -> MenuPerformanceMatrixHandler
    RPT-MNU-002 -> ItemPerformanceHandler
    RPT-DIG-001 -> QRScanAnalysisHandler
    RPT-PER-001 -> DailySummaryHandler
    RPT-PER-005 -> WeeklyTrendHandler
    RPT-PER-008 -> MonthlyAnalysisHandler
    RPT-FOR-001 -> RevenueForecastHandler
    RPT-AII-001 -> DailyInsightsHandler
    RPT-AIQ-001 -> NLQHandler
    RPT-INV-001 -> StockLevelHandler
    RPT-CMP-001 -> CampaignPerformanceHandler
    RPT-BRN-001 -> BranchComparisonHandler
    RPT-PLT-001 -> TenantGrowthHandler
    RPT-STF-001 -> StaffPerformanceHandler
    RPT-OPR-001 -> PeakHoursHandler
"""

# Sales handlers
from apps.reporting.handlers.sales.revenue_handler import RevenueReportHandler  # noqa: F401
from apps.reporting.handlers.sales.top_sellers_handler import TopSellersHandler  # noqa: F401

# Order handlers
from apps.reporting.handlers.orders.order_analysis_handler import OrderAnalysisHandler  # noqa: F401

# Customer handlers
from apps.reporting.handlers.customers.customer_overview_handler import (
    CustomerOverviewHandler,
)  # noqa: F401

# Menu handlers
from apps.reporting.handlers.menu.performance_matrix_handler import (
    MenuPerformanceMatrixHandler,
)  # noqa: F401
from apps.reporting.handlers.menu.item_performance_handler import ItemPerformanceHandler  # noqa: F401

# Digital handlers
from apps.reporting.handlers.digital.qr_scan_handler import QRScanAnalysisHandler  # noqa: F401

# Periodic handlers
from apps.reporting.handlers.periodic.daily_summary_handler import DailySummaryHandler  # noqa: F401
from apps.reporting.handlers.periodic.weekly_trend_handler import WeeklyTrendHandler  # noqa: F401
from apps.reporting.handlers.periodic.monthly_analysis_handler import (
    MonthlyAnalysisHandler,
)  # noqa: F401

# F2 Growth Phase - AI & Forecasting handlers
from apps.reporting.handlers.forecasting.revenue_forecast_handler import (
    RevenueForecastHandler,
)  # noqa: F401
from apps.reporting.handlers.ai_insights.daily_insights_handler import (
    DailyInsightsHandler,
)  # noqa: F401
from apps.reporting.handlers.ai_query.nlq_handler import NLQHandler  # noqa: F401

# F3 Enterprise Phase - Inventory, Campaign, Branch, Platform, Staff, Operations handlers
from apps.reporting.handlers.inventory.stock_level_handler import StockLevelHandler  # noqa: F401
from apps.reporting.handlers.campaigns.campaign_performance_handler import (
    CampaignPerformanceHandler,
)  # noqa: F401
from apps.reporting.handlers.branch.branch_comparison_handler import (
    BranchComparisonHandler,
)  # noqa: F401
from apps.reporting.handlers.platform.tenant_growth_handler import TenantGrowthHandler  # noqa: F401
from apps.reporting.handlers.staff.staff_performance_handler import (
    StaffPerformanceHandler,
)  # noqa: F401
from apps.reporting.handlers.operations.peak_hours_handler import PeakHoursHandler  # noqa: F401
