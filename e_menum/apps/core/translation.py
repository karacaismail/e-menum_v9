"""
Model translation options for core models.

Uses django-modeltranslation to create per-language database columns
for all translatable text fields. Supported languages: TR, EN, AR, FA, UK.
"""

from modeltranslation.translator import translator, TranslationOptions

from .models import Role


class RoleTranslationOptions(TranslationOptions):
    fields = ("display_name", "description")


translator.register(Role, RoleTranslationOptions)
