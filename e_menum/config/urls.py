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
from django.http import JsonResponse

# Import core module components for proper URL structure
from apps.core.urls import auth_urlpatterns as core_auth_urlpatterns
from apps.core.urls import router as core_router


# =============================================================================
# HEALTH CHECK & UTILITY VIEWS
# =============================================================================

def health_check(request):
    """
    Health check endpoint for monitoring and load balancers.
    Returns basic service status and version information.
    """
    return JsonResponse({
        'success': True,
        'data': {
            'status': 'healthy',
            'service': 'e-menum',
            'version': getattr(settings, 'EMENUM_API_VERSION', 'v1'),
        }
    })


def api_root(request):
    """
    API root endpoint providing information about available endpoints.
    """
    return JsonResponse({
        'success': True,
        'data': {
            'message': 'Welcome to E-Menum API',
            'version': 'v1',
            'documentation': '/api/docs/',
            'endpoints': {
                # Core module
                'auth': '/api/v1/auth/',
                'organizations': '/api/v1/organizations/',
                'users': '/api/v1/users/',
                # Menu module
                'themes': '/api/v1/themes/',
                'menus': '/api/v1/menus/',
                'categories': '/api/v1/categories/',
                'products': '/api/v1/products/',
                'allergens': '/api/v1/allergens/',
                # Orders module
                'zones': '/api/v1/zones/',
                'tables': '/api/v1/tables/',
                'qr_codes': '/api/v1/qr-codes/',
                'orders': '/api/v1/orders/',
                'service_requests': '/api/v1/service-requests/',
                # Subscriptions module
                'features': '/api/v1/features/',
                'plans': '/api/v1/plans/',
                'subscriptions': '/api/v1/subscriptions/',
                'invoices': '/api/v1/invoices/',
                'plan_features': '/api/v1/plan-features/',
                'usage': '/api/v1/usage/',
            }
        }
    })


# =============================================================================
# API V1 URL PATTERNS
# =============================================================================

api_v1_patterns = [
    # API root information
    path('', api_root, name='api-root'),

    # -------------------------------------------------------------------------
    # Core Module - Authentication endpoints
    # -------------------------------------------------------------------------
    # Auth endpoints at /api/v1/auth/ (login, logout, refresh, verify, me, etc.)
    path('auth/', include((core_auth_urlpatterns, 'core'), namespace='auth')),

    # Core resources (organizations, users) at root level
    path('', include(core_router.urls)),

    # -------------------------------------------------------------------------
    # Menu Module
    # -------------------------------------------------------------------------
    # themes/, menus/, categories/, products/, allergens/
    # Also includes nested routes: products/<id>/variants/, products/<id>/modifiers/
    path('', include(('apps.menu.urls', 'menu'), namespace='menu')),

    # -------------------------------------------------------------------------
    # Orders Module
    # -------------------------------------------------------------------------
    # zones/, tables/, qr-codes/, orders/, service-requests/
    path('', include(('apps.orders.urls', 'orders'), namespace='orders')),

    # -------------------------------------------------------------------------
    # Subscriptions Module
    # -------------------------------------------------------------------------
    # features/, plans/, plan-features/, subscriptions/, invoices/, usage/
    path('', include(('apps.subscriptions.urls', 'subscriptions'), namespace='subscriptions')),

    # -------------------------------------------------------------------------
    # Customers Module (TODO: Implement when views are ready)
    # -------------------------------------------------------------------------
    # path('', include(('apps.customers.urls', 'customers'), namespace='customers')),

    # -------------------------------------------------------------------------
    # Media Module (TODO: Implement when views are ready)
    # -------------------------------------------------------------------------
    # path('', include(('apps.media.urls', 'media'), namespace='media')),

    # -------------------------------------------------------------------------
    # Notifications Module (TODO: Implement when views are ready)
    # -------------------------------------------------------------------------
    # path('', include(('apps.notifications.urls', 'notifications'), namespace='notifications')),

    # -------------------------------------------------------------------------
    # Analytics Module (TODO: Implement when views are ready)
    # -------------------------------------------------------------------------
    # path('', include(('apps.analytics.urls', 'analytics'), namespace='analytics')),

    # -------------------------------------------------------------------------
    # AI Module (TODO: Implement when views are ready)
    # -------------------------------------------------------------------------
    # path('', include(('apps.ai.urls', 'ai'), namespace='ai')),
]


# =============================================================================
# MAIN URL PATTERNS
# =============================================================================

urlpatterns = [
    # -------------------------------------------------------------------------
    # Django Admin
    # -------------------------------------------------------------------------
    path('admin/', admin.site.urls),

    # -------------------------------------------------------------------------
    # Health Check (for monitoring, load balancers)
    # -------------------------------------------------------------------------
    path('health/', health_check, name='health-check'),
    path('healthz/', health_check, name='health-check-k8s'),  # Kubernetes style

    # -------------------------------------------------------------------------
    # API Versioned Routes
    # -------------------------------------------------------------------------
    # Current API version (v1)
    path('api/v1/', include((api_v1_patterns, 'api'), namespace='api-v1')),

    # Future versions can be added like:
    # path('api/v2/', include((api_v2_patterns, 'api'), namespace='api-v2')),

    # -------------------------------------------------------------------------
    # API Documentation (OpenAPI/Swagger)
    # -------------------------------------------------------------------------
    # Will be configured with drf-spectacular or similar
    # path('api/docs/', include('drf_spectacular.urls')),

    # -------------------------------------------------------------------------
    # Public Menu Views (Server-Side Rendered)
    # -------------------------------------------------------------------------
    # Public menu display (no authentication required)
    # path('m/<slug:menu_slug>/', include('apps.menu.public_urls')),

    # -------------------------------------------------------------------------
    # JWT Token endpoints (Simple JWT)
    # -------------------------------------------------------------------------
    # These will be uncommented when rest_framework_simplejwt is installed
    # path('api/v1/auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    # path('api/v1/auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    # path('api/v1/auth/token/verify/', TokenVerifyView.as_view(), name='token_verify'),
]


# =============================================================================
# DEVELOPMENT-ONLY URLS
# =============================================================================

if settings.DEBUG:
    # Serve media files in development
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0] if settings.STATICFILES_DIRS else settings.STATIC_ROOT)

    # Django Debug Toolbar
    try:
        import debug_toolbar
        urlpatterns = [
            path('__debug__/', include(debug_toolbar.urls)),
        ] + urlpatterns
    except ImportError:
        pass

    # DRF Browsable API authentication (for development convenience)
    urlpatterns += [
        path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    ]


# =============================================================================
# CUSTOMIZE ADMIN SITE
# =============================================================================

admin.site.site_header = 'E-Menum Administration'
admin.site.site_title = 'E-Menum Admin'
admin.site.index_title = 'Dashboard'
