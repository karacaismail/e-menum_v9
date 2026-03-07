"""
Dashboard API views for the admin mainboard.

All endpoints:
- Require staff authentication (@staff_member_required)
- Return JsonResponse
- Accept GET parameter: ?range=7d|30d|90d (default 30d)
- Are independent (one failure doesn't affect others)
"""

import logging

from django.contrib.admin.models import LogEntry
from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_GET

from apps.dashboard.services import KPIService

logger = logging.getLogger(__name__)


def _parse_range(request) -> int:
    """Parse ?range= parameter into number of days."""
    range_param = request.GET.get("range", "30d")
    mapping = {"7d": 7, "30d": 30, "90d": 90}
    return mapping.get(range_param, 30)


@staff_member_required
@require_GET
def api_kpis(request):
    """
    GET /admin/api/kpis/
    Returns 6 KPI metrics with trend data and week-over-week change.
    """
    try:
        service = KPIService()

        kpis = {
            "organizations": {
                "value": service.get_active_organizations(),
                "trend": service.get_trend("organizations", days=7),
                "change": service.get_period_comparison("organizations")["change"],
                "label": "Aktif Organizasyonlar",
                "icon": "buildings",
            },
            "qr_scans": {
                "value": service.get_today_qr_scans(),
                "trend": service.get_trend("qr_scans", days=7),
                "change": service.get_period_comparison("qr_scans")["change"],
                "label": "Bugünkü QR Taramalar",
                "icon": "qr-code",
            },
            "active_menus": {
                "value": service.get_active_menus(),
                "trend": service.get_trend("menus", days=7),
                "change": service.get_period_comparison("menus")["change"],
                "label": "Aktif Menüler",
                "icon": "book-open",
            },
            "pending_requests": {
                "value": service.get_pending_service_requests(),
                "trend": service.get_trend("service_requests", days=7),
                "change": service.get_period_comparison("service_requests")["change"],
                "label": "Bekleyen Talepler",
                "icon": "bell-ringing",
            },
            "mrr": {
                "value": service.get_mrr(),
                "trend": service.get_trend("revenue", days=7),
                "change": service.get_period_comparison("revenue")["change"],
                "label": "Aylık Gelir (MRR)",
                "icon": "currency-circle-dollar",
                "format": "currency",
            },
            "trial_count": {
                "value": service.get_trial_count(),
                "trend": service.get_trend("organizations", days=7),
                "change": 0,
                "label": "Aktif Deneme",
                "icon": "hourglass",
            },
        }

        return JsonResponse({"success": True, "data": kpis})
    except Exception as exc:
        logger.error("KPI API failed: %s", exc, exc_info=True)
        return JsonResponse(
            {"success": False, "error": str(exc)},
            status=500,
        )


@staff_member_required
@require_GET
def api_qr_scan_trend(request):
    """
    GET /admin/api/qr-scan-trend/?range=30d
    Daily QR scan counts for line chart.
    """
    try:
        days = _parse_range(request)
        service = KPIService()
        data = service.get_qr_scan_trend(days=days)
        return JsonResponse({"success": True, "data": data})
    except Exception as exc:
        logger.error("QR scan trend API failed: %s", exc, exc_info=True)
        return JsonResponse(
            {"success": False, "error": str(exc)},
            status=500,
        )


@staff_member_required
@require_GET
def api_org_activity_heatmap(request):
    """
    GET /admin/api/org-activity-heatmap/
    Last 12 weeks org × day activity matrix (top 20 orgs).
    """
    try:
        service = KPIService()
        data = service.get_org_activity_heatmap()
        return JsonResponse({"success": True, "data": data})
    except Exception as exc:
        logger.error("Heatmap API failed: %s", exc, exc_info=True)
        return JsonResponse(
            {"success": False, "error": str(exc)},
            status=500,
        )


@staff_member_required
@require_GET
def api_plan_distribution(request):
    """
    GET /admin/api/plan-distribution/
    Organization count per plan tier (donut chart).
    """
    try:
        service = KPIService()
        data = service.get_plan_distribution()
        return JsonResponse({"success": True, "data": data})
    except Exception as exc:
        logger.error("Plan distribution API failed: %s", exc, exc_info=True)
        return JsonResponse(
            {"success": False, "error": str(exc)},
            status=500,
        )


