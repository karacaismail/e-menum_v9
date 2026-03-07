"""
Serializers for the Subscriptions application.

This module provides DRF serializers for all subscription-related models:
- FeatureSerializer: Platform-level feature definitions
- PlanSerializer: Subscription plan tiers
- SubscriptionSerializer: Organization-Plan relationships
- InvoiceSerializer: Billing records
- PlanFeatureSerializer: Plan-Feature junction table
- OrganizationUsageSerializer: Resource usage tracking

API Response Format:
    All serializers work with the E-Menum standard response format:
    {
        "success": true,
        "data": {...}
    }

Multi-Tenancy:
    - Feature, Plan, PlanFeature: Platform-level (no organization FK)
    - Subscription, Invoice, OrganizationUsage: Tenant-scoped with auto-injection

Critical Rules:
    - Use TenantModelSerializer for tenant-scoped models
    - Use SoftDeleteModelSerializer for platform-level models
    - Never expose deleted_at field in public API responses
"""

from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

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
    BillingPeriod,
)
from shared.serializers.base import (
    TenantModelSerializer,
    SoftDeleteModelSerializer,
    MinimalSerializer,
)


# =============================================================================
# MINIMAL SERIALIZERS (For nested representations)
# =============================================================================


class FeatureMinimalSerializer(MinimalSerializer):
    """Minimal feature serializer for nested representations."""

    class Meta:
        model = Feature
        fields = ["id", "code", "name", "feature_type", "category", "is_active"]


class PlanMinimalSerializer(MinimalSerializer):
    """Minimal plan serializer for nested representations."""

    class Meta:
        model = Plan
        fields = ["id", "name", "slug", "tier", "is_active", "is_default"]


class SubscriptionMinimalSerializer(MinimalSerializer):
    """Minimal subscription serializer for nested representations."""

    class Meta:
        model = Subscription
        fields = ["id", "status", "billing_period", "current_period_end"]


# =============================================================================
# FEATURE SERIALIZERS (Platform-level)
# =============================================================================


