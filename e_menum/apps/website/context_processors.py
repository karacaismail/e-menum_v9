"""
Context processors for website marketing pages.

Provides shared context (navigation links, company info, social links)
that is available in every marketing template.

Data is loaded from SiteSettings (singleton) and NavigationLink models.
Falls back to sensible defaults if database is empty.
"""

import logging
from datetime import datetime

from django.core.cache import cache
from django.utils.translation import gettext_lazy as _
from django.utils.translation import get_language

logger = logging.getLogger(__name__)

CACHE_KEY_PREFIX = 'website_marketing_context'
CACHE_TIMEOUT = 300  # 5 minutes


def _cache_key():
    """Language-aware cache key."""
    lang = get_language() or 'tr'
    return f'{CACHE_KEY_PREFIX}_{lang}'


def marketing_context(request):
    """
    Inject shared marketing data into all templates.

    Cache is per-language to serve correct translations.

    Available in templates as:
        {{ marketing.company_name }}
        {{ marketing.phone }}
        {{ marketing.nav_links }}
        ...
    """
    key = _cache_key()
    cached = cache.get(key)
    if cached:
        return cached

    try:
        data = _build_context()
    except Exception:
        logger.exception('Failed to build marketing context from DB, using defaults')
        data = _default_context()

    result = {'marketing': data}
    cache.set(key, result, CACHE_TIMEOUT)
    return result


def invalidate_marketing_cache():
    """Call this after SiteSettings or NavigationLink changes. Clears all languages."""
    from django.conf import settings
    for lang_code, _lang_name in settings.LANGUAGES:
        cache.delete(f'{CACHE_KEY_PREFIX}_{lang_code}')


def _build_mega_menu():
    """Build structured mega menu data from header NavigationLink entries.

    Returns a list of top-level menu items.  Each item that has children is
    flagged with ``is_mega=True`` so templates can render it as a mega-menu
    dropdown.
    """
    from .models import NavigationLink

    parents = NavigationLink.objects.filter(
        location='header',
        parent__isnull=True,
        is_active=True,
    ).prefetch_related('children').order_by('sort_order')

    menu = []
    for parent in parents:
        active_children = parent.children.filter(is_active=True).order_by('sort_order')
        children_list = [
            {
                'url': child.url,
                'label': child.label,
                'icon': child.icon,
                'desc': child.description,
            }
            for child in active_children
        ]
        menu.append({
            'label': parent.label,
            'url': parent.url,
            'icon': parent.icon,
            'is_mega': len(children_list) > 0,
            'children': children_list,
        })
    return menu


