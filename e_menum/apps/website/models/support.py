"""Support — help center categories and articles."""

from django.db import models
from django.utils.translation import gettext_lazy as _

from .base import TimeStampedModel
from apps.seo.models import SEOMixin


# =============================================================================
# HELP CATEGORY
# =============================================================================


class HelpCategory(TimeStampedModel):
    """Help center categories."""

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
        verbose_name = _("Yardim Kategorisi")
        verbose_name_plural = _("Yardim Kategorileri")
        ordering = ["sort_order"]

    def __str__(self):
        return self.name


# =============================================================================
# HELP ARTICLE
# =============================================================================


class HelpArticle(SEOMixin, TimeStampedModel):
    """Help center articles / knowledge base."""

    category = models.ForeignKey(
        HelpCategory,
        on_delete=models.CASCADE,
        related_name="articles",
        verbose_name=_("kategori"),
    )
    title = models.CharField(_("baslik"), max_length=300)
    slug = models.SlugField(_("slug"), max_length=300, unique=True)
    content = models.TextField(_("icerik"), help_text=_("HTML icerik"))
    is_featured = models.BooleanField(_("one cikan"), default=False)
    view_count = models.PositiveIntegerField(_("goruntuleme"), default=0)
    helpful_count = models.PositiveIntegerField(_("yardimci oldu"), default=0)
    not_helpful_count = models.PositiveIntegerField(_("yardimci olmadi"), default=0)
    sort_order = models.PositiveIntegerField(_("siralama"), default=0)
    is_active = models.BooleanField(_("aktif"), default=True)

    class Meta:
        verbose_name = _("Yardim Makalesi")
        verbose_name_plural = _("Yardim Makaleleri")
        ordering = ["category", "sort_order"]

    def __str__(self):
        return f"{self.category.name} — {self.title}"
