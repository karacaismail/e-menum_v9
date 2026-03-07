"""
Celery tasks for the Core application.

Periodic background jobs: session cleanup, soft-delete garbage collection.
"""

import logging

from celery import shared_task
from django.utils import timezone
from datetime import timedelta

logger = logging.getLogger(__name__)


@shared_task(name="core.tasks.cleanup_expired_sessions")
def cleanup_expired_sessions():
    """
    Remove expired session records from the database.

    Runs daily via Celery Beat schedule defined in config/celery.py.
    """
    from django.contrib.sessions.models import Session

    expired = Session.objects.filter(expire_date__lt=timezone.now())
    count = expired.count()
    expired.delete()
    logger.info("Cleaned up %d expired sessions", count)
    return {"deleted": count}


@shared_task(name="core.tasks.cleanup_soft_deleted_records")
def cleanup_soft_deleted_records():
    """
    Permanently remove records that have been soft-deleted for more than 30 days.

    GDPR compliant: gives a 30-day recovery window before permanent deletion.
    Iterates over all models that use SoftDeleteMixin.
    """
    from django.apps import apps

    cutoff = timezone.now() - timedelta(days=30)
    total_deleted = 0

    # Find all models with deleted_at field (SoftDeleteMixin)
    for model in apps.get_models():
        if not hasattr(model, "deleted_at"):
            continue

        # Skip audit logs — they should be preserved
        if model.__name__ == "AuditLog":
            continue

        try:
            # Use all_objects manager to include soft-deleted records
            manager = getattr(model, "all_objects", model.objects)
            qs = manager.filter(deleted_at__lt=cutoff)
            count = qs.count()

            if count > 0:
                qs.delete()
                total_deleted += count
                logger.info(
                    "Permanently deleted %d %s records (soft-deleted > 30 days)",
                    count,
                    model.__name__,
                )
        except Exception as e:
            logger.warning(
                "Failed to cleanup %s: %s",
                model.__name__,
                str(e),
            )

    logger.info("Total permanently deleted: %d records", total_deleted)
    return {"total_deleted": total_deleted}
