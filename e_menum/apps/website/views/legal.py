"""Legal page views — privacy, terms, KVKK, cookie policy."""

import logging

from django.http import Http404
from django.views.generic import TemplateView

from .mixins import CmsContextMixin
from ..models import LegalPage

logger = logging.getLogger(__name__)


class LegalPageView(CmsContextMixin, TemplateView):
    """
    Generic legal page view — renders content from LegalPage model.

    Used for privacy, terms, kvkk, and cookie policy pages.
    """

    template_name = "website/legal_page.html"
    legal_slug = None  # Set by URL config or subclass

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        slug = self.legal_slug or self.kwargs.get("slug")
        legal = LegalPage.objects.filter(slug=slug, is_active=True).first()
        if not legal:
            raise Http404
        context["legal"] = legal
        return context


# Convenience subclasses with fixed slug
class PrivacyView(LegalPageView):
    legal_slug = "privacy"


class TermsView(LegalPageView):
    legal_slug = "terms"


class KvkkView(LegalPageView):
    legal_slug = "kvkk"


class CookiePolicyView(LegalPageView):
    legal_slug = "cookie"


class SlaView(LegalPageView):
    legal_slug = "sla"


class DpaView(LegalPageView):
    legal_slug = "dpa"


class SecurityPolicyView(LegalPageView):
    legal_slug = "security"


class DisclaimerView(LegalPageView):
    legal_slug = "disclaimer"
