"""Add pricing promo fields to SiteSettings for dynamic yearly badge/note management."""

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("website", "0010_sitesettings_logo_fields"),
    ]

    operations = [
        migrations.AddField(
            model_name="sitesettings",
            name="pricing_yearly_badge",
            field=models.CharField(
                default="2 AY BEDAVA",
                help_text="Yillik toggle badge metni (orn. '2 AY BEDAVA', '%17 INDIRIM')",
                max_length=50,
                verbose_name="yillik promo rozeti",
            ),
        ),
        migrations.AddField(
            model_name="sitesettings",
            name="pricing_yearly_note",
            field=models.CharField(
                blank=True,
                default="Yillik odemede 10 ay ucreti alinir.",
                help_text="Toggle altinda gosterilen aciklama metni.",
                max_length=200,
                verbose_name="yillik promo notu",
            ),
        ),
    ]
