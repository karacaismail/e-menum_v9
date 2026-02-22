"""
Django AppConfig for the Notifications application.

This configuration defines the notifications app's metadata and initialization behavior.
"""

from django.apps import AppConfig


class NotificationsConfig(AppConfig):
    """
    Configuration for the E-Menum Notifications application.

    This app provides notification management functionality:
    - User notification delivery and tracking
    - System notifications for alerts and updates
    - Order-related notifications (status changes, confirmations)
    - Promotional notifications for marketing campaigns
    - Read/unread status tracking
    - Notification scheduling and prioritization
    """

    # Application identifier - must match the import path
    name = 'apps.notifications'

    # Human-readable name for admin
    verbose_name = 'Notification Management'

    # Use BigAutoField for auto-generated primary keys
    default_auto_field = 'django.db.models.BigAutoField'

    def ready(self):
        """
        Perform initialization when the app is ready.

        This method is called once Django has finished loading.
        Used for signal registration and other startup tasks.
        """
        # Import signals to register them
        # Note: Uncomment when signals module is created
        # try:
        #     from apps.notifications import signals  # noqa: F401
        # except ImportError:
        #     pass
        pass
