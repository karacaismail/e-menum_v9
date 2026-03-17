"""
Model translation options for notification models.

Uses django-modeltranslation to create per-language database columns
for all translatable text fields. Supported languages: TR, EN, AR, FA, UK.
"""

from modeltranslation.translator import translator, TranslationOptions

from .models import Notification


class NotificationTranslationOptions(TranslationOptions):
    fields = ("title", "message")


translator.register(Notification, NotificationTranslationOptions)
