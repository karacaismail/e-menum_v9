"""
Plan Enforcement - Subscription plan limit checking and feature gating.

This module provides:
1. PlanEnforcementService: Core service for checking plan limits & features
2. RequiresPlanFeature: DRF permission class for feature gating
3. CheckPlanLimit: DRF permission class for limit checking
4. PlanEnforcementMixin: Mixin for ViewSets with auto plan checking on create

How It Works:
- When an org tries to create a resource (menu, product, user, etc.),
  the system checks if the org's active subscription plan allows it.
- Plan.limits JSON has keys like 'max_menus', 'max_products', etc.
- Plan.feature_flags JSON has keys like 'ai_content_generation', etc.
- If the org has no active subscription, it's treated as FREE tier.

Usage:
    from shared.permissions.plan_enforcement import (
        PlanEnforcementService,
        RequiresPlanFeature,
        CheckPlanLimit,
        PlanEnforcementMixin,
    )

    # In a ViewSet:
    class MenuViewSet(PlanEnforcementMixin, BaseModelViewSet):
        plan_limit_key = 'max_menus'
        plan_limit_model = Menu
        plan_limit_filter = {'deleted_at__isnull': True}

    # Feature gate:
    class AIContentView(APIView):
        permission_classes = [IsAuthenticated, RequiresPlanFeature('ai_content_generation')]

    # Programmatic check:
    service = PlanEnforcementService()
    can_create, remaining = service.check_limit(org, 'max_menus')
    if not can_create:
        raise PlanLimitExceeded('max_menus')
"""

import logging
from typing import Optional, Tuple

from django.utils.translation import gettext_lazy as _
from rest_framework import permissions, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.request import Request
from rest_framework.views import APIView

logger = logging.getLogger(__name__)


# =============================================================================
# EXCEPTIONS
# =============================================================================

class PlanLimitExceeded(PermissionDenied):
    """Raised when an organization exceeds their plan limit."""
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = _('Plan limit exceeded. Please upgrade your subscription.')
    default_code = 'plan_limit_exceeded'

    def __init__(self, limit_key: str = None, current: int = 0, limit: int = 0, **kwargs):
        detail = self.default_detail
        if limit_key:
            label = limit_key.replace('max_', '').replace('_', ' ').title()
            detail = _(
                'You have reached the %(label)s limit for your plan '
                '(%(current)d/%(limit)d). Please upgrade to add more.'
            ) % {'label': label, 'current': current, 'limit': limit}
        super().__init__(detail=detail, **kwargs)
        self.limit_key = limit_key
        self.current = current
        self.limit = limit


class FeatureNotAvailable(PermissionDenied):
    """Raised when a feature is not available on the org's plan."""
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = _('This feature is not available on your current plan.')
    default_code = 'feature_not_available'

    def __init__(self, feature_code: str = None, **kwargs):
        detail = self.default_detail
        if feature_code:
            label = feature_code.replace('_', ' ').title()
            detail = _(
                '%(label)s is not available on your current plan. '
                'Please upgrade to access this feature.'
            ) % {'label': label}
        super().__init__(detail=detail, **kwargs)
        self.feature_code = feature_code


# =============================================================================
# PLAN ENFORCEMENT SERVICE
# =============================================================================

