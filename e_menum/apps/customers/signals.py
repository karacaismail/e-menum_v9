"""
Django signals for the Customers application.

Handles domain events triggered by customer activity:
- New customer created → log for analytics
- Feedback submitted → notify staff
- Loyalty points earned → log transaction
"""

import logging

from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Customer, Feedback

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Customer)
def customer_post_save(sender, instance, created, **kwargs):
    """Handle new customer registration."""
    if created:
        logger.info(
            'New customer %s registered for organization %s (source: %s)',
            instance.id,
            instance.organization_id,
            instance.source,
        )


@receiver(post_save, sender=Feedback)
def feedback_post_save(sender, instance, created, **kwargs):
    """Notify staff when new feedback is submitted."""
    if created:
        logger.info(
            'Feedback %s submitted by customer %s (type: %s, rating: %s)',
            instance.id,
            instance.customer_id,
            instance.feedback_type,
            getattr(instance, 'rating', 'N/A'),
        )
        try:
            from apps.notifications.models import Notification
            Notification.objects.create(
                organization=instance.organization,
                notification_type='feedback',
                title='Yeni geri bildirim',
                message=f'{instance.get_feedback_type_display()} - Puan: {getattr(instance, "rating", "?")}',
                data={
                    'feedback_id': str(instance.id),
                    'feedback_type': instance.feedback_type,
                    'customer_id': str(instance.customer_id),
                },
            )
        except Exception:
            logger.warning('Could not create feedback notification for %s', instance.id)
