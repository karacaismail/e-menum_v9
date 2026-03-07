"""
Django signals for the Orders application.

Handles automatic QR code image generation when QRCode instances are
created or updated without an image.

Signal flow:
    QRCode.post_save → generate QR image if qr_image_url is empty
"""

import logging

from django.db.models.signals import post_save
from django.dispatch import receiver

logger = logging.getLogger(__name__)


@receiver(post_save, sender="orders.QRCode")
def auto_generate_qr_image(sender, instance, created, **kwargs):
    """
    Automatically generate a QR code image after saving a QRCode instance.

    Only generates if qr_image_url is empty (avoids infinite save loops).
    Runs on both create and update (if image was cleared).

    Args:
        sender: QRCode model class
        instance: QRCode instance that was saved
        created: Whether this is a new instance
    """
    if not instance.qr_image_url:
        try:
            from apps.orders.services.qr_generator import QRGeneratorService

            QRGeneratorService.generate_and_save(instance, force=False)
            logger.info(
                "Auto-generated QR image for %s (code=%s, created=%s)",
                instance.name,
                instance.code,
                created,
            )
        except Exception as e:
            logger.error(
                "Failed to auto-generate QR image for %s: %s", instance.code, str(e)
            )
