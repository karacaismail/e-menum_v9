"""
Django management command for seeding Plans, Features, PlanFeatures,
and PlanDisplayFeatures with full pricing card configuration.

This command creates the complete pricing infrastructure for E-Menum:
- 6 subscription plans (Free → Enterprise) with card styling fields
- 15+ feature definitions with category grouping
- Plan-feature relationships for the comparison table
- PlanDisplayFeature marketing bullet points with SVG icons

Plan Tiers:
| Plan | Monthly | Yearly (10mo) | Trial |
|------|---------|---------------|-------|
| Free | 0 TL | 0 TL | - |
| Starter | 2.000 TL | 20.000 TL | 14 gün |
| Growth | 4.500 TL | 45.000 TL | 14 gün |
| Professional | 8.500 TL | 85.000 TL | 14 gün |
| Business | 15.000 TL | 150.000 TL | 14 gün |
| Enterprise | Özel | Özel | - |

Usage:
    python manage.py seed_plans
    python manage.py seed_plans --force
    python manage.py seed_plans --dry-run
"""

from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.subscriptions.choices import (
    FeatureCategoryType,
    FeatureType,
    PlanTier,
)
from apps.subscriptions.models import Feature, Plan, PlanFeature


class DryRunException(Exception):
    """Exception raised to rollback dry run transactions."""
    pass


# ─── SVG ICON LIBRARY ───────────────────────────────────────────────────────
# Compact SVG icons used in PlanDisplayFeature bullet points.
# All icons: fill=none stroke=currentColor stroke-width=2 viewBox 0 0 24 24

SVG = {
    'star': '<svg fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">'
            '<path d="M12 2L15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 '
            '5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2z"/></svg>',

    'clock': '<svg fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">'
             '<circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/></svg>',

    'user': '<svg fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">'
            '<path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>'
            '<circle cx="9" cy="7" r="4"/></svg>',

    'bolt': '<svg fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">'
            '<path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"/></svg>',

    'lock': '<svg fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">'
            '<rect x="3" y="11" width="18" height="11" rx="2"/>'
            '<path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>',

    'shield': '<svg fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">'
              '<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>',

    'pulse': '<svg fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">'
             '<polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>',

    'sun': '<svg fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">'
           '<circle cx="12" cy="12" r="3"/>'
           '<path d="M19.07 4.93l-1.41 1.41M12 2v2m6.36 14.14l-1.41-1.41'
           'M22 12h-2M4.93 19.07l1.41-1.41M2 12h2M7.05 7.05L5.64 5.64M12 22v-2"/></svg>',

    'users': '<svg fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">'
             '<path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>'
             '<circle cx="9" cy="7" r="4"/>'
             '<path d="M23 21v-2a4 4 0 0 0-3-3.87"/>'
             '<path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>',

    'trend': '<svg fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">'
             '<polyline points="23 6 13.5 15.5 8.5 10.5 1 18"/>'
             '<polyline points="17 6 23 6 23 12"/></svg>',

    'monitor': '<svg fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">'
               '<rect x="2" y="3" width="20" height="14" rx="2"/>'
               '<line x1="8" y1="21" x2="16" y2="21"/>'
               '<line x1="12" y1="17" x2="12" y2="21"/></svg>',

    'grid': '<svg fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">'
            '<rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/>'
            '<rect x="14" y="14" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/></svg>',

    'database': '<svg fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">'
                '<ellipse cx="12" cy="5" rx="9" ry="3"/>'
                '<path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"/>'
                '<path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"/></svg>',

    'phone': '<svg fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">'
             '<path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07'
             'A19.5 19.5 0 0 1 4.95 12 19.79 19.79 0 0 1 1.88 3.2 2 2 0 0 1 3.88 1h3'
             'a2 2 0 0 1 2 1.72c.127.96.361 1.903.7 2.81a2 2 0 0 1-.45 2.11L8.09 8.91'
             'a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45c.907.339 1.85.573 2.81.7'
             'A2 2 0 0 1 22 16.92z"/></svg>',

    'globe': '<svg fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">'
             '<circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/>'
             '<path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10'
             ' 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/></svg>',
}


