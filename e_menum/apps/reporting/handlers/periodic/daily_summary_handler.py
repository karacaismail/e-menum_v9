"""
Daily Summary Report Handler (RPT-PER-001).

Generates a comprehensive daily summary including revenue, orders,
customers, top sellers, and comparison with the previous day.

Critical Rules:
    - ALL queries MUST filter by organization_id (multi-tenancy)
    - ALL queries on soft-delete models MUST filter deleted_at__isnull=True
    - Return values must be JSON-serializable (Decimal -> float)
"""

import logging
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import List, Optional

from django.db.models import Avg, Count, F, Q, Sum
from django.db.models.functions import ExtractHour

from apps.analytics.choices import Granularity
from apps.analytics.models import SalesAggregation
from apps.customers.models import Customer
from apps.orders.choices import OrderStatus
from apps.orders.models import Order, OrderItem, QRScan
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


@register_handler('RPT-PER-001')
class DailySummaryHandler(BaseReportHandler):
    """
    Daily summary report handler.

    Returns a comprehensive overview of a single day's business
    performance across revenue, orders, customers, and top sellers.

    Parameters:
        date: str - The date to report on in YYYY-MM-DD (defaults to yesterday)
    """

    feature_key = 'RPT-PER-001'

    def get_required_permissions(self) -> List[str]:
        return ['reporting.view']

    def get_default_parameters(self) -> dict:
        yesterday = date.today() - timedelta(days=1)
        return {
            'date': yesterday.isoformat(),
        }

    def validate_parameters(self, parameters: dict) -> dict:
        merged = {**self.get_default_parameters(), **parameters}
        merged['date'] = _parse_date(merged['date'])
        return merged

    def generate(self, org_id: str, parameters: dict) -> dict:
        report_date = parameters['date']
        prev_date = report_date - timedelta(days=1)

        # ---- Revenue metrics ----
        revenue = self._get_revenue(org_id, report_date)
        prev_revenue = self._get_revenue(org_id, prev_date)

        # ---- Order metrics ----
        orders = self._get_order_metrics(org_id, report_date)
        prev_orders = self._get_order_metrics(org_id, prev_date)

        # ---- Customer metrics ----
        customers = self._get_customer_metrics(org_id, report_date)
        prev_customers = self._get_customer_metrics(org_id, prev_date)

        # ---- Top sellers ----
        top_sellers = self._get_top_sellers(org_id, report_date, limit=5)

        # ---- Hourly distribution ----
        hourly_revenue = self._get_hourly_distribution(org_id, report_date)

        # ---- QR scans ----
        qr_scans = QRScan.objects.filter(
            organization_id=org_id,
            scanned_at__date=report_date,
        ).count()
        prev_qr_scans = QRScan.objects.filter(
            organization_id=org_id,
            scanned_at__date=prev_date,
        ).count()

        # ---- Build highlights ----
        highlights = self._build_highlights(
            revenue, prev_revenue, orders, prev_orders, top_sellers,
        )

        return {
            'date': report_date.isoformat(),
            'day_of_week': report_date.strftime('%A'),
            'revenue': {
                'total': revenue['total'],
                'net': revenue['net'],
                'discount': revenue['discount'],
                'tax': revenue['tax'],
                'refund': revenue['refund'],
                'comparison': {
                    'previous_date': prev_date.isoformat(),
                    'total': prev_revenue['total'],
                    'change_percent': _safe_percent_change(
                        revenue['total'], prev_revenue['total'],
                    ),
                },
            },
            'orders': {
                'total': orders['total'],
                'completed': orders['completed'],
                'cancelled': orders['cancelled'],
                'avg_order_value': orders['avg_order_value'],
                'comparison': {
                    'previous_date': prev_date.isoformat(),
                    'total': prev_orders['total'],
                    'change_percent': _safe_percent_change(
                        float(orders['total']), float(prev_orders['total']),
                    ),
                },
            },
            'customers': {
                'new_customers': customers['new'],
                'returning_customers': customers['returning'],
                'total_unique': customers['unique'],
                'comparison': {
                    'previous_date': prev_date.isoformat(),
                    'new_customers': prev_customers['new'],
                    'new_customers_change_percent': _safe_percent_change(
                        float(customers['new']), float(prev_customers['new']),
                    ),
                },
            },
            'qr_scans': {
                'total': qr_scans,
                'comparison': {
                    'previous_date': prev_date.isoformat(),
                    'total': prev_qr_scans,
                    'change_percent': _safe_percent_change(
                        float(qr_scans), float(prev_qr_scans),
                    ),
                },
            },
            'top_sellers': top_sellers,
            'hourly_distribution': hourly_revenue,
            'highlights': highlights,
        }

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _get_revenue(self, org_id: str, d: date) -> dict:
        """Get revenue metrics for a single day."""
        # Try SalesAggregation first
        agg = SalesAggregation.objects.filter(
            organization_id=org_id,
            deleted_at__isnull=True,
            date=d,
            granularity=Granularity.DAILY,
        ).aggregate(
            gross=Sum('gross_revenue'),
            net=Sum('net_revenue'),
        )

        if agg['gross'] is not None:
            # Get discount/tax/refund from Order table
            order_agg = Order.objects.filter(
                organization_id=org_id,
                deleted_at__isnull=True,
                created_at__date=d,
                status__in=[OrderStatus.COMPLETED, OrderStatus.DELIVERED],
            ).aggregate(
                discount=Sum('discount_amount'),
                tax=Sum('tax_amount'),
                refund=Sum('refund_amount'),
            )
            return {
                'total': _to_float(agg['gross']),
                'net': _to_float(agg['net']),
                'discount': _to_float(order_agg['discount']),
                'tax': _to_float(order_agg['tax']),
                'refund': _to_float(order_agg['refund']),
            }

        # Fallback to Order table
        qs = Order.objects.filter(
            organization_id=org_id,
            deleted_at__isnull=True,
            created_at__date=d,
            status__in=[OrderStatus.COMPLETED, OrderStatus.DELIVERED],
        )
        result = qs.aggregate(
            total=Sum('total_amount'),
            discount=Sum('discount_amount'),
            tax=Sum('tax_amount'),
            refund=Sum('refund_amount'),
        )
        total = _to_float(result['total'])
        discount = _to_float(result['discount'])
        refund = _to_float(result['refund'])
        return {
            'total': total,
            'net': total - discount - refund,
            'discount': discount,
            'tax': _to_float(result['tax']),
            'refund': refund,
        }

    def _get_order_metrics(self, org_id: str, d: date) -> dict:
        """Get order metrics for a single day."""
        qs = Order.objects.filter(
            organization_id=org_id,
            deleted_at__isnull=True,
            created_at__date=d,
        )
        total = qs.count()
        completed = qs.filter(
            status__in=[OrderStatus.COMPLETED, OrderStatus.DELIVERED],
        ).count()
        cancelled = qs.filter(status=OrderStatus.CANCELLED).count()

        aov = qs.filter(
            status__in=[OrderStatus.COMPLETED, OrderStatus.DELIVERED],
        ).aggregate(avg=Avg('total_amount'))['avg']

        return {
            'total': total,
            'completed': completed,
            'cancelled': cancelled,
            'avg_order_value': _to_float(aov),
        }

    def _get_customer_metrics(self, org_id: str, d: date) -> dict:
        """Get customer metrics for a single day."""
        new_count = Customer.objects.filter(
            organization_id=org_id,
            deleted_at__isnull=True,
            created_at__date=d,
        ).count()

        unique_customers = Order.objects.filter(
            organization_id=org_id,
            deleted_at__isnull=True,
            created_at__date=d,
            customer__isnull=False,
        ).values('customer').distinct().count()

        # Returning: customers with >1 total orders who ordered today
        from django.db.models import Subquery, OuterRef
        returning = (
            Order.objects.filter(
                organization_id=org_id,
                deleted_at__isnull=True,
                created_at__date=d,
                customer__isnull=False,
                customer__total_orders__gt=1,
            )
            .values('customer')
            .distinct()
            .count()
        )

        return {
            'new': new_count,
            'returning': returning,
            'unique': unique_customers,
        }

    def _get_top_sellers(self, org_id: str, d: date, limit: int = 5) -> List[dict]:
        """Get top selling products for a single day."""
        rows = (
            OrderItem.objects.filter(
                order__organization_id=org_id,
                order__deleted_at__isnull=True,
                deleted_at__isnull=True,
                order__status__in=[OrderStatus.COMPLETED, OrderStatus.DELIVERED],
                order__created_at__date=d,
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

    def _get_hourly_distribution(self, org_id: str, d: date) -> List[dict]:
        """Get hourly order/revenue distribution for a single day."""
        # Try SalesAggregation hourly data first
        hourly_agg = list(
            SalesAggregation.objects.filter(
                organization_id=org_id,
                deleted_at__isnull=True,
                date=d,
                granularity=Granularity.HOURLY,
            )
            .values('hour')
            .annotate(
                revenue=Sum('gross_revenue'),
                orders=Sum('order_count'),
            )
            .order_by('hour')
        )

        if hourly_agg:
            return [
                {
                    'hour': row['hour'],
                    'revenue': _to_float(row['revenue']),
                    'orders': row['orders'] or 0,
                }
                for row in hourly_agg
            ]

        # Fallback to Order table
        rows = list(
            Order.objects.filter(
                organization_id=org_id,
                deleted_at__isnull=True,
                created_at__date=d,
            )
            .annotate(hour=ExtractHour('created_at'))
            .values('hour')
            .annotate(
                revenue=Sum('total_amount'),
                orders=Count('id'),
            )
            .order_by('hour')
        )

        return [
            {
                'hour': row['hour'],
                'revenue': _to_float(row['revenue']),
                'orders': row['orders'] or 0,
            }
            for row in rows
        ]

    def _build_highlights(
        self,
        revenue: dict,
        prev_revenue: dict,
        orders: dict,
        prev_orders: dict,
        top_sellers: List[dict],
    ) -> List[str]:
        """Build list of highlight strings for the daily summary."""
        highlights = []

        rev_change = _safe_percent_change(revenue['total'], prev_revenue['total'])
        if rev_change is not None and rev_change > 0:
            highlights.append(
                f"Revenue increased by {rev_change}% compared to previous day."
            )
        elif rev_change is not None and rev_change < 0:
            highlights.append(
                f"Revenue decreased by {abs(rev_change)}% compared to previous day."
            )

        ord_change = _safe_percent_change(
            float(orders['total']), float(prev_orders['total']),
        )
        if ord_change is not None and ord_change > 10:
            highlights.append(
                f"Order volume up {ord_change}% vs yesterday."
            )

        if orders['cancelled'] > 0:
            cancel_rate = round(
                orders['cancelled'] / max(orders['total'], 1) * 100, 1,
            )
            if cancel_rate > 10:
                highlights.append(
                    f"High cancellation rate: {cancel_rate}% of orders were cancelled."
                )

        if top_sellers:
            top = top_sellers[0]
            highlights.append(
                f"Top seller: {top['product_name']} "
                f"({top['qty_sold']} sold, {top['revenue']:.0f} TRY)."
            )

        if not highlights:
            highlights.append("No significant changes compared to previous day.")

        return highlights
