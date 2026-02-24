"""Partner program views."""
import logging

from django.http import Http404
from django.views.generic import DetailView, ListView

from .mixins import CmsContextMixin
from ..models import PartnerProgram

logger = logging.getLogger(__name__)


class PartnersView(CmsContextMixin, ListView):
    """Partner programs listing."""
    template_name = 'website/partners/index.html'
    context_object_name = 'programs'
    page_slug = 'partners'

    def get_queryset(self):
        return PartnerProgram.objects.filter(
            is_active=True, deleted_at__isnull=True,
        ).prefetch_related('tiers__benefits').order_by('sort_order')


class PartnerProgramDetailView(CmsContextMixin, DetailView):
    """Partner program detail with tiers and benefits."""
    template_name = 'website/partners/program_detail.html'
    context_object_name = 'program'
    page_slug = 'partners'

    def get_queryset(self):
        return PartnerProgram.objects.filter(
            is_active=True, deleted_at__isnull=True,
        ).prefetch_related('tiers__benefits')

    def get_object(self, queryset=None):
        queryset = self.get_queryset()
        slug = self.kwargs.get('slug')
        try:
            return queryset.get(slug=slug)
        except PartnerProgram.DoesNotExist:
            raise Http404
