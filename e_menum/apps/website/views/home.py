"""Home page view."""

import logging

from django.views.generic import TemplateView

from .mixins import CmsContextMixin
from ..models import (
    CompanyStat,
    HomeSection,
    Testimonial,
    TrustBadge,
    TrustLocation,
)

logger = logging.getLogger(__name__)


class HomeView(CmsContextMixin, TemplateView):
    """Ana sayfa — landing page with hero, features, pricing summary, etc."""

    template_name = "website/home.html"
    page_slug = "home"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Problem / Solution cards
        context["problem_solution_cards"] = HomeSection.objects.filter(
            section_type="problem_solution",
            is_active=True,
        ).order_by("sort_order")

        # Feature cards
        context["feature_cards"] = HomeSection.objects.filter(
            section_type="feature_card",
            is_active=True,
        ).order_by("sort_order")

        # How it works steps
        context["how_it_works_steps"] = HomeSection.objects.filter(
            section_type="how_it_works",
            is_active=True,
        ).order_by("step_number", "sort_order")

        # Stat counters — single source: CompanyStat (managed via CMS admin)
        context["stat_counters"] = CompanyStat.objects.filter(
            is_active=True,
            deleted_at__isnull=True,
        ).order_by("sort_order")

        # Testimonials
        context["testimonials"] = Testimonial.objects.filter(
            is_active=True,
            deleted_at__isnull=True,
        ).order_by("sort_order")

        # Trust badges & locations
        context["trust_badges"] = TrustBadge.objects.filter(
            is_active=True,
            deleted_at__isnull=True,
        ).order_by("sort_order")
        context["trust_locations"] = TrustLocation.objects.filter(
            is_active=True,
            deleted_at__isnull=True,
        ).order_by("sort_order")

        # Pricing plans — all public plans for pricing section
        try:
            from apps.subscriptions.models import Plan

            context["plans"] = (
                Plan.objects.filter(
                    is_active=True,
                    is_public=True,
                    deleted_at__isnull=True,
                )
                .prefetch_related("display_features")
                .order_by("sort_order")
            )
        except Exception:
            context["plans"] = []

        return context
