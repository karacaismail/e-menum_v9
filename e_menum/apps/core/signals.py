"""
Django signals for the Core application.

Handles automatic setup tasks when core models are created/updated:
- Auto-create filer folders when Organization is created
- Audit logging for important model changes

Signal Registration:
    Signals are registered in CoreConfig.ready() via apps/core/apps.py
"""

import logging

from django.db.models.signals import post_save
from django.dispatch import receiver

logger = logging.getLogger(__name__)


@receiver(post_save, sender='core.Organization')
def create_organization_folders(sender, instance, created, **kwargs):
    """
    Auto-create django-filer folder structure for new organizations.

    When a new Organization is created, this signal creates a root folder
    (named after the organization ID) and standard subfolders for organizing
    uploaded media files.

    Folder Structure:
        {org_id}/
        ├── menu_items/   - Product images
        ├── logos/         - Restaurant logos and branding
        └── gallery/       - Gallery / promotional images
    """
    if not created:
        return

    try:
        from filer.models import Folder

        # Get the owner (first user/admin associated with the org, or None)
        owner = None
        if hasattr(instance, 'users'):
            owner = instance.users.first()

        # Create root folder using org ID as name
        root_folder, root_created = Folder.objects.get_or_create(
            name=str(instance.id),
            parent=None,
            defaults={'owner': owner}
        )

        if root_created:
            # Create standard subfolders
            for subfolder_name in ['menu_items', 'logos', 'gallery']:
                Folder.objects.get_or_create(
                    name=subfolder_name,
                    parent=root_folder,
                    defaults={'owner': owner}
                )

            logger.info(
                "Created filer folder structure for organization: %s (%s)",
                instance.name,
                instance.id
            )

    except ImportError:
        # django-filer not installed yet, skip silently
        logger.debug("django-filer not installed, skipping folder creation")
    except Exception as e:
        # Don't fail organization creation if folder setup fails
        logger.warning(
            "Failed to create filer folders for organization %s: %s",
            instance.id,
            str(e)
        )
