"""
Django template tags for SEO metadata, structured data, and scoring.

Usage in templates::

    {% load seo_tags %}

    {# Full meta tag block (title, OG, Twitter, canonical, robots) #}
    {% seo_meta page_obj %}

    {# JSON-LD structured data by schema type #}
    {% seo_jsonld "organization" %}
    {% seo_jsonld "faq" %}

    {# Breadcrumb JSON-LD from a list of (name, url) tuples #}
    {% seo_breadcrumbs crumbs %}

    {# SEO score badge #}
    {% seo_score page_obj %}

Tags:
    seo_meta        - Inclusion tag rendering meta_tags.html
    seo_jsonld      - Simple tag returning JSON-LD for a schema type
    seo_breadcrumbs - Simple tag returning BreadcrumbList JSON-LD
    seo_score       - Simple tag returning an HTML badge
"""

import logging

from django import template
from django.utils.safestring import mark_safe

register = template.Library()
logger = logging.getLogger('apps.seo')


# ──────────────────────────────────────────────────────────────────────────────
# seo_meta  (inclusion tag)
# ──────────────────────────────────────────────────────────────────────────────

@register.inclusion_tag('apps/seo/meta_tags.html', takes_context=True)
def seo_meta(context, obj=None):
    """
    Render a full set of SEO ``<meta>`` / ``<link>`` tags.

    Works with any object that uses ``SEOMixin`` (BlogPost, PSEOPage, etc.).
    Falls back to sensible defaults when fields are empty or when *obj* is
    ``None``.

    Template: ``apps/seo/meta_tags.html``
    """
    request = context.get('request')
    current_url = ''
    if request:
        current_url = request.build_absolute_uri(request.path)

    # Defaults
    defaults = {
        'meta_title': 'E-Menum | Dijital QR Menu Platformu',
        'meta_description': 'Restoran ve kafeler icin yapay zeka destekli dijital menu platformu.',
        'meta_keywords': '',
        'og_title': '',
        'og_description': '',
        'og_image': '',
        'og_type': 'website',
        'og_url': current_url,
        'twitter_card': 'summary_large_image',
        'twitter_title': '',
        'twitter_description': '',
        'twitter_image': '',
        'canonical_url': current_url,
        'robots': 'index, follow',
    }

    if obj is not None:
        # Title
        if hasattr(obj, 'get_meta_title'):
            title = obj.get_meta_title()
        elif hasattr(obj, 'meta_title') and obj.meta_title:
            title = obj.meta_title
        elif hasattr(obj, 'title') and obj.title:
            title = obj.title
        else:
            title = defaults['meta_title']
        defaults['meta_title'] = title

        # Description
        if hasattr(obj, 'get_meta_description'):
            desc = obj.get_meta_description()
        elif hasattr(obj, 'meta_description') and obj.meta_description:
            desc = obj.meta_description
        elif hasattr(obj, 'excerpt') and obj.excerpt:
            desc = obj.excerpt[:160]
        else:
            desc = ''
        if desc:
            defaults['meta_description'] = desc

        # Keywords
        if hasattr(obj, 'meta_keywords') and obj.meta_keywords:
            defaults['meta_keywords'] = obj.meta_keywords

        # Open Graph
        og_title = getattr(obj, 'og_title', '') or title
        og_desc = getattr(obj, 'og_description', '') or desc
        defaults['og_title'] = og_title
        defaults['og_description'] = og_desc
        defaults['og_type'] = getattr(obj, 'og_type', 'website') or 'website'

        # OG image
        og_image_url = ''
        if hasattr(obj, 'get_og_image_url'):
            og_image_url = obj.get_og_image_url()
        elif hasattr(obj, 'og_image') and obj.og_image:
            og_image_url = obj.og_image.url
        if og_image_url and request:
            if og_image_url.startswith('/'):
                og_image_url = f'{request.scheme}://{request.get_host()}{og_image_url}'
        defaults['og_image'] = og_image_url

        # Twitter Card
        defaults['twitter_card'] = getattr(obj, 'twitter_card', 'summary_large_image') or 'summary_large_image'
        defaults['twitter_title'] = getattr(obj, 'twitter_title', '') or og_title
        defaults['twitter_description'] = getattr(obj, 'twitter_description', '') or og_desc
        twitter_img = ''
        if hasattr(obj, 'twitter_image') and obj.twitter_image:
            twitter_img = obj.twitter_image.url
            if twitter_img.startswith('/') and request:
                twitter_img = f'{request.scheme}://{request.get_host()}{twitter_img}'
        defaults['twitter_image'] = twitter_img or og_image_url

        # Canonical
        canonical = getattr(obj, 'canonical_url', '') or current_url
        defaults['canonical_url'] = canonical

        # Robots
        if hasattr(obj, 'get_robots_meta'):
            defaults['robots'] = obj.get_robots_meta()
        else:
            robots_index = getattr(obj, 'robots_index', True)
            robots_follow = getattr(obj, 'robots_follow', True)
            parts = [
                'index' if robots_index else 'noindex',
                'follow' if robots_follow else 'nofollow',
            ]
            defaults['robots'] = ', '.join(parts)

    return defaults


