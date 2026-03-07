"""
Branch Comparison Report Handler (RPT-BRN-001).

Generates branch comparison reports showing revenue, order count,
average order value, and other KPIs across branches within an
organization. Queries Order model grouped by branch with proper
tenant filtering.

Critical Rules:
    - ALL queries MUST filter by organization_id (multi-tenancy)
    - ALL queries on soft-delete models MUST filter deleted_at__isnull=True
    - Return values must be JSON-serializable (Decimal -> float)
"""

import logging
from datetime import date, datetime, timedelta
from typing import List, Optional

from django.db.models import Avg, Count, Sum

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


def _safe_percent(numerator: float, denominator: float) -> float:
    """Safely compute percentage."""
    if denominator == 0:
        return 0.0
    return round(numerator / denominator * 100, 2)


@register_handler('RPT-BRN-001')
class BranchComparisonHandler(BaseReportHandler):
    """
    Branch comparison report handler.

    Compares performance across branches with revenue, order count,
    average order value, and customer metrics. Includes ranking
    and optional previous-period comparison.

    Parameters:
        start_date: str - Start date in YYYY-MM-DD format
        end_date: str - End date in YYYY-MM-DD format
        branch_ids: list - Optional list of specific branch UUIDs to compare
        metric: str - Primary comparison metric: revenue, orders, avg_order_value
    """

    feature_key = 'RPT-BRN-001'

    def get_required_permissions(self) -> List[str]:
        return ['reporting.view', 'branch.view']

    def get_default_parameters(self) -> dict:
        today = date.today()
        return {
            'start_date': (today - timedelta(days=30)).isoformat(),
            'end_date': today.isoformat(),
            'branch_ids': None,
            'metric': 'revenue',
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

        valid_metrics = ['revenue', 'orders', 'avg_order_value']
        if merged['metric'] not in valid_metrics:
            from shared.utils.exceptions import AppException
            raise AppException(
                code='INVALID_METRIC',
                message=f"metric must be one of {valid_metrics}",
                status_code=400,
            )

        return merged

    def generate(self, org_id: str, parameters: dict) -> dict:
        from apps.core.models import Branch
        from apps.orders.choices import OrderStatus
        from apps.orders.models import Order

        start_date = parameters['start_date']
        end_date = parameters['end_date']
        branch_ids = parameters.get('branch_ids')
        primary_metric = parameters.get('metric', 'revenue')

        # ---- Get branches for the organization ----
        branch_qs = Branch.objects.filter(
            organization_id=org_id,
            deleted_at__isnull=True,
        )
        if branch_ids:
            branch_qs = branch_qs.filter(id__in=branch_ids)

        branch_map = {str(b.id): b.name for b in branch_qs}

        # ---- Current period: Order metrics per branch ----
        order_qs = Order.objects.filter(
            organization_id=org_id,
            deleted_at__isnull=True,
            status__in=[OrderStatus.COMPLETED, OrderStatus.DELIVERED],
            created_at__date__gte=start_date,
            created_at__date__lte=end_date,
        )

        if branch_ids:
            order_qs = order_qs.filter(branch_id__in=branch_ids)

        branch_metrics = list(
            order_qs
            .values('branch_id')
            .annotate(
                revenue=Sum('total_amount'),
                order_count=Count('id'),
                avg_order_value=Avg('total_amount'),
                customer_count=Count('customer', distinct=True),
                discount_total=Sum('discount_amount'),
            )
            .order_by('-revenue')
        )

        # ---- Previous period for comparison ----
        period_days = (end_date - start_date).days + 1
        prev_end = start_date - timedelta(days=1)
        prev_start = prev_end - timedelta(days=period_days - 1)

        prev_order_qs = Order.objects.filter(
            organization_id=org_id,
            deleted_at__isnull=True,
            status__in=[OrderStatus.COMPLETED, OrderStatus.DELIVERED],
            created_at__date__gte=prev_start,
            created_at__date__lte=prev_end,
        )
        if branch_ids:
            prev_order_qs = prev_order_qs.filter(branch_id__in=branch_ids)

        prev_metrics = {}
        for row in prev_order_qs.values('branch_id').annotate(
            revenue=Sum('total_amount'),
            order_count=Count('id'),
        ):
            bid = str(row['branch_id']) if row['branch_id'] else 'unassigned'
            prev_metrics[bid] = row

        # ---- Build branch comparison data ----
        total_revenue = sum(_to_float(r['revenue']) for r in branch_metrics)

        branches_data = []
        for rank, row in enumerate(branch_metrics, 1):
            bid = str(row['branch_id']) if row['branch_id'] else 'unassigned'
            rev = _to_float(row['revenue'])
            prev = prev_metrics.get(bid, {})
            prev_rev = _to_float(prev.get('revenue'))

            branch_entry = {
                'branch_id': bid,
                'branch_name': branch_map.get(bid, 'Unassigned'),
                'rank': rank,
                'revenue': rev,
                'order_count': row['order_count'] or 0,
                'avg_order_value': _to_float(row['avg_order_value']),
                'customer_count': row['customer_count'] or 0,
                'discount_total': _to_float(row['discount_total']),
                'revenue_share_pct': _safe_percent(rev, total_revenue),
                'previous_revenue': prev_rev,
                'revenue_change_pct': (
                    round(((rev - prev_rev) / prev_rev) * 100, 2)
                    if prev_rev > 0 else None
                ),
                'previous_order_count': prev.get('order_count', 0) or 0,
            }
            branches_data.append(branch_entry)

        # Sort by primary metric
        metric_key_map = {
            'revenue': 'revenue',
            'orders': 'order_count',
            'avg_order_value': 'avg_order_value',
        }
        sort_key = metric_key_map.get(primary_metric, 'revenue')
        branches_data.sort(key=lambda x: x[sort_key], reverse=True)

        # Update ranks after re-sort
        for i, b in enumerate(branches_data, 1):
            b['rank'] = i

        # ---- Organization totals ----
        org_total = order_qs.aggregate(
            total_revenue=Sum('total_amount'),
            total_orders=Count('id'),
            total_avg_order=Avg('total_amount'),
            total_customers=Count('customer', distinct=True),
        )

        return {
            'period': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
            },
            'comparison_metric': primary_metric,
            'organization_totals': {
                'total_revenue': _to_float(org_total['total_revenue']),
                'total_orders': org_total['total_orders'] or 0,
                'avg_order_value': _to_float(org_total['total_avg_order']),
                'total_customers': org_total['total_customers'] or 0,
            },
            'branches': branches_data,
            'branch_count': len(branches_data),
        }
