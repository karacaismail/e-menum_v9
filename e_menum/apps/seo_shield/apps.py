from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class SEOShieldConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.seo_shield"
    verbose_name = _("SEO Shield")

    def ready(self):
        import apps.seo_shield.signals  # noqa: F401
