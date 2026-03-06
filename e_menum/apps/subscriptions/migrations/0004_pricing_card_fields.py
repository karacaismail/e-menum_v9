"""Add pricing card display fields to Plan model and category choices to Feature model.

New Plan fields: card_css_class, badge_label, motto, ribbon_color,
cta_text, cta_style, cta_url, price_label, custom_price_text, has_glow_effect.

Updated Feature.category to use FeatureCategoryType choices.
Updated PlanTier to include BUSINESS tier.
"""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('subscriptions', '0003_featurepermission'),
    ]

    operations = [
        # Plan model: new pricing card display fields
        migrations.AddField(
            model_name='plan',
            name='card_css_class',
            field=models.CharField(
                blank=True,
                choices=[
                    ('free', 'Free (Slate)'),
                    ('start', 'Starter (Sky Blue)'),
                    ('grow', 'Growth (Emerald)'),
                    ('pro', 'Professional (Accent/Teal)'),
                    ('biz', 'Business (Purple)'),
                    ('ent', 'Enterprise (Gold)'),
                ],
                default='',
                help_text='Visual style for the pricing card (free, start, grow, pro, biz, ent)',
                max_length=20,
                verbose_name='Card CSS class',
            ),
        ),
        migrations.AddField(
            model_name='plan',
            name='badge_label',
            field=models.CharField(
                blank=True,
                default='',
                help_text='Badge text shown on card (e.g., "Ücretsiz", "Starter"). Falls back to plan name.',
                max_length=50,
                verbose_name='Badge label',
            ),
        ),
        migrations.AddField(
            model_name='plan',
            name='motto',
            field=models.CharField(
                blank=True,
                default='',
                help_text='Motivational italic quote on pricing card (e.g., "Her büyük iş küçük bir adımla başlar.")',
                max_length=200,
                verbose_name='Motto',
            ),
        ),
        migrations.AddField(
            model_name='plan',
            name='ribbon_color',
            field=models.CharField(
                blank=True,
                choices=[
                    ('', 'Yok'),
                    ('teal', 'Teal (Accent)'),
                    ('gold', 'Gold'),
                    ('purple', 'Purple'),
                ],
                default='',
                help_text='Ribbon color if highlight_text is set (teal, gold, purple)',
                max_length=10,
                verbose_name='Ribbon color',
            ),
        ),
        migrations.AddField(
            model_name='plan',
            name='cta_text',
            field=models.CharField(
                blank=True,
                default='',
                help_text='Call-to-action button text (e.g., "Ücretsiz Başla", "14 Gün Dene", "İletişime Geçin")',
                max_length=50,
                verbose_name='CTA button text',
            ),
        ),
        migrations.AddField(
            model_name='plan',
            name='cta_style',
            field=models.CharField(
                blank=True,
                choices=[
                    ('cta-out', 'Outline'),
                    ('cta-prim', 'Primary (Filled)'),
                    ('cta-ent', 'Enterprise (Gold)'),
                ],
                default='cta-out',
                help_text='Button appearance: outline, primary (filled), or enterprise (gold)',
                max_length=20,
                verbose_name='CTA button style',
            ),
        ),
        migrations.AddField(
            model_name='plan',
            name='cta_url',
            field=models.CharField(
                blank=True,
                default='',
                help_text='URL for the CTA button (Django URL name like "website:demo" or absolute URL)',
                max_length=200,
                verbose_name='CTA URL',
            ),
        ),
        migrations.AddField(
            model_name='plan',
            name='price_label',
            field=models.CharField(
                blank=True,
                default='',
                help_text='Text below price (e.g., "Sonsuza kadar ücretsiz", "Aylık faturalanır")',
                max_length=100,
                verbose_name='Price label',
            ),
        ),
        migrations.AddField(
            model_name='plan',
            name='custom_price_text',
            field=models.CharField(
                blank=True,
                default='',
                help_text='Custom price display for enterprise plans (e.g., "Özel Fiyat")',
                max_length=50,
                verbose_name='Custom price text',
            ),
        ),
        migrations.AddField(
            model_name='plan',
            name='has_glow_effect',
            field=models.BooleanField(
                default=False,
                help_text='Show a radial glow effect on the card (used for highlighted/featured plans)',
                verbose_name='Glow effect',
            ),
        ),
        # Update Plan.tier choices to include BUSINESS
        migrations.AlterField(
            model_name='plan',
            name='tier',
            field=models.CharField(
                choices=[
                    ('FREE', 'Free'),
                    ('STARTER', 'Starter'),
                    ('GROWTH', 'Growth'),
                    ('PROFESSIONAL', 'Professional'),
                    ('BUSINESS', 'Business'),
                    ('ENTERPRISE', 'Enterprise'),
                ],
                db_index=True,
                help_text='Plan tier level (FREE, STARTER, GROWTH, etc.)',
                max_length=20,
                verbose_name='Tier',
            ),
        ),
        # Update Plan.highlight_text help_text
        migrations.AlterField(
            model_name='plan',
            name='highlight_text',
            field=models.CharField(
                blank=True,
                help_text='Optional badge/ribbon text (e.g., "En Popüler", "Özel Teklif")',
                max_length=50,
                null=True,
                verbose_name='Highlight text',
            ),
        ),
        # Update Feature.category to use choices
        migrations.AlterField(
            model_name='feature',
            name='category',
            field=models.CharField(
                choices=[
                    ('menus', 'Menü & Ürün Yönetimi'),
                    ('orders', 'Sipariş & Ödeme'),
                    ('analytics', 'Analitik & Raporlama'),
                    ('support', 'Destek & Entegrasyon'),
                    ('ai', 'Yapay Zeka'),
                    ('branding', 'Marka & Tasarım'),
                    ('integrations', 'Entegrasyonlar'),
                    ('general', 'Genel'),
                ],
                db_index=True,
                help_text='Category for grouping features (e.g., menus, orders, ai, analytics)',
                max_length=50,
                verbose_name='Category',
            ),
        ),
    ]
