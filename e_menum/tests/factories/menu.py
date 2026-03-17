"""
Factory Boy factories for menu application models.

Factories: MenuFactory, CategoryFactory, ProductFactory
"""

import uuid
from decimal import Decimal

import factory
from factory.django import DjangoModelFactory


class MenuFactory(DjangoModelFactory):
    """Factory for creating Menu instances."""

    class Meta:
        model = "menu.Menu"
        skip_postgeneration_save = True

    organization = factory.SubFactory("tests.factories.core.OrganizationFactory")
    name = factory.LazyAttribute(lambda o: f"Test Menu {uuid.uuid4().hex[:6]}")
    slug = factory.LazyAttribute(lambda o: f"test-menu-{uuid.uuid4().hex[:6]}")
    is_published = True
    is_default = False
    sort_order = 0
    settings = factory.LazyFunction(dict)


class CategoryFactory(DjangoModelFactory):
    """Factory for creating Category instances."""

    class Meta:
        model = "menu.Category"
        skip_postgeneration_save = True

    organization = factory.LazyAttribute(lambda o: o.menu.organization)
    menu = factory.SubFactory(MenuFactory)
    name = factory.LazyAttribute(lambda o: f"Test Category {uuid.uuid4().hex[:6]}")
    slug = factory.LazyAttribute(lambda o: f"test-cat-{uuid.uuid4().hex[:6]}")
    is_active = True
    sort_order = 0


class ProductFactory(DjangoModelFactory):
    """Factory for creating Product instances."""

    class Meta:
        model = "menu.Product"
        skip_postgeneration_save = True

    organization = factory.LazyAttribute(lambda o: o.category.organization)
    category = factory.SubFactory(CategoryFactory)
    name = factory.LazyAttribute(lambda o: f"Test Product {uuid.uuid4().hex[:6]}")
    slug = factory.LazyAttribute(lambda o: f"test-prod-{uuid.uuid4().hex[:6]}")
    base_price = factory.LazyFunction(lambda: Decimal("29.90"))
    currency = "TRY"
    is_active = True
    is_available = True
    sort_order = 0
