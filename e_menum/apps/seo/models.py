"""
Django ORM models for the SEO application.

This module defines models for search engine optimization:
- SEOMixin: Reusable abstract mixin for SEO metadata on any model
- AuthorProfile: Author profiles for structured data and E-E-A-T
- Redirect: URL redirect management (301/302/307/308)
- BrokenLink: Broken link detection and tracking
- TXTFileConfig: Dynamic robots.txt, humans.txt, etc.
- PSEOTemplate: Programmatic SEO page templates
- PSEOPage: Generated programmatic SEO pages
"""

import uuid
from decimal import Decimal

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.models import SoftDeleteManager, SoftDeleteMixin, TimeStampedMixin


# ──────────────────────────────────────────────────────────────
# Choices
# ──────────────────────────────────────────────────────────────

class TwitterCardType(models.TextChoices):
    SUMMARY = 'summary', _('Summary')
    SUMMARY_LARGE_IMAGE = 'summary_large_image', _('Summary Large Image')
    PLAYER = 'player', _('Player')
    APP = 'app', _('App')


class SitemapChangeFreq(models.TextChoices):
    ALWAYS = 'always', _('Always')
    HOURLY = 'hourly', _('Hourly')
    DAILY = 'daily', _('Daily')
    WEEKLY = 'weekly', _('Weekly')
    MONTHLY = 'monthly', _('Monthly')
    YEARLY = 'yearly', _('Yearly')
    NEVER = 'never', _('Never')


class RedirectType(models.IntegerChoices):
    PERMANENT = 301, _('Permanent (301)')
    TEMPORARY = 302, _('Temporary (302)')
    TEMPORARY_STRICT = 307, _('Temporary Strict (307)')
    PERMANENT_STRICT = 308, _('Permanent Strict (308)')


class TXTFileType(models.TextChoices):
    ROBOTS = 'robots', _('robots.txt')
    HUMANS = 'humans', _('humans.txt')
    SECURITY = 'security', _('security.txt')
    ADS = 'ads', _('ads.txt')
    LLMS = 'llms', _('llms.txt')


class SchemaOrgType(models.TextChoices):
    LOCAL_BUSINESS = 'LocalBusiness', _('Local Business')
    RESTAURANT = 'Restaurant', _('Restaurant')
    CAFE_OR_COFFEE_SHOP = 'CafeOrCoffeeShop', _('Cafe or Coffee Shop')
    BAR_OR_PUB = 'BarOrPub', _('Bar or Pub')
    FOOD_ESTABLISHMENT = 'FoodEstablishment', _('Food Establishment')


class CrawlReportStatus(models.TextChoices):
    RUNNING = 'running', _('Running')
    COMPLETED = 'completed', _('Completed')
    FAILED = 'failed', _('Failed')


# ──────────────────────────────────────────────────────────────
# SEOMixin (Abstract)
# ──────────────────────────────────────────────────────────────

