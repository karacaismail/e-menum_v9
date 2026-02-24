"""Content models — FAQ, TeamMember, CompanyValue, LegalPage, BlogPost."""

from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.seo.models import SEOMixin

from .base import TimeStampedModel


# =============================================================================
# FAQ
# =============================================================================

class FAQ(TimeStampedModel):
    """Frequently asked questions for pricing and contact pages."""

    class PageChoices(models.TextChoices):
        PRICING = 'pricing', _('Fiyatlandirma')
        CONTACT = 'contact', _('Iletisim')
        BOTH = 'both', _('Her Ikisi')
        SUPPORT = 'support', _('Destek')
        GENERAL = 'general', _('Genel')

    question = models.CharField(_('soru'), max_length=300)
    answer = models.TextField(_('cevap'))
    page = models.CharField(
        _('sayfa'),
        max_length=20,
        choices=PageChoices.choices,
        default=PageChoices.BOTH,
    )
    sort_order = models.PositiveIntegerField(_('siralama'), default=0)
    is_active = models.BooleanField(_('aktif'), default=True)

    class Meta:
        verbose_name = _('SSS')
        verbose_name_plural = _('SSS (Sikca Sorulan Sorular)')
        ordering = ['sort_order']

    def __str__(self):
        return self.question[:80]


# =============================================================================
# TEAM MEMBER
# =============================================================================

class TeamMember(TimeStampedModel):
    """Team member for the about page."""

    name = models.CharField(_('ad soyad'), max_length=100)
    initials = models.CharField(_('bas harfler'), max_length=5, blank=True)
    title = models.CharField(_('unvan'), max_length=200)
    avatar_color = models.CharField(_('avatar rengi'), max_length=30, default='primary')
    sort_order = models.PositiveIntegerField(_('siralama'), default=0)
    is_active = models.BooleanField(_('aktif'), default=True)

    class Meta:
        verbose_name = _('Ekip Uyesi')
        verbose_name_plural = _('Ekip Uyeleri')
        ordering = ['sort_order']

    def __str__(self):
        return f"{self.name} — {self.title}"

    def save(self, *args, **kwargs):
        if not self.initials and self.name:
            parts = self.name.split()
            self.initials = ''.join(p[0].upper() for p in parts[:2])
        super().save(*args, **kwargs)


# =============================================================================
# COMPANY VALUE
# =============================================================================

class CompanyValue(TimeStampedModel):
    """Company values for the about page."""

    title = models.CharField(_('baslik'), max_length=200)
    description = models.TextField(_('aciklama'))
    icon = models.CharField(_('ikon'), max_length=50, blank=True)
    color = models.CharField(_('renk'), max_length=30, default='primary')
    sort_order = models.PositiveIntegerField(_('siralama'), default=0)
    is_active = models.BooleanField(_('aktif'), default=True)

    class Meta:
        verbose_name = _('Sirket Degeri')
        verbose_name_plural = _('Sirket Degerleri')
        ordering = ['sort_order']

    def __str__(self):
        return self.title


# =============================================================================
# LEGAL PAGE
# =============================================================================

class LegalPage(TimeStampedModel):
    """Legal page content managed from admin (privacy, terms, kvkk)."""

    class SlugChoices(models.TextChoices):
        PRIVACY = 'privacy', _('Gizlilik Politikasi')
        TERMS = 'terms', _('Kullanim Sartlari')
        KVKK = 'kvkk', _('KVKK Aydinlatma')
        COOKIE = 'cookie', _('Cerez Politikasi')
        SLA = 'sla', _('Hizmet Duzey Anlasmasi')
        DPA = 'dpa', _('Veri Isleme Anlasmasi')
        SECURITY = 'security', _('Guvenlik Politikasi')
        DISCLAIMER = 'disclaimer', _('Sorumluluk Reddi')

    slug = models.CharField(
        _('sayfa'),
        max_length=20,
        choices=SlugChoices.choices,
        unique=True,
    )
    title = models.CharField(_('baslik'), max_length=200)
    content = models.TextField(_('icerik'), help_text=_('HTML icerik desteklenir'))
    last_updated_display = models.CharField(
        _('son guncelleme (gorunum)'),
        max_length=50,
        blank=True,
        help_text=_('Sayfada gosterilecek tarih metni'),
    )
    meta_description = models.CharField(_('meta aciklama'), max_length=300, blank=True)
    is_active = models.BooleanField(_('aktif'), default=True)

    class Meta:
        verbose_name = _('Yasal Sayfa')
        verbose_name_plural = _('Yasal Sayfalar')
        ordering = ['slug']

    def __str__(self):
        return self.get_slug_display()


# =============================================================================
# BLOG POST
# =============================================================================

class BlogPost(SEOMixin, TimeStampedModel):
    """Blog posts for the marketing blog. Includes SEO fields via SEOMixin."""

    class StatusChoices(models.TextChoices):
        DRAFT = 'draft', _('Taslak')
        PUBLISHED = 'published', _('Yayinda')
        ARCHIVED = 'archived', _('Arsivlenmis')

    title = models.CharField(_('baslik'), max_length=300)
    slug = models.SlugField(_('slug'), max_length=300, unique=True)
    excerpt = models.TextField(_('ozet'), blank=True, help_text=_('Kart onizlemesinde gosterilir'))
    content = models.TextField(_('icerik'), help_text=_('HTML icerik desteklenir'))
    category = models.CharField(_('kategori'), max_length=100, blank=True)
    author_name = models.CharField(_('yazar'), max_length=100, blank=True)

    status = models.CharField(
        _('durum'),
        max_length=20,
        choices=StatusChoices.choices,
        default=StatusChoices.DRAFT,
    )
    published_at = models.DateTimeField(_('yayin tarihi'), null=True, blank=True)
    meta_description = models.CharField(_('meta aciklama'), max_length=300, blank=True)
    is_featured = models.BooleanField(_('one cikan'), default=False)

    class Meta:
        verbose_name = _('Blog Yazisi')
        verbose_name_plural = _('Blog Yazilari')
        ordering = ['-published_at', '-created_at']

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if self.status == self.StatusChoices.PUBLISHED and not self.published_at:
            self.published_at = timezone.now()
        super().save(*args, **kwargs)
