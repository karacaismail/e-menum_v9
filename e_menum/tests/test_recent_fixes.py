"""
Tests for recent bugfixes (March 2026):

1. Team Invite 500 Error — global email unique constraint handling
   - Fresh invite (new email)
   - Duplicate email in same org (active) → error message
   - Soft-deleted user in same org → restore / re-invite
   - Active user in different org → error message
   - Soft-deleted user in different org → reassign to current org
   - Invalid role_id → handled gracefully

2. Table Management — soft-delete filtering in zone prefetch
   - Deleted tables excluded from zone listing
   - Active tables still shown

3. QR Code Target URL — menu slug routing
   - MENU type with linked menu → /m/<slug>/
   - TABLE type with linked menu → /m/<slug>/?table=<id>
   - No linked menu → /q/<code>/
   - Custom redirect_url → used as-is

4. QR Redirect View — /q/<code>/ short-URL handler
   - Active QR with menu → 302 redirect
   - Inactive QR → 404
   - Non-existent code → 404
   - QR without menu (no redirect target) → 404

Uses pytest-django with Factory Boy factories and Django test Client.
"""

import json

import pytest
from django.urls import resolve

from apps.core.choices import RoleScope, UserStatus
from apps.core.models import Role, User, UserRole
from tests.factories.core import OrganizationFactory, UserFactory
from tests.factories.orders import QRCodeFactory, TableFactory, ZoneFactory

pytestmark = pytest.mark.django_db


# =============================================================================
# SHARED FIXTURES
# =============================================================================


@pytest.fixture(autouse=True)
def _disable_canonical_redirect(settings):
    """Disable CanonicalDomainMiddleware redirect for test client."""
    settings.SEO_CANONICAL_DOMAIN = ""


@pytest.fixture
def org(db):
    """Primary test organization."""
    return OrganizationFactory(name="Test Restaurant")


@pytest.fixture
def org2(db):
    """Secondary test organization for cross-org tests."""
    return OrganizationFactory(name="Other Restaurant")


@pytest.fixture
def owner(db, org):
    """Owner user belonging to primary org."""
    return UserFactory(
        email="owner@test.com",
        password="TestPass1234!",
        organization=org,
        status="ACTIVE",
    )


@pytest.fixture
def org_role(db):
    """Organization-scoped role for assignment tests."""
    role, _ = Role.objects.get_or_create(
        name="staff",
        scope=RoleScope.ORGANIZATION,
        defaults={
            "display_name": "Staff",
            "is_system": True,
        },
    )
    return role


@pytest.fixture
def logged_in_client(client, owner):
    """Django test client logged in as owner."""
    client.force_login(owner)
    return client


# =============================================================================
# 1. TEAM INVITE — email unique constraint handling
# =============================================================================


class TestTeamInviteFreshUser:
    """Inviting a brand-new email address should create a user."""

    def test_invite_creates_user(self, logged_in_client, org, org_role):
        """POST to team-invite with a new email → user created, redirect."""
        resp = logged_in_client.post(
            "/account/team/invite/",
            {
                "email": "newhire@example.com",
                "first_name": "Yeni",
                "last_name": "Calisan",
                "role_id": str(org_role.pk),
            },
        )
        assert resp.status_code == 302
        user = User.objects.get(email="newhire@example.com")
        assert user.organization == org
        assert user.status == UserStatus.INVITED
        assert user.first_name == "Yeni"

    def test_invite_assigns_role(self, logged_in_client, org, org_role):
        """Invited user should be assigned the specified role."""
        logged_in_client.post(
            "/account/team/invite/",
            {
                "email": "roleduser@example.com",
                "first_name": "Rol",
                "last_name": "Test",
                "role_id": str(org_role.pk),
            },
        )
        user = User.objects.get(email="roleduser@example.com")
        assert UserRole.objects.filter(
            user=user, role=org_role, organization=org
        ).exists()


