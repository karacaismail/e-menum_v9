"""Add logo URL fields to SiteSettings for dynamic brand management."""

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("website", "0009_alter_investorpage_contact_email_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="sitesettings",
            name="logo_url",
            field=models.URLField(
                blank=True,
                help_text="Ana logo (navbar, footer). PNG/SVG, tercihen seffaf arkaplan.",
                max_length=500,
                verbose_name="logo URL (yatay)",
            ),
        ),
        migrations.AddField(
            model_name="sitesettings",
            name="logo_icon_url",
            field=models.URLField(
                blank=True,
                help_text="Kare ikon versiyonu (favicon, mobil). PNG/SVG.",
                max_length=500,
                verbose_name="logo ikon URL (kare)",
            ),
        ),
        migrations.AddField(
            model_name="sitesettings",
            name="logo_dark_url",
            field=models.URLField(
                blank=True,
                help_text="Koyu temada kullanilan logo versiyonu.",
                max_length=500,
                verbose_name="logo URL (koyu tema)",
            ),
        ),
        migrations.AddField(
            model_name="sitesettings",
            name="favicon_url",
            field=models.URLField(
                blank=True,
                help_text="Tarayici sekmesi ikonu. 32x32 veya SVG.",
                max_length=500,
                verbose_name="favicon URL",
            ),
        ),
    ]
