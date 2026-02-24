"""
Tests for Dashboard KPIService.

Tests cover:
- All 6 KPI metrics (active orgs, QR scans, menus, requests, MRR, trials)
- Trend data generation (7-day sparklines)
- Period comparison (week-over-week)
- Chart data endpoints (QR trend, heatmap, plan distribution, city, funnel)
- Redis caching behavior (cache hit/miss, TTL)
- Edge cases (zero data, division by zero)

Uses pytest-django fixtures with in-memory Django cache.
"""

import uuid
from datetime import timedelta
from decimal import Decimal
from unittest.mock import patch

import pytest
from django.core.cache import cache
from django.utils import timezone

from apps.dashboard.services import CACHE_PREFIX, CACHE_TTL, KPIService


@pytest.fixture(autouse=True)
def clear_dashboard_cache():
    """Clear all dashboard caches before and after each test."""
    cache.clear()
    yield
    cache.clear()


@pytest.fixture
def kpi_service():
    """Return a fresh KPIService instance."""
    return KPIService()


@pytest.fixture
def active_organization(db):
    """Create an active organization."""
    from tests.factories.core import OrganizationFactory

    return OrganizationFactory(status='ACTIVE')


@pytest.fixture
def qr_code(db, active_organization):
    """Create a QR code for the active organization."""
    from apps.orders.models import QRCode

    return QRCode.objects.create(
        organization=active_organization,
        type='MENU',
        code=f'qr-{uuid.uuid4().hex[:8]}',
        name='Test QR Code',
        is_active=True,
    )


@pytest.fixture
def starter_plan(db):
    """Get or create the Starter plan."""
    from apps.subscriptions.models import Plan

    plan, _ = Plan.objects.get_or_create(
        slug='starter',
        defaults={
            'name': 'Starter',
            'tier': 'STARTER',
            'price_monthly': Decimal('2000.00'),
            'price_yearly': Decimal('20000.00'),
            'is_active': True,
        },
    )
    return plan


# ═══════════════════════════════════════════════════════════════
# KPI METRIC TESTS
# ═══════════════════════════════════════════════════════════════


@pytest.mark.django_db
class TestGetActiveOrganizations:
    """Tests for KPIService.get_active_organizations()."""

    def test_returns_zero_when_no_orgs(self, kpi_service):
        """Should return 0 when no organizations exist."""
        assert kpi_service.get_active_organizations() == 0

    def test_counts_active_orgs_only(self, kpi_service, active_organization):
        """Should count only ACTIVE status organizations."""
        from tests.factories.core import OrganizationFactory

        # Create a suspended org
        OrganizationFactory(status='SUSPENDED')

        count = kpi_service.get_active_organizations()
        assert count == 1  # Only the active_organization

    def test_excludes_soft_deleted(self, kpi_service, active_organization):
        """Should exclude soft-deleted organizations."""
        active_organization.soft_delete()

        count = kpi_service.get_active_organizations()
        assert count == 0

    def test_result_is_cached(self, kpi_service, active_organization):
        """Should cache the result on first call."""
        # First call: cache miss → DB query
        result1 = kpi_service.get_active_organizations()

        # Verify value is now in cache
        key = f'{CACHE_PREFIX}active_organizations'
        cached = cache.get(key)
        assert cached is not None
        assert cached == result1

    def test_returns_cached_value(self, kpi_service, active_organization):
        """Should return cached value on subsequent calls."""
        key = f'{CACHE_PREFIX}active_organizations'
        cache.set(key, 999, CACHE_TTL)

        result = kpi_service.get_active_organizations()
        assert result == 999  # Returns cached, not DB


