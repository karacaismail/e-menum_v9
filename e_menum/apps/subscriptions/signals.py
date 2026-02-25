"""
Django signals for the Subscriptions application.

Handles domain events triggered by subscription lifecycle changes:
- Subscription created → welcome notification
- Subscription status changed → alert organization owner
- Invoice created → notify for payment
"""

import logging

from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Invoice, Subscription

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Subscription)
def subscription_post_save(sender, instance, created, **kwargs):
    """Handle subscription creation and status changes."""
    if created:
        logger.info(
            'Subscription %s created for organization %s (plan: %s, status: %s)',
            instance.id,
            instance.organization_id,
            getattr(instance.plan, 'name', 'N/A'),
            instance.status,
        )
        try:
            from apps.notifications.models import Notification
            Notification.objects.create(
                organization=instance.organization,
                notification_type='subscription',
                title='Abonelik olusturuldu',
                message=f'{getattr(instance.plan, "name", "Plan")} aboneligi baslatildi.',
                data={
                    'subscription_id': str(instance.id),
                    'plan_id': str(instance.plan_id) if instance.plan_id else None,
                },
            )
        except Exception:
            logger.warning('Could not create subscription notification for %s', instance.id)
    else:
        # Status change detection
        if instance.tracker and hasattr(instance, 'tracker'):
            try:
                previous_status = instance.tracker.previous('status')
                if previous_status and previous_status != instance.status:
                    logger.info(
                        'Subscription %s status changed: %s → %s',
                        instance.id,
                        previous_status,
                        instance.status,
                    )
            except Exception:
                pass


@receiver(post_save, sender=Invoice)
def invoice_post_save(sender, instance, created, **kwargs):
    """Notify when a new invoice is generated."""
    if created:
        logger.info(
            'Invoice %s created for subscription %s (amount: %s %s)',
            instance.invoice_number,
            instance.subscription_id,
            instance.total_amount,
            instance.currency,
        )
        try:
            from apps.notifications.models import Notification
            organization = instance.subscription.organization if instance.subscription else None
            if organization:
                Notification.objects.create(
                    organization=organization,
                    notification_type='billing',
                    title='Yeni fatura',
                    message=f'Fatura #{instance.invoice_number} olusturuldu. Tutar: {instance.total_amount} {instance.currency}',
                    data={
                        'invoice_id': str(instance.id),
                        'invoice_number': instance.invoice_number,
                    },
                )
        except Exception:
            logger.warning('Could not create invoice notification for %s', instance.id)
