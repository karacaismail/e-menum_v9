"""
Django ORM models for the Notifications application.

This module defines the notification-related models for E-Menum:
- Notification: User notifications for orders, system alerts, and promotions

Critical Rules:
- Every query MUST include organization_id for tenant isolation
- All entities use soft delete (deleted_at timestamp)
- No physical deletions allowed (use soft_delete method)
"""

import uuid

from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.core.models import (
    Organization,
    SoftDeleteManager,
    SoftDeleteMixin,
    TimeStampedMixin,
    User,
)
from apps.notifications.choices import (
    NotificationChannel,
    NotificationPriority,
    NotificationStatus,
    NotificationType,
)


class Notification(TimeStampedMixin, SoftDeleteMixin, models.Model):
    """
    Notification model - represents user notifications for various events.

    Notifications are used to inform users about:
    - Order status changes and confirmations
    - System alerts and maintenance notices
    - Promotional offers and marketing campaigns
    - Payment receipts and invoice reminders
    - Security alerts (login attempts, password changes)
    - Customer feedback and reviews

    Critical Rules:
    - EVERY query MUST filter by organization (multi-tenant isolation)
    - Use soft_delete() - never call delete() directly
    - Notifications are typically associated with a specific user (recipient)

    Attributes:
        id: UUID primary key (ensures global uniqueness)
        organization: FK to parent Organization (tenant isolation)
        user: FK to User who is the recipient of this notification
        notification_type: Type of notification (ORDER, SYSTEM, PROMOTION, etc.)
        status: Current delivery/read status
        priority: Priority level for ordering and urgency
        channel: Delivery channel (IN_APP, PUSH, EMAIL, SMS)
        title: Short title/subject for the notification
        message: Full notification message content
        data: JSON field for additional context (order_id, urls, etc.)
        read_at: When the notification was read/viewed
        sent_at: When the notification was sent to the channel
        delivered_at: When the notification was confirmed delivered
        scheduled_for: Optional scheduled delivery time
        expires_at: Optional expiration time after which notification is hidden
        action_url: Optional URL for click-through action
        image_url: Optional image URL for rich notifications
        metadata: Additional metadata for tracking and analytics

    Usage:
        # Create an order notification
        notification = Notification.objects.create(
            organization=org,
            user=customer,
            notification_type=NotificationType.ORDER,
            priority=NotificationPriority.HIGH,
            channel=NotificationChannel.IN_APP,
            title="Order Confirmed",
            message="Your order #1234 has been confirmed and is being prepared.",
            data={'order_id': str(order.id), 'order_number': '1234'},
            action_url='/orders/1234/'
        )

        # Query notifications for organization (ALWAYS filter by organization!)
        notifications = Notification.objects.filter(organization=org)

        # Get unread notifications for a user
        unread = Notification.objects.filter(
            organization=org,
            user=user,
            status__in=[NotificationStatus.SENT, NotificationStatus.DELIVERED]
        )

        # Mark notification as read
        notification.mark_as_read()

        # Soft delete notification (NEVER use delete())
        notification.soft_delete()
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name=_('ID'),
        help_text=_('Unique identifier (UUID)')
    )

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='notifications',
        verbose_name=_('Organization'),
        help_text=_('Organization this notification belongs to')
    )

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='notifications',
        verbose_name=_('User'),
        help_text=_('User who is the recipient of this notification')
    )

    notification_type = models.CharField(
        max_length=20,
        choices=NotificationType.choices,
        default=NotificationType.GENERAL,
        db_index=True,
        verbose_name=_('Notification type'),
        help_text=_('Category of the notification')
    )

    status = models.CharField(
        max_length=20,
        choices=NotificationStatus.choices,
        default=NotificationStatus.PENDING,
        db_index=True,
        verbose_name=_('Status'),
        help_text=_('Current delivery/read status of the notification')
    )

    priority = models.CharField(
        max_length=10,
        choices=NotificationPriority.choices,
        default=NotificationPriority.NORMAL,
        db_index=True,
        verbose_name=_('Priority'),
        help_text=_('Priority level for ordering and urgency')
    )

    channel = models.CharField(
        max_length=10,
        choices=NotificationChannel.choices,
        default=NotificationChannel.IN_APP,
        verbose_name=_('Channel'),
        help_text=_('Delivery channel for the notification')
    )

    title = models.CharField(
        max_length=255,
        verbose_name=_('Title'),
        help_text=_('Short title or subject for the notification')
    )

    message = models.TextField(
        verbose_name=_('Message'),
        help_text=_('Full notification message content')
    )

    data = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_('Data'),
        help_text=_('Additional context data (order_id, urls, etc.)')
    )

    read_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Read at'),
        help_text=_('When the notification was read/viewed by the user')
    )

    sent_at = models.DateTimeField(
        null=True,
        blank=True,
        db_index=True,
        verbose_name=_('Sent at'),
        help_text=_('When the notification was sent to the delivery channel')
    )

    delivered_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Delivered at'),
        help_text=_('When the notification was confirmed delivered')
    )

    scheduled_for = models.DateTimeField(
        null=True,
        blank=True,
        db_index=True,
        verbose_name=_('Scheduled for'),
        help_text=_('Optional scheduled delivery time (null for immediate)')
    )

    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        db_index=True,
        verbose_name=_('Expires at'),
        help_text=_('Optional expiration time after which notification is hidden')
    )

    action_url = models.URLField(
        blank=True,
        null=True,
        max_length=500,
        verbose_name=_('Action URL'),
        help_text=_('Optional URL for click-through action')
    )

    image_url = models.URLField(
        blank=True,
        null=True,
        max_length=500,
        verbose_name=_('Image URL'),
        help_text=_('Optional image URL for rich notifications')
    )

    metadata = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_('Metadata'),
        help_text=_('Additional metadata for tracking and analytics')
    )

    # Managers
    objects = SoftDeleteManager()  # Default: excludes soft-deleted
    all_objects = models.Manager()  # Includes ALL records

    class Meta:
        db_table = 'notifications'
        verbose_name = _('Notification')
        verbose_name_plural = _('Notifications')
        ordering = ['-created_at']
        indexes = [
            models.Index(
                fields=['organization', 'user', 'status'],
                name='notif_org_user_status_idx'
            ),
            models.Index(
                fields=['organization', 'status', 'deleted_at'],
                name='notif_org_status_deleted_idx'
            ),
            models.Index(
                fields=['user', 'status', 'created_at'],
                name='notif_user_status_created_idx'
            ),
            models.Index(
                fields=['notification_type', 'created_at'],
                name='notif_type_created_idx'
            ),
            models.Index(
                fields=['organization', 'notification_type'],
                name='notif_org_type_idx'
            ),
        ]

    def __str__(self) -> str:
        return f"{self.title} ({self.notification_type})"

    def __repr__(self) -> str:
        return f"<Notification(id={self.id}, type={self.notification_type}, status={self.status})>"

    @property
    def is_read(self) -> bool:
        """Check if notification has been read."""
        return self.read_at is not None or self.status == NotificationStatus.READ

    @property
    def is_sent(self) -> bool:
        """Check if notification has been sent."""
        return self.sent_at is not None or self.status in [
            NotificationStatus.SENT,
            NotificationStatus.DELIVERED,
            NotificationStatus.READ
        ]

    @property
    def is_expired(self) -> bool:
        """Check if notification has expired."""
        if self.expires_at is None:
            return False
        return timezone.now() > self.expires_at

    @property
    def is_scheduled(self) -> bool:
        """Check if notification is scheduled for future delivery."""
        if self.scheduled_for is None:
            return False
        return timezone.now() < self.scheduled_for

    @property
    def is_urgent(self) -> bool:
        """Check if notification has urgent priority."""
        return self.priority == NotificationPriority.URGENT

    def mark_as_read(self) -> None:
        """
        Mark this notification as read.

        Sets the read_at timestamp and updates status to READ.
        """
        self.read_at = timezone.now()
        self.status = NotificationStatus.READ
        self.save(update_fields=['read_at', 'status', 'updated_at'])

    def mark_as_sent(self) -> None:
        """
        Mark this notification as sent.

        Sets the sent_at timestamp and updates status to SENT.
        """
        self.sent_at = timezone.now()
        self.status = NotificationStatus.SENT
        self.save(update_fields=['sent_at', 'status', 'updated_at'])

    def mark_as_delivered(self) -> None:
        """
        Mark this notification as delivered.

        Sets the delivered_at timestamp and updates status to DELIVERED.
        """
        self.delivered_at = timezone.now()
        self.status = NotificationStatus.DELIVERED
        self.save(update_fields=['delivered_at', 'status', 'updated_at'])

    def mark_as_failed(self, error_message: str = None) -> None:
        """
        Mark this notification as failed.

        Args:
            error_message: Optional error message to store in metadata
        """
        self.status = NotificationStatus.FAILED
        if error_message:
            self.metadata['error_message'] = error_message
            self.metadata['failed_at'] = timezone.now().isoformat()
        self.save(update_fields=['status', 'metadata', 'updated_at'])

    def archive(self) -> None:
        """
        Archive this notification.

        Sets the status to ARCHIVED for user-initiated archival.
        """
        self.status = NotificationStatus.ARCHIVED
        self.save(update_fields=['status', 'updated_at'])

    def get_data(self, key: str, default=None):
        """
        Get a value from notification data.

        Args:
            key: The data key to retrieve
            default: Default value if key not found

        Returns:
            The data value or default
        """
        return self.data.get(key, default)

    def set_data(self, key: str, value) -> None:
        """
        Set a value in notification data.

        Args:
            key: The data key
            value: The value to set
        """
        self.data[key] = value
        self.save(update_fields=['data', 'updated_at'])
