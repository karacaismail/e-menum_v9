"""
Model translation options for orders models.

Uses django-modeltranslation to create per-language database columns
for all translatable text fields. Supported languages: TR, EN, AR, FA, UK.
"""

from modeltranslation.translator import translator, TranslationOptions

from .models import QRCode, Table, Zone


class ZoneTranslationOptions(TranslationOptions):
    fields = ("name", "description")


class TableTranslationOptions(TranslationOptions):
    fields = ("name",)


class QRCodeTranslationOptions(TranslationOptions):
    fields = ("name", "description")


translator.register(Zone, ZoneTranslationOptions)
translator.register(Table, TableTranslationOptions)
translator.register(QRCode, QRCodeTranslationOptions)
