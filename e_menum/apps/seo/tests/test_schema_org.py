"""
Tests for apps.seo.schema_org module.

Covers:
- SchemaBuilder base class
- OrganizationSchema to_dict() output
- ArticleSchema with mock blog post data
- FAQPageSchema with questions/answers
- BreadcrumbListSchema items
- to_json_ld() produces valid script tag output
"""

import json
from types import SimpleNamespace
from unittest.mock import MagicMock

from django.test import TestCase

from apps.seo.schema_org import (
    ArticleSchema,
    BreadcrumbListSchema,
    FAQPageSchema,
    LocalBusinessSchema,
    OrganizationSchema,
    ProductSchema,
    SchemaBuilder,
    WebPageSchema,
)


class TestSchemaBuilder(TestCase):
    """Test the abstract SchemaBuilder base class."""

    def test_base_context_returns_context_and_type(self):
        builder = SchemaBuilder()
        ctx = builder._base_context()
        self.assertEqual(ctx['@context'], 'https://schema.org')
        self.assertEqual(ctx['@type'], 'Thing')

    def test_to_dict_raises_not_implemented(self):
        builder = SchemaBuilder()
        with self.assertRaises(NotImplementedError):
            builder.to_dict()

    def test_clean_returns_stripped_string(self):
        self.assertEqual(SchemaBuilder._clean('  hello  '), 'hello')

    def test_clean_returns_none_for_empty(self):
        self.assertIsNone(SchemaBuilder._clean(''))
        self.assertIsNone(SchemaBuilder._clean('   '))
        self.assertIsNone(SchemaBuilder._clean(None))


class TestOrganizationSchema(TestCase):
    """Test OrganizationSchema."""

    def _make_settings(self, **kwargs):
        defaults = {
            'company_name': 'E-Menum',
            'description': 'Enterprise QR Menu SaaS',
            'phone': '+90 212 555 0000',
            'email': 'info@e-menum.net',
            'address': 'Istanbul, Turkey',
            'social_instagram': 'https://instagram.com/emenum',
            'social_twitter': 'https://twitter.com/emenum',
            'social_linkedin': '',
            'social_youtube': '',
        }
        defaults.update(kwargs)
        return SimpleNamespace(**defaults)

    def test_to_dict_basic_fields(self):
        settings = self._make_settings()
        schema = OrganizationSchema(settings)
        data = schema.to_dict()

        self.assertEqual(data['@context'], 'https://schema.org')
        self.assertEqual(data['@type'], 'Organization')
        self.assertEqual(data['name'], 'E-Menum')
        self.assertEqual(data['description'], 'Enterprise QR Menu SaaS')
        self.assertEqual(data['telephone'], '+90 212 555 0000')
        self.assertEqual(data['email'], 'info@e-menum.net')

    def test_to_dict_address(self):
        settings = self._make_settings()
        schema = OrganizationSchema(settings)
        data = schema.to_dict()

        self.assertIn('address', data)
        self.assertEqual(data['address']['@type'], 'PostalAddress')
        self.assertEqual(data['address']['addressLocality'], 'Istanbul, Turkey')

    def test_to_dict_social_profiles(self):
        settings = self._make_settings()
        schema = OrganizationSchema(settings)
        data = schema.to_dict()

        self.assertIn('sameAs', data)
        self.assertIn('https://instagram.com/emenum', data['sameAs'])
        self.assertIn('https://twitter.com/emenum', data['sameAs'])
        self.assertEqual(len(data['sameAs']), 2)

    def test_to_dict_contact_point(self):
        settings = self._make_settings()
        schema = OrganizationSchema(settings)
        data = schema.to_dict()

        self.assertIn('contactPoint', data)
        self.assertEqual(data['contactPoint']['@type'], 'ContactPoint')
        self.assertEqual(data['contactPoint']['contactType'], 'customer service')

    def test_to_dict_without_optional_fields(self):
        settings = self._make_settings(
            phone='', email='', address='', description='',
            social_instagram='', social_twitter='',
        )
        schema = OrganizationSchema(settings)
        data = schema.to_dict()

        self.assertNotIn('telephone', data)
        self.assertNotIn('email', data)
        self.assertNotIn('address', data)
        self.assertNotIn('description', data)
        self.assertNotIn('sameAs', data)
        self.assertNotIn('contactPoint', data)

    def test_name_defaults_to_emenum(self):
        settings = self._make_settings(company_name='')
        schema = OrganizationSchema(settings)
        data = schema.to_dict()
        self.assertEqual(data['name'], 'E-Menum')


class TestArticleSchema(TestCase):
    """Test ArticleSchema."""

    def _make_post(self, **kwargs):
        defaults = {
            'title': 'How to Create QR Menus',
            'excerpt': 'A guide to digital menus.',
            'slug': 'how-to-create-qr-menus',
            'published_at': None,
            'updated_at': None,
            'author_name': 'Jane Doe',
            'content': 'This is the full article content with many words.',
        }
        defaults.update(kwargs)
        return SimpleNamespace(**defaults)

    def test_to_dict_basic(self):
        post = self._make_post()
        schema = ArticleSchema(post, base_url='https://e-menum.net')
        data = schema.to_dict()

        self.assertEqual(data['@type'], 'Article')
        self.assertEqual(data['headline'], 'How to Create QR Menus')
        self.assertEqual(data['description'], 'A guide to digital menus.')
        self.assertEqual(data['url'], 'https://e-menum.net/blog/how-to-create-qr-menus/')

    def test_to_dict_author(self):
        post = self._make_post()
        schema = ArticleSchema(post)
        data = schema.to_dict()

        self.assertIn('author', data)
        self.assertEqual(data['author']['@type'], 'Person')
        self.assertEqual(data['author']['name'], 'Jane Doe')

    def test_to_dict_publisher(self):
        post = self._make_post()
        schema = ArticleSchema(post)
        data = schema.to_dict()

        self.assertEqual(data['publisher']['@type'], 'Organization')
        self.assertEqual(data['publisher']['name'], 'E-Menum')

    def test_to_dict_word_count(self):
        post = self._make_post(content='word ' * 100)
        schema = ArticleSchema(post)
        data = schema.to_dict()
        self.assertEqual(data['wordCount'], 100)

    def test_to_dict_without_author(self):
        post = self._make_post(author_name='')
        schema = ArticleSchema(post)
        data = schema.to_dict()
        self.assertNotIn('author', data)

    def test_to_dict_with_dates(self):
        from datetime import datetime, timezone as tz
        pub_date = datetime(2026, 1, 15, 10, 0, 0, tzinfo=tz.utc)
        post = self._make_post(published_at=pub_date, updated_at=pub_date)
        schema = ArticleSchema(post)
        data = schema.to_dict()
        self.assertIn('datePublished', data)
        self.assertIn('dateModified', data)


