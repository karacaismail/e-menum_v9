"""
Campaign Performance Report Handler (RPT-CMP-001).

Generates campaign performance overview reports showing active
campaigns, coupon usage metrics, ROI analysis, and referral stats.
Queries Campaign, Coupon, CouponUsage, and Referral models.

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
from django.db.models.functions import TruncDate

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


def _safe_percent_change(current: float, previous: float) -> Optional[float]:
    """Calculate percentage change, handling division by zero."""
    if previous == 0:
        if current == 0:
            return 0.0
        return None
    return round(((current - previous) / previous) * 100, 2)


@register_handler('RPT-CMP-001')
class CampaignPerformanceHandler(BaseReportHandler):
    """
    Campaign performance overview handler.

    Provides campaign summary metrics, per-campaign performance,
    coupon usage analytics, referral stats, and daily trend data.

    Parameters:
        start_date: str - Start date in YYYY-MM-DD format
        end_date: str - End date in YYYY-MM-DD format
        campaign_type: str - Optional filter by campaign type
        status: str - Optional filter by campaign status
    """

    feature_key = 'RPT-CMP-001'

    def get_required_permissions(self) -> List[str]:
        return ['reporting.view', 'campaign.view']

    def get_default_parameters(self) -> dict:
        today = date.today()
        return {
            'start_date': (today - timedelta(days=30)).isoformat(),
            'end_date': today.isoformat(),
            'campaign_type': None,
            'status': None,
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
        from apps.campaigns.models import Campaign, Coupon, CouponUsage, Referral

        start_date = parameters['start_date']
        end_date = parameters['end_date']
        campaign_type = parameters.get('campaign_type')
        status_filter = parameters.get('status')

        # ---- Campaign summary ----
        campaign_qs = Campaign.objects.filter(
            organization_id=org_id,
            deleted_at__isnull=True,
        )

        if campaign_type:
            campaign_qs = campaign_qs.filter(campaign_type=campaign_type)
        if status_filter:
            campaign_qs = campaign_qs.filter(status=status_filter)

        campaign_summary = campaign_qs.aggregate(
            total_campaigns=Count('id'),
            active_campaigns=Count('id', filter=Q(status='ACTIVE')),
            total_budget=Sum('budget'),
            total_spent=Sum('spent_amount'),
            total_usage=Sum('usage_count'),
        )

        # ---- Per-campaign performance (top 20) ----
        campaigns_data = list(
            campaign_qs.filter(
                start_date__date__lte=end_date,
                end_date__date__gte=start_date,
            )
            .values(
                'id', 'name', 'campaign_type', 'status',
                'budget', 'spent_amount', 'usage_count',
                'discount_value', 'discount_type',
                'start_date', 'end_date',
            )
            .order_by('-usage_count')[:20]
        )

        for c in campaigns_data:
            c['id'] = str(c['id'])
            c['budget'] = _to_float(c['budget'])
            c['spent_amount'] = _to_float(c['spent_amount'])
            c['discount_value'] = _to_float(c['discount_value'])
            c['budget_utilization_pct'] = (
                round(c['spent_amount'] / c['budget'] * 100, 2)
                if c['budget'] > 0 else 0.0
            )
            # Convert datetimes to ISO strings
            if c['start_date']:
                c['start_date'] = c['start_date'].isoformat()
            if c['end_date']:
                c['end_date'] = c['end_date'].isoformat()

        # ---- Coupon usage metrics ----
        coupon_qs = CouponUsage.objects.filter(
            organization_id=org_id,
            used_at__date__gte=start_date,
            used_at__date__lte=end_date,
        )

        coupon_metrics = coupon_qs.aggregate(
            total_redemptions=Count('id'),
            total_discount_given=Sum('discount_applied'),
            avg_discount=Avg('discount_applied'),
        )

        # Coupon usage trend (daily)
        coupon_trend = list(
            coupon_qs
            .annotate(dt=TruncDate('used_at'))
            .values('dt')
            .annotate(
                redemptions=Count('id'),
                discount_total=Sum('discount_applied'),
            )
            .order_by('dt')
        )

        for row in coupon_trend:
            row['date'] = row.pop('dt').isoformat()
            row['discount_total'] = _to_float(row['discount_total'])

        # ---- Active coupons summary ----
        active_coupons = Coupon.objects.filter(
            organization_id=org_id,
            deleted_at__isnull=True,
            is_active=True,
        ).aggregate(
            total_active=Count('id'),
            total_used=Sum('used_count'),
        )

        # ---- Referral stats ----
        referral_qs = Referral.objects.filter(
            organization_id=org_id,
            deleted_at__isnull=True,
            created_at__date__gte=start_date,
            created_at__date__lte=end_date,
        )

        referral_stats = referral_qs.aggregate(
            total_referrals=Count('id'),
            completed_referrals=Count('id', filter=Q(is_completed=True)),
            total_reward_value=Sum(
                'reward_value', filter=Q(is_completed=True),
            ),
        )

        return {
            'period': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
            },
            'campaign_summary': {
                'total_campaigns': campaign_summary['total_campaigns'] or 0,
                'active_campaigns': campaign_summary['active_campaigns'] or 0,
                'total_budget': _to_float(campaign_summary['total_budget']),
                'total_spent': _to_float(campaign_summary['total_spent']),
                'total_usage': campaign_summary['total_usage'] or 0,
                'budget_utilization_pct': (
                    round(
                        _to_float(campaign_summary['total_spent'])
                        / _to_float(campaign_summary['total_budget']) * 100, 2
                    )
                    if campaign_summary['total_budget'] and campaign_summary['total_budget'] > 0
                    else 0.0
                ),
            },
            'campaigns': campaigns_data,
            'coupon_metrics': {
                'total_redemptions': coupon_metrics['total_redemptions'] or 0,
                'total_discount_given': _to_float(coupon_metrics['total_discount_given']),
                'avg_discount': _to_float(coupon_metrics['avg_discount']),
                'active_coupons': active_coupons['total_active'] or 0,
                'total_coupon_uses': active_coupons['total_used'] or 0,
            },
            'coupon_trend': coupon_trend,
            'referral_stats': {
                'total_referrals': referral_stats['total_referrals'] or 0,
                'completed_referrals': referral_stats['completed_referrals'] or 0,
                'total_reward_value': _to_float(referral_stats['total_reward_value']),
                'conversion_rate_pct': (
                    round(
                        (referral_stats['completed_referrals'] or 0)
                        / (referral_stats['total_referrals'] or 1) * 100, 2
                    )
                    if referral_stats['total_referrals']
                    else 0.0
                ),
            },
        }
