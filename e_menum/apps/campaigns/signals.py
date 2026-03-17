"""
Signals for the Campaigns application.

Handles cross-app integrations:
- CouponUsage → LoyaltyPoint: Award loyalty points when a coupon is used
  (AUDIT BULGU-18: Campaigns ↔ Customers loyalty integration)

Critical Rules:
    - Signals must be idempotent (safe to run multiple times)
    - Use select_for_update to prevent race conditions on balance
    - All database writes are wrapped in atomic transactions
"""

import logging

from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _

logger = logging.getLogger(__name__)

# Default points awarded per coupon usage (can be overridden via settings)
COUPON_LOYALTY_POINTS = 10


@receiver(post_save, sender="campaigns.CouponUsage")
def award_loyalty_points_on_coupon_usage(sender, instance, created, **kwargs):
    """
    Award loyalty points to a customer when they use a coupon.

    Triggered after a CouponUsage record is created. Only fires on creation
    (not on update) and only if a customer is associated with the usage.

    Points are stored in the LoyaltyPoint ledger and the Customer's cached
    balance is updated atomically.

    Args:
        sender: CouponUsage model class
        instance: The CouponUsage instance that was saved
        created: True if this is a new record
        **kwargs: Additional signal arguments
    """
    if not created:
        return

    if not instance.customer_id:
        logger.debug(
            "CouponUsage %s has no customer — skipping loyalty points", instance.id
        )
        return

    try:
        _create_loyalty_transaction(instance)
    except Exception:
        logger.exception(
            "Failed to award loyalty points for CouponUsage %s", instance.id
        )


def _create_loyalty_transaction(coupon_usage):
    """
    Create a LoyaltyPoint transaction for the given coupon usage.

    Uses select_for_update on the Customer row to prevent concurrent
    balance updates from producing inconsistent balance_after values.
    """
    from apps.customers.choices import LoyaltyPointType
    from apps.customers.models import Customer, LoyaltyPoint

    with transaction.atomic():
        # Lock the customer row to safely read + update balance
        customer = Customer.objects.select_for_update().get(pk=coupon_usage.customer_id)

        points = COUPON_LOYALTY_POINTS
        new_balance = customer.loyalty_points_balance + points

        LoyaltyPoint.objects.create(
            organization_id=coupon_usage.organization_id,
            customer=customer,
            transaction_type=LoyaltyPointType.BONUS,
            points=points,
            balance_after=new_balance,
            description=str(
                _("Bonus points for using coupon: %(code)s")
                % {"code": coupon_usage.coupon.code}
            ),
            metadata={
                "source": "coupon_usage",
                "coupon_usage_id": str(coupon_usage.id),
                "coupon_id": str(coupon_usage.coupon_id),
                "discount_applied": str(coupon_usage.discount_applied),
            },
        )

        # Update cached balance on Customer
        customer.loyalty_points_balance = new_balance
        customer.save(update_fields=["loyalty_points_balance", "updated_at"])

    logger.info(
        "Awarded %d loyalty points to customer %s for CouponUsage %s",
        points,
        customer.id,
        coupon_usage.id,
    )
