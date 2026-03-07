"""
App configuration for the Reporting application.
"""

from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class ReportingConfig(AppConfig):
    """Configuration for the Reporting application."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.reporting"
    verbose_name = _("Reporting")

    def ready(self):
        """
        Register report handlers when app is ready.
        Import handlers so they auto-register with the ReportEngine.
        """
        import apps.reporting.handlers.registry  # noqa: F401
