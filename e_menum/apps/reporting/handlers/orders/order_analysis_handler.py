"""
Order Analysis Report Handler (RPT-ORD-001).

Generates comprehensive order analysis including total orders,
completion rates, average order value, distribution by status,
channel, and hourly patterns.

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
from django.db.models.functions import ExtractHour, TruncDate

from apps.orders.choices import OrderStatus, OrderType
from apps.orders.models import Order
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


@register_handler('RPT-ORD-001')
class OrderAnalysisHandler(BaseReportHandler):
    """
    Order analysis report handler.

    Returns total orders, completed/cancelled counts, average order value,
    orders by status, orders by channel (order type), and orders by hour
    of day distribution.

    Parameters:
        period: str - DAILY, WEEKLY, or MONTHLY (informational label)
        start_date: str - Start date in YYYY-MM-DD format
        end_date: str - End date in YYYY-MM-DD format
    """

    feature_key = 'RPT-ORD-001'

    def get_required_permissions(self) -> List[str]:
        return ['reporting.view', 'orders.view']

    def get_default_parameters(self) -> dict:
        today = date.today()
        return {
            'period': 'DAILY',
            'start_date': (today - timedelta(days=30)).isoformat(),
            'end_date': today.isoformat(),
        }

    def validate_parameters(self, parameters: dict) -> dict:
        merged = {**self.get_default_parameters(), **parameters}
        merged['start_date'] = _parse_date(merged['start_date'])
        merged['end_date'] = _parse_date(merged['end_date'])

        if merged['start_date'] > merged['end_date']:
            from shared.utils.exceptions import AppException
            raise AppException(
                code='INVALID_DATE_RANGE',
                message='start_date must be before or equal to end_date',
                status_code=400,
            )

        return merged

    def generate(self, org_id: str, parameters: dict) -> dict:
        start_date = parameters['start_date']
        end_date = parameters['end_date']

        # Base queryset (all orders in the period, regardless of status)
        base_qs = Order.objects.filter(
            organization_id=org_id,
            deleted_at__isnull=True,
            created_at__date__gte=start_date,
            created_at__date__lte=end_date,
        )

        # ---- Aggregate metrics ----
        total_orders = base_qs.count()

        completed_qs = base_qs.filter(
            status__in=[OrderStatus.COMPLETED, OrderStatus.DELIVERED],
        )
        completed_orders = completed_qs.count()

        cancelled_orders = base_qs.filter(status=OrderStatus.CANCELLED).count()

        financial = completed_qs.aggregate(
            total_revenue=Sum('total_amount'),
            avg_order_value=Avg('total_amount'),
            total_discount=Sum('discount_amount'),
            total_tax=Sum('tax_amount'),
            total_refund=Sum('refund_amount'),
        )

        # ---- Previous period comparison ----
        period_length = (end_date - start_date).days + 1
        prev_end = start_date - timedelta(days=1)
        prev_start = prev_end - timedelta(days=period_length - 1)

        prev_qs = Order.objects.filter(
            organization_id=org_id,
            deleted_at__isnull=True,
            created_at__date__gte=prev_start,
            created_at__date__lte=prev_end,
        )
        prev_total = prev_qs.count()
        prev_completed = prev_qs.filter(
            status__in=[OrderStatus.COMPLETED, OrderStatus.DELIVERED],
        ).count()
        prev_aov = _to_float(
            prev_qs.filter(
                status__in=[OrderStatus.COMPLETED, OrderStatus.DELIVERED],
            ).aggregate(a=Avg('total_amount'))['a']
        )

        # ---- Orders by status ----
        orders_by_status = list(
            base_qs
            .values('status')
            .annotate(count=Count('id'))
            .order_by('status')
        )

        # ---- Orders by channel (order type) ----
        orders_by_channel = list(
            base_qs
            .values('type')
            .annotate(
                count=Count('id'),
                revenue=Sum('total_amount'),
            )
            .order_by('-count')
        )

        # ---- Orders by hour of day ----
        orders_by_hour = list(
            base_qs
            .annotate(hour=ExtractHour('created_at'))
            .values('hour')
            .annotate(count=Count('id'), revenue=Sum('total_amount'))
            .order_by('hour')
        )

        # ---- Daily trend ----
        daily_trend = list(
            base_qs
            .annotate(dt=TruncDate('created_at'))
            .values('dt')
            .annotate(
                count=Count('id'),
                revenue=Sum('total_amount'),
                completed=Count('id', filter=Q(
                    status__in=[OrderStatus.COMPLETED, OrderStatus.DELIVERED],
                )),
            )
            .order_by('dt')
        )

        # Build completion and cancellation rates
        completion_rate = round(
            (completed_orders / total_orders * 100) if total_orders > 0 else 0, 2,
        )
        cancellation_rate = round(
            (cancelled_orders / total_orders * 100) if total_orders > 0 else 0, 2,
        )

        return {
            'period': {
                'type': parameters['period'],
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
            },
            'metrics': {
                'total_orders': total_orders,
                'completed_orders': completed_orders,
                'cancelled_orders': cancelled_orders,
                'pending_orders': base_qs.filter(status=OrderStatus.PENDING).count(),
                'completion_rate': completion_rate,
                'cancellation_rate': cancellation_rate,
                'total_revenue': _to_float(financial['total_revenue']),
                'avg_order_value': _to_float(financial['avg_order_value']),
                'total_discount': _to_float(financial['total_discount']),
                'total_tax': _to_float(financial['total_tax']),
                'total_refund': _to_float(financial['total_refund']),
            },
            'comparison': {
                'previous_period': {
                    'start_date': prev_start.isoformat(),
                    'end_date': prev_end.isoformat(),
                },
                'total_orders': prev_total,
                'completed_orders': prev_completed,
                'avg_order_value': prev_aov,
                'total_orders_change_percent': _safe_percent_change(
                    float(total_orders), float(prev_total),
                ),
                'completed_orders_change_percent': _safe_percent_change(
                    float(completed_orders), float(prev_completed),
                ),
            },
            'orders_by_status': [
                {'status': row['status'], 'count': row['count']}
                for row in orders_by_status
            ],
            'orders_by_channel': [
                {
                    'channel': row['type'],
                    'count': row['count'],
                    'revenue': _to_float(row['revenue']),
                    'share_percent': round(
                        (row['count'] / total_orders * 100) if total_orders > 0 else 0, 2,
                    ),
                }
                for row in orders_by_channel
            ],
            'orders_by_hour': [
                {
                    'hour': row['hour'],
                    'count': row['count'],
                    'revenue': _to_float(row['revenue']),
                }
                for row in orders_by_hour
            ],
            'daily_trend': [
                {
                    'date': row['dt'].isoformat() if row['dt'] else None,
                    'count': row['count'],
                    'revenue': _to_float(row['revenue']),
                    'completed': row['completed'],
                }
                for row in daily_trend
            ],
        }
