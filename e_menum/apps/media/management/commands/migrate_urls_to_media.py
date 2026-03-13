"""
Management command to migrate existing image/logo/avatar URL fields to Media records.

Scans Product, Category, Organization, User, and QRCode models for non-empty
URL fields that have no corresponding Media FK set, creates Media records from
the existing files, and links the FK fields.

Usage:
    python manage.py migrate_urls_to_media
    python manage.py migrate_urls_to_media --dry-run        # Preview changes
    python manage.py migrate_urls_to_media --batch-size 50   # Custom batch
    python manage.py migrate_urls_to_media --model product   # Single model
"""

import logging
import mimetypes
import os
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Migrate existing image URL fields to centralized Media records"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Preview what would be migrated without making changes",
        )
        parser.add_argument(
            "--batch-size",
            type=int,
            default=100,
            help="Number of records to process per batch (default: 100)",
        )
        parser.add_argument(
            "--model",
            type=str,
            choices=["product", "category", "organization", "user", "qrcode"],
            help="Only migrate a specific model",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        batch_size = options["batch_size"]
        model_filter = options.get("model")

        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN — no changes will be made"))

        total_created = 0

        model_handlers = {
            "product": self._migrate_products,
            "category": self._migrate_categories,
            "organization": self._migrate_organizations,
            "user": self._migrate_users,
            "qrcode": self._migrate_qrcodes,
        }

        for name, handler in model_handlers.items():
            if model_filter and name != model_filter:
                continue
            count = handler(dry_run=dry_run, batch_size=batch_size)
            total_created += count

        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f"\nDry run complete: {total_created} records would be created"
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f"\nMigration complete: {total_created} Media records created"
                )
            )

    def _migrate_products(self, *, dry_run, batch_size):
        from apps.menu.models import Product

        self.stdout.write("\n— Product images —")
        qs = Product.objects.filter(
            deleted_at__isnull=True,
            image__isnull=False,
            image_media__isnull=True,
        ).exclude(image="")

        return self._process_queryset(
            qs,
            url_field="image",
            fk_field="image_media",
            media_type="IMAGE",
            batch_size=batch_size,
            dry_run=dry_run,
            label="Product",
        )

    def _migrate_categories(self, *, dry_run, batch_size):
        from apps.menu.models import Category

        self.stdout.write("\n— Category images —")
        qs = Category.objects.filter(
            deleted_at__isnull=True,
            image__isnull=False,
            image_media__isnull=True,
        ).exclude(image="")

        return self._process_queryset(
            qs,
            url_field="image",
            fk_field="image_media",
            media_type="IMAGE",
            batch_size=batch_size,
            dry_run=dry_run,
            label="Category",
        )

    def _migrate_organizations(self, *, dry_run, batch_size):
        from apps.core.models import Organization

        self.stdout.write("\n— Organization logos —")
        qs = Organization.objects.filter(
            deleted_at__isnull=True,
            logo__isnull=False,
            logo_media__isnull=True,
        ).exclude(logo="")

        return self._process_queryset(
            qs,
            url_field="logo",
            fk_field="logo_media",
            media_type="IMAGE",
            batch_size=batch_size,
            dry_run=dry_run,
            label="Organization",
        )

    def _migrate_users(self, *, dry_run, batch_size):
        from apps.core.models import User

        self.stdout.write("\n— User avatars —")
        qs = User.objects.filter(
            deleted_at__isnull=True,
            avatar__isnull=False,
            avatar_media__isnull=True,
        ).exclude(avatar="")

        return self._process_queryset(
            qs,
            url_field="avatar",
            fk_field="avatar_media",
            media_type="IMAGE",
            batch_size=batch_size,
            dry_run=dry_run,
            label="User",
        )

    def _migrate_qrcodes(self, *, dry_run, batch_size):
        from apps.orders.models import QRCode

        self.stdout.write("\n— QR code images —")
        qs = QRCode.objects.filter(
            deleted_at__isnull=True,
            qr_image_url__isnull=False,
            qr_image_media__isnull=True,
        ).exclude(qr_image_url="")

        return self._process_queryset(
            qs,
            url_field="qr_image_url",
            fk_field="qr_image_media",
            media_type="IMAGE",
            batch_size=batch_size,
            dry_run=dry_run,
            label="QRCode",
        )

    def _process_queryset(
        self, qs, *, url_field, fk_field, media_type, batch_size, dry_run, label
    ):
        from apps.media.models import Media

        total = qs.count()
        self.stdout.write(f"  Found {total} {label} records to migrate")

        if total == 0:
            return 0

        created = 0
        offset = 0

        while offset < total:
            batch = list(qs[offset : offset + batch_size])
            if not batch:
                break

            for obj in batch:
                url = getattr(obj, url_field, "")
                if not url:
                    continue

                org = getattr(obj, "organization", None)
                if not org:
                    # User model has org directly
                    org = getattr(obj, "organization", None)
                    if not org:
                        self.stdout.write(
                            f"  ⚠ Skipping {label} {obj.pk}: no organization"
                        )
                        continue

                if dry_run:
                    self.stdout.write(
                        f"  [DRY] Would create Media for {label} {obj.pk}: {url}"
                    )
                    created += 1
                    continue

                # Try to get file info from disk (best-effort)
                file_size, width, height = self._get_file_info(url)
                mime_type = self._guess_mime_type(url)
                filename = self._extract_filename(url)

                try:
                    with transaction.atomic():
                        media = Media.objects.create(
                            organization=org,
                            name=f"{label} - {getattr(obj, 'name', str(obj.pk)[:8])}",
                            original_filename=filename,
                            file_path=self._url_to_file_path(url),
                            url=url if url.startswith(("http://", "https://")) else "",
                            storage="LOCAL",
                            media_type=media_type,
                            status="READY",
                            mime_type=mime_type,
                            file_size=file_size,
                            width=width,
                            height=height,
                            is_public=True,  # Existing images were publicly accessible
                        )
                        setattr(obj, fk_field, media)
                        obj.save(update_fields=[fk_field, "updated_at"])
                        created += 1
                except Exception:
                    logger.exception("Failed to create Media for %s %s", label, obj.pk)
                    self.stdout.write(self.style.ERROR(f"  ✗ Failed: {label} {obj.pk}"))

            offset += batch_size
            self.stdout.write(f"  Processed {min(offset, total)}/{total}")

        self.stdout.write(f"  → Created {created} Media records for {label}")
        return created

    def _get_file_info(self, url):
        """Try to read file size and dimensions from disk."""
        file_size = 0
        width = None
        height = None

        file_path = self._resolve_local_path(url)
        if file_path and file_path.exists():
            file_size = file_path.stat().st_size
            # Try to get dimensions for images
            try:
                from PIL import Image

                with Image.open(file_path) as img:
                    width, height = img.size
            except Exception:
                pass

        return file_size, width, height

    def _resolve_local_path(self, url):
        """Convert a URL to a local file path."""
        media_root = getattr(settings, "MEDIA_ROOT", "")
        if not media_root:
            return None

        # Strip leading /media/ prefix
        relative = url
        if relative.startswith("/media/"):
            relative = relative[7:]
        elif relative.startswith("media/"):
            relative = relative[6:]
        elif relative.startswith(("http://", "https://")):
            return None

        path = Path(media_root) / relative
        return path if path.exists() else None

    def _guess_mime_type(self, url):
        """Guess MIME type from URL."""
        mime, _ = mimetypes.guess_type(url)
        return mime or "application/octet-stream"

    def _extract_filename(self, url):
        """Extract filename from URL or path."""
        return os.path.basename(url.rstrip("/")) or "unknown"

    def _url_to_file_path(self, url):
        """Convert URL to a relative file_path for Media.file_path."""
        if url.startswith("/media/"):
            return url[7:]
        if url.startswith("media/"):
            return url[6:]
        if url.startswith(("http://", "https://")):
            # External URL — use the URL itself
            return url
        return url
