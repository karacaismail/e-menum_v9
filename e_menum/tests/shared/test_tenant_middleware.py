"""
Unit tests for multi-tenancy isolation and TenantMiddleware.

These tests verify:
1. TenantMiddleware correctly sets organization context on requests
2. Organization resolution from multiple sources (user, header, cookie)
3. Tenant-required endpoints return 403 without context
4. Public URLs skip tenant resolution
5. Tenant isolation between organizations
6. TenantContextMixin helper methods
7. Utility functions for tenant context management

Run with:
    pytest tests/shared/test_tenant_middleware.py -v
"""

import uuid
from unittest.mock import Mock, patch

import pytest
from django.http import JsonResponse
from django.test import RequestFactory

from apps.core.choices import OrganizationStatus, UserStatus
from apps.core.models import Organization
from shared.middleware.tenant import (
    TenantMiddleware,
    TenantContextMixin,
    get_current_organization,
    set_current_organization,
)
from tests.factories.core import (
    OrganizationFactory,
    UserFactory,
)


# =============================================================================
# TENANT MIDDLEWARE INITIALIZATION TESTS
# =============================================================================


@pytest.mark.django_db
class TestTenantMiddlewareInitialization:
    """Test cases for TenantMiddleware initialization."""

    def test_middleware_initializes_with_get_response(self):
        """Test that middleware initializes with a get_response callable."""
        get_response = Mock()
        middleware = TenantMiddleware(get_response)

        assert middleware.get_response == get_response
        assert middleware._organization_cache == {}

    def test_middleware_has_public_url_prefixes(self):
        """Test that middleware defines public URL prefixes."""
        get_response = Mock()
        middleware = TenantMiddleware(get_response)

        assert "/admin/" in middleware.PUBLIC_URL_PREFIXES
        assert "/health/" in middleware.PUBLIC_URL_PREFIXES
        assert "/api/v1/auth/" in middleware.PUBLIC_URL_PREFIXES
        assert "/api/v1/public/" in middleware.PUBLIC_URL_PREFIXES
        assert "/m/" in middleware.PUBLIC_URL_PREFIXES

    def test_middleware_has_tenant_required_prefixes(self):
        """Test that middleware defines tenant-required URL prefixes."""
        get_response = Mock()
        middleware = TenantMiddleware(get_response)

        assert "/api/v1/menus/" in middleware.TENANT_REQUIRED_PREFIXES
        assert "/api/v1/categories/" in middleware.TENANT_REQUIRED_PREFIXES
        assert "/api/v1/products/" in middleware.TENANT_REQUIRED_PREFIXES
        assert "/api/v1/orders/" in middleware.TENANT_REQUIRED_PREFIXES


# =============================================================================
# TENANT CONTEXT INJECTION TESTS
# =============================================================================


