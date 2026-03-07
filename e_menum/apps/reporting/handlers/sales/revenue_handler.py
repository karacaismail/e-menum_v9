"""
Revenue Report Handler (RPT-SAL-001).

Generates comprehensive revenue reports with period comparison,
dimensional breakdowns (channel, payment method, category), and
trend data. Primarily queries SalesAggregation for pre-aggregated
data, falling back to Order model for real-time accuracy.

Critical Rules:
    - ALL queries MUST filter by organization_id (multi-tenancy)
    - ALL queries on soft-delete models MUST filter deleted_at__isnull=True
    - Return values must be JSON-serializable (Decimal -> float)
"""

import logging
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import List, Optional

from django.db.models import Avg, Count, F, Sum
from django.db.models.functions import TruncDate, TruncWeek, TruncMonth

from apps.analytics.choices import Granularity
from apps.analytics.models import SalesAggregation
from apps.orders.choices import OrderStatus
from apps.orders.models import Order
from apps.reporting.services.report_engine import BaseReportHandler, register_handler

logger = logging.getLogger(__name__)


def _to_float(val) -> float:
    """Safely convert a Decimal or None to float."""
    if val is None:
        return 0.0
    return float(val)


def _parse_date(val) -> Optional[date]:
    """Parse a date string (YYYY-MM-DD) or return date object as-is."""
    if val is None:
        return None
    if isinstance(val, date):
        return val
    if isinstance(val, datetime):
        return val.date()
    return datetime.strptime(str(val), '%Y-%m-%d').date()


def _safe_percent_change(current: float, previous: float) -> Optional[float]:
    """Calculate percentage change, handling division by zero."""
    if previous == 0:
        if current == 0:
            return 0.0
        return None  # infinite change
    return round(((current - previous) / previous) * 100, 2)


