"""
Item Performance Report Handler (RPT-MNU-002).

Generates a paginated list of menu items with performance metrics
including quantity sold, revenue, profit margin, sales mix percentage,
and trend indicators.

Critical Rules:
    - ALL queries MUST filter by organization_id (multi-tenancy)
    - ALL queries on soft-delete models MUST filter deleted_at__isnull=True
    - Return values must be JSON-serializable (Decimal -> float)
"""

import logging
from datetime import date, datetime, timedelta
from typing import List, Optional

from django.db.models import Avg, Count, F, Sum

from apps.analytics.models import ProductPerformance
from apps.orders.choices import OrderStatus
from apps.orders.models import OrderItem
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


@register_handler('RPT-MNU-002')
class ItemPerformanceHandler(BaseReportHandler):
    """
    Item performance report handler.

    Returns a paginated list of products with detailed performance
    metrics and trend indicators.

    Parameters:
        period: str - DAILY, WEEKLY, or MONTHLY
        start_date: str - Start date in YYYY-MM-DD
        end_date: str - End date in YYYY-MM-DD
        category_id: str - Optional UUID to filter by category
        sort_by: str - 'revenue', 'quantity', 'margin', 'name' (default 'revenue')
        page: int - Page number (default 1)
        per_page: int - Items per page (default 20, max 100)
    """

    feature_key = 'RPT-MNU-002'

    def get_required_permissions(self) -> List[str]:
        return ['reporting.view', 'menu.view']

    def get_default_parameters(self) -> dict:
        today = date.today()
        return {
            'period': 'MONTHLY',
            'start_date': (today - timedelta(days=30)).isoformat(),
            'end_date': today.isoformat(),
            'category_id': None,
            'sort_by': 'revenue',
            'page': 1,
            'per_page': 20,
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

        merged['page'] = max(1, int(merged.get('page', 1)))
        merged['per_page'] = min(100, max(1, int(merged.get('per_page', 20))))

        valid_sort = ['revenue', 'quantity', 'margin', 'name']
        if merged['sort_by'] not in valid_sort:
            from shared.utils.exceptions import AppException
            raise AppException(
                code='INVALID_SORT_BY',
                message=f"sort_by must be one of {valid_sort}",
                status_code=400,
            )

        return merged

    def generate(self, org_id: str, parameters: dict) -> dict:
        start_date = parameters['start_date']
        end_date = parameters['end_date']
        category_id = parameters.get('category_id')
        sort_by = parameters['sort_by']
        page = parameters['page']
        per_page = parameters['per_page']

        # ---- Build base OrderItem queryset ----
        oi_qs = OrderItem.objects.filter(
            order__organization_id=org_id,
            order__deleted_at__isnull=True,
            deleted_at__isnull=True,
            order__status__in=[OrderStatus.COMPLETED, OrderStatus.DELIVERED],
            order__created_at__date__gte=start_date,
            order__created_at__date__lte=end_date,
            product__isnull=False,
            product__deleted_at__isnull=True,
        )

        if category_id:
            oi_qs = oi_qs.filter(product__category_id=category_id)

        # ---- Aggregate per product ----
        product_agg = (
            oi_qs
            .values(
                product_id=F('product__id'),
                product_name=F('product__name'),
                category_name=F('product__category__name'),
                category_id_val=F('product__category__id'),
                base_price=F('product__base_price'),
                is_active=F('product__is_active'),
            )
            .annotate(
                qty_sold=Sum('quantity'),
                revenue=Sum('total_price'),
                avg_price=Avg('unit_price'),
                order_count=Count('order', distinct=True),
            )
        )

        # Total revenue for sales mix computation
        total_revenue = _to_float(oi_qs.aggregate(t=Sum('total_price'))['t'])

        # ---- Sort ----
        sort_map = {
            'revenue': '-revenue',
            'quantity': '-qty_sold',
            'margin': '-avg_price',  # proxy sort; we refine margin below
            'name': 'product_name',
        }
        product_agg = product_agg.order_by(sort_map.get(sort_by, '-revenue'))

        # ---- Pagination ----
        total_items = product_agg.count()
        total_pages = max(1, (total_items + per_page - 1) // per_page)
        offset = (page - 1) * per_page
        page_data = list(product_agg[offset:offset + per_page])

        # ---- Enrich with margin and trend ----
        items = []
        for row in page_data:
            pid = row['product_id']
            rev = _to_float(row['revenue'])
            avg_p = _to_float(row['avg_price'])
            bp = _to_float(row['base_price'])

            # Get margin from ProductPerformance if available
            margin = self._get_product_margin(org_id, pid, start_date, end_date)
            if margin is None:
                # Estimate: assume cost is ~40% of base_price
                cost_est = bp * 0.4
                margin = round(
                    ((avg_p - cost_est) / avg_p * 100) if avg_p > 0 else 0, 2,
                )

            # Get trend indicator
            trend = self._get_trend(org_id, pid, start_date, end_date)

            items.append({
                'product_id': str(pid) if pid else None,
                'product_name': row['product_name'] or 'Unknown',
                'category_name': row['category_name'] or 'Uncategorized',
                'category_id': str(row['category_id_val']) if row['category_id_val'] else None,
                'is_active': row['is_active'],
                'qty_sold': row['qty_sold'] or 0,
                'revenue': rev,
                'avg_price': round(avg_p, 2),
                'order_count': row['order_count'] or 0,
                'profit_margin_percent': margin,
                'sales_mix_percent': round(
                    (rev / total_revenue * 100) if total_revenue > 0 else 0, 2,
                ),
                'trend': trend,
            })

        # If sort_by is margin, re-sort the page results by actual margin
        if sort_by == 'margin':
            items.sort(key=lambda x: x['profit_margin_percent'] or 0, reverse=True)

        return {
            'period': {
                'type': parameters['period'],
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
            },
            'filters': {
                'category_id': category_id,
                'sort_by': sort_by,
            },
            'meta': {
                'page': page,
                'per_page': per_page,
                'total': total_items,
                'total_pages': total_pages,
            },
            'total_revenue': total_revenue,
            'items': items,
        }

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _get_product_margin(
        self, org_id: str, product_id, start: date, end: date,
    ) -> Optional[float]:
        """Get average profit margin from ProductPerformance."""
        if product_id is None:
            return None

        result = (
            ProductPerformance.objects.filter(
                organization_id=org_id,
                deleted_at__isnull=True,
                product_id=product_id,
                period_start__gte=start,
                period_end__lte=end,
            )
            .aggregate(avg_margin=Avg('profit_margin'))
        )

        val = result.get('avg_margin')
        return round(float(val), 2) if val is not None else None

    def _get_trend(
        self, org_id: str, product_id, start: date, end: date,
    ) -> str:
        """
        Determine trend direction by comparing the first half vs second half
        of the period.

        Returns: 'up', 'down', or 'stable'
        """
        if product_id is None:
            return 'stable'

        period_days = (end - start).days
        if period_days < 2:
            return 'stable'

        midpoint = start + timedelta(days=period_days // 2)

        base_filter = dict(
            order__organization_id=org_id,
            order__deleted_at__isnull=True,
            deleted_at__isnull=True,
            product_id=product_id,
            order__status__in=[OrderStatus.COMPLETED, OrderStatus.DELIVERED],
        )

        first_half = OrderItem.objects.filter(
            **base_filter,
            order__created_at__date__gte=start,
            order__created_at__date__lt=midpoint,
        ).aggregate(qty=Sum('quantity'))['qty'] or 0

        second_half = OrderItem.objects.filter(
            **base_filter,
            order__created_at__date__gte=midpoint,
            order__created_at__date__lte=end,
        ).aggregate(qty=Sum('quantity'))['qty'] or 0

        if second_half > first_half * 1.1:
            return 'up'
        elif second_half < first_half * 0.9:
            return 'down'
        return 'stable'
