"""
SEO middleware classes.

Middleware:
    RedirectMiddleware          - Serve URL redirects from the Redirect model
    CanonicalDomainMiddleware   - Enforce a single canonical domain
    SEOHeadersMiddleware        - Add SEO-related response headers
    Track404Middleware          - Log 404 errors aggregated by path+day
"""

import logging
import os
from datetime import date

from django.conf import settings
from django.core.cache import cache
from django.db.models import F
from django.http import (
    HttpRequest,
    HttpResponse,
    HttpResponsePermanentRedirect,
    HttpResponseRedirect,
)
from django.utils import timezone

logger = logging.getLogger("apps.seo")

# Cache TTL for redirect rules (seconds)
_REDIRECT_CACHE_TTL = 60 * 60  # 1 hour
_REDIRECT_CACHE_PREFIX = "seo:redirect:"
_REDIRECT_MISS_SENTINEL = "__NONE__"


# ──────────────────────────────────────────────────────────────────────────────
# RedirectMiddleware
# ──────────────────────────────────────────────────────────────────────────────


class RedirectMiddleware:
    """
    Check every incoming request against the ``Redirect`` model.

    If an active redirect rule matches ``request.path``, the middleware
    returns the appropriate redirect response (301/302/307/308) and
    increments the hit counter on the rule.

    Redirect lookups are cached to avoid a DB query on every request.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        redirect_response = self._check_redirect(request)
        if redirect_response is not None:
            return redirect_response
        return self.get_response(request)

    @staticmethod
    def _check_redirect(request: HttpRequest):
        """
        Look up an active Redirect for the current path (cached).

        Returns an HTTP redirect response or ``None``.
        """
        path = request.path
        cache_key = f"{_REDIRECT_CACHE_PREFIX}{path}"

        # Try cache first
        cached = cache.get(cache_key)

        if cached == _REDIRECT_MISS_SENTINEL:
            return None

        if cached is not None:
            # cached = (target_path, redirect_type, pk_str)
            target, redirect_type, pk_str = cached
            # Fire-and-forget hit counter update (non-blocking)
            RedirectMiddleware._increment_hit_async(pk_str)
            if redirect_type in (301, 308):
                return HttpResponsePermanentRedirect(target)
            return HttpResponseRedirect(target)

        # Cache miss — query DB
        from apps.seo.models import Redirect

        try:
            rule = Redirect.objects.filter(
                source_path=path,
                is_active=True,
                deleted_at__isnull=True,
            ).first()
        except Exception:
            return None

        if rule is None:
            # Cache the miss so we don't hit DB again for this path
            cache.set(cache_key, _REDIRECT_MISS_SENTINEL, _REDIRECT_CACHE_TTL)
            return None

        # Cache the hit
        cache.set(
            cache_key,
            (rule.target_path, rule.redirect_type, str(rule.pk)),
            _REDIRECT_CACHE_TTL,
        )

        RedirectMiddleware._increment_hit_async(str(rule.pk))

        if rule.redirect_type in (301, 308):
            return HttpResponsePermanentRedirect(rule.target_path)
        return HttpResponseRedirect(rule.target_path)

    @staticmethod
    def _increment_hit_async(pk_str: str):
        """Increment redirect hit counter without blocking the request."""
        try:
            from apps.seo.models import Redirect

            Redirect.objects.filter(pk=pk_str).update(
                hit_count=F("hit_count") + 1,
                last_hit=timezone.now(),
            )
        except Exception:
            pass


# ──────────────────────────────────────────────────────────────────────────────
# CanonicalDomainMiddleware
# ──────────────────────────────────────────────────────────────────────────────


class CanonicalDomainMiddleware:
    """
    Enforce a single canonical domain with wildcard subdomain redirect.

    If ``settings.SEO_CANONICAL_DOMAIN`` is set (e.g. ``"e-menum.net"``)
    and the request's ``Host`` header does not match, the middleware issues
    a 301 redirect to the canonical domain.  This covers **all** subdomains
    including wildcard (``*.e-menum.net``): ``www``, ``api``, ``blog``,
    ``anything.e-menum.net`` → ``e-menum.net``.

    Requests to localhost, 127.0.0.1, or the server IP (``SERVER_IP`` env)
    are **excluded** so health checks, direct IP access, and reverse-proxy
    probes keep working.

    Additionally, if ``settings.APPEND_SLASH`` is ``True`` and the path
    does not end with ``/`` (and is not a file path), a trailing slash is
    appended.
    """

    # Hosts that should never be redirected (internal / health checks / test client)
    SKIP_HOSTS = {"localhost", "127.0.0.1", "0.0.0.0", "testserver"}

    def __init__(self, get_response):
        self.get_response = get_response
        self.canonical_domain = getattr(settings, "SEO_CANONICAL_DOMAIN", "")
        # Also skip the configured server IP
        server_ip = os.environ.get("SERVER_IP", "")
        if server_ip:
            self.SKIP_HOSTS = self.SKIP_HOSTS | {server_ip}

    def __call__(self, request: HttpRequest) -> HttpResponse:
        # --- Canonical domain redirect ---
        if self.canonical_domain:
            host = request.get_host().split(":")[0]  # Strip port
            canonical = self.canonical_domain.split(":")[0]

            # Skip redirect for internal/health-check hosts and IP access
            if host != canonical and host not in self.SKIP_HOSTS:
                # Preserve scheme, path, and query string
                scheme = "https" if request.is_secure() else request.scheme
                new_url = f"{scheme}://{self.canonical_domain}{request.get_full_path()}"
                return HttpResponsePermanentRedirect(new_url)

        # --- Trailing-slash normalisation ---
        if getattr(settings, "APPEND_SLASH", True):
            path = request.path
            if (
                not path.endswith("/")
                and "." not in path.rsplit("/", 1)[-1]  # skip files like .css .js
                and not path.startswith("/api/")  # skip API endpoints
                and not path.startswith("/admin/")  # let Django handle admin
            ):
                new_path = path + "/"
                query = request.META.get("QUERY_STRING", "")
                if query:
                    new_path = f"{new_path}?{query}"
                return HttpResponsePermanentRedirect(new_path)

        return self.get_response(request)


# ──────────────────────────────────────────────────────────────────────────────
# SEOHeadersMiddleware
# ──────────────────────────────────────────────────────────────────────────────


class SEOHeadersMiddleware:
    """
    Add SEO-related HTTP response headers.

    Headers set:
        ``X-Robots-Tag``
            Mirrors the robots meta content for the page.  Views can set
            ``request.seo_robots`` to override the default ``index, follow``.

        ``Link``
            ``<URL>; rel="canonical"`` header when a canonical URL is known.
            Views can set ``request.seo_canonical`` to supply a URL.

        ``Permissions-Policy``
            Set to ``interest-cohort=()`` to opt out of Google FLoC / Topics
            tracking.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        response = self.get_response(request)

        # Skip non-HTML responses (API, static files, etc.)
        content_type = response.get("Content-Type", "")
        if "text/html" not in content_type:
            return response

        # --- X-Robots-Tag ---
        robots = getattr(request, "seo_robots", None)
        if robots:
            response["X-Robots-Tag"] = robots
        else:
            # Default: allow indexing for public pages
            path = request.path
            if path.startswith("/admin/") or path.startswith("/api/"):
                response["X-Robots-Tag"] = "noindex, nofollow"

        # --- Link canonical ---
        canonical = getattr(request, "seo_canonical", None)
        if canonical:
            response["Link"] = f'<{canonical}>; rel="canonical"'

        # --- Permissions-Policy (opt out of FLoC / Topics) ---
        response["Permissions-Policy"] = "interest-cohort=()"

        return response


