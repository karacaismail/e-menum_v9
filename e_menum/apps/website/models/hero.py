"""Hero banner and home section models."""

from django.db import models
from django.utils.translation import gettext_lazy as _

from .base import TimeStampedModel


# =============================================================================
# PAGE HERO
# =============================================================================


class PageHero(TimeStampedModel):
    """Hero banner content for each marketing page."""

    class PageChoices(models.TextChoices):
        HOME = "home", _("Ana Sayfa")
        FEATURES = "features", _("Ozellikler")
        PRICING = "pricing", _("Fiyatlandirma")
        ABOUT = "about", _("Hakkimizda")
        CONTACT = "contact", _("Iletisim")
        DEMO = "demo", _("Demo")
        BLOG = "blog", _("Blog")
        SOLUTIONS = "solutions", _("Cozumler")
        CUSTOMERS = "customers", _("Musteriler")
        RESOURCES = "resources", _("Kaynaklar")
        INVESTOR = "investor", _("Yatirimci")
        PARTNERS = "partners", _("Partnerler")
        SUPPORT = "support", _("Destek")
        CAREERS = "careers", _("Kariyer")
        PRESS = "press", _("Basin")

    page = models.CharField(
        _("sayfa"),
        max_length=20,
        choices=PageChoices.choices,
        unique=True,
    )
    title = models.CharField(_("baslik"), max_length=200)
    subtitle = models.TextField(_("alt baslik"), blank=True)
    badge_text = models.CharField(_("badge metni"), max_length=100, blank=True)
    gradient_class = models.CharField(
        _("gradient sinifi"), max_length=50, default="hero-gradient"
    )

    # CTA overrides (empty = use SiteSettings defaults)
    cta_primary_text = models.CharField(_("birincil CTA"), max_length=100, blank=True)
    cta_primary_url = models.CharField(
        _("birincil CTA URL"), max_length=100, blank=True
    )
    cta_secondary_text = models.CharField(_("ikincil CTA"), max_length=100, blank=True)
    cta_secondary_url = models.CharField(
        _("ikincil CTA URL"), max_length=100, blank=True
    )
    trust_text = models.CharField(_("guven metni"), max_length=200, blank=True)

    show_hero_image = models.BooleanField(_("hero gorsel goster"), default=True)
    is_active = models.BooleanField(_("aktif"), default=True)

    class Meta:
        verbose_name = _("Sayfa Hero")
        verbose_name_plural = _("Sayfa Hero'lari")
        ordering = ["page"]

    def __str__(self):
        return f"{self.get_page_display()} — {self.title[:50]}"


# =============================================================================
# HOME SECTION
# =============================================================================


class HomeSection(TimeStampedModel):
    """Content blocks for the home page (problem/solution, features, steps, stats)."""

    class SectionTypeChoices(models.TextChoices):
        PROBLEM_SOLUTION = "problem_solution", _("Problem / Cozum")
        FEATURE_CARD = "feature_card", _("Ozellik Karti")
        HOW_IT_WORKS = "how_it_works", _("Nasil Calisir")
        STAT_COUNTER = "stat_counter", _("Istatistik Sayac")

    class CardVariantChoices(models.TextChoices):
        PROBLEM = "problem", _("Problem")
        SOLUTION = "solution", _("Cozum")
        DIFFERENTIATOR = "differentiator", _("Fark")

    section_type = models.CharField(
        _("bolum tipi"),
        max_length=30,
        choices=SectionTypeChoices.choices,
    )
    title = models.CharField(_("baslik"), max_length=200)
    description = models.TextField(_("aciklama"), blank=True)
    icon = models.CharField(
        _("ikon"),
        max_length=50,
        blank=True,
        help_text=_("Phosphor icon sinifi (ornek: ph-qr-code)"),
    )
    color = models.CharField(
        _("renk"),
        max_length=30,
        blank=True,
        help_text=_("Tailwind renk adi (ornek: primary, green, red)"),
    )

    # Stat counter fields
    stat_value = models.CharField(
        _("istatistik degeri"),
        max_length=20,
        blank=True,
        help_text=_("Ornek: 350.000+"),
    )
    stat_suffix = models.CharField(
        _("istatistik eki"), max_length=20, blank=True, help_text=_("Ornek: +, %, x")
    )

    # How it works
    step_number = models.PositiveIntegerField(_("adim numarasi"), null=True, blank=True)

    # Problem/Solution card variant
    card_variant = models.CharField(
        _("kart varyanti"),
        max_length=20,
        choices=CardVariantChoices.choices,
        blank=True,
    )

    sort_order = models.PositiveIntegerField(_("siralama"), default=0)
    is_active = models.BooleanField(_("aktif"), default=True)

    class Meta:
        verbose_name = _("Ana Sayfa Bolumu")
        verbose_name_plural = _("Ana Sayfa Bolumleri")
        ordering = ["section_type", "sort_order"]

    def __str__(self):
        return f"[{self.get_section_type_display()}] {self.title}"
