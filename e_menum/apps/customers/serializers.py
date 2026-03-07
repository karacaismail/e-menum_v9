"""
Serializers for the Customers application.

Provides serializers for:
- Customer: Customer profile CRUD
- Feedback: Customer feedback with ratings

API Endpoints:
    /api/v1/customers/          - Customer CRUD
    /api/v1/customers/feedback/ - Feedback management
"""

from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from apps.customers.models import Customer, Feedback


# =============================================================================
# CUSTOMER SERIALIZERS
# =============================================================================


class CustomerListSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for listing customers.
    """

    display_name = serializers.SerializerMethodField()
    is_returning_customer = serializers.SerializerMethodField()
    average_order_value = serializers.SerializerMethodField()

    class Meta:
        model = Customer
        fields = [
            "id",
            "name",
            "display_name",
            "email",
            "phone",
            "avatar",
            "source",
            "total_orders",
            "total_spent",
            "loyalty_points_balance",
            "is_returning_customer",
            "average_order_value",
            "marketing_consent",
            "last_visit_at",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "display_name",
            "is_returning_customer",
            "average_order_value",
            "total_orders",
            "total_spent",
            "loyalty_points_balance",
            "last_visit_at",
            "created_at",
        ]

    def get_display_name(self, obj) -> str:
        return obj.display_name

    def get_is_returning_customer(self, obj) -> bool:
        return obj.is_returning_customer

    def get_average_order_value(self, obj):
        return str(obj.average_order_value)


class CustomerDetailSerializer(serializers.ModelSerializer):
    """
    Detailed serializer for a single customer.
    """

    display_name = serializers.SerializerMethodField()
    is_returning_customer = serializers.SerializerMethodField()
    average_order_value = serializers.SerializerMethodField()

    class Meta:
        model = Customer
        fields = [
            "id",
            "name",
            "display_name",
            "email",
            "phone",
            "avatar",
            "language_preference",
            "source",
            "notes",
            "settings",
            "total_orders",
            "total_spent",
            "loyalty_points_balance",
            "is_returning_customer",
            "average_order_value",
            "marketing_consent",
            "marketing_consent_at",
            "first_visit_at",
            "last_visit_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "display_name",
            "is_returning_customer",
            "average_order_value",
            "total_orders",
            "total_spent",
            "loyalty_points_balance",
            "marketing_consent_at",
            "first_visit_at",
            "last_visit_at",
            "created_at",
            "updated_at",
        ]

    def get_display_name(self, obj) -> str:
        return obj.display_name

    def get_is_returning_customer(self, obj) -> bool:
        return obj.is_returning_customer

    def get_average_order_value(self, obj):
        return str(obj.average_order_value)


class CustomerCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating a new customer.
    """

    class Meta:
        model = Customer
        fields = [
            "name",
            "email",
            "phone",
            "avatar",
            "language_preference",
            "source",
            "notes",
            "settings",
            "marketing_consent",
        ]

    def validate_email(self, value):
        """Validate email uniqueness within organization."""
        request = self.context.get("request")
        if value and request:
            organization = getattr(request, "organization", None)
            if organization:
                if Customer.objects.filter(
                    organization=organization, email=value, deleted_at__isnull=True
                ).exists():
                    raise serializers.ValidationError(
                        _("A customer with this email already exists.")
                    )
        return value


class CustomerUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating customer information.
    """

    class Meta:
        model = Customer
        fields = [
            "name",
            "phone",
            "avatar",
            "language_preference",
            "notes",
            "settings",
            "marketing_consent",
        ]


# =============================================================================
# FEEDBACK SERIALIZERS
# =============================================================================


class FeedbackListSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for listing customer feedback.
    """

    customer_name = serializers.SerializerMethodField()
    is_positive = serializers.SerializerMethodField()

    class Meta:
        model = Feedback
        fields = [
            "id",
            "customer",
            "customer_name",
            "feedback_type",
            "rating",
            "comment",
            "status",
            "is_public",
            "is_positive",
            "has_response",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "customer_name",
            "is_positive",
            "has_response",
            "created_at",
        ]

    def get_customer_name(self, obj) -> str:
        if obj.customer:
            return obj.customer.display_name
        return _("Anonymous")

    def get_is_positive(self, obj) -> bool:
        return obj.is_positive


class FeedbackDetailSerializer(serializers.ModelSerializer):
    """
    Detailed serializer for a single feedback record.
    """

    customer_name = serializers.SerializerMethodField()
    is_positive = serializers.SerializerMethodField()
    is_negative = serializers.SerializerMethodField()
    has_response = serializers.SerializerMethodField()

    class Meta:
        model = Feedback
        fields = [
            "id",
            "customer",
            "customer_name",
            "order_id",
            "feedback_type",
            "rating",
            "comment",
            "status",
            "staff_response",
            "responded_at",
            "is_public",
            "is_positive",
            "is_negative",
            "has_response",
            "metadata",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "customer_name",
            "is_positive",
            "is_negative",
            "has_response",
            "responded_at",
            "created_at",
            "updated_at",
        ]

    def get_customer_name(self, obj) -> str:
        if obj.customer:
            return obj.customer.display_name
        return str(_("Anonymous"))

    def get_is_positive(self, obj) -> bool:
        return obj.is_positive

    def get_is_negative(self, obj) -> bool:
        return obj.is_negative

    def get_has_response(self, obj) -> bool:
        return obj.has_response


class FeedbackCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating a new feedback entry.
    Rating must be between 1 and 5.
    """

    class Meta:
        model = Feedback
        fields = [
            "customer",
            "order_id",
            "feedback_type",
            "rating",
            "comment",
            "is_public",
            "metadata",
        ]

    def validate_rating(self, value):
        if not (1 <= value <= 5):
            raise serializers.ValidationError(_("Rating must be between 1 and 5."))
        return value


class FeedbackRespondSerializer(serializers.Serializer):
    """
    Serializer for staff responding to feedback.
    """

    response = serializers.CharField(
        min_length=1, max_length=2000, help_text=_("Staff response to the feedback")
    )


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    "CustomerListSerializer",
    "CustomerDetailSerializer",
    "CustomerCreateSerializer",
    "CustomerUpdateSerializer",
    "FeedbackListSerializer",
    "FeedbackDetailSerializer",
    "FeedbackCreateSerializer",
    "FeedbackRespondSerializer",
]
