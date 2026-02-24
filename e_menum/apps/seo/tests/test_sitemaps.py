"""
Tests for apps.seo.sitemaps module.

Covers:
- StaticPageSitemap items list
- BlogPostSitemap with published posts
- PSEOPageSitemap with published pages
- Sitemap module-level dict
"""

from django.test import TestCase
from django.utils import timezone

from apps.seo.models import PSEOPage, PSEOTemplate
from apps.seo.sitemaps import (
    PSEOPageSitemap,
    StaticPageSitemap,
    sitemaps,
)


class TestStaticPageSitemap(TestCase):
    """Test StaticPageSitemap."""

    def test_items_returns_page_names(self):
        sitemap = StaticPageSitemap()
        items = sitemap.items()

        self.assertIsInstance(items, list)
        self.assertIn('website:home', items)
        self.assertIn('website:features', items)
        self.assertIn('website:pricing', items)
        self.assertIn('website:about', items)
        self.assertIn('website:contact', items)
        self.assertIn('website:demo', items)
        self.assertIn('website:blog', items)

    def test_priority(self):
        sitemap = StaticPageSitemap()
        self.assertEqual(sitemap.priority, 0.8)

    def test_changefreq(self):
        sitemap = StaticPageSitemap()
        self.assertEqual(sitemap.changefreq, 'weekly')

    def test_protocol_is_https(self):
        sitemap = StaticPageSitemap()
        self.assertEqual(sitemap.protocol, 'https')


class TestPSEOPageSitemap(TestCase):
    """Test PSEOPageSitemap."""

    def setUp(self):
        self.template = PSEOTemplate.objects.create(
            name='Sitemap Test Template',
            slug_template='{sehir}-test',
            title_template='{sehir} Test',
            description_template='Desc for {sehir}.',
            content_template='Content for {sehir}.',
        )

    def test_items_returns_only_published(self):
        # Published page
        PSEOPage.objects.create(
            template=self.template,
            slug='published-page',
            rendered_title='Published',
            is_published=True,
            published_at=timezone.now(),
        )
        # Unpublished page
        PSEOPage.objects.create(
            template=self.template,
            slug='unpublished-page',
            rendered_title='Draft',
            is_published=False,
        )
        # Soft-deleted published page
        PSEOPage.objects.create(
            template=self.template,
            slug='deleted-page',
            rendered_title='Deleted',
            is_published=True,
            published_at=timezone.now(),
            deleted_at=timezone.now(),
        )

        sitemap = PSEOPageSitemap()
        items = list(sitemap.items())

        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].slug, 'published-page')

    def test_location(self):
        page = PSEOPage.objects.create(
            template=self.template,
            slug='istanbul-kafe',
            rendered_title='Istanbul Kafe',
            is_published=True,
            published_at=timezone.now(),
        )
        sitemap = PSEOPageSitemap()
        self.assertEqual(sitemap.location(page), '/s/istanbul-kafe/')

    def test_lastmod_uses_published_at(self):
        now = timezone.now()
        page = PSEOPage.objects.create(
            template=self.template,
            slug='lastmod-test',
            is_published=True,
            published_at=now,
        )
        sitemap = PSEOPageSitemap()
        self.assertEqual(sitemap.lastmod(page), now)

    def test_lastmod_falls_back_to_updated_at(self):
        page = PSEOPage.objects.create(
            template=self.template,
            slug='no-pubdate',
            is_published=True,
            published_at=None,
        )
        sitemap = PSEOPageSitemap()
        result = sitemap.lastmod(page)
        # Falls back to updated_at
        self.assertEqual(result, page.updated_at)

    def test_priority(self):
        sitemap = PSEOPageSitemap()
        self.assertEqual(sitemap.priority, 0.5)

    def test_changefreq(self):
        sitemap = PSEOPageSitemap()
        self.assertEqual(sitemap.changefreq, 'monthly')


class TestSitemapsDict(TestCase):
    """Test the module-level sitemaps dict."""

    def test_sitemaps_contains_expected_keys(self):
        self.assertIn('static', sitemaps)
        self.assertIn('blog', sitemaps)
        self.assertIn('legal', sitemaps)
        self.assertIn('pseo', sitemaps)

    def test_sitemaps_values_are_classes(self):
        for key, cls in sitemaps.items():
            self.assertTrue(
                callable(cls),
                f'sitemaps[{key!r}] should be a callable class',
            )
