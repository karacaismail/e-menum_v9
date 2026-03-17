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
from modeltranslation.admin import TabbedTranslationAdmin

from apps.core.forms import OrganizationAdminForm
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
from shared.permissions.admin_permission_mixin import EMenumPermissionMixin


class SoftDeleteAdminMixin:
    """
    Mixin that filters out soft-deleted records in the admin queryset.

    Add this mixin to any ModelAdmin that manages a model with soft delete.
    """

    def get_queryset(self, request):
        """Filter out soft-deleted records by default."""
        qs = super().get_queryset(request)
        if hasattr(qs.model, "deleted_at"):
            return qs.filter(deleted_at__isnull=True)
        return qs


@admin.register(Organization)
class OrganizationAdmin(EMenumPermissionMixin, SoftDeleteAdminMixin, admin.ModelAdmin):
    """
    Admin interface for Organization (tenant) management.

    Provides comprehensive management of tenant organizations including:
    - View/edit organization details
    - Manage subscription status
    - Control organization settings
    - Monitor trial periods

    Note: Soft-deleted organizations are hidden by default.
    """

    form = OrganizationAdminForm

    list_display = [
        "name",
        "slug",
        "email",
        "status_badge",
        "trial_badge",
        "storefront_link",
        "created_at",
    ]
    list_filter = ["status", "created_at", "updated_at"]
    search_fields = ["name", "slug", "email", "phone"]
    readonly_fields = ["id", "created_at", "updated_at", "deleted_at"]
    ordering = ["-created_at"]
    date_hierarchy = "created_at"
    list_per_page = 25

    fieldsets = (
        (
            None,
            {
                "fields": ("id", "name", "slug", "logo"),
                "description": _("Basic organization information"),
            },
        ),
        (
            _("Contact Information"),
            {
                "fields": ("email", "phone"),
            },
        ),
        (
            _("Status & Subscription"),
            {
                "fields": ("status", "trial_ends_at"),
                "description": _("Organization lifecycle and subscription status"),
            },
        ),
        (
            _("Settings"),
            {
                "fields": ("settings",),
                "classes": ("collapse",),
                "description": _("Organization-specific configuration (JSON)"),
            },
        ),
        (
            _("Timestamps"),
            {
                "fields": ("created_at", "updated_at", "deleted_at"),
                "classes": ("collapse",),
            },
        ),
    )

    def status_badge(self, obj):
        """Display status with color-coded badge."""
        colors = {
            "ACTIVE": "#28a745",
            "SUSPENDED": "#ffc107",
            "DELETED": "#dc3545",
        }
        color = colors.get(obj.status, "#6c757d")
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-size: 11px; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display(),
        )

    status_badge.short_description = _("Status")
    status_badge.admin_order_field = "status"

    def trial_badge(self, obj):
        """Display trial status as icon."""
        if obj.is_on_trial:
            return format_html('<span style="color: #17a2b8;">&#10003; Trial</span>')
        return format_html('<span style="color: #6c757d;">-</span>')

    trial_badge.short_description = _("Trial")

    def storefront_link(self, obj):
        """Display link to the organization's public storefront menu."""
        from apps.menu.models import Menu

        default_menu = (
            Menu.objects.filter(
                organization=obj,
                is_published=True,
                deleted_at__isnull=True,
            )
            .order_by("-is_default")
            .first()
        )
        if default_menu:
            url = f"/m/{default_menu.slug}/"
            return format_html(
                '<a href="{}" target="_blank" style="display: inline-flex; align-items: center; '
                'gap: 4px; color: #818cf8; text-decoration: none; font-weight: 500;" '
                'title="Open storefront">'
                '<i class="ph ph-storefront" style="font-size: 16px;"></i> '
                '<span style="font-size: 12px;">Storefront</span></a>',
                url,
            )
        return format_html(
            '<span style="color: #6c757d; font-size: 12px;">No menu</span>'
        )

    storefront_link.short_description = _("Storefront")

    def change_view(self, request, object_id, form_url="", extra_context=None):
        """Add storefront URL to change form context."""
        extra_context = extra_context or {}
        from apps.menu.models import Menu

        obj = self.get_object(request, object_id)
        if obj:
            default_menu = (
                Menu.objects.filter(
                    organization=obj,
                    is_published=True,
                    deleted_at__isnull=True,
                )
                .order_by("-is_default")
                .first()
            )
            if default_menu:
                extra_context["storefront_url"] = f"/m/{default_menu.slug}/"
        return super().change_view(request, object_id, form_url, extra_context)

    actions = ["suspend_organizations", "activate_organizations"]

    @admin.action(description=_("Suspend selected organizations"))
    def suspend_organizations(self, request, queryset):
        """Bulk action to suspend selected organizations."""
        count = queryset.update(status="SUSPENDED")
        self.message_user(
            request,
            _("%(count)d organization(s) have been suspended.") % {"count": count},
        )

    @admin.action(description=_("Activate selected organizations"))
    def activate_organizations(self, request, queryset):
        """Bulk action to activate selected organizations."""
        count = queryset.update(status="ACTIVE")
        self.message_user(
            request,
            _("%(count)d organization(s) have been activated.") % {"count": count},
        )


class CustomUserCreationForm(UserCreationForm):
    """Custom user creation form for admin that uses email as username."""

    class Meta:
        model = User
        fields = ("email", "first_name", "last_name")


class CustomUserChangeForm(UserChangeForm):
    """Custom user change form for admin."""

    class Meta:
        model = User
        fields = "__all__"


def _hex_to_rgb(hex_color):
    """Convert hex color to comma-separated RGB string for rgba()."""
    hex_color = hex_color.lstrip("#")
    return ", ".join(str(int(hex_color[i : i + 2], 16)) for i in (0, 2, 4))


