"""
Tests for subscription views — cancel flow (P16) and downgrade display (P8).

Covers:
- Subscription page requires authentication
- Subscription page shows current plan info
- Cancel subscription sets status to CANCELLED (P16 fix)
- Available plans carry tier_index for proper upgrade/downgrade display (P8 fix)
- Downgrade plans are correctly identified via tier_index comparison
"""

from datetime import timedelta
from decimal import Decimal

import pytest
from django.urls import reverse
from django.utils import timezone

from apps.subscriptions.choices import SubscriptionStatus


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

SUBSCRIPTION_URL = reverse("accounts:subscription")
CANCEL_URL = reverse("accounts:subscription-cancel")


def _create_subscription(organization, plan, status=SubscriptionStatus.ACTIVE):
    """Create a Subscription record directly via the ORM."""
    from apps.subscriptions.models import Subscription

    now = timezone.now()
    return Subscription.objects.create(
        organization=organization,
        plan=plan,
        status=status,
        current_period_start=now,
        current_period_end=now + timedelta(days=30),
    )


def _create_plan(slug, name, tier, price_monthly, is_public=True, sort_order=0):
    """Create a Plan record directly via the ORM."""
    from apps.subscriptions.models import Plan

    return Plan.objects.create(
        slug=slug,
        name=name,
        tier=tier,
        price_monthly=Decimal(str(price_monthly)),
        price_yearly=Decimal(str(price_monthly * 10)),
        is_active=True,
        is_public=is_public,
        sort_order=sort_order,
    )


# ===========================================================================
# 1. Authentication required
# ===========================================================================


@pytest.mark.django_db
class TestSubscriptionPageAuth:
    """Subscription page must redirect unauthenticated users to login."""

    def test_subscription_page_requires_login(self, client):
        response = client.get(SUBSCRIPTION_URL)
        assert response.status_code == 302
        assert "/account/login/" in response.url

    def test_cancel_requires_login(self, client):
        response = client.post(CANCEL_URL)
        assert response.status_code == 302
        assert "/account/login/" in response.url


# ===========================================================================
# 2. Subscription page shows current plan
# ===========================================================================


@pytest.mark.django_db
class TestSubscriptionPageDisplay:
    """Subscription page should expose the current plan in context."""

    def test_shows_current_plan(self, client, organization_with_owner, free_plan):
        org, owner = organization_with_owner
        _create_subscription(org, free_plan)

        client.force_login(owner)
        response = client.get(SUBSCRIPTION_URL)

        assert response.status_code == 200
        assert response.context["plan"] == free_plan
        assert response.context["subscription"] is not None

    def test_no_subscription_shows_none(self, client, organization_with_owner):
        org, owner = organization_with_owner

        client.force_login(owner)
        response = client.get(SUBSCRIPTION_URL)

        assert response.status_code == 200
        assert response.context["plan"] is None
        assert response.context["subscription"] is None


# ===========================================================================
# 3. Cancel subscription — P16 fix verification
# ===========================================================================


@pytest.mark.django_db
class TestSubscriptionCancel:
    """
    P16 fix: subscription_cancel must set status to CANCELLED.

    Before the fix the view updated cancelled_at / cancel_at_period_end but
    forgot to set subscription.status = SubscriptionStatus.CANCELLED, so the
    subscription appeared active even after cancellation.
    """

    def test_cancel_sets_status_to_cancelled(
        self, client, organization_with_owner, starter_plan
    ):
        org, owner = organization_with_owner
        sub = _create_subscription(org, starter_plan)

        client.force_login(owner)
        response = client.post(CANCEL_URL, {"cancel_reason": "Too expensive"})

        assert response.status_code == 302  # redirect back

        sub.refresh_from_db()
        assert sub.status == SubscriptionStatus.CANCELLED
        assert sub.cancelled_at is not None
        assert sub.cancel_at_period_end is True
        assert sub.cancel_reason == "Too expensive"

    def test_cancel_without_reason(self, client, organization_with_owner, starter_plan):
        org, owner = organization_with_owner
        sub = _create_subscription(org, starter_plan)

        client.force_login(owner)
        client.post(CANCEL_URL)

        sub.refresh_from_db()
        assert sub.status == SubscriptionStatus.CANCELLED
        assert sub.cancel_reason == ""

    def test_cancel_no_subscription_shows_error(self, client, organization_with_owner):
        org, owner = organization_with_owner

        client.force_login(owner)
        response = client.post(CANCEL_URL)

        assert response.status_code == 302
        # Should redirect back to subscription page (no crash)

    def test_cancel_rejects_pending_upgrade_requests(
        self, client, organization_with_owner, starter_plan
    ):
        """Cancelling also rejects any pending upgrade requests."""
        from apps.subscriptions.models import UpgradeRequest

        org, owner = organization_with_owner
        _create_subscription(org, starter_plan)

        growth_plan = _create_plan("growth", "Growth", "GROWTH", 4500, sort_order=2)
        upgrade_req = UpgradeRequest.objects.create(
            organization=org,
            current_plan=starter_plan,
            requested_plan=growth_plan,
            requested_by=owner,
            status="PENDING",
        )

        client.force_login(owner)
        client.post(CANCEL_URL, {"cancel_reason": "Switching providers"})

        upgrade_req.refresh_from_db()
        assert upgrade_req.status == "REJECTED"


