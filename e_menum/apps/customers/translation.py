"""
Model translation options for customer models.

Uses django-modeltranslation to create per-language database columns
for all translatable text fields. Supported languages: TR, EN, AR, FA, UK.
"""

from modeltranslation.translator import translator, TranslationOptions

from .models import Feedback


class FeedbackTranslationOptions(TranslationOptions):
    fields = ("comment", "staff_response")


translator.register(Feedback, FeedbackTranslationOptions)
