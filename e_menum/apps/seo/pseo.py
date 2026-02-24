"""
Programmatic SEO (pSEO) engine.

Generates and manages programmatic SEO pages from templates + variable
combinations (e.g. city x sector).

Classes:
    PSEOEngine  - Core engine for page generation, rendering, scoring,
                  and bulk publishing.

Helpers:
    DEFAULT_CITIES                     - Top 10 Turkish cities
    DEFAULT_SECTORS                    - Top 10 F&B sector labels
    generate_city_sector_combinations  - Cartesian product of cities x sectors
"""

import logging
import re
from collections import Counter
from typing import Any, Dict, List, Optional

from django.utils import timezone

logger = logging.getLogger('apps.seo')


# ──────────────────────────────────────────────────────────────────────────────
# Default variable data
# ──────────────────────────────────────────────────────────────────────────────

DEFAULT_CITIES: List[str] = [
    'Istanbul',
    'Ankara',
    'Izmir',
    'Antalya',
    'Bursa',
    'Adana',
    'Gaziantep',
    'Konya',
    'Mersin',
    'Kayseri',
]

DEFAULT_SECTORS: List[str] = [
    'Restoran',
    'Kafe',
    'Fast Food',
    'Fine Dining',
    'Pastane',
    'Nargile Kafe',
    'Bar',
    'Pub',
    'Kebapci',
    'Pizzaci',
]


def generate_city_sector_combinations() -> List[Dict[str, str]]:
    """
    Return the Cartesian product of :data:`DEFAULT_CITIES` and
    :data:`DEFAULT_SECTORS` as a list of dicts.

    Each dict has keys ``sehir`` and ``sektor``::

        [
            {'sehir': 'Istanbul', 'sektor': 'Restoran'},
            {'sehir': 'Istanbul', 'sektor': 'Kafe'},
            ...
        ]
    """
    combinations: List[Dict[str, str]] = []
    for city in DEFAULT_CITIES:
        for sector in DEFAULT_SECTORS:
            combinations.append({
                'sehir': city,
                'sektor': sector,
            })
    return combinations


# ──────────────────────────────────────────────────────────────────────────────
# PSEOEngine
# ──────────────────────────────────────────────────────────────────────────────