class UserRoleInline(admin.TabularInline):
    """Inline admin for managing user role assignments from User change page."""

    model = UserRole
    extra = 0
    fk_name = "user"
    autocomplete_fields = ["role", "organization", "branch"]
    raw_id_fields = ["granted_by"]
    verbose_name = _("Role Assignment")
    verbose_name_plural = _("Role Assignments")
    fields = ["role", "organization", "branch", "granted_by", "expires_at"]

    def get_queryset(self, request):
        """Optimize with select_related."""
        return (
            super()
            .get_queryset(request)
            .select_related("role", "organization", "branch", "granted_by")
        )


@admin.register(User)
class UserAdmin(EMenumPermissionMixin, SoftDeleteAdminMixin, BaseUserAdmin):
    """
    Enhanced admin interface for User management.

    Extends Django's built-in UserAdmin with customizations for:
    - Email-based authentication (no username)
    - Organization membership
    - Custom status field
    - Soft delete support
    - Inline role assignment (RBAC)
    - Visual role badges in list view
    - User impersonation links

    Note: Soft-deleted users are hidden by default.
    """

    form = CustomUserChangeForm
    add_form = CustomUserCreationForm
    inlines = [UserRoleInline]

    list_display = [
        "email",
        "full_name",
        "organization",
        "roles_display",
        "status_badge",
        "is_staff",
        "is_superuser",
        "impersonate_link",
        "created_at",
    ]
    list_filter = [
        "status",
        "is_staff",
        "is_superuser",
        "organization",
        "created_at",
    ]
    search_fields = ["email", "first_name", "last_name", "phone"]
    readonly_fields = [
        "id",
        "created_at",
        "updated_at",
        "deleted_at",
        "last_login_at",
        "email_verified_at",
        "last_login",
    ]
    ordering = ["-created_at"]
    date_hierarchy = "created_at"
    list_per_page = 25
    filter_horizontal = ("groups", "user_permissions")

    # Override BaseUserAdmin fieldsets to use email instead of username
    fieldsets = (
        (
            None,
            {"fields": ("id", "email", "password"), "description": _("Credentials")},
        ),
        (
            _("Personal Information"),
            {
                "fields": ("first_name", "last_name", "phone", "avatar"),
            },
        ),
        (
            _("Organization"),
            {
                "fields": ("organization", "status"),
                "description": _("Tenant membership and account status"),
            },
        ),
        (
            _("Permissions"),
            {
                "fields": (
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            _("Important Dates"),
            {
                "fields": (
                    "email_verified_at",
                    "last_login_at",
                    "last_login",
                    "created_at",
                    "updated_at",
                    "deleted_at",
                ),
                "classes": ("collapse",),
            },
        ),
    )

    # Fieldsets for adding a new user
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "first_name",
                    "last_name",
                    "password1",
                    "password2",
                    "organization",
                    "status",
                    "is_staff",
                ),
            },
        ),
    )

    def full_name(self, obj):
        """Display user's full name."""
        return obj.full_name or obj.email

    full_name.short_description = _("Full Name")
    full_name.admin_order_field = "first_name"

    def status_badge(self, obj):
        """Display status with color-coded badge."""
        colors = {
            "ACTIVE": "#28a745",
            "INVITED": "#17a2b8",
            "SUSPENDED": "#dc3545",
        }
        color = colors.get(obj.status, "#6c757d")
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-size: 11px; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display(),
        )

    status_badge.short_description = _("Status")
    status_badge.admin_order_field = "status"

    def roles_display(self, obj):
        """Display user's RBAC role badges."""
        user_roles = (
            UserRole.objects.filter(user=obj)
            .select_related("role")
            .order_by("role__scope", "role__name")[:5]
        )

        if not user_roles:
            return format_html(
                '<span style="color: #475569; font-size: 11px; font-style: italic;">No roles</span>'
            )

        badges = ""
        for ur in user_roles:
            scope_color = "#8b5cf6" if ur.role.scope == "PLATFORM" else "#0ea5e9"
            active_style = (
                "" if ur.is_active else "opacity: 0.5; text-decoration: line-through;"
            )
            badges += (
                f'<span style="display: inline-block; padding: 2px 8px; '
                f"background: rgba({_hex_to_rgb(scope_color)}, 0.12); color: {scope_color}; "
                f"border-radius: 4px; font-size: 10px; font-weight: 600; "
                f'margin-right: 3px; margin-bottom: 2px; white-space: nowrap; {active_style}">'
                f"{ur.role.display_name}</span>"
            )

        total = UserRole.objects.filter(user=obj).count()
        if total > 5:
            badges += (
                f'<span style="color: #64748b; font-size: 10px; margin-left: 2px;">'
                f"+{total - 5}</span>"
            )

        return format_html(badges)

    roles_display.short_description = _("Roles")

    def impersonate_link(self, obj):
        """Display impersonate button for non-superuser users."""
        if obj.is_superuser:
            return format_html(
                '<span style="color: #6c757d; font-size: 11px;">-</span>'
            )
        return format_html(
            '<a href="/impersonate/{}/" style="display: inline-flex; align-items: center; '
            "gap: 4px; padding: 3px 10px; background: rgba(99, 102, 241, 0.1); "
            "color: #818cf8; border: 1px solid rgba(99, 102, 241, 0.2); "
            "border-radius: 4px; font-size: 11px; font-weight: 500; "
            'text-decoration: none; white-space: nowrap;" '
            'title="Impersonate this user">'
            '<i class="ph ph-user-switch" style="font-size: 14px;"></i> '
            "Impersonate</a>",
            obj.pk,
        )

    impersonate_link.short_description = _("Impersonate")

    actions = ["suspend_users", "activate_users", "verify_email"]

    @admin.action(description=_("Suspend selected users"))
    def suspend_users(self, request, queryset):
        """Bulk action to suspend selected users."""
        count = queryset.update(status="SUSPENDED")
        self.message_user(
            request, _("%(count)d user(s) have been suspended.") % {"count": count}
        )

    @admin.action(description=_("Activate selected users"))
    def activate_users(self, request, queryset):
        """Bulk action to activate selected users."""
        count = queryset.update(status="ACTIVE")
        self.message_user(
            request, _("%(count)d user(s) have been activated.") % {"count": count}
        )

    @admin.action(description=_("Mark email as verified"))
    def verify_email(self, request, queryset):
        """Bulk action to mark email as verified."""
        from django.utils import timezone

        count = queryset.update(email_verified_at=timezone.now())
        self.message_user(
            request, _("%(count)d user(s) email verified.") % {"count": count}
        )


