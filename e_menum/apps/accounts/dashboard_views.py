"""
Dashboard views for the restaurant owner portal.

Provides the main dashboard page and API endpoints for KPI data.
"""

import json
import logging

from django.http import JsonResponse
from django.shortcuts import render
from django.views import View
from django.views.decorators.http import require_GET

from .dashboard_services import OwnerKPIService
from .mixins import OrganizationRequiredMixin

logger = logging.getLogger(__name__)


class DashboardView(OrganizationRequiredMixin, View):
    """Restaurant owner dashboard — KPIs, charts, recent orders, quick actions."""

    template_name = "accounts/dashboard.html"

    def get(self, request):
        org = self.get_organization()
        service = OwnerKPIService(org)

        # Server-side render initial KPI data for fast paint
        kpis = service.get_all_kpis()
        recent_orders = service.get_recent_orders(limit=5)

        # Onboarding checklist: check completion status for each step
        onboarding_steps = self._get_onboarding_steps(org)

        context = {
            "kpis": kpis,
            "recent_orders": recent_orders,
            "kpis_json": json.dumps(kpis, default=str),
            "onboarding_steps": onboarding_steps,
            "onboarding_complete": all(s["done"] for s in onboarding_steps),
        }
        return render(request, self.template_name, context)

    def _get_onboarding_steps(self, org):
        """Build onboarding checklist status for the given organization."""
        from apps.menu.models import Menu, Product
        from apps.orders.models import QRCode

        has_restaurant_info = bool(org.name and org.phone)
        has_menu = Menu.objects.filter(
            organization=org, deleted_at__isnull=True
        ).exists()
        has_product = Product.objects.filter(
            organization=org, deleted_at__isnull=True
        ).exists()
        has_qr = QRCode.objects.filter(
            organization=org, deleted_at__isnull=True
        ).exists()

        return [
            {
                "key": "restaurant",
                "done": has_restaurant_info,
                "url": "accounts:restaurant-settings",
            },
            {"key": "menu", "done": has_menu, "url": "accounts:menu-create"},
            {"key": "product", "done": has_product, "url": "accounts:product-create"},
            {"key": "qrcode", "done": has_qr, "url": "accounts:qrcode-list"},
        ]


# ─── API endpoints (AJAX / JSON) ────────────────────────────────────────────


def _get_org_or_403(request):
    """Helper: return organization or None (caller returns 403)."""
    if not request.user.is_authenticated:
        return None
    return getattr(request.user, "organization", None)


@require_GET
def dashboard_kpis_api(request):
    """GET /account/api/dashboard/kpis/ — all KPI cards."""
    org = _get_org_or_403(request)
    if not org:
        return JsonResponse({"error": "Unauthorized"}, status=403)
    service = OwnerKPIService(org)
    return JsonResponse(service.get_all_kpis())


@require_GET
def dashboard_qr_trend_api(request):
    """GET /account/api/dashboard/qr-trend/ — daily QR scan counts."""
    org = _get_org_or_403(request)
    if not org:
        return JsonResponse({"error": "Unauthorized"}, status=403)
    days = int(request.GET.get("days", 30))
    days = min(days, 90)
    service = OwnerKPIService(org)
    return JsonResponse(service.get_qr_scan_trend(days=days))


@require_GET
def dashboard_revenue_api(request):
    """GET /account/api/dashboard/revenue/ — daily revenue totals."""
    org = _get_org_or_403(request)
    if not org:
        return JsonResponse({"error": "Unauthorized"}, status=403)
    days = int(request.GET.get("days", 30))
    days = min(days, 90)
    service = OwnerKPIService(org)
    return JsonResponse(service.get_revenue_trend(days=days))


@require_GET
def dashboard_orders_chart_api(request):
    """GET /account/api/dashboard/orders-chart/ — order status distribution."""
    org = _get_org_or_403(request)
    if not org:
        return JsonResponse({"error": "Unauthorized"}, status=403)
    service = OwnerKPIService(org)
    return JsonResponse(service.get_order_status_distribution())


@require_GET
def dashboard_top_products_api(request):
    """GET /account/api/dashboard/top-products/ — top 10 products by orders."""
    org = _get_org_or_403(request)
    if not org:
        return JsonResponse({"error": "Unauthorized"}, status=403)
    service = OwnerKPIService(org)
    return JsonResponse({"products": service.get_top_products()}, safe=False)


@require_GET
def dashboard_recent_orders_api(request):
    """GET /account/api/dashboard/recent-orders/ — last 10 orders."""
    org = _get_org_or_403(request)
    if not org:
        return JsonResponse({"error": "Unauthorized"}, status=403)
    service = OwnerKPIService(org)
    return JsonResponse({"orders": service.get_recent_orders()})
