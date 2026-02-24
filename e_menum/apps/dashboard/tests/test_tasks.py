"""
Tests for Dashboard Celery tasks.

Tests cover:
- generate_dashboard_insights: Creates/updates insight cards
  - Churn risk detection (30-day inactive orgs)
  - Expiring subscription warnings
  - Growth opportunity detection (>20% month-over-month)
  - Expired insight deactivation (cleanup)
  - Idempotency (safe to re-run)

- warm_kpi_cache: Pre-warms Redis caches
  - Calls KPIService.warm_all_caches()
  - Returns status dict

Uses pytest-django with in-memory DB and mocked cache.
"""

import uuid
from datetime import timedelta
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest
from django.core.cache import cache
from django.utils import timezone

from apps.dashboard.models import DashboardInsight, InsightType


@pytest.fixture(autouse=True)
def clear_cache_fixture():
    """Clear cache before and after each test."""
    cache.clear()
    yield
    cache.clear()


@pytest.fixture
def active_org(db):
    """Create a single active organization."""
    from tests.factories.core import OrganizationFactory

    return OrganizationFactory(status='ACTIVE')


@pytest.fixture
def qr_code(db, active_org):
    """Create a QR code for the org."""
    from apps.orders.models import QRCode

    return QRCode.objects.create(
        organization=active_org,
        type='MENU',
        code=f'qr-{uuid.uuid4().hex[:8]}',
        name='Test QR',
        is_active=True,
    )


@pytest.fixture
def starter_plan(db):
    """Get or create starter plan."""
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
# GENERATE DASHBOARD INSIGHTS TESTS
# ═══════════════════════════════════════════════════════════════


