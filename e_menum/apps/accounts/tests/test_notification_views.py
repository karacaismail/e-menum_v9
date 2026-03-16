"""
Tests for the notification views in the restaurant account portal.

Tests cover:
- Anonymous user redirect to login
- Unread count API returns correct count
- Notification list API returns recent notifications
- Type filter on notification list
- Mark single notification as read
- Mark all notifications as read
- Full notification page renders with pagination
- Organization-scoped filtering (tenant isolation)

Uses pytest-django with Django test Client.
"""

import uuid

import pytest
from django.test import Client
from django.urls import reverse

from apps.notifications.models import Notification


pytestmark = pytest.mark.django_db


# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture(autouse=True)
def _disable_canonical_redirect(settings):
    """Disable CanonicalDomainMiddleware redirect for test client."""
    settings.SEO_CANONICAL_DOMAIN = ""


@pytest.fixture
def org_user(make_user, organization):
    """Create a user belonging to the test organization."""
    return make_user(organization=organization)


@pytest.fixture
def authed_client(org_user):
    """Return a Django test Client logged in as org_user."""
    c = Client()
    c.force_login(org_user)
    return c


@pytest.fixture
def make_notification(organization, org_user):
    """Factory to create notifications for org_user."""

    def _make(
        title="Test Notification",
        message="Test message body",
        notification_type="ORDER",
        status="DELIVERED",
        **kwargs,
    ):
        defaults = dict(
            organization=organization,
            user=org_user,
            title=title,
            message=message,
            notification_type=notification_type,
            status=status,
        )
        defaults.update(kwargs)
        return Notification.objects.create(**defaults)

    return _make


# =============================================================================
# 1. ANONYMOUS USER REDIRECT
# =============================================================================


class TestAnonymousRedirect:
    """Anonymous users should be redirected to /account/login/."""

    def test_unread_count_redirects(self, client):
        url = reverse("accounts:notification-count-api")
        resp = client.get(url)
        assert resp.status_code == 302
        assert "/account/login/" in resp.url

    def test_notification_list_redirects(self, client):
        url = reverse("accounts:notification-list-api")
        resp = client.get(url)
        assert resp.status_code == 302
        assert "/account/login/" in resp.url

    def test_mark_read_redirects(self, client):
        url = reverse(
            "accounts:notification-mark-read-api",
            kwargs={"notification_id": uuid.uuid4()},
        )
        resp = client.post(url)
        assert resp.status_code == 302
        assert "/account/login/" in resp.url

    def test_mark_all_read_redirects(self, client):
        url = reverse("accounts:notification-mark-all-read-api")
        resp = client.post(url)
        assert resp.status_code == 302
        assert "/account/login/" in resp.url

    def test_notification_page_redirects(self, client):
        url = reverse("accounts:notification-list")
        resp = client.get(url)
        assert resp.status_code == 302
        assert "/account/login/" in resp.url


# =============================================================================
# 2. UNREAD COUNT
# =============================================================================


class TestUnreadCount:
    """GET /account/api/notifications/count/ returns correct unread count."""

    def test_zero_when_no_notifications(self, authed_client):
        url = reverse("accounts:notification-count-api")
        resp = authed_client.get(url)
        assert resp.status_code == 200
        assert resp.json()["count"] == 0

    def test_counts_only_unread(self, authed_client, make_notification):
        make_notification(status="DELIVERED")
        make_notification(status="DELIVERED")
        make_notification(status="READ")
        url = reverse("accounts:notification-count-api")
        resp = authed_client.get(url)
        assert resp.json()["count"] == 2

    def test_excludes_soft_deleted(self, authed_client, make_notification):
        from django.utils import timezone

        make_notification(status="DELIVERED")
        n = make_notification(status="DELIVERED")
        # Soft-delete via all_objects to bypass the SoftDeleteManager
        Notification.all_objects.filter(id=n.id).update(deleted_at=timezone.now())

        url = reverse("accounts:notification-count-api")
        resp = authed_client.get(url)
        assert resp.json()["count"] == 1


# =============================================================================
# 3. NOTIFICATION LIST
# =============================================================================