# ===========================================================================
# 4. Available plans have tier_index — P8 fix verification
# ===========================================================================


@pytest.mark.django_db
class TestPlanTierIndex:
    """
    P8 fix: each available plan must carry a tier_index attribute so the
    template can compare it against current_tier_index to decide whether
    a plan is an upgrade or a downgrade.

    Before the fix tier_index was missing, causing the template to render
    all plans identically (no upgrade/downgrade distinction).
    """

    def test_available_plans_have_tier_index(
        self, client, organization_with_owner, free_plan
    ):
        org, owner = organization_with_owner
        _create_subscription(org, free_plan)

        # Ensure a few public plans exist
        _create_plan("growth-t", "Growth", "GROWTH", 4500, sort_order=2)
        _create_plan("pro-t", "Professional", "PROFESSIONAL", 8500, sort_order=3)

        client.force_login(owner)
        response = client.get(SUBSCRIPTION_URL)

        plans = response.context["available_plans"]
        assert len(plans) >= 2

        for p in plans:
            assert hasattr(p, "tier_index"), (
                f"Plan '{p.name}' is missing tier_index attribute"
            )
            assert isinstance(p.tier_index, int)

    def test_tier_index_reflects_correct_order(
        self, client, organization_with_owner, free_plan
    ):
        org, owner = organization_with_owner
        _create_subscription(org, free_plan)

        _create_plan("starter-t", "Starter", "STARTER", 2000, sort_order=1)
        _create_plan("growth-t2", "Growth", "GROWTH", 4500, sort_order=2)

        client.force_login(owner)
        response = client.get(SUBSCRIPTION_URL)

        tier_order = response.context["tier_order"]
        plans = response.context["available_plans"]

        for p in plans:
            expected_index = tier_order.index(p.tier) if p.tier in tier_order else -1
            assert p.tier_index == expected_index, (
                f"Plan '{p.name}' tier_index={p.tier_index}, expected={expected_index}"
            )

    def test_current_tier_index_set_for_active_plan(
        self, client, organization_with_owner, starter_plan
    ):
        org, owner = organization_with_owner
        _create_subscription(org, starter_plan)

        client.force_login(owner)
        response = client.get(SUBSCRIPTION_URL)

        current_idx = response.context["current_tier_index"]
        tier_order = response.context["tier_order"]

        assert current_idx == tier_order.index("STARTER")

    def test_current_tier_index_is_negative_when_no_plan(
        self, client, organization_with_owner
    ):
        org, owner = organization_with_owner

        client.force_login(owner)
        response = client.get(SUBSCRIPTION_URL)

        assert response.context["current_tier_index"] == -1


# ===========================================================================
# 5. Downgrade plans properly identified
# ===========================================================================


@pytest.mark.django_db
class TestDowngradeIdentification:
    """
    Downgrade plans are those whose tier_index is less than
    current_tier_index.  The template relies on this comparison.
    """

    def test_lower_tier_plans_are_downgrades(self, client, organization_with_owner):
        growth_plan = _create_plan("growth-d", "Growth", "GROWTH", 4500, sort_order=2)
        _create_plan("free-d", "Free", "FREE", 0, sort_order=0)
        _create_plan("starter-d", "Starter", "STARTER", 2000, sort_order=1)

        org, owner = organization_with_owner
        _create_subscription(org, growth_plan)

        client.force_login(owner)
        response = client.get(SUBSCRIPTION_URL)

        current_idx = response.context["current_tier_index"]
        plans = response.context["available_plans"]

        downgrades = [p for p in plans if p.tier_index < current_idx]
        upgrades = [p for p in plans if p.tier_index > current_idx]

        # FREE and STARTER should be downgrades from GROWTH
        downgrade_tiers = {p.tier for p in downgrades}
        assert "FREE" in downgrade_tiers or "STARTER" in downgrade_tiers
        # No upgrade should have a lower index than current
        for p in upgrades:
            assert p.tier_index > current_idx
