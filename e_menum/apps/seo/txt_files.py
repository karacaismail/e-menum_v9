"""
Django views for dynamically served TXT files.

Each view checks ``TXTFileConfig`` for admin-managed content first.
If no active configuration exists (or ``auto_generate`` is enabled),
the view falls back to a sensible auto-generated default.

Views:
    robots_txt_view   - /robots.txt
    humans_txt_view   - /humans.txt
    security_txt_view - /.well-known/security.txt
    ads_txt_view      - /ads.txt
    llms_txt_view     - /llms.txt
"""

import logging
from datetime import datetime, timedelta

from django.conf import settings
from django.http import HttpRequest, HttpResponse
from django.utils import timezone

logger = logging.getLogger("apps.seo")


def _get_txt_config(file_type: str):
    """
    Return the active ``TXTFileConfig`` for *file_type*, or ``None``.

    Import is deferred to avoid circular imports at module level.
    """
    from apps.seo.models import TXTFileConfig

    try:
        return TXTFileConfig.objects.filter(
            file_type=file_type,
            is_active=True,
        ).first()
    except Exception:
        return None


def _txt_response(content: str) -> HttpResponse:
    """Shortcut: return a ``text/plain`` response."""
    return HttpResponse(content.strip() + "\n", content_type="text/plain")


# ──────────────────────────────────────────────────────────────────────────────
# robots.txt
# ──────────────────────────────────────────────────────────────────────────────


def robots_txt_view(request: HttpRequest) -> HttpResponse:
    """
    Serve ``robots.txt``.

    Priority:
    1. Admin-managed ``TXTFileConfig(file_type='robots')`` with
       ``auto_generate=False`` -- returns stored content verbatim.
    2. Auto-generated default that disallows ``/admin/`` and ``/api/``
       and points to the XML sitemap.
    """
    config = _get_txt_config("robots")

    if config and not config.auto_generate and config.content:
        return _txt_response(config.content)

    # Auto-generate
    sitemap_url = f"{request.scheme}://{request.get_host()}/sitemap.xml"
    lines = [
        "User-agent: *",
        "Disallow: /admin/",
        "Disallow: /api/",
        "Disallow: /media/filer/",
        "Disallow: /static/admin/",
        "",
        "User-agent: GPTBot",
        "Disallow: /",
        "",
        "User-agent: CCBot",
        "Disallow: /",
        "",
        f"Sitemap: {sitemap_url}",
    ]
    return _txt_response("\n".join(lines))


# ──────────────────────────────────────────────────────────────────────────────
# humans.txt
# ──────────────────────────────────────────────────────────────────────────────


def humans_txt_view(request: HttpRequest) -> HttpResponse:
    """
    Serve ``humans.txt`` following the humanstxt.org standard.

    Contains team info, technology stack, and last-updated date.
    """
    config = _get_txt_config("humans")

    if config and not config.auto_generate and config.content:
        return _txt_response(config.content)

    # Auto-generate
    now = timezone.now().strftime("%Y-%m-%d")
    lines = [
        "/* TEAM */",
        "Product: E-Menum - Enterprise QR Menu SaaS",
        f"Site: {settings.SITE_URL}",
        "Location: Istanbul, Turkey",
        "",
        "/* THANKS */",
        "Django: https://www.djangoproject.com/",
        "Tailwind CSS: https://tailwindcss.com/",
        "Alpine.js: https://alpinejs.dev/",
        "",
        "/* SITE */",
        f"Last update: {now}",
        "Language: Turkish / English",
        "Standards: HTML5, CSS3, ES6+",
        "Framework: Django 5.x",
        "Database: PostgreSQL",
        "Cache: Redis",
    ]
    return _txt_response("\n".join(lines))


# ──────────────────────────────────────────────────────────────────────────────
# security.txt  (RFC 9116)
# ──────────────────────────────────────────────────────────────────────────────


def security_txt_view(request: HttpRequest) -> HttpResponse:
    """
    Serve ``/.well-known/security.txt`` per RFC 9116.

    Fields: Contact, Expires, Preferred-Languages, Canonical.
    """
    config = _get_txt_config("security")

    if config and not config.auto_generate and config.content:
        return _txt_response(config.content)

    # Auto-generate
    host = request.get_host()
    canonical = f"{request.scheme}://{host}/.well-known/security.txt"
    # Expiry one year from now, ISO-8601
    expires = (datetime.utcnow() + timedelta(days=365)).strftime("%Y-%m-%dT%H:%M:%Sz")

    contact_email = getattr(
        settings, "DEFAULT_FROM_EMAIL", f"security@{settings.SITE_DOMAIN}"
    )

    lines = [
        f"Contact: mailto:{contact_email}",
        f"Expires: {expires}",
        "Preferred-Languages: tr, en",
        f"Canonical: {canonical}",
        f"Policy: {settings.SITE_URL}/guvenlik-politikasi/",
    ]
    return _txt_response("\n".join(lines))


# ──────────────────────────────────────────────────────────────────────────────
# ads.txt
# ──────────────────────────────────────────────────────────────────────────────


def ads_txt_view(request: HttpRequest) -> HttpResponse:
    """
    Serve ``ads.txt`` for ad network authorisations.

    Most SaaS products do not run display ads, so the default is an empty
    placeholder.  Actual ad lines should be configured via ``TXTFileConfig``.
    """
    config = _get_txt_config("ads")

    if config and not config.auto_generate and config.content:
        return _txt_response(config.content)

    # Auto-generate (empty placeholder)
    lines = [
        "# ads.txt - E-Menum",
        "# No authorized digital sellers at this time.",
        "# Configure via admin -> SEO -> TXT File Configs",
    ]
    return _txt_response("\n".join(lines))


# ──────────────────────────────────────────────────────────────────────────────
# llms.txt
# ──────────────────────────────────────────────────────────────────────────────


def llms_txt_view(request: HttpRequest) -> HttpResponse:
    """
    Serve ``llms.txt`` providing AI/LLM crawlers with guidance about the site.

    This is an emerging convention (llms.txt) for informing AI systems about
    site purpose, allowed usage, and attribution requirements.
    """
    config = _get_txt_config("llms")

    if config and not config.auto_generate and config.content:
        return _txt_response(config.content)

    # Auto-generate
    host = request.get_host()
    lines = [
        "# E-Menum - Enterprise QR Menu SaaS",
        f"# https://{host}",
        "",
        "## About",
        "E-Menum is a SaaS platform providing AI-powered digital QR menus",
        "for restaurants, cafes, and food & beverage businesses in Turkey.",
        "",
        "## Usage Policy",
        "You may reference publicly available information from this site",
        "for informational purposes. Do not scrape user-generated content",
        "or private data.",
        "",
        "## Attribution",
        "When citing information from this site, please attribute to",
        f'"E-Menum ({settings.SITE_URL})".',
        "",
        "## Contact",
        "For questions about AI/LLM usage of our content, contact",
        f"info@{settings.SITE_DOMAIN}",
        "",
        "## Pages",
        f"- Homepage: https://{host}/",
        f"- Features: https://{host}/ozellikler/",
        f"- Pricing: https://{host}/fiyatlandirma/",
        f"- Blog: https://{host}/blog/",
        f"- About: https://{host}/hakkimizda/",
    ]
    return _txt_response("\n".join(lines))
