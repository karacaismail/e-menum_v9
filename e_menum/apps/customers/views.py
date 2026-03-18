"""
Views for the Customers application.

This module provides ViewSets for customer-related operations:
- CustomerViewSet: CRUD for customers
- FeedbackViewSet: Manage customer feedback

API Endpoints:
    /api/v1/customers/                         - Customer CRUD
    /api/v1/customers/{id}/loyalty-history/    - Loyalty point history
    /api/v1/customers/feedback/                - Feedback CRUD
    /api/v1/customers/feedback/{id}/respond/   - Staff respond to feedback

Critical Rules:
    - EVERY query MUST include organization filtering (via BaseTenantViewSet)
    - Use soft_delete() - never call delete() directly
"""

import logging

from django.utils.translation import gettext_lazy as _
from rest_framework.decorators import action

from apps.customers.models import Customer, Feedback, LoyaltyPoint
from apps.customers.serializers import (
    CustomerListSerializer,
    CustomerDetailSerializer,
    CustomerCreateSerializer,
    CustomerUpdateSerializer,
    FeedbackListSerializer,
    FeedbackDetailSerializer,
    FeedbackCreateSerializer,
    FeedbackRespondSerializer,
)
from shared.views.base import BaseTenantViewSet


logger = logging.getLogger(__name__)


class CustomerViewSet(BaseTenantViewSet):
    """
    ViewSet for customer management.

    API Endpoints:
        GET    /api/v1/customers/                       - List all customers
        POST   /api/v1/customers/                       - Create a customer
        GET    /api/v1/customers/{id}/                  - Get customer details
        PUT    /api/v1/customers/{id}/                  - Update customer
        PATCH  /api/v1/customers/{id}/                  - Partial update
        DELETE /api/v1/customers/{id}/                  - Soft delete
        GET    /api/v1/customers/{id}/loyalty-history/  - Loyalty point history

    Query Parameters:
        - search: Search by name, email, or phone
        - source: Filter by acquisition source
        - has_orders: Filter customers with orders (true/false)
        - marketing_consent: Filter by marketing consent (true/false)

    Permissions:
        - Requires authentication and organization membership
    """

    queryset = Customer.objects.all()
    permission_resource = "customer"

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == "list":
            return CustomerListSerializer
        elif self.action == "create":
            return CustomerCreateSerializer
        elif self.action in ["update", "partial_update"]:
            return CustomerUpdateSerializer
        return CustomerDetailSerializer

    def get_queryset(self):
        """Return customers with optional filtering."""
        queryset = super().get_queryset().select_related("organization")

        # Prefetch related sets for detail views (avoids N+1)
        if self.action in ("retrieve", "loyalty_history"):
            queryset = queryset.prefetch_related(
                "visits", "feedbacks", "loyalty_transactions", "preferences"
            )

        # Search
        search = self.request.query_params.get("search")
        if search:
            from django.db.models import Q

            queryset = queryset.filter(
                Q(name__icontains=search)
                | Q(email__icontains=search)
                | Q(phone__icontains=search)
            )

        # Source filter
        source = self.request.query_params.get("source")
        if source:
            queryset = queryset.filter(source=source.upper())

        # Has orders filter
        has_orders = self.request.query_params.get("has_orders")
        if has_orders is not None:
            if has_orders.lower() == "true":
                queryset = queryset.filter(total_orders__gt=0)
            else:
                queryset = queryset.filter(total_orders=0)

        # Marketing consent filter
        marketing_consent = self.request.query_params.get("marketing_consent")
        if marketing_consent is not None:
            queryset = queryset.filter(
                marketing_consent=marketing_consent.lower() == "true"
            )

        return queryset.order_by("-last_visit_at", "-created_at")

    @action(detail=True, methods=["get"], url_path="loyalty-history")
    def loyalty_history(self, request, pk=None):
        """
        Get loyalty point transaction history for a customer.

        GET /api/v1/customers/{id}/loyalty-history/
            Response (200):
                {
                    "success": true,
                    "data": {
                        "balance": 500,
                        "transactions": [...]
                    }
                }
        """
        customer = self.get_object()

        transactions = (
            LoyaltyPoint.objects.filter(customer=customer)
            .order_by("-created_at")
            .values(
                "id",
                "transaction_type",
                "points",
                "balance_after",
                "description",
                "expires_at",
                "created_at",
            )
        )

        return self.get_success_response(
            {
                "balance": customer.loyalty_points_balance,
                "transactions": list(transactions),
            }
        )


