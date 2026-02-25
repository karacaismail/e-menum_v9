"""Partner programs — reseller, referral, white-label, technology."""

from django.db import models
from django.utils.translation import gettext_lazy as _

from .base import TimeStampedModel


# =============================================================================
# PARTNER PROGRAM
# =============================================================================

class PartnerProgram(TimeStampedModel):
    """Partner program types."""

    class ProgramTypeChoices(models.TextChoices):
        RESELLER = 'reseller', _('Bayi')
        REFERRAL = 'referral', _('Referans')
        WHITE_LABEL = 'white_label', _('Beyaz Etiket')
        TECHNOLOGY = 'technology', _('Teknoloji Ortagi')
        INTEGRATION = 'integration', _('Entegrasyon Ortagi')

    title = models.CharField(_('baslik'), max_length=200)
    slug = models.SlugField(_('slug'), max_length=200, unique=True)
    description = models.TextField(_('aciklama'), help_text=_('HTML icerik'))
    program_type = models.CharField(
        _('program tipi'), max_length=30,
        choices=ProgramTypeChoices.choices, default=ProgramTypeChoices.RESELLER,
    )
    icon = models.CharField(_('ikon'), max_length=50, blank=True)
    hero_image = models.ImageField(_('hero gorsel'), upload_to='website/partners/', blank=True, null=True)
    commission_info = models.TextField(_('komisyon bilgisi'), blank=True)
    requirements = models.TextField(_('katilim kosullari'), blank=True, help_text=_('HTML icerik'))
    contact_email = models.EmailField(_('iletisim e-posta'), blank=True, default='partners@e-menum.net')
    sort_order = models.PositiveIntegerField(_('siralama'), default=0)
    is_active = models.BooleanField(_('aktif'), default=True)

    class Meta:
        verbose_name = _('Partner Programi')
        verbose_name_plural = _('Partner Programlari')
        ordering = ['sort_order']

    def __str__(self):
        return f"{self.title} ({self.get_program_type_display()})"


# =============================================================================
# PARTNER TIER
# =============================================================================

class PartnerTier(TimeStampedModel):
    """Tiers within a partner program (Silver, Gold, Platinum)."""

    program = models.ForeignKey(
        PartnerProgram, on_delete=models.CASCADE,
        related_name='tiers', verbose_name=_('program'),
    )
    name = models.CharField(_('ad'), max_length=100)
    description = models.TextField(_('aciklama'), blank=True)
    commission_pct = models.DecimalField(
        _('komisyon %'), max_digits=5, decimal_places=2, null=True, blank=True,
    )
    color = models.CharField(_('renk'), max_length=30, default='primary')
    sort_order = models.PositiveIntegerField(_('siralama'), default=0)
    is_active = models.BooleanField(_('aktif'), default=True)

    class Meta:
        verbose_name = _('Partner Seviyesi')
        verbose_name_plural = _('Partner Seviyeleri')
        ordering = ['program', 'sort_order']

    def __str__(self):
        return f"{self.program.title} — {self.name}"


# =============================================================================
# PARTNER BENEFIT
# =============================================================================

class PartnerBenefit(TimeStampedModel):
    """Bullet-point benefits for a partner tier."""

    tier = models.ForeignKey(
        PartnerTier, on_delete=models.CASCADE,
        related_name='benefits', verbose_name=_('seviye'),
    )
    text = models.CharField(_('metin'), max_length=300)
    icon = models.CharField(_('ikon'), max_length=50, blank=True)
    sort_order = models.PositiveIntegerField(_('siralama'), default=0)
    is_active = models.BooleanField(_('aktif'), default=True)

    class Meta:
        verbose_name = _('Partner Avantaji')
        verbose_name_plural = _('Partner Avantajlari')
        ordering = ['tier', 'sort_order']

    def __str__(self):
        return f"{self.tier.name} — {self.text[:50]}"
