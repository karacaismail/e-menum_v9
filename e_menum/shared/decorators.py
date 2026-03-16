"""
Shared view decorators for E-Menum.

Provides access control decorators for Django views (non-DRF).
"""

from functools import wraps

from django.contrib.auth import REDIRECT_FIELD_NAME
from django.contrib.auth.decorators import user_passes_test


def superadmin_required(
    view_func=None,
    redirect_field_name=REDIRECT_FIELD_NAME,
    login_url="/accounts/login/",
):
    """
    Decorator that restricts access to superusers only.

    Use this instead of @staff_member_required for platform-level admin views
    (dashboard, settings, reports, permission matrix, etc.) to prevent
    restaurant admins from accessing the superadmin panel.

    Usage:
        @superadmin_required
        def admin_settings(request):
            ...
    """
    actual_decorator = user_passes_test(
        lambda u: u.is_active and u.is_superuser,
        login_url=login_url,
        redirect_field_name=redirect_field_name,
    )
    if view_func:
        return actual_decorator(view_func)
    return actual_decorator