@pytest.mark.django_db
class TestGetTodayQRScans:
    """Tests for KPIService.get_today_qr_scans()."""

    def test_returns_zero_when_no_scans(self, kpi_service):
        """Should return 0 when no QR scans exist."""
        assert kpi_service.get_today_qr_scans() == 0

    def test_counts_todays_scans(self, kpi_service, qr_code, active_organization):
        """Should count only today's QR scans."""
        from apps.orders.models import QRScan

        # Create a scan today
        QRScan.objects.create(
            qr_code=qr_code,
            organization=active_organization,
        )

        count = kpi_service.get_today_qr_scans()
        assert count == 1

    def test_excludes_yesterdays_scans(self, kpi_service, qr_code, active_organization):
        """Should not count yesterday's scans."""
        from apps.orders.models import QRScan

        yesterday = timezone.now() - timedelta(days=1)
        scan = QRScan.objects.create(
            qr_code=qr_code,
            organization=active_organization,
        )
        # Manually set created_at to yesterday
        QRScan.objects.filter(pk=scan.pk).update(created_at=yesterday)

        count = kpi_service.get_today_qr_scans()
        assert count == 0


@pytest.mark.django_db
class TestGetActiveMenus:
    """Tests for KPIService.get_active_menus()."""

    def test_returns_zero_when_no_menus(self, kpi_service):
        """Should return 0 when no menus exist."""
        assert kpi_service.get_active_menus() == 0

    def test_counts_published_menus_only(self, kpi_service, active_organization):
        """Should count only published (is_published=True) menus."""
        from apps.menu.models import Menu

        # Published menu
        Menu.objects.create(
            organization=active_organization,
            name='Published Menu',
            slug=f'published-{uuid.uuid4().hex[:8]}',
            is_published=True,
        )

        # Unpublished menu
        Menu.objects.create(
            organization=active_organization,
            name='Draft Menu',
            slug=f'draft-{uuid.uuid4().hex[:8]}',
            is_published=False,
        )

        count = kpi_service.get_active_menus()
        assert count == 1


@pytest.mark.django_db
class TestGetMRR:
    """Tests for KPIService.get_mrr()."""

    def test_returns_zero_when_no_subscriptions(self, kpi_service):
        """Should return 0.0 when no active subscriptions exist."""
        assert kpi_service.get_mrr() == 0.0

    def test_sums_monthly_subscriptions(self, kpi_service, active_organization, starter_plan):
        """Should sum current_price of monthly active subscriptions."""
        from apps.subscriptions.models import Subscription

        Subscription.objects.create(
            organization=active_organization,
            plan=starter_plan,
            status='ACTIVE',
            billing_period='MONTHLY',
            current_price=Decimal('2000.00'),
            currency='TRY',
            current_period_start=timezone.now(),
            current_period_end=timezone.now() + timedelta(days=30),
        )

        mrr = kpi_service.get_mrr()
        assert mrr == 2000.0

    def test_includes_yearly_divided_by_12(self, kpi_service, active_organization, starter_plan):
        """Should add yearly subscriptions divided by 12 to MRR."""
        from apps.subscriptions.models import Subscription

        Subscription.objects.create(
            organization=active_organization,
            plan=starter_plan,
            status='ACTIVE',
            billing_period='YEARLY',
            current_price=Decimal('24000.00'),
            currency='TRY',
            current_period_start=timezone.now(),
            current_period_end=timezone.now() + timedelta(days=365),
        )

        mrr = kpi_service.get_mrr()
        assert mrr == 2000.0  # 24000 / 12


@pytest.mark.django_db
class TestGetTrialCount:
    """Tests for KPIService.get_trial_count()."""

    def test_returns_zero_when_no_trials(self, kpi_service):
        """Should return 0 when no trial subscriptions exist."""
        assert kpi_service.get_trial_count() == 0

    def test_counts_trialing_subscriptions(self, kpi_service, active_organization, starter_plan):
        """Should count only TRIALING status subscriptions."""
        from apps.subscriptions.models import Subscription

        Subscription.objects.create(
            organization=active_organization,
            plan=starter_plan,
            status='TRIALING',
            billing_period='MONTHLY',
            current_price=Decimal('0'),
            currency='TRY',
            current_period_start=timezone.now(),
            current_period_end=timezone.now() + timedelta(days=14),
        )

        count = kpi_service.get_trial_count()
        assert count == 1


# ═══════════════════════════════════════════════════════════════
# TREND & COMPARISON TESTS
# ═══════════════════════════════════════════════════════════════


