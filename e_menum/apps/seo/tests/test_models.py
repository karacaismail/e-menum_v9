"""
Tests for apps.seo.models module.

Covers:
- SEOMixin methods via the concrete PSEOPage model
- AuthorProfile creation and OneToOne relationship
- Redirect model (source_path uniqueness, hit_count, redirect_type choices)
- BrokenLink model (is_resolved toggling, check_count)
- TXTFileConfig (file_type uniqueness)
- PSEOTemplate and PSEOPage relationships
"""

from decimal import Decimal

from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.test import TestCase
from django.utils import timezone

from apps.seo.models import (
    AuthorProfile,
    BrokenLink,
    PSEOPage,
    PSEOTemplate,
    Redirect,
    RedirectType,
    TXTFileConfig,
    TXTFileType,
)

User = get_user_model()


class PSEOTemplateFactory:
    """Helper to create PSEOTemplate instances for tests."""

    @staticmethod
    def create(**kwargs):
        defaults = {
            'name': 'City Sector Template',
            'slug_template': '{sehir}-{sektor}-qr-menu',
            'title_template': '{sehir} {sektor} QR Menu',
            'description_template': '{sehir} sehrinde {sektor} icin QR menu.',
            'content_template': '<h1>{sehir} {sektor}</h1><p>Content here.</p>',
            'is_active': True,
            'quality_threshold': 60,
        }
        defaults.update(kwargs)
        return PSEOTemplate.objects.create(**defaults)


# ──────────────────────────────────────────────────────────────────────────────
# SEOMixin tests (via PSEOPage)
# ──────────────────────────────────────────────────────────────────────────────

