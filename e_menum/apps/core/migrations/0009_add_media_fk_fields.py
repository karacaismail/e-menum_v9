"""Add Media ForeignKey fields to Organization and User models.

Additive migration — adds nullable FK fields for linking to the
centralized media system.  Existing URL fields are preserved for
backward compatibility.
"""

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0008_add_username_to_user"),
        ("media", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="organization",
            name="logo_media",
            field=models.ForeignKey(
                blank=True,
                help_text="Linked Media record for organization logo",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="organization_logos",
                to="media.media",
                verbose_name="Logo (Media)",
            ),
        ),
        migrations.AddField(
            model_name="user",
            name="avatar_media",
            field=models.ForeignKey(
                blank=True,
                help_text="Linked Media record for user avatar",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="user_avatars",
                to="media.media",
                verbose_name="Avatar (Media)",
            ),
        ),
    ]
