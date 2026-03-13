"""
Public media serve endpoint.

Provides a unified URL for accessing media files with proper authorization:

- ``is_public=True`` media → accessible by anyone (anonymous QR menu viewers, etc.)
- ``is_public=False`` media → requires authentication + org membership
- Platform superusers → can access any media regardless of visibility

Usage in config/urls.py::

    from apps.media.serve_view import media_serve

    urlpatterns = [
        path("media/serve/<uuid:pk>/", media_serve, name="media-serve"),
    ]

The endpoint returns a 302 redirect to the actual file URL and increments
the media's ``usage_count`` counter.
"""

import logging

from django.http import Http404, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_GET

from apps.media.models import Media

logger = logging.getLogger(__name__)


@require_GET
def media_serve(request, pk):
    """
    Serve a media file by UUID.

    Public media (``is_public=True``) is served to everyone including
    anonymous users.  Private media requires the requesting user to be
    authenticated and to belong to the media's organization.
    Superusers bypass all checks.  Fine-grained RBAC (``media.view``,
    ``media.create``, etc.) is enforced on the management API views,
    not on this file-serving endpoint.

    On success the view returns a **302 redirect** to the underlying file URL
    and bumps ``usage_count`` / ``last_used_at`` on the Media record.

    Args:
        request: HTTP request.
        pk: UUID primary key of the Media record.

    Returns:
        302 redirect to file URL, or 403/404 as appropriate.
    """
    media = get_object_or_404(Media, pk=pk, deleted_at__isnull=True)

    # ── Public media → serve to anyone ──────────────────────────────────
    if media.is_public:
        return _redirect_to_media(media)

    # ── Private media → authentication required ─────────────────────────
    if not request.user or not request.user.is_authenticated:
        raise Http404("Media not found")

    # Superusers can access any media
    if request.user.is_superuser:
        return _redirect_to_media(media)

    # Organization membership check
    user_org = getattr(request.user, "organization", None)
    request_org = getattr(request, "organization", None)
    media_org_id = media.organization_id

    # User must belong to the same org as the media
    org_match = False
    if user_org and str(user_org.id) == str(media_org_id):
        org_match = True
    elif request_org and str(request_org.id) == str(media_org_id):
        org_match = True

    if not org_match:
        raise Http404("Media not found")

    return _redirect_to_media(media)


def _redirect_to_media(media):
    """
    Build the redirect response and bump usage counters.

    Prefers ``media.url`` (full URL); falls back to ``media.file_path``
    prefixed with ``/media/`` for locally-stored files.
    """
    target_url = media.url or media.file_path
    if not target_url:
        raise Http404("Media file has no URL")

    # If file_path is a relative path, make it absolute under /media/
    if target_url and not target_url.startswith(("http://", "https://", "/")):
        target_url = f"/media/{target_url}"

    # Bump usage (best-effort, non-blocking)
    try:
        media.record_usage()
    except Exception:
        logger.debug("Could not record media usage for %s", media.pk, exc_info=True)

    response = HttpResponseRedirect(target_url)
    # Public media can be cached aggressively by CDN / browsers
    if media.is_public:
        response["Cache-Control"] = "public, max-age=86400"
    else:
        response["Cache-Control"] = "private, no-cache"
    return response
