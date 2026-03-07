"""Solutions views — sector-based solution pages."""

import logging

from django.http import Http404
from django.views.generic import DetailView, ListView

from .mixins import CmsContextMixin
from ..models import Sector, SolutionPage

logger = logging.getLogger(__name__)


class SolutionsIndexView(CmsContextMixin, ListView):
    """Solutions index — sectors and featured solutions."""

    template_name = "website/solutions/index.html"
    context_object_name = "solutions"
    page_slug = "solutions"

    def get_queryset(self):
        return (
            SolutionPage.objects.filter(
                is_active=True,
                deleted_at__isnull=True,
            )
            .select_related("sector")
            .order_by("sort_order")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["sectors"] = Sector.objects.filter(
            is_active=True,
            deleted_at__isnull=True,
        ).order_by("sort_order")
        return context


class SolutionDetailView(CmsContextMixin, DetailView):
    """Solution detail page."""

    template_name = "website/solutions/detail.html"
    context_object_name = "solution"
    page_slug = "solutions"

    def get_queryset(self):
        return SolutionPage.objects.filter(
            is_active=True,
            deleted_at__isnull=True,
        ).select_related("sector")

    def get_object(self, queryset=None):
        queryset = self.get_queryset()
        slug = self.kwargs.get("slug")
        try:
            return queryset.get(slug=slug)
        except SolutionPage.DoesNotExist:
            raise Http404
