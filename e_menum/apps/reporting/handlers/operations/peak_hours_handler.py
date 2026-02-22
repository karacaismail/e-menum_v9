"""
Peak Hours Analysis Report Handler (RPT-OPR-001).

Generates peak hours analysis reports showing order volume, revenue,
and average order value by hour of day and day of week. Helps
organizations optimize staffing, promotions, and operational planning.

Critical Rules:
    - ALL queries MUST filter by organization_id (multi-tenancy)
    - ALL queries on soft-delete models MUST filter deleted_at__isnull=True
    - Return values must be JSON-serializable (Decimal -> float)
"""

import logging
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional

from django.db.models import Avg, Count, F, Q, Sum
from django.db.models.functions import ExtractHour, ExtractWeekDay

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


# Map Django weekday (1=Sunday in some DBs) to ISO weekday names
WEEKDAY_NAMES = {
    1: 'Sunday',
    2: 'Monday',
    3: 'Tuesday',
    4: 'Wednesday',
    5: 'Thursday',
    6: 'Friday',
    7: 'Saturday',
}


@register_handler('RPT-OPR-001')
class PeakHoursHandler(BaseReportHandler):
    """
    Peak hours analysis report handler.

    Analyzes order patterns by hour of day and day of week to identify
    peak periods. Includes heatmap data (hour x weekday), top peak
    hours, and busiest days.

    Parameters:
        start_date: str - Start date in YYYY-MM-DD format
        end_date: str - End date in YYYY-MM-DD format
        branch_id: str - Optional branch UUID filter
        order_type: str - Optional order type filter (DINE_IN, TAKEAWAY, etc.)
    """

    feature_key = 'RPT-OPR-001'

    def get_required_permissions(self) -> List[str]:
        return ['reporting.view', 'orders.view']

    def get_default_parameters(self) -> dict:
        today = date.today()
        return {
            'start_date': (today - timedelta(days=30)).isoformat(),
            'end_date': today.isoformat(),
            'branch_id': None,
            'order_type': None,
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
        from apps.orders.choices import OrderStatus
        from apps.orders.models import Order

        start_date = parameters['start_date']
        end_date = parameters['end_date']
        branch_id = parameters.get('branch_id')
        order_type = parameters.get('order_type')

        # ---- Base queryset ----
        qs = Order.objects.filter(
            organization_id=org_id,
            deleted_at__isnull=True,
            status__in=[OrderStatus.COMPLETED, OrderStatus.DELIVERED],
            created_at__date__gte=start_date,
            created_at__date__lte=end_date,
        )

        if branch_id:
            qs = qs.filter(branch_id=branch_id)
        if order_type:
            qs = qs.filter(type=order_type)

        # ---- Hourly distribution ----
        hourly = list(
            qs.annotate(hour=ExtractHour('created_at'))
            .values('hour')
            .annotate(
                order_count=Count('id'),
                revenue=Sum('total_amount'),
                avg_order_value=Avg('total_amount'),
            )
            .order_by('hour')
        )

        hourly_data = []
        total_orders = sum(r['order_count'] for r in hourly)
        for row in hourly:
            hourly_data.append({
                'hour': row['hour'],
                'hour_label': f"{row['hour']:02d}:00",
                'order_count': row['order_count'],
                'revenue': _to_float(row['revenue']),
                'avg_order_value': _to_float(row['avg_order_value']),
                'share_pct': (
                    round(row['order_count'] / total_orders * 100, 2)
                    if total_orders > 0 else 0.0
                ),
            })

        # ---- Day of week distribution ----
        dow = list(
            qs.annotate(weekday=ExtractWeekDay('created_at'))
            .values('weekday')
            .annotate(
                order_count=Count('id'),
                revenue=Sum('total_amount'),
                avg_order_value=Avg('total_amount'),
            )
            .order_by('weekday')
        )

        dow_data = []
        for row in dow:
            dow_data.append({
                'weekday': row['weekday'],
                'weekday_name': WEEKDAY_NAMES.get(row['weekday'], f"Day {row['weekday']}"),
                'order_count': row['order_count'],
                'revenue': _to_float(row['revenue']),
                'avg_order_value': _to_float(row['avg_order_value']),
                'share_pct': (
                    round(row['order_count'] / total_orders * 100, 2)
                    if total_orders > 0 else 0.0
                ),
            })

        # ---- Heatmap data (hour x weekday) ----
        heatmap_rows = list(
            qs.annotate(
                hour=ExtractHour('created_at'),
                weekday=ExtractWeekDay('created_at'),
            )
            .values('hour', 'weekday')
            .annotate(
                order_count=Count('id'),
                revenue=Sum('total_amount'),
            )
            .order_by('weekday', 'hour')
        )

        heatmap = []
        for row in heatmap_rows:
            heatmap.append({
                'hour': row['hour'],
                'weekday': row['weekday'],
                'weekday_name': WEEKDAY_NAMES.get(row['weekday'], f"Day {row['weekday']}"),
                'order_count': row['order_count'],
                'revenue': _to_float(row['revenue']),
            })

        # ---- Identify top peak hours ----
        peak_hours = sorted(hourly_data, key=lambda x: x['order_count'], reverse=True)[:5]

        # ---- Identify top peak days ----
        peak_days = sorted(dow_data, key=lambda x: x['order_count'], reverse=True)[:3]

        # ---- Quiet / slow periods ----
        quiet_hours = sorted(hourly_data, key=lambda x: x['order_count'])[:3]

        return {
            'period': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
            },
            'total_orders': total_orders,
            'hourly_distribution': hourly_data,
            'day_of_week_distribution': dow_data,
            'heatmap': heatmap,
            'insights': {
                'peak_hours': peak_hours,
                'peak_days': peak_days,
                'quiet_hours': quiet_hours,
            },
        }
