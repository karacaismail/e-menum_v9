"""
Django Admin configuration for the Subscriptions application.

This module defines admin interfaces for subscription models:
- Plan
- PlanFeature
- Subscription
- Invoice

All admin classes implement multi-tenant filtering where applicable.
"""

from django.contrib import admin

# Note: Admin classes will be registered as models are created
# Example registration pattern:
#
# from apps.subscriptions.models import Plan, Subscription, Invoice
#
# @admin.register(Plan)
# class PlanAdmin(admin.ModelAdmin):
#     """Admin interface for Plan management."""
#
#     list_display = ['name', 'tier', 'price_monthly', 'price_yearly', 'is_active', 'sort_order']
#     list_filter = ['tier', 'is_active']
#     search_fields = ['name', 'description']
#     readonly_fields = ['id', 'created_at', 'updated_at']
#     ordering = ['sort_order', 'name']
#
#     fieldsets = (
#         (None, {
#             'fields': ('id', 'name', 'tier', 'description')
#         }),
#         ('Pricing', {
#             'fields': ('price_monthly', 'price_yearly', 'currency')
#         }),
#         ('Configuration', {
#             'fields': ('is_active', 'is_default', 'sort_order')
#         }),
#         ('Timestamps', {
#             'fields': ('created_at', 'updated_at'),
#             'classes': ('collapse',)
#         }),
#     )
#
#
# @admin.register(Subscription)
# class SubscriptionAdmin(admin.ModelAdmin):
#     """Admin interface for Subscription management."""
#
#     list_display = ['organization', 'plan', 'status', 'current_period_start', 'current_period_end']
#     list_filter = ['status', 'plan']
#     search_fields = ['organization__name', 'organization__slug']
#     readonly_fields = ['id', 'created_at', 'updated_at']
#     ordering = ['-created_at']
#
#     fieldsets = (
#         (None, {
#             'fields': ('id', 'organization', 'plan', 'status')
#         }),
#         ('Billing Period', {
#             'fields': ('billing_period', 'current_period_start', 'current_period_end')
#         }),
#         ('Trial', {
#             'fields': ('trial_start', 'trial_end'),
#             'classes': ('collapse',)
#         }),
#         ('Cancellation', {
#             'fields': ('cancelled_at', 'cancel_reason'),
#             'classes': ('collapse',)
#         }),
#         ('Timestamps', {
#             'fields': ('created_at', 'updated_at', 'deleted_at'),
#             'classes': ('collapse',)
#         }),
#     )
#
#     def get_queryset(self, request):
#         """Filter out soft-deleted subscriptions."""
#         qs = super().get_queryset(request)
#         return qs.filter(deleted_at__isnull=True)
#
#
# @admin.register(Invoice)
# class InvoiceAdmin(admin.ModelAdmin):
#     """Admin interface for Invoice management."""
#
#     list_display = ['invoice_number', 'subscription', 'status', 'amount', 'due_date', 'paid_at']
#     list_filter = ['status', 'created_at']
#     search_fields = ['invoice_number', 'subscription__organization__name']
#     readonly_fields = ['id', 'created_at', 'updated_at']
#     ordering = ['-created_at']
#
#     fieldsets = (
#         (None, {
#             'fields': ('id', 'invoice_number', 'subscription', 'status')
#         }),
#         ('Amounts', {
#             'fields': ('subtotal', 'tax_amount', 'discount_amount', 'amount', 'currency')
#         }),
#         ('Dates', {
#             'fields': ('period_start', 'period_end', 'due_date', 'paid_at')
#         }),
#         ('Payment', {
#             'fields': ('payment_method', 'payment_reference'),
#             'classes': ('collapse',)
#         }),
#         ('Timestamps', {
#             'fields': ('created_at', 'updated_at'),
#             'classes': ('collapse',)
#         }),
#     )
