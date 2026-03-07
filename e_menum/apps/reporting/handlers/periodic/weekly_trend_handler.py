"""
Weekly Trend Report Handler (RPT-PER-005).

Generates a weekly summary with daily breakdown, week totals,
week-over-week comparison, and trend indicators.

Critical Rules:
    - ALL queries MUST filter by organization_id (multi-tenancy)
    - ALL queries on soft-delete models MUST filter deleted_at__isnull=True
    - Return values must be JSON-serializable (Decimal -> float)
"""

import logging
from datetime import date, datetime, timedelta
from typing import List, Optional

from django.db.models import Avg, Count, F, Sum

from apps.analytics.choices import Granularity
from apps.analytics.models import SalesAggregation
from apps.customers.models import Customer
from apps.orders.choices import OrderStatus
from apps.orders.models import Order, OrderItem
from apps.reporting.services.report_engine import BaseReportHandler, register_handler

logger = logging.getLogger(__name__)


def _to_float(val) -> float:
    if val is None:
        return 0.0
    return float(val)


def _parse_date(val) -> Optional[date]:
    if val is None:
        return None
    if isinstance(val, date):
        return val
    if isinstance(val, datetime):
        return val.date()
    return datetime.strptime(str(val), '%Y-%m-%d').date()


def _safe_percent_change(current: float, previous: float) -> Optional[float]:
    if previous == 0:
        return 0.0 if current == 0 else None
    return round(((current - previous) / previous) * 100, 2)


