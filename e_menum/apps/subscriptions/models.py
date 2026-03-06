"""
Django ORM models for the Subscriptions application.

This module defines the subscription-related models for E-Menum:
- Feature: Individual capabilities/features that can be enabled per plan
- Plan: Subscription tiers (Free, Starter, Growth, Professional, Enterprise)
- Subscription: Organization-Plan relationship with billing lifecycle
- Invoice: Billing records for subscriptions
- PlanFeature: Junction table for plan-feature relationships
- OrganizationUsage: Resource usage tracking per organization

Critical Rules:
- Plans are platform-level (no organization FK)
- Features define capabilities that are controlled per plan
- Subscriptions link organizations to plans with billing state
- PlanFeature links plans to features with plan-specific configuration
- OrganizationUsage tracks resource consumption per tenant
- Use soft_delete() - never call delete() directly
"""

import uuid

from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.core.models import (
    Permission,
    SoftDeleteManager,
    SoftDeleteMixin,
    TimeStampedMixin,
)
from apps.subscriptions.choices import (
    BillingPeriod,
    FeatureCategoryType,
    FeatureType,
    InvoiceStatus,
    PlanCardStyle,
    PlanCtaStyle,
    PlanRibbonColor,
    PlanTier,
    SubscriptionPaymentMethod,
    SubscriptionStatus,
)


class Feature(TimeStampedMixin, SoftDeleteMixin, models.Model):
    """
    Feature model - individual capabilities enabled per plan.

    Features represent specific functionalities or limits that can be
    assigned to subscription plans. They can be boolean (on/off),
    limit-based (max count), or usage-based (metered).

    Features are defined at the platform level and are not tenant-specific.
    They are linked to plans through the PlanFeature junction table.

    Note:
    - This is a platform-level model (no organization FK)
    - Use soft_delete() - never call delete() directly
    - Features should be created by platform administrators

    Attributes:
        id: UUID primary key (ensures global uniqueness)
        code: Unique identifier code for feature lookup (e.g., 'max_menus')
        name: Human-readable display name
        description: Detailed description of the feature
        feature_type: Type of feature (BOOLEAN, LIMIT, USAGE)
        default_value: Default value for the feature (JSON for flexibility)
        category: Category for grouping features (e.g., 'menus', 'orders')
        sort_order: Display order within category
        is_active: Whether the feature is currently available
        metadata: Additional metadata for the feature (JSON)

    Usage:
        # Create a boolean feature
        ai_feature = Feature.objects.create(
            code='ai_content_generation',
            name='AI Content Generation',
            description='Enable AI-powered content generation for menus',
            feature_type=FeatureType.BOOLEAN,
            default_value={'enabled': False},
            category='ai'
        )

        # Create a limit feature
        menu_limit = Feature.objects.create(
            code='max_menus',
            name='Maximum Menus',
            description='Maximum number of menus allowed',
            feature_type=FeatureType.LIMIT,
            default_value={'limit': 1},
            category='menus'
        )

        # Create a usage feature
        ai_credits = Feature.objects.create(
            code='ai_credits_monthly',
            name='Monthly AI Credits',
            description='AI generation credits per month',
            feature_type=FeatureType.USAGE,
            default_value={'credits': 0, 'reset_period': 'monthly'},
            category='ai'
        )

        # Get all active features
        features = Feature.objects.filter(is_active=True)

        # Get features by category
        menu_features = Feature.objects.filter(category='menus', is_active=True)
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name=_('ID'),
        help_text=_('Unique identifier (UUID)')
    )

    code = models.CharField(
        max_length=100,
        unique=True,
        verbose_name=_('Code'),
        help_text=_('Unique identifier code for feature lookup (e.g., max_menus, ai_enabled)')
    )

    name = models.CharField(
        max_length=200,
        verbose_name=_('Name'),
        help_text=_('Human-readable display name for the feature')
    )

    description = models.TextField(
        blank=True,
        null=True,
        verbose_name=_('Description'),
        help_text=_('Detailed description of what this feature provides')
    )

    feature_type = models.CharField(
        max_length=20,
        choices=FeatureType.choices,
        default=FeatureType.BOOLEAN,
        db_index=True,
        verbose_name=_('Feature type'),
        help_text=_('Type of feature: BOOLEAN (on/off), LIMIT (max count), USAGE (metered)')
    )

    default_value = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_('Default value'),
        help_text=_('Default value for the feature (JSON format)')
    )

    category = models.CharField(
        max_length=50,
        choices=FeatureCategoryType.choices,
        db_index=True,
        verbose_name=_('Category'),
        help_text=_('Category for grouping features (e.g., menus, orders, ai, analytics)')
    )

    sort_order = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Sort order'),
        help_text=_('Display order within category (lower numbers appear first)')
    )

    is_active = models.BooleanField(
        default=True,
        db_index=True,
        verbose_name=_('Is active'),
        help_text=_('Whether the feature is currently available')
    )

    metadata = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_('Metadata'),
        help_text=_('Additional metadata for the feature (JSON)')
    )

    # Managers
    objects = SoftDeleteManager()  # Default: excludes soft-deleted
    all_objects = models.Manager()  # Includes ALL records

    class Meta:
        db_table = 'features'
        verbose_name = _('Feature')
        verbose_name_plural = _('Features')
        ordering = ['category', 'sort_order', 'name']
        indexes = [
            models.Index(fields=['code'], name='feature_code_idx'),
            models.Index(fields=['category', 'sort_order'], name='feature_cat_sort_idx'),
            models.Index(fields=['feature_type'], name='feature_type_idx'),
            models.Index(fields=['is_active', 'deleted_at'], name='feature_active_del_idx'),
        ]

    def __str__(self) -> str:
        return f"{self.name} ({self.code})"

    def __repr__(self) -> str:
        return f"<Feature(id={self.id}, code='{self.code}', type={self.feature_type})>"

    @property
    def is_boolean(self) -> bool:
        """Check if this is a boolean (on/off) feature."""
        return self.feature_type == FeatureType.BOOLEAN

    @property
    def is_limit(self) -> bool:
        """Check if this is a limit-based feature."""
        return self.feature_type == FeatureType.LIMIT

    @property
    def is_usage(self) -> bool:
        """Check if this is a usage-based (metered) feature."""
        return self.feature_type == FeatureType.USAGE

    @property
    def is_available(self) -> bool:
        """Check if feature is active and not deleted."""
        return self.is_active and not self.is_deleted

    def get_default_limit(self) -> int:
        """
        Get the default limit value for limit-type features.

        Returns:
            The default limit, or 0 if not a limit feature or not set
        """
        if not self.is_limit:
            return 0
        return self.default_value.get('limit', 0)

    def get_default_enabled(self) -> bool:
        """
        Get the default enabled value for boolean features.

        Returns:
            True if enabled by default, False otherwise
        """
        if not self.is_boolean:
            return False
        return self.default_value.get('enabled', False)

    def get_metadata(self, key: str, default=None):
        """
        Get a value from feature metadata.

        Args:
            key: The metadata key to retrieve
            default: Default value if key not found

        Returns:
            The metadata value or default
        """
        return self.metadata.get(key, default)

    def set_metadata(self, key: str, value) -> None:
        """
        Set a value in feature metadata.

        Args:
            key: The metadata key
            value: The value to set
        """
        self.metadata[key] = value
        self.save(update_fields=['metadata', 'updated_at'])


class FeaturePermission(TimeStampedMixin, models.Model):
    """
    FeaturePermission - links a Feature to a Permission (plan-gated permission).

    When an organization's plan has a feature, the permissions linked here
    are granted (e.g. feature 'ai_content_generation' gates permission 'ai_generation.create').
    Platform-level; no organization FK.
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name=_('ID'),
        help_text=_('Unique identifier (UUID)'),
    )
    feature = models.ForeignKey(
        Feature,
        on_delete=models.CASCADE,
        related_name='feature_permissions',
        verbose_name=_('Feature'),
        help_text=_('Feature that gates this permission'),
    )
    permission = models.ForeignKey(
        Permission,
        on_delete=models.CASCADE,
        related_name='feature_permissions',
        verbose_name=_('Permission'),
        help_text=_('Permission gated by the feature'),
    )

    class Meta:
        db_table = 'feature_permissions'
        verbose_name = _('Feature Permission')
        verbose_name_plural = _('Feature Permissions')
        ordering = ['feature', 'permission']
        unique_together = [['feature', 'permission']]
        indexes = [
            models.Index(fields=['feature'], name='featperm_feature_idx'),
            models.Index(fields=['permission'], name='featperm_permission_idx'),
        ]

    def __str__(self) -> str:
        return f"{self.feature.code} → {self.permission.code}"

    def __repr__(self) -> str:
        return f"<FeaturePermission(feature='{self.feature.code}', permission='{self.permission.code}')>"


