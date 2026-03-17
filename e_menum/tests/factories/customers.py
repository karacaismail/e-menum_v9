"""
Factory Boy factories for customers application models.

Factories: CustomerFactory, FeedbackFactory
"""

import uuid
from decimal import Decimal

import factory
from factory.django import DjangoModelFactory

from tests.factories.core import OrganizationFactory


class CustomerFactory(DjangoModelFactory):
    """
    Factory for creating Customer instances.

    Examples:
        customer = CustomerFactory()
        customer = CustomerFactory(name="Ali Veli", total_orders=5)
    """

    class Meta:
        model = "customers.Customer"
        skip_postgeneration_save = True

    organization = factory.SubFactory(OrganizationFactory)
    name = factory.LazyAttribute(lambda o: f"Customer {uuid.uuid4().hex[:6]}")
    email = factory.LazyAttribute(
        lambda o: f"customer-{uuid.uuid4().hex[:8]}@example.com"
    )
    phone = factory.LazyAttribute(lambda o: f"+90555{uuid.uuid4().int % 10000000:07d}")
    source = "QR_SCAN"
    language_preference = "tr"
    total_orders = 0
    total_spent = Decimal("0.00")
    loyalty_points_balance = 0
    marketing_consent = False
    settings = factory.LazyFunction(dict)


class LoyalCustomerFactory(CustomerFactory):
    """Factory for loyal customers with orders and points."""

    total_orders = 25
    total_spent = Decimal("2500.00")
    loyalty_points_balance = 500
    marketing_consent = True


class FeedbackFactory(DjangoModelFactory):
    """
    Factory for creating Feedback instances.

    Examples:
        feedback = FeedbackFactory()
        feedback = FeedbackFactory(rating=5, feedback_type="COMPLIMENT")
    """

    class Meta:
        model = "customers.Feedback"
        skip_postgeneration_save = True

    organization = factory.LazyAttribute(lambda o: o.customer.organization)
    customer = factory.SubFactory(CustomerFactory)
    feedback_type = "REVIEW"
    status = "PENDING"
    rating = 4
    comment = "Good food and service."
    source = "QR_SCAN"
    is_public = False
