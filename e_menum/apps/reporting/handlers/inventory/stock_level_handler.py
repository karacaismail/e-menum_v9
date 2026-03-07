"""
Stock Level Report Handler (RPT-INV-001).

Generates comprehensive stock level reports showing current inventory
status, low/critical items, total inventory value, and stock
distribution by category. Queries the InventoryItem model with
proper tenant filtering.

Critical Rules:
    - ALL queries MUST filter by organization_id (multi-tenancy)
    - ALL queries on soft-delete models MUST filter deleted_at__isnull=True
    - Return values must be JSON-serializable (Decimal -> float)
"""

import logging
from datetime import date, timedelta
from decimal import Decimal
from typing import List

from django.db.models import Avg, Count, F, Q, Sum

from apps.reporting.services.report_engine import BaseReportHandler, register_handler

logger = logging.getLogger(__name__)


def _to_float(val) -> float:
    """Safely convert a Decimal or None to float."""
    if val is None:
        return 0.0
    return float(val)


@register_handler('RPT-INV-001')
class StockLevelHandler(BaseReportHandler):
    """
    Stock level report handler.

    Provides current stock overview, low/critical item alerts,
    total inventory value, stock distribution by category, and
    recent movement summary.

    Parameters:
        category: str - Optional filter by item category
        include_inactive: bool - Whether to include inactive items (default: False)
        low_stock_only: bool - Show only low/critical stock items (default: False)
    """

    feature_key = 'RPT-INV-001'

    def get_required_permissions(self) -> List[str]:
        return ['reporting.view', 'inventory.view']

    def get_default_parameters(self) -> dict:
        return {
            'category': None,
            'include_inactive': False,
            'low_stock_only': False,
        }

    def validate_parameters(self, parameters: dict) -> dict:
        merged = {**self.get_default_parameters(), **parameters}

        # Coerce booleans
        if isinstance(merged['include_inactive'], str):
            merged['include_inactive'] = merged['include_inactive'].lower() in ('true', '1', 'yes')
        if isinstance(merged['low_stock_only'], str):
            merged['low_stock_only'] = merged['low_stock_only'].lower() in ('true', '1', 'yes')

        return merged

    def generate(self, org_id: str, parameters: dict) -> dict:
        from apps.inventory.models import InventoryItem, StockMovement

        category = parameters.get('category')
        include_inactive = parameters.get('include_inactive', False)
        low_stock_only = parameters.get('low_stock_only', False)

        # ---- Base queryset with tenant filtering ----
        qs = InventoryItem.objects.filter(
            organization_id=org_id,
            deleted_at__isnull=True,
        )

        if not include_inactive:
            qs = qs.filter(is_active=True)

        if category:
            qs = qs.filter(category=category)

        if low_stock_only:
            qs = qs.filter(current_stock__lte=F('min_stock_level'))

        # ---- Summary metrics ----
        summary = qs.aggregate(
            total_items=Count('id'),
            total_stock_value=Sum(F('current_stock') * F('cost_per_unit')),
            avg_stock_value=Avg(F('current_stock') * F('cost_per_unit')),
            critical_count=Count(
                'id',
                filter=Q(current_stock__lte=F('min_stock_level') * Decimal('0.5')),
            ),
            low_count=Count(
                'id',
                filter=Q(
                    current_stock__gt=F('min_stock_level') * Decimal('0.5'),
                    current_stock__lte=F('min_stock_level'),
                ),
            ),
            normal_count=Count(
                'id',
                filter=Q(
                    current_stock__gt=F('min_stock_level'),
                    current_stock__lte=F('max_stock_level'),
                ),
            ),
            excess_count=Count(
                'id',
                filter=Q(
                    max_stock_level__gt=0,
                    current_stock__gt=F('max_stock_level'),
                ),
            ),
        )

        # ---- Category breakdown ----
        category_breakdown = list(
            qs.values('category')
            .annotate(
                item_count=Count('id'),
                total_value=Sum(F('current_stock') * F('cost_per_unit')),
                low_stock_count=Count(
                    'id',
                    filter=Q(current_stock__lte=F('min_stock_level')),
                ),
            )
            .order_by('-total_value')
        )

        for row in category_breakdown:
            row['category'] = row['category'] or 'Uncategorized'
            row['total_value'] = _to_float(row['total_value'])

        # ---- Low / critical items list ----
        alert_items = list(
            qs.filter(current_stock__lte=F('min_stock_level'))
            .values(
                'id', 'name', 'sku', 'category', 'unit_type',
                'current_stock', 'min_stock_level', 'cost_per_unit',
            )
            .order_by('current_stock')[:50]
        )

        for item in alert_items:
            item['id'] = str(item['id'])
            item['current_stock'] = _to_float(item['current_stock'])
            item['min_stock_level'] = _to_float(item['min_stock_level'])
            item['cost_per_unit'] = _to_float(item['cost_per_unit'])
            item['stock_value'] = item['current_stock'] * item['cost_per_unit']
            # Classify level
            if item['current_stock'] <= item['min_stock_level'] * 0.5:
                item['level'] = 'CRITICAL'
            else:
                item['level'] = 'LOW'

        # ---- Recent movements summary (last 7 days) ----
        seven_days_ago = date.today() - timedelta(days=7)
        movement_summary = list(
            StockMovement.objects.filter(
                organization_id=org_id,
                deleted_at__isnull=True,
                created_at__date__gte=seven_days_ago,
            )
            .values('movement_type')
            .annotate(
                count=Count('id'),
                total_quantity=Sum('quantity'),
                total_cost=Sum('total_cost'),
            )
            .order_by('movement_type')
        )

        for row in movement_summary:
            row['total_quantity'] = _to_float(row['total_quantity'])
            row['total_cost'] = _to_float(row['total_cost'])

        return {
            'summary': {
                'total_items': summary['total_items'] or 0,
                'total_stock_value': _to_float(summary['total_stock_value']),
                'avg_stock_value': _to_float(summary['avg_stock_value']),
                'stock_levels': {
                    'critical': summary['critical_count'] or 0,
                    'low': summary['low_count'] or 0,
                    'normal': summary['normal_count'] or 0,
                    'excess': summary['excess_count'] or 0,
                },
            },
            'category_breakdown': category_breakdown,
            'alert_items': alert_items,
            'recent_movements': {
                'period_days': 7,
                'data': movement_summary,
            },
        }
