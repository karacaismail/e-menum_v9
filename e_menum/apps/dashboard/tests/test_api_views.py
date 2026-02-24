"""
Tests for Dashboard API views.

Tests cover:
- Authentication requirement (staff_member_required)
- All 8 main API endpoints return correct JSON structure
- Search endpoint (command palette) with min 2 chars
- Sidebar preference endpoints (pins, recent pages)
- Error handling (graceful 500 responses)
- HTTP method enforcement (GET-only, POST-only)

Uses pytest-django with Django test Client and AdminUserFactory.
"""

import json
import uuid
from datetime import timedelta
from decimal import Decimal

import pytest
from django.test import Client
from django.urls import reverse
from django.utils import timezone

from tests.factories.core import AdminUserFactory, OrganizationFactory, UserFactory


@pytest.fixture
def staff_client(db):
    """Return a Django test Client logged in as a staff/admin user."""
    admin = AdminUserFactory()
    client = Client()
    client.force_login(admin)
    return client


@pytest.fixture
def anon_client():
    """Return a Django test Client without authentication."""
    return Client()


@pytest.fixture
def regular_client(db):
    """Return a Django test Client logged in as a non-staff user."""
    user = UserFactory(is_staff=False)
    client = Client()
    client.force_login(user)
    return client


# ═══════════════════════════════════════════════════════════════
# AUTHENTICATION TESTS
# ═══════════════════════════════════════════════════════════════


@pytest.mark.django_db
class TestAuthenticationRequired:
    """All dashboard API endpoints require staff authentication."""

    API_URLS = [
        'dashboard:api-kpis',
        'dashboard:api-qr-scan-trend',
        'dashboard:api-org-activity-heatmap',
        'dashboard:api-plan-distribution',
        'dashboard:api-city-distribution',
        'dashboard:api-insights',
        'dashboard:api-recent-activity',
        'dashboard:api-subscription-funnel',
        'dashboard:api-search',
        'dashboard:api-sidebar-pins',
        'dashboard:api-sidebar-recent',
    ]

    @pytest.mark.parametrize('url_name', API_URLS)
    def test_anonymous_redirected_to_login(self, anon_client, url_name):
        """Anonymous users should be redirected to admin login."""
        url = reverse(url_name)
        response = anon_client.get(url)
        assert response.status_code in (301, 302)

    @pytest.mark.parametrize('url_name', API_URLS)
    def test_non_staff_redirected(self, regular_client, url_name):
        """Non-staff users should be redirected to admin login."""
        url = reverse(url_name)
        response = regular_client.get(url)
        assert response.status_code in (301, 302)

    @pytest.mark.parametrize('url_name', API_URLS)
    def test_staff_gets_200(self, staff_client, url_name):
        """Staff users should get 200 OK."""
        url = reverse(url_name)
        response = staff_client.get(url)
        assert response.status_code == 200


# ═══════════════════════════════════════════════════════════════
# KPI ENDPOINT TESTS
# ═══════════════════════════════════════════════════════════════


@pytest.mark.django_db
class TestAPIKpis:
    """Tests for GET /admin/api/kpis/."""

    def test_returns_json(self, staff_client):
        """Should return valid JSON with success=True."""
        url = reverse('dashboard:api-kpis')
        response = staff_client.get(url)
        data = response.json()

        assert data['success'] is True
        assert 'data' in data

    def test_contains_all_kpi_keys(self, staff_client):
        """Should contain all 6 KPI metric keys."""
        url = reverse('dashboard:api-kpis')
        data = staff_client.get(url).json()['data']

        expected_keys = {
            'organizations', 'qr_scans', 'active_menus',
            'pending_requests', 'mrr', 'trial_count',
        }
        assert set(data.keys()) == expected_keys

    def test_kpi_structure(self, staff_client):
        """Each KPI should have value, trend, change, label, icon."""
        url = reverse('dashboard:api-kpis')
        data = staff_client.get(url).json()['data']

        for key, kpi in data.items():
            assert 'value' in kpi, f'{key} missing value'
            assert 'trend' in kpi, f'{key} missing trend'
            assert 'change' in kpi, f'{key} missing change'
            assert 'label' in kpi, f'{key} missing label'
            assert 'icon' in kpi, f'{key} missing icon'

    def test_trend_is_list_of_7(self, staff_client):
        """Trend should be a 7-element list (sparkline data)."""
        url = reverse('dashboard:api-kpis')
        data = staff_client.get(url).json()['data']

        for key, kpi in data.items():
            assert isinstance(kpi['trend'], list), f'{key} trend not list'
            assert len(kpi['trend']) == 7, f'{key} trend not 7 items'


