"""Solution pages — sector and business-size based landing pages."""

from django.db import models
from django.utils.translation import gettext_lazy as _

from .base import TimeStampedModel
from apps.seo.models import SEOMixin


# =============================================================================
# SECTOR
# =============================================================================


class Sector(TimeStampedModel):
    """Industry sectors (restoran, kafe, otel, zincir, etc.)."""

    name = models.CharField(_("ad"), max_length=100)
    slug = models.SlugField(_("slug"), max_length=100, unique=True)
    description = models.TextField(_("aciklama"), blank=True)
    icon = models.CharField(
        _("ikon"), max_length=50, blank=True, help_text=_("Phosphor icon sinifi")
    )
    color = models.CharField(_("renk"), max_length=30, default="primary")
    sort_order = models.PositiveIntegerField(_("siralama"), default=0)
    is_active = models.BooleanField(_("aktif"), default=True)

    class Meta:
        verbose_name = _("Sektor")
        verbose_name_plural = _("Sektorler")
        ordering = ["sort_order"]

    def __str__(self):
        return self.name


# =============================================================================
# SOLUTION PAGE
# =============================================================================


class SolutionPage(SEOMixin, TimeStampedModel):
    """Solution landing pages for sectors or business sizes."""

    class SolutionTypeChoices(models.TextChoices):
        SECTOR = "sector", _("Sektore Gore")
        SIZE = "size", _("Buyukluge Gore")
        USE_CASE = "use_case", _("Kullanim Alanina Gore")

    title = models.CharField(_("baslik"), max_length=200)
    slug = models.SlugField(_("slug"), max_length=200, unique=True)
    subtitle = models.TextField(_("alt baslik"), blank=True)
    content = models.TextField(_("icerik"), blank=True, help_text=_("HTML icerik"))
    hero_image = models.ImageField(
        _("hero gorsel"), upload_to="website/solutions/", blank=True, null=True
    )
    hero_gradient_class = models.CharField(
        _("gradient sinifi"), max_length=50, default="hero-gradient"
    )

    sector = models.ForeignKey(
        Sector,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="solution_pages",
        verbose_name=_("sektor"),
    )
    solution_type = models.CharField(
        _("cozum tipi"),
        max_length=20,
        choices=SolutionTypeChoices.choices,
        default=SolutionTypeChoices.SECTOR,
    )
    key_benefits = models.TextField(
        _("temel faydalar"), blank=True, help_text=_("HTML liste")
    )
    pain_points = models.TextField(_("sorunlar"), blank=True, help_text=_("HTML liste"))
    target_audience = models.CharField(_("hedef kitle"), max_length=200, blank=True)

    is_featured = models.BooleanField(_("one cikan"), default=False)
    sort_order = models.PositiveIntegerField(_("siralama"), default=0)
    is_active = models.BooleanField(_("aktif"), default=True)

    class Meta:
        verbose_name = _("Cozum Sayfasi")
        verbose_name_plural = _("Cozum Sayfalari")
        ordering = ["sort_order"]

    def __str__(self):
        return self.title
