"""
URL configuration for the Orders application.

This module defines URL patterns for:
- Zone management (CRUD + activate/deactivate)
- Table management (CRUD + status actions)
- QR Code management (CRUD + scan analytics)
- Order management (CRUD + workflow actions)
- Service Request management (CRUD + acknowledge/complete)

URL Structure:
    /api/v1/zones/
        GET /                    - List zones
        POST /                   - Create zone
        GET /<id>/               - Get zone details
        PUT/PATCH /<id>/         - Update zone
        DELETE /<id>/            - Soft delete zone
        POST /<id>/activate/     - Activate zone
        POST /<id>/deactivate/   - Deactivate zone

    /api/v1/tables/
        GET /                    - List tables
        POST /                   - Create table
        GET /<id>/               - Get table details
        PUT/PATCH /<id>/         - Update table
        DELETE /<id>/            - Soft delete table
        POST /<id>/set-available/ - Set table as available
        POST /<id>/set-occupied/  - Set table as occupied
        POST /<id>/set-reserved/  - Set table as reserved
        POST /<id>/activate/      - Activate table
        POST /<id>/deactivate/    - Deactivate table

    /api/v1/qr-codes/
        GET /                    - List QR codes
        POST /                   - Create QR code
        GET /<id>/               - Get QR code details
        PUT/PATCH /<id>/         - Update QR code
        DELETE /<id>/            - Soft delete QR code
        POST /<id>/activate/     - Activate QR code
        POST /<id>/deactivate/   - Deactivate QR code
        GET /<id>/scans/         - Get scan analytics

    /api/v1/orders/
        GET /                    - List orders
        POST /                   - Create order
        GET /<id>/               - Get order details
        PUT/PATCH /<id>/         - Update order
        DELETE /<id>/            - Soft delete order
        POST /<id>/confirm/      - Confirm order
        POST /<id>/prepare/      - Start preparation
        POST /<id>/ready/        - Mark as ready
        POST /<id>/deliver/      - Mark as delivered
        POST /<id>/complete/     - Complete order
        POST /<id>/cancel/       - Cancel order
        POST /<id>/mark-paid/    - Mark as paid
        POST /<id>/recalculate/  - Recalculate totals

    /api/v1/service-requests/
        GET /                    - List service requests
        POST /                   - Create service request
        GET /<id>/               - Get service request details
        PUT/PATCH /<id>/         - Update service request
        DELETE /<id>/            - Soft delete service request
        POST /<id>/acknowledge/  - Acknowledge request
        POST /<id>/complete/     - Complete request

Usage:
    In config/urls.py:
        path('api/v1/', include('apps.orders.urls')),

    Or for specific namespace:
        path('api/v1/', include(('apps.orders.urls', 'orders'), namespace='orders')),
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from apps.orders.views import (
    ZoneViewSet,
    TableViewSet,
    QRCodeViewSet,
    OrderViewSet,
    ServiceRequestViewSet,
    DiscountViewSet,
)


app_name = "orders"


# =============================================================================
# ROUTER CONFIGURATION
# =============================================================================

# Main router for top-level resources
router = DefaultRouter()
router.register(r"zones", ZoneViewSet, basename="zone")
router.register(r"tables", TableViewSet, basename="table")
router.register(r"qr-codes", QRCodeViewSet, basename="qr-code")
router.register(r"orders", OrderViewSet, basename="order")
router.register(r"service-requests", ServiceRequestViewSet, basename="service-request")
router.register(r"discounts", DiscountViewSet, basename="discount")


# =============================================================================
# URL PATTERNS
# =============================================================================

urlpatterns = [
    path("", include(router.urls)),
]
