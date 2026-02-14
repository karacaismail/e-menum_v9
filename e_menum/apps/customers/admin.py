"""
Django Admin configuration for the Customers application.

This module defines admin interfaces for customer models:
- Customer
- CustomerVisit
- Feedback
- LoyaltyPoint

All admin classes implement multi-tenant filtering where applicable.
"""

from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from apps.customers.models import Customer, CustomerVisit, Feedback, LoyaltyPoint


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    """Admin interface for Customer management."""

    list_display = [
        'display_name_column', 'organization', 'email', 'phone',
        'total_orders', 'total_spent', 'loyalty_points_balance',
        'last_visit_at', 'source', 'created_at'
    ]
    list_filter = [
        'source', 'marketing_consent', 'organization',
        'created_at', 'last_visit_at'
    ]
    search_fields = ['name', 'email', 'phone', 'organization__name']
    readonly_fields = [
        'id', 'total_orders', 'total_spent', 'loyalty_points_balance',
        'first_visit_at', 'last_visit_at', 'created_at', 'updated_at'
    ]
    ordering = ['-created_at']

    fieldsets = (
        (None, {
            'fields': ('id', 'organization', 'name', 'email', 'phone', 'avatar')
        }),
        (_('Preferences'), {
            'fields': ('language_preference', 'source', 'settings')
        }),
        (_('Loyalty & Stats'), {
            'fields': (
                'total_orders', 'total_spent', 'loyalty_points_balance',
                'first_visit_at', 'last_visit_at'
            )
        }),
        (_('Marketing'), {
            'fields': ('marketing_consent', 'marketing_consent_at')
        }),
        (_('Notes'), {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at', 'deleted_at'),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        """Filter out soft-deleted customers."""
        qs = super().get_queryset(request)
        return qs.filter(deleted_at__isnull=True)

    @admin.display(description=_('Customer'))
    def display_name_column(self, obj):
        """Display the customer's name or email."""
        return obj.display_name


@admin.register(CustomerVisit)
class CustomerVisitAdmin(admin.ModelAdmin):
    """Admin interface for CustomerVisit management."""

    list_display = [
        'customer', 'organization', 'branch', 'visited_at',
        'source', 'duration_minutes', 'created_at'
    ]
    list_filter = ['source', 'organization', 'branch', 'visited_at']
    search_fields = [
        'customer__name', 'customer__email',
        'organization__name', 'branch__name'
    ]
    readonly_fields = ['id', 'created_at', 'updated_at']
    ordering = ['-visited_at']
    date_hierarchy = 'visited_at'

    fieldsets = (
        (None, {
            'fields': ('id', 'organization', 'customer', 'branch')
        }),
        (_('Visit Details'), {
            'fields': ('visited_at', 'source', 'table_id', 'order_id', 'duration_minutes')
        }),
        (_('Device Information'), {
            'fields': ('device_info', 'ip_address', 'user_agent'),
            'classes': ('collapse',)
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    """Admin interface for Feedback management."""

    list_display = [
        'customer_display', 'organization', 'feedback_type',
        'rating_display', 'status', 'is_public', 'created_at'
    ]
    list_filter = [
        'status', 'feedback_type', 'rating', 'is_public',
        'organization', 'created_at'
    ]
    search_fields = [
        'customer__name', 'customer__email', 'comment',
        'staff_response', 'organization__name'
    ]
    readonly_fields = [
        'id', 'created_at', 'updated_at', 'responded_at'
    ]
    ordering = ['-created_at']
    date_hierarchy = 'created_at'

    fieldsets = (
        (None, {
            'fields': ('id', 'organization', 'customer', 'order_id')
        }),
        (_('Feedback'), {
            'fields': ('feedback_type', 'rating', 'comment', 'is_public')
        }),
        (_('Status & Response'), {
            'fields': (
                'status', 'staff_response',
                'responded_by_id', 'responded_at'
            )
        }),
        (_('Metadata'), {
            'fields': ('metadata',),
            'classes': ('collapse',)
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at', 'deleted_at'),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        """Filter out soft-deleted feedback."""
        qs = super().get_queryset(request)
        return qs.filter(deleted_at__isnull=True)

    @admin.display(description=_('Customer'))
    def customer_display(self, obj):
        """Display the customer name or 'Anonymous'."""
        if obj.customer:
            return obj.customer.display_name
        return _('Anonymous')

    @admin.display(description=_('Rating'))
    def rating_display(self, obj):
        """Display rating as stars."""
        filled = '★' * obj.rating
        empty = '☆' * (5 - obj.rating)
        color = '#22C55E' if obj.rating >= 4 else '#EAB308' if obj.rating == 3 else '#EF4444'
        return format_html(
            '<span style="color: {};">{}{}</span>',
            color, filled, empty
        )


@admin.register(LoyaltyPoint)
class LoyaltyPointAdmin(admin.ModelAdmin):
    """Admin interface for LoyaltyPoint management."""

    list_display = [
        'customer', 'organization', 'transaction_type',
        'points_display', 'balance_after', 'description',
        'expires_at', 'created_at'
    ]
    list_filter = [
        'transaction_type', 'organization', 'created_at', 'expires_at'
    ]
    search_fields = [
        'customer__name', 'customer__email',
        'description', 'organization__name'
    ]
    readonly_fields = ['id', 'created_at', 'updated_at']
    ordering = ['-created_at']
    date_hierarchy = 'created_at'

    fieldsets = (
        (None, {
            'fields': ('id', 'organization', 'customer')
        }),
        (_('Transaction'), {
            'fields': (
                'transaction_type', 'points', 'balance_after',
                'order_id', 'description'
            )
        }),
        (_('Expiration'), {
            'fields': ('expires_at',)
        }),
        (_('Metadata'), {
            'fields': ('metadata',),
            'classes': ('collapse',)
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    @admin.display(description=_('Points'))
    def points_display(self, obj):
        """Display points with color coding."""
        if obj.points > 0:
            return format_html(
                '<span style="color: #22C55E; font-weight: bold;">+{}</span>',
                obj.points
            )
        else:
            return format_html(
                '<span style="color: #EF4444; font-weight: bold;">{}</span>',
                obj.points
            )