def _build_context():
    """Build the marketing context dict from database models."""
    from .models import NavigationLink, SiteSettings

    settings = SiteSettings.load()

    # Header nav links — parents + children
    header_parents = NavigationLink.objects.filter(
        location='header',
        parent__isnull=True,
        is_active=True,
    ).prefetch_related('children').order_by('sort_order')

    nav_links = []
    for link in header_parents:
        children = link.children.filter(is_active=True).order_by('sort_order')
        if children.exists():
            nav_links.append({
                'label': link.label,
                'children': [
                    {
                        'url': child.url,
                        'label': child.label,
                        'icon': child.icon,
                        'desc': child.description,
                    }
                    for child in children
                ],
            })
        else:
            nav_links.append({
                'url': link.url,
                'label': link.label,
            })

    # Footer link groups
    def _footer_links(location):
        return [
            {'url': link.url, 'label': link.label}
            for link in NavigationLink.objects.filter(
                location=location, is_active=True, parent__isnull=True,
            ).order_by('sort_order')
        ]

    return {
        # Company info
        'company_name': settings.company_name,
        'tagline': settings.tagline,
        'description': settings.description,

        # Contact info
        'phone': settings.phone,
        'email': settings.email,
        'address': settings.address,

        # Social media links
        'social': {
            'instagram': settings.social_instagram,
            'twitter': settings.social_twitter,
            'linkedin': settings.social_linkedin,
            'youtube': settings.social_youtube,
        },

        # WhatsApp CTA
        'whatsapp_number': settings.whatsapp_number,
        'whatsapp_message': settings.whatsapp_message,

        # Announcement bar
        'announcement_text': settings.announcement_text,
        'announcement_url': settings.announcement_url,
        'announcement_is_active': settings.announcement_is_active,

        # Cookie banner
        'cookie_banner_title': settings.cookie_banner_title,
        'cookie_banner_text': settings.cookie_banner_text,

        # Additional branding / legal identifiers
        'vat_no': settings.vat_no,
        'mersis_no': settings.mersis_no,
        'trade_registry': settings.trade_registry,
        'status_page_url': settings.status_page_url,

        # Navigation links (header)
        'nav_links': nav_links,

        # Mega menu (structured header navigation for storefront)
        'mega_menu': _build_mega_menu(),

        # Footer link groups
        'footer_product_links': _footer_links('footer_product'),
        'footer_solutions_links': _footer_links('footer_solutions'),
        'footer_company_links': _footer_links('footer_company'),
        'footer_support_links': _footer_links('footer_support'),
        'footer_legal_links': _footer_links('footer_legal'),
        'footer_resources_links': _footer_links('footer_resources'),
        'footer_investors_links': _footer_links('footer_investors'),

        # CTA defaults
        'cta_primary_text': settings.cta_primary_text,
        'cta_secondary_text': settings.cta_secondary_text,
        'cta_trust_text': settings.cta_trust_text,
        'cta_primary_url': settings.cta_primary_url,
        'cta_secondary_url': settings.cta_secondary_url,

        # Admin login URL
        'login_url': settings.login_url,

        # Current year for copyright
        'year': datetime.now().year,
    }


def _default_context():
    """Fallback context if DB is unavailable."""
    return {
        'company_name': 'E-Menum',
        'tagline': _('QR Menunuz, Isletmenizin Dijital Vitrini'),
        'description': _(
            'Restoran ve kafeler icin yapay zeka destekli dijital menu platformu.'
        ),
        'phone': '+90 850 123 4567',
        'email': 'info@e-menum.com',
        'address': _('Istanbul, Turkiye'),
        'social': {
            'instagram': 'https://instagram.com/emenum',
            'twitter': 'https://twitter.com/emenum',
            'linkedin': 'https://linkedin.com/company/emenum',
            'youtube': 'https://youtube.com/@emenum',
        },
        'whatsapp_number': '908501234567',
        'whatsapp_message': _('Merhaba! E-Menum hakkinda bilgi almak istiyorum.'),

        # Announcement bar
        'announcement_text': '',
        'announcement_url': '',
        'announcement_is_active': False,

        # Cookie banner
        'cookie_banner_title': 'Çerez Kullanımı',
        'cookie_banner_text': 'Web sitemizde size daha iyi bir deneyim sunabilmek için çerezleri kullanıyoruz.',

        # Additional branding / legal identifiers
        'vat_no': '',
        'mersis_no': '',
        'trade_registry': '',
        'status_page_url': 'https://status.emenum.com',

        'nav_links': [],
        'mega_menu': [],
        'footer_product_links': [],
        'footer_solutions_links': [],
        'footer_company_links': [],
        'footer_support_links': [],
        'footer_legal_links': [],
        'footer_resources_links': [],
        'footer_investors_links': [],
        'cta_primary_text': _('14 Gun Ucretsiz Basla'),
        'cta_secondary_text': _('Demo Iste'),
        'cta_trust_text': _('Kredi karti gerekmez \u00b7 2 dakikada kurulum'),
        'cta_primary_url': 'website:demo',
        'cta_secondary_url': 'website:demo',
        'login_url': '/admin/',
        'year': datetime.now().year,
    }
