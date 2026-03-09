"""
Django sitemap framework classes for XML sitemap generation.

Provides sitemap classes for all public-facing page types:
    StaticPageSitemap  - Marketing pages (home, features, pricing, etc.)
    BlogPostSitemap    - Published blog posts
    LegalPageSitemap   - Active legal pages (privacy, terms, kvkk)
    PSEOPageSitemap    - Published programmatic SEO pages

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
    Sitemap for active legal pages (privacy policy, terms, KVKK).
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
    "menus": MenuSitemap,
    "pseo": PSEOPageSitemap,
}
