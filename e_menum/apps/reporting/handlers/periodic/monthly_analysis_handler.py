"""
Monthly Analysis Report Handler (RPT-PER-008).

Generates a comprehensive monthly report with 10+ sections covering
revenue, orders, products, customers, daily trends, peak hours,
channel distribution, and month-over-month comparison.

Critical Rules:
    - ALL queries MUST filter by organization_id (multi-tenancy)
    - ALL queries on soft-delete models MUST filter deleted_at__isnull=True
    - Return values must be JSON-serializable (Decimal -> float)
"""

import calendar
import logging
from datetime import date, datetime, timedelta
from typing import List, Optional

from django.db.models import Avg, Count, F, Sum
from django.db.models.functions import ExtractHour, TruncDate

from apps.analytics.choices import Granularity
from apps.analytics.models import SalesAggregation
from apps.customers.models import Customer
from apps.orders.choices import OrderStatus
from apps.orders.models import Order, OrderItem, QRScan
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


@register_handler("RPT-PER-008")
class MonthlyAnalysisHandler(BaseReportHandler):
    """
    Monthly analysis report handler.

    Returns a full monthly report with sections for revenue summary,
    order analysis, product performance, customer metrics, daily trend,
    peak hours, channel distribution, payment distribution, and
    month-over-month comparison.

    Parameters:
        year: int - Year (e.g. 2026)
        month: int - Month (1-12)
        (defaults to previous month)
    """

    feature_key = "RPT-PER-008"

    def get_required_permissions(self) -> List[str]:
        return ["reporting.view"]

    def get_default_parameters(self) -> dict:
        today = date.today()
        if today.month == 1:
            default_year = today.year - 1
            default_month = 12
        else:
            default_year = today.year
            default_month = today.month - 1

        return {
            "year": default_year,
            "month": default_month,
        }

    def validate_parameters(self, parameters: dict) -> dict:
        merged = {**self.get_default_parameters(), **parameters}
        merged["year"] = int(merged["year"])
        merged["month"] = int(merged["month"])

        if merged["month"] < 1 or merged["month"] > 12:
            from shared.utils.exceptions import AppException

            raise AppException(
                code="INVALID_MONTH",
                message="month must be between 1 and 12",
                status_code=400,
            )

        return merged

    def generate(self, org_id: str, parameters: dict) -> dict:
        year = parameters["year"]
        month = parameters["month"]

        start_date = date(year, month, 1)
        last_day = calendar.monthrange(year, month)[1]
        end_date = date(year, month, last_day)

        # Previous month
        if month == 1:
            prev_year, prev_month = year - 1, 12
        else:
            prev_year, prev_month = year, month - 1
        prev_start = date(prev_year, prev_month, 1)
        prev_last_day = calendar.monthrange(prev_year, prev_month)[1]
        prev_end = date(prev_year, prev_month, prev_last_day)

        # 1. Revenue Summary
        revenue_summary = self._revenue_summary(org_id, start_date, end_date)
        prev_revenue = self._revenue_summary(org_id, prev_start, prev_end)

        # 2. Order Analysis
        order_analysis = self._order_analysis(org_id, start_date, end_date)
        prev_orders = self._order_analysis(org_id, prev_start, prev_end)

        # 3. Product Performance (top 10)
        product_performance = self._product_performance(org_id, start_date, end_date)

        # 4. Customer Metrics
        customer_metrics = self._customer_metrics(org_id, start_date, end_date)
        prev_customers = self._customer_metrics(org_id, prev_start, prev_end)

        # 5. Daily Trend
        daily_trend = self._daily_trend(org_id, start_date, end_date)

        # 6. Peak Hours
        peak_hours = self._peak_hours(org_id, start_date, end_date)

        # 7. Channel Distribution (by order type)
        channel_distribution = self._channel_distribution(org_id, start_date, end_date)

        # 8. Payment Distribution
        payment_distribution = self._payment_distribution(org_id, start_date, end_date)

        # 9. QR Scan Summary
        qr_summary = self._qr_scan_summary(org_id, start_date, end_date)

        # 10. Week-by-week breakdown
        weekly_breakdown = self._weekly_breakdown(org_id, start_date, end_date)

        # 11. Category performance
        category_performance = self._category_performance(org_id, start_date, end_date)

        # Build comparison
        comparison = self._build_comparison(
            revenue_summary,
            prev_revenue,
            order_analysis,
            prev_orders,
            customer_metrics,
            prev_customers,
            prev_start,
            prev_end,
        )

        return {
            "month": {
                "year": year,
                "month": month,
                "month_name": calendar.month_name[month],
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "total_days": last_day,
            },
            "revenue_summary": revenue_summary,
            "order_analysis": order_analysis,
            "product_performance": product_performance,
            "customer_metrics": customer_metrics,
            "daily_trend": daily_trend,
            "peak_hours": peak_hours,
            "channel_distribution": channel_distribution,
            "payment_distribution": payment_distribution,
            "qr_scan_summary": qr_summary,
            "weekly_breakdown": weekly_breakdown,
            "category_performance": category_performance,
            "comparison_to_previous_month": comparison,
        }

    # ------------------------------------------------------------------
    # Section builders
    # ------------------------------------------------------------------

    def _revenue_summary(self, org_id: str, start: date, end: date) -> dict:
        """Revenue summary with breakdown."""
        qs = Order.objects.filter(
            organization_id=org_id,
            deleted_at__isnull=True,
            created_at__date__gte=start,
            created_at__date__lte=end,
            status__in=[OrderStatus.COMPLETED, OrderStatus.DELIVERED],
        )

        agg = qs.aggregate(
            total_revenue=Sum("total_amount"),
            subtotal=Sum("subtotal"),
            total_tax=Sum("tax_amount"),
            total_discount=Sum("discount_amount"),
            total_refund=Sum("refund_amount"),
            total_tips=Sum("tip_amount"),
        )

        total = _to_float(agg["total_revenue"])
        discount = _to_float(agg["total_discount"])
        refund = _to_float(agg["total_refund"])
        days = (end - start).days + 1

        return {
            "total_revenue": total,
            "subtotal": _to_float(agg["subtotal"]),
            "net_revenue": total - discount - refund,
            "total_tax": _to_float(agg["total_tax"]),
            "total_discount": discount,
            "total_refund": refund,
            "total_tips": _to_float(agg["total_tips"]),
            "avg_daily_revenue": round(total / max(days, 1), 2),
        }

    def _order_analysis(self, org_id: str, start: date, end: date) -> dict:
        """Order analysis with status breakdown."""
        all_qs = Order.objects.filter(
            organization_id=org_id,
            deleted_at__isnull=True,
            created_at__date__gte=start,
            created_at__date__lte=end,
        )

        total = all_qs.count()
        completed = all_qs.filter(
            status__in=[OrderStatus.COMPLETED, OrderStatus.DELIVERED],
        ).count()
        cancelled = all_qs.filter(status=OrderStatus.CANCELLED).count()

        completed_agg = all_qs.filter(
            status__in=[OrderStatus.COMPLETED, OrderStatus.DELIVERED],
        ).aggregate(
            avg_order_value=Avg("total_amount"),
            avg_items_per_order=Avg("items__quantity"),
        )

        status_breakdown = list(
            all_qs.values("status").annotate(count=Count("id")).order_by("status")
        )

        return {
            "total_orders": total,
            "completed_orders": completed,
            "cancelled_orders": cancelled,
            "completion_rate": round(
                (completed / total * 100) if total > 0 else 0,
                2,
            ),
            "cancellation_rate": round(
                (cancelled / total * 100) if total > 0 else 0,
                2,
            ),
            "avg_order_value": _to_float(completed_agg["avg_order_value"]),
            "avg_items_per_order": _to_float(completed_agg["avg_items_per_order"]),
            "orders_by_status": [
                {"status": row["status"], "count": row["count"]}
                for row in status_breakdown
            ],
        }

    def _product_performance(
        self,
        org_id: str,
        start: date,
        end: date,
        limit: int = 10,
    ) -> List[dict]:
        """Top performing products for the month."""
        rows = (
            OrderItem.objects.filter(
                order__organization_id=org_id,
                order__deleted_at__isnull=True,
                deleted_at__isnull=True,
                order__status__in=[OrderStatus.COMPLETED, OrderStatus.DELIVERED],
                order__created_at__date__gte=start,
                order__created_at__date__lte=end,
            )
            .values(
                product_name=F("product__name"),
                product_id_val=F("product__id"),
                category_name=F("product__category__name"),
            )
            .annotate(
                qty_sold=Sum("quantity"),
                revenue=Sum("total_price"),
                avg_price=Avg("unit_price"),
                order_count=Count("order", distinct=True),
            )
            .order_by("-revenue")[:limit]
        )

        total_rev = _to_float(
            OrderItem.objects.filter(
                order__organization_id=org_id,
                order__deleted_at__isnull=True,
                deleted_at__isnull=True,
                order__status__in=[OrderStatus.COMPLETED, OrderStatus.DELIVERED],
                order__created_at__date__gte=start,
                order__created_at__date__lte=end,
            ).aggregate(t=Sum("total_price"))["t"]
        )

        return [
            {
                "rank": i + 1,
                "product_id": str(row["product_id_val"])
                if row["product_id_val"]
                else None,
                "product_name": row["product_name"] or "Unknown",
                "category_name": row["category_name"] or "Uncategorized",
                "qty_sold": row["qty_sold"] or 0,
                "revenue": _to_float(row["revenue"]),
                "avg_price": _to_float(row["avg_price"]),
                "order_count": row["order_count"] or 0,
                "revenue_share_percent": round(
                    (_to_float(row["revenue"]) / total_rev * 100)
                    if total_rev > 0
                    else 0,
                    2,
                ),
            }
            for i, row in enumerate(rows)
        ]

    def _customer_metrics(self, org_id: str, start: date, end: date) -> dict:
        """Customer metrics for the month."""
        total = Customer.objects.filter(
            organization_id=org_id,
            deleted_at__isnull=True,
        ).count()

        new = Customer.objects.filter(
            organization_id=org_id,
            deleted_at__isnull=True,
            created_at__date__gte=start,
            created_at__date__lte=end,
        ).count()

        # Unique ordering customers
        unique_ordering = (
            Order.objects.filter(
                organization_id=org_id,
                deleted_at__isnull=True,
                customer__isnull=False,
                created_at__date__gte=start,
                created_at__date__lte=end,
            )
            .values("customer")
            .distinct()
            .count()
        )

        # Returning customers (ordered more than once in the month)
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
            .annotate(oc=Count("id"))
            .filter(oc__gt=1)
            .count()
        )

        # Avg LTV
        avg_ltv = Customer.objects.filter(
            organization_id=org_id,
            deleted_at__isnull=True,
        ).aggregate(avg=Avg("lifetime_value"))["avg"]

        # Segment distribution
        segments = list(
            Customer.objects.filter(
                organization_id=org_id,
                deleted_at__isnull=True,
            )
            .exclude(rfm_segment__isnull=True)
            .exclude(rfm_segment="")
            .values("rfm_segment")
            .annotate(count=Count("id"))
            .order_by("-count")
        )

        return {
            "total_customers": total,
            "new_customers": new,
            "unique_ordering_customers": unique_ordering,
            "returning_customers": returning,
            "avg_lifetime_value": _to_float(avg_ltv),
            "segment_distribution": [
                {"segment": s["rfm_segment"], "count": s["count"]} for s in segments
            ],
        }

    def _daily_trend(self, org_id: str, start: date, end: date) -> List[dict]:
        """Daily revenue and order trend for the month."""
        # Try SalesAggregation
        agg_rows = list(
            SalesAggregation.objects.filter(
                organization_id=org_id,
                deleted_at__isnull=True,
                granularity=Granularity.DAILY,
                date__gte=start,
                date__lte=end,
            )
            .values("date")
            .annotate(
                revenue=Sum("gross_revenue"),
                orders=Sum("order_count"),
                customers=Sum("customer_count"),
            )
            .order_by("date")
        )

        if agg_rows:
            return [
                {
                    "date": row["date"].isoformat()
                    if isinstance(row["date"], date)
                    else str(row["date"]),
                    "revenue": _to_float(row["revenue"]),
                    "orders": row["orders"] or 0,
                    "customers": row["customers"] or 0,
                }
                for row in agg_rows
            ]

        # Fallback: Order table
        rows = list(
            Order.objects.filter(
                organization_id=org_id,
                deleted_at__isnull=True,
                created_at__date__gte=start,
                created_at__date__lte=end,
                status__in=[OrderStatus.COMPLETED, OrderStatus.DELIVERED],
            )
            .annotate(dt=TruncDate("created_at"))
            .values("dt")
            .annotate(
                revenue=Sum("total_amount"),
                orders=Count("id"),
                customers=Count("customer", distinct=True),
            )
            .order_by("dt")
        )

        return [
            {
                "date": row["dt"].isoformat() if row["dt"] else None,
                "revenue": _to_float(row["revenue"]),
                "orders": row["orders"] or 0,
                "customers": row["customers"] or 0,
            }
            for row in rows
        ]

    def _peak_hours(self, org_id: str, start: date, end: date) -> List[dict]:
        """Peak hours by order count and revenue."""
        rows = list(
            Order.objects.filter(
                organization_id=org_id,
                deleted_at__isnull=True,
                created_at__date__gte=start,
                created_at__date__lte=end,
            )
            .annotate(hour=ExtractHour("created_at"))
            .values("hour")
            .annotate(
                order_count=Count("id"),
                revenue=Sum("total_amount"),
                avg_order_value=Avg("total_amount"),
            )
            .order_by("hour")
        )

        return [
            {
                "hour": row["hour"],
                "order_count": row["order_count"],
                "revenue": _to_float(row["revenue"]),
                "avg_order_value": _to_float(row["avg_order_value"]),
            }
            for row in rows
        ]

    def _channel_distribution(self, org_id: str, start: date, end: date) -> List[dict]:
        """Order distribution by channel (order type)."""
        qs = Order.objects.filter(
            organization_id=org_id,
            deleted_at__isnull=True,
            created_at__date__gte=start,
            created_at__date__lte=end,
        )
        total = qs.count()

        rows = list(
            qs.values("type")
            .annotate(
                count=Count("id"),
                revenue=Sum("total_amount"),
                avg_ov=Avg("total_amount"),
            )
            .order_by("-count")
        )

        return [
            {
                "channel": row["type"],
                "order_count": row["count"],
                "revenue": _to_float(row["revenue"]),
                "avg_order_value": _to_float(row["avg_ov"]),
                "share_percent": round(
                    (row["count"] / total * 100) if total > 0 else 0,
                    2,
                ),
            }
            for row in rows
        ]

    def _payment_distribution(self, org_id: str, start: date, end: date) -> List[dict]:
        """Payment method distribution."""
        qs = Order.objects.filter(
            organization_id=org_id,
            deleted_at__isnull=True,
            created_at__date__gte=start,
            created_at__date__lte=end,
            status__in=[OrderStatus.COMPLETED, OrderStatus.DELIVERED],
        )
        total = qs.count()

        rows = list(
            qs.values("payment_method")
            .annotate(
                count=Count("id"),
                revenue=Sum("total_amount"),
            )
            .order_by("-count")
        )

        return [
            {
                "payment_method": row["payment_method"] or "UNKNOWN",
                "order_count": row["count"],
                "revenue": _to_float(row["revenue"]),
                "share_percent": round(
                    (row["count"] / total * 100) if total > 0 else 0,
                    2,
                ),
            }
            for row in rows
        ]

    def _qr_scan_summary(self, org_id: str, start: date, end: date) -> dict:
        """QR scan summary for the month."""
        qs = QRScan.objects.filter(
            organization_id=org_id,
            scanned_at__date__gte=start,
            scanned_at__date__lte=end,
        )

        total_scans = qs.count()
        unique_visitors = qs.values("session_id").distinct().count()
        days = (end - start).days + 1

        device_distribution = list(
            qs.exclude(device_type__isnull=True)
            .exclude(device_type="")
            .values("device_type")
            .annotate(count=Count("id"))
            .order_by("-count")
        )

        return {
            "total_scans": total_scans,
            "unique_visitors": unique_visitors,
            "avg_daily_scans": round(total_scans / max(days, 1), 1),
            "device_distribution": [
                {
                    "device_type": row["device_type"],
                    "count": row["count"],
                    "percent": round(
                        (row["count"] / total_scans * 100) if total_scans > 0 else 0,
                        2,
                    ),
                }
                for row in device_distribution
            ],
        }

    def _weekly_breakdown(self, org_id: str, start: date, end: date) -> List[dict]:
        """Week-by-week breakdown within the month."""
        weeks = []
        current = start

        # Find the start of each week within the month
        while current <= end:
            week_start = current
            week_end = min(current + timedelta(days=6 - current.weekday()), end)

            qs = Order.objects.filter(
                organization_id=org_id,
                deleted_at__isnull=True,
                created_at__date__gte=week_start,
                created_at__date__lte=week_end,
                status__in=[OrderStatus.COMPLETED, OrderStatus.DELIVERED],
            )

            agg = qs.aggregate(
                revenue=Sum("total_amount"),
                orders=Count("id"),
                avg_ov=Avg("total_amount"),
            )

            weeks.append(
                {
                    "week_start": week_start.isoformat(),
                    "week_end": week_end.isoformat(),
                    "week_number": week_start.isocalendar()[1],
                    "revenue": _to_float(agg["revenue"]),
                    "order_count": agg["orders"] or 0,
                    "avg_order_value": _to_float(agg["avg_ov"]),
                }
            )

            # Move to next Monday
            current = week_end + timedelta(days=1)

        return weeks

    def _category_performance(
        self,
        org_id: str,
        start: date,
        end: date,
    ) -> List[dict]:
        """Revenue and quantity by category."""
        rows = (
            OrderItem.objects.filter(
                order__organization_id=org_id,
                order__deleted_at__isnull=True,
                deleted_at__isnull=True,
                order__status__in=[OrderStatus.COMPLETED, OrderStatus.DELIVERED],
                order__created_at__date__gte=start,
                order__created_at__date__lte=end,
            )
            .values(
                category_name=F("product__category__name"),
                category_id_val=F("product__category__id"),
            )
            .annotate(
                revenue=Sum("total_price"),
                qty=Sum("quantity"),
                product_count=Count("product", distinct=True),
            )
            .order_by("-revenue")
        )

        total_rev = _to_float(
            OrderItem.objects.filter(
                order__organization_id=org_id,
                order__deleted_at__isnull=True,
                deleted_at__isnull=True,
                order__status__in=[OrderStatus.COMPLETED, OrderStatus.DELIVERED],
                order__created_at__date__gte=start,
                order__created_at__date__lte=end,
            ).aggregate(t=Sum("total_price"))["t"]
        )

        return [
            {
                "category_id": str(row["category_id_val"])
                if row["category_id_val"]
                else None,
                "category_name": row["category_name"] or "Uncategorized",
                "revenue": _to_float(row["revenue"]),
                "quantity_sold": row["qty"] or 0,
                "unique_products": row["product_count"] or 0,
                "revenue_share_percent": round(
                    (_to_float(row["revenue"]) / total_rev * 100)
                    if total_rev > 0
                    else 0,
                    2,
                ),
            }
            for row in rows
        ]

    def _build_comparison(
        self,
        revenue: dict,
        prev_revenue: dict,
        orders: dict,
        prev_orders: dict,
        customers: dict,
        prev_customers: dict,
        prev_start: date,
        prev_end: date,
    ) -> dict:
        """Build month-over-month comparison."""
        return {
            "previous_month": {
                "start_date": prev_start.isoformat(),
                "end_date": prev_end.isoformat(),
            },
            "revenue": {
                "current": revenue["total_revenue"],
                "previous": prev_revenue["total_revenue"],
                "change_percent": _safe_percent_change(
                    revenue["total_revenue"],
                    prev_revenue["total_revenue"],
                ),
            },
            "orders": {
                "current": orders["total_orders"],
                "previous": prev_orders["total_orders"],
                "change_percent": _safe_percent_change(
                    float(orders["total_orders"]),
                    float(prev_orders["total_orders"]),
                ),
            },
            "avg_order_value": {
                "current": orders["avg_order_value"],
                "previous": prev_orders["avg_order_value"],
                "change_percent": _safe_percent_change(
                    orders["avg_order_value"],
                    prev_orders["avg_order_value"],
                ),
            },
            "new_customers": {
                "current": customers["new_customers"],
                "previous": prev_customers["new_customers"],
                "change_percent": _safe_percent_change(
                    float(customers["new_customers"]),
                    float(prev_customers["new_customers"]),
                ),
            },
            "completion_rate": {
                "current": orders["completion_rate"],
                "previous": prev_orders["completion_rate"],
                "change_percent": _safe_percent_change(
                    orders["completion_rate"],
                    prev_orders["completion_rate"],
                ),
            },
        }
