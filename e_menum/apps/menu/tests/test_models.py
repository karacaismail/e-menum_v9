"""Tests for Menu app models."""

import uuid
from decimal import Decimal

import pytest

from apps.menu.models import Category, Menu, Product, Theme


@pytest.mark.django_db
class TestMenuModel:
    """Tests for the Menu model."""

    def test_create_menu(self, organization):
        menu = Menu.objects.create(
            organization=organization,
            name="Lunch Menu",
            slug=f"lunch-{uuid.uuid4().hex[:6]}",
        )
        assert menu.name == "Lunch Menu"
        assert menu.organization == organization
        assert menu.is_published is False
        assert menu.is_default is False
        assert menu.deleted_at is None

    def test_menu_str(self, menu):
        assert menu.name in str(menu)

    def test_menu_soft_delete(self, menu):
        menu.soft_delete()
        assert menu.deleted_at is not None
        assert Menu.objects.filter(id=menu.id, deleted_at__isnull=True).count() == 0

    def test_menu_org_scoped(self, organization, make_organization):
        org2 = make_organization(name="Other Org")
        Menu.objects.create(organization=organization, name="Menu 1", slug="m1")
        Menu.objects.create(organization=org2, name="Menu 2", slug="m2")
        assert (
            Menu.objects.filter(
                organization=organization, deleted_at__isnull=True
            ).count()
            == 1
        )
        assert (
            Menu.objects.filter(organization=org2, deleted_at__isnull=True).count() == 1
        )

    def test_menu_publish_toggle(self, menu):
        assert menu.is_published is True  # fixture sets True
        menu.is_published = False
        menu.save()
        menu.refresh_from_db()
        assert menu.is_published is False

    def test_menu_default_toggle(self, menu):
        menu.is_default = True
        menu.save()
        menu.refresh_from_db()
        assert menu.is_default is True


@pytest.mark.django_db
class TestCategoryModel:
    """Tests for the Category model."""

    def test_create_category(self, organization, menu):
        cat = Category.objects.create(
            organization=organization,
            menu=menu,
            name="Appetizers",
            slug=f"appetizers-{uuid.uuid4().hex[:6]}",
        )
        assert cat.name == "Appetizers"
        assert cat.menu == menu
        assert cat.organization == organization

    def test_category_with_parent(self, organization, menu):
        parent = Category.objects.create(
            organization=organization,
            menu=menu,
            name="Drinks",
            slug=f"drinks-{uuid.uuid4().hex[:6]}",
        )
        child = Category.objects.create(
            organization=organization,
            menu=menu,
            name="Hot Drinks",
            slug=f"hot-drinks-{uuid.uuid4().hex[:6]}",
            parent=parent,
        )
        assert child.parent == parent

    def test_category_soft_delete(self, category):
        category.soft_delete()
        assert category.deleted_at is not None

    def test_category_sort_order(self, organization, menu):
        Category.objects.create(
            organization=organization,
            menu=menu,
            name="B",
            slug="b",
            sort_order=2,
        )
        Category.objects.create(
            organization=organization,
            menu=menu,
            name="A",
            slug="a",
            sort_order=1,
        )
        cats = list(
            Category.objects.filter(
                organization=organization,
                menu=menu,
                deleted_at__isnull=True,
            ).order_by("sort_order")[:2]
        )
        assert cats[0].sort_order <= cats[1].sort_order


@pytest.mark.django_db
class TestProductModel:
    """Tests for the Product model."""

    def test_create_product(self, organization, category):
        product = Product.objects.create(
            organization=organization,
            category=category,
            name="Caesar Salad",
            slug=f"caesar-{uuid.uuid4().hex[:6]}",
            base_price=Decimal("45.00"),
            currency="TRY",
        )
        assert product.name == "Caesar Salad"
        assert product.base_price == Decimal("45.00")
        assert product.is_active is True

    def test_product_soft_delete(self, product):
        product.soft_delete()
        assert product.deleted_at is not None

    def test_product_price_zero(self, organization, category):
        product = Product.objects.create(
            organization=organization,
            category=category,
            name="Free Water",
            slug="free-water",
            base_price=Decimal("0.00"),
            currency="TRY",
        )
        assert product.base_price == Decimal("0.00")


@pytest.mark.django_db
class TestThemeModel:
    """Tests for the Theme model."""

    def test_create_theme(self, organization):
        theme = Theme.objects.create(
            organization=organization,
            name="Dark Theme",
            slug=f"dark-{uuid.uuid4().hex[:6]}",
            primary_color="#1A6B5A",
            secondary_color="#22c55e",
            background_color="#0F1923",
            text_color="#ffffff",
        )
        assert theme.name == "Dark Theme"
        assert theme.primary_color == "#1A6B5A"

    def test_theme_soft_delete(self, organization):
        theme = Theme.objects.create(
            organization=organization,
            name="Temp Theme",
            slug="temp",
        )
        theme.soft_delete()
        assert theme.deleted_at is not None