class PlanEnforcementService:
    """
    Core service for plan limit checking and feature gating.

    Provides methods to:
    - Get the active plan for an organization
    - Check if a limit would be exceeded
    - Check if a feature is available
    - Get usage summary

    The service is stateless and can be used anywhere in the codebase.
    """

    @staticmethod
    def get_active_subscription(organization):
        """
        Get the active subscription for an organization.

        Returns the first ACTIVE or TRIALING subscription, or None.
        """
        from apps.subscriptions.models import Subscription
        from apps.subscriptions.choices import SubscriptionStatus

        return Subscription.objects.filter(
            organization=organization,
            status__in=[SubscriptionStatus.ACTIVE, SubscriptionStatus.TRIALING],
            deleted_at__isnull=True,
        ).select_related('plan').first()

    @staticmethod
    def get_active_plan(organization):
        """
        Get the active plan for an organization.

        Returns the plan from the active subscription, or the default FREE plan.
        """
        from apps.subscriptions.models import Plan
        from apps.subscriptions.choices import PlanTier

        subscription = PlanEnforcementService.get_active_subscription(organization)
        if subscription:
            return subscription.plan

        # No active subscription → return default plan (FREE)
        return Plan.objects.filter(
            is_default=True,
            is_active=True,
            deleted_at__isnull=True,
        ).first() or Plan.objects.filter(
            tier=PlanTier.FREE,
            is_active=True,
            deleted_at__isnull=True,
        ).first()

    @staticmethod
    def check_limit(organization, limit_key: str, model_class=None,
                     extra_filter: dict = None) -> Tuple[bool, int, int]:
        """
        Check if an organization can create another resource.

        Args:
            organization: The Organization instance
            limit_key: The limit key (e.g., 'max_menus', 'max_products')
            model_class: Django model class to count current resources
            extra_filter: Additional filter kwargs for counting

        Returns:
            Tuple of (can_create: bool, current_count: int, limit: int)
            limit of -1 means unlimited
        """
        plan = PlanEnforcementService.get_active_plan(organization)
        if not plan:
            # No plan at all - use minimum defaults
            return False, 0, 0

        limit = plan.get_limit(limit_key, 0)

        # Unlimited
        if limit == -1:
            return True, 0, -1

        # Count current resources
        current_count = 0
        if model_class:
            filter_kwargs = {
                'deleted_at__isnull': True,
            }
            # Determine org field name
            if hasattr(model_class, 'organization_id'):
                filter_kwargs['organization'] = organization
            elif hasattr(model_class, 'category'):
                # Products are linked via category → menu → organization
                filter_kwargs['category__menu__organization'] = organization
            elif hasattr(model_class, 'menu'):
                # Categories are linked via menu → organization
                filter_kwargs['menu__organization'] = organization

            if extra_filter:
                filter_kwargs.update(extra_filter)

            current_count = model_class.objects.filter(**filter_kwargs).count()

        can_create = current_count < limit
        return can_create, current_count, limit

    @staticmethod
    def check_feature(organization, feature_code: str) -> bool:
        """
        Check if a feature is available on the org's plan.

        Args:
            organization: The Organization instance
            feature_code: The feature flag key (e.g., 'ai_content_generation')

        Returns:
            True if the feature is available
        """
        plan = PlanEnforcementService.get_active_plan(organization)
        if not plan:
            return False
        return plan.get_feature_flag(feature_code, False)

    @staticmethod
    def get_plan_usage_summary(organization) -> dict:
        """
        Get a summary of plan limits vs current usage.

        Returns dict with each limit key and its status.
        """
        from apps.menu.models import Menu, Category, Product
        from apps.core.models import User, UserRole
        from apps.orders.models import QRCode

        plan = PlanEnforcementService.get_active_plan(organization)
        if not plan:
            return {}

        limits = plan.limits or {}

        # Model mappings for counting
        model_mapping = {
            'max_menus': (Menu, {'organization': organization, 'deleted_at__isnull': True}),
            'max_products': (Product, {'category__menu__organization': organization, 'deleted_at__isnull': True}),
            'max_categories': (Category, {'menu__organization': organization, 'deleted_at__isnull': True}),
            'max_qr_codes': (QRCode, {'organization': organization, 'deleted_at__isnull': True}),
            'max_users': (UserRole, {'organization': organization, 'deleted_at__isnull': True}),
        }

        summary = {}
        for key, limit_value in limits.items():
            current = 0
            if key in model_mapping:
                model_cls, filter_kwargs = model_mapping[key]
                try:
                    current = model_cls.objects.filter(**filter_kwargs).count()
                except Exception:
                    current = 0

            if limit_value == -1:
                percentage = 0
                status_text = 'unlimited'
            elif limit_value > 0:
                percentage = min(100, (current / limit_value) * 100)
                status_text = 'ok' if percentage < 90 else 'warning' if percentage < 100 else 'exceeded'
            else:
                percentage = 0
                status_text = 'no_limit'

            summary[key] = {
                'current': current,
                'limit': limit_value,
                'percentage': round(percentage, 1),
                'status': status_text,
            }

        return summary

    @staticmethod
    def enforce_limit(organization, limit_key: str, model_class=None,
                       extra_filter: dict = None) -> None:
        """
        Enforce a plan limit — raise PlanLimitExceeded if exceeded.

        Use this in create() methods to block resource creation.
        """
        can_create, current, limit = PlanEnforcementService.check_limit(
            organization, limit_key, model_class, extra_filter
        )
        if not can_create:
            logger.warning(
                "Plan limit exceeded: org=%s, key=%s, current=%d, limit=%d",
                organization.name, limit_key, current, limit,
            )
            raise PlanLimitExceeded(
                limit_key=limit_key,
                current=current,
                limit=limit,
            )

    @staticmethod
    def enforce_feature(organization, feature_code: str) -> None:
        """
        Enforce a feature gate — raise FeatureNotAvailable if not enabled.

        Use this in views/services to block access to gated features.
        """
        if not PlanEnforcementService.check_feature(organization, feature_code):
            logger.warning(
                "Feature not available: org=%s, feature=%s",
                organization.name, feature_code,
            )
            raise FeatureNotAvailable(feature_code=feature_code)


