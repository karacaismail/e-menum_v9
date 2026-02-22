"""
Django TextChoices enums for core module.

These enums define the valid values for status fields and other constrained
string fields across the core domain models (Organization, User, Branch, Role, etc.).

Usage:
    from apps.core.choices import OrganizationStatus, UserStatus

    class Organization(models.Model):
        status = models.CharField(
            max_length=20,
            choices=OrganizationStatus.choices,
            default=OrganizationStatus.ACTIVE
        )
"""

from django.db import models
from django.utils.translation import gettext_lazy as _


class OrganizationStatus(models.TextChoices):
    """
    Status values for Organization (tenant) lifecycle.

    - ACTIVE: Organization is in good standing and fully operational
    - SUSPENDED: Organization is temporarily disabled (unpaid bills, violation, etc.)
    - DELETED: Organization is soft-deleted (retained for audit, not operational)
    """
    ACTIVE = 'ACTIVE', 'Active'
    SUSPENDED = 'SUSPENDED', 'Suspended'
    DELETED = 'DELETED', 'Deleted'


class UserStatus(models.TextChoices):
    """
    Status values for User account lifecycle.

    - ACTIVE: User is verified and can access the system
    - INVITED: User has been invited but hasn't completed registration
    - SUSPENDED: User account is temporarily disabled
    """
    ACTIVE = 'ACTIVE', 'Active'
    INVITED = 'INVITED', 'Invited'
    SUSPENDED = 'SUSPENDED', 'Suspended'


class BranchStatus(models.TextChoices):
    """
    Status values for Branch (physical location) lifecycle.

    - ACTIVE: Branch is operational and accepting orders
    - INACTIVE: Branch is temporarily closed (seasonal, renovation, etc.)
    - SUSPENDED: Branch is suspended by the platform (violation, unpaid bills)
    """
    ACTIVE = 'ACTIVE', 'Active'
    INACTIVE = 'INACTIVE', 'Inactive'
    SUSPENDED = 'SUSPENDED', 'Suspended'


class RoleScope(models.TextChoices):
    """
    Scope values for Role definitions.

    - PLATFORM: System-wide roles (super_admin, admin, sales, support)
    - ORGANIZATION: Organization-scoped roles (owner, manager, staff, viewer)
    """
    PLATFORM = 'PLATFORM', 'Platform'
    ORGANIZATION = 'ORGANIZATION', 'Organization'


class AuditAction(models.TextChoices):
    """
    Action types for AuditLog entries.

    Captures what type of operation was performed on a resource.
    Used for compliance, debugging, and security analysis.
    """
    # CRUD Operations
    CREATE = 'CREATE', 'Create'
    READ = 'READ', 'Read'
    UPDATE = 'UPDATE', 'Update'
    DELETE = 'DELETE', 'Delete'

    # Authentication Actions
    LOGIN = 'LOGIN', 'Login'
    LOGOUT = 'LOGOUT', 'Logout'
    LOGIN_FAILED = 'LOGIN_FAILED', 'Login Failed'
    PASSWORD_CHANGE = 'PASSWORD_CHANGE', 'Password Change'
    PASSWORD_RESET = 'PASSWORD_RESET', 'Password Reset'

    # Authorization Actions
    PERMISSION_GRANT = 'PERMISSION_GRANT', 'Permission Grant'
    PERMISSION_REVOKE = 'PERMISSION_REVOKE', 'Permission Revoke'
    ROLE_ASSIGN = 'ROLE_ASSIGN', 'Role Assign'
    ROLE_REMOVE = 'ROLE_REMOVE', 'Role Remove'

    # Account Actions
    INVITE_SENT = 'INVITE_SENT', 'Invite Sent'
    INVITE_ACCEPTED = 'INVITE_ACCEPTED', 'Invite Accepted'
    ACCOUNT_SUSPENDED = 'ACCOUNT_SUSPENDED', 'Account Suspended'
    ACCOUNT_ACTIVATED = 'ACCOUNT_ACTIVATED', 'Account Activated'

    # Data Operations
    EXPORT = 'EXPORT', 'Export'
    IMPORT = 'IMPORT', 'Import'
    BULK_UPDATE = 'BULK_UPDATE', 'Bulk Update'
    BULK_DELETE = 'BULK_DELETE', 'Bulk Delete'

    # Subscription Actions
    SUBSCRIPTION_CREATED = 'SUBSCRIPTION_CREATED', 'Subscription Created'
    SUBSCRIPTION_UPDATED = 'SUBSCRIPTION_UPDATED', 'Subscription Updated'
    SUBSCRIPTION_CANCELLED = 'SUBSCRIPTION_CANCELLED', 'Subscription Cancelled'

    # System Actions
    SETTINGS_UPDATED = 'SETTINGS_UPDATED', 'Settings Updated'
    API_KEY_CREATED = 'API_KEY_CREATED', 'API Key Created'
    API_KEY_REVOKED = 'API_KEY_REVOKED', 'API Key Revoked'


class SessionStatus(models.TextChoices):
    """
    Status values for user Session (JWT refresh token) lifecycle.

    - ACTIVE: Session is valid and can be used for token refresh
    - EXPIRED: Session has expired naturally
    - REVOKED: Session was explicitly revoked (logout, security)
    """
    ACTIVE = 'ACTIVE', 'Active'
    EXPIRED = 'EXPIRED', 'Expired'
    REVOKED = 'REVOKED', 'Revoked'


class PermissionAction(models.TextChoices):
    """
    Standard permission actions following resource.action pattern.

    Used with Permission model to define granular access control.
    Example: 'menu.create', 'order.view', 'user.delete'
    """
    VIEW = 'view', 'View'
    LIST = 'list', 'List'
    CREATE = 'create', 'Create'
    UPDATE = 'update', 'Update'
    DELETE = 'delete', 'Delete'
    MANAGE = 'manage', 'Manage'  # Full access to a resource
    PUBLISH = 'publish', 'Publish'
    EXPORT = 'export', 'Export'
    IMPORT = 'import', 'Import'


class ShiftType(models.TextChoices):
    """
    Type values for staff shifts.

    - MORNING: Morning shift
    - AFTERNOON: Afternoon shift
    - EVENING: Evening shift
    - NIGHT: Night shift
    - CUSTOM: Custom/flexible shift
    """
    MORNING = 'MORNING', _('Morning')
    AFTERNOON = 'AFTERNOON', _('Afternoon')
    EVENING = 'EVENING', _('Evening')
    NIGHT = 'NIGHT', _('Night')
    CUSTOM = 'CUSTOM', _('Custom')


class ScheduleStatus(models.TextChoices):
    """
    Status values for staff schedule entries.

    - SCHEDULED: Staff is scheduled for this shift
    - CHECKED_IN: Staff has checked in for the shift
    - CHECKED_OUT: Staff has checked out after the shift
    - ABSENT: Staff was absent for the shift
    - LATE: Staff arrived late for the shift
    """
    SCHEDULED = 'SCHEDULED', _('Scheduled')
    CHECKED_IN = 'CHECKED_IN', _('Checked In')
    CHECKED_OUT = 'CHECKED_OUT', _('Checked Out')
    ABSENT = 'ABSENT', _('Absent')
    LATE = 'LATE', _('Late')