class SEOMixin(models.Model):
    """
    Abstract mixin providing comprehensive SEO fields for any model.

    Includes Open Graph, Twitter Card, robots directives, sitemap
    configuration, structured data, and SEO scoring.
    """

    # -- Meta tags --
    meta_title = models.CharField(
        max_length=70,
        blank=True,
        verbose_name=_('Meta title'),
        help_text=_('Page title for search engines (max 70 chars)')
    )
    meta_description = models.CharField(
        max_length=160,
        blank=True,
        verbose_name=_('Meta description'),
        help_text=_('Page description for search engines (max 160 chars)')
    )
    meta_keywords = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_('Meta keywords'),
        help_text=_('Comma-separated keywords')
    )

    # -- Open Graph --
    og_title = models.CharField(
        max_length=70,
        blank=True,
        verbose_name=_('OG title'),
        help_text=_('Open Graph title for social sharing')
    )
    og_description = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_('OG description'),
        help_text=_('Open Graph description for social sharing')
    )
    og_image = models.ImageField(
        upload_to='seo/og/',
        blank=True,
        null=True,
        verbose_name=_('OG image'),
        help_text=_('Open Graph image (recommended 1200x630)')
    )
    og_type = models.CharField(
        max_length=50,
        default='website',
        verbose_name=_('OG type'),
        help_text=_('Open Graph type (e.g. website, article)')
    )

    # -- Twitter Card --
    twitter_card = models.CharField(
        max_length=20,
        choices=TwitterCardType.choices,
        default=TwitterCardType.SUMMARY_LARGE_IMAGE,
        verbose_name=_('Twitter card'),
        help_text=_('Twitter Card display type')
    )
    twitter_title = models.CharField(
        max_length=70,
        blank=True,
        verbose_name=_('Twitter title'),
        help_text=_('Title for Twitter Card')
    )
    twitter_description = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_('Twitter description'),
        help_text=_('Description for Twitter Card')
    )
    twitter_image = models.ImageField(
        upload_to='seo/twitter/',
        blank=True,
        null=True,
        verbose_name=_('Twitter image'),
        help_text=_('Image for Twitter Card')
    )

    # -- Canonical & Robots --
    canonical_url = models.URLField(
        max_length=500,
        blank=True,
        verbose_name=_('Canonical URL'),
        help_text=_('Canonical URL to prevent duplicate content')
    )
    robots_index = models.BooleanField(
        default=True,
        verbose_name=_('Robots index'),
        help_text=_('Allow search engines to index this page')
    )
    robots_follow = models.BooleanField(
        default=True,
        verbose_name=_('Robots follow'),
        help_text=_('Allow search engines to follow links on this page')
    )
    robots_extra = models.JSONField(
        default=list,
        blank=True,
        verbose_name=_('Robots extra directives'),
        help_text=_('Additional robots directives (e.g. noarchive, nosnippet)')
    )

    # -- Sitemap --
    sitemap_include = models.BooleanField(
        default=True,
        verbose_name=_('Include in sitemap'),
        help_text=_('Whether to include this page in the XML sitemap')
    )
    sitemap_priority = models.DecimalField(
        max_digits=2,
        decimal_places=1,
        default=Decimal('0.5'),
        verbose_name=_('Sitemap priority'),
        help_text=_('Priority in sitemap (0.0 to 1.0)')
    )
    sitemap_changefreq = models.CharField(
        max_length=10,
        choices=SitemapChangeFreq.choices,
        default=SitemapChangeFreq.WEEKLY,
        verbose_name=_('Sitemap change frequency'),
        help_text=_('Expected page update frequency')
    )

    # -- SEO Analysis --
    seo_score = models.IntegerField(
        default=0,
        verbose_name=_('SEO score'),
        help_text=_('Calculated SEO quality score (0-100)')
    )
    seo_suggestions = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_('SEO suggestions'),
        help_text=_('Auto-generated improvement suggestions')
    )
    structured_data = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_('Structured data'),
        help_text=_('Custom JSON-LD structured data override')
    )
    focus_keyword = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_('Focus keyword'),
        help_text=_('Primary keyword to optimize for')
    )
    last_seo_analysis = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Last SEO analysis'),
        help_text=_('Timestamp of the last SEO score calculation')
    )

    class Meta:
        abstract = True

    def get_meta_title(self) -> str:
        """Return meta title, falling back to str representation."""
        return self.meta_title or str(self)

    def get_meta_description(self) -> str:
        """Return meta description or empty string."""
        return self.meta_description or ''

    def get_og_image_url(self) -> str:
        """Return absolute URL for OG image if available."""
        if self.og_image:
            return self.og_image.url
        return ''

    def get_robots_meta(self) -> str:
        """Build the robots meta tag content string."""
        directives = []
        directives.append('index' if self.robots_index else 'noindex')
        directives.append('follow' if self.robots_follow else 'nofollow')
        if self.robots_extra:
            directives.extend(self.robots_extra)
        return ', '.join(directives)

    def calculate_seo_score(self) -> int:
        """
        Calculate a basic SEO quality score (0-100).

        Checks for presence of key SEO fields and returns a weighted score.
        """
        score = 0

        # Meta title (20 points)
        if self.meta_title:
            score += 20
            if 30 <= len(self.meta_title) <= 60:
                score += 5  # Optimal length bonus

        # Meta description (20 points)
        if self.meta_description:
            score += 20
            if 120 <= len(self.meta_description) <= 155:
                score += 5  # Optimal length bonus

        # Focus keyword (10 points)
        if self.focus_keyword:
            score += 10
            # Check keyword in title
            if self.meta_title and self.focus_keyword.lower() in self.meta_title.lower():
                score += 5

        # Open Graph (10 points)
        if self.og_title:
            score += 5
        if self.og_description:
            score += 5

        # Structured data (10 points)
        if self.structured_data:
            score += 10

        # Canonical URL (5 points)
        if self.canonical_url:
            score += 5

        # OG image (5 points)
        if self.og_image:
            score += 5

        self.seo_score = min(score, 100)
        return self.seo_score