class Plan(TimeStampedMixin, SoftDeleteMixin, models.Model):
    """
    Plan model - subscription tiers for E-Menum.

    Plans define the subscription levels available to organizations.
    Each plan has specific pricing, feature limits, and capabilities.
    Plans are platform-level entities and are not tenant-specific.

    Plan Tiers:
    - FREE: Basic features, limited usage (always available)
    - STARTER: Small businesses, essential features (₺2K/ay)
    - GROWTH: Growing businesses, more features (₺4K/ay)
    - PROFESSIONAL: Full features, priority support (₺6K/ay)
    - ENTERPRISE: Custom features, dedicated support (₺8K+/ay)

    Note:
    - This is a platform-level model (no organization FK)
    - Use soft_delete() - never call delete() directly
    - Plans should be created by platform administrators
    - Only one plan should be marked as is_default

    Attributes:
        id: UUID primary key (ensures global uniqueness)
        name: Display name of the plan
        slug: URL-friendly identifier (globally unique)
        tier: Plan tier level (FREE, STARTER, GROWTH, etc.)
        description: Detailed description of the plan
        short_description: Brief tagline for the plan
        price_monthly: Monthly subscription price
        price_yearly: Yearly subscription price (typically discounted)
        currency: Currency code for pricing (default: TRY)
        limits: JSON field containing plan limits
        feature_flags: JSON field containing boolean feature flags
        trial_days: Number of trial days for this plan (0 for no trial)
        is_active: Whether the plan is available for subscription
        is_default: Whether this is the default plan for new organizations
        is_public: Whether the plan is visible on the public pricing page
        is_custom: Whether this is a custom enterprise plan
        highlight_text: Optional badge text (e.g., "Most Popular")
        sort_order: Display order on pricing page
        metadata: Additional plan metadata (JSON)

    Usage:
        # Create a plan with limits
        starter = Plan.objects.create(
            name="Starter",
            slug="starter",
            tier=PlanTier.STARTER,
            description="Perfect for small restaurants",
            short_description="Essential features for small teams",
            price_monthly=Decimal("2000.00"),
            price_yearly=Decimal("20000.00"),
            limits={
                'max_menus': 3,
                'max_products': 200,
                'max_qr_codes': 10,
                'max_users': 5,
                'storage_mb': 500,
                'ai_credits_monthly': 100,
            },
            feature_flags={
                'ai_content_generation': True,
                'analytics_basic': True,
                'analytics_advanced': False,
                'custom_domain': False,
                'api_access': False,
            }
        )

        # Get all public plans
        public_plans = Plan.objects.filter(is_public=True, is_active=True)

        # Get default plan
        default_plan = Plan.objects.filter(is_default=True).first()

        # Get plan by tier
        free_plan = Plan.objects.filter(tier=PlanTier.FREE).first()
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name=_('ID'),
        help_text=_('Unique identifier (UUID)')
    )

    name = models.CharField(
        max_length=100,
        verbose_name=_('Name'),
        help_text=_('Display name of the plan (e.g., Starter, Professional)')
    )

    slug = models.SlugField(
        max_length=100,
        unique=True,
        verbose_name=_('Slug'),
        help_text=_('URL-friendly identifier (globally unique)')
    )

    tier = models.CharField(
        max_length=20,
        choices=PlanTier.choices,
        db_index=True,
        verbose_name=_('Tier'),
        help_text=_('Plan tier level (FREE, STARTER, GROWTH, etc.)')
    )

    description = models.TextField(
        blank=True,
        null=True,
        verbose_name=_('Description'),
        help_text=_('Detailed description of the plan and its features')
    )

    short_description = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name=_('Short description'),
        help_text=_('Brief tagline for the plan (shown on pricing cards)')
    )

    # Pricing
    price_monthly = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name=_('Monthly price'),
        help_text=_('Monthly subscription price')
    )

    price_yearly = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name=_('Yearly price'),
        help_text=_('Yearly subscription price (typically with discount)')
    )

    currency = models.CharField(
        max_length=3,
        default='TRY',
        verbose_name=_('Currency'),
        help_text=_('Currency code for pricing (e.g., TRY, USD, EUR)')
    )

    # Limits and Features (JSON fields for flexibility)
    limits = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_('Limits'),
        help_text=_(
            'Plan limits as JSON (e.g., {"max_menus": 3, "max_products": 200, '
            '"max_qr_codes": 10, "max_users": 5, "storage_mb": 500})'
        )
    )

    feature_flags = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_('Feature flags'),
        help_text=_(
            'Boolean feature flags as JSON (e.g., {"ai_enabled": true, '
            '"custom_domain": false, "api_access": false})'
        )
    )

    # Trial
    trial_days = models.PositiveIntegerField(
        default=14,
        verbose_name=_('Trial days'),
        help_text=_('Number of trial days for this plan (0 for no trial)')
    )

    # Status flags
    is_active = models.BooleanField(
        default=True,
        db_index=True,
        verbose_name=_('Is active'),
        help_text=_('Whether the plan is available for subscription')
    )

    is_default = models.BooleanField(
        default=False,
        db_index=True,
        verbose_name=_('Is default'),
        help_text=_('Whether this is the default plan for new organizations')
    )

    is_public = models.BooleanField(
        default=True,
        db_index=True,
        verbose_name=_('Is public'),
        help_text=_('Whether the plan is visible on the public pricing page')
    )

    is_custom = models.BooleanField(
        default=False,
        verbose_name=_('Is custom'),
        help_text=_('Whether this is a custom enterprise plan')
    )

    # Display
    highlight_text = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name=_('Highlight text'),
        help_text=_('Optional badge/ribbon text (e.g., "En Popüler", "Özel Teklif")')
    )

    # --- Pricing Card Display Fields ---
    card_css_class = models.CharField(
        max_length=20,
        choices=PlanCardStyle.choices,
        blank=True,
        default='',
        verbose_name=_('Card CSS class'),
        help_text=_('Visual style for the pricing card (free, start, grow, pro, biz, ent)')
    )

    badge_label = models.CharField(
        max_length=50,
        blank=True,
        default='',
        verbose_name=_('Badge label'),
        help_text=_('Badge text shown on card (e.g., "Ücretsiz", "Starter"). Falls back to plan name.')
    )

    motto = models.CharField(
        max_length=200,
        blank=True,
        default='',
        verbose_name=_('Motto'),
        help_text=_('Motivational italic quote on pricing card (e.g., "Her büyük iş küçük bir adımla başlar.")')
    )

    ribbon_color = models.CharField(
        max_length=10,
        choices=PlanRibbonColor.choices,
        blank=True,
        default='',
        verbose_name=_('Ribbon color'),
        help_text=_('Ribbon color if highlight_text is set (teal, gold, purple)')
    )

    cta_text = models.CharField(
        max_length=50,
        blank=True,
        default='',
        verbose_name=_('CTA button text'),
        help_text=_('Call-to-action button text (e.g., "Ücretsiz Başla", "14 Gün Dene", "İletişime Geçin")')
    )

    cta_style = models.CharField(
        max_length=20,
        choices=PlanCtaStyle.choices,
        blank=True,
        default='cta-out',
        verbose_name=_('CTA button style'),
        help_text=_('Button appearance: outline, primary (filled), or enterprise (gold)')
    )

    cta_url = models.CharField(
        max_length=200,
        blank=True,
        default='',
        verbose_name=_('CTA URL'),
        help_text=_('URL for the CTA button (Django URL name like "website:demo" or absolute URL)')
    )

    price_label = models.CharField(
        max_length=100,
        blank=True,
        default='',
        verbose_name=_('Price label'),
        help_text=_('Text below price (e.g., "Sonsuza kadar ücretsiz", "Aylık faturalanır")')
    )

    custom_price_text = models.CharField(
        max_length=50,
        blank=True,
        default='',
        verbose_name=_('Custom price text'),
        help_text=_('Custom price display for enterprise plans (e.g., "Özel Fiyat")')
    )

    has_glow_effect = models.BooleanField(
        default=False,
        verbose_name=_('Glow effect'),
        help_text=_('Show a radial glow effect on the card (used for highlighted/featured plans)')
    )

    sort_order = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Sort order'),
        help_text=_('Display order on pricing page (lower numbers appear first)')
    )

    # Additional metadata
    metadata = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_('Metadata'),
        help_text=_('Additional plan metadata (JSON)')
    )

    # Managers
    objects = SoftDeleteManager()  # Default: excludes soft-deleted
    all_objects = models.Manager()  # Includes ALL records

    class Meta:
        db_table = 'plans'
        verbose_name = _('Plan')
        verbose_name_plural = _('Plans')
        ordering = ['sort_order', 'price_monthly']
        indexes = [
            models.Index(fields=['tier'], name='plan_tier_idx'),
            models.Index(fields=['slug'], name='plan_slug_idx'),
            models.Index(fields=['is_active', 'is_public'], name='plan_active_public_idx'),
            models.Index(fields=['is_default'], name='plan_default_idx'),
            models.Index(fields=['sort_order'], name='plan_sort_idx'),
            models.Index(fields=['deleted_at'], name='plan_deleted_idx'),
        ]

    def __str__(self) -> str:
        return f"{self.name} ({self.tier})"

    def __repr__(self) -> str:
        return f"<Plan(id={self.id}, name='{self.name}', tier={self.tier})>"

    @property
    def is_free(self) -> bool:
        """Check if this is the free tier."""
        return self.tier == PlanTier.FREE

    @property
    def is_available(self) -> bool:
        """Check if plan is active and not deleted."""
        return self.is_active and not self.is_deleted

    @property
    def has_trial(self) -> bool:
        """Check if the plan offers a trial period."""
        return self.trial_days > 0

    @property
    def yearly_savings(self):
        """
        Calculate yearly savings compared to monthly billing.

        Returns:
            Decimal: Amount saved per year with yearly billing
        """
        monthly_yearly = self.price_monthly * 12
        return monthly_yearly - self.price_yearly

    @property
    def yearly_discount_percentage(self) -> int:
        """
        Calculate yearly discount percentage.

        Returns:
            int: Discount percentage (0-100)
        """
        if self.price_monthly == 0:
            return 0
        monthly_yearly = self.price_monthly * 12
        if monthly_yearly == 0:
            return 0
        discount = ((monthly_yearly - self.price_yearly) / monthly_yearly) * 100
        return round(discount)

    @property
    def yearly_per_month(self) -> int:
        """
        Calculate yearly price divided by 12 (monthly equivalent when billed yearly).

        Used in the pricing cards template for the monthly/yearly toggle.
        Returns an integer for clean display (e.g., 1666 instead of 1666.67).

        Returns:
            int: Rounded-down yearly price per month
        """
        if self.price_yearly == 0:
            return 0
        from decimal import Decimal, ROUND_DOWN
        return int((self.price_yearly / Decimal('12')).to_integral_value(rounding=ROUND_DOWN))

    @property
    def formatted_price_monthly(self) -> str:
        """Return formatted monthly price with currency symbol."""
        currency_symbols = {
            'TRY': '₺',
            'USD': '$',
            'EUR': '€',
            'GBP': '£',
        }
        symbol = currency_symbols.get(self.currency, self.currency)
        if self.price_monthly == 0:
            return _('Free')
        return f"{symbol}{self.price_monthly:,.0f}"

    @property
    def formatted_price_yearly(self) -> str:
        """Return formatted yearly price with currency symbol."""
        currency_symbols = {
            'TRY': '₺',
            'USD': '$',
            'EUR': '€',
            'GBP': '£',
        }
        symbol = currency_symbols.get(self.currency, self.currency)
        if self.price_yearly == 0:
            return _('Free')
        return f"{symbol}{self.price_yearly:,.0f}"

    def get_limit(self, key: str, default: int = 0) -> int:
        """
        Get a specific limit value.

        Args:
            key: The limit key (e.g., 'max_menus', 'max_products')
            default: Default value if key not found

        Returns:
            The limit value, or -1 for unlimited
        """
        value = self.limits.get(key, default)
        # Convention: -1 means unlimited
        return value

    def get_feature_flag(self, key: str, default: bool = False) -> bool:
        """
        Get a specific feature flag value.

        Args:
            key: The feature flag key (e.g., 'ai_enabled', 'custom_domain')
            default: Default value if key not found

        Returns:
            The feature flag boolean value
        """
        return self.feature_flags.get(key, default)

    def has_feature(self, feature_code: str) -> bool:
        """
        Check if the plan has a specific feature enabled.

        Args:
            feature_code: The feature code to check

        Returns:
            True if the feature is enabled for this plan
        """
        return self.get_feature_flag(feature_code, False)

    def is_limit_exceeded(self, key: str, current_count: int) -> bool:
        """
        Check if a limit has been exceeded.

        Args:
            key: The limit key to check
            current_count: Current usage count

        Returns:
            True if the limit is exceeded, False otherwise
            (Always False for unlimited/-1 limits)
        """
        limit = self.get_limit(key)
        if limit == -1:  # Unlimited
            return False
        return current_count >= limit

    def get_remaining_quota(self, key: str, current_count: int) -> int:
        """
        Get remaining quota for a limit.

        Args:
            key: The limit key to check
            current_count: Current usage count

        Returns:
            Remaining quota, or -1 for unlimited
        """
        limit = self.get_limit(key)
        if limit == -1:  # Unlimited
            return -1
        return max(0, limit - current_count)

    def set_as_default(self) -> None:
        """
        Set this plan as the default for new organizations.

        Clears is_default flag on all other plans and sets this plan as default.
        """
        # Clear default flag on other plans
        Plan.objects.filter(is_default=True).exclude(pk=self.pk).update(is_default=False)

        # Set this plan as default
        self.is_default = True
        self.save(update_fields=['is_default', 'updated_at'])

    def compare_to(self, other_plan: 'Plan') -> dict:
        """
        Compare this plan to another plan.

        Args:
            other_plan: The plan to compare against

        Returns:
            Dictionary with comparison results for limits and features
        """
        comparison = {
            'limits': {},
            'features': {},
        }

        # Compare limits
        all_limit_keys = set(self.limits.keys()) | set(other_plan.limits.keys())
        for key in all_limit_keys:
            self_value = self.get_limit(key)
            other_value = other_plan.get_limit(key)
            comparison['limits'][key] = {
                'self': self_value,
                'other': other_value,
                'difference': self_value - other_value if (self_value != -1 and other_value != -1) else None,
            }

        # Compare feature flags
        all_feature_keys = set(self.feature_flags.keys()) | set(other_plan.feature_flags.keys())
        for key in all_feature_keys:
            self_value = self.get_feature_flag(key)
            other_value = other_plan.get_feature_flag(key)
            comparison['features'][key] = {
                'self': self_value,
                'other': other_value,
            }

        return comparison

    def get_metadata(self, key: str, default=None):
        """
        Get a value from plan metadata.

        Args:
            key: The metadata key to retrieve
            default: Default value if key not found

        Returns:
            The metadata value or default
        """
        return self.metadata.get(key, default)

    def set_metadata(self, key: str, value) -> None:
        """
        Set a value in plan metadata.

        Args:
            key: The metadata key
            value: The value to set
        """
        self.metadata[key] = value
        self.save(update_fields=['metadata', 'updated_at'])

    @classmethod
    def get_default_limits(cls) -> dict:
        """
        Get default limit structure for new plans.

        Returns:
            Dictionary with standard limit keys and default values
        """
        return {
            'max_menus': 1,
            'max_products': 50,
            'max_categories': 10,
            'max_qr_codes': 3,
            'max_users': 2,
            'max_branches': 1,
            'storage_mb': 100,
            'ai_credits_monthly': 0,
        }

    @classmethod
    def get_default_feature_flags(cls) -> dict:
        """
        Get default feature flags for new plans.

        Returns:
            Dictionary with standard feature flag keys and default values
        """
        return {
            'ai_content_generation': False,
            'analytics_basic': True,
            'analytics_advanced': False,
            'custom_domain': False,
            'api_access': False,
            'white_label': False,
            'priority_support': False,
            'multi_language': False,
            'order_management': True,
            'qr_code_customization': False,
        }


class Subscription(TimeStampedMixin, SoftDeleteMixin, models.Model):
    """
    Subscription model - links Organization to Plan with billing lifecycle.

    This is the core billing entity that tracks an organization's
    subscription to a plan, including trial periods, billing cycles,
    payment status, and renewal management.

    Subscription Lifecycle:
    1. TRIALING: Organization starts with trial (trial_ends_at set)
    2. ACTIVE: Payment successful, subscription active
    3. PAST_DUE: Payment failed, grace period (7 days)
    4. CANCELLED: User cancelled, access until period end
    5. EXPIRED: Period ended or trial expired without payment
    6. SUSPENDED: Admin action, immediate access revocation

    Note:
    - Each organization has ONE active subscription at a time
    - Use soft_delete() - never call delete() directly
    - Status transitions should be logged to AuditLog
    - External payment IDs link to Iyzico or other providers

    Attributes:
        id: UUID primary key (ensures global uniqueness)
        organization: FK to Organization (tenant)
        plan: FK to Plan (subscription tier)
        status: Current subscription status
        billing_period: MONTHLY or YEARLY billing cycle
        payment_method: How the subscription is paid
        current_price: Locked-in price at subscription time
        currency: Currency code for pricing (default: TRY)
        trial_ends_at: When trial period ends (null if no trial)
        current_period_start: Start of current billing period
        current_period_end: End of current billing period
        next_billing_date: When next payment will be charged
        cancelled_at: When cancellation was requested
        cancel_reason: User-provided cancellation reason
        cancel_at_period_end: If true, cancel at period end vs immediate
        external_subscription_id: ID from payment provider (Iyzico)
        external_customer_id: Customer ID from payment provider
        payment_details: JSON for payment method details (masked card, etc.)
        metadata: Additional subscription metadata (JSON)

    Usage:
        # Create a subscription for organization
        subscription = Subscription.objects.create(
            organization=org,
            plan=starter_plan,
            status=SubscriptionStatus.TRIALING,
            billing_period=BillingPeriod.MONTHLY,
            current_price=plan.price_monthly,
            trial_ends_at=timezone.now() + timedelta(days=14),
            current_period_start=timezone.now(),
            current_period_end=timezone.now() + timedelta(days=14)
        )

        # Activate after payment
        subscription.activate()

        # Cancel subscription
        subscription.cancel(reason='Too expensive', at_period_end=True)

        # Check subscription status
        if subscription.is_valid:
            # Grant access to features
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name=_('ID'),
        help_text=_('Unique identifier (UUID)')
    )

    organization = models.ForeignKey(
        'core.Organization',
        on_delete=models.CASCADE,
        related_name='subscriptions',
        verbose_name=_('Organization'),
        help_text=_('Organization this subscription belongs to')
    )

    plan = models.ForeignKey(
        Plan,
        on_delete=models.PROTECT,
        related_name='subscriptions',
        verbose_name=_('Plan'),
        help_text=_('Subscription plan')
    )

    status = models.CharField(
        max_length=20,
        choices=SubscriptionStatus.choices,
        default=SubscriptionStatus.TRIALING,
        db_index=True,
        verbose_name=_('Status'),
        help_text=_('Current subscription status')
    )

    billing_period = models.CharField(
        max_length=20,
        choices=BillingPeriod.choices,
        default=BillingPeriod.MONTHLY,
        verbose_name=_('Billing period'),
        help_text=_('Billing cycle (MONTHLY or YEARLY)')
    )

    payment_method = models.CharField(
        max_length=20,
        choices=SubscriptionPaymentMethod.choices,
        blank=True,
        null=True,
        verbose_name=_('Payment method'),
        help_text=_('How the subscription is paid')
    )

    # Pricing locked at subscription time
    current_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name=_('Current price'),
        help_text=_('Locked-in price at subscription time')
    )

    currency = models.CharField(
        max_length=3,
        default='TRY',
        verbose_name=_('Currency'),
        help_text=_('Currency code for pricing (e.g., TRY, USD, EUR)')
    )

    # Trial management
    trial_ends_at = models.DateTimeField(
        null=True,
        blank=True,
        db_index=True,
        verbose_name=_('Trial ends at'),
        help_text=_('When the trial period ends (null if no trial)')
    )

    # Billing period tracking
    current_period_start = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Current period start'),
        help_text=_('Start of the current billing period')
    )

    current_period_end = models.DateTimeField(
        null=True,
        blank=True,
        db_index=True,
        verbose_name=_('Current period end'),
        help_text=_('End of the current billing period')
    )

    next_billing_date = models.DateTimeField(
        null=True,
        blank=True,
        db_index=True,
        verbose_name=_('Next billing date'),
        help_text=_('When next payment will be charged')
    )

    # Cancellation tracking
    cancelled_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Cancelled at'),
        help_text=_('When cancellation was requested')
    )

    cancel_reason = models.TextField(
        blank=True,
        null=True,
        verbose_name=_('Cancel reason'),
        help_text=_('User-provided reason for cancellation')
    )

    cancel_at_period_end = models.BooleanField(
        default=False,
        verbose_name=_('Cancel at period end'),
        help_text=_('If true, subscription will cancel at end of current period')
    )

    # External payment provider IDs (for Iyzico integration)
    external_subscription_id = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        db_index=True,
        verbose_name=_('External subscription ID'),
        help_text=_('Subscription ID from payment provider (e.g., Iyzico)')
    )

    external_customer_id = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        db_index=True,
        verbose_name=_('External customer ID'),
        help_text=_('Customer ID from payment provider')
    )

    # Payment details (masked card info, etc.)
    payment_details = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_('Payment details'),
        help_text=_('Masked payment method details (e.g., {"last4": "4242", "brand": "visa"})')
    )

    # Additional metadata
    metadata = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_('Metadata'),
        help_text=_('Additional subscription metadata (JSON)')
    )

    # Managers
    objects = SoftDeleteManager()  # Default: excludes soft-deleted
    all_objects = models.Manager()  # Includes ALL records

    class Meta:
        db_table = 'subscriptions'
        verbose_name = _('Subscription')
        verbose_name_plural = _('Subscriptions')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['organization', 'status'], name='sub_org_status_idx'),
            models.Index(fields=['status', 'current_period_end'], name='sub_status_period_idx'),
            models.Index(fields=['status', 'next_billing_date'], name='sub_status_billing_idx'),
            models.Index(fields=['trial_ends_at'], name='sub_trial_ends_idx'),
            models.Index(fields=['external_subscription_id'], name='sub_ext_sub_id_idx'),
            models.Index(fields=['external_customer_id'], name='sub_ext_cust_id_idx'),
            models.Index(fields=['deleted_at'], name='sub_deleted_idx'),
        ]

    def __str__(self) -> str:
        return f"{self.organization.name} - {self.plan.name} ({self.status})"

    def __repr__(self) -> str:
        return f"<Subscription(id={self.id}, org='{self.organization.name}', plan='{self.plan.name}', status={self.status})>"

    @property
    def is_active(self) -> bool:
        """Check if subscription is currently active (ACTIVE or TRIALING)."""
        return self.status in (SubscriptionStatus.ACTIVE, SubscriptionStatus.TRIALING)

    @property
    def is_trialing(self) -> bool:
        """Check if subscription is in trial period."""
        return self.status == SubscriptionStatus.TRIALING

    @property
    def is_cancelled(self) -> bool:
        """Check if subscription has been cancelled."""
        return self.status == SubscriptionStatus.CANCELLED or self.cancelled_at is not None

    @property
    def is_expired(self) -> bool:
        """Check if subscription has expired."""
        return self.status == SubscriptionStatus.EXPIRED

    @property
    def is_past_due(self) -> bool:
        """Check if subscription is past due."""
        return self.status == SubscriptionStatus.PAST_DUE

    @property
    def is_suspended(self) -> bool:
        """Check if subscription has been suspended."""
        return self.status == SubscriptionStatus.SUSPENDED

    @property
    def is_valid(self) -> bool:
        """
        Check if subscription grants access to features.

        Returns True if:
        - Status is ACTIVE or TRIALING
        - Not soft-deleted
        - Current period hasn't ended
        """
        if self.is_deleted:
            return False
        if self.status not in (SubscriptionStatus.ACTIVE, SubscriptionStatus.TRIALING):
            return False
        if self.current_period_end and timezone.now() > self.current_period_end:
            return False
        return True

    @property
    def trial_remaining_days(self) -> int:
        """
        Get remaining trial days.

        Returns:
            Number of days remaining in trial, or 0 if not trialing
        """
        if not self.is_trialing or not self.trial_ends_at:
            return 0
        remaining = self.trial_ends_at - timezone.now()
        return max(0, remaining.days)

    @property
    def days_until_renewal(self) -> int:
        """
        Get days until next billing/renewal.

        Returns:
            Number of days until next billing, or 0 if no next billing
        """
        if not self.next_billing_date:
            return 0
        remaining = self.next_billing_date - timezone.now()
        return max(0, remaining.days)

    @property
    def formatted_price(self) -> str:
        """Return formatted current price with currency symbol."""
        currency_symbols = {
            'TRY': '₺',
            'USD': '$',
            'EUR': '€',
            'GBP': '£',
        }
        symbol = currency_symbols.get(self.currency, self.currency)
        if self.current_price == 0:
            return _('Free')
        return f"{symbol}{self.current_price:,.0f}"

    def activate(self, payment_details: dict = None) -> None:
        """
        Activate the subscription after successful payment.

        Args:
            payment_details: Optional payment details to store
        """
        from django.utils import timezone

        self.status = SubscriptionStatus.ACTIVE
        if payment_details:
            self.payment_details = payment_details
        self.save(update_fields=['status', 'payment_details', 'updated_at'])

    def mark_past_due(self) -> None:
        """Mark subscription as past due after failed payment."""
        self.status = SubscriptionStatus.PAST_DUE
        self.save(update_fields=['status', 'updated_at'])

    def cancel(self, reason: str = None, at_period_end: bool = True) -> None:
        """
        Cancel the subscription.

        Args:
            reason: Optional reason for cancellation
            at_period_end: If True, cancel at end of period; if False, cancel immediately
        """
        from django.utils import timezone

        self.cancelled_at = timezone.now()
        self.cancel_reason = reason
        self.cancel_at_period_end = at_period_end

        if at_period_end:
            self.status = SubscriptionStatus.CANCELLED
        else:
            self.status = SubscriptionStatus.EXPIRED

        self.save(update_fields=[
            'status', 'cancelled_at', 'cancel_reason',
            'cancel_at_period_end', 'updated_at'
        ])

    def expire(self) -> None:
        """Mark subscription as expired."""
        self.status = SubscriptionStatus.EXPIRED
        self.save(update_fields=['status', 'updated_at'])

    def suspend(self, reason: str = None) -> None:
        """
        Suspend the subscription (admin action).

        Args:
            reason: Optional reason for suspension
        """
        self.status = SubscriptionStatus.SUSPENDED
        if reason:
            self.metadata['suspension_reason'] = reason
            self.metadata['suspended_at'] = timezone.now().isoformat()
        self.save(update_fields=['status', 'metadata', 'updated_at'])

    def reactivate(self) -> None:
        """Reactivate a suspended or cancelled subscription."""
        self.status = SubscriptionStatus.ACTIVE
        self.cancelled_at = None
        self.cancel_reason = None
        self.cancel_at_period_end = False
        self.metadata.pop('suspension_reason', None)
        self.metadata.pop('suspended_at', None)
        self.save(update_fields=[
            'status', 'cancelled_at', 'cancel_reason',
            'cancel_at_period_end', 'metadata', 'updated_at'
        ])

    def renew(self, new_period_end: 'datetime' = None) -> None:
        """
        Renew the subscription for a new billing period.

        Args:
            new_period_end: Optional end date for new period
        """
        from datetime import timedelta
        from django.utils import timezone

        self.current_period_start = self.current_period_end or timezone.now()

        if new_period_end:
            self.current_period_end = new_period_end
        else:
            # Calculate based on billing period
            if self.billing_period == BillingPeriod.YEARLY:
                self.current_period_end = self.current_period_start + timedelta(days=365)
            else:
                self.current_period_end = self.current_period_start + timedelta(days=30)

        self.next_billing_date = self.current_period_end
        self.status = SubscriptionStatus.ACTIVE
        self.save(update_fields=[
            'current_period_start', 'current_period_end',
            'next_billing_date', 'status', 'updated_at'
        ])

    def change_plan(self, new_plan: Plan, prorate: bool = True) -> None:
        """
        Change the subscription to a different plan.

        Args:
            new_plan: The new Plan to switch to
            prorate: Whether to prorate the change (for billing purposes)
        """
        old_plan = self.plan
        self.plan = new_plan

        # Update price based on billing period
        if self.billing_period == BillingPeriod.YEARLY:
            self.current_price = new_plan.price_yearly
        else:
            self.current_price = new_plan.price_monthly

        # Store upgrade/downgrade info in metadata
        self.metadata['previous_plan'] = str(old_plan.id)
        self.metadata['plan_changed_at'] = timezone.now().isoformat()
        self.metadata['proration_applied'] = prorate

        self.save(update_fields=['plan', 'current_price', 'metadata', 'updated_at'])

    def get_metadata(self, key: str, default=None):
        """Get a value from subscription metadata."""
        return self.metadata.get(key, default)

    def set_metadata(self, key: str, value) -> None:
        """Set a value in subscription metadata."""
        self.metadata[key] = value
        self.save(update_fields=['metadata', 'updated_at'])


