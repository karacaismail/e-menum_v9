# Add optional username field to User for login/display (email remains primary)

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0007_add_migration_log'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='username',
            field=models.CharField(
                blank=True,
                db_index=True,
                help_text='Optional display username for login (3–30 chars, lowercase, digits, underscore)',
                max_length=30,
                null=True,
                unique=True,
                verbose_name='Username',
            ),
        ),
    ]