# ──────────────────────────────────────────────────────────────
# AuthorProfile
# ──────────────────────────────────────────────────────────────

class AuthorProfile(SoftDeleteMixin, TimeStampedMixin, models.Model):
    """Author profile for blog posts, structured data, and E-E-A-T signals."""

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name=_('ID'),
    )
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='author_profile',
        verbose_name=_('User'),
        help_text=_('User account linked to this author profile')
    )
    bio = models.TextField(
        blank=True,
        verbose_name=_('Biography'),
        help_text=_('Author biography for display and structured data')
    )
    avatar = models.ImageField(
        upload_to='seo/authors/',
        blank=True,
        null=True,
        verbose_name=_('Avatar'),
        help_text=_('Author profile photo')
    )
    website = models.URLField(
        max_length=500,
        blank=True,
        verbose_name=_('Website'),
        help_text=_('Author personal website URL')
    )
    social_links = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_('Social links'),
        help_text=_('Social media links: {"twitter": "", "linkedin": "", "github": ""}')
    )
    expertise = models.JSONField(
        default=list,
        blank=True,
        verbose_name=_('Expertise'),
        help_text=_('List of expertise areas, e.g. ["SEO", "Digital Marketing"]')
    )
    is_verified = models.BooleanField(
        default=False,
        verbose_name=_('Is verified'),
        help_text=_('Whether this author has been verified')
    )

    # Managers
    objects = SoftDeleteManager()
    all_objects = models.Manager()

    class Meta:
        db_table = 'seo_author_profiles'
        verbose_name = _('Author Profile')
        verbose_name_plural = _('Author Profiles')
        ordering = ['-created_at']

    def __str__(self) -> str:
        return self.user.get_full_name() or self.user.email


# ──────────────────────────────────────────────────────────────
# Redirect
# ──────────────────────────────────────────────────────────────

class Redirect(SoftDeleteMixin, TimeStampedMixin, models.Model):
    """URL redirect rule for managing moved or renamed pages."""

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name=_('ID'),
    )
    source_path = models.CharField(
        max_length=500,
        unique=True,
        db_index=True,
        verbose_name=_('Source path'),
        help_text=_('Original URL path to redirect from (e.g. /old-page)')
    )
    target_path = models.CharField(
        max_length=500,
        verbose_name=_('Target path'),
        help_text=_('Destination URL path to redirect to (e.g. /new-page)')
    )
    redirect_type = models.IntegerField(
        choices=RedirectType.choices,
        default=RedirectType.PERMANENT,
        verbose_name=_('Redirect type'),
        help_text=_('HTTP redirect status code')
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=_('Is active'),
        help_text=_('Whether this redirect is currently active')
    )
    hit_count = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Hit count'),
        help_text=_('Number of times this redirect has been triggered')
    )
    last_hit = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Last hit'),
        help_text=_('Timestamp of the last redirect hit')
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_redirects',
        verbose_name=_('Created by'),
        help_text=_('User who created this redirect rule')
    )
    note = models.TextField(
        blank=True,
        verbose_name=_('Note'),
        help_text=_('Internal note about why this redirect exists')
    )

    # Managers
    objects = SoftDeleteManager()
    all_objects = models.Manager()

    class Meta:
        db_table = 'seo_redirects'
        verbose_name = _('Redirect')
        verbose_name_plural = _('Redirects')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['source_path'], name='seo_redirect_source_idx'),
            models.Index(
                fields=['is_active', 'deleted_at'],
                name='seo_redirect_active_del_idx',
            ),
        ]

    def __str__(self) -> str:
        return f'{self.source_path} -> {self.target_path} ({self.redirect_type})'


