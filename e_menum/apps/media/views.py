"""
API Views for the Media application.

Handles file uploads, listing, detail, update, and soft-delete.
All views are tenant-scoped via organization filter and protected
by RBAC permissions (media.view, media.create, media.update, media.delete).
"""

import logging

from django.utils import timezone
from django_filters import rest_framework as filters
from rest_framework import generics, parsers, permissions

from apps.media.models import Media, MediaFolder
from apps.media.serializers import (
    MediaDetailSerializer,
    MediaFolderCreateSerializer,
    MediaFolderSerializer,
    MediaListSerializer,
    MediaUploadSerializer,
)
from shared.permissions.abilities import HasOrganizationPermission

logger = logging.getLogger(__name__)


# =============================================================================
# FILTERS
# =============================================================================


class MediaFilter(filters.FilterSet):
    media_type = filters.CharFilter(field_name="media_type")
    folder = filters.UUIDFilter(field_name="folder_id")
    status = filters.CharFilter(field_name="status")
    search = filters.CharFilter(method="filter_search")

    class Meta:
        model = Media
        fields = ["media_type", "folder", "status"]

    def filter_search(self, queryset, name, value):
        return queryset.filter(title__icontains=value)


# =============================================================================
# MIXINS
# =============================================================================


class TenantMediaMixin:
    """Filter media data by the requesting user's organization."""

    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()
        organization = getattr(self.request, "organization", None)
        if organization:
            return qs.filter(organization=organization)
        return qs.none()


class MediaReadMixin(TenantMediaMixin):
    """Mixin for read-only media views (list, detail). Requires media.view."""

    permission_classes = [HasOrganizationPermission("media.view")]


class MediaCreateMixin(TenantMediaMixin):
    """Mixin for media creation views (upload, folder create). Requires media.create."""

    permission_classes = [HasOrganizationPermission("media.create")]


class MediaUpdateMixin(TenantMediaMixin):
    """Mixin for media update views. Requires media.update."""

    permission_classes = [HasOrganizationPermission("media.update")]


class MediaDeleteMixin(TenantMediaMixin):
    """Mixin for media delete views. Requires media.delete."""

    permission_classes = [HasOrganizationPermission("media.delete")]


# =============================================================================
# FOLDER VIEWS
# =============================================================================


class MediaFolderListCreateView(TenantMediaMixin, generics.ListCreateAPIView):
    """
    List or create media folders.

    GET:  List all folders for the organization (requires media.view).
    POST: Create a new folder (requires media.create).
    """

    queryset = MediaFolder.objects.filter(deleted_at__isnull=True).order_by("name")

    def get_permission_classes(self):
        if self.request.method == "POST":
            return [HasOrganizationPermission("media.create")]
        return [HasOrganizationPermission("media.view")]

    def get_permissions(self):
        return [
            perm() if isinstance(perm, type) else perm
            for perm in self.get_permission_classes()
        ]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return MediaFolderCreateSerializer
        return MediaFolderSerializer

    def perform_create(self, serializer):
        serializer.save(organization=self.request.organization)


class MediaFolderDetailView(TenantMediaMixin, generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update, or soft-delete a media folder.

    GET:    Requires media.view.
    PUT/PATCH: Requires media.update.
    DELETE: Requires media.delete.
    """

    queryset = MediaFolder.objects.filter(deleted_at__isnull=True)
    serializer_class = MediaFolderSerializer

    def get_permission_classes(self):
        if self.request.method in ("PUT", "PATCH"):
            return [HasOrganizationPermission("media.update")]
        if self.request.method == "DELETE":
            return [HasOrganizationPermission("media.delete")]
        return [HasOrganizationPermission("media.view")]

    def get_permissions(self):
        return [
            perm() if isinstance(perm, type) else perm
            for perm in self.get_permission_classes()
        ]

    def perform_destroy(self, instance):
        # Soft delete
        instance.deleted_at = timezone.now()
        instance.save(update_fields=["deleted_at"])


# =============================================================================
# MEDIA VIEWS
# =============================================================================


class MediaListView(MediaReadMixin, generics.ListAPIView):
    """
    List media files for the organization.

    Requires: media.view permission.
    Filters: media_type, folder, status, search
    """

    queryset = Media.objects.filter(deleted_at__isnull=True).order_by("-created_at")
    serializer_class = MediaListSerializer
    filterset_class = MediaFilter


class MediaUploadView(MediaCreateMixin, generics.CreateAPIView):
    """
    Upload a media file.

    Requires: media.create permission.
    Accepts multipart/form-data with a file field.
    """

    queryset = Media.objects.filter(deleted_at__isnull=True)
    serializer_class = MediaUploadSerializer
    parser_classes = [parsers.MultiPartParser, parsers.FormParser]

    def perform_create(self, serializer):
        file_obj = self.request.FILES.get("file")
        if not file_obj:
            return

        # Detect media type from MIME
        mime_type = file_obj.content_type or ""
        if mime_type.startswith("image/"):
            media_type = "IMAGE"
        elif mime_type.startswith("video/"):
            media_type = "VIDEO"
        elif mime_type == "application/pdf":
            media_type = "DOCUMENT"
        elif mime_type.startswith("audio/"):
            media_type = "AUDIO"
        else:
            media_type = "DOCUMENT"

        # Get image dimensions if applicable
        width, height = None, None
        if media_type == "IMAGE":
            try:
                from PIL import Image

                img = Image.open(file_obj)
                width, height = img.size
                file_obj.seek(0)
            except Exception:
                pass

        # Accept is_public from request data (defaults to False)
        is_public = self.request.data.get("is_public", False)
        if isinstance(is_public, str):
            is_public = is_public.lower() in ("true", "1", "yes")

        serializer.save(
            organization=self.request.organization,
            uploaded_by=self.request.user,
            original_filename=file_obj.name,
            file_size=file_obj.size,
            mime_type=mime_type,
            media_type=media_type,
            width=width,
            height=height,
            status="READY",
            is_public=bool(is_public),
        )


class MediaDetailView(TenantMediaMixin, generics.RetrieveUpdateAPIView):
    """
    Retrieve or update a media file's metadata.

    GET:       Requires media.view.
    PUT/PATCH: Requires media.update.
    """

    queryset = Media.objects.filter(deleted_at__isnull=True)
    serializer_class = MediaDetailSerializer

    def get_permission_classes(self):
        if self.request.method in ("PUT", "PATCH"):
            return [HasOrganizationPermission("media.update")]
        return [HasOrganizationPermission("media.view")]

    def get_permissions(self):
        return [
            perm() if isinstance(perm, type) else perm
            for perm in self.get_permission_classes()
        ]


class MediaDeleteView(MediaDeleteMixin, generics.DestroyAPIView):
    """
    Soft-delete a media file.

    Requires: media.delete permission.
    """

    queryset = Media.objects.filter(deleted_at__isnull=True)

    def perform_destroy(self, instance):
        instance.deleted_at = timezone.now()
        instance.save(update_fields=["deleted_at"])
