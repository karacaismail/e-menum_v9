# Generated manually for FeaturePermission model

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_remove_branch_branch_org_slug_uniq_and_more'),
        ('subscriptions', '0002_remove_invoice_invoice_org_number_uniq_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='FeaturePermission',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, help_text='Unique identifier (UUID)', primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Created at')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Updated at')),
                ('feature', models.ForeignKey(help_text='Feature that gates this permission', on_delete=django.db.models.deletion.CASCADE, related_name='feature_permissions', to='subscriptions.feature', verbose_name='Feature')),
                ('permission', models.ForeignKey(help_text='Permission gated by the feature', on_delete=django.db.models.deletion.CASCADE, related_name='feature_permissions', to='core.permission', verbose_name='Permission')),
            ],
            options={
                'verbose_name': 'Feature Permission',
                'verbose_name_plural': 'Feature Permissions',
                'db_table': 'feature_permissions',
                'ordering': ['feature', 'permission'],
                'unique_together': {('feature', 'permission')},
            },
        ),
        migrations.AddIndex(
            model_name='featurepermission',
            index=models.Index(fields=['feature'], name='featperm_feature_idx'),
        ),
        migrations.AddIndex(
            model_name='featurepermission',
            index=models.Index(fields=['permission'], name='featperm_permission_idx'),
        ),
    ]