class FeedbackViewSet(BaseTenantViewSet):
    """
    ViewSet for customer feedback management.

    API Endpoints:
        GET    /api/v1/customers/feedback/              - List all feedback
        POST   /api/v1/customers/feedback/              - Create feedback
        GET    /api/v1/customers/feedback/{id}/         - Get feedback detail
        DELETE /api/v1/customers/feedback/{id}/         - Soft delete feedback
        POST   /api/v1/customers/feedback/{id}/respond/ - Staff respond
        POST   /api/v1/customers/feedback/{id}/publish/ - Make public
        POST   /api/v1/customers/feedback/{id}/archive/ - Archive

    Query Parameters:
        - status: Filter by status
        - feedback_type: Filter by type
        - rating: Filter by exact rating
        - min_rating / max_rating: Filter by rating range
        - is_public: Filter public feedback

    Permissions:
        - Requires authentication and organization membership
    """

    queryset = Feedback.objects.all()
    permission_resource = "feedback"

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == "list":
            return FeedbackListSerializer
        elif self.action == "create":
            return FeedbackCreateSerializer
        return FeedbackDetailSerializer

    def get_queryset(self):
        """Return feedback with optional filtering."""
        queryset = super().get_queryset()
        queryset = queryset.select_related("customer", "organization")

        # Status filter
        status_filter = self.request.query_params.get("status")
        if status_filter:
            queryset = queryset.filter(status=status_filter.upper())

        # Type filter
        feedback_type = self.request.query_params.get("feedback_type")
        if feedback_type:
            queryset = queryset.filter(feedback_type=feedback_type.upper())

        # Exact rating filter
        rating = self.request.query_params.get("rating")
        if rating:
            try:
                queryset = queryset.filter(rating=int(rating))
            except (ValueError, TypeError):
                pass

        # Rating range filters
        min_rating = self.request.query_params.get("min_rating")
        if min_rating:
            try:
                queryset = queryset.filter(rating__gte=int(min_rating))
            except (ValueError, TypeError):
                pass

        max_rating = self.request.query_params.get("max_rating")
        if max_rating:
            try:
                queryset = queryset.filter(rating__lte=int(max_rating))
            except (ValueError, TypeError):
                pass

        # Public filter
        is_public = self.request.query_params.get("is_public")
        if is_public is not None:
            queryset = queryset.filter(is_public=is_public.lower() == "true")

        return queryset.order_by("-created_at")

    @action(detail=True, methods=["post"])
    def respond(self, request, pk=None):
        """
        Add a staff response to feedback.

        POST /api/v1/customers/feedback/{id}/respond/
            {
                "response": "Thank you for your feedback! ..."
            }
        """
        feedback = self.get_object()
        serializer = FeedbackRespondSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        feedback.respond(
            response=serializer.validated_data["response"], user_id=str(request.user.id)
        )

        logger.info("Feedback %s responded to by user %s", feedback.id, request.user.id)

        return self.get_success_response(
            {
                "message": str(_("Response added successfully")),
                "responded_at": feedback.responded_at.isoformat()
                if feedback.responded_at
                else None,
            }
        )

    @action(detail=True, methods=["post"])
    def publish(self, request, pk=None):
        """
        Make feedback publicly visible.

        POST /api/v1/customers/feedback/{id}/publish/
        """
        feedback = self.get_object()
        feedback.make_public()
        return self.get_success_response(
            {
                "message": str(_("Feedback is now public")),
            }
        )

    @action(detail=True, methods=["post"])
    def archive(self, request, pk=None):
        """
        Archive a feedback entry.

        POST /api/v1/customers/feedback/{id}/archive/
        """
        feedback = self.get_object()
        feedback.archive()
        return self.get_success_response(
            {
                "message": str(_("Feedback archived")),
            }
        )


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    "CustomerViewSet",
    "FeedbackViewSet",
]