@staff_member_required
@require_GET
def api_city_distribution(request):
    """
    GET /admin/api/city-distribution/
    City-based organization counts with coordinates.
    """
    try:
        service = KPIService()
        data = service.get_city_distribution()
        return JsonResponse({"success": True, "data": data})
    except Exception as exc:
        logger.error("City distribution API failed: %s", exc, exc_info=True)
        return JsonResponse(
            {"success": False, "error": str(exc)},
            status=500,
        )


@staff_member_required
@require_GET
def api_insights(request):
    """
    GET /admin/api/insights/
    Active dashboard insights (max 5, priority DESC).
    """
    try:
        from apps.dashboard.models import DashboardInsight

        now = timezone.now()

        # Deactivate expired
        DashboardInsight.objects.filter(
            is_active=True,
            expires_at__lt=now,
            deleted_at__isnull=True,
        ).update(is_active=False)

        insights = DashboardInsight.objects.filter(
            is_active=True,
            deleted_at__isnull=True,
        ).order_by("-priority", "-created_at")[:5]

        data = [
            {
                "id": str(i.id),
                "type": i.type,
                "title": i.title,
                "body": i.body,
                "action_label": i.action_label,
                "action_url": i.action_url,
                "metric_value": float(i.metric_value) if i.metric_value else None,
                "metric_label": i.metric_label,
                "priority": i.priority,
                "created_at": i.created_at.isoformat(),
            }
            for i in insights
        ]

        return JsonResponse({"success": True, "data": data})
    except Exception as exc:
        logger.error("Insights API failed: %s", exc, exc_info=True)
        return JsonResponse(
            {"success": False, "error": str(exc)},
            status=500,
        )


@staff_member_required
@require_GET
def api_recent_activity(request):
    """
    GET /admin/api/recent-activity/
    Last 20 admin log entries.
    """
    try:
        entries = LogEntry.objects.select_related(
            "user",
            "content_type",
        ).order_by("-action_time")[:20]

        ACTION_MAP = {1: "add", 2: "change", 3: "delete"}

        data = [
            {
                "user": entry.user.get_username() if entry.user else "system",
                "user_initial": (
                    entry.user.get_username()[:1].upper() if entry.user else "S"
                ),
                "action": ACTION_MAP.get(entry.action_flag, "unknown"),
                "model": entry.content_type.model if entry.content_type else "",
                "app": entry.content_type.app_label if entry.content_type else "",
                "object_repr": entry.object_repr[:80],
                "timestamp": entry.action_time.isoformat(),
                "url": entry.get_admin_url() if not entry.is_deletion() else None,
            }
            for entry in entries
        ]

        return JsonResponse({"success": True, "data": data})
    except Exception as exc:
        logger.error("Recent activity API failed: %s", exc, exc_info=True)
        return JsonResponse(
            {"success": False, "error": str(exc)},
            status=500,
        )


@staff_member_required
@require_GET
def api_subscription_funnel(request):
    """
    GET /admin/api/subscription-funnel/
    Conversion funnel: Registration → Trial → Active → Renewal.
    """
    try:
        service = KPIService()
        data = service.get_subscription_funnel()
        return JsonResponse({"success": True, "data": data})
    except Exception as exc:
        logger.error("Subscription funnel API failed: %s", exc, exc_info=True)
        return JsonResponse(
            {"success": False, "error": str(exc)},
            status=500,
        )


