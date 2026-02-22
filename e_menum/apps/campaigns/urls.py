"""
URL configuration for the Campaigns application.

Uses DRF router for automatic URL generation from ViewSets.
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.campaigns.views import (
    CampaignViewSet,
    CouponUsageViewSet,
    CouponViewSet,
    ReferralViewSet,
)

router = DefaultRouter()
router.register(r'campaigns', CampaignViewSet, basename='campaign')
router.register(r'coupons', CouponViewSet, basename='coupon')
router.register(r'coupon-usages', CouponUsageViewSet, basename='coupon-usage')
router.register(r'referrals', ReferralViewSet, basename='referral')

app_name = 'campaigns'

urlpatterns = [
    path('', include(router.urls)),
]
