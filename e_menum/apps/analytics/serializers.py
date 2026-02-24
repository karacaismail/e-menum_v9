"""
DRF Serializers for the Analytics application.

All serializers are read-only — analytics data is generated
by background tasks, not directly via API.
"""

from rest_framework import serializers

from apps.analytics.models import (
    CustomerMetric,
    DashboardMetric,
    ProductPerformance,
    SalesAggregation,
)


class DashboardMetricSerializer(serializers.ModelSerializer):
    """Read-only serializer for cached KPI metric snapshots."""

    class Meta:
        model = DashboardMetric
        fields = [
            'id', 'metric_type', 'period_type',
            'period_start', 'period_end',
            'value', 'previous_value', 'change_percent',
            'metadata', 'created_at',
        ]
        read_only_fields = fields


class SalesAggregationSerializer(serializers.ModelSerializer):
    """Read-only serializer for pre-aggregated sales data."""

    class Meta:
        model = SalesAggregation
        fields = [
            'id', 'date', 'hour', 'granularity',
            'gross_revenue', 'net_revenue',
            'order_count', 'item_count', 'avg_order_value',
            'customer_count', 'new_customer_count',
            'payment_breakdown', 'channel_breakdown', 'category_breakdown',
            'created_at',
        ]
        read_only_fields = fields


class ProductPerformanceSerializer(serializers.ModelSerializer):
    """Read-only serializer for per-product performance metrics."""

    product_name = serializers.CharField(source='product.name', read_only=True)

    class Meta:
        model = ProductPerformance
        fields = [
            'id', 'product', 'product_name',
            'period_type', 'period_start', 'period_end',
            'quantity_sold', 'revenue', 'cost', 'profit_margin',
            'sales_mix_percent', 'avg_rating', 'review_count',
            'return_count', 'view_count',
            'created_at',
        ]
        read_only_fields = fields


class CustomerMetricSerializer(serializers.ModelSerializer):
    """Read-only serializer for daily customer statistics."""

    class Meta:
        model = CustomerMetric
        fields = [
            'id', 'date',
            'total_customers', 'new_customers',
            'returning_customers', 'churn_count',
            'avg_visit_frequency', 'avg_lifetime_value', 'nps_score',
            'created_at',
        ]
        read_only_fields = fields
