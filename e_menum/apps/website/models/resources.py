"""Resources — reports, tools, webinars (blog is in content.py)."""

from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from .base import TimeStampedModel
from apps.seo.models import SEOMixin


# =============================================================================
# RESOURCE CATEGORY
# =============================================================================

class ResourceCategory(TimeStampedModel):
    """Categories for resources (reports, tools, webinars)."""

    name = models.CharField(_('ad'), max_length=100)
    slug = models.SlugField(_('slug'), max_length=100, unique=True)
    sort_order = models.PositiveIntegerField(_('siralama'), default=0)
    is_active = models.BooleanField(_('aktif'), default=True)

    class Meta:
        verbose_name = _('Kaynak Kategorisi')
        verbose_name_plural = _('Kaynak Kategorileri')
        ordering = ['sort_order']

    def __str__(self):
        return self.name


# =============================================================================
# INDUSTRY REPORT
# =============================================================================

class IndustryReport(SEOMixin, TimeStampedModel):
    """Downloadable industry reports / whitepapers."""

    title = models.CharField(_('baslik'), max_length=200)
    slug = models.SlugField(_('slug'), max_length=200, unique=True)
    excerpt = models.TextField(_('ozet'), blank=True)
    content = models.TextField(_('icerik'), blank=True, help_text=_('Rapor tanitim sayfasi HTML'))
    category = models.ForeignKey(
        ResourceCategory, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='reports', verbose_name=_('kategori'),
    )
    cover_image = models.ImageField(_('kapak gorseli'), upload_to='website/reports/', blank=True, null=True)
    file = models.FileField(_('PDF dosya'), upload_to='website/reports/files/', blank=True, null=True)
    requires_email = models.BooleanField(_('email gerektirir'), default=True, help_text=_('Indirmek icin email zorunlu'))
    download_count = models.PositiveIntegerField(_('indirme sayisi'), default=0)
    published_at = models.DateTimeField(_('yayin tarihi'), null=True, blank=True)
    is_active = models.BooleanField(_('aktif'), default=True)

    class Meta:
        verbose_name = _('Sektor Raporu')
        verbose_name_plural = _('Sektor Raporlari')
        ordering = ['-published_at', '-created_at']

    def __str__(self):
        return self.title


# =============================================================================
# FREE TOOL
# =============================================================================

class FreeTool(SEOMixin, TimeStampedModel):
    """Free online tools (calculators, generators, etc.)."""

    class ToolTypeChoices(models.TextChoices):
        MENU_COST = 'menu_cost', _('Menu Maliyet Hesaplayici')
        QR_PREVIEW = 'qr_preview', _('QR Kod Onizleme')
        ROI_CALC = 'roi_calc', _('ROI Hesaplayici')
        QR_DESIGNER = 'qr_designer', _('QR Kod Tasarlayici')

    title = models.CharField(_('baslik'), max_length=200)
    slug = models.SlugField(_('slug'), max_length=200, unique=True)
    description = models.TextField(_('aciklama'), blank=True)
    icon = models.CharField(_('ikon'), max_length=50, blank=True)
    tool_type = models.CharField(
        _('arac tipi'), max_length=50,
        choices=ToolTypeChoices.choices, default=ToolTypeChoices.MENU_COST,
    )
    template_name = models.CharField(
        _('template adi'), max_length=200, blank=True,
        help_text=_('Ozel template (orn: website/tools/roi_calc.html)'),
    )
    sort_order = models.PositiveIntegerField(_('siralama'), default=0)
    is_active = models.BooleanField(_('aktif'), default=True)

    class Meta:
        verbose_name = _('Ucretsiz Arac')
        verbose_name_plural = _('Ucretsiz Araclar')
        ordering = ['sort_order']

    def __str__(self):
        return self.title


# =============================================================================
# WEBINAR
# =============================================================================

class Webinar(SEOMixin, TimeStampedModel):
    """Webinar / online event listings."""

    class StatusChoices(models.TextChoices):
        UPCOMING = 'upcoming', _('Yaklasan')
        LIVE = 'live', _('Canli')
        RECORDED = 'recorded', _('Kayit')
        CANCELLED = 'cancelled', _('Iptal')

    title = models.CharField(_('baslik'), max_length=200)
    slug = models.SlugField(_('slug'), max_length=200, unique=True)
    description = models.TextField(_('aciklama'), blank=True)
    speaker_name = models.CharField(_('konusmaci'), max_length=100, blank=True)
    speaker_title = models.CharField(_('konusmaci unvani'), max_length=200, blank=True)
    speaker_avatar = models.ImageField(_('konusmaci fotografi'), upload_to='website/webinars/', blank=True, null=True)
    event_date = models.DateTimeField(_('etkinlik tarihi'), null=True, blank=True)
    duration_minutes = models.PositiveIntegerField(_('sure (dakika)'), default=60)
    video_url = models.URLField(_('video URL'), blank=True)
    registration_url = models.URLField(_('kayit URL'), blank=True)
    cover_image = models.ImageField(_('kapak gorseli'), upload_to='website/webinars/', blank=True, null=True)
    status = models.CharField(
        _('durum'), max_length=20,
        choices=StatusChoices.choices, default=StatusChoices.UPCOMING,
    )
    sort_order = models.PositiveIntegerField(_('siralama'), default=0)
    is_active = models.BooleanField(_('aktif'), default=True)

    class Meta:
        verbose_name = _('Webinar')
        verbose_name_plural = _('Webinarlar')
        ordering = ['-event_date', '-created_at']

    def __str__(self):
        return self.title

    @property
    def is_upcoming(self):
        return self.event_date and self.event_date > timezone.now()