class TestNotificationList:
    """GET /account/api/notifications/ returns recent notifications."""

    def test_empty_list(self, authed_client):
        url = reverse("accounts:notification-list-api")
        resp = authed_client.get(url)
        assert resp.status_code == 200
        data = resp.json()
        assert data["notifications"] == []

    def test_returns_notifications(self, authed_client, make_notification):
        make_notification(title="Order received")
        make_notification(title="Payment confirmed")
        url = reverse("accounts:notification-list-api")
        resp = authed_client.get(url)
        titles = [n["title"] for n in resp.json()["notifications"]]
        assert "Order received" in titles
        assert "Payment confirmed" in titles

    def test_max_12_notifications(self, authed_client, make_notification):
        for i in range(15):
            make_notification(title=f"Notif {i}")
        url = reverse("accounts:notification-list-api")
        resp = authed_client.get(url)
        assert len(resp.json()["notifications"]) == 12

    def test_notification_fields(self, authed_client, make_notification):
        make_notification(
            title="Field check",
            message="Body text",
            notification_type="ORDER",
            status="DELIVERED",
        )
        url = reverse("accounts:notification-list-api")
        resp = authed_client.get(url)
        notif = resp.json()["notifications"][0]
        assert "id" in notif
        assert notif["type"] == "ORDER"
        assert notif["title"] == "Field check"
        assert notif["status"] == "DELIVERED"
        assert "created_at" in notif
        assert "read" in notif


# =============================================================================
# 4. TYPE FILTER
# =============================================================================


class TestTypeFilter:
    """Notification list supports ?type= query parameter."""

    def test_filter_by_order(self, authed_client, make_notification):
        make_notification(title="Order notif", notification_type="ORDER")
        make_notification(title="System notif", notification_type="SYSTEM")
        url = reverse("accounts:notification-list-api")
        resp = authed_client.get(url, {"type": "ORDER"})
        notifications = resp.json()["notifications"]
        assert len(notifications) == 1
        assert notifications[0]["type"] == "ORDER"

    def test_filter_by_system(self, authed_client, make_notification):
        make_notification(notification_type="ORDER")
        make_notification(notification_type="SYSTEM")
        url = reverse("accounts:notification-list-api")
        resp = authed_client.get(url, {"type": "SYSTEM"})
        assert all(n["type"] == "SYSTEM" for n in resp.json()["notifications"])

    def test_invalid_type_ignored(self, authed_client, make_notification):
        make_notification(notification_type="ORDER")
        make_notification(notification_type="SYSTEM")
        url = reverse("accounts:notification-list-api")
        resp = authed_client.get(url, {"type": "INVALID"})
        # Invalid type should return all notifications (filter not applied)
        assert len(resp.json()["notifications"]) == 2


# =============================================================================
# 5. MARK READ
# =============================================================================


class TestMarkRead:
    """POST /account/api/notifications/<id>/read/ marks notification as read."""

    def test_mark_read_success(self, authed_client, make_notification):
        n = make_notification(status="DELIVERED")
        url = reverse(
            "accounts:notification-mark-read-api",
            kwargs={"notification_id": n.id},
        )
        resp = authed_client.post(url)
        assert resp.status_code == 200
        assert resp.json()["success"] is True
        n.refresh_from_db()
        assert n.status == "READ"

    def test_mark_read_not_found(self, authed_client):
        url = reverse(
            "accounts:notification-mark-read-api",
            kwargs={"notification_id": uuid.uuid4()},
        )
        resp = authed_client.post(url)
        assert resp.status_code == 404
        assert "error" in resp.json()

    def test_mark_read_requires_post(self, authed_client, make_notification):
        n = make_notification(status="DELIVERED")
        url = reverse(
            "accounts:notification-mark-read-api",
            kwargs={"notification_id": n.id},
        )
        resp = authed_client.get(url)
        assert resp.status_code == 405


# =============================================================================
# 6. MARK ALL READ
# =============================================================================


class TestMarkAllRead:
    """POST /account/api/notifications/read-all/ marks all as read."""

    def test_mark_all_read(self, authed_client, make_notification):
        make_notification(status="DELIVERED")
        make_notification(status="DELIVERED")
        make_notification(status="READ")  # already read
        url = reverse("accounts:notification-mark-all-read-api")
        resp = authed_client.post(url)
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["updated"] == 2

    def test_mark_all_read_when_none_unread(self, authed_client, make_notification):
        make_notification(status="READ")
        url = reverse("accounts:notification-mark-all-read-api")
        resp = authed_client.post(url)
        assert resp.json()["updated"] == 0

    def test_mark_all_read_requires_post(self, authed_client):
        url = reverse("accounts:notification-mark-all-read-api")
        resp = authed_client.get(url)
        assert resp.status_code == 405


# =============================================================================
# 7. NOTIFICATION PAGE (with pagination)
# =============================================================================


