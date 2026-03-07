"""
Staff Performance Report Handler (RPT-STF-001).

Generates staff performance reports showing individual and comparative
metrics including orders handled, revenue generated, average order
value, service times, ratings, and tips. Queries StaffMetric and
StaffSchedule models.

Critical Rules:
    - ALL queries MUST filter by organization_id (multi-tenancy)
    - ALL queries on soft-delete models MUST filter deleted_at__isnull=True
    - Return values must be JSON-serializable (Decimal -> float)
"""

import logging
from datetime import date, datetime, timedelta
from typing import List, Optional

from django.db.models import Avg, Count, F, Q, Sum

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


@register_handler('RPT-STF-001')
class StaffPerformanceHandler(BaseReportHandler):
    """
    Staff performance report handler.

    Provides per-staff KPIs, ranking, attendance stats, and
    aggregated team metrics for the specified period.

    Parameters:
        start_date: str - Start date in YYYY-MM-DD format
        end_date: str - End date in YYYY-MM-DD format
        user_id: str - Optional specific user UUID to report on
        sort_by: str - Sorting metric: revenue, orders, rating, tips (default: revenue)
    """

    feature_key = 'RPT-STF-001'

    def get_required_permissions(self) -> List[str]:
        return ['reporting.view', 'staff.view']

    def get_default_parameters(self) -> dict:
        today = date.today()
        return {
            'start_date': (today - timedelta(days=30)).isoformat(),
            'end_date': today.isoformat(),
            'user_id': None,
            'sort_by': 'revenue',
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

        valid_sorts = ['revenue', 'orders', 'rating', 'tips']
        if merged['sort_by'] not in valid_sorts:
            from shared.utils.exceptions import AppException
            raise AppException(
                code='INVALID_SORT_BY',
                message=f"sort_by must be one of {valid_sorts}",
                status_code=400,
            )

        return merged

    def generate(self, org_id: str, parameters: dict) -> dict:
        from apps.core.models import StaffMetric, StaffSchedule

        start_date = parameters['start_date']
        end_date = parameters['end_date']
        user_id = parameters.get('user_id')
        sort_by = parameters.get('sort_by', 'revenue')

        # ---- Staff metrics aggregation ----
        metric_qs = StaffMetric.objects.filter(
            organization_id=org_id,
            deleted_at__isnull=True,
            date__gte=start_date,
            date__lte=end_date,
        )

        if user_id:
            metric_qs = metric_qs.filter(user_id=user_id)

        # Per-staff aggregation
        staff_data = list(
            metric_qs
            .values(
                'user_id',
                staff_email=F('user__email'),
                staff_name=F('user__first_name'),
            )
            .annotate(
                total_orders=Sum('orders_handled'),
                total_revenue=Sum('revenue_generated'),
                avg_order_value=Avg('avg_order_value'),
                avg_service_time=Avg('avg_service_time_seconds'),
                avg_rating=Avg('customer_rating_avg'),
                total_ratings=Sum('rating_count'),
                total_upsells=Sum('upsell_count'),
                total_tips=Sum('tips_amount'),
                days_worked=Count('date', distinct=True),
            )
        )

        # Calculate derived metrics and sort
        sort_map = {
            'revenue': 'total_revenue',
            'orders': 'total_orders',
            'rating': 'avg_rating',
            'tips': 'total_tips',
        }
        sort_field = sort_map.get(sort_by, 'total_revenue')

        for entry in staff_data:
            entry['user_id'] = str(entry['user_id'])
            entry['total_revenue'] = _to_float(entry['total_revenue'])
            entry['avg_order_value'] = _to_float(entry['avg_order_value'])
            entry['avg_service_time'] = entry['avg_service_time'] or 0
            entry['avg_rating'] = _to_float(entry['avg_rating'])
            entry['total_tips'] = _to_float(entry['total_tips'])
            # Revenue per day
            days = entry['days_worked'] or 1
            entry['revenue_per_day'] = round(entry['total_revenue'] / days, 2)
            entry['orders_per_day'] = round((entry['total_orders'] or 0) / days, 2)

        staff_data.sort(
            key=lambda x: x.get(sort_field, 0) or 0,
            reverse=True,
        )

        # Assign rank
        for i, entry in enumerate(staff_data, 1):
            entry['rank'] = i

        # ---- Team totals ----
        team_totals = metric_qs.aggregate(
            total_orders=Sum('orders_handled'),
            total_revenue=Sum('revenue_generated'),
            avg_order_value=Avg('avg_order_value'),
            avg_service_time=Avg('avg_service_time_seconds'),
            avg_rating=Avg('customer_rating_avg'),
            total_tips=Sum('tips_amount'),
            total_upsells=Sum('upsell_count'),
        )

        # ---- Schedule / attendance stats ----
        schedule_qs = StaffSchedule.objects.filter(
            organization_id=org_id,
            deleted_at__isnull=True,
            date__gte=start_date,
            date__lte=end_date,
        )
        if user_id:
            schedule_qs = schedule_qs.filter(user_id=user_id)

        attendance_stats = schedule_qs.aggregate(
            total_scheduled=Count('id'),
            checked_in=Count('id', filter=Q(status='CHECKED_IN')),
            checked_out=Count('id', filter=Q(status='CHECKED_OUT')),
            absent=Count('id', filter=Q(status='ABSENT')),
            late=Count('id', filter=Q(status='LATE')),
        )

        total_scheduled = attendance_stats['total_scheduled'] or 0
        attendance_rate = (
            round(
                ((attendance_stats['checked_in'] or 0) + (attendance_stats['checked_out'] or 0))
                / total_scheduled * 100, 2
            )
            if total_scheduled > 0 else 0.0
        )

        return {
            'period': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
            },
            'sort_by': sort_by,
            'team_summary': {
                'staff_count': len(staff_data),
                'total_orders': team_totals['total_orders'] or 0,
                'total_revenue': _to_float(team_totals['total_revenue']),
                'avg_order_value': _to_float(team_totals['avg_order_value']),
                'avg_service_time_seconds': team_totals['avg_service_time'] or 0,
                'avg_rating': _to_float(team_totals['avg_rating']),
                'total_tips': _to_float(team_totals['total_tips']),
                'total_upsells': team_totals['total_upsells'] or 0,
            },
            'attendance': {
                'total_scheduled': total_scheduled,
                'checked_in': attendance_stats['checked_in'] or 0,
                'checked_out': attendance_stats['checked_out'] or 0,
                'absent': attendance_stats['absent'] or 0,
                'late': attendance_stats['late'] or 0,
                'attendance_rate_pct': attendance_rate,
            },
            'staff': staff_data,
        }
