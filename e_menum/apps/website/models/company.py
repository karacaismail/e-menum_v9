"""Company — careers, press releases, milestones, brand assets."""

from django.db import models
from django.utils.translation import gettext_lazy as _

from .base import TimeStampedModel
from apps.seo.models import SEOMixin


# =============================================================================
# CAREER POSITION
# =============================================================================


class CareerPosition(TimeStampedModel):
    """Job openings / career positions."""

    class EmploymentTypeChoices(models.TextChoices):
        FULL_TIME = "full_time", _("Tam Zamanli")
        PART_TIME = "part_time", _("Yari Zamanli")
        CONTRACT = "contract", _("Sozlesmeli")
        REMOTE = "remote", _("Uzaktan")
        INTERN = "intern", _("Stajyer")

    title = models.CharField(_("pozisyon"), max_length=200)
    slug = models.SlugField(_("slug"), max_length=200, unique=True)
    department = models.CharField(_("departman"), max_length=100)
    location = models.CharField(_("konum"), max_length=100, default="Istanbul, Turkiye")
    employment_type = models.CharField(
        _("calisma sekli"),
        max_length=20,
        choices=EmploymentTypeChoices.choices,
        default=EmploymentTypeChoices.FULL_TIME,
    )
    description = models.TextField(_("aciklama"), help_text=_("HTML icerik"))
    requirements = models.TextField(
        _("gereksinimler"), blank=True, help_text=_("HTML icerik")
    )
    benefits = models.TextField(_("yan haklar"), blank=True, help_text=_("HTML icerik"))
    apply_url = models.URLField(_("basvuru URL"), blank=True)
    is_featured = models.BooleanField(_("one cikan"), default=False)
    published_at = models.DateTimeField(_("yayin tarihi"), null=True, blank=True)
    expires_at = models.DateTimeField(_("bitis tarihi"), null=True, blank=True)
    sort_order = models.PositiveIntegerField(_("siralama"), default=0)
    is_active = models.BooleanField(_("aktif"), default=True)

    class Meta:
        verbose_name = _("Kariyer Ilani")
        verbose_name_plural = _("Kariyer Ilanlari")
        ordering = ["-published_at", "-created_at"]

    def __str__(self):
        return f"{self.title} — {self.department}"


# =============================================================================
# PRESS RELEASE
# =============================================================================


class PressRelease(SEOMixin, TimeStampedModel):
    """Press releases and media mentions."""

    title = models.CharField(_("baslik"), max_length=300)
    slug = models.SlugField(_("slug"), max_length=300, unique=True)
    excerpt = models.TextField(_("ozet"), blank=True)
    content = models.TextField(_("icerik"), help_text=_("HTML icerik"))
    source = models.CharField(
        _("kaynak"), max_length=200, blank=True, help_text=_("Orn: Bloomberg Turkiye")
    )
    source_url = models.URLField(_("kaynak URL"), blank=True)
    cover_image = models.ImageField(
        _("kapak gorseli"), upload_to="website/press/", blank=True, null=True
    )
    published_at = models.DateTimeField(_("yayin tarihi"), null=True, blank=True)
    is_featured = models.BooleanField(_("one cikan"), default=False)
    sort_order = models.PositiveIntegerField(_("siralama"), default=0)
    is_active = models.BooleanField(_("aktif"), default=True)

    class Meta:
        verbose_name = _("Basin Bulteni")
        verbose_name_plural = _("Basin Bultenleri")
        ordering = ["-published_at", "-created_at"]

    def __str__(self):
        return self.title


# =============================================================================
# MILESTONE
# =============================================================================


class Milestone(TimeStampedModel):
    """Company timeline milestones."""

    year = models.PositiveIntegerField(_("yil"))
    quarter = models.CharField(
        _("ceyrek"), max_length=2, blank=True, help_text=_("Q1, Q2, Q3, Q4")
    )
    title = models.CharField(_("baslik"), max_length=200)
    description = models.TextField(_("aciklama"), blank=True)
    icon = models.CharField(_("ikon"), max_length=50, blank=True)
    sort_order = models.PositiveIntegerField(_("siralama"), default=0)
    is_active = models.BooleanField(_("aktif"), default=True)

    class Meta:
        verbose_name = _("Kilometre Tasi")
        verbose_name_plural = _("Kilometre Taslari")
        ordering = ["-year", "quarter", "sort_order"]

    def __str__(self):
        q = f" {self.quarter}" if self.quarter else ""
        return f"{self.year}{q} — {self.title}"


# =============================================================================
# BRAND ASSET
# =============================================================================


class BrandAsset(TimeStampedModel):
    """Downloadable brand assets (logos, media kit, guidelines)."""

    class AssetTypeChoices(models.TextChoices):
        LOGO = "logo", _("Logo")
        ICON = "icon", _("Ikon")
        GUIDELINE = "guideline", _("Marka Kilavuzu")
        PRESS_KIT = "press_kit", _("Basin Kiti")
        COLOR_PALETTE = "color_palette", _("Renk Paleti")
        FONT = "font", _("Yazi Tipi")

    title = models.CharField(_("baslik"), max_length=200)
    description = models.TextField(_("aciklama"), blank=True)
    file = models.FileField(_("dosya"), upload_to="website/brand/")
    preview_image = models.ImageField(
        _("onizleme"), upload_to="website/brand/previews/", blank=True, null=True
    )
    asset_type = models.CharField(
        _("varlik tipi"),
        max_length=20,
        choices=AssetTypeChoices.choices,
        default=AssetTypeChoices.LOGO,
    )
    file_format = models.CharField(
        _("dosya formati"), max_length=10, blank=True, help_text=_("svg, png, pdf, zip")
    )
    sort_order = models.PositiveIntegerField(_("siralama"), default=0)
    is_active = models.BooleanField(_("aktif"), default=True)

    class Meta:
        verbose_name = _("Marka Varligi")
        verbose_name_plural = _("Marka Varliklari")
        ordering = ["asset_type", "sort_order"]

    def __str__(self):
        return f"{self.title} ({self.get_asset_type_display()})"
