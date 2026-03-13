"""
Text utilities — Turkish-aware slugify and string helpers.
"""

import re


# Transliteration map for Turkish special characters → ASCII equivalents.
_TR_MAP = str.maketrans(
    {
        "ç": "c",
        "Ç": "c",
        "ğ": "g",
        "Ğ": "g",
        "ı": "i",
        "I": "i",
        "İ": "i",
        "ö": "o",
        "Ö": "o",
        "ş": "s",
        "Ş": "s",
        "ü": "u",
        "Ü": "u",
        # Common accented characters from other languages
        "é": "e",
        "è": "e",
        "ê": "e",
        "ë": "e",
        "à": "a",
        "â": "a",
        "ä": "a",
        "î": "i",
        "ï": "i",
        "ô": "o",
        "û": "u",
        "ñ": "n",
    }
)


def slugify_tr(value: str) -> str:
    """
    Convert a string to a URL-safe slug with Turkish transliteration.

    Unlike Django's ``slugify``, this function correctly handles Turkish
    characters by transliterating them first (ç→c, ş→s, ı→i, ğ→g, ö→o, ü→u,
    İ→i, etc.) instead of stripping them.

    Examples::

        >>> slugify_tr("Özel Menü")
        'ozel-menu'
        >>> slugify_tr("İstanbul Café şöle")
        'istanbul-cafe-sole'
        >>> slugify_tr("Çay & Kahve!")
        'cay-kahve'

    """
    value = value.translate(_TR_MAP)
    value = value.lower()
    value = re.sub(r"[^a-z0-9\-]", "-", value)
    value = re.sub(r"-+", "-", value)
    return value.strip("-")