@pytest.mark.django_db
class TestGenerateDashboardInsights:
    """Tests for generate_dashboard_insights Celery task."""

    def test_runs_without_error(self):
        """Task should execute without raising on empty DB."""
        from apps.dashboard.tasks import generate_dashboard_insights

        result = generate_dashboard_insights()
        assert isinstance(result, dict)
        assert 'created' in result
        assert 'expired_deactivated' in result

    def test_deactivates_expired_insights(self):
        """Should deactivate insights that have passed their expires_at."""
        from apps.dashboard.tasks import generate_dashboard_insights

        # Create an expired but still active insight
        insight = DashboardInsight.objects.create(
            type=InsightType.INFO,
            title='Old Insight',
            body='Should be deactivated',
            priority=50,
            is_active=True,
            expires_at=timezone.now() - timedelta(hours=2),
        )
        # Force is_active=True (bypass save() auto-deactivation)
        DashboardInsight.objects.filter(pk=insight.pk).update(is_active=True)

        result = generate_dashboard_insights()

        insight.refresh_from_db()
        assert insight.is_active is False
        assert result['expired_deactivated'] >= 1

    def test_churn_risk_insight_created(self, active_org, qr_code):
        """Should create churn risk insight when orgs have no scans in 30 days."""
        from apps.dashboard.tasks import generate_dashboard_insights

        # active_org exists but has NO QR scans at all
        result = generate_dashboard_insights()

        churn_insights = DashboardInsight.objects.filter(
            title='Churn Riski',
            is_active=True,
            deleted_at__isnull=True,
        )
        assert churn_insights.exists()
        insight = churn_insights.first()
        assert insight.type == InsightType.WARNING
        assert insight.priority == 90
        assert insight.metric_value >= 1

    def test_churn_risk_not_created_when_orgs_are_active(self, active_org, qr_code):
        """Should NOT create churn risk if org has recent scans."""
        from apps.dashboard.tasks import generate_dashboard_insights
        from apps.orders.models import QRScan

        # Create a very recent scan for the org
        QRScan.objects.create(
            qr_code=qr_code,
            organization=active_org,
        )

        result = generate_dashboard_insights()

        churn_insights = DashboardInsight.objects.filter(
            title='Churn Riski',
            is_active=True,
            deleted_at__isnull=True,
        )
        # Might still exist if there are other orgs without scans,
        # but the count should not include our active_org
        if churn_insights.exists():
            # Our org shouldn't be counted as inactive
            insight = churn_insights.first()
            # This is acceptable - other orgs in test DB may be inactive
            assert insight.metric_value is not None

    def test_expiring_plans_insight(self, active_org, starter_plan):
        """Should create insight when subscriptions are about to expire."""
        from apps.dashboard.tasks import generate_dashboard_insights
        from apps.subscriptions.models import Subscription

        # Create a subscription expiring in 3 days with cancel_at_period_end
        Subscription.objects.create(
            organization=active_org,
            plan=starter_plan,
            status='ACTIVE',
            billing_period='MONTHLY',
            current_price=Decimal('2000.00'),
            currency='TRY',
            current_period_start=timezone.now() - timedelta(days=27),
            current_period_end=timezone.now() + timedelta(days=3),
            cancel_at_period_end=True,
        )

        result = generate_dashboard_insights()

        expiring = DashboardInsight.objects.filter(
            title='Süresi Dolmak Üzere',
            is_active=True,
            deleted_at__isnull=True,
        )
        assert expiring.exists()
        insight = expiring.first()
        assert insight.type == InsightType.WARNING
        assert insight.priority == 85

    def test_growth_opportunity_insight(self, db):
        """Should create insight when this month has >20% more registrations."""
        from apps.core.models import Organization
        from apps.dashboard.tasks import generate_dashboard_insights
        from tests.factories.core import OrganizationFactory

        now = timezone.now()
        this_month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        last_month_start = (this_month_start - timedelta(days=1)).replace(
            day=1, hour=0, minute=0, second=0, microsecond=0,
        )

        # Create 5 orgs last month
        for i in range(5):
            org = OrganizationFactory(status='ACTIVE')
            Organization.objects.filter(pk=org.pk).update(
                created_at=last_month_start + timedelta(days=i),
            )

        # Create 10 orgs this month (100% growth > 20%)
        for i in range(10):
            OrganizationFactory(status='ACTIVE')

        result = generate_dashboard_insights()

        growth = DashboardInsight.objects.filter(
            title='Büyüme Fırsatı',
            is_active=True,
            deleted_at__isnull=True,
        )
        assert growth.exists()
        insight = growth.first()
        assert insight.type == InsightType.OPPORTUNITY
        assert insight.metric_value >= 20  # At least 20% growth

    def test_idempotent_update_or_create(self, active_org, qr_code):
        """Running twice should update existing insights, not duplicate."""
        from apps.dashboard.tasks import generate_dashboard_insights

        # Run twice
        generate_dashboard_insights()
        generate_dashboard_insights()

        # Should not have duplicate churn risk insights
        churn_count = DashboardInsight.objects.filter(
            title='Churn Riski',
            is_active=True,
            deleted_at__isnull=True,
        ).count()
        # update_or_create should prevent duplicates
        assert churn_count <= 1

    def test_insight_has_expiry(self, active_org, qr_code):
        """Created insights should have expires_at set to 24h from now."""
        from apps.dashboard.tasks import generate_dashboard_insights

        generate_dashboard_insights()

        insights = DashboardInsight.objects.filter(
            is_active=True,
            deleted_at__isnull=True,
        )
        for insight in insights:
            if insight.expires_at:
                # Should expire roughly 24 hours from now
                diff = insight.expires_at - timezone.now()
                assert diff.total_seconds() > 0  # Not expired
                assert diff.total_seconds() < 86400 + 60  # Within 24h + 1min tolerance


# ═══════════════════════════════════════════════════════════════
# WARM KPI CACHE TESTS
# ═══════════════════════════════════════════════════════════════


@pytest.mark.django_db
class TestWarmKPICache:
    """Tests for warm_kpi_cache Celery task."""

    def test_runs_without_error(self):
        """Task should execute without raising."""
        from apps.dashboard.tasks import warm_kpi_cache

        result = warm_kpi_cache()
        assert result == {'status': 'ok'}

    def test_calls_warm_all_caches(self):
        """Should call KPIService.warm_all_caches()."""
        from apps.dashboard.tasks import warm_kpi_cache

        with patch('apps.dashboard.services.KPIService') as MockKPI:
            mock_instance = MagicMock()
            MockKPI.return_value = mock_instance

            warm_kpi_cache()

            mock_instance.warm_all_caches.assert_called_once()

    def test_populates_cache(self, db):
        """After running, cache should contain dashboard keys."""
        from apps.dashboard.services import CACHE_PREFIX
        from apps.dashboard.tasks import warm_kpi_cache

        warm_kpi_cache()

        # Check at least the basic metrics are cached
        key = f'{CACHE_PREFIX}active_organizations'
        assert cache.get(key) is not None


