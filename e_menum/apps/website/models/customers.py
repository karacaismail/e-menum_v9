"""Customer success — case studies, ROI calculator, testimonials."""

from django.db import models
from django.utils.translation import gettext_lazy as _

from .base import TimeStampedModel
from apps.seo.models import SEOMixin


# =============================================================================
# CASE STUDY
# =============================================================================


class CaseStudy(SEOMixin, TimeStampedModel):
    """Customer success stories / case studies."""

    title = models.CharField(_("baslik"), max_length=200)
    slug = models.SlugField(_("slug"), max_length=200, unique=True)
    company_name = models.CharField(_("sirket adi"), max_length=200)
    company_logo = models.ImageField(
        _("sirket logosu"), upload_to="website/case-studies/", blank=True, null=True
    )

    sector = models.ForeignKey(
        "website.Sector",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="case_studies",
        verbose_name=_("sektor"),
    )
    company_size = models.CharField(_("sirket buyuklugu"), max_length=50, blank=True)
    location = models.CharField(_("konum"), max_length=100, blank=True)

    excerpt = models.TextField(
        _("ozet"), blank=True, help_text=_("Kart onizlemesi (max 200 karakter)")
    )
    challenge = models.TextField(_("zorluk"), blank=True, help_text=_("HTML icerik"))
    solution = models.TextField(_("cozum"), blank=True, help_text=_("HTML icerik"))
    results = models.TextField(_("sonuclar"), blank=True, help_text=_("HTML icerik"))

    # Highlight stats (up to 3)
    stat_1_value = models.CharField(_("istatistik 1 deger"), max_length=20, blank=True)
    stat_1_label = models.CharField(
        _("istatistik 1 etiket"), max_length=100, blank=True
    )
    stat_2_value = models.CharField(_("istatistik 2 deger"), max_length=20, blank=True)
    stat_2_label = models.CharField(
        _("istatistik 2 etiket"), max_length=100, blank=True
    )
    stat_3_value = models.CharField(_("istatistik 3 deger"), max_length=20, blank=True)
    stat_3_label = models.CharField(
        _("istatistik 3 etiket"), max_length=100, blank=True
    )

    # Testimonial quote
    quote = models.TextField(_("musteri yorumu"), blank=True)
    quote_author = models.CharField(_("yorum sahibi"), max_length=100, blank=True)
    quote_author_title = models.CharField(
        _("yorum sahibi unvani"), max_length=200, blank=True
    )

    hero_image = models.ImageField(
        _("hero gorsel"), upload_to="website/case-studies/", blank=True, null=True
    )
    is_featured = models.BooleanField(_("one cikan"), default=False)
    published_at = models.DateTimeField(_("yayin tarihi"), null=True, blank=True)
    sort_order = models.PositiveIntegerField(_("siralama"), default=0)
    is_active = models.BooleanField(_("aktif"), default=True)

    class Meta:
        verbose_name = _("Basari Hikayesi")
        verbose_name_plural = _("Basari Hikayeleri")
        ordering = ["-published_at", "-created_at"]

    def __str__(self):
        return f"{self.company_name} — {self.title}"


# =============================================================================
# ROI CALCULATOR CONFIG
# =============================================================================


class ROICalculatorConfig(TimeStampedModel):
    """Configuration for the ROI calculator tool. Singleton."""

    title = models.CharField(_("baslik"), max_length=200, default="ROI Hesaplayici")
    description = models.TextField(_("aciklama"), blank=True)
    avg_order_increase_pct = models.DecimalField(
        _("ort. siparis artisi %"),
        max_digits=5,
        decimal_places=2,
        default=15.00,
    )
    avg_cost_reduction_pct = models.DecimalField(
        _("ort. maliyet azalma %"),
        max_digits=5,
        decimal_places=2,
        default=30.00,
    )
    avg_time_saved_hours = models.DecimalField(
        _("ort. tasarruf (saat/hafta)"),
        max_digits=5,
        decimal_places=2,
        default=10.00,
    )
    avg_menu_print_cost = models.DecimalField(
        _("ort. menu baski maliyeti (TL/ay)"),
        max_digits=8,
        decimal_places=2,
        default=2500.00,
    )
    is_active = models.BooleanField(_("aktif"), default=True)

    class Meta:
        verbose_name = _("ROI Hesaplayici Ayari")
        verbose_name_plural = _("ROI Hesaplayici Ayarlari")

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.pk and ROICalculatorConfig.objects.exists():
            existing = ROICalculatorConfig.objects.first()
            self.pk = existing.pk
        super().save(*args, **kwargs)
