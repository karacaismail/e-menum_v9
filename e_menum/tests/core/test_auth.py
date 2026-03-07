"""
Integration tests for authentication flow.

These tests verify the complete authentication lifecycle including:
- Login with email/password
- JWT token generation and refresh
- Logout and token blacklisting
- User profile retrieval and update
- Password change
- Session management

Run with:
    pytest tests/core/test_auth.py -v
"""

import uuid

import pytest
from django.utils import timezone
from rest_framework import status

from apps.core.models import Session
from apps.core.choices import UserStatus, OrganizationStatus, SessionStatus
from tests.factories.core import (
    OrganizationFactory,
    UserFactory,
)


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================


def get_login_url():
    """Return the login URL."""
    return "/api/v1/auth/login/"


def get_logout_url():
    """Return the logout URL."""
    return "/api/v1/auth/logout/"


def get_refresh_url():
    """Return the token refresh URL."""
    return "/api/v1/auth/refresh/"


def get_verify_url():
    """Return the token verify URL."""
    return "/api/v1/auth/verify/"


def get_me_url():
    """Return the user profile URL."""
    return "/api/v1/auth/me/"


def get_password_url():
    """Return the password change URL."""
    return "/api/v1/auth/password/"


def get_sessions_url():
    """Return the sessions list URL."""
    return "/api/v1/auth/sessions/"


def get_session_revoke_url(session_id):
    """Return the session revoke URL."""
    return f"/api/v1/auth/sessions/{session_id}/"


def get_sessions_revoke_all_url():
    """Return the revoke all sessions URL."""
    return "/api/v1/auth/sessions/revoke-all/"


# =============================================================================
# LOGIN TESTS
# =============================================================================


