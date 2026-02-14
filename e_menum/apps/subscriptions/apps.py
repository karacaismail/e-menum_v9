"""
Django AppConfig for the Subscriptions application.

This configuration defines the subscriptions app's metadata and initialization behavior.
"""

from django.apps import AppConfig


class SubscriptionsConfig(AppConfig):
    """
    Configuration for the E-Menum Subscriptions application.

    This app provides subscription and billing functionality:
    - Plan management (Free, Starter, Growth, Professional, Enterprise)
    - Subscription lifecycle (trial, active, past_due, cancelled, expired)
    - Invoice generation and management
    - Payment method handling
    - Feature access control based on plan tier
    """

    # Application identifier - must match the import path
    name = 'apps.subscriptions'

    # Human-readable name for admin
    verbose_name = 'Subscriptions & Billing'

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
        #     from apps.subscriptions import signals  # noqa: F401
        # except ImportError:
        #     pass
        pass
