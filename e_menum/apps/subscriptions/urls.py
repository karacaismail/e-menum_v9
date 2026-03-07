"""
URL configuration for the Subscriptions application.

This module defines URL patterns for:
- Feature management (platform-level)
- Plan management (platform-level with public read)
- Subscription management (tenant-scoped)
- Invoice management (tenant-scoped)
- PlanFeature management (platform-level)
- Usage tracking (tenant-scoped, read-only)

URL Structure:
    /api/v1/features/
        GET /                    - List features
        POST /                   - Create feature (admin)
        GET /<id>/               - Get feature details
        PUT/PATCH /<id>/         - Update feature (admin)
        DELETE /<id>/            - Soft delete feature (admin)

    /api/v1/plans/
        GET /                    - List plans (public)
        POST /                   - Create plan (admin)
        GET /<id>/               - Get plan details (public)
        PUT/PATCH /<id>/         - Update plan (admin)
        DELETE /<id>/            - Soft delete plan (admin)
        POST /<id>/set-default/  - Set as default plan (admin)
        GET /<id>/compare/       - Compare with another plan

    /api/v1/subscriptions/
        GET /                    - List organization subscriptions
        POST /                   - Create subscription
        GET /current/            - Get current active subscription
        GET /<id>/               - Get subscription details
        PUT/PATCH /<id>/         - Update subscription
        DELETE /<id>/            - Soft delete subscription
        POST /<id>/cancel/       - Cancel subscription
        POST /<id>/reactivate/   - Reactivate subscription
        POST /<id>/change-plan/  - Change subscription plan

    /api/v1/invoices/
        GET /                    - List organization invoices
        POST /                   - Create invoice
        GET /<id>/               - Get invoice details
        PUT/PATCH /<id>/         - Update invoice
        DELETE /<id>/            - Soft delete invoice
        POST /<id>/finalize/     - Finalize draft invoice
        POST /<id>/mark-paid/    - Mark invoice as paid
        POST /<id>/void/         - Void invoice
        POST /<id>/refund/       - Refund invoice

    /api/v1/plan-features/
        GET /                    - List plan-feature links
        POST /                   - Create link (admin)
        GET /<id>/               - Get link details
        PUT/PATCH /<id>/         - Update link (admin)
        DELETE /<id>/            - Delete link (admin)

    /api/v1/usage/
        GET /                    - List organization usage
        GET /summary/            - Get usage summary
        GET /<id>/               - Get usage details

Usage:
    In config/urls.py:
        path('api/v1/', include('apps.subscriptions.urls')),

    Or for specific namespace:
        path('api/v1/', include(('apps.subscriptions.urls', 'subscriptions'), namespace='subscriptions')),
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from apps.subscriptions.views import (
    FeatureViewSet,
    PlanViewSet,
    SubscriptionViewSet,
    InvoiceViewSet,
    PlanFeatureViewSet,
    OrganizationUsageViewSet,
)


app_name = "subscriptions"


# =============================================================================
# ROUTER CONFIGURATION
# =============================================================================

router = DefaultRouter()

# Platform-level resources (no tenant scope)
router.register(r"features", FeatureViewSet, basename="feature")
router.register(r"plans", PlanViewSet, basename="plan")
router.register(r"plan-features", PlanFeatureViewSet, basename="plan-feature")

# Tenant-scoped resources
router.register(r"subscriptions", SubscriptionViewSet, basename="subscription")
router.register(r"invoices", InvoiceViewSet, basename="invoice")
router.register(r"usage", OrganizationUsageViewSet, basename="usage")


# =============================================================================
# URL PATTERNS
# =============================================================================

urlpatterns = [
    path("", include(router.urls)),
]
