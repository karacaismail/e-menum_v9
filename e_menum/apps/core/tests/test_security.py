"""Security tests for access control."""

import uuid

import pytest

from apps.core.models import User


@pytest.mark.django_db
class TestSuperadminAccess:
    """Verify restaurant admins cannot access superadmin panel (P12 fix)."""

    ADMIN_URLS = [
        "/admin/dashboard/",
        "/admin/reports/",
        "/admin/seo-dashboard/",
        "/admin/settings/",
    ]

    def test_anonymous_redirected_from_admin(self, client):
        for url in self.ADMIN_URLS:
            response = client.get(url)
            assert response.status_code in (301, 302), (
                f"Anonymous user should be redirected from {url}"
            )

    def test_regular_user_blocked_from_admin(self, client):
        user = User.objects.create_user(
            email=f"regular_{uuid.uuid4().hex[:6]}@example.com",
            password="TestPass123!",
            is_staff=False,
        )
        client.force_login(user)
        for url in self.ADMIN_URLS:
            response = client.get(url)
            assert response.status_code in (302, 403), (
                f"Regular user should not access {url}"
            )

    def test_staff_user_blocked_from_admin(self, client):
        """Restaurant owners have is_staff=True but should NOT access superadmin."""
        user = User.objects.create_user(
            email=f"staff_{uuid.uuid4().hex[:6]}@example.com",
            password="TestPass123!",
            is_staff=True,
            is_superuser=False,
        )
        client.force_login(user)
        for url in self.ADMIN_URLS:
            response = client.get(url)
            assert response.status_code in (302, 403), (
                f"Staff (non-superuser) should not access {url}, got {response.status_code}"
            )

    def test_superuser_can_access_admin(self, client, admin_user):
        client.force_login(admin_user)
        response = client.get("/admin/dashboard/")
        assert response.status_code == 200, "Superuser should access admin dashboard"


@pytest.mark.django_db
class TestRestaurantPortalAccess:
    """Verify restaurant portal requires login."""

    PORTAL_URLS = [
        "/account/profile/",
        "/account/menus/",
        "/account/subscription/",
    ]

    def test_anonymous_redirected_from_portal(self, client):
        for url in self.PORTAL_URLS:
            response = client.get(url)
            assert response.status_code in (301, 302), (
                f"Anonymous user should be redirected from {url}"
            )
