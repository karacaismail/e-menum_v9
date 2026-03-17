"""
Model translation options for SEO models.

Uses django-modeltranslation to create per-language database columns
for all translatable text fields. Supported languages: TR, EN, AR, FA, UK.
"""

from modeltranslation.translator import translator, TranslationOptions

from .models import PSEOTemplate


class PSEOTemplateTranslationOptions(TranslationOptions):
    fields = ("name",)


translator.register(PSEOTemplate, PSEOTemplateTranslationOptions)
