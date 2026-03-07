"""Template tags & filters for the website app."""

from django import template
from django.urls import reverse, NoReverseMatch

register = template.Library()


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
