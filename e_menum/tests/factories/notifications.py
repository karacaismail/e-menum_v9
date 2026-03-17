"""
Factory Boy factories for notifications application models.

Factories: NotificationFactory
"""

import factory
from factory.django import DjangoModelFactory

from tests.factories.core import OrganizationFactory, UserFactory


class NotificationFactory(DjangoModelFactory):
    """
    Factory for creating Notification instances.

    Examples:
        notif = NotificationFactory()
        notif = NotificationFactory(notification_type="ORDER", priority="HIGH")
    """

    class Meta:
        model = "notifications.Notification"
        skip_postgeneration_save = True

    organization = factory.SubFactory(OrganizationFactory)
    user = factory.SubFactory(UserFactory)
    title = factory.Sequence(lambda n: f"Test Notification {n}")
    message = "This is a test notification message."
    notification_type = "GENERAL"
    status = "PENDING"
    priority = "NORMAL"
    channel = "IN_APP"
    data = factory.LazyFunction(dict)
    metadata = factory.LazyFunction(dict)


class OrderNotificationFactory(NotificationFactory):
    """Factory for order-related notifications."""

    notification_type = "ORDER"
    title = "New Order Received"
    message = "A new order has been placed at Table 5."
    priority = "HIGH"


class SystemNotificationFactory(NotificationFactory):
    """Factory for system notifications."""

    notification_type = "SYSTEM"
    title = "System Update"
    message = "Scheduled maintenance at 03:00 UTC."
    priority = "LOW"
