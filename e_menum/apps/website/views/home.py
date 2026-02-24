"""Home page view."""
import logging

from django.views.generic import TemplateView

from .mixins import CmsContextMixin
from ..models import HomeSection, Testimonial, TrustBadge, TrustLocation

logger = logging.getLogger(__name__)


class HomeView(CmsContextMixin, TemplateView):
    """Ana sayfa — landing page with hero, features, pricing summary, etc."""
    template_name = 'website/home.html'
    page_slug = 'home'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Problem / Solution cards
        context['problem_solution_cards'] = HomeSection.objects.filter(
            section_type='problem_solution', is_active=True,
        ).order_by('sort_order')

        # Feature cards
        context['feature_cards'] = HomeSection.objects.filter(
            section_type='feature_card', is_active=True,
        ).order_by('sort_order')

        # How it works steps
        context['how_it_works_steps'] = HomeSection.objects.filter(
            section_type='how_it_works', is_active=True,
        ).order_by('step_number', 'sort_order')

        # Stat counters
        context['stat_counters'] = HomeSection.objects.filter(
            section_type='stat_counter', is_active=True,
        ).order_by('sort_order')

        # Testimonials
        context['testimonials'] = Testimonial.objects.filter(
            is_active=True,
        ).order_by('sort_order')

        # Trust badges & locations
        context['trust_badges'] = TrustBadge.objects.filter(
            is_active=True,
        ).order_by('sort_order')
        context['trust_locations'] = TrustLocation.objects.filter(
            is_active=True,
        ).order_by('sort_order')

        # Pricing summary — top 3 plans from subscriptions
        try:
            from apps.subscriptions.models import Plan
            context['summary_plans'] = Plan.objects.filter(
                is_active=True, is_public=True,
            ).prefetch_related('display_features').order_by('sort_order')[:3]
        except Exception:
            context['summary_plans'] = []

        return context