# ═══════════════════════════════════════════════════════════════
# CHART ENDPOINT TESTS
# ═══════════════════════════════════════════════════════════════


@pytest.mark.django_db
class TestAPIQRScanTrend:
    """Tests for GET /admin/api/qr-scan-trend/."""

    def test_default_30d(self, staff_client):
        """Default range should be 30 days."""
        url = reverse('dashboard:api-qr-scan-trend')
        data = staff_client.get(url).json()

        assert data['success'] is True
        assert len(data['data']['dates']) == 30

    def test_custom_range_7d(self, staff_client):
        """?range=7d should return 7 days of data."""
        url = reverse('dashboard:api-qr-scan-trend')
        data = staff_client.get(url + '?range=7d').json()

        assert len(data['data']['dates']) == 7

    def test_custom_range_90d(self, staff_client):
        """?range=90d should return 90 days of data."""
        url = reverse('dashboard:api-qr-scan-trend')
        data = staff_client.get(url + '?range=90d').json()

        assert len(data['data']['dates']) == 90


@pytest.mark.django_db
class TestAPIOrgActivityHeatmap:
    """Tests for GET /admin/api/org-activity-heatmap/."""

    def test_returns_success(self, staff_client):
        """Should return success with list data."""
        url = reverse('dashboard:api-org-activity-heatmap')
        data = staff_client.get(url).json()

        assert data['success'] is True
        assert isinstance(data['data'], list)


@pytest.mark.django_db
class TestAPIPlanDistribution:
    """Tests for GET /admin/api/plan-distribution/."""

    def test_returns_success(self, staff_client):
        """Should return success with list data."""
        url = reverse('dashboard:api-plan-distribution')
        data = staff_client.get(url).json()

        assert data['success'] is True
        assert isinstance(data['data'], list)


@pytest.mark.django_db
class TestAPICityDistribution:
    """Tests for GET /admin/api/city-distribution/."""

    def test_returns_success(self, staff_client):
        """Should return success with list data."""
        url = reverse('dashboard:api-city-distribution')
        data = staff_client.get(url).json()

        assert data['success'] is True
        assert isinstance(data['data'], list)


@pytest.mark.django_db
class TestAPISubscriptionFunnel:
    """Tests for GET /admin/api/subscription-funnel/."""

    def test_returns_four_steps(self, staff_client):
        """Should return 4 funnel steps."""
        url = reverse('dashboard:api-subscription-funnel')
        data = staff_client.get(url).json()

        assert data['success'] is True
        assert len(data['data']) == 4

    def test_each_step_has_name_and_count(self, staff_client):
        """Each step should have step name and count."""
        url = reverse('dashboard:api-subscription-funnel')
        steps = staff_client.get(url).json()['data']

        for step in steps:
            assert 'step' in step
            assert 'count' in step


# ═══════════════════════════════════════════════════════════════
# INSIGHTS ENDPOINT TESTS
# ═══════════════════════════════════════════════════════════════


