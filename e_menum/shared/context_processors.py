"""
Custom context processors for the E-Menum admin interface.

Provides permission-aware data to templates so the sidebar
can dynamically show/hide items based on the current user's
(or impersonated user's) E-Menum RBAC/ABAC permissions.

The bridge between E-Menum's custom permission system
(Role/Permission/UserRole/RolePermission) and Django admin's
sidebar visibility is handled here.
"""

import json
import logging

from django.conf import settings

from shared.permissions.abilities import build_ability_for_user


def debug_context(request):
    """
    Always add 'debug' to template context.

    Django's debug context processor only adds it when DEBUG is True and
    request IP is in INTERNAL_IPS. Base layout (base.html) uses {% if debug %}
    for Tailwind CDN vs built CSS, so we need it always defined.
    """
    return {"debug": getattr(settings, "DEBUG", False)}


def platform_info(request):
    """
    Provide Django/Python version info for the admin dashboard.
    Only computed for staff users on admin pages.
    """
    import sys

    import django

    if not getattr(request, "path", "").startswith("/admin"):
        return {}
    return {
        "django_version": django.get_version(),
        "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
    }


logger = logging.getLogger(__name__)

# ─── Mapping: Admin URL → E-Menum Resource ──────────────────────────
# Maps Django admin URL patterns to E-Menum permission resource names.
# The context processor checks if the user can 'view' or 'list' the resource.
# Format: '/admin/{app_label}/{model_name}/' → 'resource_name'

ADMIN_URL_TO_RESOURCE = {
    # ── Core ──
    "/admin/core/organization/": "organization",
    "/admin/core/branch/": "branch",
    "/admin/core/user/": "user",
    "/admin/core/role/": "role",
    "/admin/core/permission/": "role",  # Permission mgmt needs role access
    "/admin/core/rolepermission/": "role",  # Role-Permission mapping
    "/admin/core/userrole/": "role",  # User-Role assignments
    "/admin/core/session/": "audit_log",  # Sessions ≈ audit trail
    "/admin/core/auditlog/": "audit_log",
    # ── Menu ──
    "/admin/menu/menu/": "menu",
    "/admin/menu/category/": "category",
    "/admin/menu/product/": "product",
    "/admin/menu/productvariant/": "product",  # Variants are part of product
    "/admin/menu/productmodifier/": "product",  # Modifiers are part of product
    "/admin/menu/allergen/": "product",  # Allergens relate to product
    "/admin/menu/productallergen/": "product",
    "/admin/menu/nutritioninfo/": "product",
    "/admin/menu/theme/": "theme",
    # ── Orders ──
    "/admin/orders/zone/": "zone",
    "/admin/orders/table/": "table",
    "/admin/orders/qrcode/": "qr_code",
    "/admin/orders/qrscan/": "qr_code",
    "/admin/orders/order/": "order",
    "/admin/orders/orderitem/": "order",
    "/admin/orders/servicerequest/": "service_request",
    # ── Customers ──
    "/admin/customers/customer/": "customer",
    "/admin/customers/customervisit/": "customer",
    "/admin/customers/feedback/": "feedback",
    "/admin/customers/loyaltypoint/": "customer",
    # ── Subscriptions ──
    "/admin/subscriptions/plan/": "plan",
    "/admin/subscriptions/feature/": "plan",
    "/admin/subscriptions/planfeature/": "plan",
    "/admin/subscriptions/featurepermission/": "plan",
    "/admin/subscriptions/subscription/": "subscription",
    "/admin/subscriptions/invoice/": "invoice",
    "/admin/subscriptions/organizationusage/": "subscription",
    # ── Inventory ──
    "/admin/inventory/supplier/": "inventory",
    "/admin/inventory/inventoryitem/": "inventory",
    "/admin/inventory/stockmovement/": "inventory",
    "/admin/inventory/purchaseorder/": "inventory",
    "/admin/inventory/purchaseorderitem/": "inventory",
    "/admin/inventory/recipe/": "inventory",
    "/admin/inventory/recipeingredient/": "inventory",
    # ── Campaigns ──
    "/admin/campaigns/campaign/": "campaign",
    "/admin/campaigns/coupon/": "campaign",
    "/admin/campaigns/couponusage/": "campaign",
    "/admin/campaigns/referral/": "campaign",
    # ── Analytics ──
    "/admin/analytics/dashboardmetric/": "analytics",
    "/admin/analytics/salesaggregation/": "analytics",
    "/admin/analytics/productperformance/": "analytics",
    "/admin/analytics/customermetric/": "analytics",
    # ── Dashboard ──
    "/admin/dashboard/dashboardinsight/": "dashboard",
    "/admin/dashboard/userpreference/": "dashboard",
    # ── Reporting ──
    "/admin/reporting/reportdefinition/": "report",
    "/admin/reporting/reportexecution/": "report",
    "/admin/reporting/reportschedule/": "report",
    "/admin/reporting/reportfavorite/": "report",
    # ── AI ──
    "/admin/ai/aiproviderconfig/": "ai_generation",
    "/admin/ai/aigeneration/": "ai_generation",
    # ── Media ──
    "/admin/media/media/": "media",
    "/admin/media/mediafolder/": "media",
    # ── Notifications ──
    "/admin/notifications/notification/": "notification",
    # ── SEO ──
    "/admin/seo/redirect/": "settings",
    "/admin/seo/notfound404log/": "settings",
    "/admin/seo/brokenlink/": "settings",
    "/admin/seo/crawlreport/": "settings",
    "/admin/seo/txtfileconfig/": "settings",
    "/admin/seo/authorprofile/": "settings",
    "/admin/seo/pseotemplate/": "settings",
    "/admin/seo/pseopage/": "settings",
    # ── SEO Shield ──
    "/admin/seo_shield/botwhitelist/": "settings",
    "/admin/seo_shield/ipriskscore/": "settings",
    "/admin/seo_shield/ruleset/": "settings",
    "/admin/seo_shield/blocklog/": "settings",
    # ── Website CMS ──
    "/admin/website/sitesettings/": "settings",
    "/admin/website/pagehero/": "settings",
    "/admin/website/homesection/": "settings",
    "/admin/website/navigationlink/": "settings",
    "/admin/website/featurecategory/": "settings",
    "/admin/website/testimonial/": "settings",
    "/admin/website/trustbadge/": "settings",
    "/admin/website/trustlocation/": "settings",
    "/admin/website/teammember/": "settings",
    "/admin/website/companyvalue/": "settings",
    "/admin/website/companystat/": "settings",
    "/admin/website/faq/": "settings",
    "/admin/website/blogpost/": "settings",
    "/admin/website/legalpage/": "settings",
    "/admin/website/plandisplayfeature/": "settings",
    "/admin/website/contactsubmission/": "settings",
    "/admin/website/demorequest/": "settings",
    "/admin/website/newslettersubscriber/": "settings",
}

