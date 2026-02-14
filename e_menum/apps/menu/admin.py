"""
Django Admin configuration for the Menu application.

This module defines admin interfaces for menu models:
- Menu
- Category
- Product
- ProductVariant
- ProductModifier
- Allergen
- Theme

All admin classes implement multi-tenant filtering where applicable.
"""

from django.contrib import admin

# Note: Admin classes will be registered as models are created
# Example registration pattern:
#
# from apps.menu.models import Menu, Category, Product, Allergen, Theme
#
# @admin.register(Menu)
# class MenuAdmin(admin.ModelAdmin):
#     """Admin interface for Menu management."""
#
#     list_display = ['name', 'organization', 'status', 'is_default', 'created_at']
#     list_filter = ['status', 'is_default', 'organization', 'created_at']
#     search_fields = ['name', 'description', 'organization__name']
#     readonly_fields = ['id', 'created_at', 'updated_at']
#     ordering = ['-created_at']
#
#     fieldsets = (
#         (None, {
#             'fields': ('id', 'organization', 'name', 'slug', 'description')
#         }),
#         ('Settings', {
#             'fields': ('status', 'is_default', 'settings')
#         }),
#         ('Timestamps', {
#             'fields': ('created_at', 'updated_at', 'deleted_at'),
#             'classes': ('collapse',)
#         }),
#     )
#
#     def get_queryset(self, request):
#         """Filter out soft-deleted menus."""
#         qs = super().get_queryset(request)
#         return qs.filter(deleted_at__isnull=True)
#
#
# @admin.register(Category)
# class CategoryAdmin(admin.ModelAdmin):
#     """Admin interface for Category management."""
#
#     list_display = ['name', 'menu', 'sort_order', 'is_visible', 'created_at']
#     list_filter = ['is_visible', 'menu', 'created_at']
#     search_fields = ['name', 'description', 'menu__name']
#     readonly_fields = ['id', 'created_at', 'updated_at']
#     ordering = ['menu', 'sort_order']
#
#     def get_queryset(self, request):
#         """Filter out soft-deleted categories."""
#         qs = super().get_queryset(request)
#         return qs.filter(deleted_at__isnull=True)
#
#
# @admin.register(Product)
# class ProductAdmin(admin.ModelAdmin):
#     """Admin interface for Product management."""
#
#     list_display = ['name', 'category', 'base_price', 'is_available', 'created_at']
#     list_filter = ['is_available', 'is_featured', 'category', 'created_at']
#     search_fields = ['name', 'description', 'category__name']
#     readonly_fields = ['id', 'created_at', 'updated_at']
#     ordering = ['category', 'sort_order']
#
#     def get_queryset(self, request):
#         """Filter out soft-deleted products."""
#         qs = super().get_queryset(request)
#         return qs.filter(deleted_at__isnull=True)
#
#
# @admin.register(Allergen)
# class AllergenAdmin(admin.ModelAdmin):
#     """Admin interface for Allergen management."""
#
#     list_display = ['name', 'code', 'icon', 'is_active']
#     list_filter = ['is_active']
#     search_fields = ['name', 'code']
#     ordering = ['name']
#
#
# @admin.register(Theme)
# class ThemeAdmin(admin.ModelAdmin):
#     """Admin interface for Theme management."""
#
#     list_display = ['name', 'organization', 'is_default', 'created_at']
#     list_filter = ['is_default', 'organization', 'created_at']
#     search_fields = ['name', 'organization__name']
#     readonly_fields = ['id', 'created_at', 'updated_at']
#     ordering = ['-created_at']
#
#     def get_queryset(self, request):
#         """Filter out soft-deleted themes."""
#         qs = super().get_queryset(request)
#         return qs.filter(deleted_at__isnull=True)
