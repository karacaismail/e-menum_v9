"""
Django AppConfig for the Media application.

This configuration defines the media app's metadata and initialization behavior.
"""

from django.apps import AppConfig


class MediaConfig(AppConfig):
    """
    Configuration for the E-Menum Media application.

    This app provides media management functionality:
    - Media file storage and retrieval
    - Folder organization for media assets
    - Support for multiple storage backends
    - Image, video, document, and audio handling
    """

    # Application identifier - must match the import path
    name = 'apps.media'

    # Human-readable name for admin
    verbose_name = 'Media'

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
        #     from apps.media import signals  # noqa: F401
        # except ImportError:
        #     pass
        pass
