"""
Django Admin configuration for the Core application.

This module defines admin interfaces for core models:
- Organization
- User
- Role
- Permission
- Session
- Branch
- AuditLog

All admin classes implement multi-tenant filtering where applicable.
"""

from django.contrib import admin

# Note: Admin classes will be registered as models are created
# Example registration pattern:
#
# from apps.core.models import Organization, User, Role, Permission
#
# @admin.register(Organization)
# class OrganizationAdmin(admin.ModelAdmin):
#     """Admin interface for Organization (tenant) management."""
#
#     list_display = ['name', 'slug', 'email', 'status', 'created_at']
#     list_filter = ['status', 'created_at']
#     search_fields = ['name', 'slug', 'email']
#     readonly_fields = ['id', 'created_at', 'updated_at']
#     ordering = ['-created_at']
#
#     fieldsets = (
#         (None, {
#             'fields': ('id', 'name', 'slug', 'email', 'phone')
#         }),
#         ('Settings', {
#             'fields': ('logo', 'settings', 'status')
#         }),
#         ('Subscription', {
#             'fields': ('plan', 'trial_ends_at')
#         }),
#         ('Timestamps', {
#             'fields': ('created_at', 'updated_at', 'deleted_at'),
#             'classes': ('collapse',)
#         }),
#     )
#
#     def get_queryset(self, request):
#         """Filter out soft-deleted organizations."""
#         qs = super().get_queryset(request)
#         return qs.filter(deleted_at__isnull=True)
#
#
# @admin.register(User)
# class UserAdmin(admin.ModelAdmin):
#     """Admin interface for User management."""
#
#     list_display = ['email', 'first_name', 'last_name', 'organization', 'status', 'is_staff']
#     list_filter = ['status', 'is_staff', 'is_superuser', 'organization']
#     search_fields = ['email', 'first_name', 'last_name']
#     readonly_fields = ['id', 'created_at', 'updated_at', 'last_login_at']
#     ordering = ['-created_at']
#
#     fieldsets = (
#         (None, {
#             'fields': ('id', 'email', 'password')
#         }),
#         ('Personal Info', {
#             'fields': ('first_name', 'last_name', 'phone', 'avatar')
#         }),
#         ('Organization', {
#             'fields': ('organization', 'status')
#         }),
#         ('Permissions', {
#             'fields': ('is_staff', 'is_superuser', 'groups', 'user_permissions'),
#             'classes': ('collapse',)
#         }),
#         ('Timestamps', {
#             'fields': ('created_at', 'updated_at', 'email_verified_at', 'last_login_at', 'deleted_at'),
#             'classes': ('collapse',)
#         }),
#     )
#
#     def get_queryset(self, request):
#         """Filter out soft-deleted users."""
#         qs = super().get_queryset(request)
#         return qs.filter(deleted_at__isnull=True)
