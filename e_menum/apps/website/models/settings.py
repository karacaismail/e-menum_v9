"""Singleton site settings model."""

import uuid

from django.db import models
from django.utils.translation import gettext_lazy as _

from .base import TimeStampedModel


class SiteSettings(TimeStampedModel):
    """
    Singleton model for site-wide settings.

    Replaces the hardcoded dict in context_processors.py.
    Use SiteSettings.load() to get the singleton instance.
    """

    # Company info
    company_name = models.CharField(_("sirket adi"), max_length=100, default="E-Menum")
    tagline = models.CharField(
        _("slogan"), max_length=200, default="QR Menunuz, Isletmenizin Dijital Vitrini"
    )
    description = models.TextField(_("aciklama"), blank=True)

    # Brand logos
    logo_url = models.URLField(
        _("logo URL (yatay)"),
        blank=True,
        max_length=500,
        help_text=_("Ana logo (navbar, footer). PNG/SVG, tercihen seffaf arkaplan."),
    )
    logo_icon_url = models.URLField(
        _("logo ikon URL (kare)"),
        blank=True,
        max_length=500,
        help_text=_("Kare ikon versiyonu (favicon, mobil). PNG/SVG."),
    )
    logo_dark_url = models.URLField(
        _("logo URL (koyu tema)"),
        blank=True,
        max_length=500,
        help_text=_("Koyu temada kullanilan logo versiyonu."),
    )
    favicon_url = models.URLField(
        _("favicon URL"),
        blank=True,
        max_length=500,
        help_text=_("Tarayici sekmesi ikonu. 32x32 veya SVG."),
    )

    # Contact info
    phone = models.CharField(_("telefon"), max_length=30, default="+90 850 123 4567")
    email = models.EmailField(_("e-posta"), default="info@e-menum.net")
    address = models.CharField(_("adres"), max_length=200, default="Istanbul, Turkiye")

    # Social media
    social_instagram = models.URLField(
        _("Instagram"), blank=True, default="https://instagram.com/emenum"
    )
    social_twitter = models.URLField(
        _("Twitter / X"), blank=True, default="https://twitter.com/emenum"
    )
    social_linkedin = models.URLField(
        _("LinkedIn"), blank=True, default="https://linkedin.com/company/emenum"
    )
    social_youtube = models.URLField(
        _("YouTube"), blank=True, default="https://youtube.com/@emenum"
    )

    # WhatsApp
    whatsapp_number = models.CharField(
        _("WhatsApp numara"), max_length=20, default="908501234567"
    )
    whatsapp_message = models.CharField(
        _("WhatsApp mesaj"),
        max_length=300,
        default="Merhaba! E-Menum hakkinda bilgi almak istiyorum.",
    )

    # CTA defaults
    cta_primary_text = models.CharField(
        _("birincil CTA metni"), max_length=100, default="14 Gun Ucretsiz Basla"
    )
    cta_secondary_text = models.CharField(
        _("ikincil CTA metni"), max_length=100, default="Demo Iste"
    )
    cta_trust_text = models.CharField(
        _("guven metni"),
        max_length=200,
        default="Kredi karti gerekmez \u00b7 2 dakikada kurulum",
    )
    cta_primary_url = models.CharField(
        _("birincil CTA URL"), max_length=100, default="website:demo"
    )
    cta_secondary_url = models.CharField(
        _("ikincil CTA URL"), max_length=100, default="website:demo"
    )

    # Login URL
    login_url = models.CharField(_("giris URL"), max_length=100, default="/admin/")

    # Announcement bar
    announcement_text = models.CharField(_("duyuru metni"), max_length=300, blank=True)
    announcement_url = models.CharField(_("duyuru URL"), max_length=200, blank=True)
    announcement_is_active = models.BooleanField(_("duyuru aktif"), default=False)

    # Cookie banner
    cookie_banner_title = models.CharField(
        _("cerez banner basligi"), max_length=200, default="Cerez Kullanimi"
    )
    cookie_banner_text = models.TextField(
        _("cerez banner metni"),
        blank=True,
        default="Web sitemizde size daha iyi bir deneyim sunabilmek icin cerezleri kullaniyoruz.",
    )

    # Additional branding
    vat_no = models.CharField(_("vergi no"), max_length=30, blank=True)
    mersis_no = models.CharField(_("mersis no"), max_length=30, blank=True)
    trade_registry = models.CharField(_("ticaret sicil"), max_length=100, blank=True)

    # Pricing promo
    pricing_yearly_badge = models.CharField(
        _("yillik promo rozeti"), max_length=50, default="2 AY BEDAVA",
        help_text=_("Yillik toggle badge metni (orn. '2 AY BEDAVA', '%17 INDIRIM')"),
    )
    pricing_yearly_note = models.CharField(
        _("yillik promo notu"), max_length=200, blank=True,
        default="Yillik odemede 10 ay ucreti alinir.",
        help_text=_("Toggle altinda gosterilen aciklama metni."),
    )

    # Status page
    status_page_url = models.URLField(
        _("durum sayfasi URL"), blank=True, default="https://status.e-menum.net"
    )

    class Meta:
        verbose_name = _("Site Ayarlari")
        verbose_name_plural = _("Site Ayarlari")

    def __str__(self):
        return self.company_name

    def save(self, *args, **kwargs):
        """Enforce singleton: always use pk of first record."""
        if not self.pk and SiteSettings.objects.exists():
            # If creating a new one but one already exists, overwrite
            existing = SiteSettings.objects.first()
            self.pk = existing.pk
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        """Get or create the singleton instance."""
        obj, _ = cls.objects.get_or_create(
            pk=cls.objects.first().pk if cls.objects.exists() else uuid.uuid4(),
        )
        return obj
