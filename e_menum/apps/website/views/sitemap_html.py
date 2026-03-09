"""HTML sitemap page view — user-facing site map for navigation."""

import logging

from django.urls import reverse, NoReverseMatch
from django.utils.translation import gettext_lazy as _
from django.views.generic import TemplateView

from .mixins import CmsContextMixin

logger = logging.getLogger(__name__)


class SitemapHTMLView(CmsContextMixin, TemplateView):
    """
    Kullanıcılar için HTML site haritası.

    Tüm public sayfaları kategorize ederek listeler.
    XML sitemap'ten farklı olarak insanlar için tasarlanmıştır.
    Dinamik içerikler (blog, araçlar, çözümler vb.) DB'den çekilir.
    """

    template_name = "website/sitemap.html"
    page_slug = "sitemap"

    @staticmethod
    def _safe_reverse(url_name):
        """Resolve a Django URL name, returning None on failure."""
        try:
            return reverse(url_name)
        except NoReverseMatch:
            logger.warning("sitemap_html: could not reverse '%s'", url_name)
            return None

    def _build_static_sections(self):
        """Return ordered list of static sitemap sections with resolved URLs."""
        raw_sections = [
            {
                "title": _("Ana Sayfalar"),
                "icon": "ph-house",
                "links": [
                    (_("Ana Sayfa"), "website:home"),
                    (_("Özellikler"), "website:features"),
                    (_("Fiyatlandırma"), "website:pricing"),
                    (_("Demo Talep Et"), "website:demo"),
                    (_("İletişim"), "website:contact"),
                ],
            },
            {
                "title": _("Çözümler"),
                "icon": "ph-lightbulb",
                "links": [
                    (_("Tüm Çözümler"), "website:solutions"),
                    (_("Müşteriler & Başarı Hikayeleri"), "website:customers"),
                    (_("ROI Hesaplayıcı"), "website:roi_calculator"),
                ],
            },
            {
                "title": _("Kaynaklar"),
                "icon": "ph-book-open",
                "links": [
                    (_("Kaynaklar Merkezi"), "website:resources"),
                    (_("Blog"), "website:blog"),
                    (_("Marka Kaynakları"), "website:brand_assets"),
                ],
            },
            {
                "title": _("Şirket"),
                "icon": "ph-buildings",
                "links": [
                    (_("Hakkımızda"), "website:about"),
                    (_("Kariyer"), "website:careers"),
                    (_("Basın"), "website:press"),
                    (_("Yatırımcı İlişkileri"), "website:investor"),
                    (_("Partnerler"), "website:partners"),
                ],
            },
            {
                "title": _("Destek"),
                "icon": "ph-headset",
                "links": [
                    (_("Yardım Merkezi"), "website:support"),
                ],
            },
            {
                "title": _("Yasal"),
                "icon": "ph-scales",
                "links": [
                    (_("Gizlilik Politikası"), "website:privacy"),
                    (_("Kullanım Şartları"), "website:terms"),
                    (_("KVKK Aydınlatma Metni"), "website:kvkk"),
                    (_("Çerez Politikası"), "website:cookie_policy"),
                ],
            },
        ]

        sections = []
        for sec in raw_sections:
            resolved = []
            for label, url_name in sec["links"]:
                url = self._safe_reverse(url_name)
                if url:
                    resolved.append({"label": str(label), "url": url})
            if resolved:
                sections.append(
                    {
                        "title": str(sec["title"]),
                        "icon": sec["icon"],
                        "links": resolved,
                    }
                )
        return sections

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["sitemap_sections"] = self._build_static_sections()

        # ── Dynamic content sections ─────────────────────────────────────
        # Blog posts
        try:
            from apps.website.models import BlogPost

            context["blog_posts"] = BlogPost.objects.filter(
                status="published",
                deleted_at__isnull=True,
            ).order_by("-published_at")[:20]
        except Exception:
            context["blog_posts"] = []

        # Free tools
        try:
            from apps.website.models import FreeTool

            context["free_tools"] = FreeTool.objects.filter(
                is_active=True,
                deleted_at__isnull=True,
            ).order_by("sort_order")
        except Exception:
            context["free_tools"] = []

        # Solution pages
        try:
            from apps.website.models import SolutionPage

            context["solution_pages"] = SolutionPage.objects.filter(
                is_active=True,
                deleted_at__isnull=True,
            ).order_by("sort_order")
        except Exception:
            context["solution_pages"] = []

        # Case studies
        try:
            from apps.website.models import CaseStudy

            context["case_studies"] = CaseStudy.objects.filter(
                is_published=True,
                deleted_at__isnull=True,
            ).order_by("-published_at")[:10]
        except Exception:
            context["case_studies"] = []

        # Industry reports
        try:
            from apps.website.models import IndustryReport

            context["industry_reports"] = IndustryReport.objects.filter(
                is_published=True,
                deleted_at__isnull=True,
            ).order_by("-published_at")[:10]
        except Exception:
            context["industry_reports"] = []

        # Webinars
        try:
            from apps.website.models import Webinar

            context["webinars"] = Webinar.objects.filter(
                is_published=True,
                deleted_at__isnull=True,
            ).order_by("-event_date")[:10]
        except Exception:
            context["webinars"] = []

        # Help categories
        try:
            from apps.website.models import HelpCategory

            context["help_categories"] = HelpCategory.objects.filter(
                is_active=True,
                deleted_at__isnull=True,
            ).order_by("sort_order")
        except Exception:
            context["help_categories"] = []

        return context
