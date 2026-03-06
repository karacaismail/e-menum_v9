"""About page view."""
import logging

from django.views.generic import TemplateView

from .mixins import CmsContextMixin
from ..models import TeamMember, CompanyValue, CompanyStat

logger = logging.getLogger(__name__)


class AboutView(CmsContextMixin, TemplateView):
    """Hakkimizda sayfasi — company story, team, values."""
    template_name = 'website/about.html'
    page_slug = 'about'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['team_members'] = TeamMember.objects.filter(
            is_active=True, deleted_at__isnull=True,
        ).order_by('sort_order')
        context['company_values'] = CompanyValue.objects.filter(
            is_active=True, deleted_at__isnull=True,
        ).order_by('sort_order')
        context['company_stats'] = CompanyStat.objects.filter(
            is_active=True, deleted_at__isnull=True,
        ).order_by('sort_order')
        return context