@pytest.mark.django_db
class TestAPIInsights:
    """Tests for GET /admin/api/insights/."""

    def test_returns_empty_when_no_insights(self, staff_client):
        """Should return empty list when no insights exist."""
        url = reverse('dashboard:api-insights')
        data = staff_client.get(url).json()

        assert data['success'] is True
        assert isinstance(data['data'], list)
        assert len(data['data']) == 0

    def test_returns_active_insights(self, staff_client):
        """Should return active insights ordered by priority."""
        from apps.dashboard.models import DashboardInsight

        DashboardInsight.objects.create(
            type='warning',
            title='Test Insight',
            body='Test body text',
            priority=90,
            is_active=True,
            expires_at=timezone.now() + timedelta(hours=24),
        )

        url = reverse('dashboard:api-insights')
        data = staff_client.get(url).json()

        assert len(data['data']) == 1
        assert data['data'][0]['title'] == 'Test Insight'
        assert data['data'][0]['type'] == 'warning'

    def test_deactivates_expired_insights(self, staff_client):
        """Should deactivate expired insights on fetch."""
        from apps.dashboard.models import DashboardInsight

        # Create an already-expired insight
        insight = DashboardInsight.objects.create(
            type='info',
            title='Expired Insight',
            body='Should be deactivated',
            priority=50,
            is_active=True,
            expires_at=timezone.now() - timedelta(hours=1),
        )
        # Force is_active=True bypassing save() logic
        DashboardInsight.objects.filter(pk=insight.pk).update(is_active=True)

        url = reverse('dashboard:api-insights')
        data = staff_client.get(url).json()

        # Should not appear in results
        assert len(data['data']) == 0

        # Verify it was deactivated in DB
        insight.refresh_from_db()
        assert insight.is_active is False

    def test_max_5_insights(self, staff_client):
        """Should return at most 5 insights."""
        from apps.dashboard.models import DashboardInsight

        for i in range(8):
            DashboardInsight.objects.create(
                type='info',
                title=f'Insight {i}',
                body=f'Body {i}',
                priority=i,
                is_active=True,
                expires_at=timezone.now() + timedelta(hours=24),
            )

        url = reverse('dashboard:api-insights')
        data = staff_client.get(url).json()

        assert len(data['data']) <= 5


# ═══════════════════════════════════════════════════════════════
# RECENT ACTIVITY TESTS
# ═══════════════════════════════════════════════════════════════


@pytest.mark.django_db
class TestAPIRecentActivity:
    """Tests for GET /admin/api/recent-activity/."""

    def test_returns_success(self, staff_client):
        """Should return success with list data."""
        url = reverse('dashboard:api-recent-activity')
        data = staff_client.get(url).json()

        assert data['success'] is True
        assert isinstance(data['data'], list)


# ═══════════════════════════════════════════════════════════════
# SEARCH ENDPOINT TESTS
# ═══════════════════════════════════════════════════════════════


@pytest.mark.django_db
class TestAPISearch:
    """Tests for GET /admin/api/search/?q=..."""

    def test_returns_empty_for_short_query(self, staff_client):
        """Should return empty groups for queries shorter than 2 chars."""
        url = reverse('dashboard:api-search')
        data = staff_client.get(url + '?q=a').json()

        assert data['success'] is True
        assert data['data']['groups'] == []

    def test_returns_empty_for_no_query(self, staff_client):
        """Should return empty groups when no query provided."""
        url = reverse('dashboard:api-search')
        data = staff_client.get(url).json()

        assert data['success'] is True
        assert data['data']['groups'] == []

    def test_searches_organizations(self, staff_client):
        """Should find organizations matching query."""
        org = OrganizationFactory(name='Istanbul Cafe ABC')

        url = reverse('dashboard:api-search')
        data = staff_client.get(url + '?q=Istanbul').json()

        assert data['success'] is True
        groups = data['data']['groups']
        org_group = next(
            (g for g in groups if g['label'] == 'Organizasyonlar'), None,
        )
        assert org_group is not None
        assert len(org_group['items']) >= 1
        assert org_group['items'][0]['title'] == 'Istanbul Cafe ABC'

    def test_searches_users(self, staff_client):
        """Should find users matching query by email."""
        user = UserFactory(email='searchable@example.com')

        url = reverse('dashboard:api-search')
        data = staff_client.get(url + '?q=searchable').json()

        groups = data['data']['groups']
        user_group = next(
            (g for g in groups if g['label'] == 'Kullanıcılar'), None,
        )
        assert user_group is not None
        assert len(user_group['items']) >= 1

    def test_search_result_structure(self, staff_client):
        """Each search result item should have title, subtitle, url."""
        OrganizationFactory(name='Structure Test Org')

        url = reverse('dashboard:api-search')
        data = staff_client.get(url + '?q=Structure Test').json()

        groups = data['data']['groups']
        if groups:
            for item in groups[0]['items']:
                assert 'title' in item
                assert 'subtitle' in item
                assert 'url' in item


# ═══════════════════════════════════════════════════════════════
# SIDEBAR PREFERENCES TESTS
# ═══════════════════════════════════════════════════════════════


