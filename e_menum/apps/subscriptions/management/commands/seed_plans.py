"""
Django management command for seeding initial Plans and Features.

This command creates the default subscription plans and feature definitions
for E-Menum. It's idempotent - running it multiple times will update existing
records rather than creating duplicates.

Plan Tiers (from spec Appendix B):
| Plan | Menus | Products | QR Codes | Users | Storage | AI Credits |
|------|-------|----------|----------|-------|---------|------------|
| Free | 1 | 50 | 3 | 2 | 100MB | 0 |
| Starter (2K TRY) | 3 | 200 | 10 | 5 | 500MB | 100 |
| Growth (4K TRY) | 10 | 500 | 50 | 15 | 2GB | 500 |
| Professional (6K TRY) | 25 | 1000 | 100 | 30 | 5GB | 1000 |
| Enterprise (8K+ TRY) | unlimited | unlimited | unlimited | unlimited | 20GB | unlimited |

Usage:
    python manage.py seed_plans
    python manage.py seed_plans --force  # Force update existing records
    python manage.py seed_plans --dry-run  # Show what would be created
"""

from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.subscriptions.choices import FeatureType, PlanTier
from apps.subscriptions.models import Feature, Plan, PlanFeature


class Command(BaseCommand):
    """Management command to seed initial Plans and Features."""

    help = 'Seed initial subscription plans and features for E-Menum'

    def add_arguments(self, parser):
        """Add command line arguments."""
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force update existing records',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be created without making changes',
        )

    def handle(self, *args, **options):
        """Execute the command."""
        force = options['force']
        dry_run = options['dry_run']

        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN - No changes will be made'))

        try:
            with transaction.atomic():
                # Create features first
                features = self._create_features(force, dry_run)
                self.stdout.write(f'Created/updated {len(features)} features')

                # Create plans
                plans = self._create_plans(force, dry_run)
                self.stdout.write(f'Created/updated {len(plans)} plans')

                # Create plan-feature relationships
                plan_features = self._create_plan_features(plans, features, force, dry_run)
                self.stdout.write(f'Created/updated {len(plan_features)} plan-feature relationships')

                if dry_run:
                    # Rollback in dry run
                    raise DryRunException()

        except DryRunException:
            self.stdout.write(self.style.WARNING('Dry run completed - no changes were made'))
        except Exception as e:
            raise CommandError(f'Failed to seed plans: {str(e)}')

        if not dry_run:
            self.stdout.write(self.style.SUCCESS('Successfully seeded plans and features!'))

    def _create_features(self, force: bool, dry_run: bool) -> dict:
        """Create or update feature definitions."""
        features_data = [
            # Limit features
            {
                'code': 'max_menus',
                'name': 'Maximum Menus',
                'description': 'Maximum number of menus allowed for the organization',
                'feature_type': FeatureType.LIMIT,
                'default_value': {'limit': 1},
                'category': 'menus',
                'sort_order': 10,
            },
            {
                'code': 'max_products',
                'name': 'Maximum Products',
                'description': 'Maximum number of products allowed across all menus',
                'feature_type': FeatureType.LIMIT,
                'default_value': {'limit': 50},
                'category': 'menus',
                'sort_order': 20,
            },
            {
                'code': 'max_categories',
                'name': 'Maximum Categories',
                'description': 'Maximum number of categories allowed per menu',
                'feature_type': FeatureType.LIMIT,
                'default_value': {'limit': 10},
                'category': 'menus',
                'sort_order': 30,
            },
            {
                'code': 'max_qr_codes',
                'name': 'Maximum QR Codes',
                'description': 'Maximum number of QR codes allowed',
                'feature_type': FeatureType.LIMIT,
                'default_value': {'limit': 3},
                'category': 'qr',
                'sort_order': 40,
            },
            {
                'code': 'max_users',
                'name': 'Maximum Users',
                'description': 'Maximum number of team members allowed',
                'feature_type': FeatureType.LIMIT,
                'default_value': {'limit': 2},
                'category': 'team',
                'sort_order': 50,
            },
            {
                'code': 'max_branches',
                'name': 'Maximum Branches',
                'description': 'Maximum number of branch locations allowed',
                'feature_type': FeatureType.LIMIT,
                'default_value': {'limit': 1},
                'category': 'organization',
                'sort_order': 60,
            },
            {
                'code': 'storage_mb',
                'name': 'Storage (MB)',
                'description': 'Total storage space for images and files in megabytes',
                'feature_type': FeatureType.LIMIT,
                'default_value': {'limit': 100},
                'category': 'storage',
                'sort_order': 70,
            },
            # Usage features
            {
                'code': 'ai_credits_monthly',
                'name': 'Monthly AI Credits',
                'description': 'AI generation credits that reset monthly',
                'feature_type': FeatureType.USAGE,
                'default_value': {'credits': 0, 'reset_period': 'monthly'},
                'category': 'ai',
                'sort_order': 80,
            },
            # Boolean features
            {
                'code': 'ai_content_generation',
                'name': 'AI Content Generation',
                'description': 'Enable AI-powered content generation for menu descriptions',
                'feature_type': FeatureType.BOOLEAN,
                'default_value': {'enabled': False},
                'category': 'ai',
                'sort_order': 90,
            },
            {
                'code': 'analytics_basic',
                'name': 'Basic Analytics',
                'description': 'Access to basic analytics dashboard with QR scan counts',
                'feature_type': FeatureType.BOOLEAN,
                'default_value': {'enabled': True},
                'category': 'analytics',
                'sort_order': 100,
            },
            {
                'code': 'analytics_advanced',
                'name': 'Advanced Analytics',
                'description': 'Access to advanced analytics with customer insights and trends',
                'feature_type': FeatureType.BOOLEAN,
                'default_value': {'enabled': False},
                'category': 'analytics',
                'sort_order': 110,
            },
            {
                'code': 'custom_domain',
                'name': 'Custom Domain',
                'description': 'Use your own domain for menu URLs',
                'feature_type': FeatureType.BOOLEAN,
                'default_value': {'enabled': False},
                'category': 'branding',
                'sort_order': 120,
            },
            {
                'code': 'white_label',
                'name': 'White Label',
                'description': 'Remove E-Menum branding from public menus',
                'feature_type': FeatureType.BOOLEAN,
                'default_value': {'enabled': False},
                'category': 'branding',
                'sort_order': 130,
            },
            {
                'code': 'api_access',
                'name': 'API Access',
                'description': 'Access to REST API for integrations',
                'feature_type': FeatureType.BOOLEAN,
                'default_value': {'enabled': False},
                'category': 'integrations',
                'sort_order': 140,
            },
            {
                'code': 'priority_support',
                'name': 'Priority Support',
                'description': 'Priority customer support with faster response times',
                'feature_type': FeatureType.BOOLEAN,
                'default_value': {'enabled': False},
                'category': 'support',
                'sort_order': 150,
            },
            {
                'code': 'multi_language',
                'name': 'Multi-Language Menus',
                'description': 'Serve menus in multiple languages',
                'feature_type': FeatureType.BOOLEAN,
                'default_value': {'enabled': False},
                'category': 'menus',
                'sort_order': 160,
            },
            {
                'code': 'order_management',
                'name': 'Order Management',
                'description': 'Accept and manage orders from menus',
                'feature_type': FeatureType.BOOLEAN,
                'default_value': {'enabled': True},
                'category': 'orders',
                'sort_order': 170,
            },
            {
                'code': 'qr_code_customization',
                'name': 'QR Code Customization',
                'description': 'Customize QR code colors and branding',
                'feature_type': FeatureType.BOOLEAN,
                'default_value': {'enabled': False},
                'category': 'qr',
                'sort_order': 180,
            },
            {
                'code': 'customer_feedback',
                'name': 'Customer Feedback',
                'description': 'Collect customer feedback and ratings',
                'feature_type': FeatureType.BOOLEAN,
                'default_value': {'enabled': True},
                'category': 'customers',
                'sort_order': 190,
            },
            {
                'code': 'loyalty_program',
                'name': 'Loyalty Program',
                'description': 'Enable customer loyalty points and rewards',
                'feature_type': FeatureType.BOOLEAN,
                'default_value': {'enabled': False},
                'category': 'customers',
                'sort_order': 200,
            },
        ]

        features = {}
        for data in features_data:
            code = data['code']
            feature, created = Feature.objects.update_or_create(
                code=code,
                defaults=data if force else {},
            )
            if created:
                # Apply all data for new records
                for key, value in data.items():
                    setattr(feature, key, value)
                feature.save()
                self.stdout.write(f'  + Created feature: {code}')
            else:
                if force:
                    self.stdout.write(f'  ~ Updated feature: {code}')
                else:
                    self.stdout.write(f'  - Skipped feature: {code} (already exists)')
            features[code] = feature

        return features

    def _create_plans(self, force: bool, dry_run: bool) -> dict:
        """Create or update subscription plans."""
        plans_data = [
            {
                'slug': 'free',
                'name': 'Free',
                'tier': PlanTier.FREE,
                'description': 'Perfect for trying out E-Menum. Basic features to get started with digital menus.',
                'short_description': 'Get started for free',
                'price_monthly': Decimal('0.00'),
                'price_yearly': Decimal('0.00'),
                'currency': 'TRY',
                'trial_days': 0,
                'is_active': True,
                'is_default': True,
                'is_public': True,
                'is_custom': False,
                'sort_order': 10,
                'limits': {
                    'max_menus': 1,
                    'max_products': 50,
                    'max_categories': 10,
                    'max_qr_codes': 3,
                    'max_users': 2,
                    'max_branches': 1,
                    'storage_mb': 100,
                    'ai_credits_monthly': 0,
                },
                'feature_flags': {
                    'ai_content_generation': False,
                    'analytics_basic': True,
                    'analytics_advanced': False,
                    'custom_domain': False,
                    'white_label': False,
                    'api_access': False,
                    'priority_support': False,
                    'multi_language': False,
                    'order_management': True,
                    'qr_code_customization': False,
                    'customer_feedback': True,
                    'loyalty_program': False,
                },
            },
            {
                'slug': 'starter',
                'name': 'Starter',
                'tier': PlanTier.STARTER,
                'description': 'Essential features for small restaurants and cafes. Start growing your digital presence.',
                'short_description': 'For small businesses',
                'price_monthly': Decimal('2000.00'),
                'price_yearly': Decimal('20000.00'),  # ~2 months free
                'currency': 'TRY',
                'trial_days': 14,
                'is_active': True,
                'is_default': False,
                'is_public': True,
                'is_custom': False,
                'sort_order': 20,
                'limits': {
                    'max_menus': 3,
                    'max_products': 200,
                    'max_categories': 25,
                    'max_qr_codes': 10,
                    'max_users': 5,
                    'max_branches': 1,
                    'storage_mb': 500,
                    'ai_credits_monthly': 100,
                },
                'feature_flags': {
                    'ai_content_generation': True,
                    'analytics_basic': True,
                    'analytics_advanced': False,
                    'custom_domain': False,
                    'white_label': False,
                    'api_access': False,
                    'priority_support': False,
                    'multi_language': False,
                    'order_management': True,
                    'qr_code_customization': True,
                    'customer_feedback': True,
                    'loyalty_program': False,
                },
            },
            {
                'slug': 'growth',
                'name': 'Growth',
                'tier': PlanTier.GROWTH,
                'description': 'More power for growing businesses. Advanced analytics and AI capabilities.',
                'short_description': 'For growing businesses',
                'price_monthly': Decimal('4000.00'),
                'price_yearly': Decimal('40000.00'),  # ~2 months free
                'currency': 'TRY',
                'trial_days': 14,
                'is_active': True,
                'is_default': False,
                'is_public': True,
                'is_custom': False,
                'highlight_text': 'Most Popular',
                'sort_order': 30,
                'limits': {
                    'max_menus': 10,
                    'max_products': 500,
                    'max_categories': 50,
                    'max_qr_codes': 50,
                    'max_users': 15,
                    'max_branches': 3,
                    'storage_mb': 2048,  # 2GB
                    'ai_credits_monthly': 500,
                },
                'feature_flags': {
                    'ai_content_generation': True,
                    'analytics_basic': True,
                    'analytics_advanced': True,
                    'custom_domain': False,
                    'white_label': False,
                    'api_access': True,
                    'priority_support': False,
                    'multi_language': True,
                    'order_management': True,
                    'qr_code_customization': True,
                    'customer_feedback': True,
                    'loyalty_program': True,
                },
            },
            {
                'slug': 'professional',
                'name': 'Professional',
                'tier': PlanTier.PROFESSIONAL,
                'description': 'Full-featured solution for established businesses. Custom branding and priority support.',
                'short_description': 'For established businesses',
                'price_monthly': Decimal('6000.00'),
                'price_yearly': Decimal('60000.00'),  # ~2 months free
                'currency': 'TRY',
                'trial_days': 14,
                'is_active': True,
                'is_default': False,
                'is_public': True,
                'is_custom': False,
                'highlight_text': 'Best Value',
                'sort_order': 40,
                'limits': {
                    'max_menus': 25,
                    'max_products': 1000,
                    'max_categories': 100,
                    'max_qr_codes': 100,
                    'max_users': 30,
                    'max_branches': 5,
                    'storage_mb': 5120,  # 5GB
                    'ai_credits_monthly': 1000,
                },
                'feature_flags': {
                    'ai_content_generation': True,
                    'analytics_basic': True,
                    'analytics_advanced': True,
                    'custom_domain': True,
                    'white_label': True,
                    'api_access': True,
                    'priority_support': True,
                    'multi_language': True,
                    'order_management': True,
                    'qr_code_customization': True,
                    'customer_feedback': True,
                    'loyalty_program': True,
                },
            },
            {
                'slug': 'enterprise',
                'name': 'Enterprise',
                'tier': PlanTier.ENTERPRISE,
                'description': 'Unlimited everything with dedicated support. Custom solutions for large organizations and chains.',
                'short_description': 'For large organizations',
                'price_monthly': Decimal('8000.00'),
                'price_yearly': Decimal('80000.00'),
                'currency': 'TRY',
                'trial_days': 30,
                'is_active': True,
                'is_default': False,
                'is_public': True,
                'is_custom': False,
                'sort_order': 50,
                'limits': {
                    'max_menus': -1,  # Unlimited
                    'max_products': -1,
                    'max_categories': -1,
                    'max_qr_codes': -1,
                    'max_users': -1,
                    'max_branches': -1,
                    'storage_mb': 20480,  # 20GB
                    'ai_credits_monthly': -1,
                },
                'feature_flags': {
                    'ai_content_generation': True,
                    'analytics_basic': True,
                    'analytics_advanced': True,
                    'custom_domain': True,
                    'white_label': True,
                    'api_access': True,
                    'priority_support': True,
                    'multi_language': True,
                    'order_management': True,
                    'qr_code_customization': True,
                    'customer_feedback': True,
                    'loyalty_program': True,
                },
            },
        ]

        plans = {}
        for data in plans_data:
            slug = data['slug']
            plan, created = Plan.objects.update_or_create(
                slug=slug,
                defaults=data if force else {},
            )
            if created:
                # Apply all data for new records
                for key, value in data.items():
                    setattr(plan, key, value)
                plan.save()
                self.stdout.write(f'  + Created plan: {data["name"]} ({slug})')
            else:
                if force:
                    self.stdout.write(f'  ~ Updated plan: {data["name"]} ({slug})')
                else:
                    self.stdout.write(f'  - Skipped plan: {data["name"]} ({slug}) (already exists)')
            plans[slug] = plan

        return plans

    def _create_plan_features(
        self,
        plans: dict,
        features: dict,
        force: bool,
        dry_run: bool
    ) -> list:
        """Create or update plan-feature relationships."""
        # Define plan-feature mappings with specific values
        plan_feature_config = {
            'free': {
                'max_menus': {'limit': 1},
                'max_products': {'limit': 50},
                'max_categories': {'limit': 10},
                'max_qr_codes': {'limit': 3},
                'max_users': {'limit': 2},
                'max_branches': {'limit': 1},
                'storage_mb': {'limit': 100},
                'ai_credits_monthly': {'credits': 0, 'reset_period': 'monthly'},
                'ai_content_generation': {'enabled': False},
                'analytics_basic': {'enabled': True},
                'analytics_advanced': {'enabled': False},
                'custom_domain': {'enabled': False},
                'white_label': {'enabled': False},
                'api_access': {'enabled': False},
                'priority_support': {'enabled': False},
                'multi_language': {'enabled': False},
                'order_management': {'enabled': True},
                'qr_code_customization': {'enabled': False},
                'customer_feedback': {'enabled': True},
                'loyalty_program': {'enabled': False},
            },
            'starter': {
                'max_menus': {'limit': 3},
                'max_products': {'limit': 200},
                'max_categories': {'limit': 25},
                'max_qr_codes': {'limit': 10},
                'max_users': {'limit': 5},
                'max_branches': {'limit': 1},
                'storage_mb': {'limit': 500},
                'ai_credits_monthly': {'credits': 100, 'reset_period': 'monthly'},
                'ai_content_generation': {'enabled': True},
                'analytics_basic': {'enabled': True},
                'analytics_advanced': {'enabled': False},
                'custom_domain': {'enabled': False},
                'white_label': {'enabled': False},
                'api_access': {'enabled': False},
                'priority_support': {'enabled': False},
                'multi_language': {'enabled': False},
                'order_management': {'enabled': True},
                'qr_code_customization': {'enabled': True},
                'customer_feedback': {'enabled': True},
                'loyalty_program': {'enabled': False},
            },
            'growth': {
                'max_menus': {'limit': 10},
                'max_products': {'limit': 500},
                'max_categories': {'limit': 50},
                'max_qr_codes': {'limit': 50},
                'max_users': {'limit': 15},
                'max_branches': {'limit': 3},
                'storage_mb': {'limit': 2048},
                'ai_credits_monthly': {'credits': 500, 'reset_period': 'monthly'},
                'ai_content_generation': {'enabled': True},
                'analytics_basic': {'enabled': True},
                'analytics_advanced': {'enabled': True},
                'custom_domain': {'enabled': False},
                'white_label': {'enabled': False},
                'api_access': {'enabled': True},
                'priority_support': {'enabled': False},
                'multi_language': {'enabled': True},
                'order_management': {'enabled': True},
                'qr_code_customization': {'enabled': True},
                'customer_feedback': {'enabled': True},
                'loyalty_program': {'enabled': True},
            },
            'professional': {
                'max_menus': {'limit': 25},
                'max_products': {'limit': 1000},
                'max_categories': {'limit': 100},
                'max_qr_codes': {'limit': 100},
                'max_users': {'limit': 30},
                'max_branches': {'limit': 5},
                'storage_mb': {'limit': 5120},
                'ai_credits_monthly': {'credits': 1000, 'reset_period': 'monthly'},
                'ai_content_generation': {'enabled': True},
                'analytics_basic': {'enabled': True},
                'analytics_advanced': {'enabled': True},
                'custom_domain': {'enabled': True},
                'white_label': {'enabled': True},
                'api_access': {'enabled': True},
                'priority_support': {'enabled': True},
                'multi_language': {'enabled': True},
                'order_management': {'enabled': True},
                'qr_code_customization': {'enabled': True},
                'customer_feedback': {'enabled': True},
                'loyalty_program': {'enabled': True},
            },
            'enterprise': {
                'max_menus': {'limit': -1},
                'max_products': {'limit': -1},
                'max_categories': {'limit': -1},
                'max_qr_codes': {'limit': -1},
                'max_users': {'limit': -1},
                'max_branches': {'limit': -1},
                'storage_mb': {'limit': 20480},
                'ai_credits_monthly': {'credits': -1, 'reset_period': 'monthly'},
                'ai_content_generation': {'enabled': True},
                'analytics_basic': {'enabled': True},
                'analytics_advanced': {'enabled': True},
                'custom_domain': {'enabled': True},
                'white_label': {'enabled': True},
                'api_access': {'enabled': True},
                'priority_support': {'enabled': True},
                'multi_language': {'enabled': True},
                'order_management': {'enabled': True},
                'qr_code_customization': {'enabled': True},
                'customer_feedback': {'enabled': True},
                'loyalty_program': {'enabled': True},
            },
        }

        created_plan_features = []
        sort_order = 0

        for plan_slug, feature_configs in plan_feature_config.items():
            plan = plans.get(plan_slug)
            if not plan:
                self.stdout.write(
                    self.style.WARNING(f'  ! Plan "{plan_slug}" not found, skipping')
                )
                continue

            for feature_code, value in feature_configs.items():
                feature = features.get(feature_code)
                if not feature:
                    self.stdout.write(
                        self.style.WARNING(f'  ! Feature "{feature_code}" not found, skipping')
                    )
                    continue

                # Determine if feature should be enabled
                is_enabled = True
                if feature.feature_type == FeatureType.BOOLEAN:
                    is_enabled = value.get('enabled', False)
                elif feature.feature_type == FeatureType.LIMIT:
                    is_enabled = value.get('limit', 0) != 0
                elif feature.feature_type == FeatureType.USAGE:
                    is_enabled = value.get('credits', 0) != 0

                defaults = {
                    'value': value,
                    'is_enabled': is_enabled,
                    'sort_order': sort_order,
                }

                plan_feature, created = PlanFeature.objects.update_or_create(
                    plan=plan,
                    feature=feature,
                    defaults=defaults if force else {},
                )

                if created:
                    for key, val in defaults.items():
                        setattr(plan_feature, key, val)
                    plan_feature.save()
                    created_plan_features.append(plan_feature)

                sort_order += 1

        return created_plan_features


class DryRunException(Exception):
    """Exception raised to rollback dry run transactions."""
    pass
