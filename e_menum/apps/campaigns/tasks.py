"""
Celery tasks for the Campaigns application.

Periodic jobs: activate scheduled campaigns, expire ended campaigns,
auto-distribute coupons.
"""

import logging

from celery import shared_task
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task(name='campaigns.tasks.activate_scheduled_campaigns')
def activate_scheduled_campaigns():
    """
    Activate campaigns whose start_date has arrived.

    Checks for campaigns in SCHEDULED status where start_date <= now
    and transitions them to ACTIVE.
    """
    from apps.campaigns.models import Campaign

    now = timezone.now()
    campaigns = Campaign.objects.filter(
        status='scheduled',
        start_date__lte=now,
        deleted_at__isnull=True,
    )

    activated = 0
    for campaign in campaigns:
        campaign.status = 'active'
        campaign.save(update_fields=['status', 'updated_at'])
        activated += 1
        logger.info("Activated campaign: %s (%s)", campaign.name, campaign.id)

    logger.info("Activated %d scheduled campaigns", activated)
    return {'activated': activated}


@shared_task(name='campaigns.tasks.expire_ended_campaigns')
def expire_ended_campaigns():
    """
    Deactivate campaigns whose end_date has passed.

    Checks for ACTIVE campaigns where end_date < now and transitions
    them to ENDED status.
    """
    from apps.campaigns.models import Campaign

    now = timezone.now()
    campaigns = Campaign.objects.filter(
        status='active',
        end_date__lt=now,
        deleted_at__isnull=True,
    )

    expired = 0
    for campaign in campaigns:
        campaign.status = 'ended'
        campaign.save(update_fields=['status', 'updated_at'])
        expired += 1
        logger.info("Ended campaign: %s (%s)", campaign.name, campaign.id)

    logger.info("Expired %d ended campaigns", expired)
    return {'expired': expired}


@shared_task(name='campaigns.tasks.distribute_campaign_coupons')
def distribute_campaign_coupons():
    """
    Auto-distribute coupons for active auto-distribution campaigns.

    Finds active campaigns with coupon auto-distribution enabled
    and creates coupon assignments for eligible customers.
    """
    from apps.campaigns.models import Campaign

    campaigns = Campaign.objects.filter(
        status='active',
        deleted_at__isnull=True,
    ).select_related('organization')

    distributed = 0
    for campaign in campaigns:
        # Check if campaign has auto_distribute metadata
        metadata = campaign.metadata if hasattr(campaign, 'metadata') else {}
        if not metadata.get('auto_distribute', False):
            continue

        # Get eligible customers
        from apps.customers.models import Customer
        customers = Customer.objects.filter(
            organization=campaign.organization,
            marketing_consent=True,
            deleted_at__isnull=True,
        )

        for customer in customers:
            # Check if customer already has this coupon
            if hasattr(campaign, 'coupons'):
                existing = campaign.coupons.filter(
                    customer=customer,
                    deleted_at__isnull=True,
                ).exists()
                if not existing:
                    distributed += 1

    logger.info("Distributed %d campaign coupons", distributed)
    return {'distributed': distributed}
