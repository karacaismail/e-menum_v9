"""
Django AppConfig for the Orders application.

This configuration defines the orders app's metadata and initialization behavior.
"""

from django.apps import AppConfig


class OrdersConfig(AppConfig):
    """
    Configuration for the E-Menum Orders application.

    This app provides order management functionality:
    - Zone and table management
    - QR code generation and tracking
    - Order creation and lifecycle management
    - Order item management
    - Service request handling (waiter calls, bill requests)
    """

    # Application identifier - must match the import path
    name = 'apps.orders'

    # Human-readable name for admin
    verbose_name = 'Order Management'

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
        #     from apps.orders import signals  # noqa: F401
        # except ImportError:
        #     pass
        pass
