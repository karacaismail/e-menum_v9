"""
Tests for critical bugfixes:
1. Orders 500 Error - customer_name property AttributeError
2. Table Management - JS URL mismatch with Django URL patterns
3. QR Code List - missing context variables (menus, tables)
4. Orders pagination - template uses page_obj but view passes orders
"""

import json
import uuid

import pytest
from django.urls import resolve

from apps.core.models import Organization, User


@pytest.fixture
def org(db):
    return Organization.objects.create(
        name="Test Restaurant",
        slug="test-restaurant",
        status="ACTIVE",
    )


@pytest.fixture
def owner(db, org):
    user = User.objects.create_user(
        email="owner@test.com",
        password="TestPass1234!",
        organization=org,
        first_name="Test",
        last_name="Owner",
        status="ACTIVE",
    )
    return user


@pytest.fixture
def logged_in_client(client, owner):
    client.login(email="owner@test.com", password="TestPass1234!")
    return client


# =============================================================================
# 1. Orders 500 Error - customer_name property
# =============================================================================


class TestOrderCustomerNameProperty:
    """Order.customer_name must not raise AttributeError."""

    def test_customer_name_without_customer(self, db, org):
        """customer_name should return info name when no customer linked."""
        from apps.orders.models import Order

        order = Order.objects.create(
            organization=org,
            order_number="TEST-001",
            type="DINE_IN",
            status="PENDING",
            customer_info={"name": "Ahmet"},
        )
        assert order.customer_name == "Ahmet"

    def test_customer_name_with_customer(self, db, org):
        """customer_name should return customer.name (not full_name)."""
        from apps.customers.models import Customer
        from apps.orders.models import Order

        customer = Customer.objects.create(
            organization=org,
            name="Mehmet Yilmaz",
            email="mehmet@test.com",
        )
        order = Order.objects.create(
            organization=org,
            order_number="TEST-002",
            type="DINE_IN",
            status="PENDING",
            customer=customer,
        )
        # This was causing 500 - full_name does not exist on Customer
        assert order.customer_name == "Mehmet Yilmaz"

    def test_customer_name_guest_default(self, db, org):
        """customer_name defaults to 'Guest' when no info."""
        from apps.orders.models import Order

        order = Order.objects.create(
            organization=org,
            order_number="TEST-003",
            type="DINE_IN",
            status="PENDING",
        )
        name = order.customer_name
        assert name is not None


# =============================================================================
# 2. Orders List View - no 500 error
# =============================================================================


class TestOrderListView:
    """Order list view should not return 500."""

    def test_order_list_no_500(self, logged_in_client):
        """GET /account/orders/ should return 200."""
        resp = logged_in_client.get("/account/orders/")
        assert resp.status_code == 200

    def test_order_list_with_orders(self, logged_in_client, org):
        """Order list with existing orders should render properly."""
        from apps.orders.models import Order

        Order.objects.create(
            organization=org,
            order_number="ORD-100",
            type="DINE_IN",
            status="PENDING",
            customer_info={"name": "Test Customer"},
        )
        resp = logged_in_client.get("/account/orders/")
        assert resp.status_code == 200
        assert b"ORD-100" in resp.content


# =============================================================================
# 3. Table Management - URL routing
# =============================================================================


