"""Customer views — case studies and ROI calculator."""
import logging

from django.http import Http404
from django.views.generic import DetailView, ListView, TemplateView

from .mixins import CmsContextMixin
from ..models import CaseStudy, ROICalculatorConfig, Sector, Testimonial

logger = logging.getLogger(__name__)


class CustomersView(CmsContextMixin, ListView):
    """Customers index — featured case studies + testimonials."""
    template_name = 'website/customers/index.html'
    context_object_name = 'case_studies'
    page_slug = 'customers'

    def get_queryset(self):
        return CaseStudy.objects.filter(
            is_active=True, deleted_at__isnull=True,
        ).select_related('sector').order_by('-is_featured', 'sort_order')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['testimonials'] = Testimonial.objects.filter(
            is_active=True, deleted_at__isnull=True,
        ).order_by('sort_order')[:6]
        context['sectors'] = Sector.objects.filter(
            is_active=True, deleted_at__isnull=True,
        ).order_by('sort_order')
        return context


class CaseStudyDetailView(CmsContextMixin, DetailView):
    """Case study detail page."""
    template_name = 'website/customers/case_study_detail.html'
    context_object_name = 'case_study'
    page_slug = 'customers'

    def get_queryset(self):
        return CaseStudy.objects.filter(
            is_active=True, deleted_at__isnull=True,
        ).select_related('sector')

    def get_object(self, queryset=None):
        queryset = self.get_queryset()
        slug = self.kwargs.get('slug')
        try:
            return queryset.get(slug=slug)
        except CaseStudy.DoesNotExist:
            raise Http404


class ROICalculatorView(CmsContextMixin, TemplateView):
    """ROI calculator page."""
    template_name = 'website/customers/roi_calculator.html'
    page_slug = 'customers'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['config'] = ROICalculatorConfig.objects.first()
        return context