@pytest.mark.django_db
class TestTenantContextInjection:
    """Test cases for tenant context injection into requests."""

    def test_request_gets_tenant_attributes_initialized(self):
        """Test that request gets tenant attributes initialized."""
        get_response = Mock(return_value=Mock())
        middleware = TenantMiddleware(get_response)

        request = RequestFactory().get("/admin/")
        middleware(request)

        assert hasattr(request, "organization")
        assert hasattr(request, "organization_id")
        assert hasattr(request, "is_tenant_aware")

    def test_public_url_sets_tenant_attributes_to_none(self):
        """Test that public URLs have tenant attributes set to None/False."""
        get_response = Mock(return_value=Mock())
        middleware = TenantMiddleware(get_response)

        request = RequestFactory().get("/admin/")
        middleware(request)

        assert request.organization is None
        assert request.organization_id is None
        assert request.is_tenant_aware is False

    def test_authenticated_user_with_organization_sets_context(self):
        """Test that authenticated user's organization is used for context."""
        org = OrganizationFactory()
        user = UserFactory(organization=org, status=UserStatus.ACTIVE)

        get_response = Mock(return_value=Mock())
        middleware = TenantMiddleware(get_response)

        request = RequestFactory().get("/api/v1/some-endpoint/")
        request.user = user

        middleware(request)

        assert request.organization == org
        assert request.organization_id == org.id
        assert request.is_tenant_aware is True

    def test_header_organization_id_sets_context(self):
        """Test that X-Organization-ID header sets tenant context."""
        org = OrganizationFactory()

        get_response = Mock(return_value=Mock())
        middleware = TenantMiddleware(get_response)

        request = RequestFactory().get(
            "/api/v1/some-endpoint/", HTTP_X_ORGANIZATION_ID=str(org.id)
        )
        # Mock unauthenticated user
        request.user = Mock()
        request.user.is_authenticated = False

        middleware(request)

        assert request.organization == org
        assert request.organization_id == org.id
        assert request.is_tenant_aware is True

    def test_cookie_organization_id_sets_context(self):
        """Test that organization cookie sets tenant context."""
        org = OrganizationFactory()

        get_response = Mock(return_value=Mock())
        middleware = TenantMiddleware(get_response)

        request = RequestFactory().get("/api/v1/some-endpoint/")
        request.COOKIES["emenum_org_id"] = str(org.id)
        # Mock unauthenticated user
        request.user = Mock()
        request.user.is_authenticated = False

        middleware(request)

        assert request.organization == org
        assert request.organization_id == org.id
        assert request.is_tenant_aware is True


# =============================================================================
# ORGANIZATION RESOLUTION PRIORITY TESTS
# =============================================================================


@pytest.mark.django_db
class TestOrganizationResolutionPriority:
    """Test cases for organization resolution order of precedence."""

    def test_user_organization_takes_priority_over_header(self):
        """Test that user's organization takes priority over header."""
        org1 = OrganizationFactory(name="User Org")
        org2 = OrganizationFactory(name="Header Org")
        user = UserFactory(organization=org1, status=UserStatus.ACTIVE)

        get_response = Mock(return_value=Mock())
        middleware = TenantMiddleware(get_response)

        request = RequestFactory().get(
            "/api/v1/some-endpoint/", HTTP_X_ORGANIZATION_ID=str(org2.id)
        )
        request.user = user

        middleware(request)

        assert request.organization == org1
        assert request.organization.name == "User Org"

    def test_header_takes_priority_over_cookie(self):
        """Test that header takes priority over cookie."""
        org1 = OrganizationFactory(name="Header Org")
        org2 = OrganizationFactory(name="Cookie Org")

        get_response = Mock(return_value=Mock())
        middleware = TenantMiddleware(get_response)

        request = RequestFactory().get(
            "/api/v1/some-endpoint/", HTTP_X_ORGANIZATION_ID=str(org1.id)
        )
        request.COOKIES["emenum_org_id"] = str(org2.id)
        # Mock unauthenticated user
        request.user = Mock()
        request.user.is_authenticated = False

        middleware(request)

        assert request.organization == org1
        assert request.organization.name == "Header Org"

    def test_cookie_used_when_no_user_or_header(self):
        """Test that cookie is used when no user or header."""
        org = OrganizationFactory(name="Cookie Org")

        get_response = Mock(return_value=Mock())
        middleware = TenantMiddleware(get_response)

        request = RequestFactory().get("/api/v1/some-endpoint/")
        request.COOKIES["emenum_org_id"] = str(org.id)
        # Mock unauthenticated user
        request.user = Mock()
        request.user.is_authenticated = False

        middleware(request)

        assert request.organization == org
        assert request.organization.name == "Cookie Org"


# =============================================================================
# TENANT REQUIRED ENDPOINT TESTS
# =============================================================================


