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


def _get_deletion_order():
    """
    Return soft-deletable models sorted in dependency order (leaves first).

    Child models (those with FK CASCADE pointing to a parent) are deleted
    before their parents to prevent FK constraint violations and ensure
    audit trail integrity.
    """
    from django.apps import apps

    # Collect all models with deleted_at (SoftDeleteMixin)
    models = []
    for model in apps.get_models():
        if not hasattr(model, "deleted_at"):
            continue
        # Skip audit logs — preserved for compliance
        if model.__name__ == "AuditLog":
            continue
        models.append(model)

    # Build a dependency score: models that are FK targets of other models
    # get a higher score (deleted later). Leaf models deleted first.
    dep_count = {m._meta.label: 0 for m in models}

    for model in models:
        for field in model._meta.get_fields():
            if hasattr(field, "related_model") and field.related_model:
                parent_label = field.related_model._meta.label
                if (
                    parent_label in dep_count
                    and parent_label != model._meta.label
                    and hasattr(field, "remote_field")
                    and getattr(field.remote_field, "on_delete", None).__name__
                    == "CASCADE"
                ):
                    # This model depends on parent_label via CASCADE
                    # Parent should be deleted AFTER this model
                    dep_count[parent_label] = max(
                        dep_count[parent_label], dep_count.get(model._meta.label, 0) + 1
                    )

    # Sort: lowest dependency count first (leaves first, roots last)
    models.sort(key=lambda m: dep_count.get(m._meta.label, 0))
    return models


@shared_task(name="core.tasks.cleanup_soft_deleted_records")
def cleanup_soft_deleted_records(dry_run=False):
    """
    Permanently remove records that have been soft-deleted for more than 30 days.

    GDPR compliant: gives a 30-day recovery window before permanent deletion.
    Models are deleted in dependency order (children first, parents last)
    to prevent FK constraint violations.

    Args:
        dry_run: If True, only count and log what would be deleted without
                 actually deleting anything.
    """
    cutoff = timezone.now() - timedelta(days=30)
    total_deleted = 0
    summary = {}

    for model in _get_deletion_order():
        try:
            # Use all_objects manager to include soft-deleted records
            manager = getattr(model, "all_objects", model.objects)
            qs = manager.filter(deleted_at__lt=cutoff)
            count = qs.count()

            if count > 0:
                summary[model.__name__] = count
                if not dry_run:
                    qs.delete()
                total_deleted += count
                logger.info(
                    "%s %d %s records (soft-deleted > 30 days)",
                    "Would delete" if dry_run else "Permanently deleted",
                    count,
                    model.__name__,
                )
        except Exception as e:
            logger.warning(
                "Failed to cleanup %s: %s",
                model.__name__,
                str(e),
            )

    logger.info(
        "%s total: %d records. Breakdown: %s",
        "Dry-run" if dry_run else "Cleanup complete",
        total_deleted,
        summary,
    )
    return {"total_deleted": total_deleted, "dry_run": dry_run, "summary": summary}
