"""
Views for the Subscriptions application.

This module provides ViewSets for subscription-related models:
- FeatureViewSet: Platform-level feature definitions (admin only)
- PlanViewSet: Subscription plan management (public read, admin write)
- SubscriptionViewSet: Organization subscription management (tenant-scoped)
- InvoiceViewSet: Billing records management (tenant-scoped)
- PlanFeatureViewSet: Plan-Feature linking (admin only)
- OrganizationUsageViewSet: Resource usage tracking (tenant-scoped, read-only)

API Endpoints:
    /api/v1/features/           - Feature CRUD (admin)
    /api/v1/plans/              - Plan CRUD (public read)
    /api/v1/subscriptions/      - Subscription CRUD (tenant)
    /api/v1/invoices/           - Invoice CRUD (tenant)
    /api/v1/plan-features/      - PlanFeature CRUD (admin)
    /api/v1/usage/              - Usage tracking (tenant, read-only)

Multi-Tenancy:
    - Feature, Plan, PlanFeature: Platform-level (no organization filter)
    - Subscription, Invoice, OrganizationUsage: Tenant-scoped with auto-filter

Critical Rules:
    - EVERY query on tenant-scoped data MUST include organization filtering
    - Use soft_delete() - never call delete() directly
    - All responses follow E-Menum standard format
"""

import logging

from django.db import models
from django.db.models import Prefetch
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers as drf_serializers
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAdminUser

from apps.subscriptions.models import (
    Feature,
    Plan,
    Subscription,
    Invoice,
    PlanFeature,
    OrganizationUsage,
)
from apps.subscriptions.choices import (
    SubscriptionStatus,
    InvoiceStatus,
)
from apps.subscriptions.serializers import (
    # Feature
    FeatureListSerializer,
    FeatureDetailSerializer,
    FeatureCreateSerializer,
    FeatureUpdateSerializer,
    # Plan
    PlanListSerializer,
    PlanDetailSerializer,
    PlanCreateSerializer,
    PlanUpdateSerializer,
    # Subscription
    SubscriptionListSerializer,
    SubscriptionDetailSerializer,
    SubscriptionCreateSerializer,
    SubscriptionUpdateSerializer,
    SubscriptionCancelSerializer,
    SubscriptionChangePlanSerializer,
    # Invoice
    InvoiceListSerializer,
    InvoiceDetailSerializer,
    InvoiceCreateSerializer,
    InvoiceUpdateSerializer,
    InvoicePaymentSerializer,
    InvoiceRefundSerializer,
    # PlanFeature
    PlanFeatureListSerializer,
    PlanFeatureDetailSerializer,
    PlanFeatureCreateSerializer,
    PlanFeatureUpdateSerializer,
    # OrganizationUsage
    OrganizationUsageListSerializer,
    OrganizationUsageDetailSerializer,
)
from shared.views.base import (
    BaseModelViewSet,
    BaseTenantViewSet,
    BaseTenantReadOnlyViewSet,
)


logger = logging.getLogger(__name__)


# =============================================================================
# FEATURE VIEWSET (Platform-level, admin only)
# =============================================================================


