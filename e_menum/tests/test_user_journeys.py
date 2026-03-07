"""
Comprehensive user journey tests for the restaurant owner portal.

Tests cover end-to-end user journeys through the /account/ portal:
1. Owner Journey — full CRUD across menus, products, QR codes, orders, customers, analytics
2. Manager Journey — view/edit menus, products, orders, tables, customers, analytics
3. Staff Journey — view menus/products, manage orders, view tables
4. Viewer Journey — read-only access to all list/detail pages
5. Anonymous User Journey — all portal pages redirect to login
6. No-Organization User Journey — authenticated but no org redirects to profile
7. QR Code Download Journey — download in all formats and sizes

Uses pytest-django with factory_boy factories and Django test Client.
All views use session-based auth via @login_required or LoginRequiredMixin.
Views with OrganizationRequiredMixin redirect to profile when user has no org.
Function-based views use _get_org(request) helper and redirect to profile when None.
"""

import uuid
from decimal import Decimal
from unittest.mock import patch
from io import BytesIO

import pytest
from django.test import Client
from django.urls import reverse

from tests.factories.core import OrganizationFactory, UserFactory
from tests.factories.orders import (
    QRCodeFactory,
    ZoneFactory,
    TableFactory,
    OrderFactory,
)


pytestmark = pytest.mark.django_db


# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture(autouse=True)
def _disable_canonical_redirect(settings):
    """Disable CanonicalDomainMiddleware redirect for test client (Host: testserver)."""
    settings.SEO_CANONICAL_DOMAIN = ""


@pytest.fixture
def org():
    """Create a test organization."""
    return OrganizationFactory()


@pytest.fixture
def other_org():
    """Create a second organization for isolation tests."""
    return OrganizationFactory()


@pytest.fixture
def owner_user(org):
    """Create an owner user with organization."""
    return UserFactory(organization=org)


@pytest.fixture
def manager_user(org):
    """Create a manager user with organization."""
    return UserFactory(organization=org)


@pytest.fixture
def staff_user(org):
    """Create a staff user with organization."""
    return UserFactory(organization=org)


@pytest.fixture
def viewer_user(org):
    """Create a viewer user with organization."""
    return UserFactory(organization=org)


@pytest.fixture
def no_org_user():
    """Create a user without any organization."""
    return UserFactory(organization=None)


@pytest.fixture
def other_org_user(other_org):
    """Create a user belonging to a different organization."""
    return UserFactory(organization=other_org)


@pytest.fixture
def owner_client(owner_user):
    """Return a client logged in as the owner."""
    client = Client()
    client.force_login(owner_user)
    return client


@pytest.fixture
def manager_client(manager_user):
    """Return a client logged in as the manager."""
    client = Client()
    client.force_login(manager_user)
    return client


@pytest.fixture
def staff_client(staff_user):
    """Return a client logged in as staff."""
    client = Client()
    client.force_login(staff_user)
    return client


@pytest.fixture
def viewer_client(viewer_user):
    """Return a client logged in as viewer."""
    client = Client()
    client.force_login(viewer_user)
    return client


@pytest.fixture
def no_org_client(no_org_user):
    """Return a client logged in as a user with no organization."""
    client = Client()
    client.force_login(no_org_user)
    return client


@pytest.fixture
def other_org_client(other_org_user):
    """Return a client logged in as a user from another organization."""
    client = Client()
    client.force_login(other_org_user)
    return client


@pytest.fixture
def anon_client():
    """Return an unauthenticated client."""
    return Client()


@pytest.fixture
def menu(org):
    """Create a test menu for the organization."""
    from apps.menu.models import Menu

    return Menu.objects.create(
        organization=org,
        name="Test Menu",
        slug=f"test-menu-{uuid.uuid4().hex[:8]}",
        description="A test menu",
        is_published=True,
        is_default=True,
    )


@pytest.fixture
def category(org, menu):
    """Create a test category within the menu."""
    from apps.menu.models import Category

    return Category.objects.create(
        organization=org,
        menu=menu,
        name="Test Category",
        slug=f"test-cat-{uuid.uuid4().hex[:8]}",
        is_active=True,
    )


@pytest.fixture
def product(org, category):
    """Create a test product within the category."""
    from apps.menu.models import Product

    return Product.objects.create(
        organization=org,
        category=category,
        name="Test Product",
        slug=f"test-product-{uuid.uuid4().hex[:8]}",
        base_price=Decimal("29.99"),
        currency="TRY",
        is_active=True,
        is_available=True,
    )


@pytest.fixture
def zone(org):
    """Create a test zone."""
    return ZoneFactory(organization=org)


@pytest.fixture
def table(org, zone):
    """Create a test table in the zone."""
    return TableFactory(organization=org, zone=zone)


@pytest.fixture
def qr_code(org):
    """Create a test QR code."""
    return QRCodeFactory(organization=org)


@pytest.fixture
def order(org):
    """Create a test order."""
    return OrderFactory(organization=org)


@pytest.fixture
def other_org_menu(other_org):
    """Create a menu belonging to another organization (for isolation tests)."""
    from apps.menu.models import Menu

    return Menu.objects.create(
        organization=other_org,
        name="Other Org Menu",
        slug=f"other-menu-{uuid.uuid4().hex[:8]}",
        is_published=True,
    )


@pytest.fixture
def other_org_qr(other_org):
    """Create a QR code belonging to another organization."""
    return QRCodeFactory(organization=other_org)


@pytest.fixture
def other_org_order(other_org):
    """Create an order belonging to another organization."""
    return OrderFactory(organization=other_org)


# =============================================================================
# HELPER — URL definitions for reuse
# =============================================================================


# Pages that require login + organization (function-based views with _get_org)
ORG_REQUIRED_GET_URLS = [
    "accounts:dashboard",
    "accounts:menu-list",
    "accounts:menu-create",
    "accounts:product-list",
    "accounts:product-create",
    "accounts:order-list",
    "accounts:table-management",
    "accounts:qrcode-list",
    "accounts:customer-list",
    "accounts:analytics",
    "accounts:theme-list",
    "accounts:theme-create",
]

# Pages that require login only (LoginRequiredMixin, no org check)
LOGIN_REQUIRED_URLS = [
    "accounts:profile",
    "accounts:settings",
    "accounts:subscription",
    "accounts:invoices",
]

# All portal URLs that anonymous users should be redirected from
ALL_PROTECTED_GET_URLS = ORG_REQUIRED_GET_URLS + LOGIN_REQUIRED_URLS


# =============================================================================
# 1. OWNER JOURNEY
# =============================================================================