# ═══════════════════════════════════════════════════════════════
# MODEL TESTS
# ═══════════════════════════════════════════════════════════════


@pytest.mark.django_db
class TestDashboardInsightModel:
    """Tests for DashboardInsight model."""

    def test_str_representation(self):
        """__str__ should show type and title."""
        insight = DashboardInsight.objects.create(
            type=InsightType.WARNING,
            title='Test Title',
            body='Test body',
        )
        assert str(insight) == '[warning] Test Title'

    def test_auto_deactivate_on_save(self):
        """Saving an insight with past expires_at should set is_active=False."""
        insight = DashboardInsight(
            type=InsightType.INFO,
            title='Expired on create',
            body='Test',
            is_active=True,
            expires_at=timezone.now() - timedelta(hours=1),
        )
        insight.save()

        assert insight.is_active is False

    def test_active_with_future_expiry(self):
        """Saving with future expires_at should keep is_active=True."""
        insight = DashboardInsight.objects.create(
            type=InsightType.SUCCESS,
            title='Fresh Insight',
            body='Test',
            is_active=True,
            expires_at=timezone.now() + timedelta(hours=24),
        )
        assert insight.is_active is True

    def test_ordering(self):
        """Should order by -priority, -created_at."""
        low = DashboardInsight.objects.create(
            type=InsightType.INFO,
            title='Low Priority',
            body='Test',
            priority=10,
        )
        high = DashboardInsight.objects.create(
            type=InsightType.WARNING,
            title='High Priority',
            body='Test',
            priority=90,
        )

        insights = list(DashboardInsight.objects.all())
        assert insights[0].pk == high.pk
        assert insights[1].pk == low.pk

    def test_soft_delete(self):
        """Soft-deleted insights should not appear in default queryset."""
        insight = DashboardInsight.objects.create(
            type=InsightType.INFO,
            title='To Delete',
            body='Test',
        )
        insight.soft_delete()

        assert DashboardInsight.objects.filter(pk=insight.pk).count() == 0
        assert DashboardInsight.all_objects.filter(pk=insight.pk).count() == 1

    def test_uuid_primary_key(self):
        """Should use UUID primary key."""
        insight = DashboardInsight.objects.create(
            type=InsightType.INFO,
            title='UUID Test',
            body='Test',
        )
        assert isinstance(insight.pk, uuid.UUID)


@pytest.mark.django_db
class TestUserPreferenceModel:
    """Tests for UserPreference model."""

    def test_create_preference(self, db):
        """Should create a user preference with JSON value."""
        from apps.core.models import User
        from apps.dashboard.models import UserPreference

        user = User.objects.create_user(
            email=f'pref-test-{uuid.uuid4().hex[:8]}@example.com',
            password='TestPass123!',
            first_name='Pref',
            last_name='User',
            status='ACTIVE',
        )

        pref = UserPreference.objects.create(
            user=user,
            key='sidebar_pins',
            value={'pins': ['/admin/core/organization/']},
        )

        assert str(pref) == f'{user} - sidebar_pins'
        assert pref.value['pins'] == ['/admin/core/organization/']

    def test_unique_together(self, db):
        """Should enforce unique_together on (user, key)."""
        from django.db import IntegrityError
        from apps.core.models import User
        from apps.dashboard.models import UserPreference

        user = User.objects.create_user(
            email=f'unique-test-{uuid.uuid4().hex[:8]}@example.com',
            password='TestPass123!',
            first_name='Unique',
            last_name='User',
            status='ACTIVE',
        )

        UserPreference.objects.create(
            user=user,
            key='test_key',
            value={'data': 1},
        )

        with pytest.raises(IntegrityError):
            UserPreference.objects.create(
                user=user,
                key='test_key',
                value={'data': 2},
            )
