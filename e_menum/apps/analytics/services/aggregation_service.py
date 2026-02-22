"""
Aggregation Service for E-Menum Analytics.

Provides methods to aggregate raw Order/OrderItem/Customer data into
pre-calculated analytics models (SalesAggregation, ProductPerformance, etc.)

All methods are idempotent - re-running with same parameters updates existing records.
All queries MUST filter by organization_id (multi-tenancy) and deleted_at__isnull=True.

Usage:
    service = AggregationService()
    service.aggregate_daily_sales(org_id, date(2026, 1, 15))
"""

import logging
from datetime import date, datetime, timedelta
from decimal import Decimal

from django.db import models as db_models
from django.db.models import (
    Avg,
    Count,
    DecimalField,
    F,
    Max,
    Min,
    Q,
    Sum,
    Value,
)
from django.db.models.functions import Coalesce, TruncDate, TruncHour
from django.utils import timezone

from apps.analytics.choices import Granularity, MetricType, PeriodType
from apps.analytics.models import (
    CustomerMetric,
    DashboardMetric,
    ProductPerformance,
    SalesAggregation,
)

logger = logging.getLogger(__name__)


class AggregationService:
    """
    Service for aggregating raw transactional data into analytics models.

    All methods:
    - Are idempotent (safe to re-run)
    - Filter by organization_id (MANDATORY)
    - Filter by deleted_at__isnull=True (soft delete)
    - Use Django ORM (no raw SQL)
    """

    # Completed/delivered statuses that count as revenue
    COMPLETED_STATUSES = ['COMPLETED', 'DELIVERED']

    def _get_completed_orders(self, organization_id):
        """
        Get base queryset of completed/delivered orders for an organization.
        Imported lazily to avoid circular imports.
        """
        from apps.orders.models import Order

        return Order.objects.filter(
            organization_id=organization_id,
            status__in=self.COMPLETED_STATUSES,
            deleted_at__isnull=True,
        )

    def aggregate_daily_sales(self, organization_id, target_date: date) -> SalesAggregation:
        """
        Aggregate daily sales data for an organization on a specific date.

        Creates or updates a SalesAggregation record with DAILY granularity.
        Computes revenue, order counts, customer counts, and breakdowns.

        Args:
            organization_id: UUID of the organization
            target_date: The date to aggregate

        Returns:
            SalesAggregation: The created/updated aggregation record
        """
        from apps.orders.models import Order, OrderItem

        orders = self._get_completed_orders(organization_id).filter(
            placed_at__date=target_date,
        )

        # Basic aggregation
        agg = orders.aggregate(
            total_gross=Coalesce(Sum('total_amount'), Value(Decimal('0')), output_field=DecimalField()),
            total_discount=Coalesce(Sum('discount_amount'), Value(Decimal('0')), output_field=DecimalField()),
            total_orders=Count('id'),
            total_customers=Count('customer_id', distinct=True),
        )

        gross_revenue = agg['total_gross']
        discount_total = agg['total_discount']
        net_revenue = gross_revenue - discount_total
        order_count = agg['total_orders']
        customer_count = agg['total_customers']
        avg_order = gross_revenue / order_count if order_count > 0 else Decimal('0')

        # Item count
        item_count = OrderItem.objects.filter(
            order__in=orders,
            deleted_at__isnull=True,
        ).aggregate(
            total=Coalesce(Sum('quantity'), Value(0))
        )['total']

        # New customers: first order on this date
        new_customer_ids = set()
        for cust_id in orders.values_list('customer_id', flat=True).distinct():
            if cust_id is None:
                continue
            first_order_date = Order.objects.filter(
                organization_id=organization_id,
                customer_id=cust_id,
                status__in=self.COMPLETED_STATUSES,
                deleted_at__isnull=True,
            ).aggregate(first=Min('placed_at'))['first']
            if first_order_date and first_order_date.date() == target_date:
                new_customer_ids.add(cust_id)

        # Payment breakdown
        payment_breakdown = {}
        payment_data = orders.values('payment_method').annotate(
            total=Sum('total_amount'),
            count=Count('id'),
        )
        for row in payment_data:
            if row['payment_method']:
                payment_breakdown[row['payment_method']] = {
                    'revenue': str(row['total'] or 0),
                    'count': row['count'],
                }

        # Channel breakdown (using order type)
        channel_breakdown = {}
        channel_data = orders.values('type').annotate(
            total=Sum('total_amount'),
            count=Count('id'),
        )
        for row in channel_data:
            if row['type']:
                channel_breakdown[row['type']] = {
                    'revenue': str(row['total'] or 0),
                    'count': row['count'],
                }

        # Category breakdown
        category_breakdown = {}
        cat_data = OrderItem.objects.filter(
            order__in=orders,
            deleted_at__isnull=True,
            product__isnull=False,
        ).values(
            'product__category_id',
            'product__category__name',
        ).annotate(
            revenue=Sum('total_price'),
            qty=Sum('quantity'),
        )
        for row in cat_data:
            cat_id = str(row['product__category_id']) if row['product__category_id'] else 'uncategorized'
            category_breakdown[cat_id] = {
                'name': row['product__category__name'] or 'Uncategorized',
                'revenue': str(row['revenue'] or 0),
                'quantity': row['qty'] or 0,
            }

        # Create or update
        obj, created = SalesAggregation.all_objects.update_or_create(
            organization_id=organization_id,
            date=target_date,
            granularity=Granularity.DAILY,
            hour=None,
            defaults={
                'gross_revenue': gross_revenue,
                'net_revenue': net_revenue,
                'order_count': order_count,
                'item_count': item_count or 0,
                'avg_order_value': avg_order,
                'customer_count': customer_count,
                'new_customer_count': len(new_customer_ids),
                'payment_breakdown': payment_breakdown,
                'channel_breakdown': channel_breakdown,
                'category_breakdown': category_breakdown,
                'deleted_at': None,  # Restore if was soft-deleted
            },
        )

        action = 'Created' if created else 'Updated'
        logger.info(
            f"{action} daily sales aggregation for org={organization_id}, "
            f"date={target_date}, revenue={gross_revenue}, orders={order_count}"
        )
        return obj

    def aggregate_hourly_sales(self, organization_id, target_date: date, hour: int) -> SalesAggregation:
        """
        Aggregate hourly sales data for a specific hour.

        Args:
            organization_id: UUID of the organization
            target_date: The date to aggregate
            hour: Hour of day (0-23)

        Returns:
            SalesAggregation: The created/updated aggregation record
        """
        from apps.orders.models import Order

        hour_start = datetime.combine(target_date, datetime.min.time().replace(hour=hour))
        hour_end = hour_start + timedelta(hours=1)

        # Make timezone-aware
        tz = timezone.get_current_timezone()
        hour_start = timezone.make_aware(hour_start, tz)
        hour_end = timezone.make_aware(hour_end, tz)

        orders = self._get_completed_orders(organization_id).filter(
            placed_at__gte=hour_start,
            placed_at__lt=hour_end,
        )

        agg = orders.aggregate(
            total_gross=Coalesce(Sum('total_amount'), Value(Decimal('0')), output_field=DecimalField()),
            total_discount=Coalesce(Sum('discount_amount'), Value(Decimal('0')), output_field=DecimalField()),
            total_orders=Count('id'),
            total_customers=Count('customer_id', distinct=True),
        )

        gross_revenue = agg['total_gross']
        net_revenue = gross_revenue - agg['total_discount']
        order_count = agg['total_orders']
        avg_order = gross_revenue / order_count if order_count > 0 else Decimal('0')

        obj, created = SalesAggregation.all_objects.update_or_create(
            organization_id=organization_id,
            date=target_date,
            granularity=Granularity.HOURLY,
            hour=hour,
            defaults={
                'gross_revenue': gross_revenue,
                'net_revenue': net_revenue,
                'order_count': order_count,
                'item_count': 0,
                'avg_order_value': avg_order,
                'customer_count': agg['total_customers'],
                'new_customer_count': 0,
                'payment_breakdown': {},
                'channel_breakdown': {},
                'category_breakdown': {},
                'deleted_at': None,
            },
        )
        return obj

    def aggregate_product_performance(
        self,
        organization_id,
        period_type: str,
        period_start: date,
        period_end: date,
    ) -> list:
        """
        Aggregate product performance for a given period.

        Calculates quantity sold, revenue, sales mix %, and ratings
        for each product in the organization.

        Args:
            organization_id: UUID of the organization
            period_type: PeriodType value (DAILY, WEEKLY, MONTHLY, etc.)
            period_start: Start of the period
            period_end: End of the period

        Returns:
            list: List of created/updated ProductPerformance records
        """
        from apps.orders.models import OrderItem

        # Aggregate per product
        product_data = OrderItem.objects.filter(
            order__organization_id=organization_id,
            order__status__in=self.COMPLETED_STATUSES,
            order__placed_at__date__gte=period_start,
            order__placed_at__date__lte=period_end,
            order__deleted_at__isnull=True,
            deleted_at__isnull=True,
            product__isnull=False,
        ).values(
            'product_id',
        ).annotate(
            qty=Coalesce(Sum('quantity'), Value(0)),
            rev=Coalesce(Sum('total_price'), Value(Decimal('0')), output_field=DecimalField()),
        )

        # Calculate total revenue for sales mix
        total_revenue = sum(row['rev'] for row in product_data) or Decimal('1')

        results = []
        for row in product_data:
            product_id = row['product_id']
            qty = row['qty']
            rev = row['rev']
            sales_mix = (rev / total_revenue * 100) if total_revenue > 0 else Decimal('0')

            # Get product cost if available
            from apps.menu.models import Product
            try:
                product = Product.objects.get(id=product_id)
                cost = product.cost_price * qty if product.cost_price else None
                margin = ((rev - cost) / rev * 100) if cost and rev > 0 else None
            except Product.DoesNotExist:
                cost = None
                margin = None

            # Feedback rating (if available)
            from apps.customers.models import Feedback
            feedback_agg = Feedback.objects.filter(
                organization_id=organization_id,
                deleted_at__isnull=True,
                created_at__date__gte=period_start,
                created_at__date__lte=period_end,
            ).aggregate(
                avg_rating=Avg('rating'),
                review_count=Count('id'),
            )

            obj, _ = ProductPerformance.all_objects.update_or_create(
                organization_id=organization_id,
                product_id=product_id,
                period_type=period_type,
                period_start=period_start,
                defaults={
                    'period_end': period_end,
                    'quantity_sold': qty,
                    'revenue': rev,
                    'cost': cost,
                    'profit_margin': margin,
                    'sales_mix_percent': sales_mix,
                    'avg_rating': feedback_agg.get('avg_rating'),
                    'review_count': feedback_agg.get('review_count', 0),
                    'return_count': 0,
                    'view_count': 0,
                    'deleted_at': None,
                },
            )
            results.append(obj)

        logger.info(
            f"Aggregated product performance for org={organization_id}, "
            f"period={period_type} {period_start}-{period_end}, products={len(results)}"
        )
        return results

    def aggregate_customer_metrics(self, organization_id, target_date: date) -> CustomerMetric:
        """
        Aggregate customer metrics for a specific date.

        Calculates total, new, and returning customer counts.

        Args:
            organization_id: UUID of the organization
            target_date: The date to aggregate

        Returns:
            CustomerMetric: The created/updated metric record
        """
        from apps.customers.models import Customer
        from apps.orders.models import Order

        # Total customers as of this date
        total = Customer.objects.filter(
            organization_id=organization_id,
            deleted_at__isnull=True,
            created_at__date__lte=target_date,
        ).count()

        # New customers on this date
        new = Customer.objects.filter(
            organization_id=organization_id,
            deleted_at__isnull=True,
            created_at__date=target_date,
        ).count()

        # Returning customers: had an order on target_date AND had an order before
        orders_today = Order.objects.filter(
            organization_id=organization_id,
            status__in=self.COMPLETED_STATUSES,
            placed_at__date=target_date,
            deleted_at__isnull=True,
            customer_id__isnull=False,
        ).values_list('customer_id', flat=True).distinct()

        returning = 0
        for cust_id in orders_today:
            has_previous = Order.objects.filter(
                organization_id=organization_id,
                customer_id=cust_id,
                status__in=self.COMPLETED_STATUSES,
                placed_at__date__lt=target_date,
                deleted_at__isnull=True,
            ).exists()
            if has_previous:
                returning += 1

        # Average lifetime value
        avg_ltv = Customer.objects.filter(
            organization_id=organization_id,
            deleted_at__isnull=True,
            total_spent__gt=0,
        ).aggregate(
            avg=Avg('total_spent'),
        )['avg']

        obj, created = CustomerMetric.all_objects.update_or_create(
            organization_id=organization_id,
            date=target_date,
            defaults={
                'total_customers': total,
                'new_customers': new,
                'returning_customers': returning,
                'churn_count': 0,
                'avg_visit_frequency': None,
                'avg_lifetime_value': avg_ltv,
                'nps_score': None,
                'deleted_at': None,
            },
        )

        logger.info(
            f"Aggregated customer metrics for org={organization_id}, "
            f"date={target_date}, total={total}, new={new}, returning={returning}"
        )
        return obj

    def aggregate_dashboard_metrics(self, organization_id, period_type: str) -> list:
        """
        Aggregate dashboard KPI metrics for the current period.

        Creates DashboardMetric records for each metric type
        with comparison to the previous period.

        Args:
            organization_id: UUID of the organization
            period_type: PeriodType value (DAILY, WEEKLY, MONTHLY)

        Returns:
            list: List of created/updated DashboardMetric records
        """
        today = timezone.localdate()

        # Calculate current and previous period boundaries
        if period_type == PeriodType.DAILY:
            current_start = today
            current_end = today
            prev_start = today - timedelta(days=1)
            prev_end = today - timedelta(days=1)
        elif period_type == PeriodType.WEEKLY:
            current_start = today - timedelta(days=today.weekday())
            current_end = today
            prev_start = current_start - timedelta(days=7)
            prev_end = current_start - timedelta(days=1)
        elif period_type == PeriodType.MONTHLY:
            current_start = today.replace(day=1)
            current_end = today
            prev_end = current_start - timedelta(days=1)
            prev_start = prev_end.replace(day=1)
        else:
            logger.warning(f"Unsupported period type: {period_type}")
            return []

        results = []

        # Revenue metric
        current_revenue = SalesAggregation.objects.filter(
            organization_id=organization_id,
            date__gte=current_start,
            date__lte=current_end,
            granularity=Granularity.DAILY,
        ).aggregate(
            total=Coalesce(Sum('gross_revenue'), Value(Decimal('0')), output_field=DecimalField()),
        )['total']

        prev_revenue = SalesAggregation.objects.filter(
            organization_id=organization_id,
            date__gte=prev_start,
            date__lte=prev_end,
            granularity=Granularity.DAILY,
        ).aggregate(
            total=Coalesce(Sum('gross_revenue'), Value(Decimal('0')), output_field=DecimalField()),
        )['total']

        change = (
            ((current_revenue - prev_revenue) / prev_revenue * 100)
            if prev_revenue and prev_revenue > 0
            else None
        )

        obj, _ = DashboardMetric.all_objects.update_or_create(
            organization_id=organization_id,
            metric_type=MetricType.REVENUE,
            period_type=period_type,
            period_start=current_start,
            defaults={
                'period_end': current_end,
                'value': current_revenue,
                'previous_value': prev_revenue,
                'change_percent': change,
                'deleted_at': None,
            },
        )
        results.append(obj)

        # Orders metric
        current_orders = SalesAggregation.objects.filter(
            organization_id=organization_id,
            date__gte=current_start,
            date__lte=current_end,
            granularity=Granularity.DAILY,
        ).aggregate(
            total=Coalesce(Sum('order_count'), Value(0)),
        )['total']

        prev_orders = SalesAggregation.objects.filter(
            organization_id=organization_id,
            date__gte=prev_start,
            date__lte=prev_end,
            granularity=Granularity.DAILY,
        ).aggregate(
            total=Coalesce(Sum('order_count'), Value(0)),
        )['total']

        order_change = (
            ((Decimal(current_orders) - Decimal(prev_orders)) / Decimal(prev_orders) * 100)
            if prev_orders and prev_orders > 0
            else None
        )

        obj, _ = DashboardMetric.all_objects.update_or_create(
            organization_id=organization_id,
            metric_type=MetricType.ORDERS,
            period_type=period_type,
            period_start=current_start,
            defaults={
                'period_end': current_end,
                'value': Decimal(current_orders),
                'previous_value': Decimal(prev_orders) if prev_orders else None,
                'change_percent': order_change,
                'deleted_at': None,
            },
        )
        results.append(obj)

        # Customers metric
        current_customers = SalesAggregation.objects.filter(
            organization_id=organization_id,
            date__gte=current_start,
            date__lte=current_end,
            granularity=Granularity.DAILY,
        ).aggregate(
            total=Coalesce(Sum('customer_count'), Value(0)),
        )['total']

        obj, _ = DashboardMetric.all_objects.update_or_create(
            organization_id=organization_id,
            metric_type=MetricType.CUSTOMERS,
            period_type=period_type,
            period_start=current_start,
            defaults={
                'period_end': current_end,
                'value': Decimal(current_customers),
                'previous_value': None,
                'change_percent': None,
                'deleted_at': None,
            },
        )
        results.append(obj)

        # Average Order Value metric
        avg_order = (
            (current_revenue / Decimal(current_orders))
            if current_orders > 0
            else Decimal('0')
        )

        obj, _ = DashboardMetric.all_objects.update_or_create(
            organization_id=organization_id,
            metric_type=MetricType.AVG_ORDER,
            period_type=period_type,
            period_start=current_start,
            defaults={
                'period_end': current_end,
                'value': avg_order,
                'previous_value': None,
                'change_percent': None,
                'deleted_at': None,
            },
        )
        results.append(obj)

        logger.info(
            f"Aggregated dashboard metrics for org={organization_id}, "
            f"period={period_type}, metrics={len(results)}"
        )
        return results