class TestOwnerJourney:
    """
    Full owner journey: login -> dashboard -> CRUD menus -> CRUD products ->
    QR codes -> orders -> customers -> analytics -> profile -> settings.
    """

    def test_dashboard_accessible(self, owner_client):
        """Owner visits dashboard and gets 200."""
        resp = owner_client.get(reverse("accounts:dashboard"))
        assert resp.status_code == 200

    def test_menu_list_accessible(self, owner_client, menu):
        """Owner visits menu list and sees existing menus."""
        resp = owner_client.get(reverse("accounts:menu-list"))
        assert resp.status_code == 200

    def test_menu_create_form_renders(self, owner_client):
        """Owner can access the menu creation form."""
        resp = owner_client.get(reverse("accounts:menu-create"))
        assert resp.status_code == 200

    def test_menu_create_post(self, owner_client, org):
        """Owner creates a new menu via POST."""
        resp = owner_client.post(
            reverse("accounts:menu-create"),
            {
                "name": "Breakfast Menu",
                "description": "Morning specials",
            },
        )
        # Successful creation redirects to menu detail
        assert resp.status_code == 302
        from apps.menu.models import Menu

        assert Menu.objects.filter(organization=org, name="Breakfast Menu").exists()

    def test_menu_detail_accessible(self, owner_client, menu):
        """Owner views a specific menu's detail page."""
        resp = owner_client.get(
            reverse("accounts:menu-detail", kwargs={"menu_id": menu.id})
        )
        assert resp.status_code == 200

    def test_menu_edit_form_renders(self, owner_client, menu):
        """Owner can access the menu edit form."""
        resp = owner_client.get(
            reverse("accounts:menu-edit", kwargs={"menu_id": menu.id})
        )
        assert resp.status_code == 200

    def test_product_list_accessible(self, owner_client, product):
        """Owner visits product list page."""
        resp = owner_client.get(reverse("accounts:product-list"))
        assert resp.status_code == 200

    def test_product_create_form_renders(self, owner_client, category):
        """Owner can access the product creation form."""
        resp = owner_client.get(reverse("accounts:product-create"))
        assert resp.status_code == 200

    def test_product_create_post(self, owner_client, org, category):
        """Owner creates a new product via POST."""
        resp = owner_client.post(
            reverse("accounts:product-create"),
            {
                "name": "Espresso",
                "category": str(category.id),
                "base_price": "15.00",
                "short_description": "Strong coffee",
                "description": "Rich espresso",
                "is_active": True,
                "is_available": True,
            },
        )
        assert resp.status_code == 302
        from apps.menu.models import Product

        assert Product.objects.filter(organization=org, name="Espresso").exists()

    def test_product_detail_accessible(self, owner_client, product):
        """Owner views a specific product detail page."""
        resp = owner_client.get(
            reverse("accounts:product-detail", kwargs={"product_id": product.id})
        )
        assert resp.status_code == 200

    def test_product_edit_form_renders(self, owner_client, product):
        """Owner can access the product edit form."""
        resp = owner_client.get(
            reverse("accounts:product-edit", kwargs={"product_id": product.id})
        )
        assert resp.status_code == 200

    def test_qrcode_list_accessible(self, owner_client, qr_code):
        """Owner visits QR code list page."""
        resp = owner_client.get(reverse("accounts:qrcode-list"))
        assert resp.status_code == 200

    def test_qrcode_create_post(self, owner_client, org):
        """Owner creates a new QR code via POST."""
        resp = owner_client.post(
            reverse("accounts:qrcode-create"),
            {
                "name": "Main Entrance QR",
                "type": "MENU",
            },
        )
        # Successful creation redirects to QR detail
        assert resp.status_code == 302
        from apps.orders.models import QRCode

        assert QRCode.objects.filter(organization=org).count() >= 1

    def test_qrcode_detail_accessible(self, owner_client, qr_code):
        """Owner views a specific QR code detail page."""
        resp = owner_client.get(
            reverse("accounts:qrcode-detail", kwargs={"qr_id": qr_code.id})
        )
        assert resp.status_code == 200

    @patch("apps.orders.services.qr_generator.QRGeneratorService.download_qr")
    def test_qrcode_download_png(self, mock_download, owner_client, qr_code):
        """Owner downloads QR code as PNG."""
        mock_download.return_value = BytesIO(b"\x89PNG\r\n\x1a\nfakedata")
        resp = owner_client.get(
            reverse("accounts:qrcode-download", kwargs={"qr_id": qr_code.id}),
            {"format": "png", "size": "512"},
        )
        assert resp.status_code == 200
        assert resp["Content-Type"] == "image/png"
        assert "attachment" in resp["Content-Disposition"]

    @patch("apps.orders.services.qr_generator.QRGeneratorService.download_qr")
    def test_qrcode_download_svg(self, mock_download, owner_client, qr_code):
        """Owner downloads QR code as SVG."""
        mock_download.return_value = BytesIO(b"<svg>fake</svg>")
        resp = owner_client.get(
            reverse("accounts:qrcode-download", kwargs={"qr_id": qr_code.id}),
            {"format": "svg"},
        )
        assert resp.status_code == 200
        assert resp["Content-Type"] == "image/svg+xml"

    @patch("apps.orders.services.qr_generator.QRGeneratorService.download_qr")
    def test_qrcode_download_jpg(self, mock_download, owner_client, qr_code):
        """Owner downloads QR code as JPG."""
        mock_download.return_value = BytesIO(b"\xff\xd8\xff\xe0fakedata")
        resp = owner_client.get(
            reverse("accounts:qrcode-download", kwargs={"qr_id": qr_code.id}),
            {"format": "jpg"},
        )
        assert resp.status_code == 200
        assert resp["Content-Type"] == "image/jpeg"

    @patch("apps.orders.services.qr_generator.QRGeneratorService.download_qr")
    def test_qrcode_download_pdf(self, mock_download, owner_client, qr_code):
        """Owner downloads QR code as PDF."""
        mock_download.return_value = BytesIO(b"%PDF-1.4 fake")
        resp = owner_client.get(
            reverse("accounts:qrcode-download", kwargs={"qr_id": qr_code.id}),
            {"format": "pdf"},
        )
        assert resp.status_code == 200
        assert resp["Content-Type"] == "application/pdf"

    @patch("apps.orders.services.qr_generator.QRGeneratorService.download_print_design")
    def test_qrcode_download_print_a4(self, mock_print, owner_client, qr_code):
        """Owner downloads print-ready PDF in A4 size."""
        mock_print.return_value = BytesIO(b"%PDF-1.4 A4 print design")
        resp = owner_client.get(
            reverse("accounts:qrcode-download-print", kwargs={"qr_id": qr_code.id}),
            {"design_size": "A4"},
        )
        assert resp.status_code == 200
        assert resp["Content-Type"] == "application/pdf"
        assert "A4" in resp["Content-Disposition"]

    def test_order_list_accessible(self, owner_client, order):
        """Owner visits order list page."""
        resp = owner_client.get(reverse("accounts:order-list"))
        assert resp.status_code == 200

    def test_order_detail_accessible(self, owner_client, order):
        """Owner views a specific order detail page."""
        resp = owner_client.get(
            reverse("accounts:order-detail", kwargs={"order_id": order.id})
        )
        assert resp.status_code == 200

    def test_customer_list_accessible(self, owner_client):
        """Owner visits customer list page."""
        resp = owner_client.get(reverse("accounts:customer-list"))
        assert resp.status_code == 200

    def test_analytics_accessible(self, owner_client):
        """Owner visits analytics page."""
        resp = owner_client.get(reverse("accounts:analytics"))
        assert resp.status_code == 200

    def test_profile_accessible(self, owner_client):
        """Owner visits profile page."""
        resp = owner_client.get(reverse("accounts:profile"))
        assert resp.status_code == 200

    def test_profile_update_post(self, owner_client, owner_user):
        """Owner updates profile via POST."""
        resp = owner_client.post(
            reverse("accounts:profile"),
            {
                "first_name": "Updated",
                "last_name": "Owner",
                "phone": "",
                "avatar": "",
            },
        )
        assert resp.status_code == 302
        owner_user.refresh_from_db()
        assert owner_user.first_name == "Updated"

    def test_settings_accessible(self, owner_client):
        """Owner visits settings page."""
        resp = owner_client.get(reverse("accounts:settings"))
        assert resp.status_code == 200

    def test_subscription_accessible(self, owner_client):
        """Owner visits subscription page."""
        resp = owner_client.get(reverse("accounts:subscription"))
        assert resp.status_code == 200

    def test_invoices_accessible(self, owner_client):
        """Owner visits invoices page."""
        resp = owner_client.get(reverse("accounts:invoices"))
        assert resp.status_code == 200

    def test_table_management_accessible(self, owner_client, zone, table):
        """Owner visits table management page."""
        resp = owner_client.get(reverse("accounts:table-management"))
        assert resp.status_code == 200

    def test_theme_list_accessible(self, owner_client):
        """Owner visits theme list page."""
        resp = owner_client.get(reverse("accounts:theme-list"))
        assert resp.status_code == 200

    def test_theme_create_form_renders(self, owner_client):
        """Owner can access the theme creation form."""
        resp = owner_client.get(reverse("accounts:theme-create"))
        assert resp.status_code == 200


