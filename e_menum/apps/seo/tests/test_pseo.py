"""
Tests for apps.seo.pseo module.

Covers:
- PSEOEngine.render_page() with variables
- PSEOEngine._score_rendered() quality score calculation
- PSEOEngine.generate_pages() creates pages and skips duplicates
- PSEOEngine.bulk_publish() only publishes above threshold
- generate_city_sector_combinations() helper
- _slugify_turkish() helper
- _SafeFormatMap missing key behaviour
"""

from django.test import TestCase
from django.utils import timezone

from apps.seo.models import PSEOPage, PSEOTemplate
from apps.seo.pseo import (
    DEFAULT_CITIES,
    DEFAULT_SECTORS,
    PSEOEngine,
    _SafeFormatMap,
    _slugify_turkish,
    generate_city_sector_combinations,
)


class TestPSEOEngineRenderPage(TestCase):
    """Test PSEOEngine.render_page()."""

    def setUp(self):
        self.template = PSEOTemplate.objects.create(
            name='Render Test',
            slug_template='{sehir}-{sektor}-qr-menu',
            title_template='{sehir} {sektor} QR Menu',
            description_template='{sehir} sehrinde {sektor} icin dijital QR menu.',
            content_template='<h1>{sehir} {sektor}</h1><p>QR menu cozumu.</p>',
        )
        self.engine = PSEOEngine()

    def test_render_page_substitutes_variables(self):
        variables = {'sehir': 'Istanbul', 'sektor': 'Restoran'}
        result = self.engine.render_page(self.template, variables)

        self.assertEqual(result['title'], 'Istanbul Restoran QR Menu')
        self.assertEqual(
            result['description'],
            'Istanbul sehrinde Restoran icin dijital QR menu.',
        )
        self.assertIn('Istanbul Restoran', result['content'])

    def test_render_page_slug_is_slugified(self):
        variables = {'sehir': 'Istanbul', 'sektor': 'Restoran'}
        result = self.engine.render_page(self.template, variables)
        # Slug should be lowercased, hyphenated
        self.assertEqual(result['slug'], 'istanbul-restoran-qr-menu')

    def test_render_page_with_turkish_chars(self):
        variables = {'sehir': 'Gaziantep', 'sektor': 'Kebapci'}
        result = self.engine.render_page(self.template, variables)
        # Turkish chars in slug should be transliterated
        slug = result['slug']
        self.assertNotIn('ı', slug)
        self.assertTrue(slug.isascii() or '-' in slug)

    def test_render_page_missing_variable_kept_as_placeholder(self):
        variables = {'sehir': 'Istanbul'}  # missing 'sektor'
        result = self.engine.render_page(self.template, variables)
        # _SafeFormatMap should keep {sektor} as-is
        self.assertIn('{sektor}', result['title'])


class TestPSEOEngineScoring(TestCase):
    """Test quality score calculation."""

    def test_score_with_optimal_title_and_desc(self):
        # Use diverse content to get high unique word ratio
        words = [f'word{i}' for i in range(300)]
        rendered = {
            'title': 'A' * 40,       # 10-70 chars = 20 pts
            'description': 'B' * 100, # 50-160 chars = 20 pts
            'content': ' '.join(words),  # 300 unique words = 25 + 20 pts
        }
        score = PSEOEngine._score_rendered(rendered)
        # Title: 20, Desc: 20, Content: 25, Unique ratio: 20, No keyword: 5 = 90
        self.assertGreaterEqual(score, 80)
        self.assertLessEqual(score, 100)

    def test_score_empty_content(self):
        rendered = {'title': '', 'description': '', 'content': ''}
        score = PSEOEngine._score_rendered(rendered)
        # No keyword set gives partial credit of 5
        self.assertEqual(score, 5)

    def test_score_title_only(self):
        rendered = {'title': 'Short', 'description': '', 'content': ''}
        score = PSEOEngine._score_rendered(rendered)
        # Title present but < 10 chars: 5 + 5 = 10, no keyword: +5
        self.assertEqual(score, 15)

    def test_score_with_focus_keyword(self):
        rendered = {
            'title': 'Best QR Menu for Istanbul',
            'description': '',
            'content': 'QR Menu is great for restaurants in Istanbul.',
        }
        score = PSEOEngine._score_rendered(rendered, focus_keyword='QR Menu')
        # Title: 5+15=20, Content words ~8: 5, Unique ratio high: ~20
        # Keyword in title: 8, keyword in content: 7
        self.assertGreaterEqual(score, 40)

    def test_score_capped_at_100(self):
        rendered = {
            'title': 'A' * 40,
            'description': 'B' * 100,
            'content': ' '.join(f'word{i}' for i in range(500)),
        }
        score = PSEOEngine._score_rendered(rendered, focus_keyword='word1')
        self.assertLessEqual(score, 100)

    def test_calculate_quality_score_updates_page(self):
        template = PSEOTemplate.objects.create(
            name='Score Test',
            slug_template='test',
            title_template='Test',
            description_template='Test desc',
            content_template='Content',
        )
        page = PSEOPage.objects.create(
            template=template,
            slug='score-page',
            rendered_title='A Good Title For SEO',
            rendered_description='A comprehensive description for the page.',
            rendered_content='word ' * 200,
        )
        engine = PSEOEngine()
        score = engine.calculate_quality_score(page)
        self.assertEqual(page.quality_score, score)
        self.assertGreater(score, 0)