@pytest.mark.django_db
class TestTenantRequiredEndpoints:
    """Test cases for endpoints requiring tenant context."""

    def test_tenant_required_path_returns_403_without_context(self):
        """Test that tenant-required paths return 403 without context."""
        get_response = Mock(return_value=Mock())
        middleware = TenantMiddleware(get_response)

        # Test all tenant-required prefixes
        tenant_required_paths = [
            "/api/v1/menus/",
            "/api/v1/categories/",
            "/api/v1/products/",
            "/api/v1/orders/",
            "/api/v1/tables/",
            "/api/v1/qr-codes/",
            "/api/v1/customers/",
            "/api/v1/analytics/",
        ]

        for path in tenant_required_paths:
            request = RequestFactory().get(path)
            # Mock unauthenticated user with no organization
            request.user = Mock()
            request.user.is_authenticated = False

            response = middleware(request)

            assert isinstance(response, JsonResponse), (
                f"Path {path} should return JsonResponse"
            )
            assert response.status_code == 403, f"Path {path} should return 403"

    def test_tenant_required_403_response_format(self):
        """Test that 403 response follows the standard error format."""
        get_response = Mock(return_value=Mock())
        middleware = TenantMiddleware(get_response)

        request = RequestFactory().get("/api/v1/menus/")
        request.user = Mock()
        request.user.is_authenticated = False

        response = middleware(request)

        import json

        data = json.loads(response.content)

        assert data["success"] is False
        assert "error" in data
        assert data["error"]["code"] == "TENANT_CONTEXT_REQUIRED"
        assert "message" in data["error"]
        assert "details" in data["error"]

    def test_tenant_required_path_passes_with_valid_context(self):
        """Test that tenant-required paths pass with valid context."""
        org = OrganizationFactory()
        user = UserFactory(organization=org, status=UserStatus.ACTIVE)

        mock_response = Mock()
        get_response = Mock(return_value=mock_response)
        middleware = TenantMiddleware(get_response)

        request = RequestFactory().get("/api/v1/menus/")
        request.user = user

        response = middleware(request)

        assert response == mock_response
        get_response.assert_called_once_with(request)


# =============================================================================
# PUBLIC URL TESTS
# =============================================================================


@pytest.mark.django_db
class TestPublicUrls:
    """Test cases for public URL handling."""

    def test_public_urls_skip_tenant_resolution(self):
        """Test that public URLs skip tenant resolution."""
        mock_response = Mock()
        get_response = Mock(return_value=mock_response)
        middleware = TenantMiddleware(get_response)

        public_paths = [
            "/admin/",
            "/health/",
            "/healthz/",
            "/api/v1/auth/login/",
            "/api/v1/public/menu/",
            "/static/css/style.css",
            "/media/images/logo.png",
            "/m/cafe-istanbul/",
        ]

        for path in public_paths:
            request = RequestFactory().get(path)
            response = middleware(request)

            assert response == mock_response, f"Path {path} should pass through"
            assert request.organization is None
            assert request.is_tenant_aware is False

    def test_public_url_does_not_return_403(self):
        """Test that public URLs do not return 403 even without context."""
        mock_response = Mock()
        get_response = Mock(return_value=mock_response)
        middleware = TenantMiddleware(get_response)

        request = RequestFactory().get("/api/v1/auth/login/")
        response = middleware(request)

        assert response == mock_response
        assert not isinstance(response, JsonResponse) or response.status_code != 403


# =============================================================================
# INVALID ORGANIZATION ID TESTS
# =============================================================================