@register_handler('RPT-SAL-001')
class RevenueReportHandler(BaseReportHandler):
    """
    Revenue report handler.

    Provides total revenue, net revenue, order count, average order value,
    comparison with the previous period, and optional dimensional breakdowns.

    Parameters:
        period: str - DAILY, WEEKLY, or MONTHLY (default: DAILY)
        start_date: str - Start date in YYYY-MM-DD format
        end_date: str - End date in YYYY-MM-DD format
        dimension: str - Optional breakdown dimension: 'channel', 'payment', 'category'
    """

    feature_key = 'RPT-SAL-001'

    def get_required_permissions(self) -> List[str]:
        return ['reporting.view', 'sales.view']

    def get_default_parameters(self) -> dict:
        today = date.today()
        return {
            'period': 'DAILY',
            'start_date': (today - timedelta(days=30)).isoformat(),
            'end_date': today.isoformat(),
            'dimension': None,
        }

    def validate_parameters(self, parameters: dict) -> dict:
        merged = {**self.get_default_parameters(), **parameters}

        # Parse and validate dates
        merged['start_date'] = _parse_date(merged['start_date'])
        merged['end_date'] = _parse_date(merged['end_date'])

        if merged['start_date'] > merged['end_date']:
            from shared.utils.exceptions import AppException
            raise AppException(
                code='INVALID_DATE_RANGE',
                message='start_date must be before or equal to end_date',
                status_code=400,
            )

        # Validate period
        valid_periods = ['DAILY', 'WEEKLY', 'MONTHLY']
        if merged['period'] not in valid_periods:
            from shared.utils.exceptions import AppException
            raise AppException(
                code='INVALID_PERIOD',
                message=f"period must be one of {valid_periods}",
                status_code=400,
            )

        # Validate dimension
        valid_dimensions = [None, 'channel', 'payment', 'category']
        if merged['dimension'] not in valid_dimensions:
            from shared.utils.exceptions import AppException
            raise AppException(
                code='INVALID_DIMENSION',
                message=f"dimension must be one of {valid_dimensions}",
                status_code=400,
            )

        return merged

    def generate(self, org_id: str, parameters: dict) -> dict:
        start_date = parameters['start_date']
        end_date = parameters['end_date']
        period = parameters['period']
        dimension = parameters.get('dimension')

        # ---- Current period metrics from SalesAggregation ----
        current_agg = self._get_aggregation_metrics(org_id, start_date, end_date)

        # ---- Previous period metrics for comparison ----
        period_length = (end_date - start_date).days + 1
        prev_end = start_date - timedelta(days=1)
        prev_start = prev_end - timedelta(days=period_length - 1)
        previous_agg = self._get_aggregation_metrics(org_id, prev_start, prev_end)

        # ---- Trend data ----
        trend = self._get_trend_data(org_id, start_date, end_date, period)

        # ---- Dimensional breakdown ----
        breakdown = None
        if dimension:
            breakdown = self._get_breakdown(org_id, start_date, end_date, dimension)

        # Build result
        result = {
            'period': {
                'type': period,
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
            },
            'metrics': {
                'total_revenue': _to_float(current_agg['gross_revenue']),
                'net_revenue': _to_float(current_agg['net_revenue']),
                'order_count': current_agg['order_count'] or 0,
                'avg_order_value': _to_float(current_agg['avg_order_value']),
                'item_count': current_agg['item_count'] or 0,
                'customer_count': current_agg['customer_count'] or 0,
            },
            'comparison': {
                'previous_period': {
                    'start_date': prev_start.isoformat(),
                    'end_date': prev_end.isoformat(),
                },
                'total_revenue': _to_float(previous_agg['gross_revenue']),
                'net_revenue': _to_float(previous_agg['net_revenue']),
                'order_count': previous_agg['order_count'] or 0,
                'avg_order_value': _to_float(previous_agg['avg_order_value']),
                'revenue_change_percent': _safe_percent_change(
                    _to_float(current_agg['gross_revenue']),
                    _to_float(previous_agg['gross_revenue']),
                ),
                'order_count_change_percent': _safe_percent_change(
                    float(current_agg['order_count'] or 0),
                    float(previous_agg['order_count'] or 0),
                ),
                'avg_order_value_change_percent': _safe_percent_change(
                    _to_float(current_agg['avg_order_value']),
                    _to_float(previous_agg['avg_order_value']),
                ),
            },
            'trend': trend,
        }

        if breakdown is not None:
            result['breakdown'] = {
                'dimension': dimension,
                'data': breakdown,
            }

        return result

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _get_aggregation_metrics(self, org_id: str, start: date, end: date) -> dict:
        """
        Fetch aggregated metrics from SalesAggregation for the given range.
        Falls back to Order table if no aggregated data exists.
        """
        agg_qs = SalesAggregation.objects.filter(
            organization_id=org_id,
            deleted_at__isnull=True,
            granularity=Granularity.DAILY,
            date__gte=start,
            date__lte=end,
        )

        result = agg_qs.aggregate(
            gross_revenue=Sum('gross_revenue'),
            net_revenue=Sum('net_revenue'),
            order_count=Sum('order_count'),
            item_count=Sum('item_count'),
            customer_count=Sum('customer_count'),
        )

        # If no aggregated data, fall back to Order table
        if result['order_count'] is None or result['order_count'] == 0:
            result = self._get_metrics_from_orders(org_id, start, end)
        else:
            # Compute average order value
            oc = result['order_count'] or 0
            gr = _to_float(result['gross_revenue'])
            result['avg_order_value'] = round(gr / oc, 2) if oc > 0 else 0

        return result

    def _get_metrics_from_orders(self, org_id: str, start: date, end: date) -> dict:
        """Fall-back: compute metrics directly from Order model."""
        qs = Order.objects.filter(
            organization_id=org_id,
            deleted_at__isnull=True,
            status__in=[
                OrderStatus.COMPLETED,
                OrderStatus.DELIVERED,
            ],
            created_at__date__gte=start,
            created_at__date__lte=end,
        )

        agg = qs.aggregate(
            gross_revenue=Sum('total_amount'),
            net_revenue=Sum(F('total_amount') - F('discount_amount') - F('refund_amount')),
            order_count=Count('id'),
            avg_order_value=Avg('total_amount'),
            customer_count=Count('customer', distinct=True),
            item_count=Sum('items__quantity'),
        )

        return {
            'gross_revenue': agg['gross_revenue'] or Decimal('0'),
            'net_revenue': agg['net_revenue'] or Decimal('0'),
            'order_count': agg['order_count'] or 0,
            'avg_order_value': agg['avg_order_value'] or Decimal('0'),
            'customer_count': agg['customer_count'] or 0,
            'item_count': agg['item_count'] or 0,
        }

    def _get_trend_data(
        self, org_id: str, start: date, end: date, period: str,
    ) -> List[dict]:
        """Return daily/weekly/monthly trend data for the given range."""
        # Try SalesAggregation first
        base_qs = SalesAggregation.objects.filter(
            organization_id=org_id,
            deleted_at__isnull=True,
            granularity=Granularity.DAILY,
            date__gte=start,
            date__lte=end,
        )

        if period == 'DAILY':
            rows = (
                base_qs
                .values('date')
                .annotate(
                    revenue=Sum('gross_revenue'),
                    net_revenue=Sum('net_revenue'),
                    orders=Sum('order_count'),
                )
                .order_by('date')
            )
        elif period == 'WEEKLY':
            rows = (
                base_qs
                .annotate(week=TruncWeek('date'))
                .values('week')
                .annotate(
                    revenue=Sum('gross_revenue'),
                    net_revenue=Sum('net_revenue'),
                    orders=Sum('order_count'),
                )
                .order_by('week')
            )
        else:  # MONTHLY
            rows = (
                base_qs
                .annotate(month=TruncMonth('date'))
                .values('month')
                .annotate(
                    revenue=Sum('gross_revenue'),
                    net_revenue=Sum('net_revenue'),
                    orders=Sum('order_count'),
                )
                .order_by('month')
            )

        trend = []
        for row in rows:
            label = row.get('date') or row.get('week') or row.get('month')
            if isinstance(label, (date, datetime)):
                label = label.isoformat() if isinstance(label, date) else label.date().isoformat()
            trend.append({
                'date': str(label),
                'revenue': _to_float(row['revenue']),
                'net_revenue': _to_float(row['net_revenue']),
                'orders': row['orders'] or 0,
            })

        # If no aggregation data, fall back to orders
        if not trend:
            trend = self._get_trend_from_orders(org_id, start, end, period)

        return trend

    def _get_trend_from_orders(
        self, org_id: str, start: date, end: date, period: str,
    ) -> List[dict]:
        """Fall-back trend from Order model."""
        qs = Order.objects.filter(
            organization_id=org_id,
            deleted_at__isnull=True,
            status__in=[OrderStatus.COMPLETED, OrderStatus.DELIVERED],
            created_at__date__gte=start,
            created_at__date__lte=end,
        )

        if period == 'DAILY':
            rows = (
                qs.annotate(dt=TruncDate('created_at'))
                .values('dt')
                .annotate(revenue=Sum('total_amount'), orders=Count('id'))
                .order_by('dt')
            )
            key = 'dt'
        elif period == 'WEEKLY':
            rows = (
                qs.annotate(dt=TruncWeek('created_at'))
                .values('dt')
                .annotate(revenue=Sum('total_amount'), orders=Count('id'))
                .order_by('dt')
            )
            key = 'dt'
        else:
            rows = (
                qs.annotate(dt=TruncMonth('created_at'))
                .values('dt')
                .annotate(revenue=Sum('total_amount'), orders=Count('id'))
                .order_by('dt')
            )
            key = 'dt'

        return [
            {
                'date': row[key].isoformat() if isinstance(row[key], (date, datetime)) else str(row[key]),
                'revenue': _to_float(row['revenue']),
                'net_revenue': _to_float(row['revenue']),
                'orders': row['orders'] or 0,
            }
            for row in rows
        ]

    def _get_breakdown(
        self, org_id: str, start: date, end: date, dimension: str,
    ) -> List[dict]:
        """Return breakdown by dimension (channel, payment, category)."""
        if dimension == 'channel':
            return self._breakdown_by_channel(org_id, start, end)
        elif dimension == 'payment':
            return self._breakdown_by_payment(org_id, start, end)
        elif dimension == 'category':
            return self._breakdown_by_category(org_id, start, end)
        return []

    def _breakdown_by_channel(self, org_id: str, start: date, end: date) -> List[dict]:
        """Revenue breakdown by order type / channel."""
        qs = Order.objects.filter(
            organization_id=org_id,
            deleted_at__isnull=True,
            status__in=[OrderStatus.COMPLETED, OrderStatus.DELIVERED],
            created_at__date__gte=start,
            created_at__date__lte=end,
        )

        rows = (
            qs.values('type')
            .annotate(
                revenue=Sum('total_amount'),
                count=Count('id'),
            )
            .order_by('-revenue')
        )

        total_rev = _to_float(qs.aggregate(t=Sum('total_amount'))['t'])
        result = []
        for row in rows:
            rev = _to_float(row['revenue'])
            result.append({
                'label': row['type'],
                'revenue': rev,
                'order_count': row['count'],
                'share_percent': round(rev / total_rev * 100, 2) if total_rev > 0 else 0,
            })
        return result

    def _breakdown_by_payment(self, org_id: str, start: date, end: date) -> List[dict]:
        """Revenue breakdown by payment method."""
        qs = Order.objects.filter(
            organization_id=org_id,
            deleted_at__isnull=True,
            status__in=[OrderStatus.COMPLETED, OrderStatus.DELIVERED],
            created_at__date__gte=start,
            created_at__date__lte=end,
        )

        rows = (
            qs.values('payment_method')
            .annotate(
                revenue=Sum('total_amount'),
                count=Count('id'),
            )
            .order_by('-revenue')
        )

        total_rev = _to_float(qs.aggregate(t=Sum('total_amount'))['t'])
        result = []
        for row in rows:
            rev = _to_float(row['revenue'])
            result.append({
                'label': row['payment_method'] or 'UNKNOWN',
                'revenue': rev,
                'order_count': row['count'],
                'share_percent': round(rev / total_rev * 100, 2) if total_rev > 0 else 0,
            })
        return result

    def _breakdown_by_category(self, org_id: str, start: date, end: date) -> List[dict]:
        """Revenue breakdown by menu category."""
        from apps.orders.models import OrderItem

        qs = OrderItem.objects.filter(
            order__organization_id=org_id,
            order__deleted_at__isnull=True,
            deleted_at__isnull=True,
            order__status__in=[OrderStatus.COMPLETED, OrderStatus.DELIVERED],
            order__created_at__date__gte=start,
            order__created_at__date__lte=end,
        )

        rows = (
            qs.values(
                category_name=F('product__category__name'),
                category_id=F('product__category__id'),
            )
            .annotate(
                revenue=Sum('total_price'),
                qty=Sum('quantity'),
            )
            .order_by('-revenue')
        )

        total_rev = _to_float(qs.aggregate(t=Sum('total_price'))['t'])
        result = []
        for row in rows:
            rev = _to_float(row['revenue'])
            result.append({
                'label': row['category_name'] or 'Uncategorized',
                'category_id': str(row['category_id']) if row['category_id'] else None,
                'revenue': rev,
                'quantity': row['qty'] or 0,
                'share_percent': round(rev / total_rev * 100, 2) if total_rev > 0 else 0,
            })
        return result