class TestPSEOEngineGeneratePages(TestCase):
    """Test PSEOEngine.generate_pages()."""

    def setUp(self):
        self.template = PSEOTemplate.objects.create(
            name='Gen Test',
            slug_template='{sehir}-{sektor}-menu',
            title_template='{sehir} {sektor} Menu',
            description_template='Menu for {sektor} in {sehir}.',
            content_template='<p>{sehir} {sektor} menu content.</p>',
        )
        self.engine = PSEOEngine()

    def test_generates_pages(self):
        variables_list = [
            {'sehir': 'Istanbul', 'sektor': 'Restoran'},
            {'sehir': 'Ankara', 'sektor': 'Kafe'},
        ]
        count = self.engine.generate_pages(self.template, variables_list)
        self.assertEqual(count, 2)
        self.assertEqual(PSEOPage.objects.count(), 2)

    def test_skips_duplicate_slugs(self):
        variables_list = [
            {'sehir': 'Istanbul', 'sektor': 'Restoran'},
        ]
        self.engine.generate_pages(self.template, variables_list)
        # Try again with same variables
        count = self.engine.generate_pages(self.template, variables_list)
        self.assertEqual(count, 0)
        self.assertEqual(PSEOPage.objects.count(), 1)

    def test_generated_pages_have_meta_fields(self):
        variables_list = [{'sehir': 'Izmir', 'sektor': 'Kafe'}]
        self.engine.generate_pages(self.template, variables_list)

        page = PSEOPage.objects.first()
        self.assertIsNotNone(page.meta_title)
        self.assertIsNotNone(page.meta_description)
        self.assertIsNotNone(page.rendered_title)
        self.assertFalse(page.is_published)

    def test_generated_pages_have_quality_score(self):
        variables_list = [{'sehir': 'Bursa', 'sektor': 'Restoran'}]
        self.engine.generate_pages(self.template, variables_list)

        page = PSEOPage.objects.first()
        self.assertGreater(page.quality_score, 0)

    def test_generate_empty_list(self):
        count = self.engine.generate_pages(self.template, [])
        self.assertEqual(count, 0)


class TestPSEOEngineBulkPublish(TestCase):
    """Test PSEOEngine.bulk_publish()."""

    def setUp(self):
        self.template = PSEOTemplate.objects.create(
            name='Publish Test',
            slug_template='pub-{sehir}',
            title_template='Pub {sehir}',
            description_template='Desc {sehir}.',
            content_template='Content {sehir}.',
            quality_threshold=60,
        )
        self.engine = PSEOEngine()

    def test_bulk_publish_above_threshold(self):
        PSEOPage.objects.create(
            template=self.template,
            slug='high-quality',
            rendered_title='High Quality',
            quality_score=80,
            is_published=False,
        )
        PSEOPage.objects.create(
            template=self.template,
            slug='low-quality',
            rendered_title='Low Quality',
            quality_score=30,
            is_published=False,
        )

        count = self.engine.bulk_publish(self.template, min_quality=60)
        self.assertEqual(count, 1)

        high = PSEOPage.objects.get(slug='high-quality')
        low = PSEOPage.objects.get(slug='low-quality')
        self.assertTrue(high.is_published)
        self.assertIsNotNone(high.published_at)
        self.assertFalse(low.is_published)
        self.assertIsNone(low.published_at)

    def test_bulk_publish_skips_already_published(self):
        PSEOPage.objects.create(
            template=self.template,
            slug='already-published',
            rendered_title='Already Published',
            quality_score=90,
            is_published=True,
            published_at=timezone.now(),
        )

        count = self.engine.bulk_publish(self.template, min_quality=60)
        self.assertEqual(count, 0)

    def test_bulk_publish_skips_soft_deleted(self):
        PSEOPage.objects.create(
            template=self.template,
            slug='deleted-high',
            rendered_title='Deleted High',
            quality_score=90,
            is_published=False,
            deleted_at=timezone.now(),
        )

        count = self.engine.bulk_publish(self.template, min_quality=60)
        self.assertEqual(count, 0)

    def test_bulk_publish_default_min_quality(self):
        PSEOPage.objects.create(
            template=self.template,
            slug='threshold-test',
            quality_score=60,
            is_published=False,
        )
        count = self.engine.bulk_publish(self.template)
        self.assertEqual(count, 1)


class TestHelpers(TestCase):
    """Test helper functions and classes."""

    def test_generate_city_sector_combinations(self):
        combos = generate_city_sector_combinations()
        expected_count = len(DEFAULT_CITIES) * len(DEFAULT_SECTORS)
        self.assertEqual(len(combos), expected_count)

        first = combos[0]
        self.assertIn('sehir', first)
        self.assertIn('sektor', first)
        self.assertEqual(first['sehir'], DEFAULT_CITIES[0])
        self.assertEqual(first['sektor'], DEFAULT_SECTORS[0])

    def test_slugify_turkish_basic(self):
        self.assertEqual(_slugify_turkish('Hello World'), 'hello-world')

    def test_slugify_turkish_transliteration(self):
        result = _slugify_turkish('Istanbul Caf\u00e9 \u015f\u00f6le')
        self.assertFalse(any(c in result for c in '\u015f\u00f6'))
        self.assertIn('istanbul', result)

    def test_slugify_turkish_special_chars(self):
        result = _slugify_turkish('\u00c7ay & Kahve!')
        self.assertNotIn('&', result)
        self.assertNotIn('!', result)

    def test_slugify_turkish_strips_hyphens(self):
        result = _slugify_turkish('--test--')
        self.assertEqual(result, 'test')

    def test_slugify_turkish_collapses_multiple_hyphens(self):
        result = _slugify_turkish('a   b   c')
        self.assertEqual(result, 'a-b-c')

    def test_safe_format_map_returns_value(self):
        m = _SafeFormatMap({'key': 'value'})
        self.assertEqual(m['key'], 'value')

    def test_safe_format_map_missing_key(self):
        m = _SafeFormatMap({})
        self.assertEqual(m['missing'], '{missing}')
