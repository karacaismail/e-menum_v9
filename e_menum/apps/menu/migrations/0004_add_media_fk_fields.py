"""Add Media ForeignKey fields to Category and Product models.

Additive migration — adds nullable FK fields for linking to the
centralized media system.  Existing URL fields are preserved for
backward compatibility.
"""

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("menu", "0003_add_icon_discount_rating"),
        ("media", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="category",
            name="image_media",
            field=models.ForeignKey(
                blank=True,
                help_text="Linked Media record for category image",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="category_images",
                to="media.media",
                verbose_name="Image (Media)",
            ),
        ),
        migrations.AddField(
            model_name="product",
            name="image_media",
            field=models.ForeignKey(
                blank=True,
                help_text="Linked Media record for product image",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="product_images",
                to="media.media",
                verbose_name="Image (Media)",
            ),
        ),
    ]
