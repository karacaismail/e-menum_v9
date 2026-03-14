"""
Django TextChoices enums for media module.

These enums define the valid values for status fields and other constrained
string fields across the media domain models (Media, MediaFolder).

Usage:
    from apps.media.choices import MediaType, MediaStorage

    class Media(models.Model):
        media_type = models.CharField(
            max_length=20,
            choices=MediaType.choices,
            default=MediaType.IMAGE
        )
"""

from django.db import models


class MediaType(models.TextChoices):
    """
    Type values for media files.

    - IMAGE: Image files (JPEG, PNG, GIF, WebP, etc.)
    - VIDEO: Video files (MP4, MOV, WebM, etc.)
    - DOCUMENT: Document files (PDF, DOC, etc.)
    - AUDIO: Audio files (MP3, WAV, etc.)
    """

    IMAGE = "IMAGE", "Image"
    VIDEO = "VIDEO", "Video"
    DOCUMENT = "DOCUMENT", "Document"
    AUDIO = "AUDIO", "Audio"


class MediaStorage(models.TextChoices):
    """
    Storage backend options for media files.

    - LOCAL: Local filesystem storage (development/simple deployments)
    - S3: Amazon S3 or S3-compatible storage
    - CLOUDINARY: Cloudinary CDN (image/video optimization)
    - GCS: Google Cloud Storage
    - AZURE: Azure Blob Storage
    """

    LOCAL = "LOCAL", "Local Storage"
    S3 = "S3", "Amazon S3"
    CLOUDINARY = "CLOUDINARY", "Cloudinary"
    GCS = "GCS", "Google Cloud Storage"
    AZURE = "AZURE", "Azure Blob Storage"


class MediaStatus(models.TextChoices):
    """
    Processing status for media files.

    - PENDING: File uploaded, awaiting processing
    - PROCESSING: File is being processed (thumbnails, optimization)
    - READY: File is ready for use
    - FAILED: Processing failed
    """

    PENDING = "PENDING", "Pending"
    PROCESSING = "PROCESSING", "Processing"
    READY = "READY", "Ready"
    FAILED = "FAILED", "Failed"