class Invoice(TimeStampedMixin, SoftDeleteMixin, models.Model):
    """
    Invoice model - billing records for subscriptions.

    Invoices track all billing transactions including subscription
    charges, one-time purchases, and refunds. They integrate with
    external payment providers and provide audit trail for billing.

    Invoice Lifecycle:
    1. DRAFT: Invoice being prepared (internal use)
    2. PENDING: Finalized and sent, awaiting payment
    3. PAID: Payment received and confirmed
    4. VOID: Cancelled/voided (duplicate, error)
    5. REFUNDED: Paid but subsequently refunded
    6. UNCOLLECTIBLE: Bad debt, unpayable

    Note:
    - Invoice numbers are unique within organization
    - Use soft_delete() - never call delete() directly
    - Payment details should be masked (no full card numbers)
    - All financial transactions should be logged

    Attributes:
        id: UUID primary key (ensures global uniqueness)
        organization: FK to Organization (tenant)
        subscription: FK to Subscription (optional for one-time purchases)
        invoice_number: Unique invoice number within organization
        status: Current invoice status
        amount_subtotal: Amount before tax
        amount_tax: Tax amount
        amount_total: Total amount due
        amount_paid: Amount actually paid
        amount_refunded: Amount refunded
        currency: Currency code
        due_date: When payment is due
        paid_at: When payment was received
        period_start: Start of billing period
        period_end: End of billing period
        description: Invoice description/memo
        line_items: JSON array of line items
        billing_address: JSON for billing address
        external_invoice_id: ID from payment provider
        external_payment_id: Payment transaction ID
        payment_details: Payment method details (masked)
        pdf_url: URL to generated PDF invoice
        metadata: Additional invoice metadata

    Usage:
        # Create an invoice for subscription renewal
        invoice = Invoice.objects.create(
            organization=org,
            subscription=subscription,
            invoice_number=Invoice.generate_number(org),
            status=InvoiceStatus.PENDING,
            amount_subtotal=subscription.current_price,
            amount_tax=Decimal('0.00'),
            amount_total=subscription.current_price,
            currency='TRY',
            due_date=timezone.now() + timedelta(days=7),
            period_start=subscription.current_period_start,
            period_end=subscription.current_period_end,
            description=f'Subscription: {subscription.plan.name}'
        )

        # Mark as paid
        invoice.mark_paid(payment_id='iyzico_123', payment_details={...})
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name=_('ID'),
        help_text=_('Unique identifier (UUID)')
    )

    organization = models.ForeignKey(
        'core.Organization',
        on_delete=models.CASCADE,
        related_name='invoices',
        verbose_name=_('Organization'),
        help_text=_('Organization this invoice belongs to')
    )

    subscription = models.ForeignKey(
        Subscription,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='invoices',
        verbose_name=_('Subscription'),
        help_text=_('Related subscription (null for one-time purchases)')
    )

    invoice_number = models.CharField(
        max_length=50,
        verbose_name=_('Invoice number'),
        help_text=_('Unique invoice number within organization')
    )

    status = models.CharField(
        max_length=20,
        choices=InvoiceStatus.choices,
        default=InvoiceStatus.DRAFT,
        db_index=True,
        verbose_name=_('Status'),
        help_text=_('Current invoice status')
    )

    # Financial amounts
    amount_subtotal = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name=_('Subtotal'),
        help_text=_('Amount before tax')
    )

    amount_tax = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name=_('Tax amount'),
        help_text=_('Tax amount')
    )

    amount_total = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name=_('Total'),
        help_text=_('Total amount due')
    )

    amount_paid = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name=_('Amount paid'),
        help_text=_('Amount actually paid')
    )

    amount_refunded = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name=_('Amount refunded'),
        help_text=_('Amount refunded')
    )

    currency = models.CharField(
        max_length=3,
        default='TRY',
        verbose_name=_('Currency'),
        help_text=_('Currency code for this invoice')
    )

    # Dates
    due_date = models.DateTimeField(
        null=True,
        blank=True,
        db_index=True,
        verbose_name=_('Due date'),
        help_text=_('When payment is due')
    )

    paid_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Paid at'),
        help_text=_('When payment was received')
    )

    period_start = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Period start'),
        help_text=_('Start of billing period covered')
    )

    period_end = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Period end'),
        help_text=_('End of billing period covered')
    )

    # Invoice details
    description = models.TextField(
        blank=True,
        null=True,
        verbose_name=_('Description'),
        help_text=_('Invoice description or memo')
    )

    line_items = models.JSONField(
        default=list,
        blank=True,
        verbose_name=_('Line items'),
        help_text=_('Array of line items: [{description, quantity, unit_price, amount}]')
    )

    billing_address = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_('Billing address'),
        help_text=_('Billing address details (JSON)')
    )

    # External payment provider integration
    external_invoice_id = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        db_index=True,
        verbose_name=_('External invoice ID'),
        help_text=_('Invoice ID from payment provider')
    )

    external_payment_id = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        db_index=True,
        verbose_name=_('External payment ID'),
        help_text=_('Payment transaction ID from provider')
    )

    payment_details = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_('Payment details'),
        help_text=_('Masked payment method details')
    )

    # Generated invoice PDF
    pdf_url = models.URLField(
        blank=True,
        null=True,
        max_length=500,
        verbose_name=_('PDF URL'),
        help_text=_('URL to generated PDF invoice')
    )

    # Additional metadata
    metadata = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_('Metadata'),
        help_text=_('Additional invoice metadata (JSON)')
    )

    # Managers
    objects = SoftDeleteManager()  # Default: excludes soft-deleted
    all_objects = models.Manager()  # Includes ALL records

    class Meta:
        db_table = 'invoices'
        verbose_name = _('Invoice')
        verbose_name_plural = _('Invoices')
        ordering = ['-created_at']
        unique_together = [['organization', 'invoice_number']]
        indexes = [
            models.Index(fields=['organization', 'status'], name='invoice_org_status_idx'),
            models.Index(fields=['status', 'due_date'], name='invoice_status_due_idx'),
            models.Index(fields=['subscription'], name='invoice_subscription_idx'),
            models.Index(fields=['invoice_number'], name='invoice_number_idx'),
            models.Index(fields=['external_invoice_id'], name='invoice_ext_inv_id_idx'),
            models.Index(fields=['external_payment_id'], name='invoice_ext_pay_id_idx'),
            models.Index(fields=['deleted_at'], name='invoice_deleted_idx'),
        ]

    def __str__(self) -> str:
        return f"Invoice {self.invoice_number} - {self.organization.name} ({self.status})"

    def __repr__(self) -> str:
        return f"<Invoice(id={self.id}, number='{self.invoice_number}', status={self.status}, total={self.amount_total})>"

    @property
    def is_paid(self) -> bool:
        """Check if invoice has been paid."""
        return self.status == InvoiceStatus.PAID

    @property
    def is_pending(self) -> bool:
        """Check if invoice is pending payment."""
        return self.status == InvoiceStatus.PENDING

    @property
    def is_draft(self) -> bool:
        """Check if invoice is still a draft."""
        return self.status == InvoiceStatus.DRAFT

    @property
    def is_void(self) -> bool:
        """Check if invoice has been voided."""
        return self.status == InvoiceStatus.VOID

    @property
    def is_refunded(self) -> bool:
        """Check if invoice has been refunded."""
        return self.status == InvoiceStatus.REFUNDED

    @property
    def is_overdue(self) -> bool:
        """Check if invoice is overdue."""
        if self.status != InvoiceStatus.PENDING:
            return False
        if not self.due_date:
            return False
        return timezone.now() > self.due_date

    @property
    def amount_due(self) -> 'Decimal':
        """Calculate remaining amount due."""
        return self.amount_total - self.amount_paid + self.amount_refunded

    @property
    def formatted_total(self) -> str:
        """Return formatted total with currency symbol."""
        currency_symbols = {
            'TRY': '₺',
            'USD': '$',
            'EUR': '€',
            'GBP': '£',
        }
        symbol = currency_symbols.get(self.currency, self.currency)
        return f"{symbol}{self.amount_total:,.2f}"

    def finalize(self) -> None:
        """Finalize draft invoice and make it pending."""
        if self.status != InvoiceStatus.DRAFT:
            return
        self.status = InvoiceStatus.PENDING
        self.save(update_fields=['status', 'updated_at'])

    def mark_paid(
        self,
        payment_id: str = None,
        payment_details: dict = None,
        amount: 'Decimal' = None
    ) -> None:
        """
        Mark invoice as paid.

        Args:
            payment_id: External payment transaction ID
            payment_details: Masked payment method details
            amount: Amount paid (defaults to amount_total)
        """
        from django.utils import timezone

        self.status = InvoiceStatus.PAID
        self.paid_at = timezone.now()
        self.amount_paid = amount if amount is not None else self.amount_total

        if payment_id:
            self.external_payment_id = payment_id
        if payment_details:
            self.payment_details = payment_details

        self.save(update_fields=[
            'status', 'paid_at', 'amount_paid',
            'external_payment_id', 'payment_details', 'updated_at'
        ])

    def void(self, reason: str = None) -> None:
        """
        Void this invoice.

        Args:
            reason: Optional reason for voiding
        """
        self.status = InvoiceStatus.VOID
        if reason:
            self.metadata['void_reason'] = reason
            self.metadata['voided_at'] = timezone.now().isoformat()
        self.save(update_fields=['status', 'metadata', 'updated_at'])

    def refund(self, amount: 'Decimal' = None, reason: str = None) -> None:
        """
        Process a refund for this invoice.

        Args:
            amount: Amount to refund (defaults to full amount)
            reason: Optional reason for refund
        """
        from django.utils import timezone

        refund_amount = amount if amount is not None else self.amount_paid
        self.amount_refunded = refund_amount
        self.status = InvoiceStatus.REFUNDED

        self.metadata['refund_reason'] = reason
        self.metadata['refunded_at'] = timezone.now().isoformat()
        self.metadata['refund_amount'] = str(refund_amount)

        self.save(update_fields=[
            'status', 'amount_refunded', 'metadata', 'updated_at'
        ])

    def mark_uncollectible(self, reason: str = None) -> None:
        """
        Mark invoice as uncollectible (bad debt).

        Args:
            reason: Optional reason for marking uncollectible
        """
        self.status = InvoiceStatus.UNCOLLECTIBLE
        if reason:
            self.metadata['uncollectible_reason'] = reason
            self.metadata['marked_uncollectible_at'] = timezone.now().isoformat()
        self.save(update_fields=['status', 'metadata', 'updated_at'])

    def add_line_item(
        self,
        description: str,
        quantity: int = 1,
        unit_price: 'Decimal' = None,
        amount: 'Decimal' = None
    ) -> None:
        """
        Add a line item to the invoice.

        Args:
            description: Line item description
            quantity: Quantity (default: 1)
            unit_price: Price per unit
            amount: Total amount (defaults to quantity * unit_price)
        """
        from decimal import Decimal

        if unit_price is None:
            unit_price = Decimal('0.00')
        if amount is None:
            amount = Decimal(str(quantity)) * unit_price

        line_item = {
            'description': description,
            'quantity': quantity,
            'unit_price': str(unit_price),
            'amount': str(amount),
        }

        self.line_items.append(line_item)
        self.save(update_fields=['line_items', 'updated_at'])

    def recalculate_totals(self) -> None:
        """Recalculate subtotal and total from line items."""
        from decimal import Decimal

        subtotal = Decimal('0.00')
        for item in self.line_items:
            subtotal += Decimal(str(item.get('amount', '0')))

        self.amount_subtotal = subtotal
        self.amount_total = subtotal + self.amount_tax
        self.save(update_fields=['amount_subtotal', 'amount_total', 'updated_at'])

    @classmethod
    def generate_number(cls, organization, prefix: str = 'INV') -> str:
        """
        Generate a unique invoice number for organization.

        Args:
            organization: Organization to generate number for
            prefix: Invoice number prefix (default: INV)

        Returns:
            Unique invoice number like 'INV-2026-00001'
        """
        from django.utils import timezone

        year = timezone.now().year
        count = cls.objects.filter(
            organization=organization,
            invoice_number__startswith=f'{prefix}-{year}'
        ).count()

        return f"{prefix}-{year}-{str(count + 1).zfill(5)}"

    def get_metadata(self, key: str, default=None):
        """Get a value from invoice metadata."""
        return self.metadata.get(key, default)

    def set_metadata(self, key: str, value) -> None:
        """Set a value in invoice metadata."""
        self.metadata[key] = value
        self.save(update_fields=['metadata', 'updated_at'])


class PlanFeature(TimeStampedMixin, models.Model):
    """
    PlanFeature model - junction table linking Plans to Features.

    This enables many-to-many relationships between plans and features,
    with plan-specific configuration for each feature (overriding defaults).

    A PlanFeature entry defines:
    - Which feature is included in which plan
    - The specific value/limit for that feature in this plan
    - Whether the feature is enabled for this plan

    Note:
    - This is a platform-level model (no organization FK)
    - Features can have different values in different plans
    - If is_enabled is False, the feature is not available even if included

    Attributes:
        id: UUID primary key
        plan: FK to Plan
        feature: FK to Feature
        value: JSON field containing plan-specific feature configuration
        is_enabled: Whether the feature is enabled for this plan
        sort_order: Display order within plan (for UI listing)
        metadata: Additional metadata (JSON)

    Usage:
        # Link a feature to a plan with specific value
        plan_feature = PlanFeature.objects.create(
            plan=starter_plan,
            feature=max_menus_feature,
            value={'limit': 3},
            is_enabled=True
        )

        # Get all features for a plan
        features = PlanFeature.objects.filter(
            plan=plan,
            is_enabled=True
        ).select_related('feature')

        # Check if a plan has a specific feature
        has_ai = PlanFeature.objects.filter(
            plan=plan,
            feature__code='ai_content_generation',
            is_enabled=True
        ).exists()

        # Get feature value for a plan
        pf = PlanFeature.objects.get(plan=plan, feature__code='max_menus')
        limit = pf.get_limit()
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name=_('ID'),
        help_text=_('Unique identifier (UUID)')
    )

    plan = models.ForeignKey(
        Plan,
        on_delete=models.CASCADE,
        related_name='plan_features',
        verbose_name=_('Plan'),
        help_text=_('Plan that includes this feature')
    )

    feature = models.ForeignKey(
        Feature,
        on_delete=models.CASCADE,
        related_name='plan_features',
        verbose_name=_('Feature'),
        help_text=_('Feature included in the plan')
    )

    value = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_('Value'),
        help_text=_(
            'Plan-specific feature configuration (JSON). '
            'For LIMIT: {"limit": 10}, for BOOLEAN: {"enabled": true}, '
            'for USAGE: {"credits": 100, "reset_period": "monthly"}'
        )
    )

    is_enabled = models.BooleanField(
        default=True,
        db_index=True,
        verbose_name=_('Is enabled'),
        help_text=_('Whether this feature is enabled for this plan')
    )

    sort_order = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Sort order'),
        help_text=_('Display order within plan (lower numbers appear first)')
    )

    metadata = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_('Metadata'),
        help_text=_('Additional metadata for this plan-feature relationship (JSON)')
    )

    class Meta:
        db_table = 'plan_features'
        verbose_name = _('Plan Feature')
        verbose_name_plural = _('Plan Features')
        ordering = ['plan', 'sort_order', 'feature__category']
        unique_together = [['plan', 'feature']]
        indexes = [
            models.Index(fields=['plan', 'is_enabled'], name='planfeat_plan_enabled_idx'),
            models.Index(fields=['feature'], name='planfeat_feature_idx'),
            models.Index(fields=['plan', 'sort_order'], name='planfeat_plan_sort_idx'),
        ]

    def __str__(self) -> str:
        status = "enabled" if self.is_enabled else "disabled"
        return f"{self.plan.name} - {self.feature.name} ({status})"

    def __repr__(self) -> str:
        return f"<PlanFeature(plan='{self.plan.name}', feature='{self.feature.code}', enabled={self.is_enabled})>"

    @property
    def is_boolean(self) -> bool:
        """Check if the linked feature is a boolean type."""
        return self.feature.feature_type == FeatureType.BOOLEAN

    @property
    def is_limit(self) -> bool:
        """Check if the linked feature is a limit type."""
        return self.feature.feature_type == FeatureType.LIMIT

    @property
    def is_usage(self) -> bool:
        """Check if the linked feature is a usage type."""
        return self.feature.feature_type == FeatureType.USAGE

    def get_enabled(self) -> bool:
        """
        Get whether the feature is enabled.

        For boolean features, checks the 'enabled' key in value.
        For other types, returns is_enabled flag.

        Returns:
            True if the feature is enabled
        """
        if self.is_boolean:
            return self.value.get('enabled', False) and self.is_enabled
        return self.is_enabled

    def get_limit(self, default: int = 0) -> int:
        """
        Get the limit value for limit-type features.

        Args:
            default: Default value if limit not set

        Returns:
            The limit value, or -1 for unlimited
        """
        if not self.is_limit:
            return default
        return self.value.get('limit', default)

    def get_credits(self, default: int = 0) -> int:
        """
        Get the credits value for usage-type features.

        Args:
            default: Default value if credits not set

        Returns:
            The credits value
        """
        if not self.is_usage:
            return default
        return self.value.get('credits', default)

    def get_reset_period(self) -> str:
        """
        Get the reset period for usage-type features.

        Returns:
            The reset period ('monthly', 'weekly', 'daily', or 'never')
        """
        if not self.is_usage:
            return 'never'
        return self.value.get('reset_period', 'monthly')

    def get_value(self, key: str, default=None):
        """
        Get a specific value from the feature configuration.

        Args:
            key: The configuration key to retrieve
            default: Default value if key not found

        Returns:
            The value or default
        """
        return self.value.get(key, default)

    def set_value(self, key: str, val) -> None:
        """
        Set a specific value in the feature configuration.

        Args:
            key: The configuration key
            val: The value to set
        """
        self.value[key] = val
        self.save(update_fields=['value', 'updated_at'])

    def get_metadata(self, key: str, default=None):
        """Get a value from plan-feature metadata."""
        return self.metadata.get(key, default)

    def set_metadata(self, key: str, value) -> None:
        """Set a value in plan-feature metadata."""
        self.metadata[key] = value
        self.save(update_fields=['metadata', 'updated_at'])