class FeatureListSerializer(SoftDeleteModelSerializer):
    """
    Serializer for feature list view.

    Features are platform-level (not tenant-scoped).
    """

    class Meta:
        model = Feature
        fields = [
            "id",
            "code",
            "name",
            "description",
            "feature_type",
            "category",
            "default_value",
            "is_active",
            "sort_order",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class FeatureDetailSerializer(SoftDeleteModelSerializer):
    """
    Serializer for feature detail view.
    """

    is_boolean = serializers.BooleanField(read_only=True)
    is_limit = serializers.BooleanField(read_only=True)
    is_usage = serializers.BooleanField(read_only=True)

    class Meta:
        model = Feature
        fields = [
            "id",
            "code",
            "name",
            "description",
            "feature_type",
            "category",
            "default_value",
            "is_active",
            "sort_order",
            "metadata",
            "is_boolean",
            "is_limit",
            "is_usage",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "is_boolean",
            "is_limit",
            "is_usage",
            "created_at",
            "updated_at",
        ]


class FeatureCreateSerializer(SoftDeleteModelSerializer):
    """
    Serializer for creating a new feature.
    """

    class Meta:
        model = Feature
        fields = [
            "code",
            "name",
            "description",
            "feature_type",
            "category",
            "default_value",
            "is_active",
            "sort_order",
            "metadata",
        ]

    def validate_code(self, value: str) -> str:
        """Validate code uniqueness."""
        existing = Feature.objects.filter(code=value, deleted_at__isnull=True).exists()
        if existing:
            raise ValidationError(_("A feature with this code already exists."))
        return value


class FeatureUpdateSerializer(SoftDeleteModelSerializer):
    """
    Serializer for updating an existing feature.
    """

    class Meta:
        model = Feature
        fields = [
            "name",
            "description",
            "feature_type",
            "category",
            "default_value",
            "is_active",
            "sort_order",
            "metadata",
        ]

    def validate_code(self, value: str) -> str:
        """Validate code uniqueness (excluding current feature)."""
        instance = self.instance
        if instance:
            existing = (
                Feature.objects.filter(code=value, deleted_at__isnull=True)
                .exclude(pk=instance.pk)
                .exists()
            )
            if existing:
                raise ValidationError(_("A feature with this code already exists."))
        return value


# =============================================================================
# PLAN SERIALIZERS (Platform-level)
# =============================================================================


class PlanFeatureInlineSerializer(serializers.ModelSerializer):
    """
    Inline serializer for plan features within plan detail.
    """

    feature = FeatureMinimalSerializer(read_only=True)

    class Meta:
        model = PlanFeature
        fields = [
            "id",
            "feature",
            "value",
            "is_enabled",
            "sort_order",
        ]
        read_only_fields = ["id"]


class PlanListSerializer(SoftDeleteModelSerializer):
    """
    Serializer for plan list view.

    Plans are platform-level (not tenant-scoped).
    """

    formatted_price_monthly = serializers.CharField(read_only=True)
    formatted_price_yearly = serializers.CharField(read_only=True)
    yearly_discount_percentage = serializers.IntegerField(read_only=True)

    class Meta:
        model = Plan
        fields = [
            "id",
            "name",
            "slug",
            "tier",
            "short_description",
            "price_monthly",
            "price_yearly",
            "formatted_price_monthly",
            "formatted_price_yearly",
            "yearly_discount_percentage",
            "currency",
            "trial_days",
            "is_active",
            "is_default",
            "is_public",
            "highlight_text",
            "sort_order",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "formatted_price_monthly",
            "formatted_price_yearly",
            "yearly_discount_percentage",
            "created_at",
            "updated_at",
        ]


class PlanDetailSerializer(SoftDeleteModelSerializer):
    """
    Serializer for plan detail view.
    """

    formatted_price_monthly = serializers.CharField(read_only=True)
    formatted_price_yearly = serializers.CharField(read_only=True)
    yearly_discount_percentage = serializers.IntegerField(read_only=True)
    yearly_savings = serializers.DecimalField(
        max_digits=10, decimal_places=2, read_only=True
    )
    has_trial = serializers.BooleanField(read_only=True)
    is_free = serializers.BooleanField(read_only=True)
    plan_features = PlanFeatureInlineSerializer(many=True, read_only=True)
    subscription_count = serializers.SerializerMethodField(
        help_text=_("Number of active subscriptions using this plan")
    )

    class Meta:
        model = Plan
        fields = [
            "id",
            "name",
            "slug",
            "tier",
            "description",
            "short_description",
            "price_monthly",
            "price_yearly",
            "formatted_price_monthly",
            "formatted_price_yearly",
            "yearly_discount_percentage",
            "yearly_savings",
            "currency",
            "limits",
            "feature_flags",
            "trial_days",
            "has_trial",
            "is_active",
            "is_default",
            "is_public",
            "is_custom",
            "is_free",
            "highlight_text",
            "sort_order",
            "metadata",
            "plan_features",
            "subscription_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "formatted_price_monthly",
            "formatted_price_yearly",
            "yearly_discount_percentage",
            "yearly_savings",
            "has_trial",
            "is_free",
            "plan_features",
            "subscription_count",
            "created_at",
            "updated_at",
        ]

    def get_subscription_count(self, obj) -> int:
        """Get the number of active subscriptions using this plan."""
        return obj.subscriptions.filter(
            status__in=[SubscriptionStatus.ACTIVE, SubscriptionStatus.TRIALING],
            deleted_at__isnull=True,
        ).count()


class PlanCreateSerializer(SoftDeleteModelSerializer):
    """
    Serializer for creating a new plan.
    """

    class Meta:
        model = Plan
        fields = [
            "name",
            "slug",
            "tier",
            "description",
            "short_description",
            "price_monthly",
            "price_yearly",
            "currency",
            "limits",
            "feature_flags",
            "trial_days",
            "is_active",
            "is_default",
            "is_public",
            "is_custom",
            "highlight_text",
            "sort_order",
            "metadata",
        ]

    def validate_slug(self, value: str) -> str:
        """Validate slug uniqueness."""
        existing = Plan.objects.filter(slug=value, deleted_at__isnull=True).exists()
        if existing:
            raise ValidationError(_("A plan with this slug already exists."))
        return value


class PlanUpdateSerializer(SoftDeleteModelSerializer):
    """
    Serializer for updating an existing plan.
    """

    class Meta:
        model = Plan
        fields = [
            "name",
            "slug",
            "tier",
            "description",
            "short_description",
            "price_monthly",
            "price_yearly",
            "currency",
            "limits",
            "feature_flags",
            "trial_days",
            "is_active",
            "is_default",
            "is_public",
            "is_custom",
            "highlight_text",
            "sort_order",
            "metadata",
        ]

    def validate_slug(self, value: str) -> str:
        """Validate slug uniqueness (excluding current plan)."""
        instance = self.instance
        if instance:
            existing = (
                Plan.objects.filter(slug=value, deleted_at__isnull=True)
                .exclude(pk=instance.pk)
                .exists()
            )
            if existing:
                raise ValidationError(_("A plan with this slug already exists."))
        return value


# =============================================================================
# SUBSCRIPTION SERIALIZERS (Tenant-scoped)
# =============================================================================


class SubscriptionListSerializer(TenantModelSerializer):
    """
    Serializer for subscription list view.
    """

    plan = PlanMinimalSerializer(read_only=True)
    formatted_price = serializers.CharField(read_only=True)
    is_valid = serializers.BooleanField(read_only=True)

    class Meta:
        model = Subscription
        fields = [
            "id",
            "plan",
            "status",
            "billing_period",
            "current_price",
            "formatted_price",
            "currency",
            "trial_ends_at",
            "current_period_start",
            "current_period_end",
            "next_billing_date",
            "is_valid",
            "organization_id",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "organization_id",
            "formatted_price",
            "is_valid",
            "created_at",
            "updated_at",
        ]


class SubscriptionDetailSerializer(TenantModelSerializer):
    """
    Serializer for subscription detail view.
    """

    plan = PlanMinimalSerializer(read_only=True)
    plan_id = serializers.UUIDField(
        write_only=True,
        required=False,
        help_text=_("Plan UUID to associate with this subscription"),
    )
    formatted_price = serializers.CharField(read_only=True)
    is_valid = serializers.BooleanField(read_only=True)
    is_active = serializers.BooleanField(read_only=True)
    is_trialing = serializers.BooleanField(read_only=True)
    is_cancelled = serializers.BooleanField(read_only=True)
    is_expired = serializers.BooleanField(read_only=True)
    trial_remaining_days = serializers.IntegerField(read_only=True)
    days_until_renewal = serializers.IntegerField(read_only=True)

    class Meta:
        model = Subscription
        fields = [
            "id",
            "plan",
            "plan_id",
            "status",
            "billing_period",
            "payment_method",
            "current_price",
            "formatted_price",
            "currency",
            "trial_ends_at",
            "current_period_start",
            "current_period_end",
            "next_billing_date",
            "cancelled_at",
            "cancel_reason",
            "cancel_at_period_end",
            "external_subscription_id",
            "external_customer_id",
            "payment_details",
            "metadata",
            "is_valid",
            "is_active",
            "is_trialing",
            "is_cancelled",
            "is_expired",
            "trial_remaining_days",
            "days_until_renewal",
            "organization_id",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "organization_id",
            "formatted_price",
            "is_valid",
            "is_active",
            "is_trialing",
            "is_cancelled",
            "is_expired",
            "trial_remaining_days",
            "days_until_renewal",
            "created_at",
            "updated_at",
        ]


class SubscriptionCreateSerializer(TenantModelSerializer):
    """
    Serializer for creating a new subscription.
    """

    plan_id = serializers.UUIDField(
        required=True, help_text=_("Plan UUID for this subscription")
    )

    class Meta:
        model = Subscription
        fields = [
            "plan_id",
            "billing_period",
            "payment_method",
            "external_subscription_id",
            "external_customer_id",
            "payment_details",
            "metadata",
        ]

    def validate_plan_id(self, value):
        """Validate plan exists and is active."""
        try:
            plan = Plan.objects.get(id=value, is_active=True, deleted_at__isnull=True)
            return plan
        except Plan.DoesNotExist:
            raise ValidationError(_("Plan not found or not active."))

    def validate(self, attrs):
        """Validate subscription creation."""
        attrs = super().validate(attrs)

        # Get organization from context
        request = self.context.get("request")
        organization = getattr(request, "organization", None) if request else None

        if organization:
            # Check if organization already has an active subscription
            existing = Subscription.objects.filter(
                organization=organization,
                status__in=[SubscriptionStatus.ACTIVE, SubscriptionStatus.TRIALING],
                deleted_at__isnull=True,
            ).exists()
            if existing:
                raise ValidationError(
                    {
                        "non_field_errors": [
                            _("Organization already has an active subscription.")
                        ]
                    }
                )

        return attrs

    def create(self, validated_data):
        """Create subscription with plan handling."""
        plan = validated_data.pop("plan_id")
        validated_data["plan"] = plan

        # Set initial values based on plan and billing period
        billing_period = validated_data.get("billing_period", BillingPeriod.MONTHLY)
        if billing_period == BillingPeriod.YEARLY:
            validated_data["current_price"] = plan.price_yearly
        else:
            validated_data["current_price"] = plan.price_monthly

        validated_data["currency"] = plan.currency

        # Set trial period if plan has trial
        if plan.trial_days > 0:
            from datetime import timedelta

            validated_data["status"] = SubscriptionStatus.TRIALING
            validated_data["trial_ends_at"] = timezone.now() + timedelta(
                days=plan.trial_days
            )
            validated_data["current_period_start"] = timezone.now()
            validated_data["current_period_end"] = validated_data["trial_ends_at"]
        else:
            validated_data["status"] = SubscriptionStatus.ACTIVE
            validated_data["current_period_start"] = timezone.now()
            # Set period end based on billing period
            from datetime import timedelta

            if billing_period == BillingPeriod.YEARLY:
                validated_data["current_period_end"] = timezone.now() + timedelta(
                    days=365
                )
            else:
                validated_data["current_period_end"] = timezone.now() + timedelta(
                    days=30
                )

        validated_data["next_billing_date"] = validated_data["current_period_end"]

        return super().create(validated_data)


class SubscriptionUpdateSerializer(TenantModelSerializer):
    """
    Serializer for updating an existing subscription.

    Note: Plan changes should use the change_plan action, not regular update.
    """

    class Meta:
        model = Subscription
        fields = [
            "billing_period",
            "payment_method",
            "external_subscription_id",
            "external_customer_id",
            "payment_details",
            "metadata",
        ]


class SubscriptionCancelSerializer(serializers.Serializer):
    """
    Serializer for subscription cancellation.
    """

    reason = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=1000,
        help_text=_("Reason for cancellation"),
    )
    at_period_end = serializers.BooleanField(
        default=True,
        help_text=_(
            "If true, cancel at end of current period. If false, cancel immediately."
        ),
    )


