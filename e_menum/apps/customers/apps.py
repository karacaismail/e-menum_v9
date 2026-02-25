"""
Django AppConfig for the Customers application.

This configuration defines the customers app's metadata and initialization behavior.
"""

from django.apps import AppConfig


class CustomersConfig(AppConfig):
    """
    Configuration for the E-Menum Customers application.

    This app provides customer-related models and functionality:
    - Customer management and profiles
    - Visit tracking for analytics
    - Feedback collection and management
    - Loyalty points system
    """

    # Application identifier - must match the import path
    name = 'apps.customers'

    # Human-readable name for admin
    verbose_name = 'Customers'

    # Use BigAutoField for auto-generated primary keys
    default_auto_field = 'django.db.models.BigAutoField'

    def ready(self):
        """
        Perform initialization when the app is ready.

        This method is called once Django has finished loading.
        Used for signal registration and other startup tasks.
        """
        # Import signals to register them
        try:
            from apps.customers import signals  # noqa: F401
        except ImportError:
            pass
