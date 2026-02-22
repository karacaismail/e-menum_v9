"""
Admin AJAX Upload Endpoint for E-Menum.

Provides a secure file upload endpoint for the admin image upload widgets.
Files are saved to MEDIA_ROOT with UUID filenames in per-organization directories.

Security:
- Requires staff authentication (@staff_member_required)
- Validates file type (images only)
- Validates file size (max 10MB from settings)
- CSRF protection via Django's built-in middleware

Usage:
    POST /admin/api/upload/
    Content-Type: multipart/form-data
    Body: file=<binary>

    Response:
    {
        "success": true,
        "url": "/media/org-uuid/menu_items/file-uuid.jpg",
        "filename": "original-name.jpg",
        "size": 123456
    }
"""

import os
from uuid import uuid4

from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST

# Allowed image MIME types
ALLOWED_IMAGE_TYPES = {
    'image/jpeg',
    'image/png',
    'image/webp',
    'image/gif',
    'image/svg+xml',
}

# Allowed extensions (as fallback check)
ALLOWED_EXTENSIONS = {
    'jpg', 'jpeg', 'png', 'webp', 'gif', 'svg',
}

# Max file size (from settings or default 10MB)
MAX_FILE_SIZE = getattr(settings, 'FILE_UPLOAD_MAX_MEMORY_SIZE', 10 * 1024 * 1024)


@staff_member_required
@require_POST
def admin_upload_view(request):
    """
    Handle file upload from admin image widgets.

    Accepts a single file via multipart/form-data, validates it,
    saves it to the appropriate directory, and returns the URL.

    Args:
        request: Django HttpRequest with file in request.FILES['file']

    Returns:
        JsonResponse with success status and file URL
    """
    # Check for file in request
    if 'file' not in request.FILES:
        return JsonResponse({
            'success': False,
            'error': 'No file provided',
        }, status=400)

    uploaded_file = request.FILES['file']

    # Validate file size
    if uploaded_file.size > MAX_FILE_SIZE:
        max_mb = MAX_FILE_SIZE / (1024 * 1024)
        return JsonResponse({
            'success': False,
            'error': f'File too large. Maximum size is {max_mb:.0f}MB.',
        }, status=400)

    # Validate MIME type
    content_type = uploaded_file.content_type
    if content_type not in ALLOWED_IMAGE_TYPES:
        return JsonResponse({
            'success': False,
            'error': f'Invalid file type: {content_type}. Allowed: JPEG, PNG, WebP, GIF, SVG.',
        }, status=400)

    # Validate extension
    original_filename = uploaded_file.name
    ext = original_filename.rsplit('.', 1)[-1].lower() if '.' in original_filename else ''
    if ext not in ALLOWED_EXTENSIONS:
        return JsonResponse({
            'success': False,
            'error': f'Invalid file extension: .{ext}. Allowed: {", ".join(sorted(ALLOWED_EXTENSIONS))}.',
        }, status=400)

    # Determine organization directory
    org_id = 'global'
    if hasattr(request.user, 'organization_id') and request.user.organization_id:
        org_id = str(request.user.organization_id)

    # Allow override via POST parameter (for superadmins uploading to specific orgs)
    org_override = request.POST.get('organization_id')
    if org_override and request.user.is_superuser:
        org_id = org_override

    # Determine subfolder based on field context
    subfolder = request.POST.get('subfolder', 'menu_items')
    if subfolder not in ('menu_items', 'logos', 'gallery', 'categories'):
        subfolder = 'menu_items'

    # Generate UUID filename
    new_filename = f"{uuid4()}.{ext}"
    relative_path = os.path.join(org_id, subfolder, new_filename)

    # Ensure directory exists
    full_dir = os.path.join(settings.MEDIA_ROOT, org_id, subfolder)
    os.makedirs(full_dir, exist_ok=True)

    # Save file
    full_path = os.path.join(settings.MEDIA_ROOT, relative_path)
    with open(full_path, 'wb+') as destination:
        for chunk in uploaded_file.chunks():
            destination.write(chunk)

    # Build URL
    file_url = f"{settings.MEDIA_URL}{relative_path}"

    return JsonResponse({
        'success': True,
        'url': file_url,
        'filename': original_filename,
        'size': uploaded_file.size,
    })