class TestTeamInviteDuplicateActiveInSameOrg:
    """Inviting an email that already belongs to an active user in this org."""

    def test_duplicate_active_same_org_shows_error(self, logged_in_client, org):
        """Should redirect with an error message, not create a duplicate."""
        UserFactory(email="existing@example.com", organization=org, status="ACTIVE")

        resp = logged_in_client.post(
            "/account/team/invite/",
            {
                "email": "existing@example.com",
                "first_name": "Duplicate",
                "last_name": "User",
            },
        )
        assert resp.status_code == 302
        # Only one user with this email should exist
        assert User.objects.filter(email="existing@example.com").count() == 1


class TestTeamInviteSoftDeletedSameOrg:
    """Inviting an email of a previously-removed user in this org → restore."""

    def test_soft_deleted_same_org_restores_user(self, logged_in_client, org):
        """Soft-deleted user should be restored with INVITED status."""
        old_user = UserFactory(
            email="removed@example.com",
            organization=org,
            status="ACTIVE",
        )
        old_user.soft_delete()
        old_user.refresh_from_db()
        assert old_user.deleted_at is not None

        resp = logged_in_client.post(
            "/account/team/invite/",
            {
                "email": "removed@example.com",
                "first_name": "Restored",
                "last_name": "User",
            },
        )
        assert resp.status_code == 302

        old_user.refresh_from_db()
        assert old_user.deleted_at is None
        assert old_user.status == UserStatus.INVITED
        assert old_user.first_name == "Restored"
        assert old_user.is_active is True


class TestTeamInviteActiveInDifferentOrg:
    """Inviting an email that belongs to an active user in another org."""

    def test_active_different_org_shows_error(self, logged_in_client, org2):
        """Should show error, not create user or reassign."""
        UserFactory(
            email="otherorg@example.com",
            organization=org2,
            status="ACTIVE",
        )

        resp = logged_in_client.post(
            "/account/team/invite/",
            {
                "email": "otherorg@example.com",
                "first_name": "Cross",
                "last_name": "Org",
            },
        )
        assert resp.status_code == 302
        # User should still belong to org2
        user = User.objects.get(email="otherorg@example.com")
        assert user.organization == org2


class TestTeamInviteSoftDeletedDifferentOrg:
    """Inviting a soft-deleted user from another org → reassign."""

    def test_soft_deleted_different_org_reassigns(self, logged_in_client, org, org2):
        """Soft-deleted user from another org should be reassigned."""
        old_user = UserFactory(
            email="movable@example.com",
            organization=org2,
            status="ACTIVE",
        )
        old_user.soft_delete()

        resp = logged_in_client.post(
            "/account/team/invite/",
            {
                "email": "movable@example.com",
                "first_name": "Moved",
                "last_name": "User",
            },
        )
        assert resp.status_code == 302

        old_user.refresh_from_db()
        assert old_user.deleted_at is None
        assert old_user.organization == org
        assert old_user.status == UserStatus.INVITED
        assert old_user.first_name == "Moved"


class TestTeamInviteValidation:
    """Input validation edge cases."""

    def test_missing_fields_returns_redirect(self, logged_in_client):
        """Missing email/name should redirect with error, not 500."""
        resp = logged_in_client.post(
            "/account/team/invite/",
            {"email": "", "first_name": "", "last_name": ""},
        )
        assert resp.status_code == 302

    def test_invalid_role_id_does_not_crash(self, logged_in_client):
        """Invalid UUID as role_id should be handled gracefully."""
        resp = logged_in_client.post(
            "/account/team/invite/",
            {
                "email": "badrole@example.com",
                "first_name": "Bad",
                "last_name": "Role",
                "role_id": "not-a-uuid",
            },
        )
        assert resp.status_code == 302
        # User should still be created (role assignment silently skipped)
        assert User.objects.filter(email="badrole@example.com").exists()

    def test_get_request_returns_405(self, logged_in_client):
        """GET on a @require_POST view should return 405."""
        resp = logged_in_client.get("/account/team/invite/")
        assert resp.status_code == 405

    def test_anonymous_redirects_to_login(self, client):
        """Anonymous POST should redirect to login."""
        resp = client.post(
            "/account/team/invite/",
            {
                "email": "anon@example.com",
                "first_name": "Anon",
                "last_name": "User",
            },
        )
        assert resp.status_code == 302
        assert "login" in resp.url