class SubscriptionChangePlanSerializer(serializers.Serializer):
    """
    Serializer for plan change requests.
    """

    plan_id = serializers.UUIDField(required=True, help_text=_("New plan UUID"))
    prorate = serializers.BooleanField(
        default=True, help_text=_("Whether to prorate the change")
    )

    def validate_plan_id(self, value):
        """Validate plan exists and is active."""
        try:
            plan = Plan.objects.get(id=value, is_active=True, deleted_at__isnull=True)
            return plan
        except Plan.DoesNotExist:
            raise ValidationError(_("Plan not found or not active."))


# =============================================================================
# INVOICE SERIALIZERS (Tenant-scoped)
# =============================================================================


class InvoiceListSerializer(TenantModelSerializer):
    """
    Serializer for invoice list view.
    """

    subscription = SubscriptionMinimalSerializer(read_only=True)
    formatted_total = serializers.CharField(read_only=True)
    is_overdue = serializers.BooleanField(read_only=True)

    class Meta:
        model = Invoice
        fields = [
            "id",
            "invoice_number",
            "subscription",
            "status",
            "amount_total",
            "formatted_total",
            "currency",
            "due_date",
            "paid_at",
            "is_overdue",
            "organization_id",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "organization_id",
            "formatted_total",
            "is_overdue",
            "created_at",
            "updated_at",
        ]


