"""
Model translation options for Subscriptions app models.

Uses django-modeltranslation to create per-language database columns
for all translatable text fields. Supported languages: TR, EN, AR, RU, DE.

Only platform-defined content models are registered (Plan, Feature).
Subscription/Invoice fields are operational data, not translated.
"""

from modeltranslation.translator import translator, TranslationOptions

from .models import Feature, Plan


# =============================================================================
# Plan
# =============================================================================

class PlanTranslationOptions(TranslationOptions):
    fields = (
        'name',
        'description',
        'short_description',
        'highlight_text',
    )


# =============================================================================
# Feature
# =============================================================================

class FeatureTranslationOptions(TranslationOptions):
    fields = (
        'name',
        'description',
    )


# =============================================================================
# REGISTER ALL
# =============================================================================

translator.register(Plan, PlanTranslationOptions)
translator.register(Feature, FeatureTranslationOptions)
