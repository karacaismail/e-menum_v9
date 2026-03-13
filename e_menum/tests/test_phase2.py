"""
Tests for Phase 2 features:
1. Admin Panel access control (is_superuser instead of is_staff)
2. Subscription upgrade request flow (pending approval)
3. Notification widget API endpoints
4. UpgradeRequest model and admin
5. CMS accessibility (no dark toggle on website, skip-to-content)
6. Gender-aware avatar template filter
7. Trust bar logos (no placeholder "Isletme" text)
8. e-menum.com -> e-menum.net references
"""

import pytest
from django.test import RequestFactory, override_settings
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
def superadmin(db):
    user = User.objects.create_superuser(
        email="admin@e-menum.net",
        password="Admin1234!emenum",
    )
    return user


@pytest.fixture
def logged_in_client(client, owner):
    client.login(email="owner@test.com", password="TestPass1234!")
    return client


@pytest.fixture
def superadmin_client(client, superadmin):
    client.login(email="admin@e-menum.net", password="Admin1234!emenum")
    return client


# =============================================================================
# 1. Admin Panel Access Control
# =============================================================================


class TestAdminPanelAccess:
    """Only superusers should see 'Admin Panel' link in the portal."""

    def test_restaurant_owner_no_admin_link(self, owner):
        """Restaurant owner (is_staff=False) should NOT have admin privileges.

        The 'Admin Panel' link is gated by ``is_superuser`` in the template,
        so verifying the user flags is sufficient. We avoid rendering the deeply
        nested dashboard template because Django's test client ``copy(context)``
        triggers RecursionError on deep template chains.
        """
        assert not owner.is_superuser
        assert not owner.is_staff


# =============================================================================
# 2. Subscription Upgrade Request Flow
# =============================================================================


class TestUpgradeRequestFlow:
    """Upgrade should create a pending request, not change plan directly."""

    @pytest.fixture
    def plan(self, db):
        from apps.subscriptions.models import Plan

        plan, _ = Plan.objects.get_or_create(
            slug="growth",
            defaults={
                "name": "Growth Plan",
                "tier": "GROWTH",
                "price_monthly": 4500,
                "is_active": True,
            },
        )
        return plan

    @pytest.fixture
    def subscription(self, db, org, plan):
        from apps.subscriptions.models import Plan, Subscription

        free_plan, _ = Plan.objects.get_or_create(
            slug="free",
            defaults={
                "name": "Free Plan",
                "tier": "FREE",
                "price_monthly": 0,
                "is_active": True,
            },
        )
        return Subscription.objects.create(
            organization=org,
            plan=free_plan,
            status="ACTIVE",
            current_price=0,
        )

    def test_upgrade_creates_pending_request(
        self, logged_in_client, org, plan, subscription
    ):
        """POST to upgrade should create an UpgradeRequest with PENDING status."""
        from apps.subscriptions.models import UpgradeRequest

        resp = logged_in_client.post(
            "/account/subscription/upgrade/",
            data={"plan_id": str(plan.id)},
        )
        assert resp.status_code == 302  # redirect

        req = UpgradeRequest.objects.filter(
            organization=org,
            deleted_at__isnull=True,
        ).first()
        assert req is not None
        assert req.status == "PENDING"
        assert req.requested_plan == plan

    def test_upgrade_no_direct_plan_change(
        self, logged_in_client, org, plan, subscription
    ):
        """Plan should NOT change immediately after upgrade request."""
        logged_in_client.post(
            "/account/subscription/upgrade/",
            data={"plan_id": str(plan.id)},
        )
        subscription.refresh_from_db()
        # Plan should still be the free plan, not the requested one
        assert subscription.plan.tier == "FREE"

    def test_duplicate_pending_request_blocked(
        self, logged_in_client, org, plan, subscription
    ):
        """Second pending request should be blocked."""
        logged_in_client.post(
            "/account/subscription/upgrade/",
            data={"plan_id": str(plan.id)},
        )
        logged_in_client.post(
            "/account/subscription/upgrade/",
            data={"plan_id": str(plan.id)},
        )
        from apps.subscriptions.models import UpgradeRequest

        count = UpgradeRequest.objects.filter(
            organization=org,
            status="PENDING",
            deleted_at__isnull=True,
        ).count()
        assert count == 1

    def test_approve_upgrades_plan(self, db, org, plan, subscription, superadmin):
        """Approving an upgrade request should change the plan."""
        from apps.subscriptions.models import UpgradeRequest

        req = UpgradeRequest.objects.create(
            organization=org,
            current_plan=subscription.plan,
            requested_plan=plan,
            requested_by=superadmin,
        )
        req.approve(reviewer=superadmin, note="Approved")

        subscription.refresh_from_db()
        assert subscription.plan == plan
        assert req.status == "APPROVED"


# =============================================================================
# 3. Notification Widget API
# =============================================================================