# ──────────────────────────────────────────────────────────────
# BrokenLink
# ──────────────────────────────────────────────────────────────

class BrokenLink(TimeStampedMixin, models.Model):
    """Detected broken link for monitoring and resolution tracking."""

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name=_('ID'),
    )
    source_url = models.URLField(
        max_length=500,
        verbose_name=_('Source URL'),
        help_text=_('URL of the page containing the broken link')
    )
    target_url = models.URLField(
        max_length=500,
        verbose_name=_('Target URL'),
        help_text=_('The broken destination URL')
    )
    status_code = models.IntegerField(
        verbose_name=_('Status code'),
        help_text=_('HTTP status code returned (e.g. 404, 500)')
    )
    source_page = models.CharField(
        max_length=500,
        blank=True,
        verbose_name=_('Source page'),
        help_text=_('Page path where the broken link was found')
    )
    link_text = models.CharField(
        max_length=300,
        blank=True,
        verbose_name=_('Link text'),
        help_text=_('Anchor text of the broken link')
    )
    first_detected = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('First detected'),
        help_text=_('When this broken link was first discovered')
    )
    last_checked = models.DateTimeField(
        auto_now=True,
        verbose_name=_('Last checked'),
        help_text=_('When this broken link was last verified')
    )
    check_count = models.PositiveIntegerField(
        default=1,
        verbose_name=_('Check count'),
        help_text=_('Number of times this link has been checked')
    )
    is_resolved = models.BooleanField(
        default=False,
        verbose_name=_('Is resolved'),
        help_text=_('Whether this broken link has been fixed')
    )
    resolved_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Resolved at'),
        help_text=_('When this broken link was resolved')
    )

    class Meta:
        db_table = 'seo_broken_links'
        verbose_name = _('Broken Link')
        verbose_name_plural = _('Broken Links')
        ordering = ['-first_detected']
        indexes = [
            models.Index(fields=['is_resolved'], name='seo_brokenlink_resolved_idx'),
            models.Index(fields=['source_url'], name='seo_brokenlink_source_idx'),
        ]

    def __str__(self) -> str:
        return f'{self.target_url} ({self.status_code})'


# ──────────────────────────────────────────────────────────────
# TXTFileConfig
# ──────────────────────────────────────────────────────────────

class TXTFileConfig(TimeStampedMixin, models.Model):
    """Configuration for dynamically served TXT files (robots, humans, etc.)."""

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name=_('ID'),
    )
    file_type = models.CharField(
        max_length=20,
        choices=TXTFileType.choices,
        unique=True,
        verbose_name=_('File type'),
        help_text=_('Type of TXT file to serve')
    )
    content = models.TextField(
        blank=True,
        verbose_name=_('Content'),
        help_text=_('File content (raw text)')
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=_('Is active'),
        help_text=_('Whether this file is actively served')
    )
    auto_generate = models.BooleanField(
        default=True,
        verbose_name=_('Auto generate'),
        help_text=_('Whether to auto-generate content from site data')
    )
    last_generated = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Last generated'),
        help_text=_('When the content was last auto-generated')
    )

    class Meta:
        db_table = 'seo_txt_file_configs'
        verbose_name = _('TXT File Config')
        verbose_name_plural = _('TXT File Configs')
        ordering = ['file_type']

    def __str__(self) -> str:
        return f'{self.get_file_type_display()}'


