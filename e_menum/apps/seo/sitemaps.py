"""
Django sitemap framework classes for XML sitemap generation.

Provides sitemap classes for all public-facing page types:
    StaticPageSitemap       - Marketing pages (home, features, pricing, etc.)
    BlogPostSitemap         - Published blog posts
    LegalPageSitemap        - Active legal pages (privacy, terms, kvkk, etc.)
    SolutionPageSitemap     - Active solution detail pages
    CaseStudySitemap        - Published case studies
    FreeToolSitemap         - Active free tools
    IndustryReportSitemap   - Published industry reports
    WebinarSitemap          - Published webinars
    CareerPositionSitemap   - Active career positions
    PressReleaseSitemap     - Published press releases
    PartnerProgramSitemap   - Active partner programs
    HelpCategorySitemap     - Active help categories
    HelpArticleSitemap      - Active help articles
    MenuSitemap             - Public restaurant menus
    PSEOPageSitemap         - Published programmatic SEO pages

Usage in urls.py::

    from django.contrib.sitemaps.views import sitemap
    from apps.seo.sitemaps import sitemaps

    urlpatterns += [
        path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='sitemap'),
    ]
"""

import logging

from django.contrib.sitemaps import Sitemap
from django.urls import reverse

logger = logging.getLogger("apps.seo")


# ──────────────────────────────────────────────────────────────────────────────
# Static Pages
# ──────────────────────────────────────────────────────────────────────────────


class StaticPageSitemap(Sitemap):
    """
    Sitemap for static marketing pages defined in the ``website`` app.

    Returns a fixed list of URL names that are resolved via ``reverse()``.
    """

    priority = 0.8
    changefreq = "weekly"
    protocol = "https"

    # URL names from ``apps.website.urls`` (app_name = 'website')
    _page_names = [
        "website:home",
        "website:features",
        "website:pricing",
        "website:about",
        "website:contact",
        "website:demo",
        "website:blog",
        "website:solutions",
        "website:customers",
        "website:roi_calculator",
        "website:resources",
        "website:careers",
        "website:press",
        "website:brand_assets",
        "website:investor",
        "website:partners",
        "website:support",
        "website:sitemap_html",
    ]

    def items(self):
        return self._page_names

    def location(self, item):
        return reverse(item)


# ──────────────────────────────────────────────────────────────────────────────
# Blog Posts
# ──────────────────────────────────────────────────────────────────────────────


class BlogPostSitemap(Sitemap):
    """
    Sitemap for published blog posts.

    ``lastmod`` is taken from ``published_at`` falling back to ``updated_at``.
    """

    priority = 0.6
    changefreq = "monthly"
    protocol = "https"

    def items(self):
        from apps.website.models import BlogPost

        return BlogPost.objects.filter(
            status="published",
            deleted_at__isnull=True,
        ).order_by("-published_at")

    def lastmod(self, obj):
        return obj.published_at or getattr(obj, "updated_at", None)

    def location(self, obj):
        return reverse("website:blog_detail", kwargs={"slug": obj.slug})


# ──────────────────────────────────────────────────────────────────────────────
# Legal Pages
# ──────────────────────────────────────────────────────────────────────────────


class LegalPageSitemap(Sitemap):
    """
    Sitemap for active legal pages (privacy, terms, KVKK, SLA, DPA, etc.).
    """

    priority = 0.3
    changefreq = "yearly"
    protocol = "https"

    # Mapping from LegalPage.slug to website URL name
    _slug_to_url = {
        "privacy": "website:privacy",
        "terms": "website:terms",
        "kvkk": "website:kvkk",
        "cookie": "website:cookie_policy",
        "sla": "website:sla",
        "dpa": "website:dpa",
        "security": "website:security",
        "disclaimer": "website:disclaimer",
    }

    def items(self):
        from apps.website.models import LegalPage

        return LegalPage.objects.filter(
            is_active=True,
            deleted_at__isnull=True,
        )

    def lastmod(self, obj):
        return getattr(obj, "updated_at", None)

    def location(self, obj):
        url_name = self._slug_to_url.get(obj.slug)
        if url_name:
            return reverse(url_name)
        # Fallback: construct path from slug
        return f"/{obj.slug}/"


# ──────────────────────────────────────────────────────────────────────────────
# Solution Pages
# ──────────────────────────────────────────────────────────────────────────────