@pytest.mark.django_db
class TestLogin:
    """Test cases for login endpoint."""

    def test_login_success(self, api_client):
        """Test successful login with valid credentials."""
        # Create user with known password
        password = "SecurePassword123!"
        user = UserFactory(password=password, status=UserStatus.ACTIVE)

        response = api_client.post(
            get_login_url(),
            {
                "email": user.email,
                "password": password,
            },
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] is True
        assert "data" in response.data
        assert "access" in response.data["data"]
        assert "refresh" in response.data["data"]
        assert "user" in response.data["data"]
        assert response.data["data"]["user"]["email"] == user.email

    def test_login_success_with_organization(self, api_client):
        """Test login returns organization info when user has one."""
        password = "SecurePassword123!"
        org = OrganizationFactory(status=OrganizationStatus.ACTIVE)
        user = UserFactory(
            password=password, status=UserStatus.ACTIVE, organization=org
        )

        response = api_client.post(
            get_login_url(),
            {
                "email": user.email,
                "password": password,
            },
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] is True
        assert "organization" in response.data["data"]
        assert response.data["data"]["organization"] is not None
        assert response.data["data"]["organization"]["id"] == str(org.id)
        assert response.data["data"]["organization"]["name"] == org.name

    def test_login_creates_session(self, api_client):
        """Test that login creates a session record."""
        password = "SecurePassword123!"
        user = UserFactory(password=password, status=UserStatus.ACTIVE)

        # Count sessions before login
        session_count_before = Session.objects.filter(user=user).count()

        response = api_client.post(
            get_login_url(),
            {
                "email": user.email,
                "password": password,
            },
        )

        assert response.status_code == status.HTTP_200_OK

        # Verify session was created
        session_count_after = Session.objects.filter(user=user).count()
        assert session_count_after == session_count_before + 1

        # Verify session has correct status
        session = Session.objects.filter(user=user).latest("created_at")
        assert session.status == SessionStatus.ACTIVE

    def test_login_updates_last_login_at(self, api_client):
        """Test that login updates user's last_login_at timestamp."""
        password = "SecurePassword123!"
        user = UserFactory(
            password=password, status=UserStatus.ACTIVE, last_login_at=None
        )

        before_login = timezone.now()
        response = api_client.post(
            get_login_url(),
            {
                "email": user.email,
                "password": password,
            },
        )

        assert response.status_code == status.HTTP_200_OK

        user.refresh_from_db()
        assert user.last_login_at is not None
        assert user.last_login_at >= before_login

    def test_login_invalid_password(self, api_client):
        """Test login fails with incorrect password."""
        user = UserFactory(password="CorrectPassword123!", status=UserStatus.ACTIVE)

        response = api_client.post(
            get_login_url(),
            {
                "email": user.email,
                "password": "WrongPassword123!",
            },
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.data["success"] is False
        assert "error" in response.data

    def test_login_nonexistent_email(self, api_client):
        """Test login fails with non-existent email."""
        response = api_client.post(
            get_login_url(),
            {
                "email": "nonexistent@example.com",
                "password": "AnyPassword123!",
            },
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.data["success"] is False
        assert "error" in response.data

    def test_login_suspended_user(self, api_client):
        """Test login fails for suspended user."""
        password = "SecurePassword123!"
        user = UserFactory(password=password, status=UserStatus.SUSPENDED)

        response = api_client.post(
            get_login_url(),
            {
                "email": user.email,
                "password": password,
            },
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.data["success"] is False

    def test_login_invited_user(self, api_client):
        """Test login fails for user with INVITED status."""
        password = "SecurePassword123!"
        user = UserFactory(password=password, status=UserStatus.INVITED)

        response = api_client.post(
            get_login_url(),
            {
                "email": user.email,
                "password": password,
            },
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.data["success"] is False

    def test_login_deleted_user(self, api_client):
        """Test login fails for soft-deleted user."""
        password = "SecurePassword123!"
        user = UserFactory(password=password, status=UserStatus.ACTIVE)
        user.soft_delete()

        response = api_client.post(
            get_login_url(),
            {
                "email": user.email,
                "password": password,
            },
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.data["success"] is False

    def test_login_suspended_organization(self, api_client):
        """Test login fails when user's organization is suspended."""
        password = "SecurePassword123!"
        org = OrganizationFactory(status=OrganizationStatus.SUSPENDED)
        user = UserFactory(
            password=password, status=UserStatus.ACTIVE, organization=org
        )

        response = api_client.post(
            get_login_url(),
            {
                "email": user.email,
                "password": password,
            },
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.data["success"] is False

    def test_login_case_insensitive_email(self, api_client):
        """Test login is case-insensitive for email."""
        password = "SecurePassword123!"
        UserFactory(
            email="test.user@example.com", password=password, status=UserStatus.ACTIVE
        )

        response = api_client.post(
            get_login_url(),
            {
                "email": "TEST.USER@EXAMPLE.COM",
                "password": password,
            },
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] is True

    def test_login_missing_email(self, api_client):
        """Test login fails when email is missing."""
        response = api_client.post(
            get_login_url(),
            {
                "password": "SomePassword123!",
            },
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.data["success"] is False

    def test_login_missing_password(self, api_client):
        """Test login fails when password is missing."""
        user = UserFactory(status=UserStatus.ACTIVE)

        response = api_client.post(
            get_login_url(),
            {
                "email": user.email,
            },
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.data["success"] is False


# =============================================================================
# LOGOUT TESTS
# =============================================================================


@pytest.mark.django_db
class TestLogout:
    """Test cases for logout endpoint."""

    def test_logout_success(self, api_client):
        """Test successful logout with valid refresh token."""
        # Login first
        password = "SecurePassword123!"
        user = UserFactory(password=password, status=UserStatus.ACTIVE)

        login_response = api_client.post(
            get_login_url(),
            {
                "email": user.email,
                "password": password,
            },
        )
        assert login_response.status_code == status.HTTP_200_OK

        access_token = login_response.data["data"]["access"]
        refresh_token = login_response.data["data"]["refresh"]

        # Logout with access token
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")
        logout_response = api_client.post(
            get_logout_url(),
            {
                "refresh": refresh_token,
            },
        )

        assert logout_response.status_code == status.HTTP_200_OK
        assert logout_response.data["success"] is True
        assert "message" in logout_response.data["data"]

    def test_logout_revokes_session(self, api_client):
        """Test that logout revokes the session in database."""
        password = "SecurePassword123!"
        user = UserFactory(password=password, status=UserStatus.ACTIVE)

        # Login first
        login_response = api_client.post(
            get_login_url(),
            {
                "email": user.email,
                "password": password,
            },
        )

        access_token = login_response.data["data"]["access"]
        refresh_token = login_response.data["data"]["refresh"]

        # Get session before logout
        session = Session.objects.filter(user=user).latest("created_at")
        assert session.status == SessionStatus.ACTIVE

        # Logout
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")
        api_client.post(get_logout_url(), {"refresh": refresh_token})

        # Verify session is revoked
        session.refresh_from_db()
        assert session.status == SessionStatus.REVOKED

    def test_logout_without_authentication(self, api_client):
        """Test logout fails without authentication."""
        response = api_client.post(
            get_logout_url(),
            {
                "refresh": "some-token",
            },
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_logout_without_refresh_token(self, api_client):
        """Test logout fails without refresh token."""
        password = "SecurePassword123!"
        user = UserFactory(password=password, status=UserStatus.ACTIVE)

        login_response = api_client.post(
            get_login_url(),
            {
                "email": user.email,
                "password": password,
            },
        )

        access_token = login_response.data["data"]["access"]
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")

        logout_response = api_client.post(get_logout_url(), {})

        assert logout_response.status_code == status.HTTP_400_BAD_REQUEST


# =============================================================================
# TOKEN REFRESH TESTS
# =============================================================================


@pytest.mark.django_db
class TestTokenRefresh:
    """Test cases for token refresh endpoint."""

    def test_token_refresh_success(self, api_client):
        """Test successful token refresh."""
        password = "SecurePassword123!"
        user = UserFactory(password=password, status=UserStatus.ACTIVE)

        # Login to get tokens
        login_response = api_client.post(
            get_login_url(),
            {
                "email": user.email,
                "password": password,
            },
        )
        refresh_token = login_response.data["data"]["refresh"]

        # Refresh token
        refresh_response = api_client.post(
            get_refresh_url(),
            {
                "refresh": refresh_token,
            },
        )

        assert refresh_response.status_code == status.HTTP_200_OK
        assert refresh_response.data["success"] is True
        assert "access" in refresh_response.data["data"]

    def test_token_refresh_returns_new_access_token(self, api_client):
        """Test that refresh returns a new access token."""
        password = "SecurePassword123!"
        user = UserFactory(password=password, status=UserStatus.ACTIVE)

        login_response = api_client.post(
            get_login_url(),
            {
                "email": user.email,
                "password": password,
            },
        )
        old_access = login_response.data["data"]["access"]
        refresh_token = login_response.data["data"]["refresh"]

        refresh_response = api_client.post(
            get_refresh_url(),
            {
                "refresh": refresh_token,
            },
        )

        new_access = refresh_response.data["data"]["access"]
        # Tokens should be different (due to different timestamps)
        assert new_access != old_access

    def test_token_refresh_invalid_token(self, api_client):
        """Test refresh fails with invalid token."""
        response = api_client.post(
            get_refresh_url(),
            {
                "refresh": "invalid-token-string",
            },
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.data["success"] is False

    def test_token_refresh_missing_token(self, api_client):
        """Test refresh fails without token."""
        response = api_client.post(get_refresh_url(), {})

        assert response.status_code in [
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_401_UNAUTHORIZED,
        ]


# =============================================================================
# TOKEN VERIFY TESTS
# =============================================================================


@pytest.mark.django_db
class TestTokenVerify:
    """Test cases for token verification endpoint."""

    def test_token_verify_valid(self, api_client):
        """Test verification of valid access token."""
        password = "SecurePassword123!"
        user = UserFactory(password=password, status=UserStatus.ACTIVE)

        login_response = api_client.post(
            get_login_url(),
            {
                "email": user.email,
                "password": password,
            },
        )
        access_token = login_response.data["data"]["access"]

        verify_response = api_client.post(
            get_verify_url(),
            {
                "token": access_token,
            },
        )

        assert verify_response.status_code == status.HTTP_200_OK
        assert verify_response.data["success"] is True
        assert verify_response.data["data"]["valid"] is True

    def test_token_verify_invalid(self, api_client):
        """Test verification of invalid token."""
        verify_response = api_client.post(
            get_verify_url(),
            {
                "token": "invalid-token-string",
            },
        )

        assert verify_response.status_code == status.HTTP_200_OK
        assert verify_response.data["success"] is True
        assert verify_response.data["data"]["valid"] is False

    def test_token_verify_missing_token(self, api_client):
        """Test verification fails without token."""
        verify_response = api_client.post(get_verify_url(), {})

        assert verify_response.status_code == status.HTTP_400_BAD_REQUEST


# =============================================================================
# USER PROFILE TESTS
# =============================================================================


@pytest.mark.django_db
class TestUserProfile:
    """Test cases for user profile endpoint."""

    def test_get_profile_success(self, api_client):
        """Test successful profile retrieval."""
        password = "SecurePassword123!"
        user = UserFactory(
            password=password,
            status=UserStatus.ACTIVE,
            first_name="John",
            last_name="Doe",
        )

        # Login
        login_response = api_client.post(
            get_login_url(),
            {
                "email": user.email,
                "password": password,
            },
        )
        access_token = login_response.data["data"]["access"]

        # Get profile
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")
        profile_response = api_client.get(get_me_url())

        assert profile_response.status_code == status.HTTP_200_OK
        assert profile_response.data["success"] is True
        assert profile_response.data["data"]["email"] == user.email
        assert profile_response.data["data"]["first_name"] == "John"
        assert profile_response.data["data"]["last_name"] == "Doe"

    def test_get_profile_unauthenticated(self, api_client):
        """Test profile retrieval fails without authentication."""
        response = api_client.get(get_me_url())

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_update_profile_success(self, api_client):
        """Test successful profile update with PUT."""
        password = "SecurePassword123!"
        user = UserFactory(
            password=password,
            status=UserStatus.ACTIVE,
            first_name="John",
            last_name="Doe",
        )

        # Login
        login_response = api_client.post(
            get_login_url(),
            {
                "email": user.email,
                "password": password,
            },
        )
        access_token = login_response.data["data"]["access"]

        # Update profile
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")
        update_response = api_client.put(
            get_me_url(),
            {
                "first_name": "Jane",
                "last_name": "Smith",
                "phone": "+905321234567",
            },
        )

        assert update_response.status_code == status.HTTP_200_OK
        assert update_response.data["success"] is True
        assert update_response.data["data"]["first_name"] == "Jane"
        assert update_response.data["data"]["last_name"] == "Smith"
        assert update_response.data["data"]["phone"] == "+905321234567"

    def test_patch_profile_success(self, api_client):
        """Test successful partial profile update with PATCH."""
        password = "SecurePassword123!"
        user = UserFactory(
            password=password,
            status=UserStatus.ACTIVE,
            first_name="John",
            last_name="Doe",
        )

        # Login
        login_response = api_client.post(
            get_login_url(),
            {
                "email": user.email,
                "password": password,
            },
        )
        access_token = login_response.data["data"]["access"]

        # Partial update
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")
        update_response = api_client.patch(
            get_me_url(),
            {
                "first_name": "Updated",
            },
        )

        assert update_response.status_code == status.HTTP_200_OK
        assert update_response.data["success"] is True
        assert update_response.data["data"]["first_name"] == "Updated"
        # Last name should remain unchanged
        assert update_response.data["data"]["last_name"] == "Doe"


# =============================================================================
# PASSWORD CHANGE TESTS
# =============================================================================


@pytest.mark.django_db
class TestPasswordChange:
    """Test cases for password change endpoint."""

    def test_password_change_success(self, api_client):
        """Test successful password change."""
        old_password = "OldPassword123!"
        new_password = "NewSecurePassword456!"
        user = UserFactory(password=old_password, status=UserStatus.ACTIVE)

        # Login
        login_response = api_client.post(
            get_login_url(),
            {
                "email": user.email,
                "password": old_password,
            },
        )
        access_token = login_response.data["data"]["access"]

        # Change password
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")
        change_response = api_client.post(
            get_password_url(),
            {
                "current_password": old_password,
                "new_password": new_password,
                "confirm_password": new_password,
            },
        )

        assert change_response.status_code == status.HTTP_200_OK
        assert change_response.data["success"] is True

        # Verify new password works
        user.refresh_from_db()
        assert user.check_password(new_password)

    def test_password_change_wrong_current_password(self, api_client):
        """Test password change fails with wrong current password."""
        password = "CorrectPassword123!"
        user = UserFactory(password=password, status=UserStatus.ACTIVE)

        login_response = api_client.post(
            get_login_url(),
            {
                "email": user.email,
                "password": password,
            },
        )
        access_token = login_response.data["data"]["access"]

        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")
        change_response = api_client.post(
            get_password_url(),
            {
                "current_password": "WrongPassword123!",
                "new_password": "NewPassword456!",
                "confirm_password": "NewPassword456!",
            },
        )

        assert change_response.status_code == status.HTTP_400_BAD_REQUEST
        assert change_response.data["success"] is False

    def test_password_change_mismatched_confirmation(self, api_client):
        """Test password change fails when confirm_password doesn't match."""
        password = "CurrentPassword123!"
        user = UserFactory(password=password, status=UserStatus.ACTIVE)

        login_response = api_client.post(
            get_login_url(),
            {
                "email": user.email,
                "password": password,
            },
        )
        access_token = login_response.data["data"]["access"]

        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")
        change_response = api_client.post(
            get_password_url(),
            {
                "current_password": password,
                "new_password": "NewPassword456!",
                "confirm_password": "DifferentPassword789!",
            },
        )

        assert change_response.status_code == status.HTTP_400_BAD_REQUEST
        assert change_response.data["success"] is False

    def test_password_change_revokes_sessions(self, api_client):
        """Test password change revokes all active sessions."""
        password = "CurrentPassword123!"
        user = UserFactory(password=password, status=UserStatus.ACTIVE)

        # Login to create session
        login_response = api_client.post(
            get_login_url(),
            {
                "email": user.email,
                "password": password,
            },
        )
        access_token = login_response.data["data"]["access"]

        # Verify session exists
        active_sessions = Session.objects.filter(
            user=user, status=SessionStatus.ACTIVE
        ).count()
        assert active_sessions >= 1

        # Change password
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")
        api_client.post(
            get_password_url(),
            {
                "current_password": password,
                "new_password": "NewPassword456!",
                "confirm_password": "NewPassword456!",
            },
        )

        # Verify sessions are revoked
        active_sessions_after = Session.objects.filter(
            user=user, status=SessionStatus.ACTIVE
        ).count()
        assert active_sessions_after == 0

    def test_password_change_same_password(self, api_client):
        """Test password change fails when new password equals current."""
        password = "CurrentPassword123!"
        user = UserFactory(password=password, status=UserStatus.ACTIVE)

        login_response = api_client.post(
            get_login_url(),
            {
                "email": user.email,
                "password": password,
            },
        )
        access_token = login_response.data["data"]["access"]

        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")
        change_response = api_client.post(
            get_password_url(),
            {
                "current_password": password,
                "new_password": password,  # Same as current
                "confirm_password": password,
            },
        )

        assert change_response.status_code == status.HTTP_400_BAD_REQUEST

    def test_password_change_too_short(self, api_client):
        """Test password change fails with password shorter than 12 chars."""
        password = "CurrentPassword123!"
        user = UserFactory(password=password, status=UserStatus.ACTIVE)

        login_response = api_client.post(
            get_login_url(),
            {
                "email": user.email,
                "password": password,
            },
        )
        access_token = login_response.data["data"]["access"]

        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")
        change_response = api_client.post(
            get_password_url(),
            {
                "current_password": password,
                "new_password": "Short!",
                "confirm_password": "Short!",
            },
        )

        assert change_response.status_code == status.HTTP_400_BAD_REQUEST


# =============================================================================
# SESSION MANAGEMENT TESTS
# =============================================================================


@pytest.mark.django_db
class TestSessionManagement:
    """Test cases for session management endpoints."""

    def test_list_sessions_success(self, api_client):
        """Test listing active sessions."""
        password = "SecurePassword123!"
        user = UserFactory(password=password, status=UserStatus.ACTIVE)

        # Login to create a session
        login_response = api_client.post(
            get_login_url(),
            {
                "email": user.email,
                "password": password,
            },
        )
        access_token = login_response.data["data"]["access"]

        # List sessions
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")
        sessions_response = api_client.get(get_sessions_url())

        assert sessions_response.status_code == status.HTTP_200_OK
        assert sessions_response.data["success"] is True
        assert isinstance(sessions_response.data["data"], list)
        assert len(sessions_response.data["data"]) >= 1

    def test_list_sessions_unauthenticated(self, api_client):
        """Test listing sessions fails without authentication."""
        response = api_client.get(get_sessions_url())

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_revoke_session_success(self, api_client):
        """Test revoking a specific session."""
        password = "SecurePassword123!"
        user = UserFactory(password=password, status=UserStatus.ACTIVE)

        # Login to create a session
        login_response = api_client.post(
            get_login_url(),
            {
                "email": user.email,
                "password": password,
            },
        )
        access_token = login_response.data["data"]["access"]

        # Get session to revoke
        session = Session.objects.filter(user=user, status=SessionStatus.ACTIVE).first()
        assert session is not None

        # Revoke session
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")
        revoke_response = api_client.delete(get_session_revoke_url(session.id))

        assert revoke_response.status_code == status.HTTP_200_OK
        assert revoke_response.data["success"] is True

        # Verify session is revoked
        session.refresh_from_db()
        assert session.status == SessionStatus.REVOKED

    def test_revoke_session_not_found(self, api_client):
        """Test revoking non-existent session returns 404."""
        password = "SecurePassword123!"
        user = UserFactory(password=password, status=UserStatus.ACTIVE)

        login_response = api_client.post(
            get_login_url(),
            {
                "email": user.email,
                "password": password,
            },
        )
        access_token = login_response.data["data"]["access"]

        # Try to revoke non-existent session
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")
        fake_session_id = uuid.uuid4()
        revoke_response = api_client.delete(get_session_revoke_url(fake_session_id))

        assert revoke_response.status_code == status.HTTP_404_NOT_FOUND

    def test_revoke_all_sessions_success(self, api_client):
        """Test revoking all sessions."""
        password = "SecurePassword123!"
        user = UserFactory(password=password, status=UserStatus.ACTIVE)

        # Login twice to create multiple sessions
        for _ in range(2):
            api_client.post(
                get_login_url(),
                {
                    "email": user.email,
                    "password": password,
                },
            )

        # Get latest access token
        login_response = api_client.post(
            get_login_url(),
            {
                "email": user.email,
                "password": password,
            },
        )
        access_token = login_response.data["data"]["access"]

        # Verify multiple sessions exist
        active_sessions = Session.objects.filter(
            user=user, status=SessionStatus.ACTIVE
        ).count()
        assert active_sessions >= 2

        # Revoke all sessions
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")
        revoke_response = api_client.post(get_sessions_revoke_all_url())

        assert revoke_response.status_code == status.HTTP_200_OK
        assert revoke_response.data["success"] is True
        assert "count" in revoke_response.data["data"]

        # Verify all sessions are revoked
        active_sessions_after = Session.objects.filter(
            user=user, status=SessionStatus.ACTIVE
        ).count()
        assert active_sessions_after == 0


# =============================================================================
# EDGE CASE TESTS
# =============================================================================


@pytest.mark.django_db
class TestAuthEdgeCases:
    """Test edge cases and security scenarios."""

    def test_login_with_whitespace_email(self, api_client):
        """Test login handles email with leading/trailing whitespace."""
        password = "SecurePassword123!"
        UserFactory(
            email="test@example.com", password=password, status=UserStatus.ACTIVE
        )

        response = api_client.post(
            get_login_url(),
            {
                "email": "  test@example.com  ",
                "password": password,
            },
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] is True

    def test_protected_endpoint_with_expired_token(self, api_client):
        """Test protected endpoint returns 401 with expired token."""
        # Using a manually crafted expired-looking token
        api_client.credentials(HTTP_AUTHORIZATION="Bearer expired-token-here")
        response = api_client.get(get_me_url())

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_protected_endpoint_with_malformed_auth_header(self, api_client):
        """Test protected endpoint with malformed Authorization header."""
        api_client.credentials(HTTP_AUTHORIZATION="InvalidFormat token")
        response = api_client.get(get_me_url())

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_session_isolation_between_users(self, api_client):
        """Test that users cannot see each other's sessions."""
        password = "SecurePassword123!"
        user1 = UserFactory(password=password, status=UserStatus.ACTIVE)
        user2 = UserFactory(password=password, status=UserStatus.ACTIVE)

        # Login both users to create sessions
        login1 = api_client.post(
            get_login_url(),
            {
                "email": user1.email,
                "password": password,
            },
        )
        api_client.post(
            get_login_url(),
            {
                "email": user2.email,
                "password": password,
            },
        )

        # User1 lists sessions
        api_client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {login1.data['data']['access']}"
        )
        sessions1 = api_client.get(get_sessions_url())

        # Verify user1 only sees their own sessions
        for session in sessions1.data["data"]:
            db_session = Session.objects.get(id=session["id"])
            assert db_session.user == user1

    def test_cannot_revoke_other_user_session(self, api_client):
        """Test that a user cannot revoke another user's session."""
        password = "SecurePassword123!"
        user1 = UserFactory(password=password, status=UserStatus.ACTIVE)
        user2 = UserFactory(password=password, status=UserStatus.ACTIVE)

        # Login both users
        login1 = api_client.post(
            get_login_url(),
            {
                "email": user1.email,
                "password": password,
            },
        )
        api_client.post(
            get_login_url(),
            {
                "email": user2.email,
                "password": password,
            },
        )

        # Get user2's session
        user2_session = Session.objects.filter(
            user=user2, status=SessionStatus.ACTIVE
        ).first()

        # User1 tries to revoke user2's session
        api_client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {login1.data['data']['access']}"
        )
        revoke_response = api_client.delete(get_session_revoke_url(user2_session.id))

        # Should return 404 (session not found for this user)
        assert revoke_response.status_code == status.HTTP_404_NOT_FOUND

        # Verify user2's session is still active
        user2_session.refresh_from_db()
        assert user2_session.status == SessionStatus.ACTIVE
