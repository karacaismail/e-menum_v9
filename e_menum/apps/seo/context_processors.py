"""
SEO context processors for E-Menum.

Adds global SEO context variables (GTM snippets, default meta tags)
to all templates via Django's template context processor mechanism.
"""

from django.conf import settings


def seo_context(request):
    """Add global SEO context variables to all templates."""
    from apps.seo.gtm import GTMManager

    gtm = GTMManager()
    return {
        "SEO_GTM_HEAD": gtm.get_head_snippet(),
        "SEO_GTM_BODY": gtm.get_body_snippet(),
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
