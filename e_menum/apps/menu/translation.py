"""
Model translation options for Menu app models.

Uses django-modeltranslation to create per-language database columns
for all translatable text fields. Supported languages: TR, EN, AR, UK, DE.

Each registered model gets _tr, _en, _ar, _uk, _de suffixed columns.
The admin uses TabbedTranslationAdmin to show language tabs.
"""

from modeltranslation.translator import translator, TranslationOptions

from .models import (
    Allergen,
    Category,
    Menu,
    NutritionInfo,
    Product,
    ProductModifier,
    ProductVariant,
    Theme,
)


# =============================================================================
# Theme
# =============================================================================

class ThemeTranslationOptions(TranslationOptions):
    fields = (
        'name',
        'description',
    )


# =============================================================================
# Menu
# =============================================================================

class MenuTranslationOptions(TranslationOptions):
    fields = (
        'name',
        'description',
    )


# =============================================================================
# Category
# =============================================================================

class CategoryTranslationOptions(TranslationOptions):
    fields = (
        'name',
        'description',
    )


# =============================================================================
# Product
# =============================================================================

class ProductTranslationOptions(TranslationOptions):
    fields = (
        'name',
        'description',
        'short_description',
    )


# =============================================================================
# ProductVariant
# =============================================================================

class ProductVariantTranslationOptions(TranslationOptions):
    fields = (
        'name',
    )


# =============================================================================
# ProductModifier
# =============================================================================

class ProductModifierTranslationOptions(TranslationOptions):
    fields = (
        'name',
    )


# =============================================================================
# Allergen
# =============================================================================

class AllergenTranslationOptions(TranslationOptions):
    fields = (
        'name',
        'description',
    )


# =============================================================================
# NutritionInfo
# =============================================================================

class NutritionInfoTranslationOptions(TranslationOptions):
    fields = (
        'serving_size',
    )


# =============================================================================
# REGISTER ALL
# =============================================================================

translator.register(Theme, ThemeTranslationOptions)
translator.register(Menu, MenuTranslationOptions)
translator.register(Category, CategoryTranslationOptions)
translator.register(Product, ProductTranslationOptions)
translator.register(ProductVariant, ProductVariantTranslationOptions)
translator.register(ProductModifier, ProductModifierTranslationOptions)
translator.register(Allergen, AllergenTranslationOptions)
translator.register(NutritionInfo, NutritionInfoTranslationOptions)