class TestNotificationPage:
    """GET /account/notifications/ renders paginated notification page."""

    def test_page_renders(self, authed_client, make_notification):
        make_notification(title="Page notification")
        url = reverse("accounts:notification-list")
        resp = authed_client.get(url)
        assert resp.status_code == 200

    def test_pagination_context(self, authed_client, make_notification):
        # Create 30 notifications (page size is 25)
        for i in range(30):
            make_notification(title=f"Paginated {i}")
        url = reverse("accounts:notification-list")
        resp = authed_client.get(url)
        assert resp.status_code == 200
        page_obj = resp.context["page_obj"]
        assert page_obj.paginator.count == 30
        assert page_obj.paginator.num_pages == 2
        assert len(page_obj.object_list) == 25

    def test_page_two(self, authed_client, make_notification):
        for i in range(30):
            make_notification(title=f"Paginated {i}")
        url = reverse("accounts:notification-list")
        resp = authed_client.get(url, {"page": 2})
        assert resp.status_code == 200
        page_obj = resp.context["page_obj"]
        assert len(page_obj.object_list) == 5

    def test_type_filter_on_page(self, authed_client, make_notification):
        for i in range(3):
            make_notification(notification_type="ORDER")
        for i in range(2):
            make_notification(notification_type="SYSTEM")
        url = reverse("accounts:notification-list")
        resp = authed_client.get(url, {"type": "ORDER"})
        assert resp.status_code == 200
        assert resp.context["current_type"] == "ORDER"
        assert resp.context["page_obj"].paginator.count == 3


# =============================================================================
# 8. ORG-SCOPED FILTERING (tenant isolation)
# =============================================================================


class TestOrgScopedFiltering:
    """Users should only see notifications from their own organization."""

    def test_user_cannot_see_other_org_notifications(
        self, make_user, make_organization, organization
    ):
        # Create a second org with its own user
        other_org = make_organization(name="Other Org")
        other_user = make_user(email="other@example.com", organization=other_org)

        # Create notification in the other org
        Notification.objects.create(
            organization=other_org,
            user=other_user,
            title="Other org notification",
            message="Should not be visible",
            notification_type="ORDER",
            status="DELIVERED",
        )

        # Create notification in the test org for our user
        org_user = make_user(email="myorguser@example.com", organization=organization)
        Notification.objects.create(
            organization=organization,
            user=org_user,
            title="My org notification",
            message="Should be visible",
            notification_type="ORDER",
            status="DELIVERED",
        )

        # Login as org_user and check
        c = Client()
        c.force_login(org_user)

        url = reverse("accounts:notification-list-api")
        resp = c.get(url)
        notifications = resp.json()["notifications"]
        assert len(notifications) == 1
        assert notifications[0]["title"] == "My org notification"

    def test_unread_count_scoped_to_org(
        self, make_user, make_organization, organization
    ):
        other_org = make_organization(name="Other Org 2")
        other_user = make_user(email="other2@example.com", organization=other_org)

        # Notification in other org
        Notification.objects.create(
            organization=other_org,
            user=other_user,
            title="Other",
            message="Other msg",
            notification_type="ORDER",
            status="DELIVERED",
        )

        # Notification in our org
        org_user = make_user(email="myorguser2@example.com", organization=organization)
        Notification.objects.create(
            organization=organization,
            user=org_user,
            title="Mine",
            message="My msg",
            notification_type="ORDER",
            status="DELIVERED",
        )

        c = Client()
        c.force_login(org_user)
        url = reverse("accounts:notification-count-api")
        resp = c.get(url)
        assert resp.json()["count"] == 1

    def test_cannot_mark_other_org_notification_read(
        self, make_user, make_organization, organization
    ):
        other_org = make_organization(name="Other Org 3")
        other_user = make_user(email="other3@example.com", organization=other_org)

        other_notif = Notification.objects.create(
            organization=other_org,
            user=other_user,
            title="Other notif",
            message="Other message",
            notification_type="ORDER",
            status="DELIVERED",
        )

        org_user = make_user(email="myorguser3@example.com", organization=organization)
        c = Client()
        c.force_login(org_user)

        url = reverse(
            "accounts:notification-mark-read-api",
            kwargs={"notification_id": other_notif.id},
        )
        resp = c.post(url)
        assert resp.status_code == 404

        # Confirm it was NOT marked read
        other_notif.refresh_from_db()
        assert other_notif.status == "DELIVERED"
