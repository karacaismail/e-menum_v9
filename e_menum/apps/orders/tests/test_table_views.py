"""Tests for table and zone management views."""

import json
import uuid

import pytest
from django.test import Client


# All URLs live under /account/ with app_name="accounts"
TABLE_MANAGEMENT_URL = "/account/tables/"
ZONE_CREATE_URL = "/account/zones/create/"
TABLE_CREATE_URL = "/account/tables/create/"
TABLE_API_URL = "/account/api/tables/"
LOGIN_URL = "/account/login/"


def _zone_edit_url(zone_id):
    return f"/account/zones/{zone_id}/edit/"


def _zone_delete_url(zone_id):
    return f"/account/zones/{zone_id}/delete/"


def _table_edit_url(table_id):
    return f"/account/tables/{table_id}/edit/"


def _table_delete_url(table_id):
    return f"/account/tables/{table_id}/delete/"


# =========================================================================
# Anonymous access — all endpoints should redirect to login
# =========================================================================


@pytest.mark.django_db
class TestAnonymousAccess:
    """Anonymous users must be redirected to the login page."""

    def test_table_management_redirects(self, client: Client):
        resp = client.get(TABLE_MANAGEMENT_URL)
        assert resp.status_code == 302
        assert LOGIN_URL in resp.url

    def test_zone_create_redirects(self, client: Client):
        resp = client.post(
            ZONE_CREATE_URL,
            json.dumps({"name": "Terrace"}),
            content_type="application/json",
        )
        assert resp.status_code == 302
        assert LOGIN_URL in resp.url

    def test_zone_edit_redirects(self, client: Client):
        fake_id = uuid.uuid4()
        resp = client.post(
            _zone_edit_url(fake_id),
            json.dumps({"name": "Updated"}),
            content_type="application/json",
        )
        assert resp.status_code == 302
        assert LOGIN_URL in resp.url

    def test_zone_delete_redirects(self, client: Client):
        fake_id = uuid.uuid4()
        resp = client.post(_zone_delete_url(fake_id))
        assert resp.status_code == 302
        assert LOGIN_URL in resp.url

    def test_table_create_redirects(self, client: Client):
        resp = client.post(
            TABLE_CREATE_URL,
            json.dumps({"name": "T1", "zone_id": str(uuid.uuid4())}),
            content_type="application/json",
        )
        assert resp.status_code == 302
        assert LOGIN_URL in resp.url

    def test_table_edit_redirects(self, client: Client):
        fake_id = uuid.uuid4()
        resp = client.post(
            _table_edit_url(fake_id),
            json.dumps({"name": "Updated"}),
            content_type="application/json",
        )
        assert resp.status_code == 302
        assert LOGIN_URL in resp.url

    def test_table_delete_redirects(self, client: Client):
        fake_id = uuid.uuid4()
        resp = client.post(_table_delete_url(fake_id))
        assert resp.status_code == 302
        assert LOGIN_URL in resp.url

    def test_table_api_redirects(self, client: Client):
        resp = client.get(TABLE_API_URL)
        assert resp.status_code == 302
        assert LOGIN_URL in resp.url


# =========================================================================
# Authenticated user without organization
# =========================================================================


@pytest.mark.django_db
class TestNoOrganization:
    """A logged-in user with no org should get a redirect or 403."""

    def test_table_management_redirects_to_profile(self, client: Client, user):
        client.force_login(user)
        resp = client.get(TABLE_MANAGEMENT_URL)
        # View redirects to accounts:profile when org is missing
        assert resp.status_code == 302
        assert "profile" in resp.url

    def test_zone_create_returns_403(self, client: Client, user):
        client.force_login(user)
        resp = client.post(
            ZONE_CREATE_URL,
            json.dumps({"name": "Terrace"}),
            content_type="application/json",
        )
        assert resp.status_code == 403

    def test_table_create_returns_403(self, client: Client, user):
        client.force_login(user)
        resp = client.post(
            TABLE_CREATE_URL,
            json.dumps({"name": "T1", "zone_id": str(uuid.uuid4())}),
            content_type="application/json",
        )
        assert resp.status_code == 403

    def test_table_api_returns_403(self, client: Client, user):
        client.force_login(user)
        resp = client.get(TABLE_API_URL)
        assert resp.status_code == 403


# =========================================================================
# Zone CRUD
# =========================================================================