class TestSEOMixin(TestCase):
    """Test SEOMixin methods using PSEOPage as the concrete model."""

    def setUp(self):
        self.template = PSEOTemplateFactory.create()
        self.page = PSEOPage.objects.create(
            template=self.template,
            slug='test-seo-page',
            rendered_title='Test SEO Page',
            rendered_content='Some content here',
        )

    def test_get_meta_title_returns_meta_title_when_set(self):
        self.page.meta_title = 'Custom Meta Title'
        self.assertEqual(self.page.get_meta_title(), 'Custom Meta Title')

    def test_get_meta_title_falls_back_to_str(self):
        self.page.meta_title = ''
        result = self.page.get_meta_title()
        # PSEOPage.__str__ returns rendered_title or slug
        self.assertEqual(result, 'Test SEO Page')

    def test_get_meta_description_returns_description(self):
        self.page.meta_description = 'A nice description'
        self.assertEqual(self.page.get_meta_description(), 'A nice description')

    def test_get_meta_description_returns_empty_when_blank(self):
        self.page.meta_description = ''
        self.assertEqual(self.page.get_meta_description(), '')

    def test_get_og_image_url_returns_empty_when_no_image(self):
        self.assertEqual(self.page.get_og_image_url(), '')

    def test_get_robots_meta_index_follow(self):
        self.page.robots_index = True
        self.page.robots_follow = True
        self.page.robots_extra = []
        self.assertEqual(self.page.get_robots_meta(), 'index, follow')

    def test_get_robots_meta_noindex_nofollow(self):
        self.page.robots_index = False
        self.page.robots_follow = False
        self.page.robots_extra = []
        self.assertEqual(self.page.get_robots_meta(), 'noindex, nofollow')

    def test_get_robots_meta_with_extra_directives(self):
        self.page.robots_index = True
        self.page.robots_follow = True
        self.page.robots_extra = ['noarchive', 'nosnippet']
        result = self.page.get_robots_meta()
        self.assertEqual(result, 'index, follow, noarchive, nosnippet')

    def test_calculate_seo_score_zero_when_empty(self):
        self.page.meta_title = ''
        self.page.meta_description = ''
        self.page.focus_keyword = ''
        self.page.og_title = ''
        self.page.og_description = ''
        self.page.structured_data = {}
        self.page.canonical_url = ''
        self.page.og_image = None
        score = self.page.calculate_seo_score()
        self.assertEqual(score, 0)

    def test_calculate_seo_score_with_meta_title(self):
        self.page.meta_title = 'A Valid Title'
        self.page.meta_description = ''
        self.page.focus_keyword = ''
        self.page.og_title = ''
        self.page.og_description = ''
        self.page.structured_data = {}
        self.page.canonical_url = ''
        self.page.og_image = None
        score = self.page.calculate_seo_score()
        self.assertEqual(score, 20)  # meta_title present but not optimal length

    def test_calculate_seo_score_optimal_title_length_bonus(self):
        # Title between 30 and 60 chars gets +5 bonus
        self.page.meta_title = 'A' * 40  # 40 chars, in optimal range
        self.page.meta_description = ''
        self.page.focus_keyword = ''
        self.page.og_title = ''
        self.page.og_description = ''
        self.page.structured_data = {}
        self.page.canonical_url = ''
        self.page.og_image = None
        score = self.page.calculate_seo_score()
        self.assertEqual(score, 25)  # 20 + 5

    def test_calculate_seo_score_with_description(self):
        self.page.meta_title = ''
        self.page.meta_description = 'A valid description for the page'
        self.page.focus_keyword = ''
        self.page.og_title = ''
        self.page.og_description = ''
        self.page.structured_data = {}
        self.page.canonical_url = ''
        self.page.og_image = None
        score = self.page.calculate_seo_score()
        self.assertEqual(score, 20)

    def test_calculate_seo_score_focus_keyword_in_title(self):
        self.page.meta_title = 'Best QR Menu Solutions'
        self.page.meta_description = ''
        self.page.focus_keyword = 'QR Menu'
        self.page.og_title = ''
        self.page.og_description = ''
        self.page.structured_data = {}
        self.page.canonical_url = ''
        self.page.og_image = None
        score = self.page.calculate_seo_score()
        # 20 (title) + 10 (keyword present) + 5 (keyword in title) = 35
        self.assertEqual(score, 35)

    def test_calculate_seo_score_capped_at_100(self):
        self.page.meta_title = 'A' * 40  # optimal (25)
        self.page.meta_description = 'B' * 130  # optimal (25)
        self.page.focus_keyword = 'A' * 40  # keyword present (10) + in title (5)
        self.page.og_title = 'OG Title'  # 5
        self.page.og_description = 'OG Desc'  # 5
        self.page.structured_data = {'@type': 'Thing'}  # 10
        self.page.canonical_url = 'https://example.com'  # 5
        # total: 25+25+15+5+5+10+5 = 90, still under 100
        score = self.page.calculate_seo_score()
        self.assertLessEqual(score, 100)

    def test_calculate_seo_score_updates_seo_score_field(self):
        self.page.meta_title = 'Test Title'
        self.page.calculate_seo_score()
        self.assertGreater(self.page.seo_score, 0)

    def test_default_seo_field_values(self):
        self.assertTrue(self.page.robots_index)
        self.assertTrue(self.page.robots_follow)
        self.assertTrue(self.page.sitemap_include)
        self.assertEqual(self.page.sitemap_priority, Decimal('0.5'))
        self.assertEqual(self.page.sitemap_changefreq, 'weekly')
        self.assertEqual(self.page.og_type, 'website')
        self.assertEqual(self.page.twitter_card, 'summary_large_image')
        self.assertEqual(self.page.seo_score, 0)


# ──────────────────────────────────────────────────────────────────────────────
# AuthorProfile tests
# ──────────────────────────────────────────────────────────────────────────────