class Command(BaseCommand):
    """Management command to seed Plans, Features, PlanFeatures, and PlanDisplayFeatures."""

    help = 'Seed subscription plans, features, and pricing card data for E-Menum'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force', action='store_true',
            help='Force update existing records',
        )
        parser.add_argument(
            '--dry-run', action='store_true',
            help='Show what would be created without making changes',
        )

    def handle(self, *args, **options):
        force = options['force']
        dry_run = options['dry_run']

        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN - No changes will be made'))

        try:
            with transaction.atomic():
                features = self._create_features(force, dry_run)
                self.stdout.write(f'Created/updated {len(features)} features')

                plans = self._create_plans(force, dry_run)
                self.stdout.write(f'Created/updated {len(plans)} plans')

                pf_count = self._create_plan_features(plans, features, force, dry_run)
                self.stdout.write(f'Created/updated {pf_count} plan-feature relationships')

                df_count = self._create_display_features(plans, force, dry_run)
                self.stdout.write(f'Created/updated {df_count} display features')

                if dry_run:
                    raise DryRunException()

        except DryRunException:
            self.stdout.write(self.style.WARNING('Dry run completed - no changes'))
        except Exception as e:
            raise CommandError(f'Failed to seed plans: {str(e)}')

        if not dry_run:
            self.stdout.write(self.style.SUCCESS(
                'Successfully seeded plans, features, and display data!'
            ))

    # ─── FEATURES ────────────────────────────────────────────────────────────

    def _create_features(self, force, dry_run):
        """Create or update Feature definitions for comparison table."""
        features_data = [
            # ── Menü & Ürün Yönetimi ──
            {
                'code': 'max_menus',
                'name': 'Menü sayısı',
                'description': 'Oluşturulabilecek maksimum menü sayısı',
                'feature_type': FeatureType.LIMIT,
                'default_value': {'limit': 1},
                'category': FeatureCategoryType.MENUS,
                'sort_order': 10,
            },
            {
                'code': 'max_products',
                'name': 'Ürün sayısı',
                'description': 'Tüm menülerdeki toplam maksimum ürün sayısı',
                'feature_type': FeatureType.LIMIT,
                'default_value': {'limit': 50},
                'category': FeatureCategoryType.MENUS,
                'sort_order': 20,
            },
            {
                'code': 'qr_code_customization',
                'name': 'Özel QR tasarımı',
                'description': 'QR kod renk ve marka özelleştirmesi',
                'feature_type': FeatureType.BOOLEAN,
                'default_value': {'enabled': False},
                'category': FeatureCategoryType.MENUS,
                'sort_order': 30,
            },
            {
                'code': 'allergen_management',
                'name': 'Alerjen yönetimi',
                'description': 'EU standardı alerjen bilgisi yönetimi',
                'feature_type': FeatureType.BOOLEAN,
                'default_value': {'enabled': False},
                'category': FeatureCategoryType.MENUS,
                'sort_order': 40,
            },
            # ── Sipariş & Ödeme ──
            {
                'code': 'order_management',
                'name': 'Dijital sipariş modülü',
                'description': 'Menüden dijital sipariş alma ve yönetimi',
                'feature_type': FeatureType.BOOLEAN,
                'default_value': {'enabled': False},
                'category': FeatureCategoryType.ORDERS,
                'sort_order': 50,
            },
            {
                'code': 'pos_integration',
                'name': 'POS entegrasyonu',
                'description': 'Yazar kasa ve POS sistemi entegrasyonu',
                'feature_type': FeatureType.BOOLEAN,
                'default_value': {'enabled': False},
                'category': FeatureCategoryType.ORDERS,
                'sort_order': 60,
            },
            {
                'code': 'loyalty_program',
                'name': 'Sadakat programı',
                'description': 'Müşteri sadakat puanları ve ödüller',
                'feature_type': FeatureType.BOOLEAN,
                'default_value': {'enabled': False},
                'category': FeatureCategoryType.ORDERS,
                'sort_order': 70,
            },
            # ── Analitik & Raporlama ──
            {
                'code': 'analytics_basic',
                'name': 'Temel dashboard',
                'description': 'QR tarama sayıları ve temel metrikler',
                'feature_type': FeatureType.BOOLEAN,
                'default_value': {'enabled': True},
                'category': FeatureCategoryType.ANALYTICS,
                'sort_order': 80,
            },
            {
                'code': 'analytics_advanced',
                'name': 'Gelişmiş raporlama',
                'description': 'Müşteri içgörüleri, trendler ve detaylı analizler',
                'feature_type': FeatureType.BOOLEAN,
                'default_value': {'enabled': False},
                'category': FeatureCategoryType.ANALYTICS,
                'sort_order': 90,
            },
            {
                'code': 'ai_credits_monthly',
                'name': 'AI içerik üretimi',
                'description': 'Yapay zeka ile menü açıklaması ve içerik üretimi',
                'feature_type': FeatureType.USAGE,
                'default_value': {'credits': 0, 'reset_period': 'monthly'},
                'category': FeatureCategoryType.ANALYTICS,
                'sort_order': 100,
            },
            # ── Destek & Entegrasyon ──
            {
                'code': 'support_channel',
                'name': 'Destek kanalı',
                'description': 'Müşteri destek kanalları ve SLA seviyesi',
                'feature_type': FeatureType.USAGE,
                'default_value': {'text': 'E-posta'},
                'category': FeatureCategoryType.SUPPORT,
                'sort_order': 110,
            },
            {
                'code': 'api_access',
                'name': 'API erişimi',
                'description': 'REST API ile entegrasyon erişimi',
                'feature_type': FeatureType.BOOLEAN,
                'default_value': {'enabled': False},
                'category': FeatureCategoryType.SUPPORT,
                'sort_order': 120,
            },
            {
                'code': 'multi_language',
                'name': 'Çoklu dil',
                'description': 'Menüleri birden fazla dilde sunma',
                'feature_type': FeatureType.LIMIT,
                'default_value': {'limit': 0},
                'category': FeatureCategoryType.SUPPORT,
                'sort_order': 130,
            },
            {
                'code': 'white_label',
                'name': 'White-label',
                'description': 'E-Menum markası kaldırılarak kendi marka ile sunma',
                'feature_type': FeatureType.BOOLEAN,
                'default_value': {'enabled': False},
                'category': FeatureCategoryType.SUPPORT,
                'sort_order': 140,
            },
            {
                'code': 'on_premise',
                'name': 'On-premise kurulum',
                'description': 'Kendi sunucunuzda veya private cloud kurulum',
                'feature_type': FeatureType.BOOLEAN,
                'default_value': {'enabled': False},
                'category': FeatureCategoryType.SUPPORT,
                'sort_order': 150,
            },
        ]

        features = {}
        for data in features_data:
            code = data['code']
            if force:
                feature, created = Feature.objects.update_or_create(
                    code=code, defaults=data,
                )
            else:
                feature, created = Feature.objects.get_or_create(
                    code=code, defaults=data,
                )
                if not created and force:
                    for k, v in data.items():
                        setattr(feature, k, v)
                    feature.save()

            action = '+' if created else ('~' if force else '-')
            self.stdout.write(f'  {action} Feature: {code}')
            features[code] = feature

        return features

    # ─── PLANS ───────────────────────────────────────────────────────────────

    def _create_plans(self, force, dry_run):
        """Create or update the 6 subscription plans with all card fields."""
        plans_data = [
            # ── FREE ──
            {
                'slug': 'free',
                'name': 'Free',
                'tier': PlanTier.FREE,
                'description': 'Dijital menü deneyimine sıfır riskle başlayın.',
                'short_description': 'İlk adımı atmak için hiçbir şey gerekmez.',
                'price_monthly': Decimal('0.00'),
                'price_yearly': Decimal('0.00'),
                'currency': 'TRY',
                'trial_days': 0,
                'is_active': True,
                'is_default': True,
                'is_public': True,
                'is_custom': False,
                'sort_order': 10,
                # Card display fields
                'card_css_class': 'free',
                'badge_label': 'Ücretsiz',
                'motto': 'Her büyük iş küçük bir adımla başlar.',
                'ribbon_color': '',
                'highlight_text': '',
                'cta_text': 'Ücretsiz Başla',
                'cta_style': 'cta-out',
                'cta_url': 'website:demo',
                'price_label': 'Sonsuza kadar ücretsiz',
                'custom_price_text': '',
                'has_glow_effect': False,
                'limits': {
                    'max_menus': 1, 'max_products': 50, 'max_categories': 10,
                    'max_qr_codes': 3, 'max_users': 2, 'max_branches': 1,
                    'storage_mb': 100, 'ai_credits_monthly': 0,
                },
                'feature_flags': {
                    'ai_content_generation': False, 'analytics_basic': True,
                    'analytics_advanced': False, 'custom_domain': False,
                    'white_label': False, 'api_access': False,
                    'priority_support': False, 'multi_language': False,
                    'order_management': False, 'qr_code_customization': False,
                    'customer_feedback': True, 'loyalty_program': False,
                },
            },
            # ── STARTER ──
            {
                'slug': 'starter',
                'name': 'Starter',
                'tier': PlanTier.STARTER,
                'description': 'İlk müşterilerini kazanmaya hazır işletmeler için temel özellikler.',
                'short_description': 'İlk müşterilerini kazanmaya hazır işletmeler için.',
                'price_monthly': Decimal('2000.00'),
                'price_yearly': Decimal('20000.00'),
                'currency': 'TRY',
                'trial_days': 14,
                'is_active': True,
                'is_default': False,
                'is_public': True,
                'is_custom': False,
                'sort_order': 20,
                'card_css_class': 'start',
                'badge_label': 'Starter',
                'motto': 'Mükemmellik bir alışkanlıktır, ürün değil.',
                'ribbon_color': '',
                'highlight_text': '',
                'cta_text': '14 Gün Dene',
                'cta_style': 'cta-out',
                'cta_url': 'website:demo',
                'price_label': 'Aylık faturalanır',
                'custom_price_text': '',
                'has_glow_effect': False,
                'limits': {
                    'max_menus': 3, 'max_products': 200, 'max_categories': 25,
                    'max_qr_codes': 10, 'max_users': 5, 'max_branches': 1,
                    'storage_mb': 500, 'ai_credits_monthly': 50,
                },
                'feature_flags': {
                    'ai_content_generation': True, 'analytics_basic': True,
                    'analytics_advanced': False, 'custom_domain': False,
                    'white_label': False, 'api_access': False,
                    'priority_support': False, 'multi_language': False,
                    'order_management': False, 'qr_code_customization': True,
                    'customer_feedback': True, 'loyalty_program': False,
                },
            },
            # ── GROWTH ──
            {
                'slug': 'growth',
                'name': 'Growth',
                'tier': PlanTier.GROWTH,
                'description': 'İvmelenme aşamasındaki işletmeler için gelişmiş analitik ve AI.',
                'short_description': 'İvmelenme aşamasındaki işletmeler için tasarlandı.',
                'price_monthly': Decimal('4500.00'),
                'price_yearly': Decimal('45000.00'),
                'currency': 'TRY',
                'trial_days': 14,
                'is_active': True,
                'is_default': False,
                'is_public': True,
                'is_custom': False,
                'sort_order': 30,
                'card_css_class': 'grow',
                'badge_label': 'Growth',
                'motto': 'Büyümek için doğru araçlara, doğru zamanda ihtiyacın var.',
                'ribbon_color': '',
                'highlight_text': '',
                'cta_text': '14 Gün Dene',
                'cta_style': 'cta-out',
                'cta_url': 'website:demo',
                'price_label': 'Aylık faturalanır',
                'custom_price_text': '',
                'has_glow_effect': False,
                'limits': {
                    'max_menus': 10, 'max_products': 1000, 'max_categories': 50,
                    'max_qr_codes': 50, 'max_users': 15, 'max_branches': 3,
                    'storage_mb': 2048, 'ai_credits_monthly': 250,
                },
                'feature_flags': {
                    'ai_content_generation': True, 'analytics_basic': True,
                    'analytics_advanced': True, 'custom_domain': False,
                    'white_label': False, 'api_access': False,
                    'priority_support': False, 'multi_language': True,
                    'order_management': True, 'qr_code_customization': True,
                    'customer_feedback': True, 'loyalty_program': True,
                },
            },
            # ── PROFESSIONAL ──
            {
                'slug': 'professional',
                'name': 'Professional',
                'tier': PlanTier.PROFESSIONAL,
                'description': 'Ciddi işletmelerin tercihi. Tam güç, tam kontrol, sınırsız ölçek.',
                'short_description': 'Ciddi işletmelerin tercihi. Tam güç, tam kontrol.',
                'price_monthly': Decimal('8500.00'),
                'price_yearly': Decimal('85000.00'),
                'currency': 'TRY',
                'trial_days': 14,
                'is_active': True,
                'is_default': False,
                'is_public': True,
                'is_custom': False,
                'sort_order': 40,
                'card_css_class': 'pro',
                'badge_label': 'Professional',
                'motto': 'Profesyoneller sonuçla ölçülür.',
                'ribbon_color': 'teal',
                'highlight_text': 'En Popüler',
                'cta_text': '14 Gün Dene',
                'cta_style': 'cta-prim',
                'cta_url': 'website:demo',
                'price_label': 'Aylık faturalanır',
                'custom_price_text': '',
                'has_glow_effect': True,
                'limits': {
                    'max_menus': -1, 'max_products': -1, 'max_categories': -1,
                    'max_qr_codes': -1, 'max_users': 30, 'max_branches': 5,
                    'storage_mb': 5120, 'ai_credits_monthly': -1,
                },
                'feature_flags': {
                    'ai_content_generation': True, 'analytics_basic': True,
                    'analytics_advanced': True, 'custom_domain': True,
                    'white_label': False, 'api_access': True,
                    'priority_support': True, 'multi_language': True,
                    'order_management': True, 'qr_code_customization': True,
                    'customer_feedback': True, 'loyalty_program': True,
                },
            },
            # ── BUSINESS ──
            {
                'slug': 'business',
                'name': 'Business',
                'tier': PlanTier.BUSINESS,
                'description': 'Birden fazla şube, tek güçlü platform. White-label ve dedike yönetici.',
                'short_description': 'Birden fazla şube, tek güçlü platform.',
                'price_monthly': Decimal('15000.00'),
                'price_yearly': Decimal('150000.00'),
                'currency': 'TRY',
                'trial_days': 14,
                'is_active': True,
                'is_default': False,
                'is_public': True,
                'is_custom': False,
                'sort_order': 50,
                'card_css_class': 'biz',
                'badge_label': 'Business',
                'motto': 'Ölçek bir ayrıcalık değil, bir sistem meselesidir.',
                'ribbon_color': '',
                'highlight_text': '',
                'cta_text': '14 Gün Dene',
                'cta_style': 'cta-out',
                'cta_url': 'website:demo',
                'price_label': 'Aylık faturalanır',
                'custom_price_text': '',
                'has_glow_effect': False,
                'limits': {
                    'max_menus': -1, 'max_products': -1, 'max_categories': -1,
                    'max_qr_codes': -1, 'max_users': -1, 'max_branches': -1,
                    'storage_mb': 10240, 'ai_credits_monthly': -1,
                },
                'feature_flags': {
                    'ai_content_generation': True, 'analytics_basic': True,
                    'analytics_advanced': True, 'custom_domain': True,
                    'white_label': True, 'api_access': True,
                    'priority_support': True, 'multi_language': True,
                    'order_management': True, 'qr_code_customization': True,
                    'customer_feedback': True, 'loyalty_program': True,
                },
            },
            # ── ENTERPRISE ──
            {
                'slug': 'enterprise',
                'name': 'Enterprise',
                'tier': PlanTier.ENTERPRISE,
                'description': 'Kurumsal düzeyde özel çözüm. SLA, on-premise, tam entegrasyon.',
                'short_description': 'Kurumsal düzeyde özel çözüm. Fiyat yerine değer konuşalım.',
                'price_monthly': Decimal('0.00'),
                'price_yearly': Decimal('0.00'),
                'currency': 'TRY',
                'trial_days': 0,
                'is_active': True,
                'is_default': False,
                'is_public': True,
                'is_custom': True,
                'sort_order': 60,
                'card_css_class': 'ent',
                'badge_label': 'Enterprise',
                'motto': 'Büyüklük standart pakete sığmaz.',
                'ribbon_color': 'gold',
                'highlight_text': 'Özel Teklif',
                'cta_text': 'İletişime Geçin',
                'cta_style': 'cta-ent',
                'cta_url': 'website:contact',
                'price_label': 'Size özel teklif',
                'custom_price_text': 'Özel Fiyat',
                'has_glow_effect': False,
                'limits': {
                    'max_menus': -1, 'max_products': -1, 'max_categories': -1,
                    'max_qr_codes': -1, 'max_users': -1, 'max_branches': -1,
                    'storage_mb': 20480, 'ai_credits_monthly': -1,
                },
                'feature_flags': {
                    'ai_content_generation': True, 'analytics_basic': True,
                    'analytics_advanced': True, 'custom_domain': True,
                    'white_label': True, 'api_access': True,
                    'priority_support': True, 'multi_language': True,
                    'order_management': True, 'qr_code_customization': True,
                    'customer_feedback': True, 'loyalty_program': True,
                },
            },
        ]

        plans = {}
        for data in plans_data:
            slug = data['slug']
            if force:
                plan, created = Plan.objects.update_or_create(
                    slug=slug, defaults=data,
                )
            else:
                plan, created = Plan.objects.get_or_create(
                    slug=slug, defaults=data,
                )

            if not created and force:
                for k, v in data.items():
                    setattr(plan, k, v)
                plan.save()

            action = '+' if created else ('~' if force else '-')
            self.stdout.write(f'  {action} Plan: {data["name"]} ({slug})')
            plans[slug] = plan

        return plans

    # ─── PLAN-FEATURES ───────────────────────────────────────────────────────

    def _create_plan_features(self, plans, features, force, dry_run):
        """Create PlanFeature entries for comparison table."""

        # Feature values per plan — matches the reference pricing comparison table
        #   Free | Starter | Growth | Professional | Business | Enterprise
        config = {
            # Menü & Ürün Yönetimi
            'max_menus': [
                {'limit': 1}, {'limit': 3}, {'limit': 10},
                {'limit': -1}, {'limit': -1}, {'limit': -1},
            ],
            'max_products': [
                {'limit': 50}, {'limit': 200}, {'limit': 1000},
                {'limit': -1}, {'limit': -1}, {'limit': -1},
            ],
            'qr_code_customization': [
                {'enabled': False}, {'enabled': True}, {'enabled': True},
                {'enabled': True}, {'enabled': True}, {'enabled': True},
            ],
            'allergen_management': [
                {'enabled': False}, {'enabled': True}, {'enabled': True},
                {'enabled': True}, {'enabled': True}, {'enabled': True},
            ],
            # Sipariş & Ödeme
            'order_management': [
                {'enabled': False}, {'enabled': False}, {'enabled': True},
                {'enabled': True}, {'enabled': True}, {'enabled': True},
            ],
            'pos_integration': [
                {'enabled': False}, {'enabled': False}, {'enabled': False},
                {'enabled': True}, {'enabled': True}, {'enabled': True},
            ],
            'loyalty_program': [
                {'enabled': False}, {'enabled': False}, {'enabled': True},
                {'enabled': True}, {'enabled': True}, {'enabled': True},
            ],
            # Analitik & Raporlama
            'analytics_basic': [
                {'enabled': True}, {'enabled': True}, {'enabled': True},
                {'enabled': True}, {'enabled': True}, {'enabled': True},
            ],
            'analytics_advanced': [
                {'enabled': False}, {'enabled': False}, {'enabled': True},
                {'enabled': True}, {'enabled': True}, {'enabled': True},
            ],
            'ai_credits_monthly': [
                {'credits': 0, 'reset_period': 'monthly'},
                {'credits': 50, 'reset_period': 'monthly'},
                {'credits': 250, 'reset_period': 'monthly'},
                {'credits': -1, 'reset_period': 'monthly'},
                {'credits': -1, 'reset_period': 'monthly'},
                {'credits': -1, 'reset_period': 'monthly', 'text': 'Özel Model'},
            ],
            # Destek & Entegrasyon
            'support_channel': [
                {'text': 'E-posta'},
                {'text': 'E-posta + Chat'},
                {'text': 'Öncelikli Chat'},
                {'text': '7/24 Öncelikli'},
                {'text': 'Dedike Ekip'},
                {'text': 'SLA + Dedike'},
            ],
            'api_access': [
                {'enabled': False}, {'enabled': False}, {'enabled': False},
                {'enabled': True}, {'enabled': True}, {'enabled': True},
            ],
            'multi_language': [
                {'limit': 0}, {'limit': 0}, {'limit': 3},
                {'limit': 6}, {'limit': 10}, {'limit': -1},
            ],
            'white_label': [
                {'enabled': False}, {'enabled': False}, {'enabled': False},
                {'enabled': False}, {'enabled': True}, {'enabled': True},
            ],
            'on_premise': [
                {'enabled': False}, {'enabled': False}, {'enabled': False},
                {'enabled': False}, {'enabled': False}, {'enabled': True},
            ],
        }

        plan_slugs = ['free', 'starter', 'growth', 'professional', 'business', 'enterprise']
        count = 0
        sort_order = 0

        for feature_code, values_list in config.items():
            feature = features.get(feature_code)
            if not feature:
                self.stdout.write(self.style.WARNING(f'  ! Feature "{feature_code}" not found'))
                continue

            for i, plan_slug in enumerate(plan_slugs):
                plan = plans.get(plan_slug)
                if not plan:
                    continue

                value = values_list[i]

                # Determine is_enabled
                is_enabled = True
                if feature.feature_type == FeatureType.BOOLEAN:
                    is_enabled = value.get('enabled', False)
                elif feature.feature_type == FeatureType.LIMIT:
                    is_enabled = value.get('limit', 0) != 0
                elif feature.feature_type == FeatureType.USAGE:
                    # USAGE features: enabled if credits > 0 or has text
                    credits = value.get('credits', -999)
                    is_enabled = credits != 0 or 'text' in value

                defaults = {
                    'value': value,
                    'is_enabled': is_enabled,
                    'sort_order': sort_order,
                }

                pf, created = PlanFeature.objects.update_or_create(
                    plan=plan, feature=feature, defaults=defaults,
                )
                count += 1
                sort_order += 1

        return count

    # ─── DISPLAY FEATURES ────────────────────────────────────────────────────

    def _create_display_features(self, plans, force, dry_run):
        """Create PlanDisplayFeature marketing bullet points with SVG icons."""
        from apps.website.models import PlanDisplayFeature

        display_data = {
            'free': [
                (SVG['star'], 'Sıfır risk, tam deneyim'),
                (SVG['clock'], 'Kendi hızında keşfet'),
                (SVG['user'], 'Tek kullanıcı, tam platform'),
            ],
            'starter': [
                (SVG['bolt'], 'Hızlı büyüme, kontrollü maliyet'),
                (SVG['lock'], 'Güvenli altyapı, güvenilir marka'),
                (SVG['shield'], '14 gün tam özellik deneyin'),
            ],
            'growth': [
                (SVG['pulse'], 'Veriye dayalı kararlar'),
                (SVG['sun'], 'Otomatize, ölçeklen, kazan'),
                (SVG['users'], 'Takım olarak daha güçlü'),
            ],
            'professional': [
                (SVG['trend'], 'Sınırsız ölçek, sınırsız ambisyon'),
                (SVG['shield'], '7/24 öncelikli destek'),
                (SVG['monitor'], 'API + tam entegrasyon'),
            ],
            'business': [
                (SVG['grid'], 'Merkezi yönetim, dağıtık operasyon'),
                (SVG['database'], 'White-label hazır altyapı'),
                (SVG['phone'], 'Dedike hesap yöneticisi'),
            ],
            'enterprise': [
                (SVG['shield'], 'SLA güvenceli altyapı'),
                (SVG['globe'], 'On-premise veya private cloud'),
                (SVG['users'], 'Özel onboarding ve entegrasyon'),
            ],
        }

        count = 0
        for plan_slug, items in display_data.items():
            plan = plans.get(plan_slug)
            if not plan:
                continue

            if force:
                # Clear existing display features for this plan
                PlanDisplayFeature.objects.filter(plan=plan).delete()

            for sort_idx, (icon_svg, text) in enumerate(items):
                obj, created = PlanDisplayFeature.objects.get_or_create(
                    plan=plan,
                    text=text,
                    defaults={
                        'icon_svg': icon_svg,
                        'sort_order': (sort_idx + 1) * 10,
                        'is_active': True,
                        'is_highlighted': False,
                    },
                )
                if not created and force:
                    obj.icon_svg = icon_svg
                    obj.sort_order = (sort_idx + 1) * 10
                    obj.is_active = True
                    obj.save()
                count += 1

            self.stdout.write(f'  + Display features for: {plan_slug} ({len(items)} items)')

        return count
