"""Investor relations view."""

import logging

from django.views.generic import TemplateView

from .mixins import CmsContextMixin
from ..models import InvestorFinancial, InvestorPage, InvestorPresentation, Milestone

logger = logging.getLogger(__name__)


class InvestorView(CmsContextMixin, TemplateView):
    """Investor relations page."""

    template_name = "website/investor/index.html"
    page_slug = "investor"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_data"] = InvestorPage.objects.first()
        context["presentations"] = InvestorPresentation.objects.filter(
            is_active=True,
            deleted_at__isnull=True,
        ).order_by("-presentation_date")
        context["financials"] = InvestorFinancial.objects.filter(
            is_active=True,
            deleted_at__isnull=True,
        ).order_by("-period", "metric_name")
        context["milestones"] = Milestone.objects.filter(
            is_active=True,
            deleted_at__isnull=True,
        ).order_by("-year", "-quarter")
        return context