# Resources that only platform-level (superuser/admin) roles should see.
# Organization-scoped roles should NOT have these unless explicitly granted.
PLATFORM_ONLY_RESOURCES = {
    "role",
    "plan",
    "audit_log",
}


def admin_sidebar_permissions(request):
    """
    Build a JSON-safe set of allowed admin URLs for the current user,
    using E-Menum's custom RBAC/ABAC permission system.

    This powers the sidebar filtering: items whose URL is not in
    ``allowed_admin_urls`` will be hidden via JavaScript.

    The function:
    1. Checks if the user is authenticated staff
    2. Superusers get '__all__' (see everything)
    3. For other staff, builds an Ability from their E-Menum roles
    4. Maps each sidebar admin URL to an E-Menum resource
    5. Checks ability.can('view', resource) OR ability.can('list', resource)
    6. Returns the list of allowed URLs as JSON

    Only runs for admin pages to avoid unnecessary DB queries.
    """
    if not hasattr(request, "user") or not request.user.is_authenticated:
        return {}

    # Only compute for admin pages
    if not request.path.startswith("/admin/"):
        return {}

    if not request.user.is_staff:
        return {"allowed_admin_urls_json": json.dumps([])}

    # Superusers see everything
    if request.user.is_superuser:
        return {"allowed_admin_urls_json": json.dumps(["__all__"])}

    # ── Build E-Menum ability for this user ──
    # Get the user's organization (could be None for platform users)
    organization = getattr(request.user, "organization", None)

    try:
        ability = build_ability_for_user(request.user, organization)
    except Exception:
        logger.exception("Failed to build ability for user %s", request.user.email)
        return {"allowed_admin_urls_json": json.dumps([])}

    # ── Check each admin URL against E-Menum permissions ──
    allowed_urls = set()

    for admin_url, resource in ADMIN_URL_TO_RESOURCE.items():
        # Check if the user can view or list this resource
        if (
            ability.can("view", resource)
            or ability.can("list", resource)
            or ability.can("manage", resource)
        ):
            allowed_urls.add(admin_url)

    logger.debug(
        "Sidebar permissions for %s: %d/%d URLs allowed (org=%s, rules=%d)",
        request.user.email,
        len(allowed_urls),
        len(ADMIN_URL_TO_RESOURCE),
        organization,
        len(ability.rules),
    )

    return {
        "allowed_admin_urls_json": json.dumps(sorted(allowed_urls)),
    }
