"""
Celery Configuration for E-Menum Enterprise QR Menu SaaS.

This module configures Celery for asynchronous task processing.
Tasks include AI content generation, analytics processing, email sending, etc.

Usage:
    # Start Celery worker (from project root containing manage.py)
    celery -A config worker -l INFO

    # Start Celery beat (for periodic tasks)
    celery -A config beat -l INFO

    # Start both worker and beat together (development)
    celery -A config worker -B -l INFO
"""

import os

from celery import Celery
from celery.schedules import crontab

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')

# Create the Celery application instance
app = Celery('e_menum')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix in Django settings.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()


# =============================================================================
# Celery Beat Periodic Tasks Schedule
# =============================================================================

app.conf.beat_schedule = {
    # =========================================================================
    # Analytics Aggregation Tasks
    # =========================================================================

    # Hourly sales aggregation - runs every hour at minute 5
    'aggregate-hourly-analytics': {
        'task': 'apps.analytics.tasks.aggregate_hourly_analytics',
        'schedule': crontab(minute=5),
        'options': {'queue': 'analytics'},
    },

    # Daily sales aggregation - runs at 02:00 UTC
    'generate-daily-summary': {
        'task': 'apps.analytics.tasks.generate_daily_summary',
        'schedule': crontab(hour=2, minute=0),
        'options': {'queue': 'analytics'},
    },

    # Product performance aggregation (daily) - runs at 02:30 UTC
    'aggregate-product-performance': {
        'task': 'apps.analytics.tasks.aggregate_product_performance',
        'schedule': crontab(hour=2, minute=30),
        'options': {'queue': 'analytics'},
    },

    # Customer metrics aggregation - runs at 03:00 UTC
    'aggregate-customer-metrics': {
        'task': 'apps.analytics.tasks.aggregate_customer_metrics',
        'schedule': crontab(hour=3, minute=0),
        'options': {'queue': 'analytics'},
    },

    # Dashboard KPI metrics - runs at 03:30 UTC
    'aggregate-dashboard-metrics': {
        'task': 'apps.analytics.tasks.aggregate_dashboard_metrics',
        'schedule': crontab(hour=3, minute=30),
        'options': {'queue': 'analytics'},
    },

    # Weekly product performance - runs Mondays at 04:00 UTC
    'aggregate-weekly-performance': {
        'task': 'apps.analytics.tasks.aggregate_weekly_performance',
        'schedule': crontab(hour=4, minute=0, day_of_week=1),
        'options': {'queue': 'analytics'},
    },

    # =========================================================================
    # Dashboard Tasks
    # =========================================================================

    # Generate dashboard insights - runs daily at 06:00 UTC
    'generate-dashboard-insights': {
        'task': 'apps.dashboard.tasks.generate_dashboard_insights',
        'schedule': crontab(hour=6, minute=0),
        'options': {'queue': 'analytics'},
    },

    # Warm dashboard KPI cache - runs every 5 minutes
    'warm-kpi-cache': {
        'task': 'apps.dashboard.tasks.warm_kpi_cache',
        'schedule': crontab(minute='*/5'),
        'options': {'queue': 'analytics'},
    },

    # =========================================================================
    # Reporting Tasks
    # =========================================================================

    # Process scheduled reports - runs every 5 minutes
    'process-scheduled-reports': {
        'task': 'apps.reporting.tasks.process_scheduled_reports',
        'schedule': crontab(minute='*/5'),
        'options': {'queue': 'reporting'},
    },

    # =========================================================================
    # System Maintenance Tasks
    # =========================================================================

    # Subscription expiry check - runs at 5 AM
    'check-subscription-expiry': {
        'task': 'apps.subscriptions.tasks.check_expiring_subscriptions',
        'schedule': crontab(hour=5, minute=0),
        'options': {'queue': 'subscriptions'},
    },

    # Send weekly digest emails - runs on Mondays at 9 AM
    'send-weekly-digest': {
        'task': 'apps.notifications.tasks.send_weekly_digest',
        'schedule': crontab(hour=9, minute=0, day_of_week=1),
        'options': {'queue': 'notifications'},
    },

    # Cleanup old sessions - runs daily at 6 AM
    'cleanup-expired-sessions': {
        'task': 'apps.core.tasks.cleanup_expired_sessions',
        'schedule': crontab(hour=6, minute=0),
        'options': {'queue': 'maintenance'},
    },

    # Cleanup soft-deleted records older than 30 days - runs weekly
    'cleanup-soft-deleted': {
        'task': 'apps.core.tasks.cleanup_soft_deleted_records',
        'schedule': crontab(hour=6, minute=30, day_of_week=0),
        'options': {'queue': 'maintenance'},
    },
}


# =============================================================================
# Task Queue Routing
# =============================================================================

app.conf.task_routes = {
    # AI tasks go to a dedicated queue (may need more resources)
    'apps.ai.tasks.*': {'queue': 'ai'},

    # Analytics tasks (can be lower priority)
    'apps.analytics.tasks.*': {'queue': 'analytics'},

    # Reporting tasks (report generation, exports)
    'apps.reporting.tasks.*': {'queue': 'reporting'},

    # Notification tasks (email, push, etc.)
    'apps.notifications.tasks.*': {'queue': 'notifications'},

    # Subscription and billing tasks
    'apps.subscriptions.tasks.*': {'queue': 'subscriptions'},

    # Media processing (image optimization, etc.)
    'apps.media.tasks.*': {'queue': 'media'},

    # Default queue for everything else
    'apps.*.tasks.*': {'queue': 'default'},
}


# =============================================================================
# Task Priority Configuration
# =============================================================================

# Define task priorities (lower = higher priority)
app.conf.task_queue_max_priority = 10
app.conf.task_default_priority = 5


# =============================================================================
# Error Handling and Retry Configuration
# =============================================================================

# Retry failed tasks
app.conf.task_acks_late = True
app.conf.task_reject_on_worker_lost = True

# Retry configuration for transient failures
app.conf.task_annotations = {
    '*': {
        'rate_limit': '100/s',
    },
    'apps.ai.tasks.*': {
        'rate_limit': '10/m',  # AI tasks rate limited
        'time_limit': 300,  # 5 minute timeout for AI tasks
    },
    'apps.notifications.tasks.send_email': {
        'rate_limit': '50/m',  # Email rate limiting
    },
}


# =============================================================================
# Debug Task
# =============================================================================

@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """
    Debug task for testing Celery configuration.

    Usage:
        from config.celery import debug_task
        debug_task.delay()
    """
    print(f'Request: {self.request!r}')
