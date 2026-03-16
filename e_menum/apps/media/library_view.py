"""
Enterprise Media Library — WordPress-style media management page.

Custom admin view at /admin/media-library/ providing:
- Grid/List view toggle
- Drag-and-drop multi-file upload with progress
- Folder tree navigation
- Media type filters
- Bulk actions (select, delete, move)
- Inline metadata editing
- Full-screen preview modal
"""

from django.shortcuts import render

from shared.decorators import superadmin_required


@superadmin_required
def media_library(request):
    """
    Render the enterprise media library page.

    All data is loaded client-side via REST API calls to:
    - /api/v1/media/           — list media files
    - /api/v1/media/upload/    — upload files
    - /api/v1/media/folders/   — list/create folders
    """
    context = {
        "title": "Media Library",
        "has_permission": True,
    }
    return render(request, "admin/media_library.html", context)
