"""
Model translation options for campaign models.

Uses django-modeltranslation to create per-language database columns
for all translatable text fields. Supported languages: TR, EN, AR, FA, UK.
"""

from modeltranslation.translator import translator, TranslationOptions

from .models import Campaign


class CampaignTranslationOptions(TranslationOptions):
    fields = ("name", "description")


translator.register(Campaign, CampaignTranslationOptions)