# ──────────────────────────────────────────────────────────────
# PSEOTemplate
# ──────────────────────────────────────────────────────────────

class PSEOTemplate(SoftDeleteMixin, TimeStampedMixin, models.Model):
    """Template for programmatic SEO page generation."""

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name=_('ID'),
    )
    name = models.CharField(
        max_length=200,
        verbose_name=_('Name'),
        help_text=_('Template name for internal reference')
    )
    slug_template = models.CharField(
        max_length=300,
        verbose_name=_('Slug template'),
        help_text=_('URL slug pattern, e.g. {sehir}-{sektor}-qr-menu')
    )
    title_template = models.CharField(
        max_length=300,
        verbose_name=_('Title template'),
        help_text=_('Page title pattern with variable placeholders')
    )
    description_template = models.TextField(
        verbose_name=_('Description template'),
        help_text=_('Meta description pattern with variable placeholders')
    )
    content_template = models.TextField(
        verbose_name=_('Content template'),
        help_text=_('Page content template with variable placeholders')
    )
    schema_type = models.CharField(
        max_length=50,
        choices=SchemaOrgType.choices,
        default=SchemaOrgType.RESTAURANT,
        verbose_name=_('Schema.org type'),
        help_text=_('Structured data type for generated pages')
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=_('Is active'),
        help_text=_('Whether this template is available for page generation')
    )
    quality_threshold = models.IntegerField(
        default=60,
        verbose_name=_('Quality threshold'),
        help_text=_('Minimum SEO score required to publish generated pages')
    )

    # Managers
    objects = SoftDeleteManager()
    all_objects = models.Manager()

    class Meta:
        db_table = 'seo_pseo_templates'
        verbose_name = _('pSEO Template')
        verbose_name_plural = _('pSEO Templates')
        ordering = ['-created_at']

    def __str__(self) -> str:
        return self.name


# ──────────────────────────────────────────────────────────────
# PSEOPage
# ──────────────────────────────────────────────────────────────

class PSEOPage(SEOMixin, SoftDeleteMixin, TimeStampedMixin, models.Model):
    """Generated programmatic SEO page from a template."""

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name=_('ID'),
    )
    template = models.ForeignKey(
        PSEOTemplate,
        on_delete=models.CASCADE,
        related_name='pages',
        verbose_name=_('Template'),
        help_text=_('Source template used to generate this page')
    )
    slug = models.SlugField(
        max_length=300,
        unique=True,
        verbose_name=_('Slug'),
        help_text=_('URL slug for this page')
    )
    variables = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_('Variables'),
        help_text=_('Template variable values used for rendering')
    )
    rendered_title = models.CharField(
        max_length=300,
        blank=True,
        verbose_name=_('Rendered title'),
        help_text=_('Rendered page title from template')
    )
    rendered_description = models.TextField(
        blank=True,
        verbose_name=_('Rendered description'),
        help_text=_('Rendered meta description from template')
    )
    rendered_content = models.TextField(
        blank=True,
        verbose_name=_('Rendered content'),
        help_text=_('Rendered page body from template')
    )
    quality_score = models.IntegerField(
        default=0,
        verbose_name=_('Quality score'),
        help_text=_('Content quality score (0-100)')
    )
    is_published = models.BooleanField(
        default=False,
        verbose_name=_('Is published'),
        help_text=_('Whether this page is publicly visible')
    )
    published_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Published at'),
        help_text=_('When this page was first published')
    )
    view_count = models.PositiveIntegerField(
        default=0,
        verbose_name=_('View count'),
        help_text=_('Number of page views')
    )

    # Managers
    objects = SoftDeleteManager()
    all_objects = models.Manager()

    class Meta:
        db_table = 'seo_pseo_pages'
        verbose_name = _('pSEO Page')
        verbose_name_plural = _('pSEO Pages')
        ordering = ['-created_at']
        indexes = [
            models.Index(
                fields=['is_published', 'deleted_at'],
                name='seo_pseopage_pub_del_idx',
            ),
            models.Index(fields=['slug'], name='seo_pseopage_slug_idx'),
        ]

    def __str__(self) -> str:
        return self.rendered_title or self.slug