@admin.register(Branch)
class BranchAdmin(EMenumPermissionMixin, SoftDeleteAdminMixin, admin.ModelAdmin):
    """Admin interface for Branch (location) management."""

    list_display = [
        "name",
        "organization",
        "city",
        "status_badge",
        "is_main",
        "created_at",
    ]
    list_filter = ["status", "is_main", "organization", "city", "created_at"]
    search_fields = ["name", "slug", "address", "city", "organization__name"]
    readonly_fields = ["id", "created_at", "updated_at", "deleted_at"]
    ordering = ["-is_main", "name"]
    list_per_page = 25

    fieldsets = (
        (
            None,
            {
                "fields": ("id", "organization", "name", "slug", "is_main"),
            },
        ),
        (
            _("Address"),
            {
                "fields": ("address", "city", "district", "postal_code", "country"),
            },
        ),
        (
            _("Contact"),
            {
                "fields": ("phone", "email"),
            },
        ),
        (
            _("Location"),
            {
                "fields": ("latitude", "longitude", "timezone"),
                "classes": ("collapse",),
            },
        ),
        (
            _("Configuration"),
            {
                "fields": ("status", "settings", "operating_hours"),
                "classes": ("collapse",),
            },
        ),
        (
            _("Timestamps"),
            {
                "fields": ("created_at", "updated_at", "deleted_at"),
                "classes": ("collapse",),
            },
        ),
    )

    def status_badge(self, obj):
        """Display status with color-coded badge."""
        colors = {
            "ACTIVE": "#28a745",
            "INACTIVE": "#6c757d",
            "SUSPENDED": "#dc3545",
        }
        color = colors.get(obj.status, "#6c757d")
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-size: 11px; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display(),
        )

    status_badge.short_description = _("Status")
    status_badge.admin_order_field = "status"


class RolePermissionInline(admin.TabularInline):
    """Inline admin for managing role permissions."""

    model = RolePermission
    extra = 1
    autocomplete_fields = ["permission"]
    verbose_name = _("Permission")
    verbose_name_plural = _("Permissions")

    def get_queryset(self, request):
        """Optimize with select_related."""
        return super().get_queryset(request).select_related("permission")