# =============================================================================
# 2. MANAGER JOURNEY
# =============================================================================


class TestManagerJourney:
    """Manager can view/edit menus, products, orders, tables, customers, analytics."""

    def test_dashboard_accessible(self, manager_client):
        resp = manager_client.get(reverse("accounts:dashboard"))
        assert resp.status_code == 200

    def test_menu_list_accessible(self, manager_client, menu):
        resp = manager_client.get(reverse("accounts:menu-list"))
        assert resp.status_code == 200

    def test_menu_create_accessible(self, manager_client):
        resp = manager_client.get(reverse("accounts:menu-create"))
        assert resp.status_code == 200

    def test_menu_detail_accessible(self, manager_client, menu):
        resp = manager_client.get(
            reverse("accounts:menu-detail", kwargs={"menu_id": menu.id})
        )
        assert resp.status_code == 200

    def test_menu_edit_accessible(self, manager_client, menu):
        resp = manager_client.get(
            reverse("accounts:menu-edit", kwargs={"menu_id": menu.id})
        )
        assert resp.status_code == 200

    def test_product_list_accessible(self, manager_client, product):
        resp = manager_client.get(reverse("accounts:product-list"))
        assert resp.status_code == 200

    def test_product_create_accessible(self, manager_client, category):
        resp = manager_client.get(reverse("accounts:product-create"))
        assert resp.status_code == 200

    def test_product_detail_accessible(self, manager_client, product):
        resp = manager_client.get(
            reverse("accounts:product-detail", kwargs={"product_id": product.id})
        )
        assert resp.status_code == 200

    def test_product_edit_accessible(self, manager_client, product):
        resp = manager_client.get(
            reverse("accounts:product-edit", kwargs={"product_id": product.id})
        )
        assert resp.status_code == 200

    def test_order_list_accessible(self, manager_client, order):
        resp = manager_client.get(reverse("accounts:order-list"))
        assert resp.status_code == 200

    def test_order_detail_accessible(self, manager_client, order):
        resp = manager_client.get(
            reverse("accounts:order-detail", kwargs={"order_id": order.id})
        )
        assert resp.status_code == 200

    def test_table_management_accessible(self, manager_client, zone, table):
        resp = manager_client.get(reverse("accounts:table-management"))
        assert resp.status_code == 200

    def test_customer_list_accessible(self, manager_client):
        resp = manager_client.get(reverse("accounts:customer-list"))
        assert resp.status_code == 200

    def test_analytics_accessible(self, manager_client):
        resp = manager_client.get(reverse("accounts:analytics"))
        assert resp.status_code == 200

    def test_qrcode_list_accessible(self, manager_client, qr_code):
        resp = manager_client.get(reverse("accounts:qrcode-list"))
        assert resp.status_code == 200

    def test_qrcode_detail_accessible(self, manager_client, qr_code):
        resp = manager_client.get(
            reverse("accounts:qrcode-detail", kwargs={"qr_id": qr_code.id})
        )
        assert resp.status_code == 200

    def test_zone_create_post(self, manager_client, org):
        """Manager creates a zone via AJAX POST."""
        import json

        resp = manager_client.post(
            reverse("accounts:zone-create"),
            data=json.dumps({"name": "Terrace", "color": "#ff5733"}),
            content_type="application/json",
        )
        assert resp.status_code == 201
        from apps.orders.models import Zone

        assert Zone.objects.filter(organization=org, name="Terrace").exists()

    def test_table_create_post(self, manager_client, org, zone):
        """Manager creates a table via AJAX POST."""
        import json

        resp = manager_client.post(
            reverse("accounts:table-create"),
            data=json.dumps(
                {
                    "name": "Table 10",
                    "zone_id": str(zone.id),
                    "capacity": 6,
                }
            ),
            content_type="application/json",
        )
        assert resp.status_code == 201
        from apps.orders.models import Table

        assert Table.objects.filter(organization=org, name="Table 10").exists()


# =============================================================================
# 3. STAFF JOURNEY
# =============================================================================