@register_handler('RPT-PER-005')
class WeeklyTrendHandler(BaseReportHandler):
    """
    Weekly trend report handler.

    Returns daily breakdown for a 7-day week, week totals, and
    comparison with the previous week.

    Parameters:
        week_start_date: str - Monday of the week in YYYY-MM-DD
                               (defaults to last week's Monday)
    """

    feature_key = 'RPT-PER-005'

    def get_required_permissions(self) -> List[str]:
        return ['reporting.view']

    def get_default_parameters(self) -> dict:
        today = date.today()
        # Find last week's Monday
        days_since_monday = today.weekday()
        this_monday = today - timedelta(days=days_since_monday)
        last_monday = this_monday - timedelta(days=7)
        return {
            'week_start_date': last_monday.isoformat(),
        }

    def validate_parameters(self, parameters: dict) -> dict:
        merged = {**self.get_default_parameters(), **parameters}
        merged['week_start_date'] = _parse_date(merged['week_start_date'])
        return merged

    def generate(self, org_id: str, parameters: dict) -> dict:
        week_start = parameters['week_start_date']
        week_end = week_start + timedelta(days=6)

        prev_week_start = week_start - timedelta(days=7)
        prev_week_end = prev_week_start + timedelta(days=6)

        # ---- Daily breakdown for the week ----
        daily_breakdown = self._get_daily_breakdown(org_id, week_start, week_end)

        # ---- Week totals ----
        week_totals = self._get_week_totals(org_id, week_start, week_end)

        # ---- Previous week totals ----
        prev_week_totals = self._get_week_totals(org_id, prev_week_start, prev_week_end)

        # ---- Top sellers for the week ----
        top_sellers = self._get_top_sellers(org_id, week_start, week_end, limit=10)

        # ---- Trends ----
        trends = self._calculate_trends(daily_breakdown)

        return {
            'week': {
                'start_date': week_start.isoformat(),
                'end_date': week_end.isoformat(),
                'week_number': week_start.isocalendar()[1],
                'year': week_start.year,
            },
            'daily_breakdown': daily_breakdown,
            'week_totals': week_totals,
            'comparison': {
                'previous_week': {
                    'start_date': prev_week_start.isoformat(),
                    'end_date': prev_week_end.isoformat(),
                },
                'revenue_change_percent': _safe_percent_change(
                    week_totals['total_revenue'], prev_week_totals['total_revenue'],
                ),
                'order_count_change_percent': _safe_percent_change(
                    float(week_totals['order_count']),
                    float(prev_week_totals['order_count']),
                ),
                'avg_order_value_change_percent': _safe_percent_change(
                    week_totals['avg_order_value'],
                    prev_week_totals['avg_order_value'],
                ),
                'new_customers_change_percent': _safe_percent_change(
                    float(week_totals['new_customers']),
                    float(prev_week_totals['new_customers']),
                ),
                'previous_week_totals': prev_week_totals,
            },
            'top_sellers': top_sellers,
            'trends': trends,
        }

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _get_daily_breakdown(
        self, org_id: str, start: date, end: date,
    ) -> List[dict]:
        """Get per-day metrics for the week."""
        # Try SalesAggregation first
        agg_rows = list(
            SalesAggregation.objects.filter(
                organization_id=org_id,
                deleted_at__isnull=True,
                granularity=Granularity.DAILY,
                date__gte=start,
                date__lte=end,
            )
            .values('date')
            .annotate(
                revenue=Sum('gross_revenue'),
                net_revenue=Sum('net_revenue'),
                orders=Sum('order_count'),
                items=Sum('item_count'),
                customers=Sum('customer_count'),
            )
            .order_by('date')
        )

        # Build a lookup for quick access
        agg_lookup = {row['date']: row for row in agg_rows}

        breakdown = []
        current = start
        while current <= end:
            if current in agg_lookup:
                row = agg_lookup[current]
                orders_count = row['orders'] or 0
                rev = _to_float(row['revenue'])
                breakdown.append({
                    'date': current.isoformat(),
                    'day_of_week': current.strftime('%A'),
                    'revenue': rev,
                    'net_revenue': _to_float(row['net_revenue']),
                    'order_count': orders_count,
                    'item_count': row['items'] or 0,
                    'customer_count': row['customers'] or 0,
                    'avg_order_value': round(
                        rev / orders_count, 2,
                    ) if orders_count > 0 else 0,
                })
            else:
                # Fallback to Order table for this day
                day_data = self._get_day_from_orders(org_id, current)
                breakdown.append(day_data)

            current += timedelta(days=1)

        return breakdown

    def _get_day_from_orders(self, org_id: str, d: date) -> dict:
        """Get metrics for a single day from Order table."""
        qs = Order.objects.filter(
            organization_id=org_id,
            deleted_at__isnull=True,
            created_at__date=d,
            status__in=[OrderStatus.COMPLETED, OrderStatus.DELIVERED],
        )

        agg = qs.aggregate(
            revenue=Sum('total_amount'),
            orders=Count('id'),
            avg_ov=Avg('total_amount'),
            customers=Count('customer', distinct=True),
        )

        item_count = OrderItem.objects.filter(
            order__organization_id=org_id,
            order__deleted_at__isnull=True,
            deleted_at__isnull=True,
            order__created_at__date=d,
            order__status__in=[OrderStatus.COMPLETED, OrderStatus.DELIVERED],
        ).aggregate(t=Sum('quantity'))['t'] or 0

        rev = _to_float(agg['revenue'])
        oc = agg['orders'] or 0

        return {
            'date': d.isoformat(),
            'day_of_week': d.strftime('%A'),
            'revenue': rev,
            'net_revenue': rev,  # Approximation when no agg data
            'order_count': oc,
            'item_count': item_count,
            'customer_count': agg['customers'] or 0,
            'avg_order_value': round(rev / oc, 2) if oc > 0 else 0,
        }

    def _get_week_totals(self, org_id: str, start: date, end: date) -> dict:
        """Get aggregate totals for a week."""
        qs = Order.objects.filter(
            organization_id=org_id,
            deleted_at__isnull=True,
            created_at__date__gte=start,
            created_at__date__lte=end,
            status__in=[OrderStatus.COMPLETED, OrderStatus.DELIVERED],
        )

        agg = qs.aggregate(
            total_revenue=Sum('total_amount'),
            order_count=Count('id'),
            avg_order_value=Avg('total_amount'),
            total_discount=Sum('discount_amount'),
            total_tax=Sum('tax_amount'),
            total_customers=Count('customer', distinct=True),
        )

        new_customers = Customer.objects.filter(
            organization_id=org_id,
            deleted_at__isnull=True,
            created_at__date__gte=start,
            created_at__date__lte=end,
        ).count()

        cancelled = Order.objects.filter(
            organization_id=org_id,
            deleted_at__isnull=True,
            created_at__date__gte=start,
            created_at__date__lte=end,
            status=OrderStatus.CANCELLED,
        ).count()

        return {
            'total_revenue': _to_float(agg['total_revenue']),
            'order_count': agg['order_count'] or 0,
            'avg_order_value': _to_float(agg['avg_order_value']),
            'total_discount': _to_float(agg['total_discount']),
            'total_tax': _to_float(agg['total_tax']),
            'unique_customers': agg['total_customers'] or 0,
            'new_customers': new_customers,
            'cancelled_orders': cancelled,
        }

    def _get_top_sellers(
        self, org_id: str, start: date, end: date, limit: int = 10,
    ) -> List[dict]:
        """Top selling products for the week."""
        rows = (
            OrderItem.objects.filter(
                order__organization_id=org_id,
                order__deleted_at__isnull=True,
                deleted_at__isnull=True,
                order__status__in=[OrderStatus.COMPLETED, OrderStatus.DELIVERED],
                order__created_at__date__gte=start,
                order__created_at__date__lte=end,
            )
            .values(
                product_name=F('product__name'),
                product_id_val=F('product__id'),
            )
            .annotate(
                qty_sold=Sum('quantity'),
                revenue=Sum('total_price'),
            )
            .order_by('-revenue')[:limit]
        )

        return [
            {
                'product_id': str(row['product_id_val']) if row['product_id_val'] else None,
                'product_name': row['product_name'] or 'Unknown',
                'qty_sold': row['qty_sold'] or 0,
                'revenue': _to_float(row['revenue']),
            }
            for row in rows
        ]

    def _calculate_trends(self, daily_breakdown: List[dict]) -> dict:
        """Determine trend directions from daily data."""
        if len(daily_breakdown) < 2:
            return {
                'revenue_trend': 'stable',
                'order_trend': 'stable',
                'best_day': None,
                'worst_day': None,
            }

        revenues = [d['revenue'] for d in daily_breakdown]
        orders = [d['order_count'] for d in daily_breakdown]

        # Simple trend: compare first half to second half
        mid = len(revenues) // 2
        first_half_rev = sum(revenues[:mid]) if mid > 0 else 0
        second_half_rev = sum(revenues[mid:])
        first_half_ord = sum(orders[:mid]) if mid > 0 else 0
        second_half_ord = sum(orders[mid:])

        def trend(first, second):
            if second > first * 1.1:
                return 'up'
            elif second < first * 0.9:
                return 'down'
            return 'stable'

        # Best and worst days
        best = max(daily_breakdown, key=lambda d: d['revenue'])
        worst = min(daily_breakdown, key=lambda d: d['revenue'])

        return {
            'revenue_trend': trend(first_half_rev, second_half_rev),
            'order_trend': trend(first_half_ord, second_half_ord),
            'best_day': {
                'date': best['date'],
                'day_of_week': best['day_of_week'],
                'revenue': best['revenue'],
                'order_count': best['order_count'],
            },
            'worst_day': {
                'date': worst['date'],
                'day_of_week': worst['day_of_week'],
                'revenue': worst['revenue'],
                'order_count': worst['order_count'],
            },
        }
