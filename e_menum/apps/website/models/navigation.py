"""Navigation link model for header and footer."""

from django.db import models
from django.utils.translation import gettext_lazy as _

from .base import TimeStampedModel


class NavigationLink(TimeStampedModel):
    """
    Header and footer navigation links, managed from admin.

    Supports dropdown children via self-FK (parent).
    Location determines where the link appears in the layout.
    """

    class LocationChoices(models.TextChoices):
        HEADER = "header", _("Header")
        FOOTER_PRODUCT = "footer_product", _("Footer — Urun")
        FOOTER_SOLUTIONS = "footer_solutions", _("Footer — Cozumler")
        FOOTER_COMPANY = "footer_company", _("Footer — Sirket")
        FOOTER_SUPPORT = "footer_support", _("Footer — Destek")
        FOOTER_LEGAL = "footer_legal", _("Footer — Yasal")
        FOOTER_RESOURCES = "footer_resources", _("Footer — Kaynaklar")
        FOOTER_INVESTORS = "footer_investors", _("Footer — Yatirimci")

    location = models.CharField(
        _("konum"),
        max_length=30,
        choices=LocationChoices.choices,
    )
    label = models.CharField(_("etiket"), max_length=100)
    url = models.CharField(
        _("URL"),
        max_length=200,
        blank=True,
        help_text=_("Django URL adi (ornek: website:features) veya /tam/yol/"),
    )
    icon = models.CharField(
        _("ikon"), max_length=50, blank=True, help_text=_("Phosphor icon sinifi")
    )
    description = models.CharField(
        _("aciklama"),
        max_length=200,
        blank=True,
        help_text=_("Dropdown aciklama metni"),
    )

    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="children",
        verbose_name=_("ust link"),
        help_text=_("Dropdown ustune bagli alt linkler icin"),
    )

    sort_order = models.PositiveIntegerField(_("siralama"), default=0)
    is_active = models.BooleanField(_("aktif"), default=True)

    class Meta:
        verbose_name = _("Navigasyon Linki")
        verbose_name_plural = _("Navigasyon Linkleri")
        ordering = ["location", "sort_order"]

    def __str__(self):
        prefix = self.get_location_display()
        if self.parent:
            return f"  \u2514\u2500 {self.label} ({prefix})"
        return f"{self.label} ({prefix})"
