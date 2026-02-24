"""
URL patterns for the Analytics application.
"""

from django.urls import path

from apps.analytics.views import (
    CustomerMetricListView,
    DashboardMetricDetailView,
    DashboardMetricListView,
    ProductPerformanceListView,
    SalesAggregationListView,
)

app_name = 'analytics'

urlpatterns = [
    path('metrics/', DashboardMetricListView.as_view(), name='metric-list'),
    path('metrics/<uuid:pk>/', DashboardMetricDetailView.as_view(), name='metric-detail'),
    path('sales/', SalesAggregationListView.as_view(), name='sales-list'),
    path('products/', ProductPerformanceListView.as_view(), name='product-performance-list'),
    path('customers/', CustomerMetricListView.as_view(), name='customer-metric-list'),
]