class InvoiceDetailSerializer(TenantModelSerializer):
    """
    Serializer for invoice detail view.
    """

    subscription = SubscriptionMinimalSerializer(read_only=True)
    subscription_id = serializers.UUIDField(
        write_only=True,
        required=False,
        allow_null=True,
        help_text=_("Subscription UUID for this invoice"),
    )
    formatted_total = serializers.CharField(read_only=True)
    is_overdue = serializers.BooleanField(read_only=True)
    is_paid = serializers.BooleanField(read_only=True)
    is_pending = serializers.BooleanField(read_only=True)
    amount_due = serializers.DecimalField(
        max_digits=10, decimal_places=2, read_only=True
    )

    class Meta:
        model = Invoice
        fields = [
            "id",
            "invoice_number",
            "subscription",
            "subscription_id",
            "status",
            "amount_subtotal",
            "amount_tax",
            "amount_total",
            "amount_paid",
            "amount_refunded",
            "amount_due",
            "formatted_total",
            "currency",
            "due_date",
            "paid_at",
            "period_start",
            "period_end",
            "description",
            "line_items",
            "billing_address",
            "external_invoice_id",
            "external_payment_id",
            "payment_details",
            "pdf_url",
            "metadata",
            "is_overdue",
            "is_paid",
            "is_pending",
            "organization_id",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "organization_id",
            "formatted_total",
            "is_overdue",
            "is_paid",
            "is_pending",
            "amount_due",
            "created_at",
            "updated_at",
        ]


