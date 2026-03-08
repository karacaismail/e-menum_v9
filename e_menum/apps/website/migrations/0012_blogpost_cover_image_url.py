"""Add cover_image_url field to BlogPost for blog card thumbnails."""

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("website", "0011_sitesettings_pricing_promo"),
    ]

    operations = [
        migrations.AddField(
            model_name="blogpost",
            name="cover_image_url",
            field=models.URLField(
                blank=True,
                help_text="Blog kart onizlemesinde gosterilir. PNG/JPG, 16:9 oran.",
                max_length=500,
                verbose_name="kapak gorseli URL",
            ),
        ),
    ]