# ──────────────────────────────────────────────────────────────────────────────
# Track404Middleware
# ──────────────────────────────────────────────────────────────────────────────


class Track404Middleware:
    """
    Track 404 responses and aggregate them in NotFound404Log.

    Each unique (path, date) pair gets one row; subsequent hits increment
    ``hit_count`` using an atomic ``F()`` expression to avoid race conditions.

    Static files, media, admin, and API paths are skipped.
    """

    SKIP_PREFIXES = ("/static/", "/media/", "/admin/", "/api/", "/__debug__/")

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        response = self.get_response(request)

        if response.status_code == 404:
            self._log_404(request)

        return response

    def _log_404(self, request: HttpRequest) -> None:
        path = request.path

        # Skip noise paths
        if any(path.startswith(prefix) for prefix in self.SKIP_PREFIXES):
            return

        # Skip paths with file extensions (static assets requested without /static/)
        if "." in path.rsplit("/", 1)[-1]:
            return

        try:
            from apps.seo.models import NotFound404Log

            today = date.today()
            user_agent = request.META.get("HTTP_USER_AGENT", "")[:500]
            referer = request.META.get("HTTP_REFERER", "")[:500]
            ip = self._get_client_ip(request)

            obj, created = NotFound404Log.objects.get_or_create(
                path=path,
                date=today,
                defaults={
                    "hit_count": 1,
                    "last_user_agent": user_agent,
                    "last_referer": referer,
                    "last_ip": ip,
                },
            )

            if not created:
                NotFound404Log.objects.filter(pk=obj.pk).update(
                    hit_count=F("hit_count") + 1,
                    last_user_agent=user_agent,
                    last_referer=referer,
                    last_ip=ip,
                )
        except Exception:
            logger.debug("Failed to log 404 for path: %s", path, exc_info=True)

    @staticmethod
    def _get_client_ip(request: HttpRequest) -> str:
        """Extract client IP from X-Forwarded-For or REMOTE_ADDR."""
        xff = request.META.get("HTTP_X_FORWARDED_FOR")
        if xff:
            return xff.split(",")[0].strip()
        return request.META.get("REMOTE_ADDR", "")
