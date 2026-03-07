"""Add icon_svg field to PlanDisplayFeature model.

Allows storing SVG markup for custom icons displayed next to
each feature bullet point on pricing cards.
"""

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("website", "0007_storefront_translations"),
    ]

    operations = [
        migrations.AddField(
            model_name="plandisplayfeature",
            name="icon_svg",
            field=models.TextField(
                blank=True,
                default="",
                help_text="SVG markup for the feature icon (e.g., <svg ...>...</svg>). Leave empty for default checkmark icon.",
                verbose_name="ikon SVG",
            ),
        ),
    ]
