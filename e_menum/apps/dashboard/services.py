"""
KPI Service for E-Menum Dashboard.

Provides cached access to platform-wide KPI metrics.
All methods read from Redis first (5-min TTL).
On cache miss, queries the database and writes to Redis.

Performance target: <200ms per method call.

Usage:
    service = KPIService()
    orgs = service.get_active_organizations()
    scans = service.get_today_qr_scans()
"""

import json
import logging
from datetime import timedelta
from decimal import Decimal
from typing import Any, Optional

from django.core.cache import cache
from django.db.models import Count, Sum
from django.db.models.functions import Coalesce
from django.utils import timezone

logger = logging.getLogger(__name__)

# Cache TTL: 5 minutes
CACHE_TTL = 300

# Cache key prefix
CACHE_PREFIX = "dashboard:kpi:"


class DecimalEncoder(json.JSONEncoder):
    """JSON encoder that handles Decimal types."""

    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super().default(obj)


class KPIService:
    """
    Platform-wide KPI metrics service with Redis caching.

    Every get_* method follows the pattern:
    1. Check Redis cache (key = dashboard:kpi:{metric})
    2. If hit → return cached value
    3. If miss → query DB, write to cache, return

    All methods are safe to call without Redis (fallback to DB query).
    """

    def _cache_key(self, metric: str, suffix: str = "") -> str:
        """Build a cache key for the given metric."""
        key = f"{CACHE_PREFIX}{metric}"
        if suffix:
            key += f":{suffix}"
        return key

    def _get_cached(self, key: str) -> Optional[Any]:
        """Try to get a value from cache."""
        try:
            val = cache.get(key)
            if val is not None:
                return val
        except Exception as exc:
            logger.warning("Redis cache read failed for %s: %s", key, exc)
        return None

    def _set_cached(self, key: str, value: Any, ttl: int = CACHE_TTL):
        """Write a value to cache."""
        try:
            cache.set(key, value, ttl)
        except Exception as exc:
            logger.warning("Redis cache write failed for %s: %s", key, exc)

    # ─── KPI Methods ──────────────────────────────────────────────

    def get_active_organizations(self) -> int:
        """
        Count of active organizations (status=ACTIVE, not deleted).

        Source: core.Organization
        """
        key = self._cache_key("active_organizations")
        cached = self._get_cached(key)
        if cached is not None:
            return cached

        from apps.core.choices import OrganizationStatus
        from apps.core.models import Organization

        count = Organization.objects.filter(
            status=OrganizationStatus.ACTIVE,
            deleted_at__isnull=True,
        ).count()

        self._set_cached(key, count)
        return count

    def get_today_qr_scans(self) -> int:
        """
        Count of QR scans today.

        Source: orders.QRScan (created_at__date = today)
        """
        key = self._cache_key("today_qr_scans")
        cached = self._get_cached(key)
        if cached is not None:
            return cached

        from apps.orders.models import QRScan

        today = timezone.localdate()
        count = QRScan.objects.filter(
            created_at__date=today,
        ).count()

        self._set_cached(key, count)
        return count

    def get_active_menus(self) -> int:
        """
        Count of published menus (is_published=True, not deleted).

        Source: menu.Menu
        """
        key = self._cache_key("active_menus")
        cached = self._get_cached(key)
        if cached is not None:
            return cached

        from apps.menu.models import Menu

        count = Menu.objects.filter(
            is_published=True,
            deleted_at__isnull=True,
        ).count()

        self._set_cached(key, count)
        return count

    def get_pending_service_requests(self) -> int:
        """
        Count of pending service requests.

        Source: orders.ServiceRequest (status='PENDING')
        """
        key = self._cache_key("pending_service_requests")
        cached = self._get_cached(key)
        if cached is not None:
            return cached

        from apps.orders.models import ServiceRequest

        count = ServiceRequest.objects.filter(
            status="PENDING",
            deleted_at__isnull=True,
        ).count()

        self._set_cached(key, count)
        return count

    def get_mrr(self) -> float:
        """
        Monthly Recurring Revenue from active monthly subscriptions.

        Source: subscriptions.Subscription
        (status=ACTIVE, billing_period=MONTHLY)
        """
        key = self._cache_key("mrr")
        cached = self._get_cached(key)
        if cached is not None:
            return cached

        from apps.subscriptions.choices import BillingPeriod, SubscriptionStatus
        from apps.subscriptions.models import Subscription

        result = Subscription.objects.filter(
            status=SubscriptionStatus.ACTIVE,
            billing_period=BillingPeriod.MONTHLY,
            deleted_at__isnull=True,
        ).aggregate(
            total=Coalesce(
                Sum("current_price"),
                Decimal("0"),
            ),
        )

        mrr = float(result["total"])

        # Also add yearly subscriptions divided by 12
        yearly_result = Subscription.objects.filter(
            status=SubscriptionStatus.ACTIVE,
            billing_period=BillingPeriod.YEARLY,
            deleted_at__isnull=True,
        ).aggregate(
            total=Coalesce(
                Sum("current_price"),
                Decimal("0"),
            ),
        )
        mrr += float(yearly_result["total"]) / 12

        self._set_cached(key, round(mrr, 2))
        return round(mrr, 2)

    def get_trial_count(self) -> int:
        """
        Count of subscriptions currently in trial.

        Source: subscriptions.Subscription (status=TRIALING)
        """
        key = self._cache_key("trial_count")
        cached = self._get_cached(key)
        if cached is not None:
            return cached

        from apps.subscriptions.choices import SubscriptionStatus
        from apps.subscriptions.models import Subscription

        count = Subscription.objects.filter(
            status=SubscriptionStatus.TRIALING,
            deleted_at__isnull=True,
        ).count()

        self._set_cached(key, count)
        return count

    # ─── Trend & Comparison ───────────────────────────────────────

    def get_trend(self, metric_key: str, days: int = 7) -> list:
        """
        Get daily values for the past N days for sparkline rendering.

        Supported metric_keys:
        - 'qr_scans': Daily QR scan counts
        - 'organizations': Daily new org registrations
        - 'orders': Daily order counts
        - 'revenue': Daily revenue

        Returns a list of int/float values, one per day (oldest first).
        """
        key = self._cache_key(f"trend:{metric_key}", f"{days}d")
        cached = self._get_cached(key)
        if cached is not None:
            return cached

        today = timezone.localdate()
        start_date = today - timedelta(days=days - 1)
        result = []

        if metric_key == "qr_scans":
            from apps.orders.models import QRScan

            for i in range(days):
                d = start_date + timedelta(days=i)
                count = QRScan.objects.filter(created_at__date=d).count()
                result.append(count)

        elif metric_key == "organizations":
            from apps.core.models import Organization

            for i in range(days):
                d = start_date + timedelta(days=i)
                count = Organization.objects.filter(
                    created_at__date=d,
                    deleted_at__isnull=True,
                ).count()
                result.append(count)

        elif metric_key == "orders":
            from apps.orders.models import Order

            for i in range(days):
                d = start_date + timedelta(days=i)
                count = Order.objects.filter(
                    placed_at__date=d,
                    deleted_at__isnull=True,
                ).count()
                result.append(count)

        elif metric_key == "revenue":
            from apps.analytics.models import SalesAggregation

            for i in range(days):
                d = start_date + timedelta(days=i)
                agg = SalesAggregation.objects.filter(
                    date=d,
                    granularity="DAILY",
                ).aggregate(
                    total=Coalesce(Sum("gross_revenue"), Decimal("0")),
                )
                result.append(float(agg["total"]))

        elif metric_key == "menus":
            from apps.menu.models import Menu

            for i in range(days):
                d = start_date + timedelta(days=i)
                count = Menu.objects.filter(
                    created_at__date=d,
                    deleted_at__isnull=True,
                ).count()
                result.append(count)

        elif metric_key == "service_requests":
            from apps.orders.models import ServiceRequest

            for i in range(days):
                d = start_date + timedelta(days=i)
                count = ServiceRequest.objects.filter(
                    created_at__date=d,
                    deleted_at__isnull=True,
                ).count()
                result.append(count)

        else:
            result = [0] * days

        self._set_cached(key, result)
        return result

    def get_period_comparison(self, metric_key: str) -> dict:
        """
        Compare this week vs last week for a given metric.

        Returns:
            {
                'current': int/float,
                'previous': int/float,
                'change': float (percentage),
            }
        """
        key = self._cache_key(f"comparison:{metric_key}")
        cached = self._get_cached(key)
        if cached is not None:
            return cached

        today = timezone.localdate()
        week_start = today - timedelta(days=today.weekday())
        prev_week_start = week_start - timedelta(days=7)
        prev_week_end = week_start - timedelta(days=1)

        current = 0
        previous = 0

        if metric_key == "qr_scans":
            from apps.orders.models import QRScan

            current = QRScan.objects.filter(
                created_at__date__gte=week_start,
                created_at__date__lte=today,
            ).count()
            previous = QRScan.objects.filter(
                created_at__date__gte=prev_week_start,
                created_at__date__lte=prev_week_end,
            ).count()

        elif metric_key == "organizations":
            from apps.core.models import Organization

            current = Organization.objects.filter(
                created_at__date__gte=week_start,
                created_at__date__lte=today,
                deleted_at__isnull=True,
            ).count()
            previous = Organization.objects.filter(
                created_at__date__gte=prev_week_start,
                created_at__date__lte=prev_week_end,
                deleted_at__isnull=True,
            ).count()

        elif metric_key == "orders":
            from apps.orders.models import Order

            current = Order.objects.filter(
                placed_at__date__gte=week_start,
                placed_at__date__lte=today,
                deleted_at__isnull=True,
            ).count()
            previous = Order.objects.filter(
                placed_at__date__gte=prev_week_start,
                placed_at__date__lte=prev_week_end,
                deleted_at__isnull=True,
            ).count()

        elif metric_key == "revenue":
            from apps.analytics.models import SalesAggregation

            c_agg = SalesAggregation.objects.filter(
                date__gte=week_start,
                date__lte=today,
                granularity="DAILY",
            ).aggregate(total=Coalesce(Sum("gross_revenue"), Decimal("0")))
            current = float(c_agg["total"])

            p_agg = SalesAggregation.objects.filter(
                date__gte=prev_week_start,
                date__lte=prev_week_end,
                granularity="DAILY",
            ).aggregate(total=Coalesce(Sum("gross_revenue"), Decimal("0")))
            previous = float(p_agg["total"])

        elif metric_key in ("menus", "active_menus"):
            from apps.menu.models import Menu

            current = Menu.objects.filter(
                created_at__date__gte=week_start,
                created_at__date__lte=today,
                deleted_at__isnull=True,
            ).count()
            previous = Menu.objects.filter(
                created_at__date__gte=prev_week_start,
                created_at__date__lte=prev_week_end,
                deleted_at__isnull=True,
            ).count()

        elif metric_key in ("service_requests", "pending_service_requests"):
            from apps.orders.models import ServiceRequest

            current = ServiceRequest.objects.filter(
                created_at__date__gte=week_start,
                created_at__date__lte=today,
                deleted_at__isnull=True,
            ).count()
            previous = ServiceRequest.objects.filter(
                created_at__date__gte=prev_week_start,
                created_at__date__lte=prev_week_end,
                deleted_at__isnull=True,
            ).count()

        # Calculate percentage change
        if previous > 0:
            change = round(((current - previous) / previous) * 100, 1)
        elif current > 0:
            change = 100.0
        else:
            change = 0.0

        result = {
            "current": current,
            "previous": previous,
            "change": change,
        }

        self._set_cached(key, result)
        return result

    # ─── QR Scan Trend (range-based) ──────────────────────────────

    def get_qr_scan_trend(self, days: int = 30) -> dict:
        """
        Daily QR scan counts for chart rendering.

        Returns:
            {
                'dates': ['2026-01-25', ...],
                'values': [42, 55, ...],
                'total': int,
            }
        """
        key = self._cache_key("qr_scan_trend", f"{days}d")
        cached = self._get_cached(key)
        if cached is not None:
            return cached

        from apps.orders.models import QRScan

        today = timezone.localdate()
        start_date = today - timedelta(days=days - 1)

        dates = []
        values = []
        total = 0

        for i in range(days):
            d = start_date + timedelta(days=i)
            count = QRScan.objects.filter(created_at__date=d).count()
            dates.append(d.isoformat())
            values.append(count)
            total += count

        result = {"dates": dates, "values": values, "total": total}
        self._set_cached(key, result)
        return result

    # ─── Organization Activity Heatmap ────────────────────────────

    def get_org_activity_heatmap(self) -> list:
        """
        Last 12 weeks: org × day activity matrix.
        Top 20 most active organizations.

        Returns list of:
            {
                'org_id': str,
                'org_name': str,
                'data': [[week_idx, day_of_week, count], ...]
            }
        """
        key = self._cache_key("org_activity_heatmap")
        cached = self._get_cached(key)
        if cached is not None:
            return cached

        from apps.orders.models import QRScan

        today = timezone.localdate()
        start_date = today - timedelta(weeks=12)

        # Top 20 orgs by scan volume
        top_orgs = (
            QRScan.objects.filter(
                created_at__date__gte=start_date,
                qr_code__organization__isnull=False,
            )
            .values("qr_code__organization_id", "qr_code__organization__name")
            .annotate(total=Count("id"))
            .order_by("-total")[:20]
        )

        result = []
        for org in top_orgs:
            org_id = str(org["qr_code__organization_id"])
            org_name = org["qr_code__organization__name"] or "Unknown"

            # Get daily counts for this org
            daily = (
                QRScan.objects.filter(
                    created_at__date__gte=start_date,
                    qr_code__organization_id=org["qr_code__organization_id"],
                )
                .values("created_at__date")
                .annotate(count=Count("id"))
            )

            # Convert to week/day matrix
            data = []
            for row in daily:
                d = row["created_at__date"]
                week_idx = (d - start_date).days // 7
                day_of_week = d.weekday()
                data.append([week_idx, day_of_week, row["count"]])

            result.append(
                {
                    "org_id": org_id,
                    "org_name": org_name[:20],  # Truncate for display
                    "data": data,
                }
            )

        self._set_cached(key, result)
        return result

    # ─── Plan Distribution ────────────────────────────────────────

    def get_plan_distribution(self) -> list:
        """
        Organization count per subscription plan tier.

        Returns:
            [{'name': 'Starter', 'value': 120}, ...]
        """
        key = self._cache_key("plan_distribution")
        cached = self._get_cached(key)
        if cached is not None:
            return cached

        from apps.subscriptions.choices import SubscriptionStatus
        from apps.subscriptions.models import Subscription

        dist = (
            Subscription.objects.filter(
                status__in=[
                    SubscriptionStatus.ACTIVE,
                    SubscriptionStatus.TRIALING,
                ],
                deleted_at__isnull=True,
            )
            .values("plan__name")
            .annotate(count=Count("id"))
            .order_by("-count")
        )

        result = [
            {"name": row["plan__name"] or "Unknown", "value": row["count"]}
            for row in dist
        ]

        self._set_cached(key, result)
        return result

    # ─── City Distribution ────────────────────────────────────────

    def get_city_distribution(self) -> list:
        """
        Organization count by city (from Branch model).

        Returns:
            [{'city': 'Istanbul', 'count': 145, 'lat': 41.0, 'lng': 28.9}, ...]
        """
        key = self._cache_key("city_distribution")
        cached = self._get_cached(key)
        if cached is not None:
            return cached

        from apps.core.models import Branch

        # Major Turkish cities with approximate coordinates
        CITY_COORDS = {
            "istanbul": (41.0082, 28.9784),
            "ankara": (39.9334, 32.8597),
            "izmir": (38.4237, 27.1428),
            "bursa": (40.1885, 29.0610),
            "antalya": (36.8969, 30.7133),
            "adana": (37.0000, 35.3213),
            "konya": (37.8746, 32.4932),
            "gaziantep": (37.0662, 37.3833),
            "mersin": (36.8121, 34.6415),
            "kayseri": (38.7312, 35.4787),
            "eskisehir": (39.7767, 30.5206),
            "diyarbakir": (37.9144, 40.2306),
            "samsun": (41.2867, 36.3300),
            "trabzon": (41.0027, 39.7168),
            "denizli": (37.7765, 29.0864),
            "mugla": (37.2153, 28.3636),
            "bodrum": (37.0344, 27.4305),
        }

        dist = (
            Branch.objects.filter(
                deleted_at__isnull=True,
                city__isnull=False,
                organization__deleted_at__isnull=True,
            )
            .values("city")
            .annotate(count=Count("organization_id", distinct=True))
            .order_by("-count")[:30]
        )

        result = []
        for row in dist:
            city = row["city"]
            city_lower = city.lower().replace("İ", "i").replace("ı", "i")
            lat, lng = CITY_COORDS.get(city_lower, (39.0, 35.0))
            result.append(
                {
                    "city": city,
                    "count": row["count"],
                    "lat": lat,
                    "lng": lng,
                }
            )

        self._set_cached(key, result)
        return result

    # ─── Subscription Funnel ──────────────────────────────────────

    def get_subscription_funnel(self) -> list:
        """
        Conversion funnel: Registration → Trial → Active → Renewal.

        Returns:
            [{'step': 'Registration', 'count': 500}, ...]
        """
        key = self._cache_key("subscription_funnel")
        cached = self._get_cached(key)
        if cached is not None:
            return cached

        from apps.core.models import Organization
        from apps.subscriptions.choices import SubscriptionStatus
        from apps.subscriptions.models import Subscription

        # Step 1: Total organizations (registrations)
        total_orgs = Organization.objects.filter(
            deleted_at__isnull=True,
        ).count()

        # Step 2: Organizations that started a trial
        trial_ever = (
            Subscription.objects.filter(
                deleted_at__isnull=True,
            )
            .values("organization_id")
            .distinct()
            .count()
        )

        # Step 3: Active subscriptions (paying)
        active_subs = Subscription.objects.filter(
            status=SubscriptionStatus.ACTIVE,
            deleted_at__isnull=True,
        ).count()

        # Step 4: Renewals (subscriptions with current_period_end in future
        # that have been active for more than 1 billing period)
        from django.utils import timezone as tz

        renewals = (
            Subscription.objects.filter(
                status=SubscriptionStatus.ACTIVE,
                deleted_at__isnull=True,
                current_period_end__gt=tz.now(),
            )
            .exclude(
                # Exclude first-time (within 35 days of creation)
                created_at__gte=tz.now() - timedelta(days=35),
            )
            .count()
        )

        result = [
            {"step": "Kayıt", "count": total_orgs},
            {"step": "Trial", "count": trial_ever},
            {"step": "Aktif", "count": active_subs},
            {"step": "Yenileme", "count": renewals},
        ]

        self._set_cached(key, result)
        return result

    # ─── Warm All Caches ──────────────────────────────────────────

    def warm_all_caches(self):
        """
        Pre-warm all KPI caches.
        Called by Celery task every 5 minutes.
        """
        logger.info("Warming dashboard KPI caches...")
        try:
            self.get_active_organizations()
            self.get_today_qr_scans()
            self.get_active_menus()
            self.get_pending_service_requests()
            self.get_mrr()
            self.get_trial_count()

            # Trends (7-day for sparklines)
            for metric in [
                "qr_scans",
                "organizations",
                "orders",
                "revenue",
                "menus",
                "service_requests",
            ]:
                self.get_trend(metric, days=7)

            # Comparisons
            for metric in ["qr_scans", "organizations", "orders", "revenue"]:
                self.get_period_comparison(metric)

            # QR scan trend for charts (30d, 90d)
            self.get_qr_scan_trend(days=30)
            self.get_qr_scan_trend(days=90)

            # Heavy queries
            self.get_org_activity_heatmap()
            self.get_plan_distribution()
            self.get_city_distribution()
            self.get_subscription_funnel()

            logger.info("Dashboard KPI cache warm complete.")
        except Exception as exc:
            logger.error("Cache warm failed: %s", exc, exc_info=True)
