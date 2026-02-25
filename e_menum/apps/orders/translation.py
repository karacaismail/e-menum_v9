"""
Model translation options for Orders app models.

Uses django-modeltranslation to create per-language database columns
for platform-defined display fields. Supported languages: TR, EN, AR, UK, DE.

Only Zone, Table name, and QRCode name/description are translated.
Order notes, cancel reasons, and user-entered data are NOT translated.
"""

from modeltranslation.translator import translator, TranslationOptions

from .models import QRCode, Zone


# =============================================================================
# Zone
# =============================================================================

class ZoneTranslationOptions(TranslationOptions):
    fields = (
        'name',
        'description',
    )


# =============================================================================
# QRCode
# =============================================================================

class QRCodeTranslationOptions(TranslationOptions):
    fields = (
        'name',
        'description',
    )


# =============================================================================
# REGISTER ALL
# =============================================================================

translator.register(Zone, ZoneTranslationOptions)
translator.register(QRCode, QRCodeTranslationOptions)
