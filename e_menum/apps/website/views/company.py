"""Company views — careers, press, brand assets."""
import logging

from django.http import Http404
from django.views.generic import DetailView, ListView, TemplateView

from .mixins import CmsContextMixin
from ..models import BrandAsset, CareerPosition, Milestone, PressRelease

logger = logging.getLogger(__name__)


class CareersView(CmsContextMixin, ListView):
    """Careers listing page."""
    template_name = 'website/company/careers.html'
    context_object_name = 'positions'
    page_slug = 'careers'

    def get_queryset(self):
        return CareerPosition.objects.filter(
            is_active=True, deleted_at__isnull=True,
        ).order_by('-created_at')


class CareerDetailView(CmsContextMixin, DetailView):
    """Career position detail."""
    template_name = 'website/company/career_detail.html'
    context_object_name = 'position'
    page_slug = 'careers'

    def get_queryset(self):
        return CareerPosition.objects.filter(is_active=True, deleted_at__isnull=True)

    def get_object(self, queryset=None):
        queryset = self.get_queryset()
        slug = self.kwargs.get('slug')
        try:
            return queryset.get(slug=slug)
        except CareerPosition.DoesNotExist:
            raise Http404


class PressView(CmsContextMixin, ListView):
    """Press releases listing."""
    template_name = 'website/company/press.html'
    context_object_name = 'releases'
    page_slug = 'press'

    def get_queryset(self):
        return PressRelease.objects.filter(
            is_active=True, deleted_at__isnull=True,
        ).order_by('-published_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['milestones'] = Milestone.objects.filter(
            is_active=True,
        ).order_by('-year', '-quarter')
        return context


class PressDetailView(CmsContextMixin, DetailView):
    """Press release detail."""
    template_name = 'website/company/press_detail.html'
    context_object_name = 'release'
    page_slug = 'press'

    def get_queryset(self):
        return PressRelease.objects.filter(is_active=True, deleted_at__isnull=True)

    def get_object(self, queryset=None):
        queryset = self.get_queryset()
        slug = self.kwargs.get('slug')
        try:
            return queryset.get(slug=slug)
        except PressRelease.DoesNotExist:
            raise Http404


class BrandAssetsView(CmsContextMixin, TemplateView):
    """Brand assets / media kit page."""
    template_name = 'website/company/brand_assets.html'
    page_slug = 'press'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['assets'] = BrandAsset.objects.filter(
            is_active=True,
        ).order_by('category', 'sort_order')
        return context
