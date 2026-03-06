import logging
from datetime import timedelta
from decimal import Decimal

from django.db.models import Count, Sum
from django.utils import timezone

logger = logging.getLogger(__name__)


class OwnerKPIService:
    """Organization-scoped KPI metrics for the restaurant owner dashboard."""

    def __init__(self, organization):
        self.organization = organization

    # ── Public API ──────────────────────────────────────────────

    def get_all_kpis(self):
        """Return all 6 KPI cards with values, trends, and changes."""
        return {
            "qr_scans": self._build_kpi(
                label="QR Tarama",
                icon="ph-qr-code",
                value=self.get_today_qr_scans(),
                trend=self.get_trend("qr_scans"),
                change=self.get_period_change("qr_scans"),
            ),
            "active_menus": self._build_kpi(
                label="Aktif Menu",
                icon="ph-book-open",
                value=self.get_active_menus(),
                trend=self.get_trend("active_menus"),
                change=self.get_period_change("active_menus"),
            ),
            "total_products": self._build_kpi(
                label="Urun",
                icon="ph-fork-knife",
                value=self.get_total_products(),
                trend=self.get_trend("total_products"),
                change=self.get_period_change("total_products"),
            ),
            "pending_orders": self._build_kpi(
                label="Bekleyen Siparis",
                icon="ph-clock",
                value=self.get_pending_orders(),
                trend=self.get_trend("pending_orders"),
                change=self.get_period_change("pending_orders"),
            ),
            "today_revenue": self._build_kpi(
                label="Gunluk Gelir",
                icon="ph-currency-circle-dollar",
                value=float(self.get_today_revenue()),
                trend=self.get_trend("revenue"),
                change=self.get_period_change("revenue"),
                format="currency",
            ),
            "total_customers": self._build_kpi(
                label="Musteri",
                icon="ph-users",
                value=self.get_total_customers(),
                trend=self.get_trend("total_customers"),
                change=self.get_period_change("total_customers"),
            ),
        }

    # ── Individual metric methods ──────────────────────────────

    def get_today_qr_scans(self):
        try:
            from apps.orders.models import QRScan

            today = timezone.now().date()
            return QRScan.objects.filter(
                organization=self.organization,
                scanned_at__date=today,
            ).count()
        except Exception:
            logger.debug("Could not fetch QR scan count", exc_info=True)
            return 0

    def get_active_menus(self):
        try:
            from apps.menu.models import Menu

            return Menu.objects.filter(
                organization=self.organization,
                is_published=True,
                deleted_at__isnull=True,
            ).count()
        except Exception:
            logger.debug("Could not fetch active menu count", exc_info=True)
            return 0

    def get_total_products(self):
        try:
            from apps.menu.models import Product

            return Product.objects.filter(
                organization=self.organization,
                is_active=True,
                deleted_at__isnull=True,
            ).count()
        except Exception:
            logger.debug("Could not fetch product count", exc_info=True)
            return 0

    def get_pending_orders(self):
        try:
            from apps.orders.models import Order

            return Order.objects.filter(
                organization=self.organization,
                status="PENDING",
                deleted_at__isnull=True,
            ).count()
        except Exception:
            logger.debug("Could not fetch pending order count", exc_info=True)
            return 0

    def get_today_revenue(self):
        try:
            from apps.orders.models import Order

            today = timezone.now().date()
            result = Order.objects.filter(
                organization=self.organization,
                status="COMPLETED",
                completed_at__date=today,
                deleted_at__isnull=True,
            ).aggregate(total=Sum("total_amount"))
            return result["total"] or Decimal("0")
        except Exception:
            logger.debug("Could not fetch today revenue", exc_info=True)
            return Decimal("0")

    def get_total_customers(self):
        try:
            from apps.customers.models import Customer

            return Customer.objects.filter(
                organization=self.organization,
                deleted_at__isnull=True,
            ).count()
        except Exception:
            logger.debug("Could not fetch customer count", exc_info=True)
            return 0

    # ── Trend data (7-day sparkline) ───────────────────────────

    def get_trend(self, metric_key, days=7):
        """Return daily values for the last *days* days (for sparkline charts)."""
        today = timezone.now().date()
        values = []
        for i in range(days - 1, -1, -1):
            day = today - timedelta(days=i)
            values.append(self._get_daily_value(metric_key, day))
        return values

    def _get_daily_value(self, metric_key, day):
        """Get a single day's value for the given metric."""
        try:
            if metric_key == "qr_scans":
                from apps.orders.models import QRScan

                return QRScan.objects.filter(
                    organization=self.organization,
                    scanned_at__date=day,
                ).count()

            elif metric_key == "revenue":
                from apps.orders.models import Order

                result = Order.objects.filter(
                    organization=self.organization,
                    status="COMPLETED",
                    completed_at__date=day,
                    deleted_at__isnull=True,
                ).aggregate(total=Sum("total_amount"))
                return float(result["total"] or 0)

            elif metric_key == "pending_orders":
                from apps.orders.models import Order

                return Order.objects.filter(
                    organization=self.organization,
                    status="PENDING",
                    created_at__date=day,
                    deleted_at__isnull=True,
                ).count()

            elif metric_key in ("active_menus", "total_products", "total_customers"):
                # Cumulative metrics -- no meaningful daily delta available.
                return 0
        except Exception:
            logger.debug(
                "Could not fetch daily value for %s on %s",
                metric_key,
                day,
                exc_info=True,
            )
        return 0

    # ── Period comparison (week-over-week change) ──────────────

    def get_period_change(self, metric_key):
        """Calculate week-over-week percentage change."""
        today = timezone.now().date()
        this_week_start = today - timedelta(days=6)
        last_week_start = this_week_start - timedelta(days=7)
        last_week_end = this_week_start - timedelta(days=1)

        this_week = self._get_period_total(metric_key, this_week_start, today)
        last_week = self._get_period_total(metric_key, last_week_start, last_week_end)

        if last_week == 0:
            return 100.0 if this_week > 0 else 0.0
        return ((this_week - last_week) / last_week) * 100

    def _get_period_total(self, metric_key, start_date, end_date):
        """Get total value for a date range."""
        try:
            if metric_key == "qr_scans":
                from apps.orders.models import QRScan

                return QRScan.objects.filter(
                    organization=self.organization,
                    scanned_at__date__gte=start_date,
                    scanned_at__date__lte=end_date,
                ).count()

            elif metric_key == "revenue":
                from apps.orders.models import Order

                result = Order.objects.filter(
                    organization=self.organization,
                    status="COMPLETED",
                    completed_at__date__gte=start_date,
                    completed_at__date__lte=end_date,
                    deleted_at__isnull=True,
                ).aggregate(total=Sum("total_amount"))
                return float(result["total"] or 0)

            elif metric_key == "pending_orders":
                from apps.orders.models import Order

                return Order.objects.filter(
                    organization=self.organization,
                    created_at__date__gte=start_date,
                    created_at__date__lte=end_date,
                    deleted_at__isnull=True,
                ).count()
        except Exception:
            logger.debug(
                "Could not fetch period total for %s (%s - %s)",
                metric_key,
                start_date,
                end_date,
                exc_info=True,
            )
        return 0

    # ── Chart data methods ─────────────────────────────────────

    def get_qr_scan_trend(self, days=30):
        """Daily QR scan counts for line chart."""
        today = timezone.now().date()
        dates = []
        values = []
        for i in range(days - 1, -1, -1):
            day = today - timedelta(days=i)
            dates.append(day.isoformat())
            try:
                from apps.orders.models import QRScan

                count = QRScan.objects.filter(
                    organization=self.organization,
                    scanned_at__date=day,
                ).count()
                values.append(count)
            except Exception:
                values.append(0)
        return {"dates": dates, "values": values}

    def get_revenue_trend(self, days=30):
        """Daily revenue for bar chart."""
        today = timezone.now().date()
        dates = []
        values = []
        for i in range(days - 1, -1, -1):
            day = today - timedelta(days=i)
            dates.append(day.isoformat())
            try:
                from apps.orders.models import Order

                result = Order.objects.filter(
                    organization=self.organization,
                    status="COMPLETED",
                    completed_at__date=day,
                    deleted_at__isnull=True,
                ).aggregate(total=Sum("total_amount"))
                values.append(float(result["total"] or 0))
            except Exception:
                values.append(0)
        return {"dates": dates, "values": values}

    def get_order_status_distribution(self):
        """Order counts by status for donut chart."""
        try:
            from apps.orders.models import Order

            qs = (
                Order.objects.filter(
                    organization=self.organization,
                    deleted_at__isnull=True,
                )
                .values("status")
                .annotate(count=Count("id"))
            )
            return {item["status"]: item["count"] for item in qs}
        except Exception:
            logger.debug("Could not fetch order status distribution", exc_info=True)
            return {}

    def get_top_products(self, limit=10):
        """Top products by order count."""
        try:
            from apps.orders.models import OrderItem

            qs = (
                OrderItem.objects.filter(
                    order__organization=self.organization,
                    order__deleted_at__isnull=True,
                    deleted_at__isnull=True,
                )
                .values("product__name")
                .annotate(
                    total_orders=Count("id"),
                    total_quantity=Sum("quantity"),
                )
                .order_by("-total_orders")[:limit]
            )
            return list(qs)
        except Exception:
            logger.debug("Could not fetch top products", exc_info=True)
            return []

    def get_recent_orders(self, limit=10):
        """Most recent orders for the activity table."""
        try:
            from apps.orders.models import Order

            orders = (
                Order.objects.filter(
                    organization=self.organization,
                    deleted_at__isnull=True,
                )
                .select_related("table")
                .order_by("-created_at")[:limit]
            )
            return [
                {
                    "id": str(o.id),
                    "order_number": o.order_number,
                    "status": o.status,
                    "type": o.type,
                    "total_amount": float(o.total_amount) if o.total_amount else 0,
                    "customer_name": o.customer_name or "-",
                    "table_name": o.table.name if o.table else "-",
                    "created_at": o.created_at.isoformat() if o.created_at else "",
                }
                for o in orders
            ]
        except Exception:
            logger.debug("Could not fetch recent orders", exc_info=True)
            return []

    # ── Internal helpers ───────────────────────────────────────

    @staticmethod
    def _build_kpi(label, icon, value, trend, change, format=None):
        return {
            "label": label,
            "icon": icon,
            "value": value,
            "trend": trend,
            "change": round(change, 1),
            "format": format,
        }
