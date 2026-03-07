from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class SEOConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.seo"
    verbose_name = _("SEO Yonetimi")

    def ready(self):
        import apps.seo.signals  # noqa: F401