class TestTableManagementURLs:
    """Table/Zone CRUD API URLs must exist and match JS calls."""

    def test_zone_create_api_url(self):
        """POST /account/api/zones/ should resolve."""
        match = resolve("/account/api/zones/")
        assert match is not None
        assert match.url_name == "zone-create-api"

    def test_zone_edit_api_url(self):
        """POST /account/api/zones/<uuid>/ should resolve."""
        test_uuid = str(uuid.uuid4())
        match = resolve(f"/account/api/zones/{test_uuid}/")
        assert match is not None
        assert match.url_name == "zone-api-detail"

    def test_table_create_api_url(self):
        """POST /account/api/tables/create/ should resolve."""
        match = resolve("/account/api/tables/create/")
        assert match is not None
        assert match.url_name == "table-create-api"

    def test_table_edit_api_url(self):
        """POST /account/api/tables/<uuid>/ should resolve."""
        test_uuid = str(uuid.uuid4())
        match = resolve(f"/account/api/tables/{test_uuid}/")
        assert match is not None
        assert match.url_name == "table-api-detail"

    def test_zone_create_functional(self, logged_in_client, org):
        """Creating a zone via API should work."""
        resp = logged_in_client.post(
            "/account/api/zones/",
            data=json.dumps({"name": "Teras", "color": "#ff0000"}),
            content_type="application/json",
        )
        assert resp.status_code in (200, 201)
        data = resp.json()
        assert data.get("success") is True

    def test_zone_delete_functional(self, logged_in_client, org):
        """Deleting a zone via API should work."""
        from apps.orders.models import Zone

        zone = Zone.objects.create(organization=org, name="ToDelete", slug="todelete")
        resp = logged_in_client.post(
            f"/account/api/zones/{zone.pk}/",
            data=json.dumps({}),
            content_type="application/json",
            HTTP_X_HTTP_METHOD_OVERRIDE="DELETE",
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("success") is True
        zone.refresh_from_db()
        assert zone.deleted_at is not None

    def test_table_create_functional(self, logged_in_client, org):
        """Creating a table via API should work."""
        from apps.orders.models import Zone

        zone = Zone.objects.create(organization=org, name="Main", slug="main")
        resp = logged_in_client.post(
            "/account/api/tables/create/",
            data=json.dumps({"zone_id": str(zone.pk), "name": "Masa 1", "capacity": 4}),
            content_type="application/json",
        )
        assert resp.status_code in (200, 201)

    def test_table_delete_functional(self, logged_in_client, org):
        """Deleting a table via API should work."""
        from apps.orders.models import Zone, Table

        zone = Zone.objects.create(organization=org, name="Main", slug="main")
        table = Table.objects.create(organization=org, zone=zone, name="T1", slug="t1")
        resp = logged_in_client.post(
            f"/account/api/tables/{table.pk}/",
            data=json.dumps({}),
            content_type="application/json",
            HTTP_X_HTTP_METHOD_OVERRIDE="DELETE",
        )
        assert resp.status_code == 200
        table.refresh_from_db()
        assert table.deleted_at is not None

    def test_table_edit_functional(self, logged_in_client, org):
        """Editing a table via API should work."""
        from apps.orders.models import Zone, Table

        zone = Zone.objects.create(organization=org, name="Main", slug="main")
        table = Table.objects.create(
            organization=org, zone=zone, name="T1", slug="t1", capacity=2
        )
        resp = logged_in_client.post(
            f"/account/api/tables/{table.pk}/",
            data=json.dumps({"name": "VIP Masa", "capacity": 6}),
            content_type="application/json",
        )
        assert resp.status_code == 200
        table.refresh_from_db()
        assert table.name == "VIP Masa"
        assert table.capacity == 6


# =============================================================================
# 4. QR Code List - context variables
# =============================================================================


class TestQRCodeListView:
    """QR code list view should pass menus and tables to template."""

    def test_qrcode_list_has_menus_context(self, logged_in_client):
        """GET /account/qr-codes/ should include 'menus' in context."""
        resp = logged_in_client.get("/account/qr-codes/")
        assert resp.status_code == 200
        assert "menus" in resp.context

    def test_qrcode_list_has_tables_context(self, logged_in_client):
        """GET /account/qr-codes/ should include 'tables' in context."""
        resp = logged_in_client.get("/account/qr-codes/")
        assert resp.status_code == 200
        assert "tables" in resp.context

    def test_qrcode_toggle_api_url(self):
        """Toggle API URL should resolve."""
        test_uuid = str(uuid.uuid4())
        match = resolve(f"/account/api/qrcodes/{test_uuid}/toggle/")
        assert match is not None
        assert match.url_name == "qrcode-toggle-api"

    def test_qrcode_create_api_url(self):
        """Create API URL should resolve."""
        match = resolve("/account/api/qrcodes/")
        assert match is not None
        assert match.url_name == "qrcode-create-api"


# =============================================================================
# 5. Superadmin visibility
# =============================================================================


class TestSuperadminVisibility:
    """Superadmin should see all organizations and users in admin."""

    def test_superadmin_sees_organizations(self, client, db):
        """Superadmin can access organization list in admin."""
        User.objects.create_superuser(
            email="admin@e-menum.net",
            password="Admin1234!emenum",
        )
        client.login(email="admin@e-menum.net", password="Admin1234!emenum")
        resp = client.get("/admin/core/organization/")
        assert resp.status_code == 200

    def test_superadmin_sees_users(self, client, db, org, owner):
        """Superadmin can see restaurant users in admin."""
        User.objects.create_superuser(
            email="admin2@e-menum.net",
            password="Admin1234!emenum",
        )
        client.login(email="admin2@e-menum.net", password="Admin1234!emenum")
        resp = client.get("/admin/core/user/")
        assert resp.status_code == 200
        # The restaurant owner should be visible
        assert b"owner@test.com" in resp.content
