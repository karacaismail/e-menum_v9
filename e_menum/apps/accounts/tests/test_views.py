"""
Tests for the restaurant account portal views.

Tests cover:
- URL resolution → all routes resolve to English paths (/account/...)
- Login flow    → email login, username login, invalid credentials, redirect after login
- Logout flow   → session cleared, redirect to login
- Profile page  → requires auth, displays user info, form submission updates profile
- Settings page → requires auth, username change, password change
- Auth backend  → EmailOrUsernameBackend authenticate() method
- Access control → anonymous users are redirected to login with ?next= parameter

Uses pytest-django with Django test Client and Factory Boy factories.
"""

import pytest
from django.test import Client
from django.urls import reverse

from tests.factories.core import UserFactory


# Apply django_db marker to all tests in this module
pytestmark = pytest.mark.django_db


# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture(autouse=True)
def _disable_canonical_redirect(settings):
    """Disable CanonicalDomainMiddleware redirect for test client (Host: testserver)."""
    settings.SEO_CANONICAL_DOMAIN = ""


@pytest.fixture
def anon_client():
    """Return an unauthenticated Django test Client."""
    return Client()


@pytest.fixture
def user_with_password(db):
    """Create a user with a known password."""
    return UserFactory(password="SecurePass123!")


@pytest.fixture
def user_with_username(db):
    """Create a user with both email and username set."""
    return UserFactory(password="SecurePass123!", username="testuser")


@pytest.fixture
def authed_client(db, user_with_password):
    """Return a Django test Client logged in as user_with_password."""
    client = Client()
    client.force_login(user_with_password)
    return client


# =============================================================================
# URL RESOLUTION TESTS — English paths
# =============================================================================


class TestURLResolution:
    """All account URLs must resolve to English paths under /account/."""

    def test_login_url_resolves(self):
        url = reverse("accounts:login")
        assert url == "/account/login/"

    def test_logout_url_resolves(self):
        url = reverse("accounts:logout")
        assert url == "/account/logout/"

    def test_profile_url_resolves(self):
        url = reverse("accounts:profile")
        assert url == "/account/profile/"

    def test_settings_url_resolves(self):
        url = reverse("accounts:settings")
        assert url == "/account/settings/"

    def test_no_turkish_slugs_in_urls(self):
        """Verify no Turkish-only path segments remain in account URLs."""
        urls = [
            reverse("accounts:login"),
            reverse("accounts:logout"),
            reverse("accounts:profile"),
            reverse("accounts:settings"),
        ]
        # Check each URL segment individually (split by /)
        turkish_only = {"hesap", "giris", "cikis", "ayarlar"}
        for url in urls:
            segments = [s for s in url.split("/") if s]
            for seg in segments:
                assert seg not in turkish_only, (
                    f'Turkish segment "{seg}" found in URL: {url}'
                )


# =============================================================================
# LOGIN VIEW TESTS
# =============================================================================


