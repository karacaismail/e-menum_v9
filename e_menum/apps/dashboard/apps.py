"""
Dashboard application configuration.

Provides the main admin dashboard (mainboard) with KPI widgets,
charts, insights, and command palette functionality.
"""

from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class DashboardConfig(AppConfig):
    """Dashboard app configuration."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.dashboard'
    verbose_name = _('Dashboard')
    label = 'dashboard'

    def ready(self):
        """Import signals and register tasks on app ready."""
        pass
