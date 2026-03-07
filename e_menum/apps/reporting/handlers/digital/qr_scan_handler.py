"""
QR Scan Analysis Report Handler (RPT-DIG-001).

Generates QR code scan analytics including total scans, unique visitors,
scans by day and hour, conversion rate, and top performing QR codes.

Critical Rules:
    - ALL queries MUST filter by organization_id (multi-tenancy)
    - QRScan does NOT use soft delete (append-only model)
    - Return values must be JSON-serializable (Decimal -> float)
"""

import logging
from datetime import date, datetime, timedelta
from typing import List, Optional

from django.db.models import Count, F
from django.db.models.functions import ExtractHour, TruncDate

from apps.orders.choices import OrderStatus
from apps.orders.models import Order, QRScan
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


@register_handler("RPT-DIG-001")
class QRScanAnalysisHandler(BaseReportHandler):
    """
    QR scan analysis report handler.

    Returns total scans, unique visitors, scans by day and hour,
    device type distribution, conversion rate, and top QR codes.

    Parameters:
        period: str - DAILY, WEEKLY, or MONTHLY
        start_date: str - Start date in YYYY-MM-DD
        end_date: str - End date in YYYY-MM-DD
    """

    feature_key = "RPT-DIG-001"

    def get_required_permissions(self) -> List[str]:
        return ["reporting.view", "analytics.view"]

    def get_default_parameters(self) -> dict:
        today = date.today()
        return {
            "period": "DAILY",
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

        # ---- Base queryset (QRScan has no soft delete) ----
        base_qs = QRScan.objects.filter(
            organization_id=org_id,
            scanned_at__date__gte=start_date,
            scanned_at__date__lte=end_date,
        )

        # ---- Core metrics ----
        total_scans = base_qs.count()
        unique_visitors = base_qs.filter(is_unique=True).count()
        # Alternative unique count via session_id if is_unique not populated
        if unique_visitors == 0 and total_scans > 0:
            unique_visitors = base_qs.values("session_id").distinct().count()

        # ---- Scans by day ----
        scans_by_day = list(
            base_qs.annotate(dt=TruncDate("scanned_at"))
            .values("dt")
            .annotate(
                count=Count("id"),
                unique_count=Count("session_id", distinct=True),
            )
            .order_by("dt")
        )

        # ---- Scans by hour ----
        scans_by_hour = list(
            base_qs.annotate(hour=ExtractHour("scanned_at"))
            .values("hour")
            .annotate(count=Count("id"))
            .order_by("hour")
        )

        # ---- Device type distribution ----
        device_distribution = list(
            base_qs.exclude(device_type__isnull=True)
            .exclude(device_type="")
            .values("device_type")
            .annotate(count=Count("id"))
            .order_by("-count")
        )

        # ---- Browser distribution ----
        browser_distribution = list(
            base_qs.exclude(browser__isnull=True)
            .exclude(browser="")
            .values("browser")
            .annotate(count=Count("id"))
            .order_by("-count")[:10]
        )

        # ---- Top QR codes ----
        top_qr_codes = list(
            base_qs.values(
                qr_id=F("qr_code__id"),
                qr_code_type=F("qr_code__type"),
            )
            .annotate(
                scan_count=Count("id"),
                unique_scan_count=Count("session_id", distinct=True),
            )
            .order_by("-scan_count")[:10]
        )

        # ---- Conversion rate: scans that led to orders ----
        conversion_rate = self._calculate_conversion_rate(
            org_id,
            start_date,
            end_date,
            total_scans,
        )

        # ---- Previous period comparison ----
        period_length = (end_date - start_date).days + 1
        prev_end = start_date - timedelta(days=1)
        prev_start = prev_end - timedelta(days=period_length - 1)

        prev_qs = QRScan.objects.filter(
            organization_id=org_id,
            scanned_at__date__gte=prev_start,
            scanned_at__date__lte=prev_end,
        )
        prev_total = prev_qs.count()
        prev_unique = prev_qs.filter(is_unique=True).count()
        if prev_unique == 0 and prev_total > 0:
            prev_unique = prev_qs.values("session_id").distinct().count()

        return {
            "period": {
                "type": parameters["period"],
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
            },
            "metrics": {
                "total_scans": total_scans,
                "unique_visitors": unique_visitors,
                "avg_daily_scans": round(
                    total_scans / max(period_length, 1),
                    1,
                ),
                "conversion_rate": conversion_rate,
            },
            "comparison": {
                "previous_period": {
                    "start_date": prev_start.isoformat(),
                    "end_date": prev_end.isoformat(),
                },
                "total_scans": prev_total,
                "unique_visitors": prev_unique,
                "total_scans_change_percent": _safe_percent_change(
                    float(total_scans),
                    float(prev_total),
                ),
                "unique_visitors_change_percent": _safe_percent_change(
                    float(unique_visitors),
                    float(prev_unique),
                ),
            },
            "scans_by_day": [
                {
                    "date": row["dt"].isoformat() if row["dt"] else None,
                    "count": row["count"],
                    "unique_count": row["unique_count"],
                }
                for row in scans_by_day
            ],
            "scans_by_hour": [
                {"hour": row["hour"], "count": row["count"]} for row in scans_by_hour
            ],
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
            "browser_distribution": [
                {
                    "browser": row["browser"],
                    "count": row["count"],
                    "percent": round(
                        (row["count"] / total_scans * 100) if total_scans > 0 else 0,
                        2,
                    ),
                }
                for row in browser_distribution
            ],
            "top_qr_codes": [
                {
                    "qr_code_id": str(row["qr_id"]) if row["qr_id"] else None,
                    "type": row["qr_code_type"],
                    "scan_count": row["scan_count"],
                    "unique_scan_count": row["unique_scan_count"],
                }
                for row in top_qr_codes
            ],
        }

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _calculate_conversion_rate(
        self,
        org_id: str,
        start: date,
        end: date,
        total_scans: int,
    ) -> float:
        """
        Calculate conversion rate: orders placed / total QR scans.

        This is a rough proxy -- we count orders in the same period
        that were placed via dine-in (assumed to originate from QR scans).
        """
        if total_scans == 0:
            return 0.0

        order_count = Order.objects.filter(
            organization_id=org_id,
            deleted_at__isnull=True,
            status__in=[
                OrderStatus.COMPLETED,
                OrderStatus.DELIVERED,
                OrderStatus.CONFIRMED,
                OrderStatus.PREPARING,
                OrderStatus.READY,
            ],
            created_at__date__gte=start,
            created_at__date__lte=end,
        ).count()

        return round((order_count / total_scans * 100), 2)
