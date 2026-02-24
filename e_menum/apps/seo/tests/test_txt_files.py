"""
Tests for apps.seo.txt_files module.

Covers:
- robots_txt_view returns text/plain with correct auto-generated content
- humans_txt_view auto-generated output
- security_txt_view auto-generated output
- ads_txt_view auto-generated output
- llms_txt_view auto-generated output
- Views with TXTFileConfig records (admin-managed content)
"""

from django.test import TestCase, RequestFactory

from apps.seo.models import TXTFileConfig, TXTFileType
from apps.seo.txt_files import (
    ads_txt_view,
    humans_txt_view,
    llms_txt_view,
    robots_txt_view,
    security_txt_view,
)


class TestRobotsTxtView(TestCase):
    """Test robots_txt_view."""

    def setUp(self):
        self.factory = RequestFactory()

    def test_returns_text_plain(self):
        request = self.factory.get('/robots.txt')
        response = robots_txt_view(request)
        self.assertEqual(response['Content-Type'], 'text/plain')

    def test_auto_generated_content(self):
        request = self.factory.get('/robots.txt')
        response = robots_txt_view(request)
        content = response.content.decode()

        self.assertIn('User-agent: *', content)
        self.assertIn('Disallow: /admin/', content)
        self.assertIn('Disallow: /api/', content)
        self.assertIn('Sitemap:', content)
        self.assertIn('sitemap.xml', content)

    def test_auto_generated_blocks_ai_bots(self):
        request = self.factory.get('/robots.txt')
        response = robots_txt_view(request)
        content = response.content.decode()

        self.assertIn('User-agent: GPTBot', content)
        self.assertIn('User-agent: CCBot', content)

    def test_admin_managed_content_overrides(self):
        TXTFileConfig.objects.create(
            file_type=TXTFileType.ROBOTS,
            content='User-agent: *\nDisallow: /private/',
            is_active=True,
            auto_generate=False,
        )
        request = self.factory.get('/robots.txt')
        response = robots_txt_view(request)
        content = response.content.decode()

        self.assertIn('Disallow: /private/', content)
        self.assertNotIn('Disallow: /admin/', content)

    def test_auto_generate_true_uses_default(self):
        TXTFileConfig.objects.create(
            file_type=TXTFileType.ROBOTS,
            content='Custom content',
            is_active=True,
            auto_generate=True,  # auto_generate=True means use default
        )
        request = self.factory.get('/robots.txt')
        response = robots_txt_view(request)
        content = response.content.decode()

        self.assertIn('User-agent: *', content)


class TestHumansTxtView(TestCase):
    """Test humans_txt_view."""

    def setUp(self):
        self.factory = RequestFactory()

    def test_returns_text_plain(self):
        request = self.factory.get('/humans.txt')
        response = humans_txt_view(request)
        self.assertEqual(response['Content-Type'], 'text/plain')

    def test_auto_generated_content(self):
        request = self.factory.get('/humans.txt')
        response = humans_txt_view(request)
        content = response.content.decode()

        self.assertIn('/* TEAM */', content)
        self.assertIn('E-Menum', content)
        self.assertIn('/* SITE */', content)
        self.assertIn('Django', content)

    def test_admin_managed_content(self):
        TXTFileConfig.objects.create(
            file_type=TXTFileType.HUMANS,
            content='/* Custom Team Info */',
            is_active=True,
            auto_generate=False,
        )
        request = self.factory.get('/humans.txt')
        response = humans_txt_view(request)
        content = response.content.decode()

        self.assertIn('/* Custom Team Info */', content)


class TestSecurityTxtView(TestCase):
    """Test security_txt_view."""

    def setUp(self):
        self.factory = RequestFactory()

    def test_returns_text_plain(self):
        request = self.factory.get('/.well-known/security.txt')
        response = security_txt_view(request)
        self.assertEqual(response['Content-Type'], 'text/plain')

    def test_auto_generated_content(self):
        request = self.factory.get('/.well-known/security.txt')
        response = security_txt_view(request)
        content = response.content.decode()

        self.assertIn('Contact: mailto:', content)
        self.assertIn('Expires:', content)
        self.assertIn('Preferred-Languages: tr, en', content)
        self.assertIn('Canonical:', content)

    def test_admin_managed_content(self):
        TXTFileConfig.objects.create(
            file_type=TXTFileType.SECURITY,
            content='Contact: mailto:custom@example.com',
            is_active=True,
            auto_generate=False,
        )
        request = self.factory.get('/.well-known/security.txt')
        response = security_txt_view(request)
        content = response.content.decode()

        self.assertIn('custom@example.com', content)


class TestAdsTxtView(TestCase):
    """Test ads_txt_view."""

    def setUp(self):
        self.factory = RequestFactory()

    def test_returns_text_plain(self):
        request = self.factory.get('/ads.txt')
        response = ads_txt_view(request)
        self.assertEqual(response['Content-Type'], 'text/plain')

    def test_auto_generated_is_placeholder(self):
        request = self.factory.get('/ads.txt')
        response = ads_txt_view(request)
        content = response.content.decode()

        self.assertIn('# ads.txt', content)
        self.assertIn('No authorized digital sellers', content)

    def test_admin_managed_content(self):
        TXTFileConfig.objects.create(
            file_type=TXTFileType.ADS,
            content='google.com, pub-1234, DIRECT',
            is_active=True,
            auto_generate=False,
        )
        request = self.factory.get('/ads.txt')
        response = ads_txt_view(request)
        content = response.content.decode()

        self.assertIn('google.com, pub-1234, DIRECT', content)


class TestLlmsTxtView(TestCase):
    """Test llms_txt_view."""

    def setUp(self):
        self.factory = RequestFactory()

    def test_returns_text_plain(self):
        request = self.factory.get('/llms.txt')
        response = llms_txt_view(request)
        self.assertEqual(response['Content-Type'], 'text/plain')

    def test_auto_generated_content(self):
        request = self.factory.get('/llms.txt')
        response = llms_txt_view(request)
        content = response.content.decode()

        self.assertIn('E-Menum', content)
        self.assertIn('## About', content)
        self.assertIn('## Usage Policy', content)
        self.assertIn('## Attribution', content)
        self.assertIn('## Pages', content)

    def test_admin_managed_content(self):
        TXTFileConfig.objects.create(
            file_type=TXTFileType.LLMS,
            content='# Custom LLMs Policy\nDo not scrape.',
            is_active=True,
            auto_generate=False,
        )
        request = self.factory.get('/llms.txt')
        response = llms_txt_view(request)
        content = response.content.decode()

        self.assertIn('# Custom LLMs Policy', content)
        self.assertIn('Do not scrape.', content)

    def test_inactive_config_uses_auto_generated(self):
        TXTFileConfig.objects.create(
            file_type=TXTFileType.LLMS,
            content='# Should not appear',
            is_active=False,
            auto_generate=False,
        )
        request = self.factory.get('/llms.txt')
        response = llms_txt_view(request)
        content = response.content.decode()

        self.assertIn('## About', content)
        self.assertNotIn('# Should not appear', content)