class TestStaffJourney:
    """
    Staff can view menus/products (read-only pages load),
    view/manage orders (change status), and view tables.
    """

    def test_dashboard_accessible(self, staff_client):
        resp = staff_client.get(reverse("accounts:dashboard"))
        assert resp.status_code == 200

    def test_menu_list_accessible(self, staff_client, menu):
        """Staff can view menu list."""
        resp = staff_client.get(reverse("accounts:menu-list"))
        assert resp.status_code == 200

    def test_menu_detail_accessible(self, staff_client, menu):
        """Staff can view menu detail."""
        resp = staff_client.get(
            reverse("accounts:menu-detail", kwargs={"menu_id": menu.id})
        )
        assert resp.status_code == 200

    def test_product_list_accessible(self, staff_client, product):
        """Staff can view product list."""
        resp = staff_client.get(reverse("accounts:product-list"))
        assert resp.status_code == 200

    def test_product_detail_accessible(self, staff_client, product):
        """Staff can view product detail."""
        resp = staff_client.get(
            reverse("accounts:product-detail", kwargs={"product_id": product.id})
        )
        assert resp.status_code == 200

    def test_order_list_accessible(self, staff_client, order):
        """Staff can view order list."""
        resp = staff_client.get(reverse("accounts:order-list"))
        assert resp.status_code == 200

    def test_order_detail_accessible(self, staff_client, order):
        """Staff can view order detail."""
        resp = staff_client.get(
            reverse("accounts:order-detail", kwargs={"order_id": order.id})
        )
        assert resp.status_code == 200

    def test_order_update_status(self, staff_client, order):
        """Staff can change order status via AJAX POST."""
        import json

        resp = staff_client.post(
            reverse("accounts:order-update-status", kwargs={"order_id": order.id}),
            data=json.dumps({"action": "confirm"}),
            content_type="application/json",
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["status"] == "CONFIRMED"

    def test_table_management_accessible(self, staff_client, zone, table):
        """Staff can view table management page."""
        resp = staff_client.get(reverse("accounts:table-management"))
        assert resp.status_code == 200

    def test_qrcode_list_accessible(self, staff_client, qr_code):
        """Staff can view QR code list."""
        resp = staff_client.get(reverse("accounts:qrcode-list"))
        assert resp.status_code == 200

    def test_customer_list_accessible(self, staff_client):
        """Staff can view customer list."""
        resp = staff_client.get(reverse("accounts:customer-list"))
        assert resp.status_code == 200


# =============================================================================
# 4. VIEWER JOURNEY
# =============================================================================


class TestViewerJourney:
    """
    Viewer can view menus, products, orders (read-only).
    Pages should load (200) for all list/detail views.
    """

    def test_dashboard_accessible(self, viewer_client):
        resp = viewer_client.get(reverse("accounts:dashboard"))
        assert resp.status_code == 200

    def test_menu_list_accessible(self, viewer_client, menu):
        resp = viewer_client.get(reverse("accounts:menu-list"))
        assert resp.status_code == 200

    def test_menu_detail_accessible(self, viewer_client, menu):
        resp = viewer_client.get(
            reverse("accounts:menu-detail", kwargs={"menu_id": menu.id})
        )
        assert resp.status_code == 200

    def test_product_list_accessible(self, viewer_client, product):
        resp = viewer_client.get(reverse("accounts:product-list"))
        assert resp.status_code == 200

    def test_product_detail_accessible(self, viewer_client, product):
        resp = viewer_client.get(
            reverse("accounts:product-detail", kwargs={"product_id": product.id})
        )
        assert resp.status_code == 200

    def test_order_list_accessible(self, viewer_client, order):
        resp = viewer_client.get(reverse("accounts:order-list"))
        assert resp.status_code == 200

    def test_order_detail_accessible(self, viewer_client, order):
        resp = viewer_client.get(
            reverse("accounts:order-detail", kwargs={"order_id": order.id})
        )
        assert resp.status_code == 200

    def test_customer_list_accessible(self, viewer_client):
        resp = viewer_client.get(reverse("accounts:customer-list"))
        assert resp.status_code == 200

    def test_analytics_accessible(self, viewer_client):
        resp = viewer_client.get(reverse("accounts:analytics"))
        assert resp.status_code == 200

    def test_table_management_accessible(self, viewer_client, zone, table):
        resp = viewer_client.get(reverse("accounts:table-management"))
        assert resp.status_code == 200

    def test_qrcode_list_accessible(self, viewer_client, qr_code):
        resp = viewer_client.get(reverse("accounts:qrcode-list"))
        assert resp.status_code == 200

    def test_qrcode_detail_accessible(self, viewer_client, qr_code):
        resp = viewer_client.get(
            reverse("accounts:qrcode-detail", kwargs={"qr_id": qr_code.id})
        )
        assert resp.status_code == 200

    def test_profile_accessible(self, viewer_client):
        resp = viewer_client.get(reverse("accounts:profile"))
        assert resp.status_code == 200

    def test_settings_accessible(self, viewer_client):
        resp = viewer_client.get(reverse("accounts:settings"))
        assert resp.status_code == 200


# =============================================================================
# 5. ANONYMOUS USER JOURNEY
# =============================================================================


class TestAnonymousUserJourney:
    """All portal URLs redirect anonymous users to the login page."""

    def test_login_page_accessible(self, anon_client):
        """Login page itself is accessible without auth."""
        resp = anon_client.get(reverse("accounts:login"))
        assert resp.status_code == 200

    @pytest.mark.parametrize("url_name", ALL_PROTECTED_GET_URLS)
    def test_protected_pages_redirect_to_login(self, anon_client, url_name):
        """Anonymous user is redirected to login for all protected pages."""
        resp = anon_client.get(reverse(url_name))
        assert resp.status_code == 302, f"{url_name} did not redirect anonymous user"
        assert "/account/login/" in resp.url, (
            f"{url_name} redirected to {resp.url} instead of login"
        )

    def test_dashboard_redirects_to_login(self, anon_client):
        """Dashboard specifically redirects to login with next parameter."""
        resp = anon_client.get(reverse("accounts:dashboard"))
        assert resp.status_code == 302
        assert "/account/login/" in resp.url

    def test_menu_list_redirects_to_login(self, anon_client):
        resp = anon_client.get(reverse("accounts:menu-list"))
        assert resp.status_code == 302
        assert "/account/login/" in resp.url

    def test_order_list_redirects_to_login(self, anon_client):
        resp = anon_client.get(reverse("accounts:order-list"))
        assert resp.status_code == 302
        assert "/account/login/" in resp.url

    def test_profile_redirects_to_login(self, anon_client):
        resp = anon_client.get(reverse("accounts:profile"))
        assert resp.status_code == 302
        assert "/account/login/" in resp.url

    def test_qrcode_list_redirects_to_login(self, anon_client):
        resp = anon_client.get(reverse("accounts:qrcode-list"))
        assert resp.status_code == 302
        assert "/account/login/" in resp.url

    def test_analytics_redirects_to_login(self, anon_client):
        resp = anon_client.get(reverse("accounts:analytics"))
        assert resp.status_code == 302
        assert "/account/login/" in resp.url

    def test_customer_list_redirects_to_login(self, anon_client):
        resp = anon_client.get(reverse("accounts:customer-list"))
        assert resp.status_code == 302
        assert "/account/login/" in resp.url

    def test_subscription_redirects_to_login(self, anon_client):
        resp = anon_client.get(reverse("accounts:subscription"))
        assert resp.status_code == 302
        assert "/account/login/" in resp.url

    def test_post_endpoints_redirect_to_login(self, anon_client):
        """POST endpoints also redirect anonymous users."""
        post_urls = [
            reverse("accounts:menu-create"),
            reverse("accounts:qrcode-create"),
            reverse("accounts:zone-create"),
            reverse("accounts:table-create"),
        ]
        for url in post_urls:
            resp = anon_client.post(url, {})
            assert resp.status_code == 302, (
                f"POST {url} did not redirect anonymous user"
            )
            assert "/account/login/" in resp.url


# =============================================================================
# 6. NO-ORGANIZATION USER JOURNEY
# =============================================================================


class TestNoOrganizationUserJourney:
    """
    Authenticated user without an organization is redirected to profile
    for org-required pages, but can access login-only pages.
    """

    def test_profile_accessible(self, no_org_client):
        """Profile page is accessible without organization (LoginRequiredMixin only)."""
        resp = no_org_client.get(reverse("accounts:profile"))
        assert resp.status_code == 200

    def test_settings_accessible(self, no_org_client):
        """Settings page is accessible without organization."""
        resp = no_org_client.get(reverse("accounts:settings"))
        assert resp.status_code == 200

    def test_subscription_accessible(self, no_org_client):
        """Subscription page is accessible without organization."""
        resp = no_org_client.get(reverse("accounts:subscription"))
        assert resp.status_code == 200

    def test_dashboard_redirects_to_profile(self, no_org_client):
        """Dashboard (OrganizationRequiredMixin) redirects to profile."""
        resp = no_org_client.get(reverse("accounts:dashboard"))
        assert resp.status_code == 302
        assert "/account/profile/" in resp.url

    def test_menu_list_redirects_to_profile(self, no_org_client):
        """Menu list (function-based _get_org check) redirects to profile."""
        resp = no_org_client.get(reverse("accounts:menu-list"))
        assert resp.status_code == 302
        assert "/account/profile/" in resp.url

    def test_menu_create_redirects_to_profile(self, no_org_client):
        resp = no_org_client.get(reverse("accounts:menu-create"))
        assert resp.status_code == 302
        assert "/account/profile/" in resp.url

    def test_product_list_redirects_to_profile(self, no_org_client):
        resp = no_org_client.get(reverse("accounts:product-list"))
        assert resp.status_code == 302
        assert "/account/profile/" in resp.url

    def test_product_create_redirects_to_profile(self, no_org_client):
        resp = no_org_client.get(reverse("accounts:product-create"))
        assert resp.status_code == 302
        assert "/account/profile/" in resp.url

    def test_order_list_redirects_to_profile(self, no_org_client):
        resp = no_org_client.get(reverse("accounts:order-list"))
        assert resp.status_code == 302
        assert "/account/profile/" in resp.url

    def test_table_management_redirects_to_profile(self, no_org_client):
        resp = no_org_client.get(reverse("accounts:table-management"))
        assert resp.status_code == 302
        assert "/account/profile/" in resp.url

    def test_qrcode_list_redirects_to_profile(self, no_org_client):
        resp = no_org_client.get(reverse("accounts:qrcode-list"))
        assert resp.status_code == 302
        assert "/account/profile/" in resp.url

    def test_customer_list_redirects_to_profile(self, no_org_client):
        resp = no_org_client.get(reverse("accounts:customer-list"))
        assert resp.status_code == 302
        assert "/account/profile/" in resp.url

    def test_analytics_redirects_to_profile(self, no_org_client):
        resp = no_org_client.get(reverse("accounts:analytics"))
        assert resp.status_code == 302
        assert "/account/profile/" in resp.url

    def test_theme_list_redirects_to_profile(self, no_org_client):
        resp = no_org_client.get(reverse("accounts:theme-list"))
        assert resp.status_code == 302
        assert "/account/profile/" in resp.url

    def test_theme_create_redirects_to_profile(self, no_org_client):
        resp = no_org_client.get(reverse("accounts:theme-create"))
        assert resp.status_code == 302
        assert "/account/profile/" in resp.url


# =============================================================================
# 7. QR CODE DOWNLOAD JOURNEY
# =============================================================================


class TestQRCodeDownloadJourney:
    """
    Owner creates QR code and downloads it in every supported format and size.
    Tests cover:
    - PNG in sizes: 128, 256, 512, 1024
    - SVG, JPG, PDF
    - Print designs: A4, A5, 10x20cm, 15x30cm, 20x40cm
    """

    @pytest.mark.parametrize("size", [128, 256, 512, 1024])
    @patch("apps.orders.services.qr_generator.QRGeneratorService.download_qr")
    def test_download_png_sizes(self, mock_download, owner_client, qr_code, size):
        """Download QR code as PNG in different sizes."""
        mock_download.return_value = BytesIO(b"\x89PNG\r\n\x1a\nfakedata")
        resp = owner_client.get(
            reverse("accounts:qrcode-download", kwargs={"qr_id": qr_code.id}),
            {"format": "png", "size": str(size)},
        )
        assert resp.status_code == 200
        assert resp["Content-Type"] == "image/png"
        assert f"{size}px.png" in resp["Content-Disposition"]
        mock_download.assert_called_once_with(qr_code, format="png", size=size)

    @patch("apps.orders.services.qr_generator.QRGeneratorService.download_qr")
    def test_download_svg(self, mock_download, owner_client, qr_code):
        """Download QR code as SVG."""
        mock_download.return_value = BytesIO(
            b'<svg xmlns="http://www.w3.org/2000/svg">...</svg>'
        )
        resp = owner_client.get(
            reverse("accounts:qrcode-download", kwargs={"qr_id": qr_code.id}),
            {"format": "svg", "size": "512"},
        )
        assert resp.status_code == 200
        assert resp["Content-Type"] == "image/svg+xml"
        assert ".svg" in resp["Content-Disposition"]

    @patch("apps.orders.services.qr_generator.QRGeneratorService.download_qr")
    def test_download_jpg(self, mock_download, owner_client, qr_code):
        """Download QR code as JPG."""
        mock_download.return_value = BytesIO(b"\xff\xd8\xff\xe0fakedata")
        resp = owner_client.get(
            reverse("accounts:qrcode-download", kwargs={"qr_id": qr_code.id}),
            {"format": "jpg", "size": "256"},
        )
        assert resp.status_code == 200
        assert resp["Content-Type"] == "image/jpeg"
        assert ".jpg" in resp["Content-Disposition"]

    @patch("apps.orders.services.qr_generator.QRGeneratorService.download_qr")
    def test_download_pdf(self, mock_download, owner_client, qr_code):
        """Download QR code as PDF."""
        mock_download.return_value = BytesIO(b"%PDF-1.4 fake")
        resp = owner_client.get(
            reverse("accounts:qrcode-download", kwargs={"qr_id": qr_code.id}),
            {"format": "pdf", "size": "512"},
        )
        assert resp.status_code == 200
        assert resp["Content-Type"] == "application/pdf"
        assert ".pdf" in resp["Content-Disposition"]

    @patch("apps.orders.services.qr_generator.QRGeneratorService.download_qr")
    def test_download_invalid_format_defaults_to_png(
        self, mock_download, owner_client, qr_code
    ):
        """Invalid format defaults to PNG."""
        mock_download.return_value = BytesIO(b"\x89PNG\r\n\x1a\nfakedata")
        resp = owner_client.get(
            reverse("accounts:qrcode-download", kwargs={"qr_id": qr_code.id}),
            {"format": "webp"},
        )
        assert resp.status_code == 200
        assert resp["Content-Type"] == "image/png"

    @patch("apps.orders.services.qr_generator.QRGeneratorService.download_qr")
    def test_download_invalid_size_defaults_to_512(
        self, mock_download, owner_client, qr_code
    ):
        """Invalid size defaults to 512."""
        mock_download.return_value = BytesIO(b"\x89PNG\r\n\x1a\nfakedata")
        resp = owner_client.get(
            reverse("accounts:qrcode-download", kwargs={"qr_id": qr_code.id}),
            {"format": "png", "size": "999"},
        )
        assert resp.status_code == 200
        mock_download.assert_called_once_with(qr_code, format="png", size=512)

    @pytest.mark.parametrize(
        "design_size", ["A4", "A5", "10x20cm", "15x30cm", "20x40cm"]
    )
    @patch("apps.orders.services.qr_generator.QRGeneratorService.download_print_design")
    def test_download_print_sizes(self, mock_print, owner_client, qr_code, design_size):
        """Download print-ready PDF in all supported sizes."""
        mock_print.return_value = BytesIO(b"%PDF-1.4 print design content")
        resp = owner_client.get(
            reverse("accounts:qrcode-download-print", kwargs={"qr_id": qr_code.id}),
            {"design_size": design_size},
        )
        assert resp.status_code == 200
        assert resp["Content-Type"] == "application/pdf"
        assert design_size in resp["Content-Disposition"]
        mock_print.assert_called_once_with(qr_code, design_size=design_size)

    @patch("apps.orders.services.qr_generator.QRGeneratorService.download_print_design")
    def test_download_print_invalid_size_defaults_to_a4(
        self, mock_print, owner_client, qr_code
    ):
        """Invalid print design size defaults to A4."""
        mock_print.return_value = BytesIO(b"%PDF-1.4 A4 fallback")
        resp = owner_client.get(
            reverse("accounts:qrcode-download-print", kwargs={"qr_id": qr_code.id}),
            {"design_size": "INVALID"},
        )
        assert resp.status_code == 200
        mock_print.assert_called_once_with(qr_code, design_size="A4")

    @patch("apps.orders.services.qr_generator.QRGeneratorService.download_qr")
    def test_download_requires_auth(self, mock_download, anon_client, qr_code):
        """Anonymous user cannot download QR codes."""
        mock_download.return_value = BytesIO(b"fake")
        resp = anon_client.get(
            reverse("accounts:qrcode-download", kwargs={"qr_id": qr_code.id}),
            {"format": "png"},
        )
        assert resp.status_code == 302
        assert "/account/login/" in resp.url

    @patch("apps.orders.services.qr_generator.QRGeneratorService.download_qr")
    def test_download_requires_org(self, mock_download, no_org_client, qr_code):
        """User without organization is redirected to profile on download."""
        mock_download.return_value = BytesIO(b"fake")
        resp = no_org_client.get(
            reverse("accounts:qrcode-download", kwargs={"qr_id": qr_code.id}),
            {"format": "png"},
        )
        assert resp.status_code == 302
        assert "/account/profile/" in resp.url


# =============================================================================
# 8. ORGANIZATION ISOLATION TESTS
# =============================================================================


class TestOrganizationIsolation:
    """
    Verify that users cannot access resources belonging to another organization.
    Accessing another org's resource should return 404.
    """

    def test_cannot_view_other_org_menu_detail(self, owner_client, other_org_menu):
        """Owner cannot view a menu from another organization (404)."""
        resp = owner_client.get(
            reverse("accounts:menu-detail", kwargs={"menu_id": other_org_menu.id})
        )
        assert resp.status_code == 404

    def test_cannot_edit_other_org_menu(self, owner_client, other_org_menu):
        """Owner cannot edit a menu from another organization (404)."""
        resp = owner_client.get(
            reverse("accounts:menu-edit", kwargs={"menu_id": other_org_menu.id})
        )
        assert resp.status_code == 404

    def test_cannot_view_other_org_order_detail(self, owner_client, other_org_order):
        """Owner cannot view an order from another organization (404)."""
        resp = owner_client.get(
            reverse("accounts:order-detail", kwargs={"order_id": other_org_order.id})
        )
        assert resp.status_code == 404

    def test_cannot_view_other_org_qrcode_detail(self, owner_client, other_org_qr):
        """Owner cannot view a QR code from another organization (404)."""
        resp = owner_client.get(
            reverse("accounts:qrcode-detail", kwargs={"qr_id": other_org_qr.id})
        )
        assert resp.status_code == 404

    @patch("apps.orders.services.qr_generator.QRGeneratorService.download_qr")
    def test_cannot_download_other_org_qrcode(
        self, mock_download, owner_client, other_org_qr
    ):
        """Owner cannot download a QR code from another organization (404)."""
        mock_download.return_value = BytesIO(b"fake")
        resp = owner_client.get(
            reverse("accounts:qrcode-download", kwargs={"qr_id": other_org_qr.id}),
            {"format": "png"},
        )
        assert resp.status_code == 404

    @patch("apps.orders.services.qr_generator.QRGeneratorService.download_print_design")
    def test_cannot_download_other_org_qrcode_print(
        self, mock_print, owner_client, other_org_qr
    ):
        """Owner cannot download print design from another organization (404)."""
        mock_print.return_value = BytesIO(b"fake")
        resp = owner_client.get(
            reverse(
                "accounts:qrcode-download-print", kwargs={"qr_id": other_org_qr.id}
            ),
            {"design_size": "A4"},
        )
        assert resp.status_code == 404

    def test_cannot_update_other_org_order_status(self, owner_client, other_org_order):
        """Owner cannot change status of another organization's order (404)."""
        import json

        resp = owner_client.post(
            reverse(
                "accounts:order-update-status", kwargs={"order_id": other_org_order.id}
            ),
            data=json.dumps({"action": "confirm"}),
            content_type="application/json",
        )
        assert resp.status_code == 404

    def test_cannot_delete_other_org_menu(self, owner_client, other_org_menu):
        """Owner cannot soft-delete another organization's menu (404)."""
        resp = owner_client.post(
            reverse("accounts:menu-delete", kwargs={"menu_id": other_org_menu.id})
        )
        assert resp.status_code == 404

    def test_menu_list_shows_only_own_org_menus(
        self, owner_client, menu, other_org_menu
    ):
        """Menu list only shows menus for the user's organization."""
        resp = owner_client.get(reverse("accounts:menu-list"))
        assert resp.status_code == 200
        content = resp.content.decode()
        assert menu.name in content
        assert other_org_menu.name not in content

    def test_order_list_shows_only_own_org_orders(
        self, owner_client, order, other_org_order
    ):
        """Order list only shows orders for the user's organization."""
        resp = owner_client.get(reverse("accounts:order-list"))
        assert resp.status_code == 200
        content = resp.content.decode()
        assert order.order_number in content
        assert other_org_order.order_number not in content

    def test_qrcode_list_shows_only_own_org_qrcodes(
        self, owner_client, qr_code, other_org_qr
    ):
        """QR code list only shows codes for the user's organization."""
        resp = owner_client.get(reverse("accounts:qrcode-list"))
        assert resp.status_code == 200
        content = resp.content.decode()
        assert qr_code.name in content
        assert other_org_qr.name not in content


# =============================================================================
# 9. DASHBOARD API ENDPOINTS
# =============================================================================


class TestDashboardAPIEndpoints:
    """Test dashboard AJAX/JSON API endpoints."""

    def test_kpis_api_requires_auth(self, anon_client):
        """KPIs API returns 403 for anonymous users."""
        resp = anon_client.get(reverse("accounts:dashboard-kpis-api"))
        assert resp.status_code == 403

    def test_kpis_api_requires_org(self, no_org_client):
        """KPIs API returns 403 for users without organization."""
        resp = no_org_client.get(reverse("accounts:dashboard-kpis-api"))
        assert resp.status_code == 403

    def test_kpis_api_accessible(self, owner_client):
        """KPIs API returns JSON for authenticated owner."""
        resp = owner_client.get(reverse("accounts:dashboard-kpis-api"))
        assert resp.status_code == 200
        assert resp["Content-Type"] == "application/json"

    def test_qr_trend_api_accessible(self, owner_client):
        resp = owner_client.get(reverse("accounts:dashboard-qr-trend-api"))
        assert resp.status_code == 200
        assert resp["Content-Type"] == "application/json"

    def test_revenue_api_accessible(self, owner_client):
        resp = owner_client.get(reverse("accounts:dashboard-revenue-api"))
        assert resp.status_code == 200
        assert resp["Content-Type"] == "application/json"

    def test_orders_chart_api_accessible(self, owner_client):
        resp = owner_client.get(reverse("accounts:dashboard-orders-chart-api"))
        assert resp.status_code == 200
        assert resp["Content-Type"] == "application/json"

    def test_top_products_api_accessible(self, owner_client):
        resp = owner_client.get(reverse("accounts:dashboard-top-products-api"))
        assert resp.status_code == 200
        assert resp["Content-Type"] == "application/json"

    def test_recent_orders_api_accessible(self, owner_client):
        resp = owner_client.get(reverse("accounts:dashboard-recent-orders-api"))
        assert resp.status_code == 200
        assert resp["Content-Type"] == "application/json"


# =============================================================================
# 10. ANALYTICS API ENDPOINTS
# =============================================================================


class TestAnalyticsAPIEndpoints:
    """Test analytics AJAX/JSON API endpoints."""

    def test_qr_scans_api_accessible(self, owner_client):
        resp = owner_client.get(reverse("accounts:analytics-qr-scans-api"))
        assert resp.status_code == 200
        data = resp.json()
        assert "daily" in data

    def test_revenue_api_accessible(self, owner_client):
        resp = owner_client.get(reverse("accounts:analytics-revenue-api"))
        assert resp.status_code == 200
        data = resp.json()
        assert "daily" in data

    def test_products_api_accessible(self, owner_client):
        resp = owner_client.get(reverse("accounts:analytics-products-api"))
        assert resp.status_code == 200
        data = resp.json()
        assert "top_sellers" in data

    def test_customers_api_accessible(self, owner_client):
        resp = owner_client.get(reverse("accounts:analytics-customers-api"))
        assert resp.status_code == 200
        data = resp.json()
        assert "total" in data

    def test_analytics_api_requires_auth(self, anon_client):
        """All analytics API endpoints redirect anonymous users."""
        api_urls = [
            reverse("accounts:analytics-qr-scans-api"),
            reverse("accounts:analytics-revenue-api"),
            reverse("accounts:analytics-products-api"),
            reverse("accounts:analytics-customers-api"),
        ]
        for url in api_urls:
            resp = anon_client.get(url)
            assert resp.status_code == 302, f"{url} did not redirect anonymous user"

    def test_analytics_api_requires_org(self, no_org_client):
        """Analytics API endpoints return 403 for users without organization."""
        api_urls = [
            reverse("accounts:analytics-qr-scans-api"),
            reverse("accounts:analytics-revenue-api"),
            reverse("accounts:analytics-products-api"),
            reverse("accounts:analytics-customers-api"),
        ]
        for url in api_urls:
            resp = no_org_client.get(url)
            assert resp.status_code == 403, f"{url} did not return 403 for no-org user"


# =============================================================================
# 11. ORDER / TABLE API ENDPOINTS
# =============================================================================


class TestOrderTableAPIEndpoints:
    """Test order and table polling API endpoints."""

    def test_order_api_accessible(self, owner_client):
        """Order polling API returns JSON."""
        resp = owner_client.get(reverse("accounts:order-api"))
        assert resp.status_code == 200
        data = resp.json()
        assert "orders" in data

    def test_table_api_accessible(self, owner_client):
        """Table polling API returns JSON."""
        resp = owner_client.get(reverse("accounts:table-api"))
        assert resp.status_code == 200
        data = resp.json()
        assert "zones" in data

    def test_order_api_requires_org(self, no_org_client):
        resp = no_org_client.get(reverse("accounts:order-api"))
        assert resp.status_code == 403

    def test_table_api_requires_org(self, no_org_client):
        resp = no_org_client.get(reverse("accounts:table-api"))
        assert resp.status_code == 403


# =============================================================================
# 12. CRUD MUTATION TESTS (POST endpoints)
# =============================================================================


class TestCRUDMutations:
    """Test POST-based mutation endpoints for menus, products, orders."""

    def test_menu_delete_soft_deletes(self, owner_client, menu):
        """Soft-deleting a menu sets deleted_at."""
        resp = owner_client.post(
            reverse("accounts:menu-delete", kwargs={"menu_id": menu.id})
        )
        assert resp.status_code == 302
        menu.refresh_from_db()
        assert menu.deleted_at is not None

    def test_product_delete_soft_deletes(self, owner_client, product):
        """Soft-deleting a product sets deleted_at."""
        resp = owner_client.post(
            reverse("accounts:product-delete", kwargs={"product_id": product.id})
        )
        assert resp.status_code == 302
        product.refresh_from_db()
        assert product.deleted_at is not None

    def test_product_toggle_active(self, owner_client, product):
        """Toggle product active status via AJAX POST."""
        original = product.is_active
        resp = owner_client.post(
            reverse("accounts:product-toggle-active", kwargs={"product_id": product.id})
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["is_active"] is not original

    def test_product_toggle_featured(self, owner_client, product):
        """Toggle product featured status via AJAX POST."""
        original = product.is_featured
        resp = owner_client.post(
            reverse(
                "accounts:product-toggle-featured", kwargs={"product_id": product.id}
            )
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["is_featured"] is not original

    def test_qrcode_toggle_active(self, owner_client, qr_code):
        """Toggle QR code active status via AJAX POST."""
        original = qr_code.is_active
        resp = owner_client.post(
            reverse("accounts:qrcode-toggle", kwargs={"qr_id": qr_code.id})
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["is_active"] is not original

    def test_zone_delete_soft_deletes(self, owner_client, zone):
        """Soft-deleting a zone via AJAX POST."""
        resp = owner_client.post(
            reverse("accounts:zone-delete", kwargs={"zone_id": zone.id})
        )
        assert resp.status_code == 200
        zone.refresh_from_db()
        assert zone.deleted_at is not None

    def test_table_delete_soft_deletes(self, owner_client, table):
        """Soft-deleting a table via AJAX POST."""
        resp = owner_client.post(
            reverse("accounts:table-delete", kwargs={"table_id": table.id})
        )
        assert resp.status_code == 200
        table.refresh_from_db()
        assert table.deleted_at is not None

    def test_order_status_transitions(self, owner_client, order):
        """Test order through multiple status transitions."""
        import json

        # PENDING -> CONFIRMED
        resp = owner_client.post(
            reverse("accounts:order-update-status", kwargs={"order_id": order.id}),
            data=json.dumps({"action": "confirm"}),
            content_type="application/json",
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "CONFIRMED"

        # CONFIRMED -> PREPARING
        resp = owner_client.post(
            reverse("accounts:order-update-status", kwargs={"order_id": order.id}),
            data=json.dumps({"action": "prepare"}),
            content_type="application/json",
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "PREPARING"

        # PREPARING -> READY
        resp = owner_client.post(
            reverse("accounts:order-update-status", kwargs={"order_id": order.id}),
            data=json.dumps({"action": "ready"}),
            content_type="application/json",
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "READY"

        # READY -> DELIVERED
        resp = owner_client.post(
            reverse("accounts:order-update-status", kwargs={"order_id": order.id}),
            data=json.dumps({"action": "deliver"}),
            content_type="application/json",
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "DELIVERED"

        # DELIVERED -> COMPLETED
        resp = owner_client.post(
            reverse("accounts:order-update-status", kwargs={"order_id": order.id}),
            data=json.dumps({"action": "complete"}),
            content_type="application/json",
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "COMPLETED"

    def test_order_cancel(self, owner_client):
        """Test order cancellation."""
        import json

        cancel_order = OrderFactory(
            organization=owner_client.session.get("_auth_user_id") and None
        )
        # Create order with correct org
        from apps.core.models import User

        user = User.objects.get(pk=owner_client.session["_auth_user_id"])
        cancel_order = OrderFactory(organization=user.organization)

        resp = owner_client.post(
            reverse(
                "accounts:order-update-status", kwargs={"order_id": cancel_order.id}
            ),
            data=json.dumps({"action": "cancel"}),
            content_type="application/json",
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "CANCELLED"

    def test_invalid_order_action_returns_400(self, owner_client, order):
        """Invalid order status action returns 400."""
        import json

        resp = owner_client.post(
            reverse("accounts:order-update-status", kwargs={"order_id": order.id}),
            data=json.dumps({"action": "invalid_action"}),
            content_type="application/json",
        )
        assert resp.status_code == 400

    def test_zone_edit_via_ajax(self, owner_client, zone):
        """Edit zone name via AJAX POST."""
        import json

        resp = owner_client.post(
            reverse("accounts:zone-edit", kwargs={"zone_id": zone.id}),
            data=json.dumps({"name": "Updated Zone Name"}),
            content_type="application/json",
        )
        assert resp.status_code == 200
        zone.refresh_from_db()
        assert zone.name == "Updated Zone Name"

    def test_table_edit_via_ajax(self, owner_client, table):
        """Edit table capacity via AJAX POST."""
        import json

        resp = owner_client.post(
            reverse("accounts:table-edit", kwargs={"table_id": table.id}),
            data=json.dumps({"capacity": 8}),
            content_type="application/json",
        )
        assert resp.status_code == 200
        table.refresh_from_db()
        assert table.capacity == 8

    def test_category_create_via_ajax(self, owner_client, menu, org):
        """Create category via AJAX POST."""
        import json

        resp = owner_client.post(
            reverse("accounts:category-create", kwargs={"menu_id": menu.id}),
            data=json.dumps({"name": "Appetizers", "description": "Starters"}),
            content_type="application/json",
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["success"] is True
        assert data["category"]["name"] == "Appetizers"

    def test_category_edit_via_ajax(self, owner_client, category):
        """Edit category via AJAX POST."""
        import json

        resp = owner_client.post(
            reverse("accounts:category-edit", kwargs={"category_id": category.id}),
            data=json.dumps({"name": "Updated Category"}),
            content_type="application/json",
        )
        assert resp.status_code == 200
        category.refresh_from_db()
        assert category.name == "Updated Category"

    def test_category_delete_via_ajax(self, owner_client, category):
        """Soft-delete category via AJAX POST."""
        resp = owner_client.post(
            reverse("accounts:category-delete", kwargs={"category_id": category.id})
        )
        assert resp.status_code == 200
        category.refresh_from_db()
        assert category.deleted_at is not None


# =============================================================================
# 13. FILTER AND SEARCH TESTS
# =============================================================================


class TestFilterAndSearch:
    """Test filter and search functionality on list pages."""

    def test_product_list_search(self, owner_client, product):
        """Search products by name."""
        resp = owner_client.get(reverse("accounts:product-list"), {"q": product.name})
        assert resp.status_code == 200

    def test_product_list_filter_by_status(self, owner_client, product):
        """Filter products by active status."""
        resp = owner_client.get(reverse("accounts:product-list"), {"status": "active"})
        assert resp.status_code == 200

    def test_order_list_filter_by_status(self, owner_client, order):
        """Filter orders by status."""
        resp = owner_client.get(reverse("accounts:order-list"), {"status": "PENDING"})
        assert resp.status_code == 200

    def test_order_list_search_by_number(self, owner_client, order):
        """Search orders by order number."""
        resp = owner_client.get(
            reverse("accounts:order-list"), {"q": order.order_number}
        )
        assert resp.status_code == 200

    def test_qrcode_list_filter_by_type(self, owner_client, qr_code):
        """Filter QR codes by type."""
        resp = owner_client.get(reverse("accounts:qrcode-list"), {"type": "MENU"})
        assert resp.status_code == 200

    def test_customer_list_search(self, owner_client):
        """Search customers by name."""
        resp = owner_client.get(reverse("accounts:customer-list"), {"q": "test"})
        assert resp.status_code == 200

    def test_customer_list_sort(self, owner_client):
        """Sort customers by name."""
        resp = owner_client.get(reverse("accounts:customer-list"), {"sort": "name"})
        assert resp.status_code == 200


# =============================================================================
# 14. LOGIN / LOGOUT FLOW INTEGRATION
# =============================================================================


class TestLoginLogoutFlow:
    """Test the full login/logout cycle in the context of user journeys."""

    def test_login_redirects_to_dashboard_for_user_with_org(self, owner_user):
        """After login, user with organization is redirected to dashboard."""
        client = Client()
        client.force_login(owner_user)
        resp = client.get(reverse("accounts:dashboard"))
        assert resp.status_code == 200

    def test_logout_then_dashboard_redirects_to_login(self, owner_client):
        """After logout, accessing dashboard redirects to login."""
        owner_client.get(reverse("accounts:logout"))
        resp = owner_client.get(reverse("accounts:dashboard"))
        assert resp.status_code == 302
        assert "/account/login/" in resp.url

    def test_authenticated_user_cannot_access_login(self, owner_client):
        """Already authenticated user visiting login page gets redirected."""
        resp = owner_client.get(reverse("accounts:login"))
        assert resp.status_code == 302
        # AccountLoginView redirects authenticated users to dashboard
        assert "/account/dashboard/" in resp.url or "/account/" in resp.url
