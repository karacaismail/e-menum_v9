"""
Django signals for the Orders application.

Handles domain events triggered by order lifecycle changes:
- Order created → notify staff
- Order status changed → notify customer + update analytics
- Service request created → notify staff
"""

import logging

from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Order, ServiceRequest

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Order)
def order_post_save(sender, instance, created, **kwargs):
    """Handle order creation and status changes."""
    if created:
        logger.info(
            'Order %s created for organization %s (table: %s)',
            instance.id,
            instance.organization_id,
            getattr(instance.table, 'name', 'N/A'),
        )
        # Create notification for staff
        try:
            from apps.notifications.models import Notification
            Notification.objects.create(
                organization=instance.organization,
                notification_type='order',
                title='Yeni siparis',
                message=f'Siparis #{instance.order_number} olusturuldu.',
                data={'order_id': str(instance.id)},
            )
        except Exception:
            logger.warning('Could not create order notification for %s', instance.id)


@receiver(post_save, sender=ServiceRequest)
def service_request_post_save(sender, instance, created, **kwargs):
    """Notify staff when a customer makes a service request (waiter call, bill request)."""
    if created:
        logger.info(
            'ServiceRequest %s (%s) for table %s in organization %s',
            instance.id,
            instance.request_type,
            getattr(instance.table, 'name', 'N/A'),
            instance.organization_id,
        )
        try:
            from apps.notifications.models import Notification
            Notification.objects.create(
                organization=instance.organization,
                notification_type='service_request',
                title='Servis talebi',
                message=f'{instance.get_request_type_display()} - Masa: {getattr(instance.table, "name", "?")}',
                data={
                    'service_request_id': str(instance.id),
                    'request_type': instance.request_type,
                },
            )
        except Exception:
            logger.warning('Could not create service request notification for %s', instance.id)
