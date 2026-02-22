"""
Celery tasks for analytics aggregation.

Periodic tasks that aggregate raw Order/Customer data into
pre-calculated analytics models for fast dashboard queries.

All tasks iterate over active organizations and call
AggregationService methods. Each task is idempotent.

Task schedule (configured in config/celery.py):
    - aggregate_hourly_sales: every hour at minute 5
    - aggregate_daily_sales: daily at 02:00 UTC
    - aggregate_product_performance: daily at 02:30 UTC
    - aggregate_customer_metrics: daily at 03:00 UTC
    - aggregate_dashboard_metrics: daily at 03:30 UTC
    - backfill_aggregations: manual trigger only
"""

import logging
from datetime import date, datetime, timedelta

from celery import shared_task
from django.utils import timezone

logger = logging.getLogger(__name__)


def _get_active_org_ids():
    """
    Return list of active organization IDs.
    Only organizations that are not soft-deleted and have active status.
    """
    from apps.core.models import Organization

    return list(
        Organization.objects.filter(
            deleted_at__isnull=True,
            is_active=True,
        ).values_list('id', flat=True)
    )


# =============================================================================
# HOURLY TASKS
# =============================================================================

@shared_task(
    bind=True,
    name='apps.analytics.tasks.aggregate_hourly_analytics',
    queue='analytics',
    max_retries=3,
    default_retry_delay=60,
    soft_time_limit=300,
    time_limit=600,
)
def aggregate_hourly_analytics(self):
    """
    Aggregate hourly sales data for all active organizations.
    Runs every hour at minute 5 (configured in celery.py).
    Aggregates the PREVIOUS hour's data.
    """
    from apps.analytics.services.aggregation_service import AggregationService

    service = AggregationService()
    now = timezone.now()
    # Aggregate previous hour
    target_hour = now.hour - 1 if now.hour > 0 else 23
    target_date = now.date() if now.hour > 0 else now.date() - timedelta(days=1)

    org_ids = _get_active_org_ids()
    success_count = 0
    error_count = 0

    for org_id in org_ids:
        try:
            service.aggregate_hourly_sales(org_id, target_date, target_hour)
            success_count += 1
        except Exception as exc:
            error_count += 1
            logger.error(
                'Hourly aggregation failed for org=%s date=%s hour=%s: %s',
                org_id, target_date, target_hour, str(exc),
                exc_info=True,
            )

    logger.info(
        'Hourly aggregation complete: date=%s hour=%s success=%d errors=%d',
        target_date, target_hour, success_count, error_count,
    )
    return {
        'date': str(target_date),
        'hour': target_hour,
        'success': success_count,
        'errors': error_count,
    }


# =============================================================================
# DAILY TASKS
# =============================================================================

@shared_task(
    bind=True,
    name='apps.analytics.tasks.generate_daily_summary',
    queue='analytics',
    max_retries=3,
    default_retry_delay=120,
    soft_time_limit=600,
    time_limit=900,
)
def generate_daily_summary(self):
    """
    Aggregate daily sales data for all active organizations.
    Runs daily at 02:00 (configured in celery.py).
    Aggregates yesterday's data.
    """
    from apps.analytics.services.aggregation_service import AggregationService

    service = AggregationService()
    yesterday = timezone.now().date() - timedelta(days=1)
    org_ids = _get_active_org_ids()
    success_count = 0
    error_count = 0

    for org_id in org_ids:
        try:
            service.aggregate_daily_sales(org_id, yesterday)
            success_count += 1
        except Exception as exc:
            error_count += 1
            logger.error(
                'Daily sales aggregation failed for org=%s date=%s: %s',
                org_id, yesterday, str(exc),
                exc_info=True,
            )

    logger.info(
        'Daily sales aggregation complete: date=%s success=%d errors=%d',
        yesterday, success_count, error_count,
    )
    return {
        'date': str(yesterday),
        'success': success_count,
        'errors': error_count,
    }