# ──────────────────────────────────────────────────────────────────────────────
# seo_jsonld  (simple tag)
# ──────────────────────────────────────────────────────────────────────────────

@register.simple_tag(takes_context=True)
def seo_jsonld(context, schema_type):
    """
    Return a ``<script type="application/ld+json">`` block for the given
    *schema_type* string.

    Supported types:
        ``organization`` - Organisation data from SiteSettings
        ``faq``          - FAQ data (from ``faqs`` context variable)
        ``local_business`` - LocalBusiness from SiteSettings

    Returns an empty string when data is unavailable.
    """
    from apps.seo.schema_org import (
        FAQPageSchema,
        LocalBusinessSchema,
        OrganizationSchema,
    )

    schema_type_lower = schema_type.lower().replace('-', '_').replace(' ', '_')

    if schema_type_lower == 'organization':
        return _build_organization_jsonld()

    if schema_type_lower == 'faq':
        faqs = context.get('faqs')
        if faqs:
            schema = FAQPageSchema(faqs)
            return mark_safe(schema.to_json_ld())
        return ''

    if schema_type_lower in ('local_business', 'localbusiness'):
        return _build_local_business_jsonld()

    logger.debug('Unknown schema type requested: %s', schema_type)
    return ''


def _build_organization_jsonld() -> str:
    """Build Organization JSON-LD from SiteSettings singleton."""
    from apps.seo.schema_org import OrganizationSchema

    try:
        from apps.website.models import SiteSettings
        site = SiteSettings.load()
        schema = OrganizationSchema(site)
        return mark_safe(schema.to_json_ld())
    except Exception:
        logger.exception('Failed to build Organization JSON-LD')
        return ''


def _build_local_business_jsonld() -> str:
    """Build LocalBusiness JSON-LD from SiteSettings singleton."""
    from apps.seo.schema_org import LocalBusinessSchema

    try:
        from apps.website.models import SiteSettings
        site = SiteSettings.load()
        schema = LocalBusinessSchema(site)
        return mark_safe(schema.to_json_ld())
    except Exception:
        logger.exception('Failed to build LocalBusiness JSON-LD')
        return ''


# ──────────────────────────────────────────────────────────────────────────────
# seo_breadcrumbs  (simple tag)
# ──────────────────────────────────────────────────────────────────────────────

@register.simple_tag
def seo_breadcrumbs(crumbs):
    """
    Return ``BreadcrumbList`` JSON-LD from a list of ``(name, url)`` tuples.

    Example usage in a template::

        {% seo_breadcrumbs breadcrumb_items %}

    Where ``breadcrumb_items`` is set in the view context as::

        [('Ana Sayfa', '/'), ('Blog', '/blog/'), ('Yazi Basligi', '/blog/slug/')]
    """
    from apps.seo.schema_org import BreadcrumbListSchema

    if not crumbs:
        return ''

    schema = BreadcrumbListSchema(list(crumbs))
    return mark_safe(schema.to_json_ld())


# ──────────────────────────────────────────────────────────────────────────────
# seo_score  (simple tag)
# ──────────────────────────────────────────────────────────────────────────────

@register.simple_tag
def seo_score(obj):
    """
    Return an HTML badge showing the SEO score of *obj*.

    Colours:
        - Green  (>= 80)
        - Yellow (>= 50)
        - Red    (< 50)

    The score is read from ``obj.seo_score`` if available; otherwise a fresh
    calculation is attempted via ``obj.calculate_seo_score()``.
    """
    if obj is None:
        return ''

    score = getattr(obj, 'seo_score', 0)
    if score == 0 and hasattr(obj, 'calculate_seo_score'):
        try:
            score = obj.calculate_seo_score()
        except Exception:
            score = 0

    # Determine colour
    if score >= 80:
        bg_class = 'bg-green-100 text-green-800'
        dot_class = 'bg-green-500'
        label = 'Iyi'
    elif score >= 50:
        bg_class = 'bg-yellow-100 text-yellow-800'
        dot_class = 'bg-yellow-500'
        label = 'Orta'
    else:
        bg_class = 'bg-red-100 text-red-800'
        dot_class = 'bg-red-500'
        label = 'Dusuk'

    html = (
        f'<span class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full '
        f'text-xs font-medium {bg_class}">'
        f'<span class="w-2 h-2 rounded-full {dot_class}"></span>'
        f'{score}/100 &middot; {label}'
        f'</span>'
    )
    return mark_safe(html)