class TestAuthorProfile(TestCase):
    """Test AuthorProfile model."""

    def setUp(self):
        self.user = User.objects.create_user(
            email='author@example.com',
            password='TestPass123!',
            first_name='Jane',
            last_name='Author',
        )

    def test_create_author_profile(self):
        profile = AuthorProfile.objects.create(
            user=self.user,
            bio='Expert in SEO and digital marketing.',
            website='https://janeauthor.com',
        )
        self.assertIsNotNone(profile.id)
        self.assertEqual(profile.user, self.user)
        self.assertIn('SEO', profile.bio)

    def test_str_returns_full_name_or_email(self):
        profile = AuthorProfile.objects.create(user=self.user)
        self.assertEqual(str(profile), 'Jane Author')

    def test_str_falls_back_to_email(self):
        self.user.first_name = ''
        self.user.last_name = ''
        self.user.save()
        profile = AuthorProfile.objects.create(user=self.user)
        self.assertEqual(str(profile), 'author@example.com')

    def test_one_to_one_relationship(self):
        AuthorProfile.objects.create(user=self.user)
        with self.assertRaises(IntegrityError):
            AuthorProfile.objects.create(user=self.user)

    def test_soft_delete(self):
        profile = AuthorProfile.objects.create(user=self.user)
        profile.soft_delete()
        self.assertTrue(profile.is_deleted)
        self.assertEqual(AuthorProfile.objects.count(), 0)
        self.assertEqual(AuthorProfile.all_objects.count(), 1)

    def test_default_field_values(self):
        profile = AuthorProfile.objects.create(user=self.user)
        self.assertEqual(profile.social_links, {})
        self.assertEqual(profile.expertise, [])
        self.assertFalse(profile.is_verified)


# ──────────────────────────────────────────────────────────────────────────────
# Redirect tests
# ──────────────────────────────────────────────────────────────────────────────

class TestRedirect(TestCase):
    """Test Redirect model."""

    def test_create_redirect(self):
        redirect = Redirect.objects.create(
            source_path='/old-page/',
            target_path='/new-page/',
            redirect_type=RedirectType.PERMANENT,
        )
        self.assertIsNotNone(redirect.id)
        self.assertEqual(redirect.hit_count, 0)
        self.assertTrue(redirect.is_active)

    def test_source_path_uniqueness(self):
        Redirect.objects.create(
            source_path='/unique-path/',
            target_path='/target/',
        )
        with self.assertRaises(IntegrityError):
            Redirect.objects.create(
                source_path='/unique-path/',
                target_path='/other-target/',
            )

    def test_redirect_type_choices(self):
        for code, label in RedirectType.choices:
            redirect = Redirect.objects.create(
                source_path=f'/path-{code}/',
                target_path='/target/',
                redirect_type=code,
            )
            self.assertEqual(redirect.redirect_type, code)

    def test_hit_count_increment(self):
        redirect = Redirect.objects.create(
            source_path='/counted/',
            target_path='/target/',
        )
        self.assertEqual(redirect.hit_count, 0)
        Redirect.objects.filter(pk=redirect.pk).update(hit_count=5)
        redirect.refresh_from_db()
        self.assertEqual(redirect.hit_count, 5)

    def test_str_representation(self):
        redirect = Redirect.objects.create(
            source_path='/from/',
            target_path='/to/',
            redirect_type=301,
        )
        self.assertEqual(str(redirect), '/from/ -> /to/ (301)')

    def test_soft_delete(self):
        redirect = Redirect.objects.create(
            source_path='/soft-del/',
            target_path='/target/',
        )
        redirect.soft_delete()
        self.assertTrue(redirect.is_deleted)
        self.assertEqual(Redirect.objects.count(), 0)
        self.assertEqual(Redirect.all_objects.count(), 1)


# ──────────────────────────────────────────────────────────────────────────────
# BrokenLink tests
# ──────────────────────────────────────────────────────────────────────────────

class TestBrokenLink(TestCase):
    """Test BrokenLink model."""

    def test_create_broken_link(self):
        link = BrokenLink.objects.create(
            source_url='https://example.com/page',
            target_url='https://example.com/missing',
            status_code=404,
        )
        self.assertIsNotNone(link.id)
        self.assertEqual(link.check_count, 1)
        self.assertFalse(link.is_resolved)

    def test_is_resolved_toggling(self):
        link = BrokenLink.objects.create(
            source_url='https://example.com/a',
            target_url='https://example.com/b',
            status_code=404,
        )
        self.assertFalse(link.is_resolved)

        link.is_resolved = True
        link.resolved_at = timezone.now()
        link.save()
        link.refresh_from_db()
        self.assertTrue(link.is_resolved)
        self.assertIsNotNone(link.resolved_at)

    def test_check_count_increments(self):
        link = BrokenLink.objects.create(
            source_url='https://example.com/c',
            target_url='https://example.com/d',
            status_code=500,
            check_count=1,
        )
        link.check_count += 1
        link.save()
        link.refresh_from_db()
        self.assertEqual(link.check_count, 2)

    def test_str_representation(self):
        link = BrokenLink.objects.create(
            source_url='https://example.com/e',
            target_url='https://example.com/broken',
            status_code=404,
        )
        self.assertEqual(str(link), 'https://example.com/broken (404)')