@shared_task(
    bind=True,
    name='apps.analytics.tasks.aggregate_product_performance',
    queue='analytics',
    max_retries=3,
    default_retry_delay=120,
    soft_time_limit=600,
    time_limit=900,
)
def aggregate_product_performance(self):
    """
    Aggregate product performance metrics for all active organizations.
    Runs daily at 02:30 UTC.
    Computes DAILY period for yesterday.
    """
    from apps.analytics.choices import PeriodType
    from apps.analytics.services.aggregation_service import AggregationService

    service = AggregationService()
    yesterday = timezone.now().date() - timedelta(days=1)
    org_ids = _get_active_org_ids()
    success_count = 0
    error_count = 0

    for org_id in org_ids:
        try:
            service.aggregate_product_performance(
                org_id=org_id,
                period_type=PeriodType.DAILY,
                start_date=yesterday,
                end_date=yesterday,
            )
            success_count += 1
        except Exception as exc:
            error_count += 1
            logger.error(
                'Product performance aggregation failed for org=%s date=%s: %s',
                org_id, yesterday, str(exc),
                exc_info=True,
            )

    logger.info(
        'Product performance aggregation complete: date=%s success=%d errors=%d',
        yesterday, success_count, error_count,
    )
    return {
        'date': str(yesterday),
        'success': success_count,
        'errors': error_count,
    }


@shared_task(
    bind=True,
    name='apps.analytics.tasks.aggregate_customer_metrics',
    queue='analytics',
    max_retries=3,
    default_retry_delay=120,
    soft_time_limit=600,
    time_limit=900,
)
def aggregate_customer_metrics(self):
    """
    Aggregate customer metrics for all active organizations.
    Runs daily at 03:00 UTC.
    """
    from apps.analytics.services.aggregation_service import AggregationService

    service = AggregationService()
    yesterday = timezone.now().date() - timedelta(days=1)
    org_ids = _get_active_org_ids()
    success_count = 0
    error_count = 0

    for org_id in org_ids:
        try:
            service.aggregate_customer_metrics(org_id, yesterday)
            success_count += 1
        except Exception as exc:
            error_count += 1
            logger.error(
                'Customer metrics aggregation failed for org=%s date=%s: %s',
                org_id, yesterday, str(exc),
                exc_info=True,
            )

    logger.info(
        'Customer metrics aggregation complete: date=%s success=%d errors=%d',
        yesterday, success_count, error_count,
    )
    return {
        'date': str(yesterday),
        'success': success_count,
        'errors': error_count,
    }


@shared_task(
    bind=True,
    name='apps.analytics.tasks.aggregate_dashboard_metrics',
    queue='analytics',
    max_retries=3,
    default_retry_delay=120,
    soft_time_limit=600,
    time_limit=900,
)
def aggregate_dashboard_metrics(self):
    """
    Aggregate dashboard KPI metrics for all active organizations.
    Runs daily at 03:30 UTC.
    Computes DAILY, WEEKLY, and MONTHLY period metrics.
    """
    from apps.analytics.choices import PeriodType
    from apps.analytics.services.aggregation_service import AggregationService

    service = AggregationService()
    org_ids = _get_active_org_ids()
    success_count = 0
    error_count = 0

    period_types = [PeriodType.DAILY, PeriodType.WEEKLY, PeriodType.MONTHLY]

    for org_id in org_ids:
        for period_type in period_types:
            try:
                service.aggregate_dashboard_metrics(org_id, period_type)
                success_count += 1
            except Exception as exc:
                error_count += 1
                logger.error(
                    'Dashboard metrics aggregation failed for org=%s period=%s: %s',
                    org_id, period_type, str(exc),
                    exc_info=True,
                )

    logger.info(
        'Dashboard metrics aggregation complete: success=%d errors=%d',
        success_count, error_count,
    )
    return {
        'success': success_count,
        'errors': error_count,
    }


# =============================================================================
# WEEKLY TASKS
# =============================================================================

