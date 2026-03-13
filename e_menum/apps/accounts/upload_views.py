"""Simple image upload views for the restaurant portal (avatar, logo)."""

import logging
import uuid

from django.contrib.auth.decorators import login_required
from django.core.files.storage import default_storage
from django.http import JsonResponse
from django.views.decorators.http import require_POST

logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "gif", "webp", "svg"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB


@login_required(login_url="/account/login/")
@require_POST
def image_upload(request):
    """
    Upload an image file and return its URL.

    POST /account/upload/image/
    Body: multipart/form-data with 'file' field
    Optional query param: ?type=avatar|logo

    Returns: {"success": true, "url": "/media/uploads/..."}
    """
    file = request.FILES.get("file")
    if not file:
        return JsonResponse({"error": "No file provided"}, status=400)

    # Validate file size
    if file.size > MAX_FILE_SIZE:
        return JsonResponse({"error": "File too large (max 5MB)"}, status=400)

    # Validate extension
    ext = file.name.rsplit(".", 1)[-1].lower() if "." in file.name else ""
    if ext not in ALLOWED_EXTENSIONS:
        return JsonResponse(
            {"error": f"Invalid file type. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"},
            status=400,
        )

    # Determine subfolder
    upload_type = request.GET.get("type", "general")
    if upload_type not in ("avatar", "logo", "general"):
        upload_type = "general"

    # Generate unique filename
    unique_name = f"{uuid.uuid4().hex[:12]}.{ext}"
    path = f"uploads/{upload_type}/{unique_name}"

    # Save file
    try:
        saved_path = default_storage.save(path, file)
        url = default_storage.url(saved_path)
        return JsonResponse({"success": True, "url": url})
    except Exception:
        logger.exception("Failed to upload file")
        return JsonResponse({"error": "Upload failed"}, status=500)