@pytest.mark.django_db
class TestInvalidOrganizationId:
    """Test cases for invalid organization ID handling."""

    def test_invalid_uuid_in_header_returns_none(self):
        """Test that invalid UUID in header results in None organization."""
        get_response = Mock(return_value=Mock())
        middleware = TenantMiddleware(get_response)

        request = RequestFactory().get(
            "/api/v1/some-endpoint/", HTTP_X_ORGANIZATION_ID="not-a-valid-uuid"
        )
        request.user = Mock()
        request.user.is_authenticated = False

        # Since the path doesn't require tenant context, it should pass
        # but organization should be None
        middleware(request)

        assert request.organization is None

    def test_nonexistent_organization_id_returns_none(self):
        """Test that non-existent organization ID results in None."""
        fake_uuid = str(uuid.uuid4())

        get_response = Mock(return_value=Mock())
        middleware = TenantMiddleware(get_response)

        request = RequestFactory().get(
            "/api/v1/some-endpoint/", HTTP_X_ORGANIZATION_ID=fake_uuid
        )
        request.user = Mock()
        request.user.is_authenticated = False

        middleware(request)

        assert request.organization is None

    def test_deleted_organization_id_returns_none(self):
        """Test that soft-deleted organization ID results in None."""
        org = OrganizationFactory()
        org.soft_delete()

        get_response = Mock(return_value=Mock())
        middleware = TenantMiddleware(get_response)

        request = RequestFactory().get(
            "/api/v1/some-endpoint/", HTTP_X_ORGANIZATION_ID=str(org.id)
        )
        request.user = Mock()
        request.user.is_authenticated = False

        middleware(request)

        assert request.organization is None

    def test_suspended_organization_id_returns_none(self):
        """Test that suspended organization ID results in None."""
        org = OrganizationFactory(status=OrganizationStatus.SUSPENDED)

        get_response = Mock(return_value=Mock())
        middleware = TenantMiddleware(get_response)

        request = RequestFactory().get(
            "/api/v1/some-endpoint/", HTTP_X_ORGANIZATION_ID=str(org.id)
        )
        request.user = Mock()
        request.user.is_authenticated = False

        middleware(request)

        assert request.organization is None


# =============================================================================
# ORGANIZATION CACHE TESTS
# =============================================================================


@pytest.mark.django_db
class TestOrganizationCache:
    """Test cases for organization caching behavior."""

    def test_organization_cached_after_first_lookup(self):
        """Test that organization is cached after first lookup."""
        org = OrganizationFactory()

        get_response = Mock(return_value=Mock())
        middleware = TenantMiddleware(get_response)

        request = RequestFactory().get(
            "/api/v1/some-endpoint/", HTTP_X_ORGANIZATION_ID=str(org.id)
        )
        request.user = Mock()
        request.user.is_authenticated = False

        middleware(request)

        # Verify organization is in cache
        assert org.id in middleware._organization_cache
        assert middleware._organization_cache[org.id] == org

    def test_cached_organization_used_for_subsequent_requests(self):
        """Test that cached organization is used for subsequent requests."""
        org = OrganizationFactory()

        get_response = Mock(return_value=Mock())
        middleware = TenantMiddleware(get_response)

        # First request
        request1 = RequestFactory().get(
            "/api/v1/some-endpoint/", HTTP_X_ORGANIZATION_ID=str(org.id)
        )
        request1.user = Mock()
        request1.user.is_authenticated = False
        middleware(request1)

        # Modify org in database (but cache should still have old reference)
        middleware._organization_cache[org.id]

        # Second request should use cache
        request2 = RequestFactory().get(
            "/api/v1/another-endpoint/", HTTP_X_ORGANIZATION_ID=str(org.id)
        )
        request2.user = Mock()
        request2.user.is_authenticated = False

        with patch.object(Organization.objects, "get") as mock_get:
            middleware(request2)
            # Should not call database again
            mock_get.assert_not_called()


# =============================================================================
# TENANT CONTEXT MIXIN TESTS
# =============================================================================