# ──────────────────────────────────────────────────────────────────────────────
# TXTFileConfig tests
# ──────────────────────────────────────────────────────────────────────────────

class TestTXTFileConfig(TestCase):
    """Test TXTFileConfig model."""

    def test_create_txt_config(self):
        config = TXTFileConfig.objects.create(
            file_type=TXTFileType.ROBOTS,
            content='User-agent: *\nDisallow: /admin/',
            is_active=True,
        )
        self.assertIsNotNone(config.id)
        self.assertTrue(config.auto_generate)

    def test_file_type_uniqueness(self):
        TXTFileConfig.objects.create(file_type=TXTFileType.ROBOTS)
        with self.assertRaises(IntegrityError):
            TXTFileConfig.objects.create(file_type=TXTFileType.ROBOTS)

    def test_str_representation(self):
        config = TXTFileConfig.objects.create(file_type=TXTFileType.HUMANS)
        self.assertEqual(str(config), 'humans.txt')

    def test_all_file_types_can_be_created(self):
        for file_type, label in TXTFileType.choices:
            config = TXTFileConfig.objects.create(file_type=file_type)
            self.assertIsNotNone(config.id)


# ──────────────────────────────────────────────────────────────────────────────
# PSEOTemplate and PSEOPage tests
# ──────────────────────────────────────────────────────────────────────────────

class TestPSEOTemplateAndPage(TestCase):
    """Test PSEOTemplate and PSEOPage relationship."""

    def setUp(self):
        self.template = PSEOTemplateFactory.create()

    def test_create_template(self):
        self.assertIsNotNone(self.template.id)
        self.assertEqual(str(self.template), 'City Sector Template')

    def test_create_page_from_template(self):
        page = PSEOPage.objects.create(
            template=self.template,
            slug='istanbul-restoran-qr-menu',
            variables={'sehir': 'Istanbul', 'sektor': 'Restoran'},
            rendered_title='Istanbul Restoran QR Menu',
            rendered_description='Istanbul sehrinde Restoran icin QR menu.',
            rendered_content='<h1>Istanbul Restoran</h1><p>Content.</p>',
        )
        self.assertEqual(page.template, self.template)
        self.assertFalse(page.is_published)
        self.assertEqual(page.view_count, 0)

    def test_template_pages_reverse_relation(self):
        PSEOPage.objects.create(
            template=self.template,
            slug='page-1',
            rendered_title='Page 1',
        )
        PSEOPage.objects.create(
            template=self.template,
            slug='page-2',
            rendered_title='Page 2',
        )
        self.assertEqual(self.template.pages.count(), 2)

    def test_page_slug_uniqueness(self):
        PSEOPage.objects.create(
            template=self.template,
            slug='unique-slug',
        )
        with self.assertRaises(IntegrityError):
            PSEOPage.objects.create(
                template=self.template,
                slug='unique-slug',
            )

    def test_page_str_returns_rendered_title(self):
        page = PSEOPage.objects.create(
            template=self.template,
            slug='str-test',
            rendered_title='My Title',
        )
        self.assertEqual(str(page), 'My Title')

    def test_page_str_falls_back_to_slug(self):
        page = PSEOPage.objects.create(
            template=self.template,
            slug='fallback-slug',
            rendered_title='',
        )
        self.assertEqual(str(page), 'fallback-slug')

    def test_page_soft_delete(self):
        page = PSEOPage.objects.create(
            template=self.template,
            slug='soft-del-page',
        )
        page.soft_delete()
        self.assertTrue(page.is_deleted)
        self.assertEqual(PSEOPage.objects.count(), 0)
        self.assertEqual(PSEOPage.all_objects.count(), 1)

    def test_template_soft_delete(self):
        self.template.soft_delete()
        self.assertTrue(self.template.is_deleted)
        self.assertEqual(PSEOTemplate.objects.count(), 0)
        self.assertEqual(PSEOTemplate.all_objects.count(), 1)
