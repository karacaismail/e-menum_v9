"""
Django AppConfig for the Core application.

This configuration defines the core app's metadata and initialization behavior.
"""

from django.apps import AppConfig


class CoreConfig(AppConfig):
    """
    Configuration for the E-Menum Core application.

    This app provides foundational models and functionality:
    - Organization (tenant) management
    - User authentication and management
    - Role-based access control (RBAC)
    - Permission definitions
    - Session management
    - Audit logging
    """

    # Application identifier - must match the import path
    name = 'apps.core'

    # Human-readable name for admin
    verbose_name = 'Core'

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
        #     from apps.core import signals  # noqa: F401
        # except ImportError:
        #     pass
        pass
