"""
API Views for the Media application.

Handles file uploads, listing, detail, update, and soft-delete.
All views are tenant-scoped via organization filter and protected
by RBAC permissions (media.view, media.create, media.update, media.delete).

Admin/staff users accessing via the Media Library admin page are
granted implicit access — they authenticate through Django session
and do not need explicit CASL permissions.
"""

import logging

from django.db.models import Q
from django.utils import timezone
from django_filters import rest_framework as filters
from rest_framework import (
    generics,
    parsers,
    permissions,
    serializers as drf_serializers,
)

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
        """Search by name, title, and original_filename."""
        return queryset.filter(
            Q(name__icontains=value)
            | Q(title__icontains=value)
            | Q(original_filename__icontains=value)
        )


# =============================================================================
# MIXINS
# =============================================================================


class TenantMediaMixin:
    """
    Filter media data by the requesting user's organization.

    Tenant resolution order:
    1. Superusers see ALL media (cross-org visibility)
    2. Staff users with org context → their org's media
    3. Staff users without org → user.organization fallback
    4. Staff users with no org at all → all media (platform admin)
    5. Regular API users → strict tenant filtering
    """

    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user

        # Superusers see ALL media across organizations
        if user.is_superuser:
            return qs

        # Try request.organization (set by TenantMiddleware)
        organization = getattr(self.request, "organization", None)

        # Fallback for staff: admin panel JS calls /api/v1/media/ but
        # TenantMiddleware may not have resolved org for this user.
        if not organization and user.is_staff:
            organization = getattr(user, "organization", None)

        if organization:
            return qs.filter(organization=organization)

        # Staff without any org = platform admin → show all
        if user.is_staff:
            return qs

        return qs.none()

    def get_permissions(self):
        """
        Staff/superuser bypass CASL permission checks.
        Regular API users need explicit HasOrganizationPermission.
        """
        if hasattr(self, "request") and hasattr(self.request, "user"):
            user = self.request.user
            if user.is_authenticated and (user.is_staff or user.is_superuser):
                return [permissions.IsAuthenticated()]

        return [
            perm() if isinstance(perm, type) else perm
            for perm in self.permission_classes
        ]


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

    def get_serializer_class(self):
        if self.request.method == "POST":
            return MediaFolderCreateSerializer
        return MediaFolderSerializer

    def perform_create(self, serializer):
        org = getattr(self.request, "organization", None)
        if not org:
            org = getattr(self.request.user, "organization", None)
        serializer.save(organization=org)


class MediaFolderDetailView(TenantMediaMixin, generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update, or soft-delete a media folder.

    GET:    Requires media.view.
    PUT/PATCH: Requires media.update.
    DELETE: Requires media.delete.
    """

    queryset = MediaFolder.objects.filter(deleted_at__isnull=True)
    serializer_class = MediaFolderSerializer

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

    queryset = (
        Media.objects.filter(deleted_at__isnull=True)
        .select_related("organization", "folder", "uploaded_by")
        .order_by("-created_at")
    )
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
        class IsPublicSerializer(drf_serializers.Serializer):
            is_public = drf_serializers.BooleanField(default=False, required=False)

        pub_serializer = IsPublicSerializer(data=self.request.data)
        pub_serializer.is_valid(raise_exception=True)
        is_public = pub_serializer.validated_data.get("is_public", False)

        # Resolve organization — request.organization or user's org fallback
        org = getattr(self.request, "organization", None)
        if not org:
            org = getattr(self.request.user, "organization", None)

        serializer.save(
            organization=org,
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

    GET:       Requires media.view (or staff status).
    PUT/PATCH: Requires media.update (or staff status).
    """

    queryset = Media.objects.filter(deleted_at__isnull=True).select_related(
        "organization", "folder", "uploaded_by"
    )
    serializer_class = MediaDetailSerializer


class MediaDeleteView(MediaDeleteMixin, generics.DestroyAPIView):
    """
    Soft-delete a media file.

    Requires: media.delete permission.
    """

    queryset = Media.objects.filter(deleted_at__isnull=True)

    def perform_destroy(self, instance):
        instance.deleted_at = timezone.now()
        instance.save(update_fields=["deleted_at"])
