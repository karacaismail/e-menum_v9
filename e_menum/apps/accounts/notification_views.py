"""Notification API views for the restaurant owner portal navbar widget.

Provides lightweight JSON endpoints for:
- Unread notification count (polling)
- Recent notifications list (max 12, with tab filtering)
- Mark notification as read
- Mark all notifications as read

All views use session auth (login_required) and filter by organization.
"""

import logging

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_GET, require_POST

logger = logging.getLogger(__name__)


def _get_org(request):
    return getattr(request.user, "organization", None)


@login_required(login_url="/account/login/")
@require_GET
def notification_unread_count(request):
    """Return unread notification count for the current user."""
    org = _get_org(request)
    if not org:
        return JsonResponse({"count": 0})

    from apps.notifications.models import Notification

    count = Notification.objects.filter(
        organization=org,
        user=request.user,
        status="UNREAD",
        deleted_at__isnull=True,
    ).count()

    return JsonResponse({"count": count})


@login_required(login_url="/account/login/")
@require_GET
def notification_list(request):
    """Return recent notifications (max 12) with optional type filter."""
    org = _get_org(request)
    if not org:
        return JsonResponse({"notifications": []})

    from apps.notifications.models import Notification

    qs = Notification.objects.filter(
        organization=org,
        user=request.user,
        deleted_at__isnull=True,
    ).order_by("-created_at")

    # Optional type filter (tab-based)
    ntype = request.GET.get("type", "").strip().upper()
    if ntype and ntype in ("ORDER", "SYSTEM", "PROMOTION", "PAYMENT", "SECURITY"):
        qs = qs.filter(notification_type=ntype)

    notifications = []
    for n in qs[:12]:
        notifications.append(
            {
                "id": str(n.id),
                "type": n.notification_type,
                "title": n.title or "",
                "message": (n.message or "")[:120],
                "status": n.status,
                "priority": n.priority,
                "created_at": n.created_at.isoformat() if n.created_at else "",
                "read": n.status == "READ",
            }
        )

    return JsonResponse({"notifications": notifications})


@login_required(login_url="/account/login/")
@require_POST
def notification_mark_read(request, notification_id):
    """Mark a single notification as read."""
    org = _get_org(request)
    if not org:
        return JsonResponse({"error": "Unauthorized"}, status=403)

    from apps.notifications.models import Notification

    try:
        notif = Notification.objects.get(
            id=notification_id,
            organization=org,
            user=request.user,
            deleted_at__isnull=True,
        )
        notif.status = "READ"
        notif.save(update_fields=["status", "updated_at"])
        return JsonResponse({"success": True})
    except Notification.DoesNotExist:
        return JsonResponse({"error": "Not found"}, status=404)


@login_required(login_url="/account/login/")
@require_POST
def notification_mark_all_read(request):
    """Mark all unread notifications as read for the current user."""
    org = _get_org(request)
    if not org:
        return JsonResponse({"error": "Unauthorized"}, status=403)

    from apps.notifications.models import Notification

    updated = Notification.objects.filter(
        organization=org,
        user=request.user,
        status="UNREAD",
        deleted_at__isnull=True,
    ).update(status="READ")

    return JsonResponse({"success": True, "updated": updated})
