"""
Model translation options for inventory models.

Uses django-modeltranslation to create per-language database columns
for all translatable text fields. Supported languages: TR, EN, AR, FA, UK.
"""

from modeltranslation.translator import translator, TranslationOptions

from .models import InventoryItem, Recipe


class InventoryItemTranslationOptions(TranslationOptions):
    fields = ("name",)


class RecipeTranslationOptions(TranslationOptions):
    fields = ("name", "description")


translator.register(InventoryItem, InventoryItemTranslationOptions)
translator.register(Recipe, RecipeTranslationOptions)
