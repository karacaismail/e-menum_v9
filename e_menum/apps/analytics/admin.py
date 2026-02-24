"""
Django Admin configuration for the Analytics application.
"""

from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from apps.analytics.models import (
    CustomerMetric,
    DashboardMetric,
    ProductPerformance,
    SalesAggregation,
)


@admin.register(DashboardMetric)
class DashboardMetricAdmin(admin.ModelAdmin):
    list_display = (
        'organization', 'metric_type', 'period_type',
        'period_start', 'period_end', 'value', 'change_percent',
    )
    list_filter = ('metric_type', 'period_type', 'organization')
    search_fields = ('organization__name',)
    readonly_fields = ('id', 'created_at', 'updated_at')
    date_hierarchy = 'period_start'
    ordering = ('-period_start',)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('organization')


@admin.register(SalesAggregation)
class SalesAggregationAdmin(admin.ModelAdmin):
    list_display = (
        'organization', 'date', 'granularity',
        'gross_revenue', 'order_count', 'customer_count',
    )
    list_filter = ('granularity', 'organization')
    search_fields = ('organization__name',)
    readonly_fields = ('id', 'created_at', 'updated_at')
    date_hierarchy = 'date'
    ordering = ('-date',)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('organization')


@admin.register(ProductPerformance)
class ProductPerformanceAdmin(admin.ModelAdmin):
    list_display = (
        'organization', 'product', 'period_type',
        'period_start', 'quantity_sold', 'revenue', 'profit_margin',
    )
    list_filter = ('period_type', 'organization')
    search_fields = ('organization__name', 'product__name')
    readonly_fields = ('id', 'created_at', 'updated_at')
    date_hierarchy = 'period_start'
    ordering = ('-period_start',)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('organization', 'product')


@admin.register(CustomerMetric)
class CustomerMetricAdmin(admin.ModelAdmin):
    list_display = (
        'organization', 'date', 'total_customers',
        'new_customers', 'returning_customers', 'nps_score',
    )
    list_filter = ('organization',)
    search_fields = ('organization__name',)
    readonly_fields = ('id', 'created_at', 'updated_at')
    date_hierarchy = 'date'
    ordering = ('-date',)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('organization')