class OrganizationUsage(TimeStampedMixin, models.Model):
    """
    OrganizationUsage model - tracks resource usage per organization.

    This model enables metering and limiting of usage-based features
    for organizations. It tracks current usage against plan limits
    and supports periodic resets (e.g., monthly AI credits).

    Usage tracking is essential for:
    - Enforcing plan limits (max menus, max products, etc.)
    - Metering usage-based features (AI generations, API calls)
    - Billing calculations for overage charges
    - Analytics on resource consumption

    Note:
    - This is tenant-scoped (has organization FK)
    - Use soft_delete() if needed, but typically usage records are retained
    - Reset operations should be performed by scheduled tasks

    Attributes:
        id: UUID primary key
        organization: FK to Organization (tenant)
        feature: FK to Feature being tracked
        current_usage: Current usage count for this period
        usage_limit: Limit from plan (cached for quick checks)
        period_start: Start of current tracking period
        period_end: End of current tracking period
        last_reset_at: When usage was last reset
        last_usage_at: When usage was last recorded
        metadata: Additional metadata (JSON)

    Usage:
        # Create usage tracking for an organization
        usage = OrganizationUsage.objects.create(
            organization=org,
            feature=ai_credits_feature,
            current_usage=0,
            usage_limit=100,
            period_start=timezone.now(),
            period_end=timezone.now() + timedelta(days=30)
        )

        # Increment usage
        usage.increment()

        # Check if limit exceeded
        if usage.is_limit_exceeded:
            raise QuotaExceededError()

        # Reset usage (e.g., at start of new billing period)
        usage.reset()

        # Get remaining quota
        remaining = usage.remaining_quota
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name=_('ID'),
        help_text=_('Unique identifier (UUID)')
    )

    organization = models.ForeignKey(
        'core.Organization',
        on_delete=models.CASCADE,
        related_name='usage_records',
        verbose_name=_('Organization'),
        help_text=_('Organization this usage belongs to')
    )

    feature = models.ForeignKey(
        Feature,
        on_delete=models.CASCADE,
        related_name='usage_records',
        verbose_name=_('Feature'),
        help_text=_('Feature being tracked')
    )

    current_usage = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Current usage'),
        help_text=_('Current usage count for this period')
    )

    usage_limit = models.IntegerField(
        default=-1,
        verbose_name=_('Usage limit'),
        help_text=_('Limit from plan (-1 = unlimited)')
    )

    period_start = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Period start'),
        help_text=_('Start of current tracking period')
    )

    period_end = models.DateTimeField(
        null=True,
        blank=True,
        db_index=True,
        verbose_name=_('Period end'),
        help_text=_('End of current tracking period')
    )

    last_reset_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Last reset at'),
        help_text=_('When usage was last reset')
    )

    last_usage_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Last usage at'),
        help_text=_('When usage was last recorded')
    )

    metadata = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_('Metadata'),
        help_text=_('Additional usage metadata (e.g., usage breakdown, history)')
    )

    class Meta:
        db_table = 'organization_usage'
        verbose_name = _('Organization Usage')
        verbose_name_plural = _('Organization Usage')
        ordering = ['-updated_at']
        unique_together = [['organization', 'feature']]
        indexes = [
            models.Index(fields=['organization', 'feature'], name='orgusage_org_feat_idx'),
            models.Index(fields=['organization', 'period_end'], name='orgusage_org_period_idx'),
            models.Index(fields=['feature', 'period_end'], name='orgusage_feat_period_idx'),
        ]

    def __str__(self) -> str:
        limit_str = str(self.usage_limit) if self.usage_limit >= 0 else "∞"
        return f"{self.organization.name} - {self.feature.name}: {self.current_usage}/{limit_str}"

    def __repr__(self) -> str:
        return f"<OrganizationUsage(org='{self.organization.name}', feature='{self.feature.code}', usage={self.current_usage}/{self.usage_limit})>"

    @property
    def is_unlimited(self) -> bool:
        """Check if usage has no limit (unlimited)."""
        return self.usage_limit == -1

    @property
    def is_limit_exceeded(self) -> bool:
        """
        Check if usage limit has been exceeded.

        Returns:
            True if current usage >= limit, False for unlimited
        """
        if self.is_unlimited:
            return False
        return self.current_usage >= self.usage_limit

    @property
    def remaining_quota(self) -> int:
        """
        Get remaining quota.

        Returns:
            Remaining usage count, or -1 for unlimited
        """
        if self.is_unlimited:
            return -1
        return max(0, self.usage_limit - self.current_usage)

    @property
    def usage_percentage(self) -> float:
        """
        Get usage as percentage of limit.

        Returns:
            Percentage (0-100+), or 0 for unlimited
        """
        if self.is_unlimited or self.usage_limit == 0:
            return 0.0
        return (self.current_usage / self.usage_limit) * 100

    @property
    def is_period_active(self) -> bool:
        """Check if current tracking period is active."""
        now = timezone.now()
        if self.period_start and self.period_end:
            return self.period_start <= now <= self.period_end
        return True  # No period restrictions

    @property
    def is_period_expired(self) -> bool:
        """Check if current tracking period has expired."""
        if not self.period_end:
            return False
        return timezone.now() > self.period_end

    def increment(self, amount: int = 1) -> bool:
        """
        Increment usage count.

        Args:
            amount: Amount to increment (default: 1)

        Returns:
            True if increment successful, False if would exceed limit
        """
        if not self.is_unlimited and (self.current_usage + amount) > self.usage_limit:
            return False

        self.current_usage += amount
        self.last_usage_at = timezone.now()
        self.save(update_fields=['current_usage', 'last_usage_at', 'updated_at'])
        return True

    def decrement(self, amount: int = 1) -> None:
        """
        Decrement usage count (e.g., for refunds or corrections).

        Args:
            amount: Amount to decrement (default: 1)
        """
        self.current_usage = max(0, self.current_usage - amount)
        self.save(update_fields=['current_usage', 'updated_at'])

    def set_usage(self, count: int) -> None:
        """
        Set usage to a specific count.

        Args:
            count: New usage count
        """
        self.current_usage = max(0, count)
        self.last_usage_at = timezone.now()
        self.save(update_fields=['current_usage', 'last_usage_at', 'updated_at'])

    def reset(self, new_period_end: 'datetime' = None) -> None:
        """
        Reset usage count (typically at start of new billing period).

        Args:
            new_period_end: Optional new period end date
        """
        from datetime import timedelta

        old_usage = self.current_usage

        self.current_usage = 0
        self.period_start = timezone.now()
        self.last_reset_at = timezone.now()

        if new_period_end:
            self.period_end = new_period_end
        elif self.period_end:
            # Default: extend by same period duration
            if self.period_start:
                duration = self.period_end - self.period_start
                self.period_end = self.period_start + duration
            else:
                # Default to 30 days
                self.period_end = self.period_start + timedelta(days=30)

        # Store reset history in metadata
        reset_history = self.metadata.get('reset_history', [])
        reset_history.append({
            'reset_at': timezone.now().isoformat(),
            'previous_usage': old_usage,
        })
        # Keep only last 12 resets
        self.metadata['reset_history'] = reset_history[-12:]

        self.save(update_fields=[
            'current_usage', 'period_start', 'period_end',
            'last_reset_at', 'metadata', 'updated_at'
        ])

    def update_limit(self, new_limit: int) -> None:
        """
        Update the usage limit (e.g., when plan changes).

        Args:
            new_limit: New usage limit (-1 for unlimited)
        """
        self.usage_limit = new_limit
        self.save(update_fields=['usage_limit', 'updated_at'])

    def can_use(self, amount: int = 1) -> bool:
        """
        Check if usage of given amount is allowed.

        Args:
            amount: Amount to check (default: 1)

        Returns:
            True if usage is allowed, False if would exceed limit
        """
        if self.is_unlimited:
            return True
        return (self.current_usage + amount) <= self.usage_limit

    def get_metadata(self, key: str, default=None):
        """Get a value from usage metadata."""
        return self.metadata.get(key, default)

    def set_metadata(self, key: str, value) -> None:
        """Set a value in usage metadata."""
        self.metadata[key] = value
        self.save(update_fields=['metadata', 'updated_at'])
