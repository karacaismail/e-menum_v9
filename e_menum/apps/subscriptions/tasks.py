"""
Celery tasks for the Subscriptions application.

Periodic jobs: expiring subscription alerts, dunning workflow,
plan limit enforcement.
"""

import logging

from celery import shared_task
from django.utils import timezone
from datetime import timedelta

logger = logging.getLogger(__name__)


@shared_task(name="subscriptions.tasks.check_expiring_subscriptions")
def check_expiring_subscriptions():
    """
    Find subscriptions expiring within 7 days and create notifications.

    Dunning schedule (from spec):
      Day 0: Mark PAST_DUE, send warning
      Day 3: Reminder email
      Day 5: Final warning
      Day 7: Mark EXPIRED, restrict access
    """
    from apps.subscriptions.models import Subscription
    from apps.notifications.models import Notification

    now = timezone.now()
    expiring_soon = Subscription.objects.filter(
        end_date__lte=now + timedelta(days=7),
        end_date__gt=now,
        status="active",
        deleted_at__isnull=True,
    ).select_related("organization")

    notified = 0
    for sub in expiring_soon:
        days_left = (sub.end_date - now).days

        # Determine notification priority based on urgency
        if days_left <= 1:
            priority = "URGENT"
        elif days_left <= 3:
            priority = "HIGH"
        else:
            priority = "NORMAL"

        # Create in-app notification for organization owner(s)
        owners = sub.organization.users.filter(
            role="owner",
            is_active=True,
            deleted_at__isnull=True,
        )
        for owner in owners:
            Notification.objects.get_or_create(
                organization=sub.organization,
                user=owner,
                notification_type="PAYMENT",
                title=f"Aboneliginiz {days_left} gun icinde sona eriyor",
                message=(
                    f"{sub.organization.name} icin {sub.plan.name if hasattr(sub, 'plan') and sub.plan else 'mevcut'} "
                    f"plan aboneliginiz {sub.end_date.strftime('%d.%m.%Y')} tarihinde sona erecek. "
                    f"Kesintisiz hizmet icin lutfen yenileyin."
                ),
                defaults={
                    "priority": priority,
                    "channel": "IN_APP",
                    "status": "PENDING",
                    "action_url": "/admin/subscriptions/",
                    "data": {
                        "subscription_id": str(sub.id),
                        "days_left": days_left,
                        "end_date": sub.end_date.isoformat(),
                    },
                },
            )
            notified += 1

    logger.info("Sent %d expiring subscription notifications", notified)
    return {"notified": notified, "expiring_count": expiring_soon.count()}


@shared_task(name="subscriptions.tasks.expire_past_due_subscriptions")
def expire_past_due_subscriptions():
    """
    Mark PAST_DUE subscriptions as EXPIRED after 7-day grace period.
    """
    from apps.subscriptions.models import Subscription

    cutoff = timezone.now() - timedelta(days=7)
    past_due = Subscription.objects.filter(
        status="past_due",
        end_date__lt=cutoff,
        deleted_at__isnull=True,
    )

    count = past_due.count()
    past_due.update(status="expired")
    logger.info("Expired %d past-due subscriptions", count)
    return {"expired": count}
