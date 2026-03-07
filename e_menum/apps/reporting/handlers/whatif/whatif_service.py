"""
What-If Simulation Service.

Provides scenario simulation capabilities for strategic decision-making.
Each simulation computes projected outcomes based on current data and
hypothetical changes, returning current state, projected state, impact
analysis, and confidence levels.

Simulation Types:
    - simulate_price_change: Impact of changing a product's price
    - simulate_menu_change: Impact of adding/removing menu items
    - simulate_campaign: Impact of running a promotional campaign
    - simulate_expansion: Impact of adding new branches
    - simulate_staffing: Impact of staffing changes
    - simulate_hours: Impact of changing operating hours

Critical Rules:
    - ALL queries MUST filter by organization_id (multi-tenancy)
    - ALL queries on soft-delete models MUST filter deleted_at__isnull=True
    - Return values must be JSON-serializable (Decimal -> float)
"""

import logging
from datetime import date, timedelta

from django.db.models import Avg, Count, Sum

logger = logging.getLogger(__name__)


def _to_float(val) -> float:
    """Safely convert a Decimal or None to float."""
    if val is None:
        return 0.0
    return float(val)


class WhatIfService:
    """
    What-If simulation service for strategic planning.

    Provides six simulation types for projecting the impact of
    business decisions. Each method returns a standardized result
    containing current_state, projected_state, impact, and confidence.
    """

    def simulate_price_change(
        self,
        org_id: str,
        product_id: str,
        new_price: float,
    ) -> dict:
        """
        Simulate the impact of changing a product's price.

        Uses historical order data to estimate how a price change would
        affect revenue and order volume, applying a simple price
        elasticity model.

        Args:
            org_id: Organization UUID string
            product_id: Product UUID string
            new_price: The proposed new price

        Returns:
            dict with current_state, projected_state, impact, confidence
        """
        from apps.menu.models import Product
        from apps.orders.choices import OrderStatus
        from apps.orders.models import OrderItem

        # Get current product info
        try:
            product = Product.objects.get(
                id=product_id,
                organization_id=org_id,
                deleted_at__isnull=True,
            )
        except Product.DoesNotExist:
            return self._error_result('Product not found')

        current_price = _to_float(product.price)
        new_price = float(new_price)

        if current_price == 0:
            return self._error_result('Product has zero price')

        # Get recent order data (last 90 days)
        ninety_days_ago = date.today() - timedelta(days=90)
        item_qs = OrderItem.objects.filter(
            order__organization_id=org_id,
            product_id=product_id,
            order__deleted_at__isnull=True,
            deleted_at__isnull=True,
            order__status__in=[OrderStatus.COMPLETED, OrderStatus.DELIVERED],
            order__created_at__date__gte=ninety_days_ago,
        )

        metrics = item_qs.aggregate(
            total_quantity=Sum('quantity'),
            total_revenue=Sum('total_price'),
            order_count=Count('order', distinct=True),
        )

        total_qty = metrics['total_quantity'] or 0
        total_rev = _to_float(metrics['total_revenue'])

        # Price elasticity estimation (simplified model)
        # Typical food industry elasticity: -0.5 to -1.5
        elasticity = -0.8
        price_change_pct = (new_price - current_price) / current_price
        qty_change_pct = elasticity * price_change_pct

        projected_qty = max(0, total_qty * (1 + qty_change_pct))
        projected_revenue = projected_qty * new_price

        revenue_impact = projected_revenue - total_rev
        revenue_impact_pct = (
            round(revenue_impact / total_rev * 100, 2) if total_rev > 0 else 0.0
        )

        return {
            'simulation_type': 'price_change',
            'product_id': product_id,
            'product_name': product.name,
            'current_state': {
                'price': current_price,
                'total_quantity_sold': total_qty,
                'total_revenue': total_rev,
                'period_days': 90,
            },
            'projected_state': {
                'price': new_price,
                'projected_quantity': round(projected_qty, 0),
                'projected_revenue': round(projected_revenue, 2),
                'price_change_pct': round(price_change_pct * 100, 2),
                'quantity_change_pct': round(qty_change_pct * 100, 2),
            },
            'impact': {
                'revenue_impact': round(revenue_impact, 2),
                'revenue_impact_pct': revenue_impact_pct,
                'recommendation': (
                    'positive' if revenue_impact > 0
                    else 'negative' if revenue_impact < 0
                    else 'neutral'
                ),
            },
            'confidence': {
                'level': 'medium' if total_qty >= 50 else 'low',
                'data_points': total_qty,
                'notes': 'Based on 90-day sales data with -0.8 price elasticity assumption.',
            },
        }

    def simulate_menu_change(
        self,
        org_id: str,
        changes: dict,
    ) -> dict:
        """
        Simulate the impact of menu changes (adding/removing items).

        Args:
            org_id: Organization UUID string
            changes: Dict with 'add' (list of product specs) and 'remove' (list of product IDs)

        Returns:
            dict with current_state, projected_state, impact, confidence
        """
        from apps.menu.models import Product
        from apps.orders.choices import OrderStatus
        from apps.orders.models import Order, OrderItem

        thirty_days_ago = date.today() - timedelta(days=30)

        # Current menu performance
        current_products = Product.objects.filter(
            organization_id=org_id,
            deleted_at__isnull=True,
            is_active=True,
        ).count()

        current_revenue = _to_float(
            Order.objects.filter(
                organization_id=org_id,
                deleted_at__isnull=True,
                status__in=[OrderStatus.COMPLETED, OrderStatus.DELIVERED],
                created_at__date__gte=thirty_days_ago,
            ).aggregate(rev=Sum('total_amount'))['rev']
        )

        current_orders = Order.objects.filter(
            organization_id=org_id,
            deleted_at__isnull=True,
            status__in=[OrderStatus.COMPLETED, OrderStatus.DELIVERED],
            created_at__date__gte=thirty_days_ago,
        ).count()

        # Calculate removal impact
        remove_ids = changes.get('remove', [])
        removal_revenue = 0.0
        removal_details = []

        for pid in remove_ids:
            item_rev = _to_float(
                OrderItem.objects.filter(
                    order__organization_id=org_id,
                    product_id=pid,
                    order__deleted_at__isnull=True,
                    deleted_at__isnull=True,
                    order__status__in=[OrderStatus.COMPLETED, OrderStatus.DELIVERED],
                    order__created_at__date__gte=thirty_days_ago,
                ).aggregate(rev=Sum('total_price'))['rev']
            )
            removal_revenue += item_rev
            removal_details.append({
                'product_id': str(pid),
                'lost_revenue': item_rev,
            })

        # Estimate addition impact (use average product revenue)
        add_items = changes.get('add', [])
        avg_product_revenue = current_revenue / max(current_products, 1)
        addition_revenue = len(add_items) * avg_product_revenue * 0.6  # 60% of avg (new item ramp-up)

        projected_revenue = current_revenue - removal_revenue + addition_revenue
        projected_products = current_products - len(remove_ids) + len(add_items)

        return {
            'simulation_type': 'menu_change',
            'current_state': {
                'total_products': current_products,
                'monthly_revenue': current_revenue,
                'monthly_orders': current_orders,
                'avg_revenue_per_product': round(avg_product_revenue, 2),
            },
            'projected_state': {
                'total_products': projected_products,
                'projected_monthly_revenue': round(projected_revenue, 2),
                'items_to_add': len(add_items),
                'items_to_remove': len(remove_ids),
            },
            'impact': {
                'revenue_impact': round(projected_revenue - current_revenue, 2),
                'revenue_impact_pct': (
                    round((projected_revenue - current_revenue) / current_revenue * 100, 2)
                    if current_revenue > 0 else 0.0
                ),
                'removal_details': removal_details,
                'addition_estimated_revenue': round(addition_revenue, 2),
            },
            'confidence': {
                'level': 'medium',
                'data_points': current_orders,
                'notes': (
                    'New items estimated at 60% of average product revenue '
                    'for ramp-up period. Removal impact based on actual 30-day sales.'
                ),
            },
        }

    def simulate_campaign(
        self,
        org_id: str,
        campaign_params: dict,
    ) -> dict:
        """
        Simulate the impact of running a promotional campaign.

        Args:
            org_id: Organization UUID string
            campaign_params: Dict with campaign details:
                - discount_value: float
                - discount_type: 'PERCENTAGE' or 'FIXED'
                - duration_days: int
                - target_audience_size: int (optional)

        Returns:
            dict with current_state, projected_state, impact, confidence
        """
        from apps.orders.choices import OrderStatus
        from apps.orders.models import Order

        thirty_days_ago = date.today() - timedelta(days=30)

        # Current baseline
        base_qs = Order.objects.filter(
            organization_id=org_id,
            deleted_at__isnull=True,
            status__in=[OrderStatus.COMPLETED, OrderStatus.DELIVERED],
            created_at__date__gte=thirty_days_ago,
        )

        baseline = base_qs.aggregate(
            total_revenue=Sum('total_amount'),
            total_orders=Count('id'),
            avg_order_value=Avg('total_amount'),
            total_customers=Count('customer', distinct=True),
        )

        daily_revenue = _to_float(baseline['total_revenue']) / 30
        daily_orders = (baseline['total_orders'] or 0) / 30
        avg_order = _to_float(baseline['avg_order_value'])

        discount_value = float(campaign_params.get('discount_value', 10))
        discount_type = campaign_params.get('discount_type', 'PERCENTAGE')
        duration_days = int(campaign_params.get('duration_days', 14))

        # Campaign uplift estimate (industry averages)
        order_uplift_pct = 0.20  # 20% more orders during campaign
        avg_discount_per_order = (
            avg_order * (discount_value / 100)
            if discount_type == 'PERCENTAGE'
            else discount_value
        )

        campaign_daily_orders = daily_orders * (1 + order_uplift_pct)
        campaign_daily_revenue = (
            campaign_daily_orders * (avg_order - avg_discount_per_order)
        )

        total_campaign_revenue = campaign_daily_revenue * duration_days
        total_baseline_revenue = daily_revenue * duration_days
        total_discount_cost = avg_discount_per_order * campaign_daily_orders * duration_days
        additional_orders = (campaign_daily_orders - daily_orders) * duration_days

        return {
            'simulation_type': 'campaign',
            'current_state': {
                'daily_revenue': round(daily_revenue, 2),
                'daily_orders': round(daily_orders, 1),
                'avg_order_value': round(avg_order, 2),
                'baseline_period_days': 30,
            },
            'projected_state': {
                'campaign_duration_days': duration_days,
                'projected_daily_orders': round(campaign_daily_orders, 1),
                'projected_daily_revenue': round(campaign_daily_revenue, 2),
                'projected_total_revenue': round(total_campaign_revenue, 2),
                'additional_orders': round(additional_orders, 0),
                'avg_discount_per_order': round(avg_discount_per_order, 2),
            },
            'impact': {
                'revenue_impact': round(total_campaign_revenue - total_baseline_revenue, 2),
                'total_discount_cost': round(total_discount_cost, 2),
                'net_impact': round(
                    total_campaign_revenue - total_baseline_revenue - total_discount_cost, 2
                ),
                'roi_pct': (
                    round(
                        (total_campaign_revenue - total_baseline_revenue - total_discount_cost)
                        / total_discount_cost * 100, 2
                    )
                    if total_discount_cost > 0 else 0.0
                ),
            },
            'confidence': {
                'level': 'medium',
                'data_points': baseline['total_orders'] or 0,
                'notes': (
                    'Assumes 20% order uplift during campaign. '
                    'Actual results depend on campaign execution and market conditions.'
                ),
            },
        }

    def simulate_expansion(
        self,
        org_id: str,
        expansion_params: dict,
    ) -> dict:
        """
        Simulate the impact of opening new branches.

        Args:
            org_id: Organization UUID string
            expansion_params: Dict with:
                - new_branches: int (number of new branches)
                - avg_setup_cost: float (per branch)
                - ramp_up_months: int (months to reach full capacity)

        Returns:
            dict with current_state, projected_state, impact, confidence
        """
        from apps.core.models import Branch
        from apps.orders.choices import OrderStatus
        from apps.orders.models import Order

        thirty_days_ago = date.today() - timedelta(days=30)

        # Current branch performance
        current_branches = Branch.objects.filter(
            organization_id=org_id,
            deleted_at__isnull=True,
            status='ACTIVE',
        ).count()

        current_revenue = _to_float(
            Order.objects.filter(
                organization_id=org_id,
                deleted_at__isnull=True,
                status__in=[OrderStatus.COMPLETED, OrderStatus.DELIVERED],
                created_at__date__gte=thirty_days_ago,
            ).aggregate(rev=Sum('total_amount'))['rev']
        )

        revenue_per_branch = current_revenue / max(current_branches, 1)

        new_branches = int(expansion_params.get('new_branches', 1))
        avg_setup_cost = float(expansion_params.get('avg_setup_cost', 100000))
        ramp_up_months = int(expansion_params.get('ramp_up_months', 6))

        # New branches operate at 50% capacity during ramp-up
        ramp_up_factor = 0.5
        new_branch_monthly_rev = revenue_per_branch * ramp_up_factor
        total_new_revenue_monthly = new_branch_monthly_rev * new_branches
        total_setup_cost = avg_setup_cost * new_branches

        # Break-even estimation
        monthly_operating_cost = avg_setup_cost * 0.08  # ~8% of setup cost as monthly operating
        total_monthly_operating = monthly_operating_cost * new_branches
        net_monthly_revenue = total_new_revenue_monthly - total_monthly_operating

        break_even_months = (
            round(total_setup_cost / net_monthly_revenue)
            if net_monthly_revenue > 0 else None
        )

        return {
            'simulation_type': 'expansion',
            'current_state': {
                'current_branches': current_branches,
                'monthly_revenue': current_revenue,
                'revenue_per_branch': round(revenue_per_branch, 2),
            },
            'projected_state': {
                'total_branches': current_branches + new_branches,
                'new_branches': new_branches,
                'projected_monthly_revenue': round(
                    current_revenue + total_new_revenue_monthly, 2
                ),
                'new_branch_monthly_revenue': round(total_new_revenue_monthly, 2),
                'ramp_up_months': ramp_up_months,
            },
            'impact': {
                'total_setup_cost': round(total_setup_cost, 2),
                'monthly_operating_cost': round(total_monthly_operating, 2),
                'net_monthly_revenue': round(net_monthly_revenue, 2),
                'break_even_months': break_even_months,
                'annual_projected_addition': round(total_new_revenue_monthly * 12, 2),
            },
            'confidence': {
                'level': 'low',
                'data_points': current_branches,
                'notes': (
                    f'Based on average revenue per existing branch ({current_branches}). '
                    f'New branches estimated at 50% capacity during {ramp_up_months}-month ramp-up. '
                    'Location, market conditions, and competition significantly affect outcomes.'
                ),
            },
        }

    def simulate_staffing(
        self,
        org_id: str,
        staffing_changes: dict,
    ) -> dict:
        """
        Simulate the impact of staffing changes.

        Args:
            org_id: Organization UUID string
            staffing_changes: Dict with:
                - add_staff: int (number of new staff)
                - remove_staff: int (number of staff to remove)
                - avg_monthly_cost: float (per staff member)

        Returns:
            dict with current_state, projected_state, impact, confidence
        """
        from apps.core.models import StaffMetric, User

        thirty_days_ago = date.today() - timedelta(days=30)

        # Current staff metrics
        current_staff = User.objects.filter(
            organization_id=org_id,
            deleted_at__isnull=True,
            status='ACTIVE',
        ).count()

        staff_metrics = StaffMetric.objects.filter(
            organization_id=org_id,
            deleted_at__isnull=True,
            date__gte=thirty_days_ago,
        ).aggregate(
            total_revenue=Sum('revenue_generated'),
            total_orders=Sum('orders_handled'),
            avg_service_time=Avg('avg_service_time_seconds'),
            avg_rating=Avg('customer_rating_avg'),
            total_tips=Sum('tips_amount'),
        )

        total_revenue = _to_float(staff_metrics['total_revenue'])
        revenue_per_staff = total_revenue / max(current_staff, 1)
        orders_per_staff = (staff_metrics['total_orders'] or 0) / max(current_staff, 1)

        add_staff = int(staffing_changes.get('add_staff', 0))
        remove_staff = int(staffing_changes.get('remove_staff', 0))
        avg_monthly_cost = float(staffing_changes.get('avg_monthly_cost', 15000))

        new_staff_count = current_staff + add_staff - remove_staff
        new_staff_count = max(new_staff_count, 1)  # At least 1 staff

        # Estimate impact
        # Adding staff: diminishing returns (each new staff adds 70% of avg revenue)
        added_revenue = add_staff * revenue_per_staff * 0.7
        # Removing staff: service degradation (lost revenue = 90% of avg)
        lost_revenue = remove_staff * revenue_per_staff * 0.9

        projected_revenue = total_revenue + added_revenue - lost_revenue
        cost_change = (add_staff - remove_staff) * avg_monthly_cost

        # Service time improvement/degradation
        current_service_time = staff_metrics['avg_service_time'] or 300  # default 5 min
        if new_staff_count > current_staff:
            projected_service_time = current_service_time * (current_staff / new_staff_count)
        elif new_staff_count < current_staff:
            projected_service_time = current_service_time * (current_staff / new_staff_count)
        else:
            projected_service_time = current_service_time

        return {
            'simulation_type': 'staffing',
            'current_state': {
                'current_staff': current_staff,
                'monthly_revenue': total_revenue,
                'revenue_per_staff': round(revenue_per_staff, 2),
                'orders_per_staff': round(orders_per_staff, 1),
                'avg_service_time_seconds': round(current_service_time),
                'avg_rating': _to_float(staff_metrics['avg_rating']),
            },
            'projected_state': {
                'projected_staff': new_staff_count,
                'staff_added': add_staff,
                'staff_removed': remove_staff,
                'projected_monthly_revenue': round(projected_revenue, 2),
                'projected_service_time_seconds': round(projected_service_time),
            },
            'impact': {
                'revenue_impact': round(projected_revenue - total_revenue, 2),
                'cost_impact': round(cost_change, 2),
                'net_impact': round(
                    (projected_revenue - total_revenue) - cost_change, 2
                ),
                'service_time_change_seconds': round(
                    projected_service_time - current_service_time
                ),
            },
            'confidence': {
                'level': 'medium' if current_staff >= 5 else 'low',
                'data_points': current_staff,
                'notes': (
                    'New staff estimated at 70% of average revenue generation. '
                    'Removed staff impact estimated at 90% of their average contribution. '
                    'Service time scaled proportionally to staff count.'
                ),
            },
        }

    def simulate_hours(
        self,
        org_id: str,
        new_hours: dict,
    ) -> dict:
        """
        Simulate the impact of changing operating hours.

        Args:
            org_id: Organization UUID string
            new_hours: Dict with:
                - extend_open_hour: int (e.g., opening 1 hour earlier)
                - extend_close_hour: int (e.g., closing 1 hour later)
                - close_days: list (days to close, e.g., ['Sunday'])

        Returns:
            dict with current_state, projected_state, impact, confidence
        """
        from apps.orders.choices import OrderStatus
        from apps.orders.models import Order
        from django.db.models.functions import ExtractHour, ExtractWeekDay

        thirty_days_ago = date.today() - timedelta(days=30)

        # Base orders queryset
        qs = Order.objects.filter(
            organization_id=org_id,
            deleted_at__isnull=True,
            status__in=[OrderStatus.COMPLETED, OrderStatus.DELIVERED],
            created_at__date__gte=thirty_days_ago,
        )

        # Current hourly distribution
        hourly_dist = dict(
            qs.annotate(hour=ExtractHour('created_at'))
            .values_list('hour')
            .annotate(
                revenue=Sum('total_amount'),
                count=Count('id'),
            )
            .values_list('hour', 'revenue')
        )

        total_revenue = _to_float(qs.aggregate(rev=Sum('total_amount'))['rev'])
        total_orders = qs.count()

        extend_open = int(new_hours.get('extend_open_hour', 0))
        extend_close = int(new_hours.get('extend_close_hour', 0))
        close_days = new_hours.get('close_days', [])

        # Estimate revenue from extended hours
        # Use average of adjacent hours at 50% capacity
        extended_revenue = 0.0
        if extend_open > 0:
            # Opening earlier: use first operating hour revenue at 40%
            earliest_hour_rev = min(
                (_to_float(hourly_dist.get(h, 0)) for h in range(6, 12)),
                default=0.0,
            )
            extended_revenue += earliest_hour_rev * extend_open * 0.4

        if extend_close > 0:
            # Closing later: use last operating hour revenue at 50%
            latest_hour_rev = min(
                (_to_float(hourly_dist.get(h, 0)) for h in range(20, 24)),
                default=0.0,
            )
            extended_revenue += latest_hour_rev * extend_close * 0.5

        # Estimate revenue lost from closing days
        day_map = {
            'Sunday': 1, 'Monday': 2, 'Tuesday': 3,
            'Wednesday': 4, 'Thursday': 5, 'Friday': 6, 'Saturday': 7,
        }
        lost_revenue = 0.0
        for day_name in close_days:
            day_num = day_map.get(day_name)
            if day_num:
                day_rev = _to_float(
                    qs.annotate(weekday=ExtractWeekDay('created_at'))
                    .filter(weekday=day_num)
                    .aggregate(rev=Sum('total_amount'))['rev']
                )
                lost_revenue += day_rev

        projected_revenue = total_revenue + extended_revenue - lost_revenue

        return {
            'simulation_type': 'hours_change',
            'current_state': {
                'monthly_revenue': total_revenue,
                'monthly_orders': total_orders,
                'period_days': 30,
            },
            'projected_state': {
                'projected_monthly_revenue': round(projected_revenue, 2),
                'extend_open_hours': extend_open,
                'extend_close_hours': extend_close,
                'close_days': close_days,
            },
            'impact': {
                'extended_hours_revenue': round(extended_revenue, 2),
                'closed_days_lost_revenue': round(lost_revenue, 2),
                'net_revenue_impact': round(projected_revenue - total_revenue, 2),
                'net_revenue_impact_pct': (
                    round((projected_revenue - total_revenue) / total_revenue * 100, 2)
                    if total_revenue > 0 else 0.0
                ),
            },
            'confidence': {
                'level': 'low',
                'data_points': total_orders,
                'notes': (
                    'Extended opening hours estimated at 40% of first operating hour revenue. '
                    'Extended closing hours estimated at 50% of last operating hour revenue. '
                    'Closed day revenue loss based on actual day-of-week data.'
                ),
            },
        }

    @staticmethod
    def _error_result(message: str) -> dict:
        """Return a standardized error result."""
        return {
            'simulation_type': 'error',
            'current_state': {},
            'projected_state': {},
            'impact': {
                'error': message,
            },
            'confidence': {
                'level': 'none',
                'data_points': 0,
                'notes': message,
            },
        }
