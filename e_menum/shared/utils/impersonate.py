"""
Impersonation utility functions for django-impersonate.

Defines who can impersonate (superusers and platform admins)
and who can be impersonated (non-superuser organization users).

Used by IMPERSONATE settings in config/settings/base.py.
"""


def can_impersonate(request):
    """
    Check if the current user is allowed to impersonate other users.

    Only superusers and staff members can impersonate.
    This prevents regular organization users from impersonating each other.

    Args:
        request: Django HTTP request with authenticated user

    Returns:
        bool: True if the user can impersonate
    """
    if not request.user.is_authenticated:
        return False
    # Superusers can always impersonate
    if request.user.is_superuser:
        return True
    # Staff members (platform admins) can impersonate
    if request.user.is_staff:
        return True
    return False


def get_impersonatable_users(request):
    """
    Return a queryset of users that can be impersonated.

    Superusers cannot be impersonated (security measure).
    Only active, non-deleted users can be impersonated.

    Args:
        request: Django HTTP request

    Returns:
        QuerySet: Users that can be impersonated
    """
    from apps.core.models import User

    return User.objects.filter(
        is_superuser=False,
        status='ACTIVE',
        deleted_at__isnull=True,
    ).select_related('organization')
