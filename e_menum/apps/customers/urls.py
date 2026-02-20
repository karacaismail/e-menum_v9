"""
URL configuration for the Customers application.

Routes:
    GET    /api/v1/customers/                       - List customers
    POST   /api/v1/customers/                       - Create customer
    GET    /api/v1/customers/{id}/                  - Get customer details
    PUT    /api/v1/customers/{id}/                  - Update customer
    PATCH  /api/v1/customers/{id}/                  - Partial update
    DELETE /api/v1/customers/{id}/                  - Soft delete
    GET    /api/v1/customers/{id}/loyalty-history/  - Loyalty history

    GET    /api/v1/customers/feedback/              - List feedback
    POST   /api/v1/customers/feedback/              - Create feedback
    GET    /api/v1/customers/feedback/{id}/         - Get feedback detail
    DELETE /api/v1/customers/feedback/{id}/         - Delete feedback
    POST   /api/v1/customers/feedback/{id}/respond/ - Staff respond
    POST   /api/v1/customers/feedback/{id}/publish/ - Make public
    POST   /api/v1/customers/feedback/{id}/archive/ - Archive
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from apps.customers.views import CustomerViewSet, FeedbackViewSet


app_name = 'customers'

router = DefaultRouter()
router.register(r'customers', CustomerViewSet, basename='customer')
router.register(r'customers/feedback', FeedbackViewSet, basename='feedback')

urlpatterns = [
    path('', include(router.urls)),
]