# =============================================================================
# 2. TABLE MANAGEMENT — soft-delete filtering
# =============================================================================


class TestTableSoftDeleteFiltering:
    """Soft-deleted tables should not appear in zone listing."""

    def test_deleted_tables_excluded_from_management_page(self, logged_in_client, org):
        """GET /account/tables/ should not show soft-deleted tables."""
        zone = ZoneFactory(organization=org, name="Main Hall")
        TableFactory(zone=zone, name="Active Table")
        t2 = TableFactory(zone=zone, name="Deleted Table")
        t2.soft_delete()

        resp = logged_in_client.get("/account/tables/")
        assert resp.status_code == 200
        content = resp.content.decode()
        assert "Active Table" in content
        assert "Deleted Table" not in content

    def test_active_tables_shown_in_management_page(self, logged_in_client, org):
        """Active tables should be visible on the management page."""
        zone = ZoneFactory(organization=org, name="Garden")
        TableFactory(zone=zone, name="Table Alpha")
        TableFactory(zone=zone, name="Table Beta")

        resp = logged_in_client.get("/account/tables/")
        assert resp.status_code == 200
        content = resp.content.decode()
        assert "Table Alpha" in content
        assert "Table Beta" in content

    def test_deleted_zones_excluded(self, logged_in_client, org):
        """Soft-deleted zones should not appear on the page."""
        ZoneFactory(organization=org, name="Active Zone")
        z2 = ZoneFactory(organization=org, name="Deleted Zone")
        z2.soft_delete()

        resp = logged_in_client.get("/account/tables/")
        assert resp.status_code == 200
        content = resp.content.decode()
        assert "Active Zone" in content
        assert "Deleted Zone" not in content


# =============================================================================
# 3. QR CODE TARGET URL — menu slug routing
# =============================================================================


class TestQRCodeTargetURL:
    """Tests for QRGeneratorService.get_target_url() routing logic."""

    def test_menu_type_with_linked_menu(self, org, settings):
        """MENU QR with a linked menu should generate /m/<slug>/ URL."""
        from apps.menu.models import Menu
        from apps.orders.services.qr_generator import QRGeneratorService

        settings.SITE_URL = "https://e-menum.net"

        menu = Menu.objects.create(
            organization=org,
            name="Lunch Menu",
            slug="lunch-menu",
            is_published=True,
        )
        qr = QRCodeFactory(organization=org, type="MENU", menu=menu)

        url = QRGeneratorService.get_target_url(qr)
        assert url == "https://e-menum.net/m/lunch-menu/"

    def test_table_type_with_linked_menu_and_table(self, org, settings):
        """TABLE QR with menu should generate /m/<slug>/?table=<id> URL."""
        from apps.menu.models import Menu
        from apps.orders.services.qr_generator import QRGeneratorService

        settings.SITE_URL = "https://e-menum.net"

        menu = Menu.objects.create(
            organization=org,
            name="Dinner Menu",
            slug="dinner-menu",
            is_published=True,
        )
        zone = ZoneFactory(organization=org)
        table = TableFactory(zone=zone)
        qr = QRCodeFactory(organization=org, type="TABLE", menu=menu, table=table)

        url = QRGeneratorService.get_target_url(qr)
        assert url.startswith("https://e-menum.net/m/dinner-menu/")
        assert f"?table={table.pk}" in url

    def test_no_linked_menu_falls_back_to_short_url(self, org, settings):
        """QR without menu should fall back to /q/<code>/ URL."""
        from apps.orders.services.qr_generator import QRGeneratorService

        settings.SITE_URL = "https://e-menum.net"

        qr = QRCodeFactory(organization=org, type="MENU")
        # No menu linked

        url = QRGeneratorService.get_target_url(qr)
        assert url == f"https://e-menum.net/q/{qr.code}/"

    def test_redirect_url_takes_priority(self, org, settings):
        """Custom redirect_url should override all other logic."""
        from apps.orders.services.qr_generator import QRGeneratorService

        settings.SITE_URL = "https://e-menum.net"

        qr = QRCodeFactory(organization=org, type="MENU")
        qr.redirect_url = "https://custom.com/my-menu/"
        qr.save(update_fields=["redirect_url"])

        url = QRGeneratorService.get_target_url(qr)
        assert url == "https://custom.com/my-menu/"