class FeatureViewSet(BaseModelViewSet):
    """
    ViewSet for feature management.

    Features define capabilities that can be enabled per plan.
    This is a platform-level resource managed by administrators.

    API Endpoints:
        GET    /api/v1/features/              - List all features
        POST   /api/v1/features/              - Create a new feature (admin)
        GET    /api/v1/features/{id}/         - Get feature details
        PUT    /api/v1/features/{id}/         - Update feature (admin)
        PATCH  /api/v1/features/{id}/         - Partial update feature (admin)
        DELETE /api/v1/features/{id}/         - Soft delete feature (admin)

    Query Parameters:
        - category: Filter by category
        - feature_type: Filter by type (BOOLEAN, LIMIT, USAGE)
        - is_active: Filter by active status
        - search: Search by name or code

    Permissions:
        - GET: AllowAny (public API for feature discovery)
        - POST/PUT/PATCH/DELETE: IsAdminUser
    """

    queryset = Feature.objects.all()

    def get_permissions(self):
        """Return permissions based on action."""
        if self.action in ["list", "retrieve"]:
            return [AllowAny()]
        return [IsAdminUser()]

    def get_serializer_class(self):
        """Return the appropriate serializer based on action."""
        if self.action == "list":
            return FeatureListSerializer
        elif self.action == "create":
            return FeatureCreateSerializer
        elif self.action in ["update", "partial_update"]:
            return FeatureUpdateSerializer
        return FeatureDetailSerializer

    def get_queryset(self):
        """
        Return features with optional filters.
        """
        queryset = super().get_queryset()

        # Filter by category
        category = self.request.query_params.get("category")
        if category:
            queryset = queryset.filter(category=category)

        # Filter by feature_type
        feature_type = self.request.query_params.get("feature_type")
        if feature_type:
            queryset = queryset.filter(feature_type=feature_type.upper())

        # Filter by active status
        is_active = self.request.query_params.get("is_active")
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == "true")

        # Search by name or code
        search = self.request.query_params.get("search")
        if search:
            queryset = queryset.filter(
                models.Q(name__icontains=search) | models.Q(code__icontains=search)
            )

        return queryset.order_by("category", "sort_order", "name")


# =============================================================================
# PLAN VIEWSET (Platform-level, public read)
# =============================================================================


