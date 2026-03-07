"""
Celery tasks for the Dashboard app.

Tasks:
- generate_dashboard_insights: Daily at 06:00, creates insight cards
- warm_kpi_cache: Every 5 minutes, pre-warms Redis caches

All tasks are idempotent and safe to re-run.
"""

import logging
from datetime import timedelta

from celery import shared_task
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    name="apps.dashboard.tasks.generate_dashboard_insights",
    queue="analytics",
    max_retries=3,
    default_retry_delay=120,
    soft_time_limit=300,
    time_limit=600,
)
def generate_dashboard_insights(self):
    """
    Generate dashboard insight cards based on platform data patterns.

    Runs daily at 06:00 UTC (configured in celery.py beat_schedule).

    Queries:
    1. Churn risk: Active orgs with 0 QR scans in last 30 days
    2. Expiring plans: Subscriptions ending within 7 days (no auto-renew)
    3. Growth opportunity: >20% registration increase this month vs last
    4. Cleanup: Deactivate expired insights
    """
    from apps.dashboard.models import DashboardInsight, InsightType

    now = timezone.now()
    insights_created = 0

    # ─── Cleanup: deactivate expired insights ─────────────────
    expired_count = DashboardInsight.objects.filter(
        is_active=True,
        expires_at__lt=now,
        deleted_at__isnull=True,
    ).update(is_active=False)

    if expired_count:
        logger.info("Deactivated %d expired insights", expired_count)

    # ─── Query 1: Churn Risk ─────────────────────────────────
    try:
        from apps.core.choices import OrganizationStatus
        from apps.core.models import Organization
        from apps.orders.models import QRScan

        thirty_days_ago = now - timedelta(days=30)

        # Active orgs
        active_orgs = Organization.objects.filter(
            status=OrganizationStatus.ACTIVE,
            deleted_at__isnull=True,
        )

        # Orgs with at least one QR scan in last 30 days
        active_scan_org_ids = (
            QRScan.objects.filter(
                created_at__gte=thirty_days_ago,
                qr_code__organization__isnull=False,
            )
            .values_list("qr_code__organization_id", flat=True)
            .distinct()
        )

        # Orgs with NO scans in 30 days
        inactive_orgs_count = active_orgs.exclude(
            id__in=active_scan_org_ids,
        ).count()

        if inactive_orgs_count > 0:
            DashboardInsight.objects.update_or_create(
                title="Churn Riski",
                type=InsightType.WARNING,
                is_active=True,
                expires_at__gte=now,
                deleted_at__isnull=True,
                defaults={
                    "body": f"{inactive_orgs_count} organizasyon son 30 gündür aktif değil.",
                    "metric_value": inactive_orgs_count,
                    "metric_label": "organizasyon",
                    "action_label": "Görüntüle",
                    "action_url": "/admin/core/organization/?status=ACTIVE",
                    "priority": 90,
                    "is_active": True,
                    "expires_at": now + timedelta(hours=24),
                },
            )
            insights_created += 1
    except Exception as exc:
        logger.error("Churn risk insight failed: %s", exc, exc_info=True)

    # ─── Query 2: Expiring Subscriptions ─────────────────────
    try:
        from apps.subscriptions.choices import SubscriptionStatus
        from apps.subscriptions.models import Subscription

        seven_days = now + timedelta(days=7)

        expiring = Subscription.objects.filter(
            status__in=[SubscriptionStatus.ACTIVE, SubscriptionStatus.TRIALING],
            current_period_end__lte=seven_days,
            current_period_end__gt=now,
            cancel_at_period_end=True,
            deleted_at__isnull=True,
        ).count()

        if expiring > 0:
            DashboardInsight.objects.update_or_create(
                title="Süresi Dolmak Üzere",
                type=InsightType.WARNING,
                is_active=True,
                expires_at__gte=now,
                deleted_at__isnull=True,
                defaults={
                    "body": f"{expiring} aboneliğin süresi 7 gün içinde doluyor.",
                    "metric_value": expiring,
                    "metric_label": "abonelik",
                    "action_label": "Abonelikleri Gör",
                    "action_url": "/admin/subscriptions/subscription/",
                    "priority": 85,
                    "is_active": True,
                    "expires_at": now + timedelta(hours=24),
                },
            )
            insights_created += 1
    except Exception as exc:
        logger.error("Expiring plans insight failed: %s", exc, exc_info=True)

    # ─── Query 3: Growth Opportunity ─────────────────────────
    try:
        from apps.core.models import Organization

        this_month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        last_month_end = this_month_start - timedelta(seconds=1)
        last_month_start = last_month_end.replace(
            day=1, hour=0, minute=0, second=0, microsecond=0
        )

        this_month_count = Organization.objects.filter(
            created_at__gte=this_month_start,
            deleted_at__isnull=True,
        ).count()

        last_month_count = Organization.objects.filter(
            created_at__gte=last_month_start,
            created_at__lt=this_month_start,
            deleted_at__isnull=True,
        ).count()

        if last_month_count > 0:
            growth_pct = (
                (this_month_count - last_month_count) / last_month_count
            ) * 100
            if growth_pct > 20:
                DashboardInsight.objects.update_or_create(
                    title="Büyüme Fırsatı",
                    type=InsightType.OPPORTUNITY,
                    is_active=True,
                    expires_at__gte=now,
                    deleted_at__isnull=True,
                    defaults={
                        "body": f"Bu ay kayıtlarda %{growth_pct:.0f} artış var! Geçen ay: {last_month_count}, bu ay: {this_month_count}.",
                        "metric_value": growth_pct,
                        "metric_label": "büyüme",
                        "action_label": "Analiz Et",
                        "action_url": "/admin/core/organization/",
                        "priority": 70,
                        "is_active": True,
                        "expires_at": now + timedelta(hours=24),
                    },
                )
                insights_created += 1
    except Exception as exc:
        logger.error("Growth opportunity insight failed: %s", exc, exc_info=True)

    # ─── Query 4: Pending Translations (if available) ────────
    try:
        # Check if translation model exists
        from django.apps import apps as django_apps

        if django_apps.is_installed("apps.website"):
            # Try to check for pending content that might need translation
            from apps.website.models import BlogPost

            drafts = BlogPost.objects.filter(
                status="DRAFT",
                deleted_at__isnull=True,
            ).count()
            if drafts > 10:
                DashboardInsight.objects.update_or_create(
                    title="Bekleyen İçerik",
                    type=InsightType.INFO,
                    is_active=True,
                    expires_at__gte=now,
                    deleted_at__isnull=True,
                    defaults={
                        "body": f"{drafts} taslak blog yazısı yayınlanmayı bekliyor.",
                        "metric_value": drafts,
                        "metric_label": "taslak",
                        "action_label": "İçerikleri Gör",
                        "action_url": "/admin/website/blogpost/?status=DRAFT",
                        "priority": 50,
                        "is_active": True,
                        "expires_at": now + timedelta(hours=24),
                    },
                )
                insights_created += 1
    except (ImportError, Exception):
        pass  # Module not available, skip

    logger.info(
        "Dashboard insights generated: created=%d, expired_deactivated=%d",
        insights_created,
        expired_count,
    )
    return {
        "created": insights_created,
        "expired_deactivated": expired_count,
    }


@shared_task(
    bind=True,
    name="apps.dashboard.tasks.warm_kpi_cache",
    queue="analytics",
    max_retries=1,
    default_retry_delay=30,
    soft_time_limit=120,
    time_limit=180,
)
def warm_kpi_cache(self):
    """
    Pre-warm all dashboard KPI caches.

    Runs every 5 minutes (configured in celery.py beat_schedule).
    Ensures dashboard loads instantly without cold cache queries.
    """
    from apps.dashboard.services import KPIService

    service = KPIService()
    service.warm_all_caches()
    return {"status": "ok"}
