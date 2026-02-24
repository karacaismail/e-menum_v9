"""Feature category and bullet models for the /ozellikler/ page."""

from django.db import models
from django.utils.translation import gettext_lazy as _

from .base import TimeStampedModel


# =============================================================================
# FEATURE CATEGORY + FEATURE BULLET
# =============================================================================

class FeatureCategory(TimeStampedModel):
    """Feature showcase category for the /ozellikler/ page."""

    title = models.CharField(_('baslik'), max_length=200)
    description = models.TextField(_('aciklama'), blank=True)
    badge_text = models.CharField(_('badge metni'), max_length=50, blank=True)
    badge_color = models.CharField(_('badge rengi'), max_length=30, default='primary')
    icon = models.CharField(_('ikon'), max_length=50, blank=True)
    image_alt = models.CharField(_('gorsel alt metni'), max_length=200, blank=True)
    layout_reversed = models.BooleanField(_('ters duzenleme'), default=False)
    sort_order = models.PositiveIntegerField(_('siralama'), default=0)
    is_active = models.BooleanField(_('aktif'), default=True)

    class Meta:
        verbose_name = _('Ozellik Kategorisi')
        verbose_name_plural = _('Ozellik Kategorileri')
        ordering = ['sort_order']

    def __str__(self):
        return self.title


class FeatureBullet(TimeStampedModel):
    """Bullet point within a feature category."""

    category = models.ForeignKey(
        FeatureCategory,
        on_delete=models.CASCADE,
        related_name='bullets',
        verbose_name=_('kategori'),
    )
    text = models.CharField(_('metin'), max_length=300)
    sort_order = models.PositiveIntegerField(_('siralama'), default=0)
    is_active = models.BooleanField(_('aktif'), default=True)

    class Meta:
        verbose_name = _('Ozellik Maddesi')
        verbose_name_plural = _('Ozellik Maddeleri')
        ordering = ['sort_order']

    def __str__(self):
        return f"{self.category.title} — {self.text[:50]}"
