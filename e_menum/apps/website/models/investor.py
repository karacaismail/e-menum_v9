"""Investor relations — page content, presentations, financials."""

from django.db import models
from django.utils.translation import gettext_lazy as _

from .base import TimeStampedModel


# =============================================================================
# INVESTOR PAGE
# =============================================================================

class InvestorPage(TimeStampedModel):
    """Singleton investor relations page content."""

    title = models.CharField(_('baslik'), max_length=200, default='Yatirimci Iliskileri')
    subtitle = models.TextField(_('alt baslik'), blank=True)
    overview_content = models.TextField(_('genel bakis'), blank=True, help_text=_('HTML icerik'))
    market_size_tam = models.CharField(_('TAM'), max_length=50, blank=True, help_text=_('Toplam Adreslenebilir Pazar'))
    market_size_sam = models.CharField(_('SAM'), max_length=50, blank=True, help_text=_('Hizmet Verilebilir Pazar'))
    market_size_som = models.CharField(_('SOM'), max_length=50, blank=True, help_text=_('Elde Edilebilir Pazar'))
    investment_thesis = models.TextField(_('yatirim tezi'), blank=True, help_text=_('HTML icerik'))
    contact_email = models.EmailField(_('iletisim e-posta'), blank=True, default='investor@e-menum.net')
    is_active = models.BooleanField(_('aktif'), default=True)

    class Meta:
        verbose_name = _('Yatirimci Sayfasi')
        verbose_name_plural = _('Yatirimci Sayfalari')

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.pk and InvestorPage.objects.exists():
            existing = InvestorPage.objects.first()
            self.pk = existing.pk
        super().save(*args, **kwargs)


# =============================================================================
# INVESTOR PRESENTATION
# =============================================================================

class InvestorPresentation(TimeStampedModel):
    """Investor presentations / pitch decks."""

    title = models.CharField(_('baslik'), max_length=200)
    description = models.TextField(_('aciklama'), blank=True)
    file = models.FileField(_('dosya'), upload_to='website/investor/')
    cover_image = models.ImageField(_('kapak'), upload_to='website/investor/covers/', blank=True, null=True)
    presentation_date = models.DateField(_('sunum tarihi'), null=True, blank=True)
    sort_order = models.PositiveIntegerField(_('siralama'), default=0)
    is_active = models.BooleanField(_('aktif'), default=True)

    class Meta:
        verbose_name = _('Yatirimci Sunumu')
        verbose_name_plural = _('Yatirimci Sunumlari')
        ordering = ['-presentation_date', 'sort_order']

    def __str__(self):
        return self.title


# =============================================================================
# INVESTOR FINANCIAL
# =============================================================================

class InvestorFinancial(TimeStampedModel):
    """Financial highlights / KPI metrics for investor page."""

    period = models.CharField(_('donem'), max_length=50, help_text=_('Orn: Q4 2025, FY 2025'))
    metric_name = models.CharField(_('metrik adi'), max_length=100)
    metric_value = models.CharField(_('deger'), max_length=50)
    change_pct = models.DecimalField(
        _('degisim %'), max_digits=6, decimal_places=2, null=True, blank=True,
    )
    sort_order = models.PositiveIntegerField(_('siralama'), default=0)
    is_active = models.BooleanField(_('aktif'), default=True)

    class Meta:
        verbose_name = _('Finansal Gosterge')
        verbose_name_plural = _('Finansal Gostergeler')
        ordering = ['-period', 'sort_order']

    def __str__(self):
        return f"{self.period} — {self.metric_name}: {self.metric_value}"