class InvoiceCreateSerializer(TenantModelSerializer):
    """
    Serializer for creating a new invoice.
    """

    subscription_id = serializers.UUIDField(
        required=False,
        allow_null=True,
        help_text=_("Subscription UUID for this invoice"),
    )
    auto_generate_number = serializers.BooleanField(
        default=True, write_only=True, help_text=_("Auto-generate invoice number")
    )

    class Meta:
        model = Invoice
        fields = [
            "subscription_id",
            "invoice_number",
            "auto_generate_number",
            "status",
            "amount_subtotal",
            "amount_tax",
            "amount_total",
            "currency",
            "due_date",
            "period_start",
            "period_end",
            "description",
            "line_items",
            "billing_address",
            "external_invoice_id",
            "metadata",
        ]

    def validate_subscription_id(self, value):
        """Validate subscription belongs to the same organization."""
        if value is None:
            return None

        request = self.context.get("request")
        organization = getattr(request, "organization", None) if request else None

        if organization:
            try:
                subscription = Subscription.objects.get(
                    id=value, organization=organization, deleted_at__isnull=True
                )
                return subscription
            except Subscription.DoesNotExist:
                raise ValidationError(_("Subscription not found."))

        return value

    def create(self, validated_data):
        """Create invoice with auto-generated number."""
        subscription = validated_data.pop("subscription_id", None)
        auto_generate_number = validated_data.pop("auto_generate_number", True)

        if subscription:
            validated_data["subscription"] = subscription

        # Auto-generate invoice number if requested
        if auto_generate_number and not validated_data.get("invoice_number"):
            request = self.context.get("request")
            organization = getattr(request, "organization", None) if request else None
            if organization:
                validated_data["invoice_number"] = Invoice.generate_number(organization)

        return super().create(validated_data)


