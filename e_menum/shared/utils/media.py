"""
Media upload utilities for E-Menum.

Provides upload path factories for django-filer and standard Django file fields.
All uploaded files are organized by restaurant (organization) with UUID4 filenames
to prevent conflicts and preserve privacy.

Directory Structure:
    media/{restaurant_id}/menu_items/{uuid4}.{ext}
    media/{restaurant_id}/logos/{uuid4}.{ext}
    media/{restaurant_id}/gallery/{uuid4}.{ext}

Usage:
    from shared.utils.media import restaurant_upload_path

    class Product(models.Model):
        image = models.ImageField(upload_to=restaurant_upload_path)
"""

from uuid import uuid4


def restaurant_upload_path(instance, filename):
    """
    Generate upload path isolated per restaurant.

    Creates path: {org_id}/menu_items/{uuid4}.{ext}

    Args:
        instance: Model instance being uploaded to
        filename: Original filename

    Returns:
        str: Upload path relative to MEDIA_ROOT
    """
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "bin"
    new_filename = f"{uuid4()}.{ext}"

    # Try to get organization_id from the instance
    org_id = _get_org_id(instance)

    return f"{org_id}/menu_items/{new_filename}"


def restaurant_logo_path(instance, filename):
    """
    Generate upload path for restaurant logos.

    Creates path: {org_id}/logos/{uuid4}.{ext}
    """
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "png"
    new_filename = f"{uuid4()}.{ext}"
    org_id = _get_org_id(instance)
    return f"{org_id}/logos/{new_filename}"


def restaurant_gallery_path(instance, filename):
    """
    Generate upload path for restaurant gallery images.

    Creates path: {org_id}/gallery/{uuid4}.{ext}
    """
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "jpg"
    new_filename = f"{uuid4()}.{ext}"
    org_id = _get_org_id(instance)
    return f"{org_id}/gallery/{new_filename}"


def filer_upload_path(instance, filename):
    """
    Upload path factory for django-filer.

    Used in FILER_STORAGES settings to route filer uploads
    into per-organization directories.

    Args:
        instance: Filer File/Image instance
        filename: Original filename

    Returns:
        str: Upload path relative to filer storage root
    """
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "bin"
    new_filename = f"{uuid4()}.{ext}"

    # Filer files have a folder hierarchy; use folder name as org_id if available
    if hasattr(instance, "folder") and instance.folder:
        # Walk up to find root folder (which is the org_id)
        folder = instance.folder
        while folder.parent:
            folder = folder.parent
        org_id = folder.name
        return f"{org_id}/{new_filename}"

    return f"global/{new_filename}"


def _get_org_id(instance):
    """
    Extract organization ID from a model instance.

    Tries multiple attribute paths to find the organization ID.

    Args:
        instance: Django model instance

    Returns:
        str: Organization ID or 'global'
    """
    # Direct organization FK
    if hasattr(instance, "organization_id") and instance.organization_id:
        return str(instance.organization_id)

    # Via organization object
    if hasattr(instance, "organization") and instance.organization:
        return str(instance.organization.id)

    # Via product → organization
    if hasattr(instance, "product") and instance.product:
        return str(instance.product.organization_id)

    # Via category → organization
    if hasattr(instance, "category") and instance.category:
        return str(instance.category.organization_id)

    # Via menu → organization
    if hasattr(instance, "menu") and instance.menu:
        return str(instance.menu.organization_id)

    return "global"
