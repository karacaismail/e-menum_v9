"""
Factory Boy factories for subscriptions application models.

Factories: PlanFactory, SubscriptionFactory, FeatureFactory
"""

import uuid
from decimal import Decimal

import factory
from django.utils import timezone
from factory.django import DjangoModelFactory

from tests.factories.core import OrganizationFactory


class PlanFactory(DjangoModelFactory):
    """
    Factory for creating Plan instances (platform-level, no org FK).

    Examples:
        plan = PlanFactory()
        plan = PlanFactory(tier="PROFESSIONAL", price_monthly=Decimal("199.00"))
    """

    class Meta:
        model = "subscriptions.Plan"
        skip_postgeneration_save = True

    name = factory.LazyAttribute(lambda o: f"Test Plan {uuid.uuid4().hex[:6]}")
    slug = factory.LazyAttribute(lambda o: f"test-plan-{uuid.uuid4().hex[:6]}")
    tier = "STARTER"
    price_monthly = Decimal("99.00")
    price_yearly = Decimal("990.00")
    currency = "TRY"
    trial_days = 14
    is_active = True
    is_default = False
    is_public = True
    sort_order = 0
    limits = factory.LazyFunction(dict)
    feature_flags = factory.LazyFunction(dict)
    metadata = factory.LazyFunction(dict)


class FreePlanFactory(PlanFactory):
    """Factory for free tier plans."""

    tier = "FREE"
    price_monthly = Decimal("0.00")
    price_yearly = Decimal("0.00")
    trial_days = 0


class EnterprisePlanFactory(PlanFactory):
    """Factory for enterprise plans."""

    tier = "ENTERPRISE"
    price_monthly = Decimal("999.00")
    price_yearly = Decimal("9990.00")
    is_public = False
    is_custom = True


class FeatureFactory(DjangoModelFactory):
    """Factory for creating Feature instances (platform-level)."""

    class Meta:
        model = "subscriptions.Feature"
        skip_postgeneration_save = True

    code = factory.LazyAttribute(lambda o: f"feature-{uuid.uuid4().hex[:8]}")
    name = factory.LazyAttribute(lambda o: f"Test Feature {uuid.uuid4().hex[:6]}")
    feature_type = "BOOLEAN"
    category = "GENERAL"
    is_active = True
    sort_order = 0
    default_value = factory.LazyFunction(dict)
    metadata = factory.LazyFunction(dict)


class SubscriptionFactory(DjangoModelFactory):
    """
    Factory for creating Subscription instances.

    Examples:
        sub = SubscriptionFactory()
        sub = SubscriptionFactory(status="TRIALING", plan=FreePlanFactory())
    """

    class Meta:
        model = "subscriptions.Subscription"
        skip_postgeneration_save = True

    organization = factory.SubFactory(OrganizationFactory)
    plan = factory.SubFactory(PlanFactory)
    status = "ACTIVE"
    billing_period = "MONTHLY"
    payment_method = "CREDIT_CARD"
    current_price = Decimal("99.00")
    currency = "TRY"

    @factory.lazy_attribute
    def current_period_start(self):
        return timezone.now()

    @factory.lazy_attribute
    def current_period_end(self):
        from datetime import timedelta

        return timezone.now() + timedelta(days=30)


class TrialSubscriptionFactory(SubscriptionFactory):
    """Factory for trial subscriptions."""

    status = "TRIALING"
    current_price = Decimal("0.00")

    @factory.lazy_attribute
    def trial_ends_at(self):
        from datetime import timedelta

        return timezone.now() + timedelta(days=14)