@admin.register(Role)
class RoleAdmin(EMenumPermissionMixin, TabbedTranslationAdmin):
    """
    Enhanced admin interface for Role management.

    Features:
    - Visual scope badge (Platform vs Organization)
    - Permission count and user count columns
    - Permission matrix preview (readonly, shows all assigned permissions)
    - Duplicate role action
    - Color-coded system role indicator
    """

    list_display = [
        "display_name",
        "name",
        "scope_badge",
        "organization",
        "permission_count",
        "user_count",
        "system_badge",
        "created_at",
    ]
    list_filter = ["scope", "is_system", "organization", "created_at"]
    search_fields = ["name", "display_name", "description", "organization__name"]
    readonly_fields = [
        "id",
        "created_at",
        "updated_at",
        "permission_matrix_preview",
        "assigned_users_preview",
    ]
    ordering = ["scope", "name"]
    list_per_page = 25
    inlines = [RolePermissionInline]

    fieldsets = (
        (
            None,
            {
                "fields": ("id", "name", "display_name", "description"),
            },
        ),
        (
            _("Scope"),
            {
                "fields": ("scope", "organization", "is_system"),
                "description": _(
                    "Platform roles apply system-wide. Organization roles are tenant-scoped."
                ),
            },
        ),
        (
            _("Permission Matrix"),
            {
                "fields": ("permission_matrix_preview",),
                "description": _(
                    "Visual overview of all permissions assigned to this role, grouped by resource. "
                    "Use the inline form below to add or remove permissions."
                ),
            },
        ),
        (
            _("Assigned Users"),
            {
                "fields": ("assigned_users_preview",),
                "classes": ("collapse",),
                "description": _("Users currently assigned to this role."),
            },
        ),
        (
            _("Timestamps"),
            {
                "fields": ("created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )

    def get_queryset(self, request):
        """Annotate with permission and user counts for list display."""
        from django.db.models import Count

        return (
            super()
            .get_queryset(request)
            .annotate(
                _permission_count=Count("role_permissions", distinct=True),
                _user_count=Count("user_roles", distinct=True),
            )
        )

    def scope_badge(self, obj):
        """Display scope as a color-coded badge."""
        if obj.scope == "PLATFORM":
            return format_html(
                '<span style="background: linear-gradient(135deg, #6366f1, #8b5cf6); '
                "color: white; padding: 3px 10px; border-radius: 3px; font-size: 11px; "
                'font-weight: bold; letter-spacing: 0.5px;">'
                '<i class="ph ph-globe" style="font-size: 12px; margin-right: 3px;"></i>'
                "Platform</span>"
            )
        return format_html(
            '<span style="background: linear-gradient(135deg, #0ea5e9, #06b6d4); '
            "color: white; padding: 3px 10px; border-radius: 3px; font-size: 11px; "
            'font-weight: bold; letter-spacing: 0.5px;">'
            '<i class="ph ph-buildings" style="font-size: 12px; margin-right: 3px;"></i>'
            "Organization</span>"
        )

    scope_badge.short_description = _("Scope")
    scope_badge.admin_order_field = "scope"

    def permission_count(self, obj):
        """Display the number of permissions assigned to this role."""
        count = getattr(obj, "_permission_count", 0)
        if count == 0:
            return format_html(
                '<span style="color: #ef4444; font-size: 12px;">'
                '<i class="ph ph-warning" style="font-size: 13px;"></i> 0</span>'
            )
        return format_html(
            '<span style="color: #22c55e; font-weight: 600; font-size: 12px;">'
            '<i class="ph ph-shield-check" style="font-size: 13px;"></i> {}</span>',
            count,
        )

    permission_count.short_description = _("Permissions")
    permission_count.admin_order_field = "_permission_count"

    def user_count(self, obj):
        """Display the number of users assigned to this role."""
        count = getattr(obj, "_user_count", 0)
        return format_html(
            '<span style="color: #94a3b8; font-size: 12px;">'
            '<i class="ph ph-users" style="font-size: 13px;"></i> {}</span>',
            count,
        )

    user_count.short_description = _("Users")
    user_count.admin_order_field = "_user_count"

    def system_badge(self, obj):
        """Display system role status with icon."""
        if obj.is_system:
            return format_html(
                '<span style="color: #f59e0b; font-size: 12px;" title="System role - cannot be deleted">'
                '<i class="ph-fill ph-lock-simple" style="font-size: 14px;"></i></span>'
            )
        return format_html(
            '<span style="color: #475569; font-size: 12px;" title="Custom role">'
            '<i class="ph ph-lock-simple-open" style="font-size: 14px;"></i></span>'
        )

    system_badge.short_description = _("System")
    system_badge.admin_order_field = "is_system"

    def permission_matrix_preview(self, obj):
        """
        Display a visual permission matrix showing all assigned permissions
        grouped by resource with action columns.
        """
        if not obj.pk:
            return format_html(
                '<span style="color: #64748b; font-style: italic;">Save the role first to see permissions.</span>'
            )

        role_perms = (
            RolePermission.objects.filter(role=obj)
            .select_related("permission")
            .order_by("permission__resource", "permission__action")
        )

        if not role_perms.exists():
            return format_html(
                '<div style="padding: 12px 16px; background: rgba(239, 68, 68, 0.08); '
                "border: 1px solid rgba(239, 68, 68, 0.2); border-radius: 6px; "
                'color: #ef4444; font-size: 13px;">'
                '<i class="ph ph-warning-circle" style="font-size: 16px; margin-right: 6px;"></i>'
                "No permissions assigned to this role.</div>"
            )

        # Group permissions by resource
        resource_perms = {}
        for rp in role_perms:
            resource = rp.permission.resource
            if resource not in resource_perms:
                resource_perms[resource] = []
            resource_perms[resource].append(rp.permission.action)

        # Action color map
        action_colors = {
            "VIEW": ("#3b82f6", "ph-eye"),
            "CREATE": ("#22c55e", "ph-plus-circle"),
            "UPDATE": ("#f59e0b", "ph-pencil-simple"),
            "DELETE": ("#ef4444", "ph-trash"),
            "MANAGE": ("#8b5cf6", "ph-gear"),
            "EXPORT": ("#06b6d4", "ph-download-simple"),
        }

        rows = ""
        for resource, actions in sorted(resource_perms.items()):
            action_badges = ""
            for action in sorted(actions):
                color, icon = action_colors.get(
                    action.upper(), ("#64748b", "ph-circle")
                )
                action_badges += (
                    f'<span style="display: inline-flex; align-items: center; gap: 3px; '
                    f"padding: 2px 8px; background: rgba({_hex_to_rgb(color)}, 0.12); "
                    f"color: {color}; border-radius: 4px; font-size: 11px; font-weight: 500; "
                    f'margin-right: 4px; margin-bottom: 2px;">'
                    f'<i class="ph {icon}" style="font-size: 12px;"></i>{action}</span>'
                )

            rows += (
                f'<tr style="border-bottom: 1px solid rgba(148, 163, 184, 0.1);">'
                f'<td style="padding: 8px 12px; font-weight: 600; color: #e2e8f0; font-size: 13px; '
                f'white-space: nowrap; vertical-align: top;">'
                f'<code style="background: rgba(99, 102, 241, 0.12); color: #a5b4fc; '
                f'padding: 2px 8px; border-radius: 4px; font-size: 12px;">{resource}</code></td>'
                f'<td style="padding: 8px 12px;">{action_badges}</td></tr>'
            )

        return format_html(
            '<div style="border: 1px solid rgba(148, 163, 184, 0.15); border-radius: 8px; '
            'overflow: hidden; max-width: 600px;">'
            '<table style="width: 100%; border-collapse: collapse;">'
            '<thead><tr style="background: rgba(99, 102, 241, 0.08); '
            'border-bottom: 1px solid rgba(148, 163, 184, 0.15);">'
            '<th style="padding: 8px 12px; text-align: left; color: #94a3b8; font-size: 11px; '
            'font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;">Resource</th>'
            '<th style="padding: 8px 12px; text-align: left; color: #94a3b8; font-size: 11px; '
            'font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;">Actions</th>'
            "</tr></thead>"
            "<tbody>{}</tbody>"
            "</table>"
            '<div style="padding: 6px 12px; background: rgba(148, 163, 184, 0.05); '
            'border-top: 1px solid rgba(148, 163, 184, 0.1); color: #64748b; font-size: 11px;">'
            '<i class="ph ph-info" style="font-size: 12px; margin-right: 4px;"></i>'
            "{} resource(s), {} permission(s) total</div>"
            "</div>",
            rows,
            len(resource_perms),
            role_perms.count(),
        )

    permission_matrix_preview.short_description = _("Permission Matrix")

    def assigned_users_preview(self, obj):
        """Display a list of users assigned to this role."""
        if not obj.pk:
            return format_html(
                '<span style="color: #64748b; font-style: italic;">Save the role first.</span>'
            )

        user_roles = (
            UserRole.objects.filter(role=obj)
            .select_related("user", "organization")
            .order_by("user__email")[:20]
        )

        if not user_roles.exists():
            return format_html(
                '<span style="color: #64748b; font-style: italic; font-size: 13px;">'
                "No users assigned to this role.</span>"
            )

        items = ""
        for ur in user_roles:
            org_label = ur.organization.name if ur.organization else "Platform"
            active_dot = (
                '<span style="width: 6px; height: 6px; border-radius: 50%; '
                'background: #22c55e; display: inline-block; margin-right: 6px;" '
                'title="Active"></span>'
                if ur.is_active
                else '<span style="width: 6px; height: 6px; border-radius: 50%; '
                'background: #ef4444; display: inline-block; margin-right: 6px;" '
                'title="Expired"></span>'
            )
            items += (
                f'<div style="display: flex; align-items: center; gap: 8px; '
                f'padding: 6px 0; border-bottom: 1px solid rgba(148, 163, 184, 0.08);">'
                f"{active_dot}"
                f'<span style="color: #e2e8f0; font-size: 13px; font-weight: 500;">'
                f"{ur.user.email}</span>"
                f'<span style="color: #64748b; font-size: 11px;">@ {org_label}</span>'
                f"</div>"
            )

        total = UserRole.objects.filter(role=obj).count()
        more_text = ""
        if total > 20:
            more_text = (
                f'<div style="padding: 8px 0; color: #64748b; font-size: 12px;">'
                f"... and {total - 20} more</div>"
            )

        return format_html(
            '<div style="max-width: 500px;">{}{}</div>', items, more_text
        )

    assigned_users_preview.short_description = _("Assigned Users")

    actions = ["duplicate_role"]

    @admin.action(description=_("Duplicate selected roles (without users)"))
    def duplicate_role(self, request, queryset):
        """Create a copy of the selected roles with all their permissions."""
        for role in queryset:
            # Get original permissions
            original_perms = RolePermission.objects.filter(role=role)

            # Create new role
            role.pk = None
            role.name = f"{role.name}_copy"
            role.display_name = f"{role.display_name} (Copy)"
            role.is_system = False
            role.save()

            # Copy permissions
            for rp in original_perms:
                RolePermission.objects.create(
                    role=role, permission=rp.permission, conditions=rp.conditions
                )

        self.message_user(
            request,
            _("%(count)d role(s) have been duplicated.") % {"count": queryset.count()},
        )


@admin.register(Permission)
class PermissionAdmin(EMenumPermissionMixin, admin.ModelAdmin):
    """
    Enhanced admin interface for Permission management.

    Features:
    - Dark-theme compatible code display
    - Color-coded action badges
    - Usage count (how many roles use this permission)
    - Grouped resource display
    """

    list_display = [
        "code_display",
        "resource_badge",
        "action_badge",
        "description",
        "usage_count",
        "system_badge",
    ]
    list_filter = ["resource", "action", "is_system"]
    search_fields = ["resource", "action", "description"]
    readonly_fields = ["id", "created_at", "updated_at", "used_by_roles_preview"]
    ordering = ["resource", "action"]
    list_per_page = 50

    fieldsets = (
        (
            None,
            {
                "fields": ("id", "resource", "action", "description"),
            },
        ),
        (
            _("Settings"),
            {
                "fields": ("is_system",),
            },
        ),
        (
            _("Used By Roles"),
            {
                "fields": ("used_by_roles_preview",),
                "description": _("Roles that have this permission assigned."),
            },
        ),
        (
            _("Timestamps"),
            {
                "fields": ("created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )

    def get_queryset(self, request):
        """Annotate with usage count."""
        from django.db.models import Count

        return (
            super()
            .get_queryset(request)
            .annotate(
                _usage_count=Count("role_permissions", distinct=True),
            )
        )

    def code_display(self, obj):
        """Display the permission code with dark-theme styling."""
        return format_html(
            '<code style="background: rgba(99, 102, 241, 0.12); color: #a5b4fc; '
            "padding: 3px 8px; border-radius: 4px; font-size: 12px; font-weight: 600; "
            'letter-spacing: 0.3px;">{}.{}</code>',
            obj.resource,
            obj.action,
        )

    code_display.short_description = _("Permission Code")
    code_display.admin_order_field = "resource"

    def resource_badge(self, obj):
        """Display resource with a styled badge."""
        return format_html(
            '<span style="color: #e2e8f0; font-weight: 500; font-size: 13px;">{}</span>',
            obj.resource,
        )

    resource_badge.short_description = _("Resource")
    resource_badge.admin_order_field = "resource"

    def action_badge(self, obj):
        """Display action with color-coded badge."""
        action_styles = {
            "VIEW": ("#3b82f6", "ph-eye"),
            "CREATE": ("#22c55e", "ph-plus-circle"),
            "UPDATE": ("#f59e0b", "ph-pencil-simple"),
            "DELETE": ("#ef4444", "ph-trash"),
            "MANAGE": ("#8b5cf6", "ph-gear"),
            "EXPORT": ("#06b6d4", "ph-download-simple"),
        }
        color, icon = action_styles.get(obj.action.upper(), ("#64748b", "ph-circle"))
        return format_html(
            '<span style="display: inline-flex; align-items: center; gap: 4px; '
            "padding: 3px 10px; background: rgba({}, 0.12); color: {}; "
            'border-radius: 4px; font-size: 11px; font-weight: 600;">'
            '<i class="ph {}" style="font-size: 13px;"></i>{}</span>',
            _hex_to_rgb(color),
            color,
            icon,
            obj.get_action_display(),
        )

    action_badge.short_description = _("Action")
    action_badge.admin_order_field = "action"

    def usage_count(self, obj):
        """Display how many roles use this permission."""
        count = getattr(obj, "_usage_count", 0)
        if count == 0:
            return format_html(
                '<span style="color: #475569; font-size: 12px;">0 roles</span>'
            )
        return format_html(
            '<span style="color: #22c55e; font-size: 12px; font-weight: 500;">'
            '<i class="ph ph-shield-check" style="font-size: 12px;"></i> {} role{}</span>',
            count,
            "s" if count > 1 else "",
        )

    usage_count.short_description = _("Used By")
    usage_count.admin_order_field = "_usage_count"

    def system_badge(self, obj):
        """Display system permission status."""
        if obj.is_system:
            return format_html(
                '<span style="color: #f59e0b;" title="System permission">'
                '<i class="ph-fill ph-lock-simple" style="font-size: 14px;"></i></span>'
            )
        return format_html(
            '<span style="color: #475569;" title="Custom permission">'
            '<i class="ph ph-lock-simple-open" style="font-size: 14px;"></i></span>'
        )

    system_badge.short_description = _("System")
    system_badge.admin_order_field = "is_system"

    def used_by_roles_preview(self, obj):
        """Display which roles use this permission."""
        if not obj.pk:
            return format_html(
                '<span style="color: #64748b; font-style: italic;">Save first.</span>'
            )

        role_perms = (
            RolePermission.objects.filter(permission=obj)
            .select_related("role", "role__organization")
            .order_by("role__scope", "role__name")
        )

        if not role_perms.exists():
            return format_html(
                '<span style="color: #64748b; font-style: italic; font-size: 13px;">'
                "No roles use this permission.</span>"
            )

        items = ""
        for rp in role_perms:
            scope_color = "#8b5cf6" if rp.role.scope == "PLATFORM" else "#0ea5e9"
            scope_icon = "ph-globe" if rp.role.scope == "PLATFORM" else "ph-buildings"
            org_label = (
                f" ({rp.role.organization.name})" if rp.role.organization else ""
            )
            conditions_tag = ""
            if rp.conditions:
                conditions_tag = (
                    '<span style="margin-left: 6px; color: #f59e0b; font-size: 11px;" '
                    'title="Has CASL conditions">'
                    '<i class="ph ph-funnel" style="font-size: 12px;"></i></span>'
                )

            items += (
                f'<div style="display: inline-flex; align-items: center; gap: 6px; '
                f"padding: 4px 10px; margin: 2px 4px 2px 0; background: rgba(148, 163, 184, 0.06); "
                f'border: 1px solid rgba(148, 163, 184, 0.1); border-radius: 6px;">'
                f'<i class="ph {scope_icon}" style="font-size: 12px; color: {scope_color};"></i>'
                f'<span style="color: #e2e8f0; font-size: 12px; font-weight: 500;">'
                f"{rp.role.display_name}</span>"
                f'<span style="color: #64748b; font-size: 11px;">{org_label}</span>'
                f"{conditions_tag}"
                f"</div>"
            )

        return format_html(
            '<div style="display: flex; flex-wrap: wrap; gap: 2px;">{}</div>', items
        )

    used_by_roles_preview.short_description = _("Used By Roles")


@admin.register(Session)
class SessionAdmin(EMenumPermissionMixin, admin.ModelAdmin):
    """Admin interface for Session (JWT token) management."""

    list_display = [
        "user",
        "status_badge",
        "ip_address",
        "expires_at",
        "created_at",
    ]
    list_filter = ["status", "created_at", "expires_at"]
    search_fields = ["user__email", "ip_address", "user_agent"]
    readonly_fields = [
        "id",
        "refresh_token",
        "created_at",
        "updated_at",
        "revoked_at",
    ]
    ordering = ["-created_at"]
    list_per_page = 50
    date_hierarchy = "created_at"

    fieldsets = (
        (
            None,
            {
                "fields": ("id", "user", "status"),
            },
        ),
        (
            _("Token Details"),
            {
                "fields": ("refresh_token", "expires_at"),
            },
        ),
        (
            _("Client Information"),
            {
                "fields": ("ip_address", "user_agent"),
            },
        ),
        (
            _("Revocation"),
            {
                "fields": ("revoked_at", "revoke_reason"),
                "classes": ("collapse",),
            },
        ),
        (
            _("Timestamps"),
            {
                "fields": ("created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )

    def status_badge(self, obj):
        """Display status with color-coded badge."""
        colors = {
            "ACTIVE": "#28a745",
            "EXPIRED": "#6c757d",
            "REVOKED": "#dc3545",
        }
        color = colors.get(obj.status, "#6c757d")
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-size: 11px; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display(),
        )

    status_badge.short_description = _("Status")
    status_badge.admin_order_field = "status"

    actions = ["revoke_sessions"]

    @admin.action(description=_("Revoke selected sessions"))
    def revoke_sessions(self, request, queryset):
        """Bulk action to revoke selected sessions."""
        from django.utils import timezone

        count = queryset.update(
            status="REVOKED",
            revoked_at=timezone.now(),
            revoke_reason="Revoked by admin",
        )
        self.message_user(
            request, _("%(count)d session(s) have been revoked.") % {"count": count}
        )


@admin.register(UserRole)
class UserRoleAdmin(EMenumPermissionMixin, admin.ModelAdmin):
    """
    Enhanced admin interface for User-Role assignment management.

    Features:
    - Visual status indicator (active/expired)
    - Scope display with org + branch info
    - Role scope badge
    - Auto-populate granted_by on save
    """

    list_display = [
        "user_display",
        "role_display",
        "scope_display",
        "granted_by_display",
        "status_indicator",
        "expires_display",
        "created_at",
    ]
    list_filter = ["role", "role__scope", "organization", "created_at"]
    search_fields = [
        "user__email",
        "user__first_name",
        "user__last_name",
        "role__name",
        "role__display_name",
        "organization__name",
        "granted_by__email",
    ]
    readonly_fields = ["id", "created_at", "updated_at"]
    ordering = ["-created_at"]
    list_per_page = 50
    raw_id_fields = ["user", "granted_by"]
    autocomplete_fields = ["organization", "branch", "role"]
    list_select_related = ["user", "role", "organization", "branch", "granted_by"]

    fieldsets = (
        (
            None,
            {
                "fields": ("id", "user", "role"),
                "description": _("Select a user and assign a role."),
            },
        ),
        (
            _("Scope"),
            {
                "fields": ("organization", "branch"),
                "description": _(
                    "Organization scope is required for organization roles. "
                    "Branch further restricts access to a specific location."
                ),
            },
        ),
        (
            _("Administration"),
            {
                "fields": ("granted_by", "expires_at"),
                "description": _(
                    "Set an expiration date for temporary role assignments. "
                    "Leave blank for permanent assignments."
                ),
            },
        ),
        (
            _("Timestamps"),
            {
                "fields": ("created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )

    def user_display(self, obj):
        """Display user email with name."""
        name = obj.user.full_name
        if name and name != obj.user.email:
            return format_html(
                '<div><span style="color: #e2e8f0; font-weight: 500;">{}</span><br>'
                '<span style="color: #64748b; font-size: 11px;">{}</span></div>',
                obj.user.email,
                name,
            )
        return format_html(
            '<span style="color: #e2e8f0; font-weight: 500;">{}</span>', obj.user.email
        )

    user_display.short_description = _("User")
    user_display.admin_order_field = "user__email"

    def role_display(self, obj):
        """Display role with scope badge."""
        scope_color = "#8b5cf6" if obj.role.scope == "PLATFORM" else "#0ea5e9"
        scope_icon = "ph-globe" if obj.role.scope == "PLATFORM" else "ph-buildings"
        return format_html(
            '<span style="display: inline-flex; align-items: center; gap: 6px;">'
            '<i class="ph {}" style="font-size: 14px; color: {};"></i>'
            '<span style="font-weight: 500;">{}</span></span>',
            scope_icon,
            scope_color,
            obj.role.display_name,
        )

    role_display.short_description = _("Role")
    role_display.admin_order_field = "role__display_name"

    def scope_display(self, obj):
        """Display organization and branch scope."""
        if obj.organization:
            org_text = obj.organization.name
            if obj.branch:
                return format_html(
                    '<div><span style="color: #e2e8f0; font-size: 13px;">{}</span><br>'
                    '<span style="color: #94a3b8; font-size: 11px;">'
                    '<i class="ph ph-map-pin" style="font-size: 11px;"></i> {}</span></div>',
                    org_text,
                    obj.branch.name,
                )
            return format_html(
                '<span style="color: #e2e8f0; font-size: 13px;">{}</span>', org_text
            )
        return format_html(
            '<span style="color: #8b5cf6; font-size: 12px; font-style: italic;">'
            '<i class="ph ph-globe" style="font-size: 12px;"></i> Platform-wide</span>'
        )

    scope_display.short_description = _("Scope")
    scope_display.admin_order_field = "organization__name"

    def granted_by_display(self, obj):
        """Display who granted this role."""
        if obj.granted_by:
            return format_html(
                '<span style="color: #94a3b8; font-size: 12px;">{}</span>',
                obj.granted_by.email,
            )
        return format_html(
            '<span style="color: #475569; font-size: 11px; font-style: italic;">System</span>'
        )

    granted_by_display.short_description = _("Granted By")
    granted_by_display.admin_order_field = "granted_by__email"

    def status_indicator(self, obj):
        """Display active/expired status with visual indicator."""
        if obj.is_active:
            return format_html(
                '<span style="display: inline-flex; align-items: center; gap: 4px; '
                "padding: 3px 10px; background: rgba(34, 197, 94, 0.1); "
                'color: #22c55e; border-radius: 4px; font-size: 11px; font-weight: 600;">'
                '<span style="width: 6px; height: 6px; border-radius: 50%; '
                'background: #22c55e;"></span>Active</span>'
            )
        return format_html(
            '<span style="display: inline-flex; align-items: center; gap: 4px; '
            "padding: 3px 10px; background: rgba(239, 68, 68, 0.1); "
            'color: #ef4444; border-radius: 4px; font-size: 11px; font-weight: 600;">'
            '<span style="width: 6px; height: 6px; border-radius: 50%; '
            'background: #ef4444;"></span>Expired</span>'
        )

    status_indicator.short_description = _("Status")

    def expires_display(self, obj):
        """Display expiration date or permanent label."""
        if obj.expires_at:
            from django.utils import timezone

            if obj.expires_at < timezone.now():
                return format_html(
                    '<span style="color: #ef4444; font-size: 12px;" title="{}">'
                    '<i class="ph ph-clock-countdown" style="font-size: 13px;"></i> Expired</span>',
                    obj.expires_at.strftime("%Y-%m-%d %H:%M"),
                )
            return format_html(
                '<span style="color: #f59e0b; font-size: 12px;" title="{}">'
                '<i class="ph ph-clock" style="font-size: 13px;"></i> {}</span>',
                obj.expires_at.strftime("%Y-%m-%d %H:%M"),
                obj.expires_at.strftime("%Y-%m-%d"),
            )
        return format_html(
            '<span style="color: #22c55e; font-size: 12px;">'
            '<i class="ph ph-infinity" style="font-size: 13px;"></i> Permanent</span>'
        )

    expires_display.short_description = _("Expires")
    expires_display.admin_order_field = "expires_at"

    def save_model(self, request, obj, form, change):
        """Auto-populate granted_by if not set."""
        if not change and not obj.granted_by:
            obj.granted_by = request.user
        super().save_model(request, obj, form, change)

    actions = ["revoke_assignments"]

    @admin.action(description=_("Revoke selected role assignments (set expired)"))
    def revoke_assignments(self, request, queryset):
        """Bulk action to expire selected role assignments immediately."""
        from django.utils import timezone

        count = queryset.update(expires_at=timezone.now())
        self.message_user(
            request,
            _("%(count)d role assignment(s) have been revoked.") % {"count": count},
        )


@admin.register(RolePermission)
class RolePermissionAdmin(EMenumPermissionMixin, admin.ModelAdmin):
    """
    Enhanced admin interface for Role-Permission assignment management.

    Features:
    - Dark-theme compatible permission code display
    - Role scope indicator
    - Visual conditions indicator
    """

    list_display = [
        "role_display",
        "permission_code_display",
        "conditions_badge",
        "created_at",
    ]
    list_filter = ["role", "role__scope", "permission__resource", "created_at"]
    search_fields = [
        "role__name",
        "role__display_name",
        "permission__resource",
        "permission__action",
    ]
    readonly_fields = ["id", "created_at", "updated_at"]
    ordering = ["role", "permission"]
    list_per_page = 50
    autocomplete_fields = ["role", "permission"]
    list_select_related = ["role", "role__organization", "permission"]

    fieldsets = (
        (
            None,
            {
                "fields": ("id", "role", "permission"),
            },
        ),
        (
            _("Conditions"),
            {
                "fields": ("conditions",),
                "description": _(
                    "CASL-like conditions for fine-grained access control (JSON). "
                    'Example: {"organization_id": "${user.organization_id}"} restricts '
                    "access to the user's own organization data."
                ),
            },
        ),
        (
            _("Timestamps"),
            {
                "fields": ("created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )

    def role_display(self, obj):
        """Display role with scope indicator."""
        scope_color = "#8b5cf6" if obj.role.scope == "PLATFORM" else "#0ea5e9"
        scope_icon = "ph-globe" if obj.role.scope == "PLATFORM" else "ph-buildings"
        org_label = f" ({obj.role.organization.name})" if obj.role.organization else ""
        return format_html(
            '<span style="display: inline-flex; align-items: center; gap: 6px;">'
            '<i class="ph {}" style="font-size: 14px; color: {};"></i>'
            '<span style="font-weight: 500;">{}</span>'
            '<span style="color: #64748b; font-size: 11px;">{}</span></span>',
            scope_icon,
            scope_color,
            obj.role.display_name,
            org_label,
        )

    role_display.short_description = _("Role")
    role_display.admin_order_field = "role__name"

    def permission_code_display(self, obj):
        """Display the permission code with dark-theme styling and action color."""
        action_colors = {
            "VIEW": "#3b82f6",
            "CREATE": "#22c55e",
            "UPDATE": "#f59e0b",
            "DELETE": "#ef4444",
            "MANAGE": "#8b5cf6",
            "EXPORT": "#06b6d4",
        }
        color = action_colors.get(obj.permission.action.upper(), "#64748b")
        return format_html(
            '<code style="background: rgba({}, 0.12); color: {}; '
            'padding: 3px 8px; border-radius: 4px; font-size: 12px; font-weight: 600;">'
            "{}</code>",
            _hex_to_rgb(color),
            color,
            obj.permission.code,
        )

    permission_code_display.short_description = _("Permission")
    permission_code_display.admin_order_field = "permission__resource"

    def conditions_badge(self, obj):
        """Display conditions status with visual indicator."""
        if obj.conditions:
            import json

            try:
                conditions_str = json.dumps(obj.conditions, indent=2)
                preview = (
                    conditions_str[:80] + "..."
                    if len(conditions_str) > 80
                    else conditions_str
                )
            except (TypeError, ValueError):
                preview = str(obj.conditions)

            return format_html(
                '<span style="display: inline-flex; align-items: center; gap: 4px; '
                "padding: 3px 10px; background: rgba(245, 158, 11, 0.1); "
                'color: #f59e0b; border-radius: 4px; font-size: 11px; font-weight: 500;" '
                'title="{}">'
                '<i class="ph ph-funnel" style="font-size: 13px;"></i> Conditional</span>',
                preview,
            )
        return format_html(
            '<span style="color: #475569; font-size: 11px;">'
            '<i class="ph ph-check-circle" style="font-size: 13px;"></i> Full Access</span>'
        )

    conditions_badge.short_description = _("Conditions")


@admin.register(AuditLog)
class AuditLogAdmin(EMenumPermissionMixin, admin.ModelAdmin):
    """
    Admin interface for AuditLog viewing.

    Note: AuditLogs are read-only in admin. They are created
    automatically by the system and should not be modified.
    """

    list_display = [
        "created_at",
        "action_badge",
        "resource_display",
        "user",
        "organization",
        "ip_address",
    ]
    list_filter = ["action", "resource", "organization", "created_at"]
    search_fields = [
        "user__email",
        "resource",
        "resource_id",
        "description",
        "ip_address",
    ]
    readonly_fields = [
        "id",
        "organization",
        "user",
        "action",
        "resource",
        "resource_id",
        "description",
        "old_values",
        "new_values",
        "ip_address",
        "user_agent",
        "metadata",
        "created_at",
    ]
    ordering = ["-created_at"]
    list_per_page = 100
    date_hierarchy = "created_at"

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
        (
            None,
            {
                "fields": ("id", "created_at"),
            },
        ),
        (
            _("Action Details"),
            {
                "fields": ("action", "resource", "resource_id", "description"),
            },
        ),
        (
            _("Context"),
            {
                "fields": ("organization", "user", "ip_address", "user_agent"),
            },
        ),
        (
            _("Data Changes"),
            {
                "fields": ("old_values", "new_values"),
                "classes": ("collapse",),
            },
        ),
        (
            _("Metadata"),
            {
                "fields": ("metadata",),
                "classes": ("collapse",),
            },
        ),
    )

    def action_badge(self, obj):
        """Display action with color-coded badge."""
        colors = {
            "CREATE": "#28a745",
            "UPDATE": "#17a2b8",
            "DELETE": "#dc3545",
            "LOGIN": "#28a745",
            "LOGOUT": "#6c757d",
            "LOGIN_FAILED": "#ffc107",
        }
        color = colors.get(obj.action, "#6c757d")
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-size: 11px; font-weight: bold;">{}</span>',
            color,
            obj.get_action_display(),
        )

    action_badge.short_description = _("Action")
    action_badge.admin_order_field = "action"

    def resource_display(self, obj):
        """Display resource with ID."""
        if obj.resource_id:
            return format_html(
                '<span>{}</span> <code style="background-color: #f1f1f1; '
                'padding: 2px 6px; border-radius: 3px; font-size: 10px;">{}</code>',
                obj.resource,
                obj.resource_id[:8] + "..."
                if len(obj.resource_id) > 8
                else obj.resource_id,
            )
        return obj.resource

    resource_display.short_description = _("Resource")
    resource_display.admin_order_field = "resource"
