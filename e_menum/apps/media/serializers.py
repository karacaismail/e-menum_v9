"""
DRF Serializers for the Media application.
"""

from rest_framework import serializers

from apps.media.models import Media, MediaFolder


class MediaFolderSerializer(serializers.ModelSerializer):
    """Serializer for media folders."""
    children_count = serializers.SerializerMethodField()
    media_count = serializers.SerializerMethodField()

    class Meta:
        model = MediaFolder
        fields = [
            'id', 'name', 'slug', 'parent',
            'children_count', 'media_count',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'slug', 'created_at', 'updated_at']

    def get_children_count(self, obj):
        return obj.children.filter(deleted_at__isnull=True).count()

    def get_media_count(self, obj):
        return obj.media_files.filter(deleted_at__isnull=True).count()


class MediaFolderCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating media folders."""

    class Meta:
        model = MediaFolder
        fields = ['name', 'parent']


class MediaListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for media listing."""
    folder_name = serializers.CharField(source='folder.name', read_only=True, default=None)

    class Meta:
        model = Media
        fields = [
            'id', 'title', 'file', 'media_type', 'mime_type',
            'file_size', 'width', 'height',
            'folder', 'folder_name',
            'alt_text', 'status',
            'usage_count', 'created_at',
        ]
        read_only_fields = [
            'id', 'media_type', 'mime_type', 'file_size',
            'width', 'height', 'status', 'usage_count', 'created_at',
        ]


class MediaDetailSerializer(serializers.ModelSerializer):
    """Full serializer for media detail."""
    folder_name = serializers.CharField(source='folder.name', read_only=True, default=None)

    class Meta:
        model = Media
        fields = [
            'id', 'title', 'original_filename', 'file', 'file_url',
            'media_type', 'mime_type', 'file_size',
            'width', 'height',
            'folder', 'folder_name',
            'alt_text', 'caption', 'seo_title',
            'storage_backend', 'status',
            'usage_count', 'last_used_at',
            'metadata',
            'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'original_filename', 'file_url',
            'media_type', 'mime_type', 'file_size',
            'width', 'height', 'storage_backend', 'status',
            'usage_count', 'last_used_at',
            'created_at', 'updated_at',
        ]


class MediaUploadSerializer(serializers.ModelSerializer):
    """Serializer for uploading media files."""

    class Meta:
        model = Media
        fields = ['file', 'folder', 'title', 'alt_text', 'caption']
        extra_kwargs = {
            'file': {'required': True},
            'folder': {'required': False},
        }

    def validate_file(self, value):
        # Max 10MB
        if value.size > 10 * 1024 * 1024:
            raise serializers.ValidationError('Dosya boyutu 10MB\'dan buyuk olamaz.')

        # Allowed types
        allowed_types = [
            'image/jpeg', 'image/png', 'image/gif', 'image/webp', 'image/svg+xml',
            'video/mp4', 'video/webm',
            'application/pdf',
        ]
        if value.content_type not in allowed_types:
            raise serializers.ValidationError(
                f'Desteklenmeyen dosya tipi: {value.content_type}'
            )
        return value
