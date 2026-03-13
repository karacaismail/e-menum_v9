"""
QR code short-URL redirect handler.

Handles /q/<code>/ URLs by looking up the QRCode record, logging the scan,
and redirecting the user to the actual target (menu page, custom URL, etc.).

Usage:
    # In config/urls.py:
    from apps.orders.qr_redirect_view import qr_short_url_redirect

    urlpatterns = [
        path('q/<str:code>/', qr_short_url_redirect, name='qr-short-url'),
    ]
"""

import logging
from datetime import timedelta

from django.http import Http404
from django.shortcuts import redirect
from django.utils import timezone

logger = logging.getLogger(__name__)


def qr_short_url_redirect(request, code):
    """
    Look up a QR code by its short code and redirect to the target URL.

    Also records a QRScan entry for analytics tracking.

    Args:
        request: HTTP request
        code: The short QR code string (e.g., 'BCD58DFC')

    Returns:
        302 redirect to target URL, or 404 if QR code not found / inactive.
    """
    from apps.orders.models import QRCode

    try:
        qr = QRCode.objects.select_related("menu", "table", "organization").get(
            code=code,
            deleted_at__isnull=True,
        )
    except QRCode.DoesNotExist:
        logger.warning("QR short-URL not found: code=%s", code)
        raise Http404("QR code not found")

    if not qr.is_active:
        logger.info("QR short-URL inactive: code=%s", code)
        raise Http404("QR code is inactive")

    # Build the target URL
    from apps.orders.services.qr_generator import QRGeneratorService

    target_url = QRGeneratorService.get_target_url(qr)

    # If target URL is the same /q/<code>/ pattern (no menu linked), show 404
    if f"/q/{code}/" in target_url:
        logger.warning("QR code %s has no linked menu, cannot redirect", code)
        raise Http404("QR code has no linked menu")

    # Record the scan asynchronously (best-effort)
    try:
        _record_scan(request, qr)
    except Exception:
        logger.debug("Could not record QR scan for %s", code, exc_info=True)

    logger.info("QR redirect: code=%s -> %s", code, target_url)
    return redirect(target_url)


def _record_scan(request, qr):
    """Record a QR scan event for analytics."""
    from apps.orders.models import QRScan

    ip_address = _get_client_ip(request)
    user_agent = request.META.get("HTTP_USER_AGENT", "")

    # Determine device type from user agent
    ua_lower = user_agent.lower()
    if "mobile" in ua_lower or "android" in ua_lower or "iphone" in ua_lower:
        device_type = "mobile"
    elif "tablet" in ua_lower or "ipad" in ua_lower:
        device_type = "tablet"
    else:
        device_type = "desktop"

    # Check if this is a unique scan (same IP + QR in last 24h)
    recent_scan = QRScan.objects.filter(
        qr_code=qr,
        ip_address=ip_address,
        scanned_at__gte=timezone.now() - timedelta(hours=24),
    ).exists()

    QRScan.objects.create(
        qr_code=qr,
        organization=qr.organization,
        ip_address=ip_address,
        user_agent=user_agent,
        device_type=device_type,
        is_unique=not recent_scan,
    )

    # Update cached counters on QRCode
    from django.db.models import F

    update_fields = {
        "scan_count": F("scan_count") + 1,
        "last_scanned_at": timezone.now(),
    }
    if not recent_scan:
        update_fields["unique_scan_count"] = F("unique_scan_count") + 1

    QRCode = type(qr)
    QRCode.objects.filter(pk=qr.pk).update(**update_fields)


def _get_client_ip(request):
    """Extract client IP from request, considering reverse proxy headers."""
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        return x_forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "")
