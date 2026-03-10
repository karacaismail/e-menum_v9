"""Template tags & filters for the website app."""

from django import template
from django.urls import reverse, NoReverseMatch

register = template.Library()


# Gender-aware avatar URLs using Unsplash professional headshots.
# Maps Turkish first names to gender for correct photo assignment.
_FEMALE_NAMES = {
    "ayse",
    "fatma",
    "zeynep",
    "selin",
    "elif",
    "deniz",  # more commonly female in Turkish context
    "pinar",
    "gamze",
    "esra",
    "merve",
    "buse",
    "ebru",
    "gul",
    "ozlem",
    "canan",
    "tugba",
    "derya",
    "asli",
    "sibel",
    "nalan",
    "nilay",
    "yasemin",
    "hulya",
    "leyla",
    "naz",
    "ceren",
    "melis",
    "defne",
    "irem",
}

# Unsplash professional headshot IDs - male
_MALE_PHOTOS = [
    "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=96&h=96&fit=crop&crop=face",
    "https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=96&h=96&fit=crop&crop=face",
    "https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=96&h=96&fit=crop&crop=face",
    "https://images.unsplash.com/photo-1519085360753-af0119f7cbe7?w=96&h=96&fit=crop&crop=face",
    "https://images.unsplash.com/photo-1506794778202-cad84cf45f1d?w=96&h=96&fit=crop&crop=face",
    "https://images.unsplash.com/photo-1463453091185-61582044d556?w=96&h=96&fit=crop&crop=face",
    "https://images.unsplash.com/photo-1560250097-0b93528c311a?w=96&h=96&fit=crop&crop=face",
    "https://images.unsplash.com/photo-1492562080023-ab3db95bfbce?w=96&h=96&fit=crop&crop=face",
    "https://images.unsplash.com/photo-1534030347209-467a5b0ad3e6?w=96&h=96&fit=crop&crop=face",
    "https://images.unsplash.com/photo-1548449112-96a38a643324?w=96&h=96&fit=crop&crop=face",
]

# Unsplash professional headshot IDs - female
_FEMALE_PHOTOS = [
    "https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=96&h=96&fit=crop&crop=face",
    "https://images.unsplash.com/photo-1438761681033-6461ffad8d80?w=96&h=96&fit=crop&crop=face",
    "https://images.unsplash.com/photo-1544005313-94ddf0286df2?w=96&h=96&fit=crop&crop=face",
    "https://images.unsplash.com/photo-1580489944761-15a19d654956?w=96&h=96&fit=crop&crop=face",
    "https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?w=96&h=96&fit=crop&crop=face",
    "https://images.unsplash.com/photo-1487412720507-e7ab37603c6f?w=96&h=96&fit=crop&crop=face",
    "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=96&h=96&fit=crop&crop=face",
    "https://images.unsplash.com/photo-1567532939604-b6b5b0db2604?w=96&h=96&fit=crop&crop=face",
    "https://images.unsplash.com/photo-1531746020798-e6953c6e8e04?w=96&h=96&fit=crop&crop=face",
    "https://images.unsplash.com/photo-1548142813-c348350df52b?w=96&h=96&fit=crop&crop=face",
]


@register.filter
def split(value, delimiter=","):
    """Split a string by a delimiter.

    Usage in template:
        {% for item in "a,b,c"|split:"," %}
    """
    if not value:
        return []
    return value.split(delimiter)


@register.filter
def gender_avatar(name, counter=0):
    """Return a gender-appropriate Unsplash headshot URL for a Turkish name.

    Usage in template:
        {{ member.name|gender_avatar:forloop.counter }}
    """
    if not name:
        return _MALE_PHOTOS[0]

    first_name = name.strip().split()[0].lower().replace("ı", "i").replace("ş", "s")
    idx = int(counter or 0) % 10

    if first_name in _FEMALE_NAMES:
        return _FEMALE_PHOTOS[idx]
    return _MALE_PHOTOS[idx]


@register.filter
def resolve_nav_url(url_value):
    """Resolve a NavigationLink *url* field to an href-ready string.

    Supports three formats stored in NavigationLink.url:
      1. Django URL name  → ``website:features``  (reversed via ``reverse()``)
      2. Absolute path    → ``/ozellikler/``       (returned as-is)
      3. Full URL         → ``https://…``          (returned as-is)

    Falls back to ``#`` when resolution fails.
    """
    if not url_value:
        return "#"
    # Raw path or full URL — pass through
    if url_value.startswith("/") or url_value.startswith("http"):
        return url_value
    # Anchor-only
    if url_value.startswith("#"):
        return url_value
    # Try Django URL name
    try:
        return reverse(url_value)
    except NoReverseMatch:
        return "#"
