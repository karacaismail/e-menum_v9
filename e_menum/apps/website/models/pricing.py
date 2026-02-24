"""Pricing display models — PlanDisplayFeature."""

from django.db import models
from django.utils.translation import gettext_lazy as _

from .base import TimeStampedModel


class PlanDisplayFeature(TimeStampedModel):
    """
    Marketing bullet points displayed on pricing cards.

    These are separate from the technical Feature/PlanFeature models in
    apps.subscriptions — they represent the customer-facing feature labels
    shown on the pricing page cards.
    """

    plan = models.ForeignKey(
        'subscriptions.Plan',
        on_delete=models.CASCADE,
        related_name='display_features',
        verbose_name=_('plan'),
    )
    text = models.CharField(_('metin'), max_length=200)
    is_highlighted = models.BooleanField(_('vurgulu'), default=False, help_text=_('Kalin yazi ile gosterilir'))
    sort_order = models.PositiveIntegerField(_('siralama'), default=0)
    is_active = models.BooleanField(_('aktif'), default=True)

    class Meta:
        verbose_name = _('Plan Gosterim Ozelligi')
        verbose_name_plural = _('Plan Gosterim Ozellikleri')
        ordering = ['plan', 'sort_order']

    def __str__(self):
        return f"{self.plan.name} — {self.text[:50]}"
