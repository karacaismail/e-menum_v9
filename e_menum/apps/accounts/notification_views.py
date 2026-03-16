"""Notification API views for the restaurant owner portal navbar widget.

Provides lightweight JSON endpoints for:
- Unread notification count (polling)
- Recent notifications list (max 12, with tab filtering)
- Mark notification as read
- Mark all notifications as read

All views use session auth (login_required).
- Regular users: filter by organization + user
- Superadmin/staff (no org): filter by user only, or show all SYSTEM notifications
"""

import logging

from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_GET, require_POST

logger = logging.getLogger(__name__)


def _get_org(request):
    return getattr(request.user, "organization", None)


def _base_filter(request):
    """Build base queryset filter depending on user type.

    - Users with an organization: org-scoped + user-scoped
    - Superadmin/staff without org: user-scoped OR system-wide notifications
    """
    org = _get_org(request)
    if org:
        return Q(organization=org, user=request.user, deleted_at__isnull=True)
    # Superadmin/staff: own notifications OR system-wide (user=None) notifications
    return Q(user=request.user, deleted_at__isnull=True) | Q(
        user__isnull=True, notification_type="SYSTEM", deleted_at__isnull=True
    )


@login_required(login_url="/account/login/")
@require_GET
def notification_unread_count(request):
    """Return unread notification count for the current user."""
    from apps.notifications.models import Notification

    count = (
        Notification.objects.filter(
            _base_filter(request),
        )
        .exclude(status="READ")
        .count()
    )

    return JsonResponse({"count": count})


@login_required(login_url="/account/login/")
@require_GET
def notification_list(request):
    """Return recent notifications (max 12) with optional type filter."""
    from apps.notifications.models import Notification

    qs = Notification.objects.filter(
        _base_filter(request),
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
    from apps.notifications.models import Notification

    try:
        notif = Notification.objects.get(
            _base_filter(request),
            id=notification_id,
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
    from apps.notifications.models import Notification

    updated = (
        Notification.objects.filter(
            _base_filter(request),
        )
        .exclude(status="READ")
        .update(status="READ")
    )

    return JsonResponse({"success": True, "updated": updated})


@login_required(login_url="/account/login/")
@require_GET
def notification_page(request):
    """Full-page view of all notifications (paginated)."""
    from apps.notifications.models import Notification

    qs = Notification.objects.filter(
        _base_filter(request),
    ).order_by("-created_at")

    ntype = request.GET.get("type", "").strip().upper()
    if ntype and ntype in ("ORDER", "SYSTEM", "PROMOTION", "PAYMENT", "SECURITY"):
        qs = qs.filter(notification_type=ntype)

    paginator = Paginator(qs, 25)
    page_number = request.GET.get("page", 1)
    page_obj = paginator.get_page(page_number)

    return render(
        request,
        "accounts/notifications/list.html",
        {
            "page_obj": page_obj,
            "current_type": ntype,
            "notification_types": [
                "ORDER",
                "SYSTEM",
                "PROMOTION",
                "PAYMENT",
                "SECURITY",
            ],
        },
    )
