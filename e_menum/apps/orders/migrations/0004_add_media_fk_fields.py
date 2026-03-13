"""Add Media ForeignKey field to QRCode model.

Additive migration — adds nullable FK field for linking QR code images
to the centralized media system.  The existing ``qr_image_url`` field
is preserved for backward compatibility.
"""

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        (
            "orders",
            "0003_order_refund_amount_alter_order_type_discount_refund_and_more",
        ),
        ("media", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="qrcode",
            name="qr_image_media",
            field=models.ForeignKey(
                blank=True,
                help_text="Linked Media record for QR code image",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="qrcode_images",
                to="media.media",
                verbose_name="QR Image (Media)",
            ),
        ),
    ]
