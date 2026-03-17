"""
Model translation options for menu models.

Uses django-modeltranslation to create per-language database columns
for all translatable text fields. Supported languages: TR, EN, AR, FA, UK.

Each registered model gets _tr, _en, _ar, _fa, _uk suffixed columns.
"""

from modeltranslation.translator import translator, TranslationOptions

from .models import (
    Allergen,
    Category,
    Menu,
    Product,
    ProductModifier,
    ProductVariant,
    Theme,
)


class ThemeTranslationOptions(TranslationOptions):
    fields = ("name", "description")


class MenuTranslationOptions(TranslationOptions):
    fields = ("name", "description")


class CategoryTranslationOptions(TranslationOptions):
    fields = ("name", "description")


class ProductTranslationOptions(TranslationOptions):
    fields = ("name", "description", "short_description")


class ProductVariantTranslationOptions(TranslationOptions):
    fields = ("name",)


class ProductModifierTranslationOptions(TranslationOptions):
    fields = ("name",)


class AllergenTranslationOptions(TranslationOptions):
    fields = ("name", "description")


translator.register(Theme, ThemeTranslationOptions)
translator.register(Menu, MenuTranslationOptions)
translator.register(Category, CategoryTranslationOptions)
translator.register(Product, ProductTranslationOptions)
translator.register(ProductVariant, ProductVariantTranslationOptions)
translator.register(ProductModifier, ProductModifierTranslationOptions)
translator.register(Allergen, AllergenTranslationOptions)
