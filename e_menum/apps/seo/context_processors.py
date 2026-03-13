"""
SEO context processors for E-Menum.

Adds global SEO context variables (GTM snippets, tracking integrations,
default meta tags) to all templates via Django's template context
processor mechanism.
"""

import logging

from django.conf import settings
from django.utils.safestring import mark_safe

logger = logging.getLogger("apps.seo")


def _get_tracking_scripts():
    """
    Fetch active tracking integrations and group by injection position.

    Returns a dict with keys: 'head', 'body_start', 'body_end'.
    Each value is a safe HTML string of concatenated script tags.
    Uses database caching (Django's cache framework) with a 5-minute TTL.
    """
    from django.core.cache import cache

    cache_key = "seo:tracking_scripts"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    try:
        from apps.seo.models import TrackingIntegration

        integrations = TrackingIntegration.objects.filter(is_active=True)

        # Filter by environment if configured
        env_name = getattr(settings, "ENVIRONMENT", "production")
        scripts = {"head": [], "body_start": [], "body_end": []}

        for integration in integrations:
            # Skip if environment restriction is set and doesn't match
            envs = integration.environments
            if envs and env_name not in envs:
                continue

            tag = integration.get_script_tag()
            if tag:
                scripts[integration.position].append(tag)

        result = {k: mark_safe("\n".join(v)) if v else "" for k, v in scripts.items()}

        cache.set(cache_key, result, 300)  # 5-minute TTL
        return result

    except Exception:
        logger.exception("Failed to load tracking integrations")
        return {"head": "", "body_start": "", "body_end": ""}


def seo_context(request):
    """Add global SEO context variables to all templates."""
    from apps.seo.gtm import GTMManager

    gtm = GTMManager()
    tracking = _get_tracking_scripts()

    # Combine GTM head snippet with tracking head scripts
    gtm_head = gtm.get_head_snippet()
    tracking_head = tracking.get("head", "")
    combined_head = "\n".join(filter(None, [gtm_head, tracking_head]))

    gtm_body = gtm.get_body_snippet()
    tracking_body_start = tracking.get("body_start", "")
    combined_body = "\n".join(filter(None, [gtm_body, tracking_body_start]))

    return {
        "SEO_GTM_HEAD": mark_safe(combined_head) if combined_head else "",
        "SEO_GTM_BODY": mark_safe(combined_body) if combined_body else "",
        "SEO_TRACKING_BODY_END": tracking.get("body_end", ""),
        "SEO_SITE_NAME": getattr(settings, "SEO_SITE_NAME", "E-Menum"),
        "SEO_DEFAULT_TITLE": getattr(
            settings,
            "SEO_DEFAULT_TITLE",
            "E-Menum - Akilli QR Menu Platformu",
        ),
        "SEO_DEFAULT_DESCRIPTION": getattr(
            settings,
            "SEO_DEFAULT_DESCRIPTION",
            "Restoran ve kafeler icin yapay zeka destekli dijital menu platformu.",
        ),
        "SEO_DEFAULT_OG_IMAGE": getattr(settings, "SEO_DEFAULT_OG_IMAGE", ""),
    }
