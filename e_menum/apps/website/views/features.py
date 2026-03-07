"""Features page view."""

import logging

from django.views.generic import TemplateView

from .mixins import CmsContextMixin
from ..models import CompanyStat, FeatureCategory

logger = logging.getLogger(__name__)


class FeaturesView(CmsContextMixin, TemplateView):
    """Ozellikler sayfasi — detailed feature showcase."""

    template_name = "website/features.html"
    page_slug = "features"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["feature_categories"] = (
            FeatureCategory.objects.filter(
                is_active=True,
                deleted_at__isnull=True,
            )
            .prefetch_related("bullets")
            .order_by("sort_order")
        )

        context["stat_counters"] = CompanyStat.objects.filter(
            is_active=True,
            deleted_at__isnull=True,
        ).order_by("sort_order")
        return context
