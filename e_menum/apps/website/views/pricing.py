"""Pricing page view."""

import logging
from collections import OrderedDict

from django.utils.translation import gettext_lazy as _
from django.views.generic import TemplateView

from .mixins import CmsContextMixin
from ..models import FAQ

logger = logging.getLogger(__name__)


def _format_feature_value(value, is_enabled):
    """Convert PlanFeature JSON value to human-readable display string."""
    if not value or not isinstance(value, dict):
        return ""

    # LIMIT type: {'limit': 10} or {'limit': -1} (unlimited)
    if "limit" in value:
        limit = value["limit"]
        if limit == -1:
            return str(_("Sinirsiz"))
        return str(limit)

    # USAGE type: {'credits': 100, 'reset_period': 'monthly'}
    if "credits" in value:
        credits_val = value["credits"]
        if credits_val == -1:
            return str(_("Sinirsiz"))
        # Include period if available (e.g., "250 / ay")
        period = value.get("reset_period", "")
        period_labels = {
            "monthly": str(_("/ ay")),
            "weekly": str(_("/ hafta")),
            "daily": str(_("/ gun")),
        }
        suffix = period_labels.get(period, "")
        if suffix:
            return f"{credits_val} {suffix}"
        return str(credits_val)

    # TEXT type: {'text': 'E-posta + Chat'}
    if "text" in value:
        return str(value["text"])

    # BOOLEAN type: {'enabled': true/false}
    if "enabled" in value:
        return ""  # Handled by is_enabled check/cross icons

    return ""


class PricingView(CmsContextMixin, TemplateView):
    """Fiyatlandirma sayfasi — pricing plans, feature matrix, calculator."""

    template_name = "website/pricing.html"
    page_slug = "pricing"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Plans with display features
        try:
            from apps.subscriptions.models import Plan, Feature, PlanFeature

            plans_qs = Plan.objects.filter(
                    is_active=True,
                    is_public=True,
                    deleted_at__isnull=True,
                ).order_by("sort_order")

            plans = list(plans_qs.prefetch_related("display_features"))
            context["plans"] = plans

            # Build comparison matrix grouped by category
            features = Feature.objects.filter(
                is_active=True,
                deleted_at__isnull=True,
            ).order_by("category", "sort_order")

            # Pre-fetch all PlanFeatures at once (avoid N+1)
            plan_ids = [p.id for p in plans]
            feature_ids = [f.id for f in features]
            plan_features = PlanFeature.objects.filter(
                plan_id__in=plan_ids,
                feature_id__in=feature_ids,
            ).select_related("feature")

            # Build lookup dict: (plan_id, feature_id) -> PlanFeature
            pf_lookup = {}
            for pf in plan_features:
                pf_lookup[(str(pf.plan_id), str(pf.feature_id))] = pf

            # Group features by category
            grouped_matrix = OrderedDict()
            for feature in features:
                cat = feature.category
                cat_display = feature.get_category_display()

                if cat not in grouped_matrix:
                    grouped_matrix[cat] = {
                        "category_key": cat,
                        "category_display": cat_display,
                        "rows": [],
                    }

                row = {
                    "feature": feature,
                    "values": [],
                }
                for plan in plans:
                    pf = pf_lookup.get((str(plan.id), str(feature.id)))
                    if pf:
                        row["values"].append(
                            {
                                "is_enabled": pf.is_enabled,
                                "value": pf.value,
                                "display_value": _format_feature_value(
                                    pf.value,
                                    pf.is_enabled,
                                ),
                            }
                        )
                    else:
                        row["values"].append(
                            {
                                "is_enabled": False,
                                "value": None,
                                "display_value": "",
                            }
                        )
                grouped_matrix[cat]["rows"].append(row)

            context["comparison_groups"] = list(grouped_matrix.values())

            # Also provide flat matrix for backward compatibility
            flat_matrix = []
            for group in grouped_matrix.values():
                flat_matrix.extend(group["rows"])
            context["comparison_matrix"] = flat_matrix

        except Exception:
            logger.exception("Failed to load pricing data")
            context["plans"] = []
            context["comparison_matrix"] = []
            context["comparison_groups"] = []

        # FAQs for pricing page
        context["faqs"] = FAQ.objects.filter(
            is_active=True,
            page__in=["pricing", "both"],
        ).order_by("sort_order")

        return context
