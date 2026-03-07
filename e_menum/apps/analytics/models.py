"""
Django ORM models for the Analytics application.

This module defines analytics aggregation models for E-Menum:
- DashboardMetric: Cached KPI snapshots per period (revenue, orders, etc.)
- SalesAggregation: Pre-aggregated daily/hourly sales data
- ProductPerformance: Per-product performance metrics per period
- CustomerMetric: Daily customer statistics

Critical Rules:
- Every query MUST include organization_id for tenant isolation
- All entities use soft delete (deleted_at timestamp)
- No physical deletions allowed (use soft_delete method)
- Aggregation data is idempotent - re-running updates existing records
"""

import uuid

from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.analytics.choices import Granularity, MetricType, PeriodType
from apps.core.models import (
    Organization,
    SoftDeleteManager,
    SoftDeleteMixin,
    TimeStampedMixin,
)


class DashboardMetric(TimeStampedMixin, SoftDeleteMixin, models.Model):
    """
    Cached KPI metric snapshots per organization and period.

    Stores pre-calculated dashboard metrics (revenue, orders, customers, etc.)
    for fast dashboard rendering without real-time aggregation.

    Each metric tracks current value, previous value, and percentage change
    for comparison displays (e.g., "Revenue: ₺45,000 (+12% vs last week").

    Attributes:
        organization: FK to parent Organization (tenant isolation)
        metric_type: Type of metric (REVENUE, ORDERS, CUSTOMERS, etc.)
        period_type: Time period granularity (DAILY, WEEKLY, MONTHLY, etc.)
        period_start: Start date of the measurement period
        period_end: End date of the measurement period
        value: Current period value
        previous_value: Previous period value (for comparison)
        change_percent: Percentage change from previous period
        metadata: Additional context data (JSON)
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name=_("ID"),
    )

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="dashboard_metrics",
        verbose_name=_("Organization"),
    )

    metric_type = models.CharField(
        max_length=30,
        choices=MetricType.choices,
        verbose_name=_("Metric type"),
    )

    period_type = models.CharField(
        max_length=20,
        choices=PeriodType.choices,
        verbose_name=_("Period type"),
    )

    period_start = models.DateField(
        verbose_name=_("Period start"),
    )

    period_end = models.DateField(
        verbose_name=_("Period end"),
    )

    value = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        verbose_name=_("Value"),
    )

    previous_value = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Previous value"),
    )

    change_percent = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Change percent"),
    )

    metadata = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_("Metadata"),
    )

    # Managers
    objects = SoftDeleteManager()
    all_objects = models.Manager()

    class Meta:
        db_table = "analytics_dashboard_metrics"
        verbose_name = _("Dashboard Metric")
        verbose_name_plural = _("Dashboard Metrics")
        ordering = ["-period_start"]
        unique_together = [
            ["organization", "metric_type", "period_type", "period_start"],
        ]
        indexes = [
            models.Index(
                fields=["organization", "period_type", "period_start"],
                name="dm_org_period_start_idx",
            ),
            models.Index(
                fields=["organization", "metric_type"],
                name="dm_org_metric_idx",
            ),
            models.Index(
                fields=["organization", "deleted_at"],
                name="dm_org_deleted_idx",
            ),
        ]

    def __str__(self):
        return f"{self.metric_type} ({self.period_type}) - {self.period_start}"


class SalesAggregation(TimeStampedMixin, SoftDeleteMixin, models.Model):
    """
    Pre-aggregated sales data at daily or hourly granularity.

    Stores rolled-up sales metrics from Order/OrderItem tables,
    including payment, channel, and category breakdowns as JSON.

    This model is the primary data source for revenue reports,
    sales dashboards, and trend analysis.

    Attributes:
        organization: FK to parent Organization
        date: The date of the aggregation
        hour: Hour of day (0-23) for hourly granularity, null for daily
        granularity: HOURLY or DAILY
        gross_revenue: Total revenue before discounts
        net_revenue: Revenue after discounts
        order_count: Number of orders
        item_count: Total items sold
        avg_order_value: Average order value
        customer_count: Distinct customer count
        new_customer_count: First-time customers
        payment_breakdown: JSON breakdown by payment method
        channel_breakdown: JSON breakdown by order type/channel
        category_breakdown: JSON breakdown by menu category
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name=_("ID"),
    )

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="sales_aggregations",
        verbose_name=_("Organization"),
    )

    date = models.DateField(
        verbose_name=_("Date"),
    )

    hour = models.IntegerField(
        null=True,
        blank=True,
        verbose_name=_("Hour"),
        help_text=_("Hour of day (0-23) for hourly granularity"),
    )

    granularity = models.CharField(
        max_length=10,
        choices=Granularity.choices,
        default=Granularity.DAILY,
        verbose_name=_("Granularity"),
    )

    gross_revenue = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        verbose_name=_("Gross revenue"),
    )

    net_revenue = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        verbose_name=_("Net revenue"),
    )

    order_count = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Order count"),
    )

    item_count = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Item count"),
    )

    avg_order_value = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name=_("Average order value"),
    )

    customer_count = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Customer count"),
    )

    new_customer_count = models.PositiveIntegerField(
        default=0,
        verbose_name=_("New customer count"),
    )

    payment_breakdown = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_("Payment breakdown"),
        help_text=_("Breakdown by payment method: {cash: X, card: Y, ...}"),
    )

    channel_breakdown = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_("Channel breakdown"),
        help_text=_("Breakdown by order type: {dine_in: X, takeaway: Y, ...}"),
    )

    category_breakdown = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_("Category breakdown"),
        help_text=_("Breakdown by category: {cat_id: {revenue: X, qty: Y}, ...}"),
    )

    # Managers
    objects = SoftDeleteManager()
    all_objects = models.Manager()

    class Meta:
        db_table = "analytics_sales_aggregations"
        verbose_name = _("Sales Aggregation")
        verbose_name_plural = _("Sales Aggregations")
        ordering = ["-date", "-hour"]
        indexes = [
            models.Index(
                fields=["organization", "date", "granularity"],
                name="sa_org_date_gran_idx",
            ),
            models.Index(
                fields=["organization", "date", "hour"],
                name="sa_org_date_hour_idx",
            ),
            models.Index(
                fields=["organization", "deleted_at"],
                name="sa_org_deleted_idx",
            ),
        ]

    def __str__(self):
        hour_str = f" H{self.hour}" if self.hour is not None else ""
        return f"Sales {self.date}{hour_str} ({self.granularity})"