class PlanViewSet(BaseModelViewSet):
    """
    ViewSet for plan management.

    Plans define subscription tiers with pricing and features.
    This is a platform-level resource with public read access.

    API Endpoints:
        GET    /api/v1/plans/                  - List all plans (public)
        POST   /api/v1/plans/                  - Create a new plan (admin)
        GET    /api/v1/plans/{id}/             - Get plan details (public)
        PUT    /api/v1/plans/{id}/             - Update plan (admin)
        PATCH  /api/v1/plans/{id}/             - Partial update plan (admin)
        DELETE /api/v1/plans/{id}/             - Soft delete plan (admin)
        POST   /api/v1/plans/{id}/set-default/ - Set as default plan (admin)
        GET    /api/v1/plans/{id}/compare/     - Compare with another plan

    Query Parameters:
        - tier: Filter by tier (FREE, STARTER, GROWTH, etc.)
        - is_active: Filter by active status
        - is_public: Filter by public visibility
        - search: Search by name

    Permissions:
        - GET: AllowAny (public pricing page)
        - POST/PUT/PATCH/DELETE: IsAdminUser
    """

    queryset = Plan.objects.all()

    def get_permissions(self):
        """Return permissions based on action."""
        if self.action in ["list", "retrieve", "compare"]:
            return [AllowAny()]
        return [IsAdminUser()]

    def get_serializer_class(self):
        """Return the appropriate serializer based on action."""
        if self.action == "list":
            return PlanListSerializer
        elif self.action == "create":
            return PlanCreateSerializer
        elif self.action in ["update", "partial_update"]:
            return PlanUpdateSerializer
        return PlanDetailSerializer

    def get_queryset(self):
        """
        Return plans with optional filters.
        """
        queryset = super().get_queryset()

        # For detail view, prefetch plan features
        if self.action == "retrieve":
            queryset = queryset.prefetch_related(
                Prefetch(
                    "plan_features",
                    queryset=PlanFeature.objects.filter(is_enabled=True)
                    .select_related("feature")
                    .order_by("sort_order", "feature__name"),
                )
            )

        # Filter by tier
        tier = self.request.query_params.get("tier")
        if tier:
            queryset = queryset.filter(tier=tier.upper())

        # Filter by active status
        is_active = self.request.query_params.get("is_active")
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == "true")

        # Filter by public visibility
        is_public = self.request.query_params.get("is_public")
        if is_public is not None:
            queryset = queryset.filter(is_public=is_public.lower() == "true")

        # Search by name
        search = self.request.query_params.get("search")
        if search:
            queryset = queryset.filter(name__icontains=search)

        return queryset.order_by("sort_order", "price_monthly")

    @action(detail=True, methods=["post"], url_path="set-default")
    def set_default(self, request, pk=None):
        """
        Set this plan as the default for new organizations.

        POST /api/v1/plans/{id}/set-default/
            Response (200):
                {
                    "success": true,
                    "data": {
                        "message": "Plan set as default"
                    }
                }
        """
        plan = self.get_object()
        plan.set_as_default()

        return self.get_success_response({"message": str(_("Plan set as default"))})

    @action(detail=True, methods=["get"])
    def compare(self, request, pk=None):
        """
        Compare this plan with another plan.

        GET /api/v1/plans/{id}/compare/?with={other_plan_id}
            Response (200):
                {
                    "success": true,
                    "data": {
                        "plan": {...},
                        "compared_to": {...},
                        "comparison": {
                            "limits": {...},
                            "features": {...}
                        }
                    }
                }
        """
        plan = self.get_object()

        # Get the plan to compare with
        other_plan_id = request.query_params.get("with")
        if not other_plan_id:
            return self.get_error_response(
                code="MISSING_PARAMETER",
                message=str(_('The "with" parameter is required')),
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        try:
            other_plan = Plan.objects.get(id=other_plan_id, deleted_at__isnull=True)
        except Plan.DoesNotExist:
            return self.get_error_response(
                code="PLAN_NOT_FOUND",
                message=str(_("Comparison plan not found")),
                status_code=status.HTTP_404_NOT_FOUND,
            )

        comparison = plan.compare_to(other_plan)

        return self.get_success_response(
            {
                "plan": PlanDetailSerializer(plan).data,
                "compared_to": PlanDetailSerializer(other_plan).data,
                "comparison": comparison,
            }
        )


# =============================================================================
# SUBSCRIPTION VIEWSET (Tenant-scoped)
# =============================================================================


class SubscriptionViewSet(BaseTenantViewSet):
    """
    ViewSet for subscription management.

    Subscriptions link organizations to plans with billing lifecycle.
    Each organization can have one active subscription at a time.

    API Endpoints:
        GET    /api/v1/subscriptions/              - List organization subscriptions
        POST   /api/v1/subscriptions/              - Create a new subscription
        GET    /api/v1/subscriptions/{id}/         - Get subscription details
        PUT    /api/v1/subscriptions/{id}/         - Update subscription
        PATCH  /api/v1/subscriptions/{id}/         - Partial update subscription
        DELETE /api/v1/subscriptions/{id}/         - Soft delete subscription
        POST   /api/v1/subscriptions/{id}/cancel/  - Cancel subscription
        POST   /api/v1/subscriptions/{id}/reactivate/ - Reactivate subscription
        POST   /api/v1/subscriptions/{id}/change-plan/ - Change subscription plan
        GET    /api/v1/subscriptions/current/      - Get current active subscription

    Query Parameters:
        - status: Filter by status (ACTIVE, TRIALING, etc.)

    Permissions:
        - Requires authentication
        - Requires organization membership
    """

    queryset = Subscription.objects.all()
    permission_resource = "subscription"

    def get_serializer_class(self):
        """Return the appropriate serializer based on action."""
        if self.action == "list":
            return SubscriptionListSerializer
        elif self.action == "create":
            return SubscriptionCreateSerializer
        elif self.action in ["update", "partial_update"]:
            return SubscriptionUpdateSerializer
        elif self.action == "cancel":
            return SubscriptionCancelSerializer
        elif self.action == "change_plan":
            return SubscriptionChangePlanSerializer
        return SubscriptionDetailSerializer

    def get_queryset(self):
        """
        Return subscriptions filtered by organization.
        """
        queryset = super().get_queryset()

        # Optimize with select_related
        queryset = queryset.select_related("plan")

        # Filter by status
        status_filter = self.request.query_params.get("status")
        if status_filter:
            queryset = queryset.filter(status=status_filter.upper())

        return queryset.order_by("-created_at")

    @action(detail=False, methods=["get"])
    def current(self, request):
        """
        Get the current active subscription for the organization.

        GET /api/v1/subscriptions/current/
            Response (200):
                {
                    "success": true,
                    "data": {...}
                }
        """
        organization = self.get_organization()
        if not organization:
            return self.get_error_response(
                code="NO_ORGANIZATION",
                message=str(_("Organization context required")),
                status_code=status.HTTP_403_FORBIDDEN,
            )

        subscription = (
            Subscription.objects.filter(
                organization=organization,
                status__in=[SubscriptionStatus.ACTIVE, SubscriptionStatus.TRIALING],
                deleted_at__isnull=True,
            )
            .select_related("plan")
            .first()
        )

        if not subscription:
            return self.get_success_response(None)

        serializer = SubscriptionDetailSerializer(subscription)
        return self.get_success_response(serializer.data)

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        """
        Cancel the subscription.

        POST /api/v1/subscriptions/{id}/cancel/
            Request body:
                {
                    "reason": "Too expensive",
                    "at_period_end": true
                }
            Response (200):
                {
                    "success": true,
                    "data": {
                        "message": "Subscription cancelled",
                        "cancelled_at": "2024-01-15T12:00:00Z"
                    }
                }
        """
        subscription = self.get_object()

        serializer = SubscriptionCancelSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        subscription.cancel(
            reason=serializer.validated_data.get("reason"),
            at_period_end=serializer.validated_data.get("at_period_end", True),
        )

        return self.get_success_response(
            {
                "message": str(_("Subscription cancelled")),
                "cancelled_at": subscription.cancelled_at.isoformat()
                if subscription.cancelled_at
                else None,
                "cancel_at_period_end": subscription.cancel_at_period_end,
            }
        )

    @action(detail=True, methods=["post"])
    def reactivate(self, request, pk=None):
        """
        Reactivate a cancelled or suspended subscription.

        POST /api/v1/subscriptions/{id}/reactivate/
            Response (200):
                {
                    "success": true,
                    "data": {
                        "message": "Subscription reactivated"
                    }
                }
        """
        subscription = self.get_object()

        if subscription.status not in [
            SubscriptionStatus.CANCELLED,
            SubscriptionStatus.SUSPENDED,
        ]:
            return self.get_error_response(
                code="INVALID_STATUS",
                message=str(
                    _("Only cancelled or suspended subscriptions can be reactivated")
                ),
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        subscription.reactivate()

        return self.get_success_response(
            {
                "message": str(_("Subscription reactivated")),
                "status": subscription.status,
            }
        )

    @action(detail=True, methods=["post"], url_path="change-plan")
    def change_plan(self, request, pk=None):
        """
        Change the subscription to a different plan.

        POST /api/v1/subscriptions/{id}/change-plan/
            Request body:
                {
                    "plan_id": "uuid",
                    "prorate": true
                }
            Response (200):
                {
                    "success": true,
                    "data": {
                        "message": "Plan changed",
                        "new_plan": {...}
                    }
                }
        """
        subscription = self.get_object()

        serializer = SubscriptionChangePlanSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        new_plan = serializer.validated_data["plan_id"]
        prorate = serializer.validated_data.get("prorate", True)

        subscription.change_plan(new_plan, prorate=prorate)

        return self.get_success_response(
            {
                "message": str(_("Plan changed successfully")),
                "new_plan": {
                    "id": str(new_plan.id),
                    "name": new_plan.name,
                    "tier": new_plan.tier,
                },
                "current_price": str(subscription.current_price),
            }
        )


# =============================================================================
# INVOICE VIEWSET (Tenant-scoped)
# =============================================================================


class InvoiceViewSet(BaseTenantViewSet):
    """
    ViewSet for invoice management.

    Invoices track billing transactions for subscriptions.

    API Endpoints:
        GET    /api/v1/invoices/               - List organization invoices
        POST   /api/v1/invoices/               - Create a new invoice
        GET    /api/v1/invoices/{id}/          - Get invoice details
        PUT    /api/v1/invoices/{id}/          - Update invoice
        PATCH  /api/v1/invoices/{id}/          - Partial update invoice
        DELETE /api/v1/invoices/{id}/          - Soft delete invoice
        POST   /api/v1/invoices/{id}/finalize/ - Finalize draft invoice
        POST   /api/v1/invoices/{id}/mark-paid/ - Mark invoice as paid
        POST   /api/v1/invoices/{id}/void/     - Void invoice
        POST   /api/v1/invoices/{id}/refund/   - Refund invoice

    Query Parameters:
        - status: Filter by status (DRAFT, PENDING, PAID, etc.)
        - subscription_id: Filter by subscription

    Permissions:
        - Requires authentication
        - Requires organization membership
    """

    queryset = Invoice.objects.all()
    permission_resource = "invoice"

    def get_serializer_class(self):
        """Return the appropriate serializer based on action."""
        if self.action == "list":
            return InvoiceListSerializer
        elif self.action == "create":
            return InvoiceCreateSerializer
        elif self.action in ["update", "partial_update"]:
            return InvoiceUpdateSerializer
        elif self.action == "mark_paid":
            return InvoicePaymentSerializer
        elif self.action == "refund":
            return InvoiceRefundSerializer
        return InvoiceDetailSerializer

    def get_queryset(self):
        """
        Return invoices filtered by organization.
        """
        queryset = super().get_queryset()

        # Optimize with select_related
        queryset = queryset.select_related("subscription", "subscription__plan")

        # Filter by status
        status_filter = self.request.query_params.get("status")
        if status_filter:
            queryset = queryset.filter(status=status_filter.upper())

        # Filter by subscription
        subscription_id = self.request.query_params.get("subscription_id")
        if subscription_id:
            queryset = queryset.filter(subscription_id=subscription_id)

        return queryset.order_by("-created_at")

    @action(detail=True, methods=["post"])
    def finalize(self, request, pk=None):
        """
        Finalize a draft invoice and make it pending.

        POST /api/v1/invoices/{id}/finalize/
            Response (200):
                {
                    "success": true,
                    "data": {
                        "message": "Invoice finalized",
                        "status": "PENDING"
                    }
                }
        """
        invoice = self.get_object()

        if invoice.status != InvoiceStatus.DRAFT:
            return self.get_error_response(
                code="INVALID_STATUS",
                message=str(_("Only draft invoices can be finalized")),
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        invoice.finalize()

        return self.get_success_response(
            {
                "message": str(_("Invoice finalized")),
                "status": invoice.status,
            }
        )

    @action(detail=True, methods=["post"], url_path="mark-paid")
    def mark_paid(self, request, pk=None):
        """
        Mark an invoice as paid.

        POST /api/v1/invoices/{id}/mark-paid/
            Request body:
                {
                    "payment_id": "external_payment_123",
                    "payment_details": {"last4": "4242", "brand": "visa"},
                    "amount": 2000.00
                }
            Response (200):
                {
                    "success": true,
                    "data": {
                        "message": "Invoice marked as paid",
                        "paid_at": "2024-01-15T12:00:00Z"
                    }
                }
        """
        invoice = self.get_object()

        if invoice.status not in [InvoiceStatus.PENDING, InvoiceStatus.DRAFT]:
            return self.get_error_response(
                code="INVALID_STATUS",
                message=str(_("Only pending or draft invoices can be marked as paid")),
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        serializer = InvoicePaymentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        invoice.mark_paid(
            payment_id=serializer.validated_data.get("payment_id"),
            payment_details=serializer.validated_data.get("payment_details"),
            amount=serializer.validated_data.get("amount"),
        )

        return self.get_success_response(
            {
                "message": str(_("Invoice marked as paid")),
                "paid_at": invoice.paid_at.isoformat() if invoice.paid_at else None,
                "amount_paid": str(invoice.amount_paid),
            }
        )

    @action(detail=True, methods=["post"])
    def void(self, request, pk=None):
        """
        Void an invoice.

        POST /api/v1/invoices/{id}/void/
            Request body:
                {
                    "reason": "Duplicate invoice"
                }
            Response (200):
                {
                    "success": true,
                    "data": {
                        "message": "Invoice voided"
                    }
                }
        """
        invoice = self.get_object()

        if invoice.status == InvoiceStatus.PAID:
            return self.get_error_response(
                code="INVALID_STATUS",
                message=str(_("Paid invoices cannot be voided. Use refund instead.")),
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        class VoidInvoiceSerializer(drf_serializers.Serializer):
            reason = drf_serializers.CharField(
                required=False, allow_blank=True, allow_null=True, max_length=500
            )

        serializer = VoidInvoiceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        reason = serializer.validated_data.get("reason")
        invoice.void(reason=reason)

        return self.get_success_response(
            {
                "message": str(_("Invoice voided")),
                "status": invoice.status,
            }
        )

    @action(detail=True, methods=["post"])
    def refund(self, request, pk=None):
        """
        Refund a paid invoice.

        POST /api/v1/invoices/{id}/refund/
            Request body:
                {
                    "amount": 1000.00,
                    "reason": "Customer requested refund"
                }
            Response (200):
                {
                    "success": true,
                    "data": {
                        "message": "Invoice refunded",
                        "amount_refunded": 1000.00
                    }
                }
        """
        invoice = self.get_object()

        if invoice.status != InvoiceStatus.PAID:
            return self.get_error_response(
                code="INVALID_STATUS",
                message=str(_("Only paid invoices can be refunded")),
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        serializer = InvoiceRefundSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        invoice.refund(
            amount=serializer.validated_data.get("amount"),
            reason=serializer.validated_data.get("reason"),
        )

        return self.get_success_response(
            {
                "message": str(_("Invoice refunded")),
                "amount_refunded": str(invoice.amount_refunded),
                "status": invoice.status,
            }
        )


# =============================================================================
# PLAN FEATURE VIEWSET (Platform-level, admin only)
# =============================================================================


class PlanFeatureViewSet(BaseModelViewSet):
    """
    ViewSet for plan-feature relationship management.

    Links features to plans with plan-specific configuration.
    This is a platform-level resource managed by administrators.

    API Endpoints:
        GET    /api/v1/plan-features/          - List all plan-feature links
        POST   /api/v1/plan-features/          - Create a new link (admin)
        GET    /api/v1/plan-features/{id}/     - Get link details
        PUT    /api/v1/plan-features/{id}/     - Update link (admin)
        DELETE /api/v1/plan-features/{id}/     - Delete link (admin)

    Query Parameters:
        - plan_id: Filter by plan
        - feature_id: Filter by feature
        - is_enabled: Filter by enabled status

    Permissions:
        - GET: AllowAny (public)
        - POST/PUT/DELETE: IsAdminUser
    """

    queryset = PlanFeature.objects.all()

    def get_permissions(self):
        """Return permissions based on action."""
        if self.action in ["list", "retrieve"]:
            return [AllowAny()]
        return [IsAdminUser()]

    def get_serializer_class(self):
        """Return the appropriate serializer based on action."""
        if self.action == "list":
            return PlanFeatureListSerializer
        elif self.action == "create":
            return PlanFeatureCreateSerializer
        elif self.action in ["update", "partial_update"]:
            return PlanFeatureUpdateSerializer
        return PlanFeatureDetailSerializer

    def get_queryset(self):
        """
        Return plan features with optional filters.
        """
        queryset = super().get_queryset()

        # Optimize with select_related
        queryset = queryset.select_related("plan", "feature")

        # Filter by plan
        plan_id = self.request.query_params.get("plan_id")
        if plan_id:
            queryset = queryset.filter(plan_id=plan_id)

        # Filter by feature
        feature_id = self.request.query_params.get("feature_id")
        if feature_id:
            queryset = queryset.filter(feature_id=feature_id)

        # Filter by enabled status
        is_enabled = self.request.query_params.get("is_enabled")
        if is_enabled is not None:
            queryset = queryset.filter(is_enabled=is_enabled.lower() == "true")

        return queryset.order_by("plan__sort_order", "sort_order", "feature__name")


# =============================================================================
# ORGANIZATION USAGE VIEWSET (Tenant-scoped, read-only for users)
# =============================================================================


class OrganizationUsageViewSet(BaseTenantReadOnlyViewSet):
    """
    ViewSet for organization usage tracking (read-only).

    Tracks resource usage against plan limits for the current organization.
    Users can view their usage but cannot modify it directly.

    API Endpoints:
        GET    /api/v1/usage/                  - List organization usage
        GET    /api/v1/usage/{id}/             - Get usage details
        GET    /api/v1/usage/summary/          - Get usage summary

    Query Parameters:
        - feature_code: Filter by feature code

    Permissions:
        - Requires authentication
        - Requires organization membership
    """

    queryset = OrganizationUsage.objects.all()
    permission_resource = "usage"

    def get_serializer_class(self):
        """Return the appropriate serializer based on action."""
        if self.action == "list":
            return OrganizationUsageListSerializer
        return OrganizationUsageDetailSerializer

    def get_queryset(self):
        """
        Return usage records filtered by organization.
        """
        queryset = super().get_queryset()

        # Optimize with select_related
        queryset = queryset.select_related("feature")

        # Filter by feature code
        feature_code = self.request.query_params.get("feature_code")
        if feature_code:
            queryset = queryset.filter(feature__code=feature_code)

        return queryset.order_by("feature__category", "feature__sort_order")

    @action(detail=False, methods=["get"])
    def summary(self, request):
        """
        Get a summary of usage for the organization.

        GET /api/v1/usage/summary/
            Response (200):
                {
                    "success": true,
                    "data": {
                        "total_features_tracked": 5,
                        "features_at_limit": 1,
                        "features_near_limit": 2,
                        "usage_by_category": {...}
                    }
                }
        """
        organization = self.get_organization()
        if not organization:
            return self.get_error_response(
                code="NO_ORGANIZATION",
                message=str(_("Organization context required")),
                status_code=status.HTTP_403_FORBIDDEN,
            )

        usage_records = OrganizationUsage.objects.filter(
            organization=organization
        ).select_related("feature")

        total_tracked = usage_records.count()
        at_limit = sum(1 for u in usage_records if u.is_limit_exceeded)
        near_limit = sum(
            1
            for u in usage_records
            if not u.is_unlimited
            and not u.is_limit_exceeded
            and u.usage_percentage >= 80
        )

        # Group by category
        usage_by_category = {}
        for usage in usage_records:
            category = usage.feature.category
            if category not in usage_by_category:
                usage_by_category[category] = []
            usage_by_category[category].append(
                {
                    "feature_code": usage.feature.code,
                    "feature_name": usage.feature.name,
                    "current_usage": usage.current_usage,
                    "limit": usage.usage_limit,
                    "percentage": usage.usage_percentage,
                    "is_exceeded": usage.is_limit_exceeded,
                }
            )

        return self.get_success_response(
            {
                "total_features_tracked": total_tracked,
                "features_at_limit": at_limit,
                "features_near_limit": near_limit,
                "usage_by_category": usage_by_category,
            }
        )


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    "FeatureViewSet",
    "PlanViewSet",
    "SubscriptionViewSet",
    "InvoiceViewSet",
    "PlanFeatureViewSet",
    "OrganizationUsageViewSet",
]
