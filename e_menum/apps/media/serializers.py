"""
DRF Serializers for the Media application.

Field mapping (serializer ↔ model):
- name             → Media.name
- original_filename → Media.original_filename
- url              → Media.url
- thumbnail_url    → Media.thumbnail_url
- file_path        → Media.file_path
- storage          → Media.storage
- title            → Media.title
"""

from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from apps.media.models import Media, MediaFolder


class MediaFolderSerializer(serializers.ModelSerializer):
    """Serializer for media folders."""

    children_count = serializers.SerializerMethodField()
    media_count = serializers.SerializerMethodField()

    class Meta:
        model = MediaFolder
        fields = [
            "id",
            "name",
            "slug",
            "parent",
            "children_count",
            "media_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "slug", "created_at", "updated_at"]

    def get_children_count(self, obj):
        return obj.children.filter(deleted_at__isnull=True).count()

    def get_media_count(self, obj):
        return obj.media_files.filter(deleted_at__isnull=True).count()


class MediaFolderCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating media folders."""

    class Meta:
        model = MediaFolder
        fields = ["name", "parent"]


class MediaListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for media listing.

    Includes every field the Media Library JS template expects:
    id, name, original_filename, url, thumbnail_url, media_type,
    mime_type, file_size, width, height, folder, alt_text, title,
    caption, status, is_public, is_image, created_at.
    """

    folder_name = serializers.CharField(
        source="folder.name", read_only=True, default=None
    )
    is_image = serializers.SerializerMethodField()
    uploaded_by_email = serializers.CharField(
        source="uploaded_by.email", read_only=True, default=None
    )
    organization_name = serializers.CharField(
        source="organization.name", read_only=True, default=None
    )

    class Meta:
        model = Media
        fields = [
            "id",
            "name",
            "original_filename",
            "url",
            "thumbnail_url",
            "media_type",
            "mime_type",
            "file_size",
            "width",
            "height",
            "folder",
            "folder_name",
            "alt_text",
            "title",
            "caption",
            "status",
            "is_public",
            "is_image",
            "usage_count",
            "uploaded_by_email",
            "organization_name",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "original_filename",
            "url",
            "thumbnail_url",
            "media_type",
            "mime_type",
            "file_size",
            "width",
            "height",
            "status",
            "usage_count",
            "created_at",
        ]

    def get_is_image(self, obj):
        return obj.media_type == "IMAGE"


class MediaDetailSerializer(serializers.ModelSerializer):
    """Full serializer for media detail."""

    folder_name = serializers.CharField(
        source="folder.name", read_only=True, default=None
    )
    is_image = serializers.SerializerMethodField()
    uploaded_by_email = serializers.CharField(
        source="uploaded_by.email", read_only=True, default=None
    )
    organization_name = serializers.CharField(
        source="organization.name", read_only=True, default=None
    )

    class Meta:
        model = Media
        fields = [
            "id",
            "name",
            "original_filename",
            "url",
            "thumbnail_url",
            "file_path",
            "media_type",
            "mime_type",
            "file_size",
            "width",
            "height",
            "folder",
            "folder_name",
            "alt_text",
            "title",
            "caption",
            "storage",
            "status",
            "is_public",
            "is_image",
            "usage_count",
            "last_used_at",
            "uploaded_by_email",
            "organization_name",
            "metadata",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "original_filename",
            "url",
            "thumbnail_url",
            "file_path",
            "media_type",
            "mime_type",
            "file_size",
            "width",
            "height",
            "storage",
            "status",
            "usage_count",
            "last_used_at",
            "created_at",
            "updated_at",
        ]

    def get_is_image(self, obj):
        return obj.media_type == "IMAGE"


class MediaUploadSerializer(serializers.Serializer):
    """Serializer for uploading media files.

    This is a plain Serializer (not ModelSerializer) because the Media
    model stores file_path as a CharField — there is no FileField on
    the model.  The view's perform_create() handles file saving and
    passes the resolved fields to Media.objects.create().
    """

    file = serializers.FileField(required=True)
    folder = serializers.UUIDField(required=False, allow_null=True)
    title = serializers.CharField(required=False, allow_blank=True, default="")
    alt_text = serializers.CharField(required=False, allow_blank=True, default="")
    caption = serializers.CharField(required=False, allow_blank=True, default="")

    def validate_file(self, value):
        # Max 10MB
        if value.size > 10 * 1024 * 1024:
            raise serializers.ValidationError(_("Dosya boyutu 10MB'dan buyuk olamaz."))

        # Allowed types
        allowed_types = [
            "image/jpeg",
            "image/png",
            "image/gif",
            "image/webp",
            "image/svg+xml",
            "video/mp4",
            "video/webm",
            "application/pdf",
        ]
        if value.content_type not in allowed_types:
            raise serializers.ValidationError(
                f"Desteklenmeyen dosya tipi: {value.content_type}"
            )
        return value

    def create(self, validated_data):
        """Create a Media instance.

        The view's perform_create() passes extra kwargs (organization,
        uploaded_by, mime_type, etc.) which arrive here via **validated_data.
        """
        validated_data.pop("file", None)
        return Media.objects.create(**validated_data)
