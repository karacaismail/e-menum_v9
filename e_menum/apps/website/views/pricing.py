"""Pricing page view."""
import logging

from django.utils.translation import gettext_lazy as _
from django.views.generic import TemplateView

from .mixins import CmsContextMixin
from ..models import FAQ

logger = logging.getLogger(__name__)


def _format_feature_value(value, is_enabled):
    """Convert PlanFeature JSON value to human-readable display string."""
    if not value or not isinstance(value, dict):
        return ''

    # LIMIT type: {'limit': 10} or {'limit': -1} (unlimited)
    if 'limit' in value:
        limit = value['limit']
        if limit == -1:
            return str(_('Sinirsiz'))
        return str(limit)

    # USAGE type: {'credits': 100, 'reset_period': 'monthly'}
    if 'credits' in value:
        credits = value['credits']
        if credits == -1:
            return str(_('Sinirsiz'))
        return str(credits)

    # BOOLEAN type: {'enabled': true/false}
    if 'enabled' in value:
        return ''  # Handled by is_enabled check/cross icons

    return ''


class PricingView(CmsContextMixin, TemplateView):
    """Fiyatlandirma sayfasi — pricing plans, feature matrix, calculator."""
    template_name = 'website/pricing.html'
    page_slug = 'pricing'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Plans with display features
        try:
            from apps.subscriptions.models import Plan, Feature, PlanFeature
            plans = Plan.objects.filter(
                is_active=True, is_public=True, deleted_at__isnull=True,
            ).prefetch_related('display_features').order_by('sort_order')
            context['plans'] = plans

            # Comparison matrix: list of dicts {feature, values: [plan_value, ...]}
            features = Feature.objects.filter(
                is_active=True, deleted_at__isnull=True,
            ).order_by('category', 'sort_order')

            matrix = []
            for feature in features:
                row = {
                    'feature': feature,
                    'values': [],
                }
                for plan in plans:
                    pf = PlanFeature.objects.filter(
                        plan=plan, feature=feature,
                    ).first()
                    if pf:
                        row['values'].append({
                            'is_enabled': pf.is_enabled,
                            'value': pf.value,
                            'display_value': _format_feature_value(
                                pf.value, pf.is_enabled,
                            ),
                        })
                    else:
                        row['values'].append({
                            'is_enabled': False,
                            'value': None,
                            'display_value': '',
                        })
                matrix.append(row)
            context['comparison_matrix'] = matrix
        except Exception:
            context['plans'] = []
            context['comparison_matrix'] = []

        # FAQs for pricing page
        context['faqs'] = FAQ.objects.filter(
            is_active=True, deleted_at__isnull=True,
            page__in=['pricing', 'both'],
        ).order_by('sort_order')

        return context