# ──────────────────────────────────────────────────────────────
# NotFound404Log
# ──────────────────────────────────────────────────────────────

class NotFound404Log(TimeStampedMixin, models.Model):
    """
    Aggregated 404 error log — one record per unique path per day.

    Prevents table bloat by using (path, date) as a unique constraint
    and incrementing hit_count on each new 404 for the same path+day.
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name=_('ID'),
    )
    path = models.CharField(
        max_length=500,
        db_index=True,
        verbose_name=_('Path'),
        help_text=_('URL path that returned 404'),
    )
    date = models.DateField(
        db_index=True,
        verbose_name=_('Date'),
        help_text=_('Day the 404 was recorded'),
    )
    hit_count = models.PositiveIntegerField(
        default=1,
        verbose_name=_('Hit count'),
        help_text=_('Number of 404 hits for this path on this day'),
    )
    last_user_agent = models.TextField(
        blank=True,
        verbose_name=_('Last user agent'),
        help_text=_('Most recent user agent that triggered this 404'),
    )
    last_referer = models.URLField(
        max_length=500,
        blank=True,
        verbose_name=_('Last referer'),
        help_text=_('Most recent HTTP referer header'),
    )
    last_ip = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name=_('Last IP'),
        help_text=_('Most recent IP address that triggered this 404'),
    )

    class Meta:
        db_table = 'seo_404_logs'
        verbose_name = _('404 Log')
        verbose_name_plural = _('404 Logs')
        ordering = ['-date', '-hit_count']
        unique_together = [('path', 'date')]
        indexes = [
            models.Index(fields=['-date', '-hit_count'], name='seo_404_date_hits_idx'),
        ]

    def __str__(self) -> str:
        return f'{self.path} ({self.hit_count}x on {self.date})'


# ──────────────────────────────────────────────────────────────
# CrawlReport
# ──────────────────────────────────────────────────────────────

class CrawlReport(TimeStampedMixin, models.Model):
    """Persisted result of a broken link crawl run."""

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name=_('ID'),
    )
    started_at = models.DateTimeField(
        verbose_name=_('Started at'),
        help_text=_('When the crawl started'),
    )
    finished_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Finished at'),
        help_text=_('When the crawl finished'),
    )
    total_pages = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Total pages'),
        help_text=_('Number of pages crawled'),
    )
    total_links = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Total links'),
        help_text=_('Total number of links checked'),
    )
    broken_count = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Broken count'),
        help_text=_('Number of broken links found'),
    )
    redirected_count = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Redirected count'),
        help_text=_('Number of redirected links found'),
    )
    healthy_count = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Healthy count'),
        help_text=_('Number of healthy links found'),
    )
    status = models.CharField(
        max_length=20,
        choices=CrawlReportStatus.choices,
        default=CrawlReportStatus.RUNNING,
        verbose_name=_('Status'),
        help_text=_('Current status of the crawl'),
    )
    error_message = models.TextField(
        blank=True,
        verbose_name=_('Error message'),
        help_text=_('Error details if the crawl failed'),
    )

    class Meta:
        db_table = 'seo_crawl_reports'
        verbose_name = _('Crawl Report')
        verbose_name_plural = _('Crawl Reports')
        ordering = ['-started_at']

    def __str__(self) -> str:
        return f'Crawl {self.started_at:%Y-%m-%d %H:%M} — {self.get_status_display()}'
