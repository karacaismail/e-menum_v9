"""
Django Admin configuration for the Orders application.

This module defines admin interfaces for order models:
- Zone
- Table
- QRCode
- QRScan
- Order
- OrderItem
- ServiceRequest

All admin classes implement multi-tenant filtering where applicable.
"""

from django.contrib import admin

# Note: Admin classes will be registered as models are created
# Example registration pattern:
#
# from apps.orders.models import Zone, Table, QRCode, Order, OrderItem, ServiceRequest
#
# @admin.register(Zone)
# class ZoneAdmin(admin.ModelAdmin):
#     """Admin interface for Zone management."""
#
#     list_display = ['name', 'organization', 'is_active', 'sort_order', 'created_at']
#     list_filter = ['is_active', 'organization', 'created_at']
#     search_fields = ['name', 'description', 'organization__name']
#     readonly_fields = ['id', 'created_at', 'updated_at']
#     ordering = ['organization', 'sort_order']
#
#     def get_queryset(self, request):
#         """Filter out soft-deleted zones."""
#         qs = super().get_queryset(request)
#         return qs.filter(deleted_at__isnull=True)
#
#
# @admin.register(Table)
# class TableAdmin(admin.ModelAdmin):
#     """Admin interface for Table management."""
#
#     list_display = ['name', 'zone', 'status', 'capacity', 'is_active', 'created_at']
#     list_filter = ['status', 'is_active', 'zone', 'created_at']
#     search_fields = ['name', 'code', 'zone__name']
#     readonly_fields = ['id', 'created_at', 'updated_at']
#     ordering = ['zone', 'sort_order']
#
#     def get_queryset(self, request):
#         """Filter out soft-deleted tables."""
#         qs = super().get_queryset(request)
#         return qs.filter(deleted_at__isnull=True)
#
#
# @admin.register(QRCode)
# class QRCodeAdmin(admin.ModelAdmin):
#     """Admin interface for QRCode management."""
#
#     list_display = ['code', 'qr_type', 'organization', 'table', 'is_active', 'created_at']
#     list_filter = ['qr_type', 'is_active', 'organization', 'created_at']
#     search_fields = ['code', 'organization__name', 'table__name']
#     readonly_fields = ['id', 'code', 'created_at', 'updated_at']
#     ordering = ['-created_at']
#
#     def get_queryset(self, request):
#         """Filter out soft-deleted QR codes."""
#         qs = super().get_queryset(request)
#         return qs.filter(deleted_at__isnull=True)
#
#
# @admin.register(Order)
# class OrderAdmin(admin.ModelAdmin):
#     """Admin interface for Order management."""
#
#     list_display = ['order_number', 'organization', 'status', 'order_type', 'total', 'created_at']
#     list_filter = ['status', 'order_type', 'organization', 'created_at']
#     search_fields = ['order_number', 'organization__name', 'customer__name']
#     readonly_fields = ['id', 'order_number', 'created_at', 'updated_at']
#     ordering = ['-created_at']
#
#     fieldsets = (
#         (None, {
#             'fields': ('id', 'order_number', 'organization', 'status', 'order_type')
#         }),
#         ('Customer & Table', {
#             'fields': ('customer', 'table', 'guest_name', 'guest_phone')
#         }),
#         ('Pricing', {
#             'fields': ('subtotal', 'tax_amount', 'discount_amount', 'total', 'currency')
#         }),
#         ('Notes', {
#             'fields': ('customer_notes', 'internal_notes'),
#             'classes': ('collapse',)
#         }),
#         ('Timestamps', {
#             'fields': ('created_at', 'updated_at', 'confirmed_at', 'completed_at', 'cancelled_at'),
#             'classes': ('collapse',)
#         }),
#     )
#
#     def get_queryset(self, request):
#         """Filter out soft-deleted orders."""
#         qs = super().get_queryset(request)
#         return qs.filter(deleted_at__isnull=True)
#
#
# @admin.register(OrderItem)
# class OrderItemAdmin(admin.ModelAdmin):
#     """Admin interface for OrderItem management."""
#
#     list_display = ['order', 'product', 'variant', 'quantity', 'unit_price', 'total', 'status']
#     list_filter = ['status', 'created_at']
#     search_fields = ['order__order_number', 'product__name']
#     readonly_fields = ['id', 'created_at', 'updated_at']
#     ordering = ['order', 'created_at']
#
#
# @admin.register(ServiceRequest)
# class ServiceRequestAdmin(admin.ModelAdmin):
#     """Admin interface for ServiceRequest management."""
#
#     list_display = ['table', 'request_type', 'status', 'created_at', 'responded_at']
#     list_filter = ['request_type', 'status', 'created_at']
#     search_fields = ['table__name', 'notes']
#     readonly_fields = ['id', 'created_at', 'updated_at']
#     ordering = ['-created_at']
