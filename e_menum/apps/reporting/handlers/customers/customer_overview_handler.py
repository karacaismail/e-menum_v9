"""
Customer Overview Report Handler (RPT-CUS-001).

Generates customer overview metrics including total, new, and returning
customer counts, average lifetime value, RFM segment distribution,
and top customers by spending.

Critical Rules:
    - ALL queries MUST filter by organization_id (multi-tenancy)
    - ALL queries on soft-delete models MUST filter deleted_at__isnull=True
    - Return values must be JSON-serializable (Decimal -> float)
"""

import logging
from datetime import date, datetime, timedelta
from typing import List, Optional

from django.db.models import Avg, Count, F, Sum
from django.db.models.functions import TruncDate

from apps.analytics.models import CustomerMetric
from apps.customers.models import Customer
from apps.orders.choices import OrderStatus
from apps.orders.models import Order
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
    return datetime.strptime(str(val), "%Y-%m-%d").date()


def _safe_percent_change(current: float, previous: float) -> Optional[float]:
    if previous == 0:
        return 0.0 if current == 0 else None
    return round(((current - previous) / previous) * 100, 2)


@register_handler("RPT-CUS-001")
class CustomerOverviewHandler(BaseReportHandler):
    """
    Customer overview report handler.

    Returns total customers, new vs returning customers, average lifetime
    value, RFM segment distribution, and top customers by spending.

    Parameters:
        period: str - DAILY, WEEKLY, or MONTHLY
        start_date: str - Start date in YYYY-MM-DD format
        end_date: str - End date in YYYY-MM-DD format
    """

    feature_key = "RPT-CUS-001"

    def get_required_permissions(self) -> List[str]:
        return ["reporting.view", "customers.view"]

    def get_default_parameters(self) -> dict:
        today = date.today()
        return {
            "period": "MONTHLY",
            "start_date": (today - timedelta(days=30)).isoformat(),
            "end_date": today.isoformat(),
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

        return merged

    def generate(self, org_id: str, parameters: dict) -> dict:
        start_date = parameters["start_date"]
        end_date = parameters["end_date"]

        # ---- Customer base metrics ----
        all_customers_qs = Customer.objects.filter(
            organization_id=org_id,
            deleted_at__isnull=True,
        )

        total_customers = all_customers_qs.count()

        # New customers in the period (created_at within range)
        new_customers_qs = all_customers_qs.filter(
            created_at__date__gte=start_date,
            created_at__date__lte=end_date,
        )
        new_customers = new_customers_qs.count()

        # Returning customers: those who placed >1 order in the period
        returning_customers = self._count_returning_customers(
            org_id,
            start_date,
            end_date,
        )

        # ---- Lifetime value statistics ----
        ltv_stats = all_customers_qs.aggregate(
            avg_lifetime_value=Avg("lifetime_value"),
            avg_total_spent=Avg("total_spent"),
            avg_total_orders=Avg("total_orders"),
        )

        # ---- RFM Segment distribution ----
        segment_distribution = list(
            all_customers_qs.exclude(rfm_segment__isnull=True)
            .exclude(rfm_segment="")
            .values("rfm_segment")
            .annotate(count=Count("id"))
            .order_by("-count")
        )

        segment_total = sum(s["count"] for s in segment_distribution)
        segments = [
            {
                "segment": row["rfm_segment"],
                "count": row["count"],
                "percent": round(
                    (row["count"] / segment_total * 100) if segment_total > 0 else 0,
                    2,
                ),
            }
            for row in segment_distribution
        ]

        # ---- Top customers by spending in the period ----
        top_customers = self._get_top_customers(org_id, start_date, end_date)

        # ---- New customers daily trend ----
        new_customer_trend = list(
            new_customers_qs.annotate(dt=TruncDate("created_at"))
            .values("dt")
            .annotate(count=Count("id"))
            .order_by("dt")
        )

        # ---- Previous period comparison ----
        period_length = (end_date - start_date).days + 1
        prev_end = start_date - timedelta(days=1)
        prev_start = prev_end - timedelta(days=period_length - 1)

        prev_new = Customer.objects.filter(
            organization_id=org_id,
            deleted_at__isnull=True,
            created_at__date__gte=prev_start,
            created_at__date__lte=prev_end,
        ).count()

        prev_returning = self._count_returning_customers(
            org_id,
            prev_start,
            prev_end,
        )

        # ---- Try CustomerMetric for enriched data ----
        latest_metric = (
            CustomerMetric.objects.filter(
                organization_id=org_id,
                deleted_at__isnull=True,
                date__lte=end_date,
            )
            .order_by("-date")
            .first()
        )

        nps_score = None
        churn_count = 0
        avg_visit_frequency = None
        if latest_metric:
            nps_score = (
                _to_float(latest_metric.nps_score) if latest_metric.nps_score else None
            )
            churn_count = latest_metric.churn_count or 0
            avg_visit_frequency = (
                _to_float(latest_metric.avg_visit_frequency)
                if latest_metric.avg_visit_frequency
                else None
            )

        return {
            "period": {
                "type": parameters["period"],
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
            },
            "metrics": {
                "total_customers": total_customers,
                "new_customers": new_customers,
                "returning_customers": returning_customers,
                "avg_lifetime_value": _to_float(ltv_stats["avg_lifetime_value"]),
                "avg_total_spent": _to_float(ltv_stats["avg_total_spent"]),
                "avg_orders_per_customer": _to_float(ltv_stats["avg_total_orders"]),
                "nps_score": nps_score,
                "churn_count": churn_count,
                "avg_visit_frequency": avg_visit_frequency,
            },
            "comparison": {
                "previous_period": {
                    "start_date": prev_start.isoformat(),
                    "end_date": prev_end.isoformat(),
                },
                "new_customers": prev_new,
                "returning_customers": prev_returning,
                "new_customers_change_percent": _safe_percent_change(
                    float(new_customers),
                    float(prev_new),
                ),
                "returning_customers_change_percent": _safe_percent_change(
                    float(returning_customers),
                    float(prev_returning),
                ),
            },
            "segment_distribution": segments,
            "top_customers": top_customers,
            "new_customer_trend": [
                {
                    "date": row["dt"].isoformat() if row["dt"] else None,
                    "count": row["count"],
                }
                for row in new_customer_trend
            ],
        }

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _count_returning_customers(
        self,
        org_id: str,
        start: date,
        end: date,
    ) -> int:
        """
        Count customers who placed more than one order in the given period.
        """
        from django.db.models import Count as DjangoCount

        returning = (
            Order.objects.filter(
                organization_id=org_id,
                deleted_at__isnull=True,
                customer__isnull=False,
                status__in=[OrderStatus.COMPLETED, OrderStatus.DELIVERED],
                created_at__date__gte=start,
                created_at__date__lte=end,
            )
            .values("customer")
            .annotate(order_count=DjangoCount("id"))
            .filter(order_count__gt=1)
        )
        return returning.count()

    def _get_top_customers(
        self,
        org_id: str,
        start: date,
        end: date,
        limit: int = 10,
    ) -> List[dict]:
        """
        Return top customers by total spending in the period.
        """
        rows = (
            Order.objects.filter(
                organization_id=org_id,
                deleted_at__isnull=True,
                customer__isnull=False,
                customer__deleted_at__isnull=True,
                status__in=[OrderStatus.COMPLETED, OrderStatus.DELIVERED],
                created_at__date__gte=start,
                created_at__date__lte=end,
            )
            .values(
                customer_id=F("customer__id"),
                customer_name=F("customer__name"),
                customer_email=F("customer__email"),
                rfm=F("customer__rfm_segment"),
            )
            .annotate(
                total_spent=Sum("total_amount"),
                order_count=Count("id"),
                avg_order_value=Avg("total_amount"),
            )
            .order_by("-total_spent")[:limit]
        )

        return [
            {
                "customer_id": str(row["customer_id"]),
                "name": row["customer_name"] or "Unknown",
                "email": row["customer_email"],
                "rfm_segment": row["rfm"],
                "total_spent": _to_float(row["total_spent"]),
                "order_count": row["order_count"],
                "avg_order_value": _to_float(row["avg_order_value"]),
            }
            for row in rows
        ]