class TestFAQPageSchema(TestCase):
    """Test FAQPageSchema."""

    def test_to_dict_with_faqs(self):
        faqs = [
            SimpleNamespace(question='What is QR Menu?', answer='A digital menu accessible via QR code.'),
            SimpleNamespace(question='How much does it cost?', answer='Starting from free.'),
        ]
        schema = FAQPageSchema(faqs)
        data = schema.to_dict()

        self.assertEqual(data['@type'], 'FAQPage')
        self.assertEqual(len(data['mainEntity']), 2)
        self.assertEqual(data['mainEntity'][0]['@type'], 'Question')
        self.assertEqual(data['mainEntity'][0]['name'], 'What is QR Menu?')
        self.assertEqual(data['mainEntity'][0]['acceptedAnswer']['@type'], 'Answer')
        self.assertEqual(
            data['mainEntity'][0]['acceptedAnswer']['text'],
            'A digital menu accessible via QR code.',
        )

    def test_to_dict_empty_faqs(self):
        schema = FAQPageSchema([])
        data = schema.to_dict()
        self.assertEqual(data['mainEntity'], [])

    def test_skips_faqs_with_empty_fields(self):
        faqs = [
            SimpleNamespace(question='Valid?', answer='Yes.'),
            SimpleNamespace(question='', answer='No question.'),
            SimpleNamespace(question='No answer?', answer=''),
        ]
        schema = FAQPageSchema(faqs)
        data = schema.to_dict()
        self.assertEqual(len(data['mainEntity']), 1)


class TestBreadcrumbListSchema(TestCase):
    """Test BreadcrumbListSchema."""

    def test_to_dict_with_crumbs(self):
        crumbs = [
            ('Home', '/'),
            ('Blog', '/blog/'),
            ('My Post', '/blog/my-post/'),
        ]
        schema = BreadcrumbListSchema(crumbs)
        data = schema.to_dict()

        self.assertEqual(data['@type'], 'BreadcrumbList')
        self.assertEqual(len(data['itemListElement']), 3)

        first = data['itemListElement'][0]
        self.assertEqual(first['@type'], 'ListItem')
        self.assertEqual(first['position'], 1)
        self.assertEqual(first['name'], 'Home')
        self.assertEqual(first['item'], '/')

        last = data['itemListElement'][2]
        self.assertEqual(last['position'], 3)
        self.assertEqual(last['name'], 'My Post')

    def test_to_dict_empty_crumbs(self):
        schema = BreadcrumbListSchema([])
        data = schema.to_dict()
        self.assertEqual(data['itemListElement'], [])


class TestToJsonLd(TestCase):
    """Test to_json_ld() method produces valid script tag."""

    def test_json_ld_output_format(self):
        crumbs = [('Home', '/')]
        schema = BreadcrumbListSchema(crumbs)
        result = schema.to_json_ld()

        self.assertIn('<script type="application/ld+json">', result)
        self.assertIn('</script>', result)
        self.assertIn('"@context": "https://schema.org"', result)
        self.assertIn('"@type": "BreadcrumbList"', result)

    def test_json_ld_contains_valid_json(self):
        crumbs = [('Home', '/'), ('About', '/about/')]
        schema = BreadcrumbListSchema(crumbs)
        result = schema.to_json_ld()

        # Extract JSON between script tags
        json_str = result.split('<script type="application/ld+json">\n')[1]
        json_str = json_str.split('\n</script>')[0]
        parsed = json.loads(json_str)

        self.assertEqual(parsed['@type'], 'BreadcrumbList')
        self.assertEqual(len(parsed['itemListElement']), 2)

    def test_json_ld_is_marked_safe(self):
        schema = BreadcrumbListSchema([('Home', '/')])
        result = schema.to_json_ld()
        # Django SafeString is a subclass of str with __html__
        self.assertTrue(hasattr(result, '__html__'))


class TestProductSchema(TestCase):
    """Test ProductSchema."""

    def test_to_dict_with_price(self):
        schema = ProductSchema(
            name='Starter Plan',
            description='For growing businesses',
            price=2000.0,
            currency='TRY',
            sku='starter-monthly',
        )
        data = schema.to_dict()

        self.assertEqual(data['@type'], 'Product')
        self.assertEqual(data['name'], 'Starter Plan')
        self.assertIn('offers', data)
        self.assertEqual(data['offers']['@type'], 'Offer')
        self.assertEqual(data['offers']['price'], '2000.0')
        self.assertEqual(data['offers']['priceCurrency'], 'TRY')

    def test_to_dict_without_price(self):
        schema = ProductSchema(name='Free Plan')
        data = schema.to_dict()
        self.assertNotIn('offers', data)
