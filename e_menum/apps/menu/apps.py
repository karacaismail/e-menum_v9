"""
Django AppConfig for the Menu application.

This configuration defines the menu app's metadata and initialization behavior.
"""

from django.apps import AppConfig


class MenuConfig(AppConfig):
    """
    Configuration for the E-Menum Menu application.

    This app provides menu management functionality:
    - Menu creation and customization
    - Category organization
    - Product management with variants and modifiers
    - Allergen tracking
    - Theme and styling options
    """

    # Application identifier - must match the import path
    name = "apps.menu"

    # Human-readable name for admin
    verbose_name = "Menu Management"

    # Use BigAutoField for auto-generated primary keys
    default_auto_field = "django.db.models.BigAutoField"

    def ready(self):
        """
        Perform initialization when the app is ready.

        This method is called once Django has finished loading.
        Used for signal registration and other startup tasks.
        """
        # Import signals to register them
        # Note: Uncomment when signals module is created
        # try:
        #     from apps.menu import signals  # noqa: F401
        # except ImportError:
        #     pass
        pass