class SolutionPageSitemap(Sitemap):
    """Sitemap for active solution detail pages (e.g. /cozumler/<slug>/)."""

    priority = 0.7
    changefreq = "monthly"
    protocol = "https"

    def items(self):
        from apps.website.models import SolutionPage

        return SolutionPage.objects.filter(
            is_active=True,
            deleted_at__isnull=True,
        ).order_by("sort_order")

    def lastmod(self, obj):
        return getattr(obj, "updated_at", None)

    def location(self, obj):
        return reverse("website:solution_detail", kwargs={"slug": obj.slug})


# ──────────────────────────────────────────────────────────────────────────────
# Case Studies
# ──────────────────────────────────────────────────────────────────────────────


class CaseStudySitemap(Sitemap):
    """Sitemap for published case studies."""

    priority = 0.5
    changefreq = "monthly"
    protocol = "https"

    def items(self):
        from apps.website.models import CaseStudy

        return CaseStudy.objects.filter(
            is_active=True,
            deleted_at__isnull=True,
        ).order_by("-published_at")

    def lastmod(self, obj):
        return obj.published_at or getattr(obj, "updated_at", None)

    def location(self, obj):
        return reverse("website:case_study_detail", kwargs={"slug": obj.slug})


# ──────────────────────────────────────────────────────────────────────────────
# Free Tools
# ──────────────────────────────────────────────────────────────────────────────


class FreeToolSitemap(Sitemap):
    """Sitemap for active free tools."""

    priority = 0.6
    changefreq = "monthly"
    protocol = "https"

    def items(self):
        from apps.website.models import FreeTool

        return FreeTool.objects.filter(
            is_active=True,
            deleted_at__isnull=True,
        ).order_by("sort_order")

    def lastmod(self, obj):
        return getattr(obj, "updated_at", None)

    def location(self, obj):
        return reverse("website:tool_detail", kwargs={"slug": obj.slug})


# ──────────────────────────────────────────────────────────────────────────────
# Industry Reports
# ──────────────────────────────────────────────────────────────────────────────


class IndustryReportSitemap(Sitemap):
    """Sitemap for published industry reports."""

    priority = 0.5
    changefreq = "monthly"
    protocol = "https"

    def items(self):
        from apps.website.models import IndustryReport

        return IndustryReport.objects.filter(
            is_active=True,
            deleted_at__isnull=True,
        ).order_by("-published_at")

    def lastmod(self, obj):
        return obj.published_at or getattr(obj, "updated_at", None)

    def location(self, obj):
        return reverse("website:report_detail", kwargs={"slug": obj.slug})


# ──────────────────────────────────────────────────────────────────────────────
# Webinars
# ──────────────────────────────────────────────────────────────────────────────


class WebinarSitemap(Sitemap):
    """Sitemap for published webinars."""

    priority = 0.5
    changefreq = "monthly"
    protocol = "https"

    def items(self):
        from apps.website.models import Webinar

        return Webinar.objects.filter(
            is_active=True,
            deleted_at__isnull=True,
        ).order_by("-event_date")

    def lastmod(self, obj):
        return getattr(obj, "updated_at", None)

    def location(self, obj):
        return reverse("website:webinar_detail", kwargs={"slug": obj.slug})


# ──────────────────────────────────────────────────────────────────────────────
# Career Positions
# ──────────────────────────────────────────────────────────────────────────────


class CareerPositionSitemap(Sitemap):
    """Sitemap for active career positions."""

    priority = 0.5
    changefreq = "weekly"
    protocol = "https"

    def items(self):
        from apps.website.models import CareerPosition

        return CareerPosition.objects.filter(
            is_active=True,
            deleted_at__isnull=True,
        ).order_by("-created_at")

    def lastmod(self, obj):
        return getattr(obj, "updated_at", None)

    def location(self, obj):
        return reverse("website:career_detail", kwargs={"slug": obj.slug})


# ──────────────────────────────────────────────────────────────────────────────
# Press Releases
# ──────────────────────────────────────────────────────────────────────────────


class PressReleaseSitemap(Sitemap):
    """Sitemap for published press releases."""

    priority = 0.4
    changefreq = "monthly"
    protocol = "https"

    def items(self):
        from apps.website.models import PressRelease

        return PressRelease.objects.filter(
            is_active=True,
            deleted_at__isnull=True,
        ).order_by("-published_at")

    def lastmod(self, obj):
        return obj.published_at or getattr(obj, "updated_at", None)

    def location(self, obj):
        return reverse("website:press_detail", kwargs={"slug": obj.slug})


