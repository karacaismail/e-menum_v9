"""
Top Sellers Report Handler (RPT-SAL-009).

Generates ranked lists of best-selling products by quantity, revenue,
or profit margin. Queries OrderItem with Product joins, applying
proper multi-tenant and soft-delete filters.

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
from django.db.models.functions import Coalesce

from apps.orders.choices import OrderStatus
from apps.orders.models import Order, OrderItem
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


@register_handler('RPT-SAL-009')
class TopSellersHandler(BaseReportHandler):
    """
    Top sellers report handler.

    Returns a ranked list of products sorted by quantity sold, revenue,
    or margin with each product's share of total revenue.

    Parameters:
        period: str - DAILY, WEEKLY, or MONTHLY (informational label)
        start_date: str - Start date in YYYY-MM-DD format
        end_date: str - End date in YYYY-MM-DD format
        limit: int - Maximum number of products to return (default 20)
        sort_by: str - 'quantity', 'revenue', or 'margin' (default 'revenue')
    """

    feature_key = 'RPT-SAL-009'

    def get_required_permissions(self) -> List[str]:
        return ['reporting.view', 'sales.view']

    def get_default_parameters(self) -> dict:
        today = date.today()
        return {
            'period': 'MONTHLY',
            'start_date': (today - timedelta(days=30)).isoformat(),
            'end_date': today.isoformat(),
            'limit': 20,
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

        merged['limit'] = int(merged.get('limit', 20))
        if merged['limit'] < 1:
            merged['limit'] = 20

        valid_sort = ['quantity', 'revenue', 'margin']
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
        limit = parameters['limit']
        sort_by = parameters['sort_by']

        # Base queryset: order items from completed/delivered orders
        base_qs = OrderItem.objects.filter(
            order__organization_id=org_id,
            order__deleted_at__isnull=True,
            deleted_at__isnull=True,
            order__status__in=[OrderStatus.COMPLETED, OrderStatus.DELIVERED],
            order__created_at__date__gte=start_date,
            order__created_at__date__lte=end_date,
        )

        # Aggregate by product
        product_stats = (
            base_qs
            .values(
                product_id=F('product__id'),
                product_name=F('product__name'),
                category_name=F('product__category__name'),
                product_base_price=F('product__base_price'),
            )
            .annotate(
                qty_sold=Sum('quantity'),
                revenue=Sum('total_price'),
                avg_price=Avg('unit_price'),
                order_count=Count('order', distinct=True),
            )
        )

        # Calculate total revenue for share computation
        total_revenue = _to_float(base_qs.aggregate(t=Sum('total_price'))['t'])

        # Determine sort order
        if sort_by == 'quantity':
            product_stats = product_stats.order_by('-qty_sold')
        elif sort_by == 'margin':
            # Sort by revenue per unit (proxy for margin when cost not available)
            product_stats = product_stats.order_by('-avg_price')
        else:
            product_stats = product_stats.order_by('-revenue')

        # Apply limit
        product_stats = product_stats[:limit]

        # Build ranked list
        items = []
        for rank, row in enumerate(product_stats, start=1):
            rev = _to_float(row['revenue'])
            qty = row['qty_sold'] or 0
            avg_p = _to_float(row['avg_price'])
            base_p = _to_float(row['product_base_price'])

            # Estimate margin: (avg_price - base_price * 0.4) / avg_price * 100
            # This is a rough estimate since we don't have cost_price on Product.
            # We use the ProductPerformance profit_margin if available, else estimate.
            margin = self._get_product_margin(
                org_id, row['product_id'], start_date, end_date,
            )

            items.append({
                'rank': rank,
                'product_id': str(row['product_id']) if row['product_id'] else None,
                'product_name': row['product_name'] or 'Unknown',
                'category_name': row['category_name'] or 'Uncategorized',
                'qty_sold': qty,
                'revenue': rev,
                'avg_price': round(avg_p, 2),
                'order_count': row['order_count'] or 0,
                'revenue_share_percent': round(
                    (rev / total_revenue * 100) if total_revenue > 0 else 0, 2,
                ),
                'profit_margin_percent': margin,
            })

        return {
            'period': {
                'type': parameters['period'],
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
            },
            'sort_by': sort_by,
            'total_revenue': total_revenue,
            'total_items_sold': sum(i['qty_sold'] for i in items),
            'product_count': len(items),
            'items': items,
        }

    def _get_product_margin(
        self,
        org_id: str,
        product_id,
        start: date,
        end: date,
    ) -> Optional[float]:
        """
        Try to retrieve profit margin from ProductPerformance records.
        Returns None if no data available.
        """
        if product_id is None:
            return None

        from apps.analytics.models import ProductPerformance

        perf = (
            ProductPerformance.objects.filter(
                organization_id=org_id,
                deleted_at__isnull=True,
                product_id=product_id,
                period_start__gte=start,
                period_end__lte=end,
            )
            .aggregate(avg_margin=Avg('profit_margin'))
        )

        val = perf.get('avg_margin')
        return round(float(val), 2) if val is not None else None