@shared_task(
    bind=True,
    name='apps.analytics.tasks.aggregate_weekly_performance',
    queue='analytics',
    max_retries=3,
    default_retry_delay=120,
    soft_time_limit=900,
    time_limit=1200,
)
def aggregate_weekly_performance(self):
    """
    Aggregate weekly product performance for all active organizations.
    Runs every Monday at 04:00 UTC.
    Computes WEEKLY period for the previous 7 days.
    """
    from apps.analytics.choices import PeriodType
    from apps.analytics.services.aggregation_service import AggregationService

    service = AggregationService()
    today = timezone.now().date()
    week_start = today - timedelta(days=7)
    week_end = today - timedelta(days=1)
    org_ids = _get_active_org_ids()
    success_count = 0
    error_count = 0

    for org_id in org_ids:
        try:
            service.aggregate_product_performance(
                org_id=org_id,
                period_type=PeriodType.WEEKLY,
                start_date=week_start,
                end_date=week_end,
            )
            success_count += 1
        except Exception as exc:
            error_count += 1
            logger.error(
                'Weekly product performance failed for org=%s: %s',
                org_id, str(exc),
                exc_info=True,
            )

    logger.info(
        'Weekly product performance complete: %s to %s success=%d errors=%d',
        week_start, week_end, success_count, error_count,
    )
    return {
        'week_start': str(week_start),
        'week_end': str(week_end),
        'success': success_count,
        'errors': error_count,
    }


# =============================================================================
# BACKFILL (MANUAL TRIGGER)
# =============================================================================

@shared_task(
    bind=True,
    name='apps.analytics.tasks.backfill_aggregations',
    queue='analytics',
    max_retries=0,
    soft_time_limit=3600,
    time_limit=7200,
)
def backfill_aggregations(self, org_id=None, start_date_str=None, end_date_str=None):
    """
    Backfill aggregation data for a date range.
    Can target a specific organization or all organizations.

    Manual trigger only - not in beat schedule.

    Args:
        org_id: UUID string of specific organization (None = all orgs)
        start_date_str: Start date as 'YYYY-MM-DD' string
        end_date_str: End date as 'YYYY-MM-DD' string (inclusive)

    Usage:
        # Backfill last 30 days for all orgs
        from apps.analytics.tasks import backfill_aggregations
        backfill_aggregations.delay(
            start_date_str='2026-01-01',
            end_date_str='2026-01-31',
        )

        # Backfill specific org
        backfill_aggregations.delay(
            org_id='uuid-here',
            start_date_str='2026-01-01',
            end_date_str='2026-01-31',
        )
    """
    from apps.analytics.choices import PeriodType
    from apps.analytics.services.aggregation_service import AggregationService

    service = AggregationService()

    # Parse dates
    if start_date_str:
        start = date.fromisoformat(start_date_str)
    else:
        start = timezone.now().date() - timedelta(days=30)

    if end_date_str:
        end = date.fromisoformat(end_date_str)
    else:
        end = timezone.now().date() - timedelta(days=1)

    # Get org IDs
    if org_id:
        org_ids = [org_id]
    else:
        org_ids = _get_active_org_ids()

    total_success = 0
    total_errors = 0
    total_days = (end - start).days + 1

    logger.info(
        'Starting backfill: orgs=%d days=%d (%s to %s)',
        len(org_ids), total_days, start, end,
    )

    for org_id_item in org_ids:
        current_date = start
        while current_date <= end:
            try:
                # Daily sales
                service.aggregate_daily_sales(org_id_item, current_date)

                # Hourly sales (0-23)
                for hour in range(24):
                    service.aggregate_hourly_sales(org_id_item, current_date, hour)

                # Product performance (daily)
                service.aggregate_product_performance(
                    org_id=org_id_item,
                    period_type=PeriodType.DAILY,
                    start_date=current_date,
                    end_date=current_date,
                )

                # Customer metrics
                service.aggregate_customer_metrics(org_id_item, current_date)

                total_success += 1
            except Exception as exc:
                total_errors += 1
                logger.error(
                    'Backfill failed for org=%s date=%s: %s',
                    org_id_item, current_date, str(exc),
                    exc_info=True,
                )

            current_date += timedelta(days=1)

        # Dashboard metrics for the org (latest snapshot)
        try:
            for pt in [PeriodType.DAILY, PeriodType.WEEKLY, PeriodType.MONTHLY]:
                service.aggregate_dashboard_metrics(org_id_item, pt)
        except Exception as exc:
            logger.error(
                'Backfill dashboard metrics failed for org=%s: %s',
                org_id_item, str(exc),
                exc_info=True,
            )

    logger.info(
        'Backfill complete: orgs=%d days_success=%d days_error=%d',
        len(org_ids), total_success, total_errors,
    )
    return {
        'orgs_processed': len(org_ids),
        'days_success': total_success,
        'days_error': total_errors,
        'date_range': f'{start} to {end}',
    }