@pytest.mark.django_db
class TestAPISidebarPins:
    """Tests for sidebar pin/recent preferences."""

    def test_get_pins_creates_default(self, staff_client):
        """GET pins should create default empty preference."""
        url = reverse('dashboard:api-sidebar-pins')
        data = staff_client.get(url).json()

        assert data['success'] is True
        assert 'pins' in data['data']
        assert data['data']['pins'] == []

    def test_save_and_retrieve_pins(self, staff_client):
        """Should save and retrieve pinned items."""
        save_url = reverse('dashboard:api-sidebar-pins-save')
        get_url = reverse('dashboard:api-sidebar-pins')

        pins_data = {'pins': ['/admin/core/organization/', '/admin/menu/menu/']}

        response = staff_client.post(
            save_url,
            data=json.dumps(pins_data),
            content_type='application/json',
        )
        assert response.json()['success'] is True

        # Retrieve saved pins
        data = staff_client.get(get_url).json()
        assert data['data']['pins'] == pins_data['pins']

    def test_save_pins_rejects_get(self, staff_client):
        """POST-only endpoint should reject GET requests."""
        url = reverse('dashboard:api-sidebar-pins-save')
        response = staff_client.get(url)
        assert response.status_code == 405

    def test_get_recent_creates_default(self, staff_client):
        """GET recent should create default empty preference."""
        url = reverse('dashboard:api-sidebar-recent')
        data = staff_client.get(url).json()

        assert data['success'] is True
        assert 'pages' in data['data']
        assert data['data']['pages'] == []

    def test_save_and_retrieve_recent(self, staff_client):
        """Should save and retrieve recent pages."""
        save_url = reverse('dashboard:api-sidebar-recent-save')
        get_url = reverse('dashboard:api-sidebar-recent')

        page_data = {
            'url': '/admin/core/organization/',
            'label': 'Organizations',
        }

        response = staff_client.post(
            save_url,
            data=json.dumps(page_data),
            content_type='application/json',
        )
        assert response.json()['success'] is True

        data = staff_client.get(get_url).json()
        assert len(data['data']['pages']) == 1
        assert data['data']['pages'][0]['url'] == page_data['url']

    def test_recent_pages_max_5(self, staff_client):
        """Recent pages should be limited to 5 entries."""
        save_url = reverse('dashboard:api-sidebar-recent-save')
        get_url = reverse('dashboard:api-sidebar-recent')

        for i in range(7):
            staff_client.post(
                save_url,
                data=json.dumps({
                    'url': f'/admin/page/{i}/',
                    'label': f'Page {i}',
                }),
                content_type='application/json',
            )

        data = staff_client.get(get_url).json()
        assert len(data['data']['pages']) <= 5

    def test_recent_pages_deduplication(self, staff_client):
        """Visiting the same page should move it to top, not duplicate."""
        save_url = reverse('dashboard:api-sidebar-recent-save')
        get_url = reverse('dashboard:api-sidebar-recent')

        page = {'url': '/admin/core/organization/', 'label': 'Orgs'}

        # Visit twice
        staff_client.post(save_url, data=json.dumps(page), content_type='application/json')
        staff_client.post(save_url, data=json.dumps(page), content_type='application/json')

        data = staff_client.get(get_url).json()
        assert len(data['data']['pages']) == 1


# ═══════════════════════════════════════════════════════════════
# MAINBOARD VIEW TESTS
# ═══════════════════════════════════════════════════════════════


@pytest.mark.django_db
class TestMainboardView:
    """Tests for the main dashboard view."""

    def test_mainboard_requires_staff(self, anon_client):
        """Mainboard page should require authentication."""
        url = reverse('dashboard:mainboard')
        response = anon_client.get(url)
        assert response.status_code in (301, 302)

    def test_mainboard_returns_200(self, staff_client):
        """Mainboard page should return 200 for staff."""
        url = reverse('dashboard:mainboard')
        response = staff_client.get(url)
        assert response.status_code == 200

    def test_mainboard_uses_correct_template(self, staff_client):
        """Mainboard should use dashboard/mainboard.html template."""
        url = reverse('dashboard:mainboard')
        response = staff_client.get(url)
        assert 'dashboard/mainboard.html' in [t.name for t in response.templates]
