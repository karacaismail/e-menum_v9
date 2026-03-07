"""
Menu Performance Matrix Report Handler (RPT-MNU-001).

Classifies products into a BCG-style matrix based on sales volume
and profit margin:
    - Star: High sales, high margin
    - Cash Cow: High sales, low margin
    - Question Mark: Low sales, high margin
    - Dog: Low sales, low margin

Critical Rules:
    - ALL queries MUST filter by organization_id (multi-tenancy)
    - ALL queries on soft-delete models MUST filter deleted_at__isnull=True
    - Return values must be JSON-serializable (Decimal -> float)
"""

import logging
from datetime import date, datetime, timedelta
from typing import List, Optional

from django.db.models import Avg, F, Sum

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


QUADRANT_STAR = 'Star'
QUADRANT_CASH_COW = 'Cash Cow'
QUADRANT_QUESTION_MARK = 'Question Mark'
QUADRANT_DOG = 'Dog'


@register_handler('RPT-MNU-001')
class MenuPerformanceMatrixHandler(BaseReportHandler):
    """
    Menu performance matrix (BCG) report handler.

    Classifies each product into one of four quadrants based on
    its relative sales volume and margin compared to the averages.

    Parameters:
        period: str - DAILY, WEEKLY, or MONTHLY
        start_date: str - Start date in YYYY-MM-DD
        end_date: str - End date in YYYY-MM-DD
    """

    feature_key = 'RPT-MNU-001'

    def get_required_permissions(self) -> List[str]:
        return ['reporting.view', 'menu.view']

    def get_default_parameters(self) -> dict:
        today = date.today()
        return {
            'period': 'MONTHLY',
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

        # ---- Gather per-product data ----
        products = self._gather_product_data(org_id, start_date, end_date)

        if not products:
            return {
                'period': {
                    'type': parameters['period'],
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat(),
                },
                'summary': {
                    'total_products': 0,
                    'avg_quantity_sold': 0,
                    'avg_margin': 0,
                },
                'quadrants': {
                    QUADRANT_STAR: 0,
                    QUADRANT_CASH_COW: 0,
                    QUADRANT_QUESTION_MARK: 0,
                    QUADRANT_DOG: 0,
                },
                'products': [],
                'recommendations': [],
            }

        # ---- Calculate averages as thresholds ----
        quantities = [p['qty_sold'] for p in products]
        margins = [p['margin'] for p in products]

        avg_qty = sum(quantities) / len(quantities) if quantities else 0
        avg_margin = sum(margins) / len(margins) if margins else 0

        # ---- Classify each product ----
        quadrant_counts = {
            QUADRANT_STAR: 0,
            QUADRANT_CASH_COW: 0,
            QUADRANT_QUESTION_MARK: 0,
            QUADRANT_DOG: 0,
        }

        for p in products:
            high_sales = p['qty_sold'] >= avg_qty
            high_margin = p['margin'] >= avg_margin

            if high_sales and high_margin:
                quadrant = QUADRANT_STAR
            elif high_sales and not high_margin:
                quadrant = QUADRANT_CASH_COW
            elif not high_sales and high_margin:
                quadrant = QUADRANT_QUESTION_MARK
            else:
                quadrant = QUADRANT_DOG

            p['quadrant'] = quadrant
            quadrant_counts[quadrant] += 1

        # ---- Generate recommendations ----
        recommendations = self._generate_recommendations(products, quadrant_counts)

        # ---- Sort products by revenue descending ----
        products.sort(key=lambda x: x['revenue'], reverse=True)

        return {
            'period': {
                'type': parameters['period'],
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
            },
            'summary': {
                'total_products': len(products),
                'avg_quantity_sold': round(avg_qty, 1),
                'avg_margin': round(avg_margin, 2),
            },
            'quadrants': quadrant_counts,
            'products': products,
            'recommendations': recommendations,
        }

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _gather_product_data(
        self, org_id: str, start: date, end: date,
    ) -> List[dict]:
        """
        Gather per-product sales and margin data.

        First tries ProductPerformance for pre-calculated margins.
        Falls back to OrderItem aggregation with estimated margins.
        """
        # Try ProductPerformance first
        perf_qs = ProductPerformance.objects.filter(
            organization_id=org_id,
            deleted_at__isnull=True,
            period_start__gte=start,
            period_end__lte=end,
        )

        perf_data = list(
            perf_qs
            .values(
                pid=F('product__id'),
                pname=F('product__name'),
                cat=F('product__category__name'),
            )
            .annotate(
                total_qty=Sum('quantity_sold'),
                total_revenue=Sum('revenue'),
                avg_margin=Avg('profit_margin'),
                avg_sales_mix=Avg('sales_mix_percent'),
            )
        )

        if perf_data:
            products = []
            for row in perf_data:
                products.append({
                    'product_id': str(row['pid']) if row['pid'] else None,
                    'product_name': row['pname'] or 'Unknown',
                    'category_name': row['cat'] or 'Uncategorized',
                    'qty_sold': row['total_qty'] or 0,
                    'revenue': _to_float(row['total_revenue']),
                    'margin': _to_float(row['avg_margin']),
                    'sales_mix_percent': _to_float(row['avg_sales_mix']),
                })
            return products

        # Fall back to OrderItem aggregation
        return self._gather_from_order_items(org_id, start, end)

    def _gather_from_order_items(
        self, org_id: str, start: date, end: date,
    ) -> List[dict]:
        """
        Aggregate product data directly from OrderItem.
        Estimate margin using (unit_price - base_price) / unit_price.
        """
        qs = OrderItem.objects.filter(
            order__organization_id=org_id,
            order__deleted_at__isnull=True,
            deleted_at__isnull=True,
            order__status__in=[OrderStatus.COMPLETED, OrderStatus.DELIVERED],
            order__created_at__date__gte=start,
            order__created_at__date__lte=end,
            product__isnull=False,
        )

        rows = (
            qs
            .values(
                pid=F('product__id'),
                pname=F('product__name'),
                cat=F('product__category__name'),
                base_price=F('product__base_price'),
            )
            .annotate(
                total_qty=Sum('quantity'),
                total_revenue=Sum('total_price'),
                avg_unit_price=Avg('unit_price'),
            )
        )

        total_revenue = _to_float(qs.aggregate(t=Sum('total_price'))['t'])
        products = []
        for row in rows:
            avg_up = _to_float(row['avg_unit_price'])
            bp = _to_float(row['base_price'])
            rev = _to_float(row['total_revenue'])

            # Estimate margin as (selling_price - cost_estimate) / selling_price
            # Since we don't have cost_price, use base_price * 0.4 as cost proxy
            cost_estimate = bp * 0.4
            margin = round(
                ((avg_up - cost_estimate) / avg_up * 100) if avg_up > 0 else 0, 2,
            )

            products.append({
                'product_id': str(row['pid']) if row['pid'] else None,
                'product_name': row['pname'] or 'Unknown',
                'category_name': row['cat'] or 'Uncategorized',
                'qty_sold': row['total_qty'] or 0,
                'revenue': rev,
                'margin': margin,
                'sales_mix_percent': round(
                    (rev / total_revenue * 100) if total_revenue > 0 else 0, 2,
                ),
            })

        return products

    def _generate_recommendations(
        self, products: List[dict], quadrant_counts: dict,
    ) -> List[dict]:
        """Generate actionable recommendations based on BCG analysis."""
        recommendations = []

        stars = [p for p in products if p.get('quadrant') == QUADRANT_STAR]
        cash_cows = [p for p in products if p.get('quadrant') == QUADRANT_CASH_COW]
        question_marks = [p for p in products if p.get('quadrant') == QUADRANT_QUESTION_MARK]
        dogs = [p for p in products if p.get('quadrant') == QUADRANT_DOG]

        if stars:
            top_star = max(stars, key=lambda x: x['revenue'])
            recommendations.append({
                'type': 'promote',
                'priority': 'high',
                'message': (
                    f"'{top_star['product_name']}' is a Star product with high sales "
                    f"and high margin. Feature it prominently on your menu."
                ),
                'product_id': top_star['product_id'],
            })

        if cash_cows:
            low_margin_cow = min(cash_cows, key=lambda x: x['margin'])
            recommendations.append({
                'type': 'optimize',
                'priority': 'medium',
                'message': (
                    f"'{low_margin_cow['product_name']}' sells well but has low margin. "
                    f"Consider reviewing its pricing or reducing costs."
                ),
                'product_id': low_margin_cow['product_id'],
            })

        if question_marks:
            top_qm = max(question_marks, key=lambda x: x['margin'])
            recommendations.append({
                'type': 'investigate',
                'priority': 'medium',
                'message': (
                    f"'{top_qm['product_name']}' has high margin but low sales. "
                    f"Consider promoting it or adding it to combo deals."
                ),
                'product_id': top_qm['product_id'],
            })

        if dogs:
            worst_dog = min(dogs, key=lambda x: x['revenue'])
            recommendations.append({
                'type': 'review',
                'priority': 'low',
                'message': (
                    f"'{worst_dog['product_name']}' has both low sales and low margin. "
                    f"Consider removing it from the menu or redesigning it."
                ),
                'product_id': worst_dog['product_id'],
            })

        if quadrant_counts.get(QUADRANT_DOG, 0) > len(products) * 0.3:
            recommendations.append({
                'type': 'alert',
                'priority': 'high',
                'message': (
                    "Over 30% of your products are in the 'Dog' quadrant. "
                    "Consider a menu redesign to focus on better-performing items."
                ),
                'product_id': None,
            })

        return recommendations
