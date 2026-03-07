"""
Tenant Growth Report Handler (RPT-PLT-001).

Platform-level report showing organization (tenant) growth metrics,
registration trends, plan distribution, and churn data. This handler
does NOT filter by organization_id since it is a platform-level report.

Critical Rules:
    - This is a PLATFORM-LEVEL report - no org_id filtering
    - Only accessible by platform admins (super_admin, admin)
    - ALL queries on soft-delete models MUST filter deleted_at__isnull=True
    - Return values must be JSON-serializable (Decimal -> float)
"""

import logging
from datetime import date, datetime, timedelta
from typing import List, Optional

from django.db.models import Count
from django.db.models.functions import TruncDate, TruncMonth, TruncWeek

from apps.reporting.services.report_engine import BaseReportHandler, register_handler

logger = logging.getLogger(__name__)


def _parse_date(val) -> Optional[date]:
    """Parse a date string (YYYY-MM-DD) or return date object as-is."""
    if val is None:
        return None
    if isinstance(val, date):
        return val
    if isinstance(val, datetime):
        return val.date()
    return datetime.strptime(str(val), "%Y-%m-%d").date()


@register_handler("RPT-PLT-001")
class TenantGrowthHandler(BaseReportHandler):
    """
    Platform tenant growth report handler.

    Shows organization sign-up trends, status distribution, plan
    breakdown, trial conversion rate, and churn metrics.

    Note: This is a PLATFORM-level report. The org_id parameter
    is ignored. Only platform admin users should access this.

    Parameters:
        start_date: str - Start date in YYYY-MM-DD format
        end_date: str - End date in YYYY-MM-DD format
        period: str - Grouping period: DAILY, WEEKLY, MONTHLY (default: MONTHLY)
    """

    feature_key = "RPT-PLT-001"

    def get_required_permissions(self) -> List[str]:
        return ["platform.admin", "reporting.view"]

    def get_default_parameters(self) -> dict:
        today = date.today()
        return {
            "start_date": (today - timedelta(days=365)).isoformat(),
            "end_date": today.isoformat(),
            "period": "MONTHLY",
        }

    def validate_parameters(self, parameters: dict) -> dict:
        merged = {**self.get_default_parameters(), **parameters}

        merged["start_date"] = _parse_date(merged["start_date"])
        merged["end_date"] = _parse_date(merged["end_date"])

        if merged["start_date"] > merged["end_date"]:
            from shared.utils.exceptions import AppException

            raise AppException(
                code="INVALID_DATE_RANGE",
                message="start_date must be before or equal to end_date",
                status_code=400,
            )

        valid_periods = ["DAILY", "WEEKLY", "MONTHLY"]
        if merged["period"] not in valid_periods:
            from shared.utils.exceptions import AppException

            raise AppException(
                code="INVALID_PERIOD",
                message=f"period must be one of {valid_periods}",
                status_code=400,
            )

        return merged

    def generate(self, org_id: str, parameters: dict) -> dict:
        """
        Generate platform tenant growth report.

        Note: org_id is ignored for platform-level reports.
        """
        from apps.core.models import Organization

        start_date = parameters["start_date"]
        end_date = parameters["end_date"]
        period = parameters["period"]

        # ---- Overall tenant counts ----
        all_orgs = Organization.objects.filter(deleted_at__isnull=True)

        status_distribution = list(
            all_orgs.values("status").annotate(count=Count("id")).order_by("status")
        )

        total_tenants = sum(s["count"] for s in status_distribution)
        active_tenants = next(
            (s["count"] for s in status_distribution if s["status"] == "ACTIVE"), 0
        )

        # ---- New registrations in period ----
        period_orgs = all_orgs.filter(
            created_at__date__gte=start_date,
            created_at__date__lte=end_date,
        )

        new_registrations = period_orgs.count()

        # ---- Registration trend ----
        if period == "DAILY":
            trunc_func = TruncDate("created_at")
            group_key = "date"
        elif period == "WEEKLY":
            trunc_func = TruncWeek("created_at")
            group_key = "week"
        else:
            trunc_func = TruncMonth("created_at")
            group_key = "month"

        trend_rows = list(
            period_orgs.annotate(**{group_key: trunc_func})
            .values(group_key)
            .annotate(count=Count("id"))
            .order_by(group_key)
        )

        trend_data = []
        for row in trend_rows:
            dt_val = row[group_key]
            if isinstance(dt_val, (date, datetime)):
                dt_str = (
                    dt_val.isoformat()
                    if isinstance(dt_val, date)
                    else dt_val.date().isoformat()
                )
            else:
                dt_str = str(dt_val)
            trend_data.append(
                {
                    "date": dt_str,
                    "new_tenants": row["count"],
                }
            )

        # ---- Churn (soft-deleted organizations) in period ----
        churned = Organization.all_objects.filter(
            deleted_at__isnull=False,
            deleted_at__date__gte=start_date,
            deleted_at__date__lte=end_date,
        ).count()

        suspended = Organization.all_objects.filter(
            status="SUSPENDED",
            updated_at__date__gte=start_date,
            updated_at__date__lte=end_date,
        ).count()

        # ---- Trial metrics ----
        from django.utils import timezone

        now = timezone.now()

        on_trial = all_orgs.filter(
            trial_ends_at__isnull=False,
            trial_ends_at__gt=now,
        ).count()

        trial_expired = all_orgs.filter(
            trial_ends_at__isnull=False,
            trial_ends_at__lte=now,
        ).count()

        # ---- Growth rate calculation ----
        period_length = (end_date - start_date).days + 1
        prev_end = start_date - timedelta(days=1)
        prev_start = prev_end - timedelta(days=period_length - 1)

        prev_new = all_orgs.filter(
            created_at__date__gte=prev_start,
            created_at__date__lte=prev_end,
        ).count()

        if prev_new > 0:
            growth_rate_pct = round(
                ((new_registrations - prev_new) / prev_new) * 100, 2
            )
        elif new_registrations > 0:
            growth_rate_pct = 100.0
        else:
            growth_rate_pct = 0.0

        # ---- Net growth (new minus churned) ----
        net_growth = new_registrations - churned

        return {
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "grouping": period,
            },
            "overview": {
                "total_tenants": total_tenants,
                "active_tenants": active_tenants,
                "new_registrations": new_registrations,
                "churned": churned,
                "suspended": suspended,
                "net_growth": net_growth,
                "growth_rate_pct": growth_rate_pct,
            },
            "status_distribution": status_distribution,
            "trial_metrics": {
                "currently_on_trial": on_trial,
                "trial_expired": trial_expired,
            },
            "trend": trend_data,
            "comparison": {
                "previous_period": {
                    "start_date": prev_start.isoformat(),
                    "end_date": prev_end.isoformat(),
                },
                "previous_new_registrations": prev_new,
            },
        }
