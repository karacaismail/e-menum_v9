"""
Shared mixins for the restaurant owner portal.

OrganizationRequiredMixin ensures authenticated access with an organization.
NeverCacheMixin adds no-cache headers to prevent back/forward browser issues.
"""

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.views.decorators.cache import never_cache


class NeverCacheMixin:
    """Add Cache-Control: no-store to prevent browser back/forward caching."""

    @method_decorator(never_cache)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)


class OrganizationRequiredMixin(NeverCacheMixin, LoginRequiredMixin):
    """
    Ensures that the user is authenticated AND has an organization linked.

    - Redirects unauthenticated users to /account/login/
    - Redirects superadmins/staff without organization to /admin/
    - Redirects regular users without organization to /account/profile/
    - Adds no-cache headers to prevent browser back/forward issues
    """

    login_url = "/account/login/"

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()

        # Check if user is being impersonated — use the real user
        is_impersonating = getattr(request, "impersonator", None) is not None

        if not getattr(request.user, "organization", None):
            # Superadmin/staff without org → send back to admin panel
            if request.user.is_superuser or request.user.is_staff:
                if is_impersonating:
                    # Impersonating a user with no org — stop impersonation
                    return redirect("/impersonate/stop/")
                return redirect("/admin/")

            messages.error(request, _("Hesabiniza bagli bir organizasyon bulunamadi."))
            return redirect("accounts:profile")

        return super().dispatch(request, *args, **kwargs)

    def get_organization(self):
        return self.request.user.organization
