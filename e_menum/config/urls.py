"""
E-Menum URL Configuration

Root URL configuration with API versioning structure.
API endpoints follow the pattern: /api/v1/{resource}/

URL Structure:
- /admin/                   - Django Admin
- /api/v1/                  - API Version 1 (current)
- /api/v1/auth/             - Authentication endpoints (login, logout, tokens)
- /api/v1/organizations/    - Organization management
- /api/v1/users/            - User management
- /api/v1/themes/           - Theme management
- /api/v1/menus/            - Menu management
- /api/v1/categories/       - Category management
- /api/v1/products/         - Product management (with variants/modifiers)
- /api/v1/allergens/        - Allergen information
- /api/v1/zones/            - Zone management
- /api/v1/tables/           - Table management
- /api/v1/qr-codes/         - QR code management
- /api/v1/orders/           - Order management
- /api/v1/service-requests/ - Service request management
- /api/v1/features/         - Feature management
- /api/v1/plans/            - Plan management
- /api/v1/subscriptions/    - Subscription management
- /api/v1/invoices/         - Invoice management
- /api/v1/usage/            - Usage tracking
- /health/                  - Health check endpoint
- /m/{slug}/                - Public menu view (SSR)

For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls.i18n import i18n_patterns
from django.http import JsonResponse
from django.utils import timezone

# RedirectView no longer needed — root now served by website app
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render

# Import core module components for proper URL structure
from apps.core.urls import auth_urlpatterns as core_auth_urlpatterns
from apps.core.urls import router as core_router

# Import public menu SSR views
from apps.menu.public_views import PublicMenuView, PublicMenuDetailView

# Import QR code short-URL redirect view
from apps.orders.qr_redirect_view import qr_short_url_redirect

# Import admin upload view
from shared.views.admin_upload import admin_upload_view

# Import enterprise media library view
from apps.media.library_view import media_library

# Import public media serve endpoint
from apps.media.serve_view import media_serve

# Import temporary diagnostics view (remove after debugging)
from apps.core.diagnostics_view import diagnostics_view


# =============================================================================
# HEALTH CHECK & UTILITY VIEWS
# =============================================================================


def health_check(request):
    """
    Health check endpoint for monitoring and load balancers.
    Returns basic service status and version information.
    """
    return JsonResponse(
        {
            "success": True,
            "data": {
                "status": "healthy",
                "service": "e-menum",
                "version": getattr(settings, "EMENUM_API_VERSION", "v1"),
            },
        }
    )


@staff_member_required
def admin_reports(request):
    """
    Custom admin reports page with basic stats.
    """
    from apps.core.models import User
    from apps.menu.models import Menu, Product
    from apps.orders.models import Order

    context = {
        "title": "Reports",
        "total_users": User.objects.filter(deleted_at__isnull=True).count(),
        "total_menus": Menu.objects.filter(deleted_at__isnull=True).count(),
        "total_products": Product.objects.filter(deleted_at__isnull=True).count(),
        "total_orders": Order.objects.filter(deleted_at__isnull=True).count(),
        "is_nav_sidebar_enabled": False,
        "has_permission": True,
    }
    return render(request, "admin/reports.html", context)


@staff_member_required
def admin_seo_dashboard(request):
    """
    SEO Dashboard — overview of 404s, broken links, redirects, and crawl reports.
    """
    from datetime import timedelta
    from django.db.models import Sum, Max, Avg
    from apps.seo.models import BrokenLink, CrawlReport, NotFound404Log, Redirect

    now = timezone.now()
    today = now.date()
    thirty_days_ago = today - timedelta(days=30)

    # Stats
    total_redirects = Redirect.objects.filter(
        is_active=True, deleted_at__isnull=True
    ).count()
    total_broken_links = BrokenLink.objects.filter(is_resolved=False).count()
    today_404s = (
        NotFound404Log.objects.filter(date=today).aggregate(total=Sum("hit_count"))[
            "total"
        ]
        or 0
    )

    # Average SEO score from BlogPosts
    avg_seo_score = None
    try:
        from apps.website.models import BlogPost

        result = BlogPost.objects.filter(deleted_at__isnull=True).aggregate(
            avg=Avg("seo_score")
        )
        if result["avg"] is not None:
            avg_seo_score = round(result["avg"])
    except (ImportError, Exception):
        pass

    # Top 404 paths (last 30 days, aggregated by path)
    top_404s = (
        NotFound404Log.objects.filter(date__gte=thirty_days_ago)
        .values("path")
        .annotate(total_hits=Sum("hit_count"), last_date=Max("date"))
        .order_by("-total_hits")[:10]
    )

    # Recent unresolved broken links
    recent_broken_links = BrokenLink.objects.filter(is_resolved=False).order_by(
        "-first_detected"
    )[:10]

    # Last crawl report
    last_crawl = CrawlReport.objects.first()

    context = {
        "title": "SEO Dashboard",
        "total_redirects": total_redirects,
        "total_broken_links": total_broken_links,
        "today_404s": today_404s,
        "avg_seo_score": avg_seo_score,
        "top_404s": top_404s,
        "recent_broken_links": recent_broken_links,
        "last_crawl": last_crawl,
        "is_nav_sidebar_enabled": False,
        "has_permission": True,
    }
    return render(request, "admin/seo_dashboard.html", context)


@staff_member_required
def admin_shield_dashboard(request):
    """
    Shield Dashboard — overview of blocked requests, threats, and IP reputation.
    """
    from datetime import timedelta
    from django.db.models import Count

    now = timezone.now()
    today = now.date()

    try:
        from apps.seo_shield.models import BlockLog, IPRiskScore

        # Stats
        blocked_today = BlockLog.objects.filter(created_at__date=today).count()
        blocked_7d = BlockLog.objects.filter(
            created_at__gte=now - timedelta(days=7)
        ).count()
        blocked_30d = BlockLog.objects.filter(
            created_at__gte=now - timedelta(days=30)
        ).count()
        high_risk_ips = IPRiskScore.objects.filter(
            risk_score__gt=60,
            is_blacklisted=False,
        ).count()

        # Top block reasons (last 30 days)
        top_reasons = (
            BlockLog.objects.filter(created_at__gte=now - timedelta(days=30))
            .values("reason")
            .annotate(count=Count("id"))
            .order_by("-count")[:10]
        )

        # Top blocked IPs (last 7 days)
        top_blocked_ips = (
            BlockLog.objects.filter(created_at__gte=now - timedelta(days=7))
            .values("ip_address", "country_code")
            .annotate(count=Count("id"))
            .order_by("-count")[:10]
        )

        # Recent block logs
        recent_logs = BlockLog.objects.order_by("-created_at")[:20]

    except (ImportError, Exception):
        blocked_today = blocked_7d = blocked_30d = high_risk_ips = 0
        top_reasons = top_blocked_ips = recent_logs = []

    context = {
        "title": "Shield Dashboard",
        "blocked_today": blocked_today,
        "blocked_7d": blocked_7d,
        "blocked_30d": blocked_30d,
        "high_risk_ips": high_risk_ips,
        "top_reasons": top_reasons,
        "top_blocked_ips": top_blocked_ips,
        "recent_logs": recent_logs,
        "is_nav_sidebar_enabled": False,
        "has_permission": True,
    }
    return render(request, "admin/shield_dashboard.html", context)


@staff_member_required
def admin_settings(request):
    """
    Settings hub page — central place for platform configuration.

    Shows categorised cards linking to AI providers, password change,
    permission matrix, subscription plans, and other settings.
    """
    context = {
        "title": "Settings",
        "is_nav_sidebar_enabled": False,
        "has_permission": True,
    }
    return render(request, "admin/settings.html", context)


@staff_member_required
def permission_matrix(request):
    """
    Permission Matrix admin page — cross-role permission comparison.

    Shows a grid of all permissions (rows) vs all roles (columns),
    with visual indicators for granted, conditional (ABAC), or no access.
    Supports filtering by role scope (platform/organization/all).
    """
    from collections import OrderedDict
    from apps.core.models import Permission, Role, RolePermission

    # Scope filter
    scope_filter = request.GET.get("scope", "all")

    # Fetch roles
    roles_qs = Role.objects.all().order_by("scope", "name")
    if scope_filter == "platform":
        roles_qs = roles_qs.filter(scope="PLATFORM")
    elif scope_filter == "organization":
        roles_qs = roles_qs.filter(scope="ORGANIZATION")

    roles = list(roles_qs)

    # Fetch all permissions grouped by resource
    permissions = Permission.objects.all().order_by("resource", "action")

    # Build role-permission lookup: {(role_id, perm_id): has_conditions}
    role_perm_map = {}
    for rp in RolePermission.objects.all().select_related("permission"):
        has_conditions = bool(rp.conditions)
        role_perm_map[(str(rp.role_id), str(rp.permission_id))] = has_conditions

    # Build matrix: {resource: [perm_data, ...]}
    matrix = OrderedDict()
    for perm in permissions:
        if perm.resource not in matrix:
            matrix[perm.resource] = []

        # Check each role for this permission
        role_checks = []
        for role in roles:
            key = (str(role.id), str(perm.id))
            if key in role_perm_map:
                if role_perm_map[key]:
                    role_checks.append("conditional")
                else:
                    role_checks.append("yes")
            else:
                role_checks.append("no")

        matrix[perm.resource].append(
            {
                "code": perm.code,
                "action": perm.action,
                "action_lower": perm.action.lower(),
                "description": perm.description or "",
                "role_checks": role_checks,
            }
        )

    context = {
        "title": "Permission Matrix",
        "roles": roles,
        "matrix": matrix,
        "scope_filter": scope_filter,
        "col_count": len(roles) + 1,
        "total_roles": len(roles),
        "total_permissions": permissions.count(),
        "total_resources": len(matrix),
        "total_assignments": len(role_perm_map),
        "is_nav_sidebar_enabled": False,
        "has_permission": True,
    }
    return render(request, "admin/permission_matrix.html", context)


def api_root(request):
    """
    API root endpoint providing information about available endpoints.
    """
    return JsonResponse(
        {
            "success": True,
            "data": {
                "message": "Welcome to E-Menum API",
                "version": "v1",
                "documentation": "/api/docs/",
                "endpoints": {
                    # Core module
                    "auth": "/api/v1/auth/",
                    "organizations": "/api/v1/organizations/",
                    "users": "/api/v1/users/",
                    # Menu module
                    "themes": "/api/v1/themes/",
                    "menus": "/api/v1/menus/",
                    "categories": "/api/v1/categories/",
                    "products": "/api/v1/products/",
                    "allergens": "/api/v1/allergens/",
                    # Orders module
                    "zones": "/api/v1/zones/",
                    "tables": "/api/v1/tables/",
                    "qr_codes": "/api/v1/qr-codes/",
                    "orders": "/api/v1/orders/",
                    "service_requests": "/api/v1/service-requests/",
                    # Subscriptions module
                    "features": "/api/v1/features/",
                    "plans": "/api/v1/plans/",
                    "subscriptions": "/api/v1/subscriptions/",
                    "invoices": "/api/v1/invoices/",
                    "plan_features": "/api/v1/plan-features/",
                    "usage": "/api/v1/usage/",
                    # Reporting module
                    "report_catalog": "/api/v1/reports/catalog/",
                    "report_run": "/api/v1/reports/run/",
                    "report_executions": "/api/v1/reports/executions/",
                    "report_schedules": "/api/v1/reports/schedules/",
                    "report_favorites": "/api/v1/reports/favorites/",
                    "dashboard_metrics": "/api/v1/dashboard/metrics/",
                    # Inventory module
                    "inventory_items": "/api/v1/inventory/items/",
                    "stock_movements": "/api/v1/inventory/movements/",
                    "suppliers": "/api/v1/inventory/suppliers/",
                    "purchase_orders": "/api/v1/inventory/purchase-orders/",
                    "recipes": "/api/v1/inventory/recipes/",
                    # Campaigns module
                    "campaigns": "/api/v1/campaigns/",
                    "coupons": "/api/v1/coupons/",
                    "referrals": "/api/v1/referrals/",
                },
            },
        }
    )


# =============================================================================
# API V1 URL PATTERNS
# =============================================================================

api_v1_patterns = [
    # API root information
    path("", api_root, name="api-root"),
    # -------------------------------------------------------------------------
    # Core Module - Authentication endpoints
    # -------------------------------------------------------------------------
    # Auth endpoints at /api/v1/auth/ (login, logout, refresh, verify, me, etc.)
    path("auth/", include((core_auth_urlpatterns, "core"), namespace="auth")),
    # Core resources (organizations, users) at root level
    path("", include(core_router.urls)),
    # -------------------------------------------------------------------------
    # Menu Module
    # -------------------------------------------------------------------------
    # themes/, menus/, categories/, products/, allergens/
    # Also includes nested routes: products/<id>/variants/, products/<id>/modifiers/
    path("", include(("apps.menu.urls", "menu"), namespace="menu")),
    # -------------------------------------------------------------------------
    # Orders Module
    # -------------------------------------------------------------------------
    # zones/, tables/, qr-codes/, orders/, service-requests/
    path("", include(("apps.orders.urls", "orders"), namespace="orders")),
    # -------------------------------------------------------------------------
    # Subscriptions Module
    # -------------------------------------------------------------------------
    # features/, plans/, plan-features/, subscriptions/, invoices/, usage/
    path(
        "",
        include(
            ("apps.subscriptions.urls", "subscriptions"), namespace="subscriptions"
        ),
    ),
    # -------------------------------------------------------------------------
    # Notifications Module
    # -------------------------------------------------------------------------
    # notifications/ (list, detail, read, read-all, archive)
    path(
        "",
        include(
            ("apps.notifications.urls", "notifications"), namespace="notifications"
        ),
    ),
    # -------------------------------------------------------------------------
    # Media Module
    # -------------------------------------------------------------------------
    # media/folders/, media/files/ (upload, CRUD, move)
    path("media/", include(("apps.media.urls", "media"), namespace="media")),
    # -------------------------------------------------------------------------
    # Customers Module
    # -------------------------------------------------------------------------
    # customers/, customers/feedback/ (CRUD, loyalty-history, respond, etc.)
    path("", include(("apps.customers.urls", "customers"), namespace="customers")),
    # -------------------------------------------------------------------------
    # Reporting Module
    # -------------------------------------------------------------------------
    # reports/catalog/, reports/run/, reports/executions/, reports/schedules/,
    # reports/favorites/, dashboard/metrics/
    path("", include(("apps.reporting.urls", "reporting"), namespace="reporting")),
    # -------------------------------------------------------------------------
    # Inventory Module
    # -------------------------------------------------------------------------
    # inventory/items/, inventory/movements/, inventory/suppliers/,
    # inventory/purchase-orders/, inventory/recipes/
    path("", include(("apps.inventory.urls", "inventory"), namespace="inventory")),
    # -------------------------------------------------------------------------
    # Campaigns Module
    # -------------------------------------------------------------------------
    # campaigns/, coupons/, referrals/
    path("", include(("apps.campaigns.urls", "campaigns"), namespace="campaigns")),
    # -------------------------------------------------------------------------
    # Analytics Module (STUB - not yet implemented)
    # -------------------------------------------------------------------------
    # path('', include(('apps.analytics.urls', 'analytics'), namespace='analytics')),
    # -------------------------------------------------------------------------
    # AI Module
    # -------------------------------------------------------------------------
    path("ai/", include(("apps.ai.urls", "ai"), namespace="ai")),
]


# =============================================================================
# MAIN URL PATTERNS
# =============================================================================

urlpatterns = [
    # -------------------------------------------------------------------------
    # SEO URLs (robots.txt, sitemap.xml, etc.) — must be before i18n/admin
    # -------------------------------------------------------------------------
    path("", include("apps.seo.urls")),
    # -------------------------------------------------------------------------
    # Language switching view (non-prefixed)
    # -------------------------------------------------------------------------
    path("i18n/", include("django.conf.urls.i18n")),
    # -------------------------------------------------------------------------
    # Custom Admin Pages (must be BEFORE admin/ catch-all)
    # -------------------------------------------------------------------------
    path("admin/settings/", admin_settings, name="admin-settings"),
    path("admin/reports/", admin_reports, name="admin-reports"),
    path("admin/permission-matrix/", permission_matrix, name="admin-permission-matrix"),
    path("admin/seo-dashboard/", admin_seo_dashboard, name="admin-seo-dashboard"),
    path(
        "admin/shield-dashboard/", admin_shield_dashboard, name="admin-shield-dashboard"
    ),
    # Enterprise media library
    path("admin/media-library/", media_library, name="admin-media-library"),
    # Admin AJAX upload endpoint for image upload widgets
    path("admin/api/upload/", admin_upload_view, name="admin-upload"),
    # -------------------------------------------------------------------------
    # Dashboard App (mainboard + API endpoints)
    # -------------------------------------------------------------------------
    path(
        "admin/", include(("apps.dashboard.urls", "dashboard"), namespace="dashboard")
    ),
    # -------------------------------------------------------------------------
    # User Impersonation (django-impersonate)
    # -------------------------------------------------------------------------
    path("impersonate/", include("impersonate.urls")),
    # -------------------------------------------------------------------------
    # Django Admin
    # -------------------------------------------------------------------------
    path("admin/", admin.site.urls),
    # -------------------------------------------------------------------------
    # Restaurant Owner Portal (/account/)
    # -------------------------------------------------------------------------
    path("account/", include(("apps.accounts.urls", "accounts"), namespace="accounts")),
    # -------------------------------------------------------------------------
    # Health Check (for monitoring, load balancers)
    # -------------------------------------------------------------------------
    path("health/", health_check, name="health-check"),
    path("healthz/", health_check, name="health-check-k8s"),  # Kubernetes style
    # TEMPORARY: production diagnostics (protected by DIAGNOSTICS_TOKEN env)
    path("diag/", diagnostics_view, name="diagnostics"),
    # -------------------------------------------------------------------------
    # API Versioned Routes
    # -------------------------------------------------------------------------
    # Current API version (v1)
    path("api/v1/", include((api_v1_patterns, "api"), namespace="api-v1")),
    # Future versions can be added like:
    # path('api/v2/', include((api_v2_patterns, 'api'), namespace='api-v2')),
    # -------------------------------------------------------------------------
    # API Documentation (OpenAPI/Swagger)
    # -------------------------------------------------------------------------
    # Will be configured with drf-spectacular or similar
    # path('api/docs/', include('drf_spectacular.urls')),
    # -------------------------------------------------------------------------
    # Public Media Serve (redirect to file URL with RBAC)
    # -------------------------------------------------------------------------
    # Serves public media to anyone, private media requires auth + org membership
    path("media/serve/<uuid:pk>/", media_serve, name="media-serve"),
    # -------------------------------------------------------------------------
    # QR Short URL Redirect
    # -------------------------------------------------------------------------
    # Handles /q/<code>/ → redirects to actual menu or target URL
    path("q/<str:code>/", qr_short_url_redirect, name="qr-short-url"),
    # -------------------------------------------------------------------------
    # Public Menu Views (Server-Side Rendered)
    # -------------------------------------------------------------------------
    # Public menu display (no authentication required) - accessed via QR code
    path("m/<slug:menu_slug>/", PublicMenuView.as_view(), name="public-menu"),
    path(
        "m/<slug:menu_slug>/product/<uuid:product_id>/",
        PublicMenuDetailView.as_view(),
        name="public-menu-product",
    ),
    # -------------------------------------------------------------------------
    # JWT Token endpoints (Simple JWT)
    # -------------------------------------------------------------------------
    # NOTE: JWT refresh/verify endpoints are already active via core/urls.py:
    #   POST /api/v1/auth/refresh/  → TokenRefreshView (custom)
    #   POST /api/v1/auth/verify/   → TokenVerifyView (custom)
    #
    # The SimpleJWT standard views below are NOT needed (custom views used):
    # path('api/v1/auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    # path('api/v1/auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    # path('api/v1/auth/token/verify/', TokenVerifyView.as_view(), name='token_verify'),
]

# =============================================================================
# I18N URL PATTERNS — Language-prefixed website URLs
# =============================================================================
# Website marketing pages with language prefix: /tr/, /en/, /ar/, /uk/, /fa/
urlpatterns += i18n_patterns(
    path("", include(("apps.website.urls", "website"), namespace="website")),
    prefix_default_language=True,
)


# =============================================================================
# DEVELOPMENT-ONLY URLS
# =============================================================================

if settings.DEBUG:
    # Serve media files in development
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(
        settings.STATIC_URL,
        document_root=settings.STATICFILES_DIRS[0]
        if settings.STATICFILES_DIRS
        else settings.STATIC_ROOT,
    )

    # Django Debug Toolbar (only when in INSTALLED_APPS)
    if "debug_toolbar" in settings.INSTALLED_APPS:
        try:
            import debug_toolbar

            urlpatterns = [
                path("__debug__/", include(debug_toolbar.urls)),
            ] + urlpatterns
        except ImportError:
            pass

    # DRF Browsable API authentication (for development convenience)
    urlpatterns += [
        path("api-auth/", include("rest_framework.urls", namespace="rest_framework")),
    ]


# =============================================================================
# CUSTOMIZE ADMIN SITE
# =============================================================================

admin.site.site_header = "E-Menum Administration"
admin.site.site_title = "E-Menum Admin"
admin.site.index_title = "Dashboard"
