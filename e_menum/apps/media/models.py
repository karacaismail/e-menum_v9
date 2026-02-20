"""
Django ORM models for the Media application.

This module defines the media-related models for E-Menum:
- MediaFolder: Hierarchical folder structure for organizing media
- Media: Individual media files (images, videos, documents, audio)

Critical Rules:
- Every query MUST include organization_id for tenant isolation
- All entities use soft delete (deleted_at timestamp)
- No physical deletions allowed (use soft_delete method)
- Media files should be stored in tenant-isolated paths
"""

import uuid
from pathlib import Path

from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.core.models import (
    Organization,
    SoftDeleteManager,
    SoftDeleteMixin,
    TimeStampedMixin,
    User,
)
from apps.media.choices import (
    MediaStatus,
    MediaStorage,
    MediaType,
)


class MediaFolder(TimeStampedMixin, SoftDeleteMixin, models.Model):
    """
    MediaFolder model - hierarchical folder structure for organizing media.

    Supports nested folders for organizing media assets within an organization.
    Folders can be public (accessible without auth) or private (requires auth).

    Critical Rules:
    - EVERY query MUST filter by organization (multi-tenant isolation)
    - Use soft_delete() - never call delete() directly
    - Slug is unique within parent folder scope

    Attributes:
        id: UUID primary key (ensures global uniqueness)
        organization: FK to parent Organization (tenant isolation)
        parent: Self-referential FK for nested folder structure
        name: Display name of the folder
        slug: URL-friendly identifier (unique within parent)
        description: Optional folder description
        is_public: Whether folder contents are publicly accessible
        sort_order: Display order within parent folder
        metadata: JSON field for custom folder attributes

    Usage:
        # Create a root folder
        folder = MediaFolder.objects.create(
            organization=org,
            name="Product Images",
            slug="product-images"
        )

        # Create a nested folder
        subfolder = MediaFolder.objects.create(
            organization=org,
            parent=folder,
            name="Burgers",
            slug="burgers"
        )

        # Query folders for organization (ALWAYS filter by organization!)
        folders = MediaFolder.objects.filter(organization=org)

        # Get root folders only
        root_folders = MediaFolder.objects.filter(
            organization=org,
            parent__isnull=True
        )

        # Soft delete folder (NEVER use delete())
        folder.soft_delete()
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name=_('ID'),
        help_text=_('Unique identifier (UUID)')
    )

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='media_folders',
        verbose_name=_('Organization'),
        help_text=_('Organization this folder belongs to')
    )

    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children',
        verbose_name=_('Parent folder'),
        help_text=_('Parent folder for nesting (null = root folder)')
    )

    # Identity
    name = models.CharField(
        max_length=255,
        verbose_name=_('Name'),
        help_text=_('Display name of the folder')
    )

    slug = models.SlugField(
        max_length=100,
        verbose_name=_('Slug'),
        help_text=_('URL-friendly identifier (unique within parent)')
    )

    description = models.TextField(
        blank=True,
        null=True,
        verbose_name=_('Description'),
        help_text=_('Optional folder description')
    )

    # Access control
    is_public = models.BooleanField(
        default=False,
        verbose_name=_('Is public'),
        help_text=_('Whether folder contents are publicly accessible')
    )

    # Ordering
    sort_order = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Sort order'),
        help_text=_('Display order within parent folder')
    )

    # Additional data
    metadata = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_('Metadata'),
        help_text=_('Custom folder attributes (JSON)')
    )

    # Managers
    objects = SoftDeleteManager()  # Default: excludes soft-deleted
    all_objects = models.Manager()  # Includes ALL records

    class Meta:
        db_table = 'media_folders'
        verbose_name = _('Media Folder')
        verbose_name_plural = _('Media Folders')
        ordering = ['sort_order', 'name']
        unique_together = [['organization', 'parent', 'slug']]
        indexes = [
            models.Index(fields=['organization', 'deleted_at'], name='mediafolder_org_deleted_idx'),
            models.Index(fields=['organization', 'parent'], name='mediafolder_org_parent_idx'),
            models.Index(fields=['parent', 'sort_order'], name='mediafolder_parent_sort_idx'),
        ]

    def __str__(self) -> str:
        return f"{self.name} ({self.organization.name})"

    def __repr__(self) -> str:
        return f"<MediaFolder(id={self.id}, name='{self.name}', org='{self.organization.name}')>"

    @property
    def is_root(self) -> bool:
        """Check if this is a root folder (no parent)."""
        return self.parent is None

    @property
    def media_count(self) -> int:
        """Return the count of media files in this folder."""
        return self.media_files.filter(deleted_at__isnull=True).count()

    @property
    def children_count(self) -> int:
        """Return the count of child folders."""
        return self.children.filter(deleted_at__isnull=True).count()

    def get_ancestors(self):
        """
        Return list of ancestor folders from root to immediate parent.

        Returns:
            List of MediaFolder instances from root to parent
        """
        ancestors = []
        current = self.parent
        while current is not None:
            ancestors.insert(0, current)
            current = current.parent
        return ancestors

    def get_descendants(self):
        """
        Return all descendant folders (recursive children).

        Returns:
            QuerySet of all descendant MediaFolder instances
        """
        descendants = list(self.children.filter(deleted_at__isnull=True))
        for child in list(descendants):
            descendants.extend(child.get_descendants())
        return descendants

    def get_full_path(self) -> str:
        """
        Return the full path from root to this folder.

        Returns:
            str: Path like "root/parent/current"
        """
        ancestors = self.get_ancestors()
        path_parts = [a.slug for a in ancestors] + [self.slug]
        return '/'.join(path_parts)

    def get_breadcrumb(self) -> list:
        """
        Return breadcrumb data for navigation.

        Returns:
            List of dicts with 'id', 'name', 'slug' for each ancestor + self
        """
        breadcrumb = []
        for ancestor in self.get_ancestors():
            breadcrumb.append({
                'id': str(ancestor.id),
                'name': ancestor.name,
                'slug': ancestor.slug,
            })
        breadcrumb.append({
            'id': str(self.id),
            'name': self.name,
            'slug': self.slug,
        })
        return breadcrumb


class Media(TimeStampedMixin, SoftDeleteMixin, models.Model):
    """
    Media model - represents individual media files (images, videos, documents, audio).

    Media files are stored with tenant isolation and support multiple storage backends.
    Each media item can be organized into folders and have rich metadata for SEO and
    accessibility purposes.

    Critical Rules:
    - EVERY query MUST filter by organization (multi-tenant isolation)
    - Use soft_delete() - never call delete() directly
    - File paths should include organization ID for tenant isolation

    Attributes:
        id: UUID primary key (ensures global uniqueness)
        organization: FK to parent Organization (tenant isolation)
        folder: Optional FK to MediaFolder for organization
        uploaded_by: FK to User who uploaded the file
        name: Display name of the media
        original_filename: Original filename when uploaded
        file_path: Path or key to the stored file
        url: Public URL to access the file
        storage: Storage backend used (LOCAL, S3, etc.)
        media_type: Type of media (IMAGE, VIDEO, DOCUMENT, AUDIO)
        status: Processing status (PENDING, PROCESSING, READY, FAILED)
        mime_type: MIME type of the file
        file_size: Size in bytes
        width: Width in pixels (for images/videos)
        height: Height in pixels (for images/videos)
        duration: Duration in seconds (for videos/audio)
        thumbnail_url: URL to thumbnail image
        alt_text: Alt text for accessibility
        title: Title for SEO
        caption: Caption or description
        is_public: Whether media is publicly accessible
        metadata: Additional file metadata (EXIF, etc.)

    Usage:
        # Create a media record
        media = Media.objects.create(
            organization=org,
            folder=product_images_folder,
            uploaded_by=user,
            name="Burger Photo",
            original_filename="burger-001.jpg",
            file_path="orgs/{org_id}/media/burger-001.jpg",
            url="https://cdn.example.com/orgs/{org_id}/media/burger-001.jpg",
            storage=MediaStorage.S3,
            media_type=MediaType.IMAGE,
            mime_type="image/jpeg",
            file_size=245000,
            width=1920,
            height=1080
        )

        # Query media for organization (ALWAYS filter by organization!)
        media_items = Media.objects.filter(organization=org)

        # Get images only
        images = Media.objects.filter(
            organization=org,
            media_type=MediaType.IMAGE
        )

        # Soft delete media (NEVER use delete())
        media.soft_delete()
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name=_('ID'),
        help_text=_('Unique identifier (UUID)')
    )

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='media_files',
        verbose_name=_('Organization'),
        help_text=_('Organization this media belongs to')
    )

    folder = models.ForeignKey(
        MediaFolder,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='media_files',
        verbose_name=_('Folder'),
        help_text=_('Folder containing this media (null = root/unfiled)')
    )

    uploaded_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='uploaded_media',
        verbose_name=_('Uploaded by'),
        help_text=_('User who uploaded this media')
    )

    # Identity
    name = models.CharField(
        max_length=255,
        verbose_name=_('Name'),
        help_text=_('Display name of the media')
    )

    original_filename = models.CharField(
        max_length=500,
        verbose_name=_('Original filename'),
        help_text=_('Original filename when uploaded')
    )

    # Storage
    file_path = models.CharField(
        max_length=1000,
        verbose_name=_('File path'),
        help_text=_('Path or key to the stored file')
    )

    url = models.URLField(
        max_length=2000,
        blank=True,
        null=True,
        verbose_name=_('URL'),
        help_text=_('Public URL to access the file')
    )

    storage = models.CharField(
        max_length=20,
        choices=MediaStorage.choices,
        default=MediaStorage.LOCAL,
        verbose_name=_('Storage'),
        help_text=_('Storage backend used')
    )

    # Type and status
    media_type = models.CharField(
        max_length=20,
        choices=MediaType.choices,
        default=MediaType.IMAGE,
        db_index=True,
        verbose_name=_('Media type'),
        help_text=_('Type of media file')
    )

    status = models.CharField(
        max_length=20,
        choices=MediaStatus.choices,
        default=MediaStatus.PENDING,
        db_index=True,
        verbose_name=_('Status'),
        help_text=_('Processing status')
    )

    # Technical metadata
    mime_type = models.CharField(
        max_length=100,
        verbose_name=_('MIME type'),
        help_text=_('MIME type of the file (e.g., image/jpeg)')
    )

    file_size = models.PositiveBigIntegerField(
        verbose_name=_('File size'),
        help_text=_('File size in bytes')
    )

    # Dimensions (for images/videos)
    width = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=_('Width'),
        help_text=_('Width in pixels (for images/videos)')
    )

    height = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=_('Height'),
        help_text=_('Height in pixels (for images/videos)')
    )

    # Duration (for videos/audio)
    duration = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=_('Duration'),
        help_text=_('Duration in seconds (for videos/audio)')
    )

    # Thumbnail
    thumbnail_url = models.URLField(
        max_length=2000,
        blank=True,
        null=True,
        verbose_name=_('Thumbnail URL'),
        help_text=_('URL to thumbnail image')
    )

    # SEO and accessibility
    alt_text = models.CharField(
        max_length=500,
        blank=True,
        null=True,
        verbose_name=_('Alt text'),
        help_text=_('Alt text for accessibility (required for images)')
    )

    title = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name=_('Title'),
        help_text=_('Title for SEO purposes')
    )

    caption = models.TextField(
        blank=True,
        null=True,
        verbose_name=_('Caption'),
        help_text=_('Caption or description of the media')
    )

    # Access control
    is_public = models.BooleanField(
        default=False,
        verbose_name=_('Is public'),
        help_text=_('Whether media is publicly accessible without authentication')
    )

    # Additional data
    metadata = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_('Metadata'),
        help_text=_('Additional file metadata (EXIF, custom fields, etc.)')
    )

    # Usage tracking
    usage_count = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Usage count'),
        help_text=_('Number of times this media is used in content')
    )

    last_used_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Last used at'),
        help_text=_('When this media was last used in content')
    )

    # Managers
    objects = SoftDeleteManager()  # Default: excludes soft-deleted
    all_objects = models.Manager()  # Includes ALL records

    class Meta:
        db_table = 'media'
        verbose_name = _('Media')
        verbose_name_plural = _('Media')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['organization', 'deleted_at'], name='media_org_deleted_idx'),
            models.Index(fields=['organization', 'folder'], name='media_org_folder_idx'),
            models.Index(fields=['organization', 'media_type'], name='media_org_type_idx'),
            models.Index(fields=['organization', 'status'], name='media_org_status_idx'),
            models.Index(fields=['organization', 'is_public'], name='media_org_public_idx'),
            models.Index(fields=['created_at'], name='media_created_idx'),
        ]

    def __str__(self) -> str:
        return f"{self.name} ({self.media_type})"

    def __repr__(self) -> str:
        return f"<Media(id={self.id}, name='{self.name}', type={self.media_type})>"

    @property
    def is_image(self) -> bool:
        """Check if this is an image file."""
        return self.media_type == MediaType.IMAGE

    @property
    def is_video(self) -> bool:
        """Check if this is a video file."""
        return self.media_type == MediaType.VIDEO

    @property
    def is_document(self) -> bool:
        """Check if this is a document file."""
        return self.media_type == MediaType.DOCUMENT

    @property
    def is_audio(self) -> bool:
        """Check if this is an audio file."""
        return self.media_type == MediaType.AUDIO

    @property
    def is_ready(self) -> bool:
        """Check if media processing is complete and ready for use."""
        return self.status == MediaStatus.READY

    @property
    def file_extension(self) -> str:
        """Return the file extension from the original filename."""
        return Path(self.original_filename).suffix.lower()

    @property
    def dimensions(self) -> str:
        """Return dimensions as a string (e.g., '1920x1080')."""
        if self.width and self.height:
            return f"{self.width}x{self.height}"
        return None

    @property
    def human_readable_size(self) -> str:
        """Return file size in human-readable format."""
        if self.file_size is None:
            return "0 B"
        size = float(self.file_size)
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} PB"

    @property
    def duration_formatted(self) -> str:
        """Return duration in human-readable format (MM:SS or HH:MM:SS)."""
        if self.duration is None:
            return None
        hours, remainder = divmod(self.duration, 3600)
        minutes, seconds = divmod(remainder, 60)
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        return f"{minutes:02d}:{seconds:02d}"

    def mark_processing(self) -> None:
        """Mark media as currently being processed."""
        self.status = MediaStatus.PROCESSING
        self.save(update_fields=['status', 'updated_at'])

    def mark_ready(self, url: str = None, thumbnail_url: str = None) -> None:
        """
        Mark media as ready for use.

        Args:
            url: Optional URL to set
            thumbnail_url: Optional thumbnail URL to set
        """
        self.status = MediaStatus.READY
        update_fields = ['status', 'updated_at']

        if url:
            self.url = url
            update_fields.append('url')
        if thumbnail_url:
            self.thumbnail_url = thumbnail_url
            update_fields.append('thumbnail_url')

        self.save(update_fields=update_fields)

    def mark_failed(self, error_message: str = None) -> None:
        """
        Mark media processing as failed.

        Args:
            error_message: Optional error message to store in metadata
        """
        self.status = MediaStatus.FAILED
        if error_message:
            self.metadata['error'] = error_message
            self.metadata['failed_at'] = timezone.now().isoformat()
        self.save(update_fields=['status', 'metadata', 'updated_at'])

    def record_usage(self) -> None:
        """Record that this media was used in content."""
        self.usage_count += 1
        self.last_used_at = timezone.now()
        self.save(update_fields=['usage_count', 'last_used_at', 'updated_at'])

    def move_to_folder(self, folder) -> None:
        """
        Move media to a different folder.

        Args:
            folder: MediaFolder instance or None for root
        """
        self.folder = folder
        self.save(update_fields=['folder', 'updated_at'])

    def get_metadata(self, key: str, default=None):
        """Get a value from media metadata."""
        return self.metadata.get(key, default)

    def set_metadata(self, key: str, value) -> None:
        """Set a value in media metadata."""
        self.metadata[key] = value
        self.save(update_fields=['metadata', 'updated_at'])