# =============================================================================
# DRF PERMISSION CLASSES
# =============================================================================

class RequiresPlanFeature(permissions.BasePermission):
    """
    DRF permission class that checks if a feature is available on the org's plan.

    Usage:
        class AIContentViewSet(viewsets.ViewSet):
            permission_classes = [IsAuthenticated, RequiresPlanFeature('ai_content_generation')]
    """

    def __init__(self, feature_code: str):
        self.feature_code = feature_code

    def has_permission(self, request: Request, view: APIView) -> bool:
        if not request.user or not request.user.is_authenticated:
            return False

        # Superusers bypass plan checks
        if request.user.is_superuser:
            return True

        organization = getattr(request, 'organization', None)
        if not organization:
            return False

        available = PlanEnforcementService.check_feature(organization, self.feature_code)
        if not available:
            self.message = _(
                'The feature "%(feature)s" is not available on your current plan.'
            ) % {'feature': self.feature_code.replace('_', ' ').title()}
        return available


def requires_plan_feature(feature_code: str):
    """
    Factory function for RequiresPlanFeature.

    Usage:
        class AIView(APIView):
            permission_classes = [IsAuthenticated, requires_plan_feature('ai_content_generation')]
    """
    class DynamicFeaturePermission(RequiresPlanFeature):
        def __init__(self):
            super().__init__(feature_code)
    DynamicFeaturePermission.__name__ = f'RequiresFeature_{feature_code}'
    return DynamicFeaturePermission


class CheckPlanLimit(permissions.BasePermission):
    """
    DRF permission class that checks plan limits on create actions.

    Only blocks 'create' action, allows all other actions through.

    Usage in ViewSet:
        permission_classes = [IsAuthenticated, CheckPlanLimit]
        plan_limit_key = 'max_menus'
        plan_limit_model = Menu
    """

    def has_permission(self, request: Request, view: APIView) -> bool:
        if not request.user or not request.user.is_authenticated:
            return False

        if request.user.is_superuser:
            return True

        # Only check on create action
        action = getattr(view, 'action', None)
        if action != 'create':
            return True

        organization = getattr(request, 'organization', None)
        if not organization:
            return True  # No org context, let other permissions handle

        limit_key = getattr(view, 'plan_limit_key', None)
        model_class = getattr(view, 'plan_limit_model', None)
        extra_filter = getattr(view, 'plan_limit_filter', None)

        if not limit_key:
            return True  # No limit configured

        can_create, current, limit = PlanEnforcementService.check_limit(
            organization, limit_key, model_class, extra_filter
        )

        if not can_create:
            label = limit_key.replace('max_', '').replace('_', ' ').title()
            self.message = _(
                'You have reached the %(label)s limit (%(current)d/%(limit)d) '
                'for your plan. Please upgrade to create more.'
            ) % {'label': label, 'current': current, 'limit': limit}
            return False

        return True


# =============================================================================
# VIEWSET MIXIN
# =============================================================================

class PlanEnforcementMixin:
    """
    Mixin for DRF ViewSets that enforces plan limits on create.

    Add to any ViewSet that creates resources which should be plan-limited.

    Attributes:
        plan_limit_key: The limit key from Plan.limits (e.g., 'max_menus')
        plan_limit_model: The model class to count for limits
        plan_limit_filter: Extra filters for counting (default: {'deleted_at__isnull': True})

    Usage:
        class MenuViewSet(PlanEnforcementMixin, BaseModelViewSet):
            plan_limit_key = 'max_menus'
            plan_limit_model = Menu

        class ProductViewSet(PlanEnforcementMixin, BaseModelViewSet):
            plan_limit_key = 'max_products'
            plan_limit_model = Product
    """

    plan_limit_key: str = None
    plan_limit_model = None
    plan_limit_filter: dict = None

    def perform_create(self, serializer):
        """
        Override perform_create to check plan limits before saving.
        """
        if self.plan_limit_key:
            organization = getattr(self.request, 'organization', None)
            if organization and not self.request.user.is_superuser:
                PlanEnforcementService.enforce_limit(
                    organization=organization,
                    limit_key=self.plan_limit_key,
                    model_class=self.plan_limit_model,
                    extra_filter=self.plan_limit_filter,
                )
        super().perform_create(serializer)


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    'PlanEnforcementService',
    'PlanLimitExceeded',
    'FeatureNotAvailable',
    'RequiresPlanFeature',
    'requires_plan_feature',
    'CheckPlanLimit',
    'PlanEnforcementMixin',
]