class InvoiceUpdateSerializer(TenantModelSerializer):
    """
    Serializer for updating an existing invoice.
    """

    class Meta:
        model = Invoice
        fields = [
            "status",
            "due_date",
            "description",
            "line_items",
            "billing_address",
            "external_invoice_id",
            "external_payment_id",
            "payment_details",
            "pdf_url",
            "metadata",
        ]


class InvoicePaymentSerializer(serializers.Serializer):
    """
    Serializer for marking an invoice as paid.
    """

    payment_id = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=255,
        help_text=_("External payment transaction ID"),
    )
    payment_details = serializers.DictField(
        required=False, help_text=_("Masked payment method details")
    )
    amount = serializers.DecimalField(
        required=False,
        max_digits=10,
        decimal_places=2,
        help_text=_("Amount paid (defaults to total)"),
    )


class InvoiceRefundSerializer(serializers.Serializer):
    """
    Serializer for refunding an invoice.
    """

    amount = serializers.DecimalField(
        required=False,
        max_digits=10,
        decimal_places=2,
        help_text=_("Amount to refund (defaults to full amount)"),
    )
    reason = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=1000,
        help_text=_("Reason for refund"),
    )


# =============================================================================
# PLAN FEATURE SERIALIZERS (Platform-level junction table)
# =============================================================================