@pytest.mark.django_db
class TestTenantContextMixin:
    """Test cases for TenantContextMixin helper methods."""

    def test_get_organization_returns_organization_from_request(self):
        """Test that get_organization returns request.organization."""
        org = OrganizationFactory()

        class MockView(TenantContextMixin):
            pass

        view = MockView()
        view.request = Mock()
        view.request.organization = org

        assert view.get_organization() == org

    def test_get_organization_returns_none_when_not_set(self):
        """Test that get_organization returns None when not set."""

        class MockView(TenantContextMixin):
            pass

        view = MockView()
        view.request = Mock(spec=[])  # No organization attribute

        assert view.get_organization() is None

    def test_get_organization_id_returns_organization_id(self):
        """Test that get_organization_id returns request.organization_id."""
        org = OrganizationFactory()

        class MockView(TenantContextMixin):
            pass

        view = MockView()
        view.request = Mock()
        view.request.organization_id = org.id

        assert view.get_organization_id() == org.id

    def test_get_organization_id_returns_none_when_not_set(self):
        """Test that get_organization_id returns None when not set."""

        class MockView(TenantContextMixin):
            pass

        view = MockView()
        view.request = Mock(spec=[])

        assert view.get_organization_id() is None

    def test_require_organization_returns_organization_when_present(self):
        """Test that require_organization returns org when present."""
        org = OrganizationFactory()

        class MockView(TenantContextMixin):
            pass

        view = MockView()
        view.request = Mock()
        view.request.organization = org

        assert view.require_organization() == org

    def test_require_organization_raises_permission_denied_when_none(self):
        """Test that require_organization raises PermissionDenied when None."""
        from django.core.exceptions import PermissionDenied

        class MockView(TenantContextMixin):
            pass

        view = MockView()
        view.request = Mock()
        view.request.organization = None

        with pytest.raises(PermissionDenied):
            view.require_organization()


# =============================================================================
# UTILITY FUNCTION TESTS
# =============================================================================


@pytest.mark.django_db
class TestUtilityFunctions:
    """Test cases for utility functions."""

    def test_get_current_organization_returns_organization(self):
        """Test that get_current_organization returns request.organization."""
        org = OrganizationFactory()

        request = Mock()
        request.organization = org

        assert get_current_organization(request) == org

    def test_get_current_organization_returns_none_when_not_set(self):
        """Test that get_current_organization returns None when not set."""
        request = Mock(spec=[])

        assert get_current_organization(request) is None

    def test_set_current_organization_sets_all_attributes(self):
        """Test that set_current_organization sets all tenant attributes."""
        org = OrganizationFactory()
        request = Mock()

        set_current_organization(request, org)

        assert request.organization == org
        assert request.organization_id == org.id
        assert request.is_tenant_aware is True

    def test_set_current_organization_with_none_clears_context(self):
        """Test that set_current_organization with None clears context."""
        request = Mock()

        set_current_organization(request, None)

        assert request.organization is None
        assert request.organization_id is None
        assert request.is_tenant_aware is False


# =============================================================================
# TENANT ISOLATION TESTS
# =============================================================================


@pytest.mark.django_db
class TestTenantIsolation:
    """Test cases for verifying tenant isolation."""

    def test_user_can_only_access_own_organization(self):
        """Test that user can only access their own organization."""
        org1 = OrganizationFactory(name="Org One")
        org2 = OrganizationFactory(name="Org Two")
        user = UserFactory(organization=org1, status=UserStatus.ACTIVE)

        get_response = Mock(return_value=Mock())
        middleware = TenantMiddleware(get_response)

        request = RequestFactory().get("/api/v1/menus/")
        request.user = user

        middleware(request)

        # User's organization should be set
        assert request.organization == org1
        assert request.organization.name == "Org One"

        # User should NOT have access to org2
        assert request.organization != org2

    def test_different_users_get_different_organization_contexts(self):
        """Test that different users get their respective organizations."""
        org1 = OrganizationFactory(name="Cafe One")
        org2 = OrganizationFactory(name="Cafe Two")
        user1 = UserFactory(organization=org1, status=UserStatus.ACTIVE)
        user2 = UserFactory(organization=org2, status=UserStatus.ACTIVE)

        get_response = Mock(return_value=Mock())
        middleware = TenantMiddleware(get_response)

        # Request for user1
        request1 = RequestFactory().get("/api/v1/menus/")
        request1.user = user1
        middleware(request1)

        # Request for user2
        request2 = RequestFactory().get("/api/v1/menus/")
        request2.user = user2
        middleware(request2)

        # Each user should have their own organization context
        assert request1.organization == org1
        assert request2.organization == org2
        assert request1.organization != request2.organization

    def test_anonymous_user_has_no_organization_context(self):
        """Test that anonymous user has no organization context."""
        get_response = Mock(return_value=Mock())
        middleware = TenantMiddleware(get_response)

        request = RequestFactory().get("/api/v1/auth/login/")  # Public URL
        request.user = Mock()
        request.user.is_authenticated = False

        middleware(request)

        assert request.organization is None
        assert request.is_tenant_aware is False

    def test_user_without_organization_has_no_context(self):
        """Test that user without organization has no context."""
        # Platform user without organization
        user = UserFactory(organization=None, status=UserStatus.ACTIVE)

        get_response = Mock(return_value=Mock())
        middleware = TenantMiddleware(get_response)

        request = RequestFactory().get("/api/v1/some-endpoint/")
        request.user = user

        middleware(request)

        assert request.organization is None