class PSEOEngine:
    """
    Core engine for programmatic SEO page lifecycle.

    Typical workflow::

        engine = PSEOEngine()
        variables_list = generate_city_sector_combinations()
        count = engine.generate_pages(template, variables_list)
        published = engine.bulk_publish(template, min_quality=60)
    """

    # ── Rendering ────────────────────────────────────────────────────────

    @staticmethod
    def render_page(template, variables: Dict[str, str]) -> Dict[str, str]:
        """
        Render a single pSEO page from *template* and *variables*.

        Uses ``str.format_map`` for template substitution so that
        placeholders like ``{sehir}`` and ``{sektor}`` in the template
        fields are replaced with the supplied values.

        Parameters
        ----------
        template:
            A ``PSEOTemplate`` model instance.
        variables:
            Dict of placeholder key/value pairs.

        Returns
        -------
        dict
            Keys: ``slug``, ``title``, ``description``, ``content``.
        """
        safe_vars = _SafeFormatMap(variables)

        slug = template.slug_template.format_map(safe_vars)
        title = template.title_template.format_map(safe_vars)
        description = template.description_template.format_map(safe_vars)
        content = template.content_template.format_map(safe_vars)

        # Normalise slug
        slug = _slugify_turkish(slug)

        return {
            'slug': slug,
            'title': title,
            'description': description,
            'content': content,
        }

    # ── Generation ───────────────────────────────────────────────────────

    def generate_pages(self, template, variables_list: List[Dict[str, str]]) -> int:
        """
        Generate ``PSEOPage`` records from *template* for every variable
        combination in *variables_list*.

        Existing pages with the same slug are skipped (no duplicates).

        Returns the number of newly created pages.
        """
        from apps.seo.models import PSEOPage

        created = 0
        for variables in variables_list:
            rendered = self.render_page(template, variables)
            slug = rendered['slug']

            # Skip if page already exists for this slug
            if PSEOPage.objects.filter(slug=slug, deleted_at__isnull=True).exists():
                logger.debug('pSEO page already exists for slug: %s', slug)
                continue

            quality = self._score_rendered(rendered)

            page = PSEOPage(
                template=template,
                slug=slug,
                variables=variables,
                rendered_title=rendered['title'],
                rendered_description=rendered['description'],
                rendered_content=rendered['content'],
                quality_score=quality,
                # Inherit SEOMixin defaults
                meta_title=rendered['title'][:70],
                meta_description=rendered['description'][:160],
            )
            page.save()
            created += 1
            logger.debug('Created pSEO page: %s (quality=%d)', slug, quality)

        logger.info(
            'pSEO generation complete: %d pages created from template "%s"',
            created,
            template.name,
        )
        return created

    # ── Quality scoring ──────────────────────────────────────────────────

    def calculate_quality_score(self, page) -> int:
        """
        Score a ``PSEOPage`` from 0 to 100 based on content quality
        heuristics.

        Scoring criteria (weights):
            - Title length (10-70 chars optimal) ................. 20
            - Description length (50-160 chars optimal) .......... 20
            - Content length (>300 words is good) ................ 25
            - Unique content ratio (unique words / total) ........ 20
            - Keyword presence (focus_keyword in title/content) .. 15

        The ``page.quality_score`` field is updated in-place but **not**
        saved automatically.
        """
        rendered = {
            'title': page.rendered_title or '',
            'description': page.rendered_description or '',
            'content': page.rendered_content or '',
        }
        focus = getattr(page, 'focus_keyword', '') or ''

        score = self._score_rendered(rendered, focus_keyword=focus)
        page.quality_score = score
        return score

    @staticmethod
    def _score_rendered(
        rendered: Dict[str, str],
        focus_keyword: str = '',
    ) -> int:
        """Score a dict of rendered fields. Returns 0-100."""
        score = 0
        title = rendered.get('title', '')
        description = rendered.get('description', '')
        content = rendered.get('content', '')

        # --- Title (max 20 pts) ---
        title_len = len(title)
        if title_len > 0:
            score += 5
            if 10 <= title_len <= 70:
                score += 15
            elif title_len < 10:
                score += 5
            else:
                score += 8  # too long but present

        # --- Description (max 20 pts) ---
        desc_len = len(description)
        if desc_len > 0:
            score += 5
            if 50 <= desc_len <= 160:
                score += 15
            elif desc_len < 50:
                score += 5
            else:
                score += 8

        # --- Content length (max 25 pts) ---
        words = content.split()
        word_count = len(words)
        if word_count >= 300:
            score += 25
        elif word_count >= 150:
            score += 18
        elif word_count >= 50:
            score += 10
        elif word_count > 0:
            score += 5

        # --- Unique content ratio (max 20 pts) ---
        if word_count > 0:
            lower_words = [w.lower() for w in words]
            unique_count = len(set(lower_words))
            ratio = unique_count / word_count
            if ratio >= 0.6:
                score += 20
            elif ratio >= 0.4:
                score += 14
            elif ratio >= 0.2:
                score += 8
            else:
                score += 3

        # --- Keyword presence (max 15 pts) ---
        if focus_keyword:
            kw_lower = focus_keyword.lower()
            if kw_lower in title.lower():
                score += 8
            if kw_lower in content.lower():
                score += 7
        else:
            # No keyword set -- give partial credit
            score += 5

        return min(score, 100)

    # ── Bulk publish ─────────────────────────────────────────────────────

    def bulk_publish(self, template, min_quality: int = 60) -> int:
        """
        Publish all unpublished pages for *template* where
        ``quality_score >= min_quality``.

        Sets ``is_published=True`` and ``published_at`` to the current
        timestamp.

        Returns the number of pages published.
        """
        from apps.seo.models import PSEOPage

        pages = PSEOPage.objects.filter(
            template=template,
            is_published=False,
            quality_score__gte=min_quality,
            deleted_at__isnull=True,
        )

        now = timezone.now()
        count = pages.update(
            is_published=True,
            published_at=now,
        )

        logger.info(
            'Bulk published %d pSEO pages for template "%s" (min_quality=%d)',
            count,
            template.name,
            min_quality,
        )
        return count


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

class _SafeFormatMap(dict):
    """
    A dict subclass that returns the placeholder key wrapped in braces
    when a key is missing, instead of raising ``KeyError``.

    This makes ``str.format_map`` safe for partial rendering.
    """

    def __missing__(self, key: str) -> str:
        return f'{{{key}}}'


def _slugify_turkish(value: str) -> str:
    """
    Convert a string to a URL-safe slug, handling Turkish characters.

    Transliterates Turkish-specific characters (ç->c, ş->s, etc.),
    lowercases, replaces whitespace/special chars with hyphens, and
    strips leading/trailing hyphens.
    """
    tr_map = str.maketrans({
        'ç': 'c', 'Ç': 'c',
        'ğ': 'g', 'Ğ': 'g',
        'ı': 'i', 'I': 'i',
        'İ': 'i',
        'ö': 'o', 'Ö': 'o',
        'ş': 's', 'Ş': 's',
        'ü': 'u', 'Ü': 'u',
    })
    value = value.translate(tr_map)
    value = value.lower()
    value = re.sub(r'[^a-z0-9\-]', '-', value)
    value = re.sub(r'-+', '-', value)
    return value.strip('-')
