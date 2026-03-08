"""
URL patterns for the restaurant account portal.

All paths live under /account/ with English slugs.
"""

from django.urls import path

from . import views
from . import dashboard_views
from . import menu_views
from . import product_views
from . import order_views
from . import table_views
from . import qr_views
from . import customer_views
from . import analytics_views
from . import subscription_views
from . import support_views
from . import team_views
from . import notification_views
from . import restaurant_views

app_name = "accounts"

urlpatterns = [
    # ── Auth ──────────────────────────────────────────────────────────────
    path("login/", views.AccountLoginView.as_view(), name="login"),
    path("register/", views.RegisterView.as_view(), name="register"),
    path("logout/", views.AccountLogoutView.as_view(), name="logout"),
    # ── Dashboard ─────────────────────────────────────────────────────────
    path("dashboard/", dashboard_views.DashboardView.as_view(), name="dashboard"),
    # ── Dashboard API ─────────────────────────────────────────────────────
    path(
        "api/dashboard/kpis/",
        dashboard_views.dashboard_kpis_api,
        name="dashboard-kpis-api",
    ),
    path(
        "api/dashboard/qr-trend/",
        dashboard_views.dashboard_qr_trend_api,
        name="dashboard-qr-trend-api",
    ),
    path(
        "api/dashboard/revenue/",
        dashboard_views.dashboard_revenue_api,
        name="dashboard-revenue-api",
    ),
    path(
        "api/dashboard/orders-chart/",
        dashboard_views.dashboard_orders_chart_api,
        name="dashboard-orders-chart-api",
    ),
    path(
        "api/dashboard/top-products/",
        dashboard_views.dashboard_top_products_api,
        name="dashboard-top-products-api",
    ),
    path(
        "api/dashboard/recent-orders/",
        dashboard_views.dashboard_recent_orders_api,
        name="dashboard-recent-orders-api",
    ),
    # ── Menu CRUD ─────────────────────────────────────────────────────────
    path("menus/", menu_views.menu_list, name="menu-list"),
    path("menus/create/", menu_views.menu_create, name="menu-create"),
    path("menus/<uuid:menu_id>/", menu_views.menu_detail, name="menu-detail"),
    path("menus/<uuid:menu_id>/edit/", menu_views.menu_edit, name="menu-edit"),
    path("menus/<uuid:menu_id>/delete/", menu_views.menu_delete, name="menu-delete"),
    path("menus/<uuid:menu_id>/publish/", menu_views.menu_publish, name="menu-publish"),
    path(
        "menus/<uuid:menu_id>/default/",
        menu_views.menu_set_default,
        name="menu-set-default",
    ),
    # ── Category CRUD (AJAX) ──────────────────────────────────────────────
    path(
        "menus/<uuid:menu_id>/categories/create/",
        menu_views.category_create,
        name="category-create",
    ),
    path(
        "menus/<uuid:menu_id>/categories/reorder/",
        menu_views.category_reorder,
        name="category-reorder",
    ),
    path(
        "categories/<uuid:category_id>/edit/",
        menu_views.category_edit,
        name="category-edit",
    ),
    path(
        "categories/<uuid:category_id>/delete/",
        menu_views.category_delete,
        name="category-delete",
    ),
    # ── Product CRUD ──────────────────────────────────────────────────────
    path("products/", product_views.product_list, name="product-list"),
    path("products/create/", product_views.product_create, name="product-create"),
    path(
        "products/<uuid:product_id>/",
        product_views.product_detail,
        name="product-detail",
    ),
    path(
        "products/<uuid:product_id>/edit/",
        product_views.product_edit,
        name="product-edit",
    ),
    path(
        "products/<uuid:product_id>/delete/",
        product_views.product_delete,
        name="product-delete",
    ),
    path(
        "products/<uuid:product_id>/toggle-active/",
        product_views.product_toggle_active,
        name="product-toggle-active",
    ),
    path(
        "products/<uuid:product_id>/toggle-featured/",
        product_views.product_toggle_featured,
        name="product-toggle-featured",
    ),
    # ── Theme CRUD ────────────────────────────────────────────────────────
    path("themes/", menu_views.theme_list, name="theme-list"),
    path("themes/create/", menu_views.theme_create, name="theme-create"),
    path("themes/<uuid:theme_id>/edit/", menu_views.theme_edit, name="theme-edit"),
    path(
        "themes/<uuid:theme_id>/delete/", menu_views.theme_delete, name="theme-delete"
    ),
    # ── Order Management ──────────────────────────────────────────────────
    path("orders/", order_views.order_list, name="order-list"),
    path("orders/<uuid:order_id>/", order_views.order_detail, name="order-detail"),
    path(
        "orders/<uuid:order_id>/status/",
        order_views.order_update_status,
        name="order-update-status",
    ),
    path("api/orders/", order_views.order_api, name="order-api"),
    # ── Table & Zone Management ───────────────────────────────────────────
    path("tables/", table_views.table_management, name="table-management"),
    path("zones/create/", table_views.zone_create, name="zone-create"),
    path("zones/<uuid:zone_id>/edit/", table_views.zone_edit, name="zone-edit"),
    path("zones/<uuid:zone_id>/delete/", table_views.zone_delete, name="zone-delete"),
    path("tables/create/", table_views.table_create, name="table-create"),
    path("tables/<uuid:table_id>/edit/", table_views.table_edit, name="table-edit"),
    path(
        "tables/<uuid:table_id>/delete/", table_views.table_delete, name="table-delete"
    ),
    path("api/tables/", table_views.table_api, name="table-api"),
    # ── Zone & Table API (AJAX from Alpine.js templates) ─────────────────
    path("api/zones/", table_views.zone_create, name="zone-create-api"),
    path(
        "api/zones/<uuid:zone_id>/",
        table_views.zone_api_detail,
        name="zone-api-detail",
    ),
    path(
        "api/tables/create/",
        table_views.table_create,
        name="table-create-api",
    ),
    path(
        "api/tables/<uuid:table_id>/",
        table_views.table_api_detail,
        name="table-api-detail",
    ),
    # ── QR Code Management ────────────────────────────────────────────────
    path("qr-codes/", qr_views.qrcode_list, name="qrcode-list"),
    path("qr-codes/create/", qr_views.qrcode_create, name="qrcode-create"),
    path("qr-codes/<uuid:qr_id>/", qr_views.qrcode_detail, name="qrcode-detail"),
    path("qr-codes/<uuid:qr_id>/toggle/", qr_views.qrcode_toggle, name="qrcode-toggle"),
    # ── QR Code API (AJAX from Alpine.js templates) ──────────────────────
    path(
        "api/qrcodes/<uuid:qr_id>/toggle/",
        qr_views.qrcode_toggle,
        name="qrcode-toggle-api",
    ),
    path("api/qrcodes/", qr_views.qrcode_create_api, name="qrcode-create-api"),
    path(
        "qr-codes/<uuid:qr_id>/download/",
        qr_views.qrcode_download,
        name="qrcode-download",
    ),
    path(
        "qr-codes/<uuid:qr_id>/download-print/",
        qr_views.qrcode_download_print,
        name="qrcode-download-print",
    ),
    path(
        "qr-codes/<uuid:qr_id>/download-branded/",
        qr_views.qrcode_download_branded_print,
        name="qrcode-download-branded",
    ),
    # ── Customer Management ───────────────────────────────────────────────
    path("customers/", customer_views.customer_list, name="customer-list"),
    path(
        "customers/<uuid:customer_id>/",
        customer_views.customer_detail,
        name="customer-detail",
    ),
    # ── Analytics ─────────────────────────────────────────────────────────
    path("analytics/", analytics_views.analytics_overview, name="analytics"),
    path(
        "api/analytics/qr-scans/",
        analytics_views.analytics_qr_scans_api,
        name="analytics-qr-scans-api",
    ),
    path(
        "api/analytics/revenue/",
        analytics_views.analytics_revenue_api,
        name="analytics-revenue-api",
    ),
    path(
        "api/analytics/products/",
        analytics_views.analytics_products_api,
        name="analytics-products-api",
    ),
    path(
        "api/analytics/customers/",
        analytics_views.analytics_customers_api,
        name="analytics-customers-api",
    ),
    # ── Team Management ──────────────────────────────────────────────────
    path("team/", team_views.team_list, name="team-list"),
    path("team/invite/", team_views.team_invite, name="team-invite"),
    path(
        "team/<uuid:user_id>/role/",
        team_views.team_assign_role,
        name="team-assign-role",
    ),
    path("team/<uuid:user_id>/remove/", team_views.team_remove, name="team-remove"),
    # ── Support Tickets ──────────────────────────────────────────────────
    path("support/", support_views.support_list, name="support-list"),
    path("support/create/", support_views.support_create, name="support-create"),
    path(
        "support/<uuid:ticket_id>/", support_views.support_detail, name="support-detail"
    ),
    path(
        "support/<uuid:ticket_id>/comment/",
        support_views.support_add_comment,
        name="support-add-comment",
    ),
    # ── Account (existing) ────────────────────────────────────────────────
    path("profile/", views.ProfileView.as_view(), name="profile"),
    path("settings/", views.AccountSettingsView.as_view(), name="settings"),
    path(
        "restaurant-settings/",
        restaurant_views.restaurant_settings,
        name="restaurant-settings",
    ),
    path("subscription/", views.SubscriptionView.as_view(), name="subscription"),
    path("invoices/", views.InvoicesView.as_view(), name="invoices"),
    # ── Subscription Actions ───────────────────────────────────────────
    path(
        "subscription/upgrade/",
        subscription_views.subscription_upgrade,
        name="subscription-upgrade",
    ),
    path(
        "subscription/eft-info/",
        subscription_views.subscription_eft_info,
        name="subscription-eft",
    ),
    path(
        "subscription/cancel/",
        subscription_views.subscription_cancel,
        name="subscription-cancel",
    ),
    path(
        "invoices/<uuid:invoice_id>/pdf/",
        subscription_views.invoice_download_pdf,
        name="invoice-download-pdf",
    ),
    # ── Notification API (navbar widget) ────────────────────────────────
    path(
        "api/notifications/count/",
        notification_views.notification_unread_count,
        name="notification-count-api",
    ),
    path(
        "api/notifications/",
        notification_views.notification_list,
        name="notification-list-api",
    ),
    path(
        "api/notifications/<uuid:notification_id>/read/",
        notification_views.notification_mark_read,
        name="notification-mark-read-api",
    ),
    path(
        "api/notifications/read-all/",
        notification_views.notification_mark_all_read,
        name="notification-mark-all-read-api",
    ),
]
