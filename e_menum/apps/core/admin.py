"""
Django Admin configuration for the Core application.

This module defines admin interfaces for core models:
- Organization
- User
- Role
- Permission
- Session
- Branch
- UserRole
- RolePermission
- AuditLog

All admin classes implement multi-tenant filtering where applicable.
Soft-deleted records are filtered out by default in all applicable models.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import UserChangeForm, UserCreationForm
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from apps.core.models import (
    AuditLog,
    Branch,
    Organization,
    Permission,
    Role,
    RolePermission,
    Session,
    User,
    UserRole,
)


class SoftDeleteAdminMixin:
    """
    Mixin that filters out soft-deleted records in the admin queryset.

    Add this mixin to any ModelAdmin that manages a model with soft delete.
    """

    def get_queryset(self, request):
        """Filter out soft-deleted records by default."""
        qs = super().get_queryset(request)
        if hasattr(qs.model, 'deleted_at'):
            return qs.filter(deleted_at__isnull=True)
        return qs


@admin.register(Organization)
class OrganizationAdmin(SoftDeleteAdminMixin, admin.ModelAdmin):
    """
    Admin interface for Organization (tenant) management.

    Provides comprehensive management of tenant organizations including:
    - View/edit organization details
    - Manage subscription status
    - Control organization settings
    - Monitor trial periods

    Note: Soft-deleted organizations are hidden by default.
    """

    list_display = [
        'name',
        'slug',
        'email',
        'status_badge',
        'is_on_trial',
        'created_at',
    ]
    list_filter = ['status', 'created_at', 'updated_at']
    search_fields = ['name', 'slug', 'email', 'phone']
    readonly_fields = ['id', 'created_at', 'updated_at', 'deleted_at']
    ordering = ['-created_at']
    date_hierarchy = 'created_at'
    list_per_page = 25

    fieldsets = (
        (None, {
            'fields': ('id', 'name', 'slug', 'logo'),
            'description': _('Basic organization information')
        }),
        (_('Contact Information'), {
            'fields': ('email', 'phone'),
        }),
        (_('Status & Subscription'), {
            'fields': ('status', 'trial_ends_at'),
            'description': _('Organization lifecycle and subscription status')
        }),
        (_('Settings'), {
            'fields': ('settings',),
            'classes': ('collapse',),
            'description': _('Organization-specific configuration (JSON)')
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at', 'deleted_at'),
            'classes': ('collapse',),
        }),
    )

    def status_badge(self, obj):
        """Display status with color-coded badge."""
        colors = {
            'ACTIVE': '#28a745',
            'SUSPENDED': '#ffc107',
            'DELETED': '#dc3545',
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-size: 11px; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = _('Status')
    status_badge.admin_order_field = 'status'

    def is_on_trial(self, obj):
        """Display trial status as icon."""
        if obj.is_on_trial:
            return format_html(
                '<span style="color: #17a2b8;">&#10003; Trial</span>'
            )
        return format_html('<span style="color: #6c757d;">-</span>')
    is_on_trial.short_description = _('Trial')
    is_on_trial.boolean = True

    actions = ['suspend_organizations', 'activate_organizations']

    @admin.action(description=_('Suspend selected organizations'))
    def suspend_organizations(self, request, queryset):
        """Bulk action to suspend selected organizations."""
        count = queryset.update(status='SUSPENDED')
        self.message_user(
            request,
            _('%(count)d organization(s) have been suspended.') % {'count': count}
        )

    @admin.action(description=_('Activate selected organizations'))
    def activate_organizations(self, request, queryset):
        """Bulk action to activate selected organizations."""
        count = queryset.update(status='ACTIVE')
        self.message_user(
            request,
            _('%(count)d organization(s) have been activated.') % {'count': count}
        )


class CustomUserCreationForm(UserCreationForm):
    """Custom user creation form for admin that uses email as username."""

    class Meta:
        model = User
        fields = ('email', 'first_name', 'last_name')


class CustomUserChangeForm(UserChangeForm):
    """Custom user change form for admin."""

    class Meta:
        model = User
        fields = '__all__'


@admin.register(User)
class UserAdmin(SoftDeleteAdminMixin, BaseUserAdmin):
    """
    Admin interface for User management.

    Extends Django's built-in UserAdmin with customizations for:
    - Email-based authentication (no username)
    - Organization membership
    - Custom status field
    - Soft delete support

    Note: Soft-deleted users are hidden by default.
    """

    form = CustomUserChangeForm
    add_form = CustomUserCreationForm

    list_display = [
        'email',
        'full_name',
        'organization',
        'status_badge',
        'is_staff',
        'is_superuser',
        'created_at',
    ]
    list_filter = [
        'status',
        'is_staff',
        'is_superuser',
        'organization',
        'created_at',
    ]
    search_fields = ['email', 'first_name', 'last_name', 'phone']
    readonly_fields = [
        'id',
        'created_at',
        'updated_at',
        'deleted_at',
        'last_login_at',
        'email_verified_at',
        'last_login',
    ]
    ordering = ['-created_at']
    date_hierarchy = 'created_at'
    list_per_page = 25
    filter_horizontal = ('groups', 'user_permissions')

    # Override BaseUserAdmin fieldsets to use email instead of username
    fieldsets = (
        (None, {
            'fields': ('id', 'email', 'password'),
            'description': _('Credentials')
        }),
        (_('Personal Information'), {
            'fields': ('first_name', 'last_name', 'phone', 'avatar'),
        }),
        (_('Organization'), {
            'fields': ('organization', 'status'),
            'description': _('Tenant membership and account status')
        }),
        (_('Permissions'), {
            'fields': (
                'is_staff',
                'is_superuser',
                'groups',
                'user_permissions',
            ),
            'classes': ('collapse',),
        }),
        (_('Important Dates'), {
            'fields': (
                'email_verified_at',
                'last_login_at',
                'last_login',
                'created_at',
                'updated_at',
                'deleted_at',
            ),
            'classes': ('collapse',),
        }),
    )

    # Fieldsets for adding a new user
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'email',
                'first_name',
                'last_name',
                'password1',
                'password2',
                'organization',
                'status',
                'is_staff',
            ),
        }),
    )

    def full_name(self, obj):
        """Display user's full name."""
        return obj.full_name or obj.email
    full_name.short_description = _('Full Name')
    full_name.admin_order_field = 'first_name'

    def status_badge(self, obj):
        """Display status with color-coded badge."""
        colors = {
            'ACTIVE': '#28a745',
            'INVITED': '#17a2b8',
            'SUSPENDED': '#dc3545',
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-size: 11px; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = _('Status')
    status_badge.admin_order_field = 'status'

    actions = ['suspend_users', 'activate_users', 'verify_email']

    @admin.action(description=_('Suspend selected users'))
    def suspend_users(self, request, queryset):
        """Bulk action to suspend selected users."""
        count = queryset.update(status='SUSPENDED')
        self.message_user(
            request,
            _('%(count)d user(s) have been suspended.') % {'count': count}
        )

    @admin.action(description=_('Activate selected users'))
    def activate_users(self, request, queryset):
        """Bulk action to activate selected users."""
        count = queryset.update(status='ACTIVE')
        self.message_user(
            request,
            _('%(count)d user(s) have been activated.') % {'count': count}
        )

    @admin.action(description=_('Mark email as verified'))
    def verify_email(self, request, queryset):
        """Bulk action to mark email as verified."""
        from django.utils import timezone
        count = queryset.update(email_verified_at=timezone.now())
        self.message_user(
            request,
            _('%(count)d user(s) email verified.') % {'count': count}
        )


@admin.register(Branch)
class BranchAdmin(SoftDeleteAdminMixin, admin.ModelAdmin):
    """Admin interface for Branch (location) management."""

    list_display = [
        'name',
        'organization',
        'city',
        'status_badge',
        'is_main',
        'created_at',
    ]
    list_filter = ['status', 'is_main', 'organization', 'city', 'created_at']
    search_fields = ['name', 'slug', 'address', 'city', 'organization__name']
    readonly_fields = ['id', 'created_at', 'updated_at', 'deleted_at']
    ordering = ['-is_main', 'name']
    list_per_page = 25

    fieldsets = (
        (None, {
            'fields': ('id', 'organization', 'name', 'slug', 'is_main'),
        }),
        (_('Address'), {
            'fields': ('address', 'city', 'district', 'postal_code', 'country'),
        }),
        (_('Contact'), {
            'fields': ('phone', 'email'),
        }),
        (_('Location'), {
            'fields': ('latitude', 'longitude', 'timezone'),
            'classes': ('collapse',),
        }),
        (_('Configuration'), {
            'fields': ('status', 'settings', 'operating_hours'),
            'classes': ('collapse',),
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at', 'deleted_at'),
            'classes': ('collapse',),
        }),
    )

    def status_badge(self, obj):
        """Display status with color-coded badge."""
        colors = {
            'ACTIVE': '#28a745',
            'INACTIVE': '#6c757d',
            'SUSPENDED': '#dc3545',
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-size: 11px; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = _('Status')
    status_badge.admin_order_field = 'status'


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    """Admin interface for Role management."""

    list_display = [
        'display_name',
        'name',
        'scope',
        'organization',
        'is_system',
        'created_at',
    ]
    list_filter = ['scope', 'is_system', 'organization', 'created_at']
    search_fields = ['name', 'display_name', 'description', 'organization__name']
    readonly_fields = ['id', 'created_at', 'updated_at']
    ordering = ['scope', 'name']
    list_per_page = 25
    filter_horizontal = ('permissions',)

    fieldsets = (
        (None, {
            'fields': ('id', 'name', 'display_name', 'description'),
        }),
        (_('Scope'), {
            'fields': ('scope', 'organization', 'is_system'),
        }),
        (_('Permissions'), {
            'fields': ('permissions',),
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )


@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    """Admin interface for Permission management."""

    list_display = [
        'code',
        'resource',
        'action',
        'description',
        'is_system',
    ]
    list_filter = ['resource', 'action', 'is_system']
    search_fields = ['resource', 'action', 'description']
    readonly_fields = ['id', 'created_at', 'updated_at']
    ordering = ['resource', 'action']
    list_per_page = 50

    fieldsets = (
        (None, {
            'fields': ('id', 'resource', 'action', 'description'),
        }),
        (_('Settings'), {
            'fields': ('is_system',),
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    def code(self, obj):
        """Display the permission code (resource.action)."""
        return format_html(
            '<code style="background-color: #f1f1f1; padding: 2px 6px; '
            'border-radius: 3px;">{}.{}</code>',
            obj.resource,
            obj.action
        )
    code.short_description = _('Permission Code')
    code.admin_order_field = 'resource'


@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    """Admin interface for Session (JWT token) management."""

    list_display = [
        'user',
        'status_badge',
        'ip_address',
        'expires_at',
        'created_at',
    ]
    list_filter = ['status', 'created_at', 'expires_at']
    search_fields = ['user__email', 'ip_address', 'user_agent']
    readonly_fields = [
        'id',
        'refresh_token',
        'created_at',
        'updated_at',
        'revoked_at',
    ]
    ordering = ['-created_at']
    list_per_page = 50
    date_hierarchy = 'created_at'

    fieldsets = (
        (None, {
            'fields': ('id', 'user', 'status'),
        }),
        (_('Token Details'), {
            'fields': ('refresh_token', 'expires_at'),
        }),
        (_('Client Information'), {
            'fields': ('ip_address', 'user_agent'),
        }),
        (_('Revocation'), {
            'fields': ('revoked_at', 'revoke_reason'),
            'classes': ('collapse',),
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    def status_badge(self, obj):
        """Display status with color-coded badge."""
        colors = {
            'ACTIVE': '#28a745',
            'EXPIRED': '#6c757d',
            'REVOKED': '#dc3545',
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-size: 11px; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = _('Status')
    status_badge.admin_order_field = 'status'

    actions = ['revoke_sessions']

    @admin.action(description=_('Revoke selected sessions'))
    def revoke_sessions(self, request, queryset):
        """Bulk action to revoke selected sessions."""
        from django.utils import timezone
        count = queryset.update(
            status='REVOKED',
            revoked_at=timezone.now(),
            revoke_reason='Revoked by admin'
        )
        self.message_user(
            request,
            _('%(count)d session(s) have been revoked.') % {'count': count}
        )


@admin.register(UserRole)
class UserRoleAdmin(admin.ModelAdmin):
    """Admin interface for User-Role assignment management."""

    list_display = [
        'user',
        'role',
        'organization',
        'branch',
        'granted_by',
        'is_active',
        'created_at',
    ]
    list_filter = ['role', 'organization', 'created_at']
    search_fields = [
        'user__email',
        'role__name',
        'organization__name',
        'granted_by__email',
    ]
    readonly_fields = ['id', 'created_at', 'updated_at']
    ordering = ['-created_at']
    list_per_page = 50
    raw_id_fields = ['user', 'granted_by']
    autocomplete_fields = ['organization', 'branch', 'role']

    fieldsets = (
        (None, {
            'fields': ('id', 'user', 'role'),
        }),
        (_('Scope'), {
            'fields': ('organization', 'branch'),
        }),
        (_('Administration'), {
            'fields': ('granted_by', 'expires_at'),
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    def is_active(self, obj):
        """Display if role assignment is currently active."""
        return obj.is_active
    is_active.boolean = True
    is_active.short_description = _('Active')


@admin.register(RolePermission)
class RolePermissionAdmin(admin.ModelAdmin):
    """Admin interface for Role-Permission assignment management."""

    list_display = [
        'role',
        'permission_code',
        'has_conditions',
        'created_at',
    ]
    list_filter = ['role', 'permission__resource', 'created_at']
    search_fields = [
        'role__name',
        'permission__resource',
        'permission__action',
    ]
    readonly_fields = ['id', 'created_at', 'updated_at']
    ordering = ['role', 'permission']
    list_per_page = 50
    autocomplete_fields = ['role', 'permission']

    fieldsets = (
        (None, {
            'fields': ('id', 'role', 'permission'),
        }),
        (_('Conditions'), {
            'fields': ('conditions',),
            'description': _('CASL-like conditions for fine-grained access control (JSON)')
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    def permission_code(self, obj):
        """Display the permission code."""
        return format_html(
            '<code style="background-color: #f1f1f1; padding: 2px 6px; '
            'border-radius: 3px;">{}</code>',
            obj.permission.code
        )
    permission_code.short_description = _('Permission')
    permission_code.admin_order_field = 'permission__resource'

    def has_conditions(self, obj):
        """Display if this assignment has conditions."""
        return bool(obj.conditions)
    has_conditions.boolean = True
    has_conditions.short_description = _('Conditions')


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    """
    Admin interface for AuditLog viewing.

    Note: AuditLogs are read-only in admin. They are created
    automatically by the system and should not be modified.
    """

    list_display = [
        'created_at',
        'action_badge',
        'resource_display',
        'user',
        'organization',
        'ip_address',
    ]
    list_filter = ['action', 'resource', 'organization', 'created_at']
    search_fields = [
        'user__email',
        'resource',
        'resource_id',
        'description',
        'ip_address',
    ]
    readonly_fields = [
        'id',
        'organization',
        'user',
        'action',
        'resource',
        'resource_id',
        'description',
        'old_values',
        'new_values',
        'ip_address',
        'user_agent',
        'metadata',
        'created_at',
    ]
    ordering = ['-created_at']
    list_per_page = 100
    date_hierarchy = 'created_at'

    # Make audit logs read-only
    def has_add_permission(self, request):
        """Prevent adding audit logs manually."""
        return False

    def has_change_permission(self, request, obj=None):
        """Prevent modifying audit logs."""
        return False

    def has_delete_permission(self, request, obj=None):
        """Prevent deleting audit logs."""
        return False

    fieldsets = (
        (None, {
            'fields': ('id', 'created_at'),
        }),
        (_('Action Details'), {
            'fields': ('action', 'resource', 'resource_id', 'description'),
        }),
        (_('Context'), {
            'fields': ('organization', 'user', 'ip_address', 'user_agent'),
        }),
        (_('Data Changes'), {
            'fields': ('old_values', 'new_values'),
            'classes': ('collapse',),
        }),
        (_('Metadata'), {
            'fields': ('metadata',),
            'classes': ('collapse',),
        }),
    )

    def action_badge(self, obj):
        """Display action with color-coded badge."""
        colors = {
            'CREATE': '#28a745',
            'UPDATE': '#17a2b8',
            'DELETE': '#dc3545',
            'LOGIN': '#28a745',
            'LOGOUT': '#6c757d',
            'LOGIN_FAILED': '#ffc107',
        }
        color = colors.get(obj.action, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-size: 11px; font-weight: bold;">{}</span>',
            color,
            obj.get_action_display()
        )
    action_badge.short_description = _('Action')
    action_badge.admin_order_field = 'action'

    def resource_display(self, obj):
        """Display resource with ID."""
        if obj.resource_id:
            return format_html(
                '<span>{}</span> <code style="background-color: #f1f1f1; '
                'padding: 2px 6px; border-radius: 3px; font-size: 10px;">{}</code>',
                obj.resource,
                obj.resource_id[:8] + '...' if len(obj.resource_id) > 8 else obj.resource_id
            )
        return obj.resource
    resource_display.short_description = _('Resource')
    resource_display.admin_order_field = 'resource'
