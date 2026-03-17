"""
Model translation options for subscription models.

Uses django-modeltranslation to create per-language database columns
for all translatable text fields. Supported languages: TR, EN, AR, FA, UK.
"""

from modeltranslation.translator import translator, TranslationOptions

from .models import Feature, Plan


class PlanTranslationOptions(TranslationOptions):
    fields = ("name", "description")


class FeatureTranslationOptions(TranslationOptions):
    fields = ("name", "description")


translator.register(Plan, PlanTranslationOptions)
translator.register(Feature, FeatureTranslationOptions)