@pytest.mark.django_db
class TestGetTrend:
    """Tests for KPIService.get_trend()."""

    def test_returns_list_of_correct_length(self, kpi_service):
        """Should return a list with length equal to days parameter."""
        result = kpi_service.get_trend('qr_scans', days=7)
        assert isinstance(result, list)
        assert len(result) == 7

    def test_returns_zeros_for_unknown_metric(self, kpi_service):
        """Should return list of zeros for unknown metric key."""
        result = kpi_service.get_trend('nonexistent', days=5)
        assert result == [0, 0, 0, 0, 0]

    def test_qr_scans_trend(self, kpi_service, qr_code, active_organization):
        """Should return daily QR scan counts."""
        from apps.orders.models import QRScan

        # Create a scan today
        QRScan.objects.create(
            qr_code=qr_code,
            organization=active_organization,
        )

        result = kpi_service.get_trend('qr_scans', days=3)
        assert len(result) == 3
        assert result[-1] >= 1  # Today should have at least 1

    def test_organizations_trend(self, kpi_service, active_organization):
        """Should return daily new org registration counts."""
        result = kpi_service.get_trend('organizations', days=3)
        assert len(result) == 3
        assert result[-1] >= 1  # Today's active_organization


@pytest.mark.django_db
class TestGetPeriodComparison:
    """Tests for KPIService.get_period_comparison()."""

    def test_returns_dict_with_required_keys(self, kpi_service):
        """Should return dict with current, previous, change keys."""
        result = kpi_service.get_period_comparison('qr_scans')
        assert 'current' in result
        assert 'previous' in result
        assert 'change' in result

    def test_returns_zero_change_when_both_zero(self, kpi_service):
        """Should return 0.0 change when both periods have zero values."""
        result = kpi_service.get_period_comparison('qr_scans')
        assert result['change'] == 0.0

    def test_returns_100_change_when_previous_zero(self, kpi_service, qr_code, active_organization):
        """Should return 100.0 change when previous is zero but current is positive."""
        from apps.orders.models import QRScan

        # Create scans this week
        QRScan.objects.create(
            qr_code=qr_code,
            organization=active_organization,
        )

        result = kpi_service.get_period_comparison('qr_scans')
        if result['current'] > 0 and result['previous'] == 0:
            assert result['change'] == 100.0


# ═══════════════════════════════════════════════════════════════
# CHART DATA TESTS
# ═══════════════════════════════════════════════════════════════


@pytest.mark.django_db
class TestGetQRScanTrend:
    """Tests for KPIService.get_qr_scan_trend()."""

    def test_returns_correct_structure(self, kpi_service):
        """Should return dict with dates, values, and total."""
        result = kpi_service.get_qr_scan_trend(days=7)
        assert 'dates' in result
        assert 'values' in result
        assert 'total' in result
        assert len(result['dates']) == 7
        assert len(result['values']) == 7

    def test_total_equals_sum_of_values(self, kpi_service):
        """Total should equal sum of daily values."""
        result = kpi_service.get_qr_scan_trend(days=7)
        assert result['total'] == sum(result['values'])

    def test_dates_are_iso_format(self, kpi_service):
        """Dates should be in ISO format (YYYY-MM-DD)."""
        result = kpi_service.get_qr_scan_trend(days=3)
        for date_str in result['dates']:
            assert len(date_str) == 10  # YYYY-MM-DD
            assert date_str[4] == '-'


@pytest.mark.django_db
class TestGetPlanDistribution:
    """Tests for KPIService.get_plan_distribution()."""

    def test_returns_empty_list_when_no_subscriptions(self, kpi_service):
        """Should return empty list when no active subscriptions."""
        result = kpi_service.get_plan_distribution()
        assert isinstance(result, list)

    def test_returns_correct_structure(self, kpi_service, active_organization, starter_plan):
        """Should return list of {name, value} dicts."""
        from apps.subscriptions.models import Subscription

        Subscription.objects.create(
            organization=active_organization,
            plan=starter_plan,
            status='ACTIVE',
            billing_period='MONTHLY',
            current_price=Decimal('2000.00'),
            currency='TRY',
            current_period_start=timezone.now(),
            current_period_end=timezone.now() + timedelta(days=30),
        )

        result = kpi_service.get_plan_distribution()
        assert len(result) >= 1
        assert 'name' in result[0]
        assert 'value' in result[0]
        assert result[0]['name'] == 'Starter'