class ProductPerformance(TimeStampedMixin, SoftDeleteMixin, models.Model):
    """
    Per-product performance metrics aggregated by period.

    Tracks sales volume, revenue, profitability, and customer satisfaction
    for each product. Used for menu performance matrix (BCG), top sellers,
    and product optimization reports.

    Attributes:
        organization: FK to parent Organization
        product: FK to menu Product
        period_type: Aggregation period (DAILY, WEEKLY, MONTHLY, etc.)
        period_start: Start of the measurement period
        period_end: End of the measurement period
        quantity_sold: Total units sold
        revenue: Total revenue generated
        cost: Total cost (if known)
        profit_margin: Profit margin percentage
        sales_mix_percent: Product's share of total sales
        avg_rating: Average customer rating
        review_count: Number of reviews
        return_count: Number of returns/cancellations
        view_count: Number of menu views (for conversion analysis)
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name=_("ID"),
    )

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="product_performances",
        verbose_name=_("Organization"),
    )

    product = models.ForeignKey(
        "menu.Product",
        on_delete=models.CASCADE,
        related_name="performance_records",
        verbose_name=_("Product"),
    )

    period_type = models.CharField(
        max_length=20,
        choices=PeriodType.choices,
        verbose_name=_("Period type"),
    )

    period_start = models.DateField(
        verbose_name=_("Period start"),
    )

    period_end = models.DateField(
        verbose_name=_("Period end"),
    )

    quantity_sold = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Quantity sold"),
    )

    revenue = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        verbose_name=_("Revenue"),
    )

    cost = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Cost"),
    )

    profit_margin = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Profit margin (%)"),
    )

    sales_mix_percent = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=0,
        verbose_name=_("Sales mix (%)"),
    )

    avg_rating = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Average rating"),
    )

    review_count = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Review count"),
    )

    return_count = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Return count"),
    )

    view_count = models.PositiveIntegerField(
        default=0,
        verbose_name=_("View count"),
    )

    # Managers
    objects = SoftDeleteManager()
    all_objects = models.Manager()

    class Meta:
        db_table = "analytics_product_performances"
        verbose_name = _("Product Performance")
        verbose_name_plural = _("Product Performances")
        ordering = ["-period_start", "-revenue"]
        unique_together = [
            ["organization", "product", "period_type", "period_start"],
        ]
        indexes = [
            models.Index(
                fields=["organization", "period_type", "period_start"],
                name="pp_org_period_start_idx",
            ),
            models.Index(
                fields=["organization", "product"],
                name="pp_org_product_idx",
            ),
            models.Index(
                fields=["organization", "deleted_at"],
                name="pp_org_deleted_idx",
            ),
        ]

    def __str__(self):
        return f"{self.product} ({self.period_type} {self.period_start})"


class CustomerMetric(TimeStampedMixin, SoftDeleteMixin, models.Model):
    """
    Daily customer statistics per organization.

    Tracks customer acquisition, retention, and satisfaction metrics.
    Used for customer overview reports, churn analysis, and NPS tracking.

    Attributes:
        organization: FK to parent Organization
        date: Date of the metric snapshot
        total_customers: Total registered customers
        new_customers: Customers registered on this date
        returning_customers: Customers with repeat orders on this date
        churn_count: Customers considered churned
        avg_visit_frequency: Average visits per customer
        avg_lifetime_value: Average customer lifetime value
        nps_score: Net Promoter Score
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name=_("ID"),
    )

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="customer_metrics",
        verbose_name=_("Organization"),
    )

    date = models.DateField(
        verbose_name=_("Date"),
    )

    total_customers = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Total customers"),
    )

    new_customers = models.PositiveIntegerField(
        default=0,
        verbose_name=_("New customers"),
    )

    returning_customers = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Returning customers"),
    )

    churn_count = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Churn count"),
    )

    avg_visit_frequency = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Average visit frequency"),
    )

    avg_lifetime_value = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Average lifetime value"),
    )

    nps_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("NPS score"),
    )

    # Managers
    objects = SoftDeleteManager()
    all_objects = models.Manager()

    class Meta:
        db_table = "analytics_customer_metrics"
        verbose_name = _("Customer Metric")
        verbose_name_plural = _("Customer Metrics")
        ordering = ["-date"]
        unique_together = [
            ["organization", "date"],
        ]
        indexes = [
            models.Index(
                fields=["organization", "date"],
                name="cm_org_date_idx",
            ),
            models.Index(
                fields=["organization", "deleted_at"],
                name="cm_org_deleted_idx",
            ),
        ]

    def __str__(self):
        return f"Customer metrics {self.date} - {self.organization}"
