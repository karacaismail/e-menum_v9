"""
Django ORM models for the Subscriptions application.

This module defines the subscription-related models for E-Menum:
- Feature: Individual capabilities/features that can be enabled per plan
- Plan: Subscription tiers (Free, Starter, Growth, Professional, Enterprise)

Additional models to be added in later subtasks:
- Subscription: Organization-Plan relationship with billing
- Invoice: Billing records for subscriptions
- PlanFeature: Junction table for plan-feature relationships
- OrganizationUsage: Resource usage tracking per organization

Critical Rules:
- Plans are platform-level (no organization FK)
- Features define capabilities that are controlled per plan
- Use soft_delete() - never call delete() directly
"""

import uuid

from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.models import (
    SoftDeleteManager,
    SoftDeleteMixin,
    TimeStampedMixin,
)
from apps.subscriptions.choices import (
    BillingPeriod,
    FeatureType,
    PlanTier,
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
        help_text=_('Optional badge text (e.g., "Most Popular", "Best Value")')
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
