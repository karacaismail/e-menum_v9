"""
Django TextChoices enums for notifications module.

These enums define the valid values for status fields and other constrained
string fields across the notifications domain models.

Usage:
    from apps.notifications.choices import NotificationType, NotificationStatus

    class Notification(models.Model):
        notification_type = models.CharField(
            max_length=20,
            choices=NotificationType.choices,
            default=NotificationType.GENERAL
        )
"""

from django.db import models


class NotificationType(models.TextChoices):
    """
    Type values for Notification categorization.

    - ORDER: Order-related notifications (status changes, confirmations)
    - SYSTEM: System alerts and updates (maintenance, new features)
    - PROMOTION: Marketing and promotional notifications
    - PAYMENT: Payment-related notifications (invoices, receipts)
    - FEEDBACK: Customer feedback notifications
    - SECURITY: Security alerts (login attempts, password changes)
    - GENERAL: General notifications that don't fit other categories
    """
    ORDER = 'ORDER', 'Order'
    SYSTEM = 'SYSTEM', 'System'
    PROMOTION = 'PROMOTION', 'Promotion'
    PAYMENT = 'PAYMENT', 'Payment'
    FEEDBACK = 'FEEDBACK', 'Feedback'
    SECURITY = 'SECURITY', 'Security'
    GENERAL = 'GENERAL', 'General'


class NotificationStatus(models.TextChoices):
    """
    Status values for Notification lifecycle.

    Notifications follow this progression:
    PENDING → SENT → DELIVERED → READ

    - PENDING: Notification created but not yet sent
    - SENT: Notification has been sent to delivery channel
    - DELIVERED: Notification confirmed delivered to recipient
    - READ: Recipient has read/viewed the notification
    - ARCHIVED: Notification has been archived by user
    - FAILED: Notification delivery failed
    """
    PENDING = 'PENDING', 'Pending'
    SENT = 'SENT', 'Sent'
    DELIVERED = 'DELIVERED', 'Delivered'
    READ = 'READ', 'Read'
    ARCHIVED = 'ARCHIVED', 'Archived'
    FAILED = 'FAILED', 'Failed'


class NotificationPriority(models.TextChoices):
    """
    Priority levels for Notification delivery and display.

    - LOW: Non-urgent notifications (weekly summaries, tips)
    - NORMAL: Standard priority notifications
    - HIGH: Important notifications requiring attention
    - URGENT: Critical notifications requiring immediate attention
    """
    LOW = 'LOW', 'Low'
    NORMAL = 'NORMAL', 'Normal'
    HIGH = 'HIGH', 'High'
    URGENT = 'URGENT', 'Urgent'


class NotificationChannel(models.TextChoices):
    """
    Delivery channel for notifications.

    - IN_APP: In-application notifications (bell icon, notification center)
    - PUSH: Push notifications (mobile/browser)
    - EMAIL: Email notifications
    - SMS: SMS text message notifications
    """
    IN_APP = 'IN_APP', 'In-App'
    PUSH = 'PUSH', 'Push'
    EMAIL = 'EMAIL', 'Email'
    SMS = 'SMS', 'SMS'
