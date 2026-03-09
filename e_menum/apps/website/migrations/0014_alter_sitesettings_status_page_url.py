# Generated manually to match CI output

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("website", "0013_populate_blog_cover_images"),
    ]

    operations = [
        migrations.AlterField(
            model_name="sitesettings",
            name="status_page_url",
            field=models.URLField(
                blank=True, default="", verbose_name="durum sayfasi URL"
            ),
        ),
    ]