# =============================================================================
# 4. QR REDIRECT VIEW — /q/<code>/ handler
# =============================================================================


class TestQRRedirectView:
    """Tests for the /q/<code>/ short-URL redirect handler."""

    def test_url_resolves(self):
        """The /q/<code>/ URL should resolve to the redirect view."""
        match = resolve("/q/TESTCODE/")
        assert match is not None
        assert match.url_name == "qr-short-url"

    def test_active_qr_with_menu_redirects(self, client, org, settings):
        """Active QR code with a linked menu should 302 redirect."""
        from apps.menu.models import Menu

        settings.SITE_URL = "https://e-menum.net"

        menu = Menu.objects.create(
            organization=org,
            name="QR Menu",
            slug="qr-test-menu",
            is_published=True,
        )
        qr = QRCodeFactory(organization=org, type="MENU", menu=menu, is_active=True)

        resp = client.get(f"/q/{qr.code}/")
        assert resp.status_code == 302
        assert "/m/qr-test-menu/" in resp.url

    def test_inactive_qr_returns_404(self, client, org):
        """Inactive QR code should return 404."""
        qr = QRCodeFactory(organization=org, type="MENU", is_active=False)

        resp = client.get(f"/q/{qr.code}/")
        assert resp.status_code == 404

    def test_nonexistent_code_returns_404(self, client):
        """Non-existent QR code should return 404."""
        resp = client.get("/q/NONEXIST/")
        assert resp.status_code == 404

    def test_qr_without_menu_returns_404(self, client, org, settings):
        """QR without linked menu (fallback = self-referencing /q/) → 404."""
        settings.SITE_URL = "https://e-menum.net"
        qr = QRCodeFactory(organization=org, type="MENU", is_active=True)
        # No menu linked → get_target_url returns /q/<code>/ → infinite loop detection → 404

        resp = client.get(f"/q/{qr.code}/")
        assert resp.status_code == 404

    def test_soft_deleted_qr_returns_404(self, client, org):
        """Soft-deleted QR code should return 404."""
        from apps.menu.models import Menu

        menu = Menu.objects.create(
            organization=org,
            name="Deleted QR Menu",
            slug="deleted-qr-menu",
            is_published=True,
        )
        qr = QRCodeFactory(organization=org, type="MENU", menu=menu, is_active=True)
        qr.soft_delete()

        resp = client.get(f"/q/{qr.code}/")
        assert resp.status_code == 404


# =============================================================================
# 5. QR CREATE VIEW — image generation on create
# =============================================================================


class TestQRCodeCreateGeneratesImage:
    """QR code creation should trigger image generation."""

    def test_create_qr_via_api_returns_201(self, logged_in_client, org):
        """POST to qrcode-create-api should return 201."""
        from apps.menu.models import Menu

        menu = Menu.objects.create(
            organization=org,
            name="API Test Menu",
            slug="api-test-menu",
            is_published=True,
        )

        resp = logged_in_client.post(
            "/account/api/qrcodes/",
            data=json.dumps(
                {
                    "qr_type": "MENU",
                    "name": "Test API QR",
                    "menu_id": str(menu.pk),
                }
            ),
            content_type="application/json",
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data.get("success") is True
        assert "qr" in data
        assert "id" in data["qr"]
