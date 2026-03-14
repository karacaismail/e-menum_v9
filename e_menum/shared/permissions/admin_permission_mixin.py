"""
Admin permission mixin that bridges E-Menum's custom RBAC/ABAC system
with Django admin's built-in permission checks.

By default, Django admin checks permissions via django.contrib.auth.Permission
(the auth_permission table). E-Menum uses its own Role/Permission/UserRole/
RolePermission models instead. This mixin overrides Django admin's permission
methods to use E-Menum's ability system.

Usage:
    from shared.permissions.admin_permission_mixin import EMenumPermissionMixin

    @admin.register(Menu)
    class MenuAdmin(EMenumPermissionMixin, SoftDeleteAdminMixin, admin.ModelAdmin):
        emenum_resource = 'menu'  # Optional: override auto-detected resource name
        ...

If ``emenum_resource`` is not set, the mixin uses DJANGO_MODEL_TO_RESOURCE
mapping, falling back to model._meta.model_name.
"""

import logging

from shared.permissions.abilities import build_ability_for_user

logger = logging.getLogger(__name__)

# ─── Mapping: Django model_name → E-Menum resource ──────────────────
# Only entries where the names differ are needed here.
# Models NOT listed will use their model_name as-is.
DJANGO_MODEL_TO_RESOURCE = {
    # ── Core ──
    "permission": "role",
    "userrole": "role",
    "rolepermission": "role",
    "session": "audit_log",
    "auditlog": "audit_log",
    # ── Menu ──
    "productvariant": "product",
    "productmodifier": "product",
    "productallergen": "product",
    "allergen": "product",
    "nutritioninfo": "product",
    # ── Orders ──
    "qrcode": "qr_code",
    "qrscan": "qr_code",
    "orderitem": "order",
    "servicerequest": "service_request",
    # ── Customers ──
    "customervisit": "customer",
    "loyaltypoint": "customer",
    # ── Subscriptions ──
    "feature": "plan",
    "planfeature": "plan",
    "featurepermission": "plan",
    "organizationusage": "subscription",
    # ── Inventory ──
    "inventoryitem": "inventory",
    "stockmovement": "inventory",
    "purchaseorder": "inventory",
    "purchaseorderitem": "inventory",
    "recipe": "inventory",
    "recipeingredient": "inventory",
    "supplier": "inventory",
    # ── Campaigns ──
    "coupon": "campaign",
    "couponusage": "campaign",
    "referral": "campaign",
    # ── Analytics ──
    "dashboardmetric": "analytics",
    "salesaggregation": "analytics",
    "productperformance": "analytics",
    "customermetric": "analytics",
    # ── Dashboard ──
    "dashboardinsight": "dashboard",
    "userpreference": "dashboard",
    # ── Reporting ──
    "reportdefinition": "report",
    "reportexecution": "report",
    "reportschedule": "report",
    "reportfavorite": "report",
    # ── Media ──
    "mediafolder": "media",
    # ── AI ──
    "aigeneration": "ai_generation",
    "aiproviderconfig": "ai_generation",
    # ── SEO ──
    "redirect": "settings",
    "notfound404log": "settings",
    "brokenlink": "settings",
    "crawlreport": "settings",
    "txtfileconfig": "settings",
    "authorprofile": "settings",
    "pseotemplate": "settings",
    "pseopage": "settings",
    "trackingintegration": "settings",
    "corewebvitalssnapshot": "settings",
    # ── SEO Shield ──
    "botwhitelist": "settings",
    "ipriskscore": "settings",
    "ruleset": "settings",
    "blocklog": "settings",
    # ── Website CMS ──
    "sitesettings": "settings",
    "pagehero": "settings",
    "homesection": "settings",
    "navigationlink": "settings",
    "featurecategory": "settings",
    "testimonial": "settings",
    "trustbadge": "settings",
    "trustlocation": "settings",
    "teammember": "settings",
    "companyvalue": "settings",
    "companystat": "settings",
    "faq": "settings",
    "blogpost": "settings",
    "legalpage": "settings",
    "plandisplayfeature": "settings",
    "contactsubmission": "settings",
    "demorequest": "settings",
    "newslettersubscriber": "settings",
}


class EMenumPermissionMixin:
    """
    Mixin that overrides Django admin permission checks to use
    E-Menum's custom RBAC/ABAC ability system.

    Place this BEFORE ModelAdmin in MRO:
        class MyAdmin(EMenumPermissionMixin, admin.ModelAdmin): ...

    Attributes:
        emenum_resource (str): Explicit E-Menum resource name.
            If not set, auto-detected from model name + mapping.
    """

    emenum_resource = None  # Override in subclass if needed

    def _get_emenum_resource(self):
        """Resolve E-Menum resource name for this ModelAdmin."""
        if self.emenum_resource:
            return self.emenum_resource
        model_name = self.model._meta.model_name
        return DJANGO_MODEL_TO_RESOURCE.get(model_name, model_name)

    def _build_ability(self, request):
        """
        Build (or retrieve cached) ability for the requesting user.

        Caches the Ability on the request object to avoid repeated
        DB queries within the same request cycle.
        """
        # Cache key on request to avoid rebuilding per ModelAdmin instance
        cache_attr = "_emenum_ability"
        if hasattr(request, cache_attr):
            return getattr(request, cache_attr)

        user = request.user
        organization = getattr(user, "organization", None)
        ability = build_ability_for_user(user, organization)
        setattr(request, cache_attr, ability)
        return ability

    def _check_emenum_permission(self, request, action, obj=None):
        """
        Check if the user has E-Menum permission for the given action.

        Returns True if:
        - User is superuser (Django fast-path)
        - User has ability.can(action, resource)
        - User has ability.can('manage', resource) (catch-all)
        """
        user = request.user
        if not user.is_authenticated:
            return False
        if user.is_superuser:
            return True

        try:
            ability = self._build_ability(request)
            resource = self._get_emenum_resource()
            return ability.can(action, resource)
        except Exception:
            logger.exception(
                "Permission check failed for %s on %s.%s",
                user.email,
                self._get_emenum_resource(),
                action,
            )
            return False

    # ─── Django Admin Permission Overrides ───────────────────────────

    def has_module_permission(self, request):
        """
        Controls whether the model appears in the admin index.
        Maps to E-Menum 'view' or 'list' permission.
        """
        if not request.user.is_authenticated:
            return False
        if request.user.is_superuser:
            return True
        return self._check_emenum_permission(
            request, "view"
        ) or self._check_emenum_permission(request, "list")

    def has_view_permission(self, request, obj=None):
        """
        Controls access to the changelist and detail views.
        Maps to E-Menum 'view' permission.
        """
        if request.user.is_superuser:
            return True
        return self._check_emenum_permission(request, "view", obj)

    def has_add_permission(self, request):
        """
        Controls the "Add" button and add form.
        Maps to E-Menum 'create' permission.
        """
        if request.user.is_superuser:
            return True
        return self._check_emenum_permission(request, "create")

    def has_change_permission(self, request, obj=None):
        """
        Controls the edit/change form.
        Maps to E-Menum 'update' permission.
        """
        if request.user.is_superuser:
            return True
        return self._check_emenum_permission(request, "update", obj)

    def has_delete_permission(self, request, obj=None):
        """
        Controls the delete action/button.
        Maps to E-Menum 'delete' permission.
        """
        if request.user.is_superuser:
            return True
        return self._check_emenum_permission(request, "delete", obj)