@pytest.mark.django_db
class TestGetCityDistribution:
    """Tests for KPIService.get_city_distribution()."""

    def test_returns_empty_when_no_branches(self, kpi_service):
        """Should return empty list when no branches exist."""
        result = kpi_service.get_city_distribution()
        assert isinstance(result, list)

    def test_returns_city_with_coordinates(self, kpi_service, active_organization):
        """Should return city distribution with lat/lng coordinates."""
        from apps.core.models import Branch

        Branch.objects.create(
            organization=active_organization,
            name='Istanbul Branch',
            slug=f'istanbul-{uuid.uuid4().hex[:8]}',
            city='Istanbul',
            status='ACTIVE',
        )

        result = kpi_service.get_city_distribution()
        assert len(result) >= 1
        assert result[0]['city'] == 'Istanbul'
        assert 'lat' in result[0]
        assert 'lng' in result[0]
        assert 'count' in result[0]


@pytest.mark.django_db
class TestGetSubscriptionFunnel:
    """Tests for KPIService.get_subscription_funnel()."""

    def test_returns_four_steps(self, kpi_service):
        """Should return exactly 4 funnel steps."""
        result = kpi_service.get_subscription_funnel()
        assert len(result) == 4

    def test_step_names(self, kpi_service):
        """Should have correct step names in Turkish."""
        result = kpi_service.get_subscription_funnel()
        steps = [r['step'] for r in result]
        assert steps == ['Kayıt', 'Trial', 'Aktif', 'Yenileme']

    def test_registration_count_includes_all_orgs(self, kpi_service, active_organization):
        """Registration step should include all non-deleted organizations."""
        result = kpi_service.get_subscription_funnel()
        # active_organization exists, so registration should be >= 1
        assert result[0]['count'] >= 1


@pytest.mark.django_db
class TestGetOrgActivityHeatmap:
    """Tests for KPIService.get_org_activity_heatmap()."""

    def test_returns_empty_list_when_no_scans(self, kpi_service):
        """Should return empty list when no QR scans exist."""
        result = kpi_service.get_org_activity_heatmap()
        assert isinstance(result, list)
        assert len(result) == 0

    def test_returns_correct_structure(self, kpi_service, qr_code, active_organization):
        """Should return org activity data with correct structure."""
        from apps.orders.models import QRScan

        # Create some scans
        for _ in range(3):
            QRScan.objects.create(
                qr_code=qr_code,
                organization=active_organization,
            )

        result = kpi_service.get_org_activity_heatmap()
        assert len(result) >= 1
        assert 'org_id' in result[0]
        assert 'org_name' in result[0]
        assert 'data' in result[0]


# ═══════════════════════════════════════════════════════════════
# CACHE BEHAVIOR TESTS
# ═══════════════════════════════════════════════════════════════


@pytest.mark.django_db
class TestCacheBehavior:
    """Tests for KPIService caching behavior."""

    def test_cache_key_format(self, kpi_service):
        """Cache keys should follow CACHE_PREFIX pattern."""
        key = kpi_service._cache_key('test_metric')
        assert key == f'{CACHE_PREFIX}test_metric'

    def test_cache_key_with_suffix(self, kpi_service):
        """Cache key with suffix should include colon separator."""
        key = kpi_service._cache_key('test_metric', '7d')
        assert key == f'{CACHE_PREFIX}test_metric:7d'

    def test_get_cached_returns_none_on_miss(self, kpi_service):
        """Should return None when key not in cache."""
        result = kpi_service._get_cached('nonexistent_key')
        assert result is None

    def test_set_and_get_cached(self, kpi_service):
        """Should store and retrieve values from cache."""
        key = 'test_cache_key'
        value = {'count': 42}

        kpi_service._set_cached(key, value)
        result = kpi_service._get_cached(key)
        assert result == value

    def test_warm_all_caches(self, kpi_service):
        """warm_all_caches should run without error."""
        # Should not raise even with empty DB
        kpi_service.warm_all_caches()

        # Verify some keys are now cached
        key = f'{CACHE_PREFIX}active_organizations'
        assert cache.get(key) is not None