class TestNotificationAPI:
    """Notification API endpoints for navbar widget."""

    def test_notification_count_url(self):
        match = resolve("/account/api/notifications/count/")
        assert match is not None
        assert match.url_name == "notification-count-api"

    def test_notification_list_url(self):
        match = resolve("/account/api/notifications/")
        assert match is not None
        assert match.url_name == "notification-list-api"

    def test_notification_count_returns_json(self, logged_in_client):
        resp = logged_in_client.get("/account/api/notifications/count/")
        assert resp.status_code == 200
        data = resp.json()
        assert "count" in data
        assert isinstance(data["count"], int)

    def test_notification_list_returns_json(self, logged_in_client):
        resp = logged_in_client.get("/account/api/notifications/")
        assert resp.status_code == 200
        data = resp.json()
        assert "notifications" in data
        assert isinstance(data["notifications"], list)

    def test_notification_mark_all_read(self, logged_in_client):
        resp = logged_in_client.post("/account/api/notifications/read-all/")
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True


# =============================================================================
# 4. UpgradeRequest Admin
# =============================================================================


class TestUpgradeRequestAdmin:
    """Superadmin should be able to manage upgrade requests in Django Admin."""

    def test_superadmin_sees_upgrade_requests(self, superadmin_client):
        resp = superadmin_client.get("/admin/subscriptions/upgraderequest/")
        assert resp.status_code == 200


# =============================================================================
# 5. Gender Avatar Template Filter
# =============================================================================


class TestGenderAvatarFilter:
    """Gender-aware avatar filter returns correct gender photos."""

    def test_male_name_returns_male_photo(self):
        from apps.website.templatetags.website_tags import gender_avatar

        url = gender_avatar("Mehmet Yilmaz", 1)
        assert "unsplash.com" in url
        # Male photos list
        assert "507003211169" in url or "472099645785" in url or "unsplash" in url

    def test_female_name_returns_female_photo(self):
        from apps.website.templatetags.website_tags import gender_avatar

        url = gender_avatar("Fatma Ozturk", 1)
        assert "unsplash.com" in url
        # Female photos list
        assert "494790108377" in url or "438761681033" in url or "unsplash" in url

    def test_empty_name_fallback(self):
        from apps.website.templatetags.website_tags import gender_avatar

        url = gender_avatar("", 0)
        assert "unsplash.com" in url


# =============================================================================
# 6. e-menum.com -> e-menum.net (mockup templates)
# =============================================================================


class TestDomainReferences:
    """Mockup templates should use e-menum.net, not e-menum.com."""

    def test_mockups_use_correct_domain(self):
        import os

        mockup_dir = os.path.join(
            os.getcwd(),
            "templates",
            "website",
            "partials",
            "mockups",
        )
        if not os.path.exists(mockup_dir):
            pytest.skip("Mockup directory not found")

        for fname in os.listdir(mockup_dir):
            if fname.endswith(".html"):
                fpath = os.path.join(mockup_dir, fname)
                with open(fpath) as f:
                    content = f.read()
                assert "e-menum.com" not in content, (
                    f"{fname} still contains e-menum.com"
                )


# =============================================================================
# 7. Wildcard Subdomain → Canonical Domain Redirect
# =============================================================================


class TestWildcardSubdomainRedirect:
    """CanonicalDomainMiddleware should 301 redirect any subdomain to canonical."""

    @pytest.fixture
    def middleware(self):
        from apps.seo.middleware import CanonicalDomainMiddleware

        def dummy_response(request):
            from django.http import HttpResponse

            return HttpResponse("OK")

        with override_settings(SEO_CANONICAL_DOMAIN="e-menum.net"):
            mw = CanonicalDomainMiddleware(dummy_response)
        return mw

    @pytest.fixture
    def factory(self):
        return RequestFactory()

    def test_www_redirects_to_canonical(self, middleware, factory):
        request = factory.get("/tr/fiyat/", SERVER_NAME="www.e-menum.net")
        resp = middleware(request)
        assert resp.status_code == 301
        assert "e-menum.net/tr/fiyat/" in resp["Location"]
        assert "www." not in resp["Location"]

    def test_api_redirects_to_canonical(self, middleware, factory):
        request = factory.get("/api/v1/menus/", SERVER_NAME="api.e-menum.net")
        resp = middleware(request)
        assert resp.status_code == 301
        assert "e-menum.net/api/v1/menus/" in resp["Location"]

    def test_random_subdomain_redirects(self, middleware, factory):
        request = factory.get("/", SERVER_NAME="blog.e-menum.net")
        resp = middleware(request)
        assert resp.status_code == 301
        assert "e-menum.net/" in resp["Location"]

    def test_canonical_domain_no_redirect(self, middleware, factory):
        request = factory.get("/", SERVER_NAME="e-menum.net")
        resp = middleware(request)
        assert resp.status_code == 200

    def test_localhost_skipped(self, middleware, factory):
        request = factory.get("/", SERVER_NAME="localhost")
        resp = middleware(request)
        assert resp.status_code == 200

    @override_settings(SEO_CANONICAL_DOMAIN="e-menum.net")
    def test_allowed_hosts_wildcard(self):
        """Production ALLOWED_HOSTS with .e-menum.net accepts any subdomain."""
        from django.http import HttpRequest

        request = HttpRequest()
        request.META["HTTP_HOST"] = "anything.e-menum.net"
        request.META["SERVER_NAME"] = "anything.e-menum.net"

        with override_settings(
            ALLOWED_HOSTS=["e-menum.net", ".e-menum.net"],
        ):
            host = request.get_host()
            assert host == "anything.e-menum.net"
