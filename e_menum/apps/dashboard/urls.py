"""
Dashboard URL configuration.

All URLs are prefixed with /admin/dashboard/ or /admin/api/
and require staff authentication.
"""

from django.urls import path

from apps.dashboard import api_views, views

app_name = "dashboard"

urlpatterns = [
    # ─── Main Dashboard Page ──────────────────────────────────
    path("dashboard/", views.mainboard, name="mainboard"),
    # ─── API Endpoints ────────────────────────────────────────
    path("api/kpis/", api_views.api_kpis, name="api-kpis"),
    path("api/qr-scan-trend/", api_views.api_qr_scan_trend, name="api-qr-scan-trend"),
    path(
        "api/org-activity-heatmap/",
        api_views.api_org_activity_heatmap,
        name="api-org-activity-heatmap",
    ),
    path(
        "api/plan-distribution/",
        api_views.api_plan_distribution,
        name="api-plan-distribution",
    ),
    path(
        "api/city-distribution/",
        api_views.api_city_distribution,
        name="api-city-distribution",
    ),
    path("api/insights/", api_views.api_insights, name="api-insights"),
    path(
        "api/recent-activity/",
        api_views.api_recent_activity,
        name="api-recent-activity",
    ),
    path(
        "api/subscription-funnel/",
        api_views.api_subscription_funnel,
        name="api-subscription-funnel",
    ),
    # ─── Search (Command Palette) ─────────────────────────────
    path("api/search/", api_views.api_search, name="api-search"),
    # ─── Sidebar Preferences ─────────────────────────────────
    path("api/sidebar/pins/", api_views.api_sidebar_pins, name="api-sidebar-pins"),
    path(
        "api/sidebar/pins/save/",
        api_views.api_sidebar_pins_save,
        name="api-sidebar-pins-save",
    ),
    path(
        "api/sidebar/recent/", api_views.api_sidebar_recent, name="api-sidebar-recent"
    ),
    path(
        "api/sidebar/recent/save/",
        api_views.api_sidebar_recent_save,
        name="api-sidebar-recent-save",
    ),
]
