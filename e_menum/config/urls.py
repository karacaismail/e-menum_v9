"""
E-Menum URL Configuration

Root URL configuration with API versioning structure.
API endpoints follow the pattern: /api/v1/{resource}/

URL Structure:
- /admin/                   - Django Admin
- /api/v1/                  - API Version 1 (current)
- /api/v1/auth/             - Authentication endpoints
- /api/v1/menus/            - Menu management
- /api/v1/categories/       - Category management
- /api/v1/products/         - Product management
- /api/v1/orders/           - Order management
- /api/v1/qr-codes/         - QR code management
- /api/v1/subscriptions/    - Subscription management
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
from django.views.generic import TemplateView


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
                'auth': '/api/v1/auth/',
                'menus': '/api/v1/menus/',
                'categories': '/api/v1/categories/',
                'products': '/api/v1/products/',
                'orders': '/api/v1/orders/',
                'qr_codes': '/api/v1/qr-codes/',
                'subscriptions': '/api/v1/subscriptions/',
                'organizations': '/api/v1/organizations/',
            }
        }
    })


# =============================================================================
# API V1 URL PATTERNS
# =============================================================================

api_v1_patterns = [
    # API root information
    path('', api_root, name='api-root'),

    # Authentication endpoints (JWT)
    path('auth/', include(('apps.core.urls', 'core'), namespace='auth')),

    # Core module
    # path('organizations/', include('apps.core.api.organization_urls')),
    # path('users/', include('apps.core.api.user_urls')),
    # path('roles/', include('apps.core.api.role_urls')),

    # Menu module
    # path('menus/', include('apps.menu.api.urls')),
    # path('categories/', include('apps.menu.api.category_urls')),
    # path('products/', include('apps.menu.api.product_urls')),
    # path('themes/', include('apps.menu.api.theme_urls')),

    # Orders module
    # path('orders/', include('apps.orders.api.urls')),
    # path('tables/', include('apps.orders.api.table_urls')),
    # path('zones/', include('apps.orders.api.zone_urls')),
    # path('qr-codes/', include('apps.orders.api.qrcode_urls')),

    # Subscriptions module
    # path('plans/', include('apps.subscriptions.api.plan_urls')),
    # path('subscriptions/', include('apps.subscriptions.api.subscription_urls')),
    # path('invoices/', include('apps.subscriptions.api.invoice_urls')),

    # Customers module
    # path('customers/', include('apps.customers.api.urls')),
    # path('feedback/', include('apps.customers.api.feedback_urls')),

    # Media module
    # path('media/', include('apps.media.api.urls')),

    # Notifications module
    # path('notifications/', include('apps.notifications.api.urls')),

    # Analytics module (read-only endpoints)
    # path('analytics/', include('apps.analytics.api.urls')),

    # AI module (content generation)
    # path('ai/', include('apps.ai.api.urls')),
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
