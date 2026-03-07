"""
Shared mixins for the restaurant owner portal.

OrganizationRequiredMixin ensures authenticated access with an organization.
"""

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.utils.translation import gettext_lazy as _


class OrganizationRequiredMixin(LoginRequiredMixin):
    """
    Ensures that the user is authenticated AND has an organization linked.

    - Redirects unauthenticated users to /account/login/
    - Redirects users without an organization to /account/profile/
    """

    login_url = "/account/login/"

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if not getattr(request.user, "organization", None):
            messages.error(request, _("Hesabiniza bagli bir organizasyon bulunamadi."))
            return redirect("accounts:profile")
        return super().dispatch(request, *args, **kwargs)

    def get_organization(self):
        return self.request.user.organization
