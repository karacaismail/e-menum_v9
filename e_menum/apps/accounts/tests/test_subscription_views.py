"""
Tests for Account Subscription and Invoice views.

Tests cover:
- URL resolution → /account/subscription/ and /account/invoices/
- Access control → requires login
- Display → subscription details and invoice list render
"""

import pytest
from django.test import Client
from django.urls import reverse

from tests.factories.core import OrganizationFactory, UserFactory


pytestmark = pytest.mark.django_db


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture(autouse=True)
def _disable_canonical_redirect(settings):
    settings.SEO_CANONICAL_DOMAIN = ''


@pytest.fixture
def org(db):
    return OrganizationFactory()


@pytest.fixture
def user(db, org):
    return UserFactory(organization=org, is_staff=False)


@pytest.fixture
def auth_client(db, user):
    client = Client()
    client.force_login(user)
    return client


@pytest.fixture
def anon_client():
    return Client()


# =============================================================================
# URL RESOLUTION TESTS
# =============================================================================

class TestSubscriptionURLs:
    """Subscription and Invoice URLs must resolve correctly."""

    def test_subscription_url_resolves(self):
        url = reverse('accounts:subscription')
        assert url == '/account/subscription/'

    def test_invoices_url_resolves(self):
        url = reverse('accounts:invoices')
        assert url == '/account/invoices/'


# =============================================================================
# ACCESS CONTROL TESTS
# =============================================================================

class TestSubscriptionAccess:
    """Subscription pages require authentication."""

    def test_subscription_anonymous_redirected(self, anon_client):
        resp = anon_client.get(reverse('accounts:subscription'))
        assert resp.status_code == 302

    def test_subscription_auth_user_can_access(self, auth_client):
        resp = auth_client.get(reverse('accounts:subscription'))
        assert resp.status_code == 200

    def test_invoices_anonymous_redirected(self, anon_client):
        resp = anon_client.get(reverse('accounts:invoices'))
        assert resp.status_code == 302

    def test_invoices_auth_user_can_access(self, auth_client):
        resp = auth_client.get(reverse('accounts:invoices'))
        assert resp.status_code == 200


# =============================================================================
# DISPLAY TESTS
# =============================================================================

class TestSubscriptionRendering:
    """Subscription page shows plan details."""

    def test_subscription_page_renders(self, auth_client):
        resp = auth_client.get(reverse('accounts:subscription'))
        assert resp.status_code == 200
        assert b'subscription' in resp.content.lower() or b'plan' in resp.content.lower()

    def test_subscription_has_context(self, auth_client):
        resp = auth_client.get(reverse('accounts:subscription'))
        assert 'subscription' in resp.context or 'plan' in resp.context


class TestInvoicesRendering:
    """Invoices page shows billing history."""

    def test_invoices_page_renders(self, auth_client):
        resp = auth_client.get(reverse('accounts:invoices'))
        assert resp.status_code == 200
        assert b'invoice' in resp.content.lower()

    def test_invoices_has_context(self, auth_client):
        resp = auth_client.get(reverse('accounts:invoices'))
        assert 'invoices' in resp.context