class PlanFeatureListSerializer(serializers.ModelSerializer):
    """
    Serializer for plan feature list view.
    """

    plan = PlanMinimalSerializer(read_only=True)
    feature = FeatureMinimalSerializer(read_only=True)

    class Meta:
        model = PlanFeature
        fields = [
            "id",
            "plan",
            "feature",
            "value",
            "is_enabled",
            "sort_order",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class PlanFeatureDetailSerializer(serializers.ModelSerializer):
    """
    Serializer for plan feature detail view.
    """

    plan = PlanMinimalSerializer(read_only=True)
    plan_id = serializers.UUIDField(
        write_only=True, required=False, help_text=_("Plan UUID")
    )
    feature = FeatureMinimalSerializer(read_only=True)
    feature_id = serializers.UUIDField(
        write_only=True, required=False, help_text=_("Feature UUID")
    )

    class Meta:
        model = PlanFeature
        fields = [
            "id",
            "plan",
            "plan_id",
            "feature",
            "feature_id",
            "value",
            "is_enabled",
            "sort_order",
            "metadata",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class PlanFeatureCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating a plan feature link.
    """

    plan_id = serializers.UUIDField(required=True, help_text=_("Plan UUID"))
    feature_id = serializers.UUIDField(required=True, help_text=_("Feature UUID"))

    class Meta:
        model = PlanFeature
        fields = [
            "plan_id",
            "feature_id",
            "value",
            "is_enabled",
            "sort_order",
            "metadata",
        ]

    def validate_plan_id(self, value):
        """Validate plan exists."""
        try:
            plan = Plan.objects.get(id=value, deleted_at__isnull=True)
            return plan
        except Plan.DoesNotExist:
            raise ValidationError(_("Plan not found."))

    def validate_feature_id(self, value):
        """Validate feature exists."""
        try:
            feature = Feature.objects.get(id=value, deleted_at__isnull=True)
            return feature
        except Feature.DoesNotExist:
            raise ValidationError(_("Feature not found."))

    def validate(self, attrs):
        """Validate plan-feature uniqueness."""
        attrs = super().validate(attrs)

        plan = attrs.get("plan_id")
        feature = attrs.get("feature_id")

        if plan and feature:
            existing = PlanFeature.objects.filter(plan=plan, feature=feature).exists()
            if existing:
                raise ValidationError(
                    {
                        "non_field_errors": [
                            _("This feature is already linked to this plan.")
                        ]
                    }
                )

        return attrs

    def create(self, validated_data):
        """Create plan feature with FK handling."""
        plan = validated_data.pop("plan_id")
        feature = validated_data.pop("feature_id")

        validated_data["plan"] = plan
        validated_data["feature"] = feature

        return super().create(validated_data)


class PlanFeatureUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating a plan feature link.
    """

    class Meta:
        model = PlanFeature
        fields = [
            "value",
            "is_enabled",
            "sort_order",
            "metadata",
        ]


# =============================================================================
# ORGANIZATION USAGE SERIALIZERS (Tenant-scoped)
# =============================================================================


class OrganizationUsageListSerializer(TenantModelSerializer):
    """
    Serializer for organization usage list view.
    """

    feature = FeatureMinimalSerializer(read_only=True)
    usage_percentage = serializers.FloatField(read_only=True)
    is_limit_exceeded = serializers.BooleanField(read_only=True)

    class Meta:
        model = OrganizationUsage
        fields = [
            "id",
            "feature",
            "current_usage",
            "usage_limit",
            "usage_percentage",
            "is_limit_exceeded",
            "period_start",
            "period_end",
            "last_usage_at",
            "organization_id",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "organization_id",
            "usage_percentage",
            "is_limit_exceeded",
            "created_at",
            "updated_at",
        ]


class OrganizationUsageDetailSerializer(TenantModelSerializer):
    """
    Serializer for organization usage detail view.
    """

    feature = FeatureMinimalSerializer(read_only=True)
    feature_id = serializers.UUIDField(
        write_only=True, required=False, help_text=_("Feature UUID to track usage for")
    )
    usage_percentage = serializers.FloatField(read_only=True)
    is_limit_exceeded = serializers.BooleanField(read_only=True)
    is_unlimited = serializers.BooleanField(read_only=True)
    remaining_quota = serializers.IntegerField(read_only=True)

    class Meta:
        model = OrganizationUsage
        fields = [
            "id",
            "feature",
            "feature_id",
            "current_usage",
            "usage_limit",
            "usage_percentage",
            "is_limit_exceeded",
            "is_unlimited",
            "remaining_quota",
            "period_start",
            "period_end",
            "last_reset_at",
            "last_usage_at",
            "metadata",
            "organization_id",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "organization_id",
            "usage_percentage",
            "is_limit_exceeded",
            "is_unlimited",
            "remaining_quota",
            "created_at",
            "updated_at",
        ]


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Minimal serializers
    "FeatureMinimalSerializer",
    "PlanMinimalSerializer",
    "SubscriptionMinimalSerializer",
    # Feature serializers
    "FeatureListSerializer",
    "FeatureDetailSerializer",
    "FeatureCreateSerializer",
    "FeatureUpdateSerializer",
    # Plan serializers
    "PlanListSerializer",
    "PlanDetailSerializer",
    "PlanCreateSerializer",
    "PlanUpdateSerializer",
    "PlanFeatureInlineSerializer",
    # Subscription serializers
    "SubscriptionListSerializer",
    "SubscriptionDetailSerializer",
    "SubscriptionCreateSerializer",
    "SubscriptionUpdateSerializer",
    "SubscriptionCancelSerializer",
    "SubscriptionChangePlanSerializer",
    # Invoice serializers
    "InvoiceListSerializer",
    "InvoiceDetailSerializer",
    "InvoiceCreateSerializer",
    "InvoiceUpdateSerializer",
    "InvoicePaymentSerializer",
    "InvoiceRefundSerializer",
    # PlanFeature serializers
    "PlanFeatureListSerializer",
    "PlanFeatureDetailSerializer",
    "PlanFeatureCreateSerializer",
    "PlanFeatureUpdateSerializer",
    # OrganizationUsage serializers
    "OrganizationUsageListSerializer",
    "OrganizationUsageDetailSerializer",
]
