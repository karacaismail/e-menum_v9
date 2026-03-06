"""Resource views — reports, tools, webinars."""
import logging

from django.http import Http404
from django.views.generic import DetailView, TemplateView

from .mixins import CmsContextMixin
from ..models import FreeTool, IndustryReport, ResourceCategory, Webinar

logger = logging.getLogger(__name__)


class ResourcesView(CmsContextMixin, TemplateView):
    """Resources hub — lists all resource types."""
    template_name = 'website/resources/index.html'
    page_slug = 'resources'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['reports'] = IndustryReport.objects.filter(
            is_active=True, deleted_at__isnull=True,
        ).order_by('-created_at')[:4]
        context['tools'] = FreeTool.objects.filter(
            is_active=True, deleted_at__isnull=True,
        ).order_by('sort_order')[:4]
        context['webinars'] = Webinar.objects.filter(
            is_active=True, deleted_at__isnull=True,
        ).order_by('-event_date')[:4]
        context['categories'] = ResourceCategory.objects.filter(
            is_active=True, deleted_at__isnull=True,
        ).order_by('sort_order')
        return context


class ReportDetailView(CmsContextMixin, DetailView):
    """Industry report detail."""
    template_name = 'website/resources/report_detail.html'
    context_object_name = 'report'
    page_slug = 'resources'

    def get_queryset(self):
        return IndustryReport.objects.filter(is_active=True, deleted_at__isnull=True)

    def get_object(self, queryset=None):
        queryset = self.get_queryset()
        slug = self.kwargs.get('slug')
        try:
            return queryset.get(slug=slug)
        except IndustryReport.DoesNotExist:
            raise Http404


class ToolDetailView(CmsContextMixin, DetailView):
    """Free tool detail."""
    template_name = 'website/resources/tool_detail.html'
    context_object_name = 'tool'
    page_slug = 'resources'

    def get_queryset(self):
        return FreeTool.objects.filter(is_active=True, deleted_at__isnull=True)

    def get_object(self, queryset=None):
        queryset = self.get_queryset()
        slug = self.kwargs.get('slug')
        try:
            return queryset.get(slug=slug)
        except FreeTool.DoesNotExist:
            raise Http404


class WebinarDetailView(CmsContextMixin, DetailView):
    """Webinar detail."""
    template_name = 'website/resources/webinar_detail.html'
    context_object_name = 'webinar'
    page_slug = 'resources'

    def get_queryset(self):
        return Webinar.objects.filter(is_active=True, deleted_at__isnull=True)

    def get_object(self, queryset=None):
        queryset = self.get_queryset()
        slug = self.kwargs.get('slug')
        try:
            return queryset.get(slug=slug)
        except Webinar.DoesNotExist:
            raise Http404