class TestLoginView:
    """Tests for AccountLoginView — GET and POST."""

    def test_login_page_renders(self, anon_client):
        """GET /account/login/ returns 200 with login form."""
        resp = anon_client.get(reverse("accounts:login"))
        assert resp.status_code == 200
        assert b"csrfmiddlewaretoken" in resp.content

    def test_login_with_email(self, anon_client, user_with_password):
        """POST with valid email + password → 302 redirect to profile."""
        resp = anon_client.post(
            reverse("accounts:login"),
            {
                "identifier": user_with_password.email,
                "password": "SecurePass123!",
            },
        )
        assert resp.status_code == 302
        assert reverse("accounts:profile") in resp.url

    def test_login_with_username(self, anon_client, user_with_username):
        """POST with valid username + password → 302 redirect to profile."""
        resp = anon_client.post(
            reverse("accounts:login"),
            {
                "identifier": "testuser",
                "password": "SecurePass123!",
            },
        )
        assert resp.status_code == 302
        assert reverse("accounts:profile") in resp.url

    def test_login_invalid_password(self, anon_client, user_with_password):
        """POST with wrong password → stays on login page (200)."""
        resp = anon_client.post(
            reverse("accounts:login"),
            {
                "identifier": user_with_password.email,
                "password": "WrongPassword999!",
            },
        )
        assert resp.status_code == 200

    def test_login_nonexistent_user(self, anon_client):
        """POST with unknown email → stays on login page (200)."""
        resp = anon_client.post(
            reverse("accounts:login"),
            {
                "identifier": "nobody@nowhere.com",
                "password": "SomePassword123!",
            },
        )
        assert resp.status_code == 200

    def test_login_redirects_authenticated_user(self, authed_client):
        """Authenticated user visiting login page gets redirected to profile."""
        resp = authed_client.get(reverse("accounts:login"))
        assert resp.status_code == 302
        assert reverse("accounts:profile") in resp.url

    def test_login_next_parameter(self, anon_client, user_with_password):
        """Login with ?next= parameter redirects to that URL after success."""
        settings_url = reverse("accounts:settings")
        resp = anon_client.post(
            reverse("accounts:login") + f"?next={settings_url}",
            {
                "identifier": user_with_password.email,
                "password": "SecurePass123!",
            },
        )
        assert resp.status_code == 302
        assert settings_url in resp.url


# =============================================================================
# LOGOUT VIEW TESTS
# =============================================================================


class TestLogoutView:
    """Tests for AccountLogoutView."""

    def test_logout_clears_session(self, authed_client):
        """GET /account/logout/ logs out and redirects to login."""
        resp = authed_client.get(reverse("accounts:logout"))
        assert resp.status_code == 302
        assert reverse("accounts:login") in resp.url

        # After logout, profile should require login again
        profile_resp = authed_client.get(reverse("accounts:profile"))
        assert profile_resp.status_code == 302

    def test_logout_post(self, authed_client):
        """POST /account/logout/ also works."""
        resp = authed_client.post(reverse("accounts:logout"))
        assert resp.status_code == 302
        assert reverse("accounts:login") in resp.url


# =============================================================================
# ACCESS CONTROL TESTS
# =============================================================================


class TestAccessControl:
    """Protected pages redirect anonymous users to login."""

    def test_profile_requires_login(self, anon_client):
        """Anonymous user on /account/profile/ → redirect to login with ?next=."""
        resp = anon_client.get(reverse("accounts:profile"))
        assert resp.status_code == 302
        assert "login" in resp.url
        assert "next=" in resp.url

    def test_settings_requires_login(self, anon_client):
        """Anonymous user on /account/settings/ → redirect to login with ?next=."""
        resp = anon_client.get(reverse("accounts:settings"))
        assert resp.status_code == 302
        assert "login" in resp.url
        assert "next=" in resp.url


# =============================================================================
# PROFILE VIEW TESTS
# =============================================================================


class TestProfileView:
    """Tests for ProfileView — personal info editing."""

    def test_profile_renders_for_authenticated_user(
        self, authed_client, user_with_password
    ):
        """GET /account/profile/ shows profile form for logged-in user."""
        resp = authed_client.get(reverse("accounts:profile"))
        assert resp.status_code == 200
        assert user_with_password.email.encode() in resp.content

    def test_profile_update_name(self, authed_client, user_with_password):
        """POST updates first_name and last_name."""
        resp = authed_client.post(
            reverse("accounts:profile"),
            {
                "first_name": "Yeni",
                "last_name": "İsim",
                "phone": "",
                "avatar": "",
            },
        )
        assert resp.status_code == 302
        user_with_password.refresh_from_db()
        assert user_with_password.first_name == "Yeni"
        assert user_with_password.last_name == "İsim"


# =============================================================================
# SETTINGS VIEW TESTS
# =============================================================================


