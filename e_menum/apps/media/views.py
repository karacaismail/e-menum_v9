"""
API Views for the Media application.

Handles file uploads, listing, detail, update, and soft-delete.
All views are tenant-scoped via organization filter.
"""

import logging
import mimetypes
import os

from django.utils import timezone
from django_filters import rest_framework as filters
from rest_framework import generics, parsers, permissions, status
from rest_framework.response import Response

from apps.media.models import Media, MediaFolder
from apps.media.serializers import (
    MediaDetailSerializer,
    MediaFolderCreateSerializer,
    MediaFolderSerializer,
    MediaListSerializer,
    MediaUploadSerializer,
)

logger = logging.getLogger(__name__)


# =============================================================================
# FILTERS
# =============================================================================


class MediaFilter(filters.FilterSet):
    media_type = filters.CharFilter(field_name='media_type')
    folder = filters.UUIDFilter(field_name='folder_id')
    status = filters.CharFilter(field_name='status')
    search = filters.CharFilter(method='filter_search')

    class Meta:
        model = Media
        fields = ['media_type', 'folder', 'status']

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
        organization = getattr(self.request, 'organization', None)
        if organization:
            return qs.filter(organization=organization)
        return qs.none()


# =============================================================================
# FOLDER VIEWS
# =============================================================================


class MediaFolderListCreateView(TenantMediaMixin, generics.ListCreateAPIView):
    """
    List or create media folders.
    GET: List all folders for the organization
    POST: Create a new folder
    """
    queryset = MediaFolder.objects.filter(deleted_at__isnull=True).order_by('name')

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return MediaFolderCreateSerializer
        return MediaFolderSerializer

    def perform_create(self, serializer):
        serializer.save(organization=self.request.organization)


class MediaFolderDetailView(TenantMediaMixin, generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, or soft-delete a media folder."""
    queryset = MediaFolder.objects.filter(deleted_at__isnull=True)
    serializer_class = MediaFolderSerializer

    def perform_destroy(self, instance):
        # Soft delete
        instance.deleted_at = timezone.now()
        instance.save(update_fields=['deleted_at'])


# =============================================================================
# MEDIA VIEWS
# =============================================================================


class MediaListView(TenantMediaMixin, generics.ListAPIView):
    """
    List media files for the organization.
    Filters: media_type, folder, status, search
    """
    queryset = Media.objects.filter(deleted_at__isnull=True).order_by('-created_at')
    serializer_class = MediaListSerializer
    filterset_class = MediaFilter


class MediaUploadView(TenantMediaMixin, generics.CreateAPIView):
    """
    Upload a media file.
    Accepts multipart/form-data with a file field.
    """
    queryset = Media.objects.filter(deleted_at__isnull=True)
    serializer_class = MediaUploadSerializer
    parser_classes = [parsers.MultiPartParser, parsers.FormParser]

    def perform_create(self, serializer):
        file_obj = self.request.FILES.get('file')
        if not file_obj:
            return

        # Detect media type from MIME
        mime_type = file_obj.content_type or ''
        if mime_type.startswith('image/'):
            media_type = 'IMAGE'
        elif mime_type.startswith('video/'):
            media_type = 'VIDEO'
        elif mime_type == 'application/pdf':
            media_type = 'DOCUMENT'
        elif mime_type.startswith('audio/'):
            media_type = 'AUDIO'
        else:
            media_type = 'DOCUMENT'

        # Get image dimensions if applicable
        width, height = None, None
        if media_type == 'IMAGE':
            try:
                from PIL import Image
                img = Image.open(file_obj)
                width, height = img.size
                file_obj.seek(0)
            except Exception:
                pass

        serializer.save(
            organization=self.request.organization,
            uploaded_by=self.request.user,
            original_filename=file_obj.name,
            file_size=file_obj.size,
            mime_type=mime_type,
            media_type=media_type,
            width=width,
            height=height,
            status='READY',
        )


class MediaDetailView(TenantMediaMixin, generics.RetrieveUpdateAPIView):
    """Retrieve or update a media file's metadata."""
    queryset = Media.objects.filter(deleted_at__isnull=True)
    serializer_class = MediaDetailSerializer


class MediaDeleteView(TenantMediaMixin, generics.DestroyAPIView):
    """Soft-delete a media file."""
    queryset = Media.objects.filter(deleted_at__isnull=True)

    def perform_destroy(self, instance):
        instance.deleted_at = timezone.now()
        instance.save(update_fields=['deleted_at'])
