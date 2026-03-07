"""
DRF ViewSets for the Campaigns application.

Provides ViewSets for all campaign models using BaseTenantViewSet
for automatic organization filtering, soft delete, and standard
response format.
"""

from shared.views.base import BaseTenantViewSet, BaseTenantReadOnlyViewSet

from apps.campaigns.models import (
    Campaign,
    Coupon,
    CouponUsage,
    Referral,
)
from apps.campaigns.serializers import (
    CampaignSerializer,
    CouponSerializer,
    CouponUsageSerializer,
    ReferralSerializer,
)


class CampaignViewSet(BaseTenantViewSet):
    """ViewSet for Campaign CRUD operations."""

    queryset = Campaign.objects.select_related("created_by").all()
    serializer_class = CampaignSerializer
    permission_resource = "campaign"

    def perform_create(self, serializer):
        """Auto-set created_by from request user."""
        organization = self.require_organization()
        serializer.save(
            organization=organization,
            created_by=self.request.user,
        )


class CouponViewSet(BaseTenantViewSet):
    """ViewSet for Coupon CRUD operations."""

    queryset = Coupon.objects.select_related("campaign").all()
    serializer_class = CouponSerializer
    permission_resource = "campaign"


class CouponUsageViewSet(BaseTenantReadOnlyViewSet):
    """Read-only ViewSet for CouponUsage records (audit trail)."""

    queryset = CouponUsage.objects.select_related(
        "coupon",
        "order",
        "customer",
    ).all()
    serializer_class = CouponUsageSerializer
    permission_resource = "campaign"


class ReferralViewSet(BaseTenantViewSet):
    """ViewSet for Referral CRUD operations."""

    queryset = Referral.objects.select_related("referrer", "referred").all()
    serializer_class = ReferralSerializer
    permission_resource = "campaign"
