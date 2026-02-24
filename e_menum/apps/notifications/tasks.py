"""
Celery tasks for the Notifications application.

Periodic jobs: weekly digest email, notification cleanup,
pending notification delivery.
"""

import logging

from celery import shared_task
from django.utils import timezone
from datetime import timedelta

logger = logging.getLogger(__name__)


@shared_task(name='notifications.tasks.send_weekly_digest')
def send_weekly_digest():
    """
    Send a weekly digest email summarizing unread notifications.

    Runs every Monday morning via Celery Beat schedule.
    Groups notifications by type and sends a summary email.
    """
    from apps.core.models import User
    from apps.notifications.models import Notification
    from django.core.mail import send_mail
    from django.conf import settings

    week_ago = timezone.now() - timedelta(days=7)
    users = User.objects.filter(
        is_active=True,
        deleted_at__isnull=True,
    ).exclude(email='')

    sent = 0
    for user in users:
        # Get unread notifications from the past week
        unread = Notification.objects.filter(
            user=user,
            read_at__isnull=True,
            created_at__gte=week_ago,
            deleted_at__isnull=True,
        )
        count = unread.count()

        if count == 0:
            continue

        # Build type breakdown
        type_counts = {}
        for n in unread.values('notification_type').distinct():
            ntype = n['notification_type']
            type_counts[ntype] = unread.filter(notification_type=ntype).count()

        # Build email content
        type_lines = '\n'.join(
            f'  - {ntype}: {cnt} bildirim'
            for ntype, cnt in type_counts.items()
        )

        try:
            send_mail(
                subject=f'E-Menum Haftalik Ozet: {count} okunmamis bildirim',
                message=(
                    f'Merhaba {user.first_name or user.email},\n\n'
                    f'Gecen hafta {count} okunmamis bildiriminiz var:\n'
                    f'{type_lines}\n\n'
                    f'Bildirimleri gormek icin panele giris yapin.\n\n'
                    f'E-Menum Ekibi'
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=True,
            )
            sent += 1
        except Exception as e:
            logger.warning("Failed to send digest to %s: %s", user.email, str(e))

    logger.info("Sent %d weekly digest emails", sent)
    return {'sent': sent}


@shared_task(name='notifications.tasks.cleanup_old_notifications')
def cleanup_old_notifications():
    """
    Archive notifications older than 90 days that have been read.
    Delete archived notifications older than 180 days.
    """
    from apps.notifications.models import Notification

    now = timezone.now()

    # Archive read notifications older than 90 days
    archive_cutoff = now - timedelta(days=90)
    archived = Notification.objects.filter(
        read_at__isnull=False,
        status__in=['SENT', 'DELIVERED', 'READ'],
        created_at__lt=archive_cutoff,
        deleted_at__isnull=True,
    ).update(status='ARCHIVED')

    # Soft-delete archived notifications older than 180 days
    delete_cutoff = now - timedelta(days=180)
    deleted = Notification.objects.filter(
        status='ARCHIVED',
        created_at__lt=delete_cutoff,
        deleted_at__isnull=True,
    ).update(deleted_at=now)

    logger.info("Archived %d, soft-deleted %d old notifications", archived, deleted)
    return {'archived': archived, 'deleted': deleted}