@pytest.mark.django_db
class TestZoneCRUD:
    """Zone create / edit / delete operations."""

    def test_create_zone(self, client: Client, staff_user):
        client.force_login(staff_user)
        resp = client.post(
            ZONE_CREATE_URL,
            json.dumps({"name": "Terrace", "description": "Outdoor area"}),
            content_type="application/json",
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["success"] is True
        assert data["zone"]["name"] == "Terrace"

    def test_create_zone_missing_name(self, client: Client, staff_user):
        client.force_login(staff_user)
        resp = client.post(
            ZONE_CREATE_URL,
            json.dumps({"name": ""}),
            content_type="application/json",
        )
        assert resp.status_code == 400

    def test_create_zone_invalid_json(self, client: Client, staff_user):
        client.force_login(staff_user)
        resp = client.post(
            ZONE_CREATE_URL,
            "not json",
            content_type="application/json",
        )
        assert resp.status_code == 400

    def test_edit_zone(self, client: Client, staff_user, zone):
        client.force_login(staff_user)
        resp = client.post(
            _zone_edit_url(zone.id),
            json.dumps({"name": "Updated Zone", "color": "#ff0000"}),
            content_type="application/json",
        )
        assert resp.status_code == 200
        assert resp.json()["success"] is True
        zone.refresh_from_db()
        assert zone.name == "Updated Zone"
        assert zone.color == "#ff0000"

    def test_edit_zone_partial_update(self, client: Client, staff_user, zone):
        """Only supplied fields should be updated."""
        client.force_login(staff_user)
        original_name = zone.name
        resp = client.post(
            _zone_edit_url(zone.id),
            json.dumps({"description": "new description"}),
            content_type="application/json",
        )
        assert resp.status_code == 200
        zone.refresh_from_db()
        assert zone.name == original_name
        assert zone.description == "new description"

    def test_delete_zone_soft_deletes(self, client: Client, staff_user, zone):
        client.force_login(staff_user)
        resp = client.post(_zone_delete_url(zone.id))
        assert resp.status_code == 200
        assert resp.json()["success"] is True

        # Verify soft-delete: deleted_at is set, record still exists
        zone.refresh_from_db()
        assert zone.deleted_at is not None

    def test_delete_zone_not_found_after_soft_delete(
        self, client: Client, staff_user, zone
    ):
        """A second delete on the same zone should 404 (already soft-deleted)."""
        client.force_login(staff_user)
        client.post(_zone_delete_url(zone.id))
        resp = client.post(_zone_delete_url(zone.id))
        assert resp.status_code == 404

    def test_edit_nonexistent_zone_returns_404(self, client: Client, staff_user):
        client.force_login(staff_user)
        resp = client.post(
            _zone_edit_url(uuid.uuid4()),
            json.dumps({"name": "Ghost"}),
            content_type="application/json",
        )
        assert resp.status_code == 404


# =========================================================================
# Table CRUD
# =========================================================================


@pytest.mark.django_db
class TestTableCRUD:
    """Table create / edit / delete operations."""

    def test_create_table(self, client: Client, staff_user, zone):
        client.force_login(staff_user)
        resp = client.post(
            TABLE_CREATE_URL,
            json.dumps({"name": "Table 10", "zone_id": str(zone.id)}),
            content_type="application/json",
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["success"] is True
        assert data["table"]["name"] == "Table 10"

    def test_create_table_missing_fields(self, client: Client, staff_user):
        client.force_login(staff_user)
        resp = client.post(
            TABLE_CREATE_URL,
            json.dumps({"name": "T1"}),
            content_type="application/json",
        )
        assert resp.status_code == 400

    def test_create_table_invalid_json(self, client: Client, staff_user):
        client.force_login(staff_user)
        resp = client.post(
            TABLE_CREATE_URL,
            "{bad",
            content_type="application/json",
        )
        assert resp.status_code == 400

    def test_edit_table(self, client: Client, staff_user, table):
        client.force_login(staff_user)
        resp = client.post(
            _table_edit_url(table.id),
            json.dumps({"name": "VIP Table", "capacity": 8, "status": "RESERVED"}),
            content_type="application/json",
        )
        assert resp.status_code == 200
        assert resp.json()["success"] is True
        table.refresh_from_db()
        assert table.name == "VIP Table"
        assert table.capacity == 8
        assert table.status == "RESERVED"

    def test_edit_table_invalid_status_ignored(self, client: Client, staff_user, table):
        """An invalid status value should be silently ignored."""
        client.force_login(staff_user)
        resp = client.post(
            _table_edit_url(table.id),
            json.dumps({"status": "INVALID_STATUS"}),
            content_type="application/json",
        )
        assert resp.status_code == 200
        table.refresh_from_db()
        assert table.status == "AVAILABLE"  # unchanged

    def test_delete_table_soft_deletes(self, client: Client, staff_user, table):
        client.force_login(staff_user)
        resp = client.post(_table_delete_url(table.id))
        assert resp.status_code == 200
        assert resp.json()["success"] is True

        table.refresh_from_db()
        assert table.deleted_at is not None

    def test_delete_table_twice_returns_404(self, client: Client, staff_user, table):
        client.force_login(staff_user)
        client.post(_table_delete_url(table.id))
        resp = client.post(_table_delete_url(table.id))
        assert resp.status_code == 404

    def test_edit_nonexistent_table_returns_404(self, client: Client, staff_user):
        client.force_login(staff_user)
        resp = client.post(
            _table_edit_url(uuid.uuid4()),
            json.dumps({"name": "Ghost"}),
            content_type="application/json",
        )
        assert resp.status_code == 404


# =========================================================================
# Table API (JSON endpoint)
# =========================================================================


@pytest.mark.django_db
class TestTableAPI:
    """The GET /account/api/tables/ endpoint returns JSON zones + tables."""

    def test_returns_json_structure(self, client: Client, staff_user, table):
        client.force_login(staff_user)
        resp = client.get(TABLE_API_URL)
        assert resp.status_code == 200
        data = resp.json()
        assert "zones" in data
        assert isinstance(data["zones"], list)
        assert len(data["zones"]) >= 1

        zone_data = data["zones"][0]
        assert "id" in zone_data
        assert "name" in zone_data
        assert "color" in zone_data
        assert "tables" in zone_data
        assert isinstance(zone_data["tables"], list)

    def test_table_fields_present(self, client: Client, staff_user, table):
        client.force_login(staff_user)
        resp = client.get(TABLE_API_URL)
        data = resp.json()
        tbl = data["zones"][0]["tables"][0]
        for field in ("id", "name", "number", "capacity", "status", "is_active"):
            assert field in tbl, f"Missing field: {field}"

    def test_empty_org_returns_empty_zones(self, client: Client, make_user, make_organization):
        """An org with no zones should return an empty list."""
        org = make_organization()
        u = make_user(organization=org)
        client.force_login(u)
        resp = client.get(TABLE_API_URL)
        assert resp.status_code == 200
        assert resp.json()["zones"] == []

    def test_soft_deleted_zones_excluded(self, client: Client, staff_user, zone):
        """Soft-deleted zones should not appear in the API response."""
        client.force_login(staff_user)
        zone.soft_delete()
        resp = client.get(TABLE_API_URL)
        data = resp.json()
        zone_ids = [z["id"] for z in data["zones"]]
        assert str(zone.id) not in zone_ids


# =========================================================================
# Tenant isolation
# =========================================================================


@pytest.mark.django_db
class TestTenantIsolation:
    """Users from org A must not see or modify org B's data."""

    def test_cannot_see_other_org_zones_in_api(
        self, client: Client, make_user, make_organization
    ):
        from apps.orders.models import Zone

        org_a = make_organization(name="Org A")
        org_b = make_organization(name="Org B")
        user_a = make_user(organization=org_a)

        Zone.objects.create(
            organization=org_b,
            name="Secret Zone",
            slug=f"secret-{uuid.uuid4().hex[:6]}",
            is_active=True,
        )

        client.force_login(user_a)
        resp = client.get(TABLE_API_URL)
        data = resp.json()
        zone_names = [z["name"] for z in data["zones"]]
        assert "Secret Zone" not in zone_names

    def test_cannot_edit_other_org_zone(
        self, client: Client, make_user, make_organization
    ):
        from apps.orders.models import Zone

        org_a = make_organization(name="Org A")
        org_b = make_organization(name="Org B")
        user_a = make_user(organization=org_a)

        zone_b = Zone.objects.create(
            organization=org_b,
            name="B Zone",
            slug=f"b-zone-{uuid.uuid4().hex[:6]}",
            is_active=True,
        )

        client.force_login(user_a)
        resp = client.post(
            _zone_edit_url(zone_b.id),
            json.dumps({"name": "Hacked"}),
            content_type="application/json",
        )
        assert resp.status_code == 404

    def test_cannot_delete_other_org_zone(
        self, client: Client, make_user, make_organization
    ):
        from apps.orders.models import Zone

        org_a = make_organization(name="Org A")
        org_b = make_organization(name="Org B")
        user_a = make_user(organization=org_a)

        zone_b = Zone.objects.create(
            organization=org_b,
            name="B Zone",
            slug=f"b-zone-{uuid.uuid4().hex[:6]}",
            is_active=True,
        )

        client.force_login(user_a)
        resp = client.post(_zone_delete_url(zone_b.id))
        assert resp.status_code == 404

    def test_cannot_edit_other_org_table(
        self, client: Client, make_user, make_organization
    ):
        from apps.orders.models import Table, Zone

        org_a = make_organization(name="Org A")
        org_b = make_organization(name="Org B")
        user_a = make_user(organization=org_a)

        zone_b = Zone.objects.create(
            organization=org_b,
            name="B Zone",
            slug=f"b-zone-{uuid.uuid4().hex[:6]}",
            is_active=True,
        )
        table_b = Table.objects.create(
            organization=org_b,
            zone=zone_b,
            name="B Table",
            number="99",
            capacity=2,
            status="AVAILABLE",
        )

        client.force_login(user_a)
        resp = client.post(
            _table_edit_url(table_b.id),
            json.dumps({"name": "Hacked Table"}),
            content_type="application/json",
        )
        assert resp.status_code == 404

    def test_cannot_delete_other_org_table(
        self, client: Client, make_user, make_organization
    ):
        from apps.orders.models import Table, Zone

        org_a = make_organization(name="Org A")
        org_b = make_organization(name="Org B")
        user_a = make_user(organization=org_a)

        zone_b = Zone.objects.create(
            organization=org_b,
            name="B Zone",
            slug=f"b-zone-{uuid.uuid4().hex[:6]}",
            is_active=True,
        )
        table_b = Table.objects.create(
            organization=org_b,
            zone=zone_b,
            name="B Table",
            number="99",
            capacity=2,
            status="AVAILABLE",
        )

        client.force_login(user_a)
        resp = client.post(_table_delete_url(table_b.id))
        assert resp.status_code == 404