class TestSettingsView:
    """Tests for AccountSettingsView — username, password, sessions."""

    def test_settings_renders(self, authed_client, user_with_password):
        """GET /account/settings/ shows settings page."""
        resp = authed_client.get(reverse("accounts:settings"))
        assert resp.status_code == 200
        assert user_with_password.email.encode() in resp.content

    def test_change_username(self, authed_client, user_with_password):
        """POST with action=change_username updates username."""
        resp = authed_client.post(
            reverse("accounts:settings"),
            {
                "action": "change_username",
                "username": "new_username",
            },
        )
        assert resp.status_code == 302
        user_with_password.refresh_from_db()
        assert user_with_password.username == "new_username"

    def test_change_username_invalid(self, authed_client, user_with_password):
        """POST with invalid username (too short) re-renders form."""
        resp = authed_client.post(
            reverse("accounts:settings"),
            {
                "action": "change_username",
                "username": "ab",
            },
        )
        assert resp.status_code == 200

    def test_change_password(self, authed_client, user_with_password):
        """POST with action=change_password updates password."""
        resp = authed_client.post(
            reverse("accounts:settings"),
            {
                "action": "change_password",
                "current_password": "SecurePass123!",
                "new_password": "NewSecurePass456!",
                "confirm_password": "NewSecurePass456!",
            },
        )
        assert resp.status_code == 302
        user_with_password.refresh_from_db()
        assert user_with_password.check_password("NewSecurePass456!")

    def test_change_password_wrong_current(self, authed_client, user_with_password):
        """POST with wrong current password re-renders form."""
        resp = authed_client.post(
            reverse("accounts:settings"),
            {
                "action": "change_password",
                "current_password": "WrongPassword!",
                "new_password": "NewSecurePass456!",
                "confirm_password": "NewSecurePass456!",
            },
        )
        assert resp.status_code == 200

    def test_change_password_mismatch(self, authed_client, user_with_password):
        """POST with non-matching new passwords re-renders form."""
        resp = authed_client.post(
            reverse("accounts:settings"),
            {
                "action": "change_password",
                "current_password": "SecurePass123!",
                "new_password": "NewSecurePass456!",
                "confirm_password": "DifferentPass789!",
            },
        )
        assert resp.status_code == 200


# =============================================================================
# AUTH BACKEND TESTS
# =============================================================================


class TestEmailOrUsernameBackend:
    """Tests for the custom authentication backend."""

    def test_authenticate_with_email(self, user_with_password):
        from django.contrib.auth import authenticate

        user = authenticate(
            username=user_with_password.email, password="SecurePass123!"
        )
        assert user is not None
        assert user.pk == user_with_password.pk

    def test_authenticate_with_username(self, user_with_username):
        from django.contrib.auth import authenticate

        user = authenticate(username="testuser", password="SecurePass123!")
        assert user is not None
        assert user.pk == user_with_username.pk

    def test_authenticate_case_insensitive_email(self, user_with_password):
        from django.contrib.auth import authenticate

        upper_email = user_with_password.email.upper()
        user = authenticate(username=upper_email, password="SecurePass123!")
        assert user is not None

    def test_authenticate_case_insensitive_username(self, user_with_username):
        from django.contrib.auth import authenticate

        user = authenticate(username="TESTUSER", password="SecurePass123!")
        assert user is not None

    def test_authenticate_wrong_password_returns_none(self, user_with_password):
        from django.contrib.auth import authenticate

        user = authenticate(username=user_with_password.email, password="WrongPass!")
        assert user is None

    def test_authenticate_nonexistent_user_returns_none(self, db):
        from django.contrib.auth import authenticate

        user = authenticate(username="ghost@nowhere.com", password="anything")
        assert user is None

    def test_authenticate_empty_identifier_returns_none(self, db):
        from django.contrib.auth import authenticate

        user = authenticate(username="", password="anything")
        assert user is None

    def test_authenticate_none_returns_none(self, db):
        from django.contrib.auth import authenticate

        user = authenticate(username=None, password=None)
        assert user is None