# =============================================================================
# EDGE CASE TESTS
# =============================================================================


@pytest.mark.django_db
class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_organization_id_header_ignored(self):
        """Test that empty organization ID header is ignored."""
        get_response = Mock(return_value=Mock())
        middleware = TenantMiddleware(get_response)

        request = RequestFactory().get(
            "/api/v1/some-endpoint/", HTTP_X_ORGANIZATION_ID=""
        )
        request.user = Mock()
        request.user.is_authenticated = False

        middleware(request)

        assert request.organization is None

    def test_whitespace_organization_id_header_handled(self):
        """Test that whitespace organization ID is handled gracefully."""
        get_response = Mock(return_value=Mock())
        middleware = TenantMiddleware(get_response)

        request = RequestFactory().get(
            "/api/v1/some-endpoint/", HTTP_X_ORGANIZATION_ID="   "
        )
        request.user = Mock()
        request.user.is_authenticated = False

        middleware(request)

        assert request.organization is None

    def test_request_without_user_attribute_handled(self):
        """Test that request without user attribute is handled."""
        get_response = Mock(return_value=Mock())
        middleware = TenantMiddleware(get_response)

        request = RequestFactory().get("/api/v1/some-endpoint/")
        # Don't set user attribute at all

        # Should not raise an error
        middleware(request)

        assert request.organization is None

    def test_database_error_handled_gracefully(self):
        """Test that database errors are handled gracefully."""
        org_id = str(uuid.uuid4())

        get_response = Mock(return_value=Mock())
        middleware = TenantMiddleware(get_response)

        request = RequestFactory().get(
            "/api/v1/some-endpoint/", HTTP_X_ORGANIZATION_ID=org_id
        )
        request.user = Mock()
        request.user.is_authenticated = False

        # The organization doesn't exist, so it should return None
        middleware(request)

        assert request.organization is None


# =============================================================================
# CUSTOM SETTINGS TESTS
# =============================================================================


@pytest.mark.django_db
class TestCustomSettings:
    """Test cases for custom settings configuration."""

    def test_custom_header_name_from_settings(self, settings):
        """Test that custom header name from settings is respected."""
        settings.EMENUM_TENANT_HEADER = "X-Tenant-ID"

        org = OrganizationFactory()

        get_response = Mock(return_value=Mock())
        middleware = TenantMiddleware(get_response)

        request = RequestFactory().get(
            "/api/v1/some-endpoint/", HTTP_X_TENANT_ID=str(org.id)
        )
        request.user = Mock()
        request.user.is_authenticated = False

        middleware(request)

        assert request.organization == org

    def test_custom_cookie_name_from_settings(self, settings):
        """Test that custom cookie name from settings is respected."""
        settings.EMENUM_TENANT_COOKIE = "tenant_id"

        org = OrganizationFactory()

        get_response = Mock(return_value=Mock())
        middleware = TenantMiddleware(get_response)

        request = RequestFactory().get("/api/v1/some-endpoint/")
        request.COOKIES["tenant_id"] = str(org.id)
        request.user = Mock()
        request.user.is_authenticated = False

        middleware(request)

        assert request.organization == org
