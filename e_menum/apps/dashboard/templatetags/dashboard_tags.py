"""
Dashboard template tags.

Provides:
- active_nav_section: Returns 'active' if request.path starts with prefix
"""

from django import template

register = template.Library()


@register.simple_tag(takes_context=True)
def active_nav_section(context, section_prefix):
    """
    Return 'active' if request.path starts with the given prefix.

    Usage:
        {% load dashboard_tags %}
        <a class="nav-main-item {% active_nav_section '/admin/menu/' %}">
    """
    request = context.get("request")
    if request and request.path.startswith(section_prefix):
        return "active"
    return ""