@staff_member_required
@require_GET
def api_search(request):
    """
    GET /admin/api/search/?q=<query>
    Command palette search across organizations, users, menus.
    Minimum 2 characters required.
    """
    try:
        q = request.GET.get("q", "").strip()
        if len(q) < 2:
            return JsonResponse(
                {
                    "success": True,
                    "data": {"groups": []},
                }
            )

        groups = []

        # Search Organizations
        try:
            from apps.core.models import Organization

            orgs = Organization.objects.filter(
                name__icontains=q,
                deleted_at__isnull=True,
            )[:5]
            if orgs.exists():
                groups.append(
                    {
                        "label": "Organizasyonlar",
                        "icon": "buildings",
                        "items": [
                            {
                                "title": org.name,
                                "subtitle": org.email or org.slug,
                                "url": f"/admin/core/organization/{org.pk}/change/",
                            }
                            for org in orgs
                        ],
                    }
                )
        except Exception:
            pass

        # Search Users
        try:
            from apps.core.models import User
            from django.db.models import Q

            users = User.objects.filter(
                Q(email__icontains=q)
                | Q(first_name__icontains=q)
                | Q(last_name__icontains=q),
                deleted_at__isnull=True,
            )[:5]
            if users.exists():
                groups.append(
                    {
                        "label": "Kullanıcılar",
                        "icon": "users",
                        "items": [
                            {
                                "title": user.get_username(),
                                "subtitle": user.email,
                                "url": f"/admin/core/user/{user.pk}/change/",
                            }
                            for user in users
                        ],
                    }
                )
        except Exception:
            pass

        # Search Menus
        try:
            from apps.menu.models import Menu

            menus = Menu.objects.filter(
                name__icontains=q,
                deleted_at__isnull=True,
            )[:5]
            if menus.exists():
                groups.append(
                    {
                        "label": "Menüler",
                        "icon": "book-open",
                        "items": [
                            {
                                "title": menu.name,
                                "subtitle": str(menu.organization)
                                if menu.organization
                                else "",
                                "url": f"/admin/menu/menu/{menu.pk}/change/",
                            }
                            for menu in menus
                        ],
                    }
                )
        except Exception:
            pass

        return JsonResponse(
            {
                "success": True,
                "data": {"groups": groups},
            }
        )
    except Exception as exc:
        logger.error("Search API failed: %s", exc, exc_info=True)
        return JsonResponse(
            {"success": False, "error": str(exc)},
            status=500,
        )


@staff_member_required
@require_GET
def api_sidebar_pins(request):
    """
    GET /admin/api/sidebar/pins/
    Get user's pinned sidebar items.
    """
    try:
        from apps.dashboard.models import UserPreference

        pref, _ = UserPreference.objects.get_or_create(
            user=request.user,
            key="sidebar_pins",
            defaults={"value": {"pins": []}},
        )
        return JsonResponse({"success": True, "data": pref.value})
    except Exception as exc:
        logger.error("Sidebar pins API failed: %s", exc, exc_info=True)
        return JsonResponse({"success": False, "error": str(exc)}, status=500)


@staff_member_required
def api_sidebar_pins_save(request):
    """
    POST /admin/api/sidebar/pins/save/
    Save user's pinned sidebar items.
    Body: {"pins": ["/admin/core/organization/", ...]}
    """
    if request.method != "POST":
        return JsonResponse({"success": False, "error": "POST required"}, status=405)

    try:
        import json

        body = json.loads(request.body)
        from apps.dashboard.models import UserPreference

        pref, _ = UserPreference.objects.update_or_create(
            user=request.user,
            key="sidebar_pins",
            defaults={"value": body},
        )
        return JsonResponse({"success": True})
    except Exception as exc:
        logger.error("Sidebar pins save failed: %s", exc, exc_info=True)
        return JsonResponse({"success": False, "error": str(exc)}, status=500)


@staff_member_required
@require_GET
def api_sidebar_recent(request):
    """
    GET /admin/api/sidebar/recent/
    Get user's recently visited admin pages.
    """
    try:
        from apps.dashboard.models import UserPreference

        pref, _ = UserPreference.objects.get_or_create(
            user=request.user,
            key="recent_pages",
            defaults={"value": {"pages": []}},
        )
        return JsonResponse({"success": True, "data": pref.value})
    except Exception as exc:
        logger.error("Sidebar recent API failed: %s", exc, exc_info=True)
        return JsonResponse({"success": False, "error": str(exc)}, status=500)


@staff_member_required
def api_sidebar_recent_save(request):
    """
    POST /admin/api/sidebar/recent/save/
    Record a page visit. Keeps max 5 entries.
    Body: {"url": "/admin/core/organization/", "label": "Organizations"}
    """
    if request.method != "POST":
        return JsonResponse({"success": False, "error": "POST required"}, status=405)

    try:
        import json

        body = json.loads(request.body)
        from apps.dashboard.models import UserPreference

        pref, _ = UserPreference.objects.get_or_create(
            user=request.user,
            key="recent_pages",
            defaults={"value": {"pages": []}},
        )

        pages = pref.value.get("pages", [])

        # Remove duplicate
        new_entry = {"url": body.get("url", ""), "label": body.get("label", "")}
        pages = [p for p in pages if p.get("url") != new_entry["url"]]

        # Prepend and limit to 5
        pages.insert(0, new_entry)
        pages = pages[:5]

        pref.value = {"pages": pages}
        pref.save()

        return JsonResponse({"success": True})
    except Exception as exc:
        logger.error("Sidebar recent save failed: %s", exc, exc_info=True)
        return JsonResponse({"success": False, "error": str(exc)}, status=500)
