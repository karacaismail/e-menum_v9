"""
Dashboard HTML views.

Provides the main admin dashboard page (mainboard).
All data is loaded via JavaScript fetch calls to API endpoints.
The template renders as an empty shell with skeleton loaders.
"""

from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render


@staff_member_required
def mainboard(request):
    """
    Main dashboard view — renders the mainboard template.

    All data is fetched client-side via JavaScript.
    Template contains skeleton loaders for each card.
    Page load target: ~50ms (empty template).
    """
    context = {
        "title": "Dashboard",
        "is_nav_sidebar_enabled": False,
        "has_permission": True,
    }
    return render(request, "dashboard/mainboard.html", context)