# ──────────────────────────────────────────────────────────────────────────────
# Partner Programs
# ──────────────────────────────────────────────────────────────────────────────


class PartnerProgramSitemap(Sitemap):
    """Sitemap for active partner programs."""

    priority = 0.5
    changefreq = "monthly"
    protocol = "https"

    def items(self):
        from apps.website.models import PartnerProgram

        return PartnerProgram.objects.filter(
            is_active=True,
            deleted_at__isnull=True,
        ).order_by("sort_order")

    def lastmod(self, obj):
        return getattr(obj, "updated_at", None)

    def location(self, obj):
        return reverse("website:partner_detail", kwargs={"slug": obj.slug})


# ──────────────────────────────────────────────────────────────────────────────
# Help Categories
# ──────────────────────────────────────────────────────────────────────────────


class HelpCategorySitemap(Sitemap):
    """Sitemap for active help center categories."""

    priority = 0.4
    changefreq = "monthly"
    protocol = "https"

    def items(self):
        from apps.website.models import HelpCategory

        return HelpCategory.objects.filter(
            is_active=True,
            deleted_at__isnull=True,
        ).order_by("sort_order")

    def lastmod(self, obj):
        return getattr(obj, "updated_at", None)

    def location(self, obj):
        return reverse("website:help_category", kwargs={"slug": obj.slug})


# ──────────────────────────────────────────────────────────────────────────────
# Help Articles
# ──────────────────────────────────────────────────────────────────────────────


class HelpArticleSitemap(Sitemap):
    """Sitemap for active help center articles."""

    priority = 0.4
    changefreq = "monthly"
    protocol = "https"

    def items(self):
        from apps.website.models import HelpArticle

        return (
            HelpArticle.objects.filter(
                is_active=True,
                deleted_at__isnull=True,
                category__is_active=True,
                category__deleted_at__isnull=True,
            )
            .select_related("category")
            .order_by("category__sort_order", "sort_order")
        )

    def lastmod(self, obj):
        return getattr(obj, "updated_at", None)

    def location(self, obj):
        return reverse(
            "website:help_article",
            kwargs={
                "category_slug": obj.category.slug,
                "article_slug": obj.slug,
            },
        )


# ──────────────────────────────────────────────────────────────────────────────
# Menus (Public)
# ──────────────────────────────────────────────────────────────────────────────


class MenuSitemap(Sitemap):
    """
    Sitemap for published, active menus with public URLs.
    """

    priority = 0.7
    changefreq = "weekly"
    protocol = "https"

    def items(self):
        from apps.menu.models import Menu

        return Menu.objects.filter(
            is_active=True,
            deleted_at__isnull=True,
        ).order_by("-updated_at")

    def lastmod(self, obj):
        return getattr(obj, "updated_at", None)

    def location(self, obj):
        return f"/m/{obj.slug}/"


# ──────────────────────────────────────────────────────────────────────────────
# Programmatic SEO Pages
# ──────────────────────────────────────────────────────────────────────────────


class PSEOPageSitemap(Sitemap):
    """
    Sitemap for published programmatic SEO pages.
    """

    priority = 0.5
    changefreq = "monthly"
    protocol = "https"

    def items(self):
        from apps.seo.models import PSEOPage

        return PSEOPage.objects.filter(
            is_published=True,
            deleted_at__isnull=True,
        ).order_by("-published_at")

    def lastmod(self, obj):
        return obj.published_at or getattr(obj, "updated_at", None)

    def location(self, obj):
        return f"/s/{obj.slug}/"


# ──────────────────────────────────────────────────────────────────────────────
# Module-level dict for urls.py
# ──────────────────────────────────────────────────────────────────────────────

sitemaps = {
    "static": StaticPageSitemap,
    "blog": BlogPostSitemap,
    "legal": LegalPageSitemap,
    "solutions": SolutionPageSitemap,
    "case_studies": CaseStudySitemap,
    "free_tools": FreeToolSitemap,
    "reports": IndustryReportSitemap,
    "webinars": WebinarSitemap,
    "careers": CareerPositionSitemap,
    "press": PressReleaseSitemap,
    "partners": PartnerProgramSitemap,
    "help_categories": HelpCategorySitemap,
    "help_articles": HelpArticleSitemap,
    "menus": MenuSitemap,
    "pseo": PSEOPageSitemap,
}
