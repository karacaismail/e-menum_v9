"""Social proof models — Testimonial, TrustBadge, TrustLocation, CompanyStat."""

from django.db import models
from django.utils.translation import gettext_lazy as _

from .base import TimeStampedModel


# =============================================================================
# TESTIMONIAL
# =============================================================================


class Testimonial(TimeStampedModel):
    """Customer testimonials for social proof."""

    author_name = models.CharField(_("yazar adi"), max_length=100)
    initials = models.CharField(_("bas harfler"), max_length=5, blank=True)
    author_role_or_business = models.CharField(
        _("rol / isletme"), max_length=200, blank=True
    )
    author_location = models.CharField(_("konum"), max_length=100, blank=True)

    business_type_label = models.CharField(
        _("isletme tipi etiketi"), max_length=50, blank=True
    )
    badge_color = models.CharField(_("badge rengi"), max_length=30, default="primary")
    avatar_color = models.CharField(_("avatar rengi"), max_length=30, default="primary")

    quote = models.TextField(_("yorum"))
    rating = models.PositiveSmallIntegerField(
        _("puan"), default=5, help_text=_("1-5 arasi")
    )

    sort_order = models.PositiveIntegerField(_("siralama"), default=0)
    is_active = models.BooleanField(_("aktif"), default=True)

    class Meta:
        verbose_name = _("Musteri Yorumu")
        verbose_name_plural = _("Musteri Yorumlari")
        ordering = ["sort_order"]

    def __str__(self):
        return f"{self.author_name} — {self.rating}\u2605"

    def save(self, *args, **kwargs):
        if not self.initials and self.author_name:
            parts = self.author_name.split()
            self.initials = "".join(p[0].upper() for p in parts[:2])
        super().save(*args, **kwargs)


# =============================================================================
# TRUST BADGE + TRUST LOCATION
# =============================================================================


class TrustBadge(TimeStampedModel):
    """Trust badges displayed on trust bar (KVKK, SSL, Uptime, etc.)."""

    label = models.CharField(_("etiket"), max_length=100)
    icon = models.CharField(
        _("ikon"), max_length=50, help_text=_("Phosphor icon sinifi")
    )
    sort_order = models.PositiveIntegerField(_("siralama"), default=0)
    is_active = models.BooleanField(_("aktif"), default=True)

    class Meta:
        verbose_name = _("Guven Rozeti")
        verbose_name_plural = _("Guven Rozetleri")
        ordering = ["sort_order"]

    def __str__(self):
        return self.label


class TrustLocation(TimeStampedModel):
    """Location-based social proof entries (e.g., "Istanbul'dan 47 isletme")."""

    text = models.CharField(_("metin"), max_length=200)
    sort_order = models.PositiveIntegerField(_("siralama"), default=0)
    is_active = models.BooleanField(_("aktif"), default=True)

    class Meta:
        verbose_name = _("Guven Lokasyon")
        verbose_name_plural = _("Guven Lokasyonlari")
        ordering = ["sort_order"]

    def __str__(self):
        return self.text


# =============================================================================
# COMPANY STAT
# =============================================================================


class CompanyStat(TimeStampedModel):
    """Company statistics for the about page."""

    value = models.CharField(_("deger"), max_length=50)
    label = models.CharField(_("etiket"), max_length=100)
    sort_order = models.PositiveIntegerField(_("siralama"), default=0)
    is_active = models.BooleanField(_("aktif"), default=True)

    class Meta:
        verbose_name = _("Sirket Istatistigi")
        verbose_name_plural = _("Sirket Istatistikleri")
        ordering = ["sort_order"]

    def __str__(self):
        return f"{self.value} — {self.label}"
