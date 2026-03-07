# Generated manually for E-Menum Subscriptions Module
# This migration creates all subscription-related models

import uuid
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    """
    Initial migration for the subscriptions module.

    Creates:
    - Feature: Individual capabilities/features that can be enabled per plan
    - Plan: Subscription tiers (Free, Starter, Growth, Professional, Enterprise)
    - Subscription: Organization-Plan relationship with billing lifecycle
    - Invoice: Billing records for subscriptions
    - PlanFeature: Junction table for plan-feature relationships
    - OrganizationUsage: Resource usage tracking per organization
    """

    initial = True

    dependencies = [
        ("core", "0001_initial"),
    ]

    operations = [
        # 1. Feature model (individual capabilities enabled per plan)
        migrations.CreateModel(
            name="Feature",
            fields=[
                (
                    "created_at",
                    models.DateTimeField(
                        auto_now_add=True,
                        help_text="Timestamp when record was created",
                        verbose_name="Created at",
                    ),
                ),
                (
                    "updated_at",
                    models.DateTimeField(
                        auto_now=True,
                        help_text="Timestamp when record was last updated",
                        verbose_name="Updated at",
                    ),
                ),
                (
                    "deleted_at",
                    models.DateTimeField(
                        blank=True,
                        db_index=True,
                        help_text="Timestamp when record was soft-deleted (null = active)",
                        null=True,
                        verbose_name="Deleted at",
                    ),
                ),
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        help_text="Unique identifier (UUID)",
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "code",
                    models.CharField(
                        help_text="Unique identifier code for feature lookup (e.g., max_menus, ai_enabled)",
                        max_length=100,
                        unique=True,
                        verbose_name="Code",
                    ),
                ),
                (
                    "name",
                    models.CharField(
                        help_text="Human-readable display name for the feature",
                        max_length=200,
                        verbose_name="Name",
                    ),
                ),
                (
                    "description",
                    models.TextField(
                        blank=True,
                        help_text="Detailed description of what this feature provides",
                        null=True,
                        verbose_name="Description",
                    ),
                ),
                (
                    "feature_type",
                    models.CharField(
                        choices=[
                            ("BOOLEAN", "Boolean"),
                            ("LIMIT", "Limit"),
                            ("USAGE", "Usage"),
                        ],
                        db_index=True,
                        default="BOOLEAN",
                        help_text="Type of feature: BOOLEAN (on/off), LIMIT (max count), USAGE (metered)",
                        max_length=20,
                        verbose_name="Feature type",
                    ),
                ),
                (
                    "default_value",
                    models.JSONField(
                        blank=True,
                        default=dict,
                        help_text="Default value for the feature (JSON format)",
                        verbose_name="Default value",
                    ),
                ),
                (
                    "category",
                    models.CharField(
                        db_index=True,
                        help_text="Category for grouping features (e.g., menus, orders, ai, analytics)",
                        max_length=50,
                        verbose_name="Category",
                    ),
                ),
                (
                    "sort_order",
                    models.PositiveIntegerField(
                        default=0,
                        help_text="Display order within category (lower numbers appear first)",
                        verbose_name="Sort order",
                    ),
                ),
                (
                    "is_active",
                    models.BooleanField(
                        db_index=True,
                        default=True,
                        help_text="Whether the feature is currently available",
                        verbose_name="Is active",
                    ),
                ),
                (
                    "metadata",
                    models.JSONField(
                        blank=True,
                        default=dict,
                        help_text="Additional metadata for the feature (JSON)",
                        verbose_name="Metadata",
                    ),
                ),
            ],
            options={
                "verbose_name": "Feature",
                "verbose_name_plural": "Features",
                "db_table": "features",
                "ordering": ["category", "sort_order", "name"],
            },
        ),
        migrations.AddIndex(
            model_name="feature",
            index=models.Index(fields=["code"], name="feature_code_idx"),
        ),
        migrations.AddIndex(
            model_name="feature",
            index=models.Index(
                fields=["category", "sort_order"], name="feature_cat_sort_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="feature",
            index=models.Index(fields=["feature_type"], name="feature_type_idx"),
        ),
        migrations.AddIndex(
            model_name="feature",
            index=models.Index(
                fields=["is_active", "deleted_at"], name="feature_active_del_idx"
            ),
        ),
        # 2. Plan model (subscription tiers)
        migrations.CreateModel(
            name="Plan",
            fields=[
                (
                    "created_at",
                    models.DateTimeField(
                        auto_now_add=True,
                        help_text="Timestamp when record was created",
                        verbose_name="Created at",
                    ),
                ),
                (
                    "updated_at",
                    models.DateTimeField(
                        auto_now=True,
                        help_text="Timestamp when record was last updated",
                        verbose_name="Updated at",
                    ),
                ),
                (
                    "deleted_at",
                    models.DateTimeField(
                        blank=True,
                        db_index=True,
                        help_text="Timestamp when record was soft-deleted (null = active)",
                        null=True,
                        verbose_name="Deleted at",
                    ),
                ),
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        help_text="Unique identifier (UUID)",
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "name",
                    models.CharField(
                        help_text="Display name of the plan (e.g., Starter, Professional)",
                        max_length=100,
                        verbose_name="Name",
                    ),
                ),
                (
                    "slug",
                    models.SlugField(
                        help_text="URL-friendly identifier (globally unique)",
                        max_length=100,
                        unique=True,
                        verbose_name="Slug",
                    ),
                ),
                (
                    "tier",
                    models.CharField(
                        choices=[
                            ("FREE", "Free"),
                            ("STARTER", "Starter"),
                            ("GROWTH", "Growth"),
                            ("PROFESSIONAL", "Professional"),
                            ("ENTERPRISE", "Enterprise"),
                        ],
                        db_index=True,
                        help_text="Plan tier level (FREE, STARTER, GROWTH, etc.)",
                        max_length=20,
                        verbose_name="Tier",
                    ),
                ),
                (
                    "description",
                    models.TextField(
                        blank=True,
                        help_text="Detailed description of the plan and its features",
                        null=True,
                        verbose_name="Description",
                    ),
                ),
                (
                    "short_description",
                    models.CharField(
                        blank=True,
                        help_text="Brief tagline for the plan (shown on pricing cards)",
                        max_length=200,
                        null=True,
                        verbose_name="Short description",
                    ),
                ),
                (
                    "price_monthly",
                    models.DecimalField(
                        decimal_places=2,
                        default=0,
                        help_text="Monthly subscription price",
                        max_digits=10,
                        verbose_name="Monthly price",
                    ),
                ),
                (
                    "price_yearly",
                    models.DecimalField(
                        decimal_places=2,
                        default=0,
                        help_text="Yearly subscription price (typically with discount)",
                        max_digits=10,
                        verbose_name="Yearly price",
                    ),
                ),
                (
                    "currency",
                    models.CharField(
                        default="TRY",
                        help_text="Currency code for pricing (e.g., TRY, USD, EUR)",
                        max_length=3,
                        verbose_name="Currency",
                    ),
                ),
                (
                    "limits",
                    models.JSONField(
                        blank=True,
                        default=dict,
                        help_text='Plan limits as JSON (e.g., {"max_menus": 3, "max_products": 200, "max_qr_codes": 10, "max_users": 5, "storage_mb": 500})',
                        verbose_name="Limits",
                    ),
                ),
                (
                    "feature_flags",
                    models.JSONField(
                        blank=True,
                        default=dict,
                        help_text='Boolean feature flags as JSON (e.g., {"ai_enabled": true, "custom_domain": false, "api_access": false})',
                        verbose_name="Feature flags",
                    ),
                ),
                (
                    "trial_days",
                    models.PositiveIntegerField(
                        default=14,
                        help_text="Number of trial days for this plan (0 for no trial)",
                        verbose_name="Trial days",
                    ),
                ),
                (
                    "is_active",
                    models.BooleanField(
                        db_index=True,
                        default=True,
                        help_text="Whether the plan is available for subscription",
                        verbose_name="Is active",
                    ),
                ),
                (
                    "is_default",
                    models.BooleanField(
                        db_index=True,
                        default=False,
                        help_text="Whether this is the default plan for new organizations",
                        verbose_name="Is default",
                    ),
                ),
                (
                    "is_public",
                    models.BooleanField(
                        db_index=True,
                        default=True,
                        help_text="Whether the plan is visible on the public pricing page",
                        verbose_name="Is public",
                    ),
                ),
                (
                    "is_custom",
                    models.BooleanField(
                        default=False,
                        help_text="Whether this is a custom enterprise plan",
                        verbose_name="Is custom",
                    ),
                ),
                (
                    "highlight_text",
                    models.CharField(
                        blank=True,
                        help_text='Optional badge text (e.g., "Most Popular", "Best Value")',
                        max_length=50,
                        null=True,
                        verbose_name="Highlight text",
                    ),
                ),
                (
                    "sort_order",
                    models.PositiveIntegerField(
                        default=0,
                        help_text="Display order on pricing page (lower numbers appear first)",
                        verbose_name="Sort order",
                    ),
                ),
                (
                    "metadata",
                    models.JSONField(
                        blank=True,
                        default=dict,
                        help_text="Additional plan metadata (JSON)",
                        verbose_name="Metadata",
                    ),
                ),
            ],
            options={
                "verbose_name": "Plan",
                "verbose_name_plural": "Plans",
                "db_table": "plans",
                "ordering": ["sort_order", "price_monthly"],
            },
        ),
        migrations.AddIndex(
            model_name="plan",
            index=models.Index(fields=["tier"], name="plan_tier_idx"),
        ),
        migrations.AddIndex(
            model_name="plan",
            index=models.Index(fields=["slug"], name="plan_slug_idx"),
        ),
        migrations.AddIndex(
            model_name="plan",
            index=models.Index(
                fields=["is_active", "is_public"], name="plan_active_public_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="plan",
            index=models.Index(fields=["is_default"], name="plan_default_idx"),
        ),
        migrations.AddIndex(
            model_name="plan",
            index=models.Index(fields=["sort_order"], name="plan_sort_idx"),
        ),
        migrations.AddIndex(
            model_name="plan",
            index=models.Index(fields=["deleted_at"], name="plan_deleted_idx"),
        ),
        # 3. Subscription model (organization-plan relationship with billing lifecycle)
        migrations.CreateModel(
            name="Subscription",
            fields=[
                (
                    "created_at",
                    models.DateTimeField(
                        auto_now_add=True,
                        help_text="Timestamp when record was created",
                        verbose_name="Created at",
                    ),
                ),
                (
                    "updated_at",
                    models.DateTimeField(
                        auto_now=True,
                        help_text="Timestamp when record was last updated",
                        verbose_name="Updated at",
                    ),
                ),
                (
                    "deleted_at",
                    models.DateTimeField(
                        blank=True,
                        db_index=True,
                        help_text="Timestamp when record was soft-deleted (null = active)",
                        null=True,
                        verbose_name="Deleted at",
                    ),
                ),
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        help_text="Unique identifier (UUID)",
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("TRIALING", "Trialing"),
                            ("ACTIVE", "Active"),
                            ("PAST_DUE", "Past Due"),
                            ("CANCELLED", "Cancelled"),
                            ("EXPIRED", "Expired"),
                            ("SUSPENDED", "Suspended"),
                        ],
                        db_index=True,
                        default="TRIALING",
                        help_text="Current subscription status",
                        max_length=20,
                        verbose_name="Status",
                    ),
                ),
                (
                    "billing_period",
                    models.CharField(
                        choices=[("MONTHLY", "Monthly"), ("YEARLY", "Yearly")],
                        default="MONTHLY",
                        help_text="Billing cycle (MONTHLY or YEARLY)",
                        max_length=20,
                        verbose_name="Billing period",
                    ),
                ),
                (
                    "payment_method",
                    models.CharField(
                        blank=True,
                        choices=[
                            ("CREDIT_CARD", "Credit Card"),
                            ("BANK_TRANSFER", "Bank Transfer"),
                            ("IYZICO", "Iyzico"),
                            ("OTHER", "Other"),
                        ],
                        help_text="How the subscription is paid",
                        max_length=20,
                        null=True,
                        verbose_name="Payment method",
                    ),
                ),
                (
                    "current_price",
                    models.DecimalField(
                        decimal_places=2,
                        default=0,
                        help_text="Locked-in price at subscription time",
                        max_digits=10,
                        verbose_name="Current price",
                    ),
                ),
                (
                    "currency",
                    models.CharField(
                        default="TRY",
                        help_text="Currency code for pricing (e.g., TRY, USD, EUR)",
                        max_length=3,
                        verbose_name="Currency",
                    ),
                ),
                (
                    "trial_ends_at",
                    models.DateTimeField(
                        blank=True,
                        db_index=True,
                        help_text="When the trial period ends (null if no trial)",
                        null=True,
                        verbose_name="Trial ends at",
                    ),
                ),
                (
                    "current_period_start",
                    models.DateTimeField(
                        blank=True,
                        help_text="Start of the current billing period",
                        null=True,
                        verbose_name="Current period start",
                    ),
                ),
                (
                    "current_period_end",
                    models.DateTimeField(
                        blank=True,
                        db_index=True,
                        help_text="End of the current billing period",
                        null=True,
                        verbose_name="Current period end",
                    ),
                ),
                (
                    "next_billing_date",
                    models.DateTimeField(
                        blank=True,
                        db_index=True,
                        help_text="When next payment will be charged",
                        null=True,
                        verbose_name="Next billing date",
                    ),
                ),
                (
                    "cancelled_at",
                    models.DateTimeField(
                        blank=True,
                        help_text="When cancellation was requested",
                        null=True,
                        verbose_name="Cancelled at",
                    ),
                ),
                (
                    "cancel_reason",
                    models.TextField(
                        blank=True,
                        help_text="User-provided reason for cancellation",
                        null=True,
                        verbose_name="Cancel reason",
                    ),
                ),
                (
                    "cancel_at_period_end",
                    models.BooleanField(
                        default=False,
                        help_text="If true, subscription will cancel at end of current period",
                        verbose_name="Cancel at period end",
                    ),
                ),
                (
                    "external_subscription_id",
                    models.CharField(
                        blank=True,
                        db_index=True,
                        help_text="Subscription ID from payment provider (e.g., Iyzico)",
                        max_length=255,
                        null=True,
                        verbose_name="External subscription ID",
                    ),
                ),
                (
                    "external_customer_id",
                    models.CharField(
                        blank=True,
                        db_index=True,
                        help_text="Customer ID from payment provider",
                        max_length=255,
                        null=True,
                        verbose_name="External customer ID",
                    ),
                ),
                (
                    "payment_details",
                    models.JSONField(
                        blank=True,
                        default=dict,
                        help_text='Masked payment method details (e.g., {"last4": "4242", "brand": "visa"})',
                        verbose_name="Payment details",
                    ),
                ),
                (
                    "metadata",
                    models.JSONField(
                        blank=True,
                        default=dict,
                        help_text="Additional subscription metadata (JSON)",
                        verbose_name="Metadata",
                    ),
                ),
                (
                    "organization",
                    models.ForeignKey(
                        help_text="Organization this subscription belongs to",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="subscriptions",
                        to="core.organization",
                        verbose_name="Organization",
                    ),
                ),
                (
                    "plan",
                    models.ForeignKey(
                        help_text="Subscription plan",
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="subscriptions",
                        to="subscriptions.plan",
                        verbose_name="Plan",
                    ),
                ),
            ],
            options={
                "verbose_name": "Subscription",
                "verbose_name_plural": "Subscriptions",
                "db_table": "subscriptions",
                "ordering": ["-created_at"],
            },
        ),
        migrations.AddIndex(
            model_name="subscription",
            index=models.Index(
                fields=["organization", "status"], name="sub_org_status_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="subscription",
            index=models.Index(
                fields=["status", "current_period_end"], name="sub_status_period_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="subscription",
            index=models.Index(
                fields=["status", "next_billing_date"], name="sub_status_billing_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="subscription",
            index=models.Index(fields=["trial_ends_at"], name="sub_trial_ends_idx"),
        ),
        migrations.AddIndex(
            model_name="subscription",
            index=models.Index(
                fields=["external_subscription_id"], name="sub_ext_sub_id_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="subscription",
            index=models.Index(
                fields=["external_customer_id"], name="sub_ext_cust_id_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="subscription",
            index=models.Index(fields=["deleted_at"], name="sub_deleted_idx"),
        ),
        # 4. Invoice model (billing records for subscriptions)
        migrations.CreateModel(
            name="Invoice",
            fields=[
                (
                    "created_at",
                    models.DateTimeField(
                        auto_now_add=True,
                        help_text="Timestamp when record was created",
                        verbose_name="Created at",
                    ),
                ),
                (
                    "updated_at",
                    models.DateTimeField(
                        auto_now=True,
                        help_text="Timestamp when record was last updated",
                        verbose_name="Updated at",
                    ),
                ),
                (
                    "deleted_at",
                    models.DateTimeField(
                        blank=True,
                        db_index=True,
                        help_text="Timestamp when record was soft-deleted (null = active)",
                        null=True,
                        verbose_name="Deleted at",
                    ),
                ),
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        help_text="Unique identifier (UUID)",
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "invoice_number",
                    models.CharField(
                        help_text="Unique invoice number within organization",
                        max_length=50,
                        verbose_name="Invoice number",
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("DRAFT", "Draft"),
                            ("PENDING", "Pending"),
                            ("PAID", "Paid"),
                            ("VOID", "Void"),
                            ("REFUNDED", "Refunded"),
                            ("UNCOLLECTIBLE", "Uncollectible"),
                        ],
                        db_index=True,
                        default="DRAFT",
                        help_text="Current invoice status",
                        max_length=20,
                        verbose_name="Status",
                    ),
                ),
                (
                    "amount_subtotal",
                    models.DecimalField(
                        decimal_places=2,
                        default=0,
                        help_text="Amount before tax",
                        max_digits=10,
                        verbose_name="Subtotal",
                    ),
                ),
                (
                    "amount_tax",
                    models.DecimalField(
                        decimal_places=2,
                        default=0,
                        help_text="Tax amount",
                        max_digits=10,
                        verbose_name="Tax amount",
                    ),
                ),
                (
                    "amount_total",
                    models.DecimalField(
                        decimal_places=2,
                        default=0,
                        help_text="Total amount due",
                        max_digits=10,
                        verbose_name="Total",
                    ),
                ),
                (
                    "amount_paid",
                    models.DecimalField(
                        decimal_places=2,
                        default=0,
                        help_text="Amount actually paid",
                        max_digits=10,
                        verbose_name="Amount paid",
                    ),
                ),
                (
                    "amount_refunded",
                    models.DecimalField(
                        decimal_places=2,
                        default=0,
                        help_text="Amount refunded",
                        max_digits=10,
                        verbose_name="Amount refunded",
                    ),
                ),
                (
                    "currency",
                    models.CharField(
                        default="TRY",
                        help_text="Currency code for this invoice",
                        max_length=3,
                        verbose_name="Currency",
                    ),
                ),
                (
                    "due_date",
                    models.DateTimeField(
                        blank=True,
                        db_index=True,
                        help_text="When payment is due",
                        null=True,
                        verbose_name="Due date",
                    ),
                ),
                (
                    "paid_at",
                    models.DateTimeField(
                        blank=True,
                        help_text="When payment was received",
                        null=True,
                        verbose_name="Paid at",
                    ),
                ),
                (
                    "period_start",
                    models.DateTimeField(
                        blank=True,
                        help_text="Start of billing period covered",
                        null=True,
                        verbose_name="Period start",
                    ),
                ),
                (
                    "period_end",
                    models.DateTimeField(
                        blank=True,
                        help_text="End of billing period covered",
                        null=True,
                        verbose_name="Period end",
                    ),
                ),
                (
                    "description",
                    models.TextField(
                        blank=True,
                        help_text="Invoice description or memo",
                        null=True,
                        verbose_name="Description",
                    ),
                ),
                (
                    "line_items",
                    models.JSONField(
                        blank=True,
                        default=list,
                        help_text="Array of line items: [{description, quantity, unit_price, amount}]",
                        verbose_name="Line items",
                    ),
                ),
                (
                    "billing_address",
                    models.JSONField(
                        blank=True,
                        default=dict,
                        help_text="Billing address details (JSON)",
                        verbose_name="Billing address",
                    ),
                ),
                (
                    "external_invoice_id",
                    models.CharField(
                        blank=True,
                        db_index=True,
                        help_text="Invoice ID from payment provider",
                        max_length=255,
                        null=True,
                        verbose_name="External invoice ID",
                    ),
                ),
                (
                    "external_payment_id",
                    models.CharField(
                        blank=True,
                        db_index=True,
                        help_text="Payment transaction ID from provider",
                        max_length=255,
                        null=True,
                        verbose_name="External payment ID",
                    ),
                ),
                (
                    "payment_details",
                    models.JSONField(
                        blank=True,
                        default=dict,
                        help_text="Masked payment method details",
                        verbose_name="Payment details",
                    ),
                ),
                (
                    "pdf_url",
                    models.URLField(
                        blank=True,
                        help_text="URL to generated PDF invoice",
                        max_length=500,
                        null=True,
                        verbose_name="PDF URL",
                    ),
                ),
                (
                    "metadata",
                    models.JSONField(
                        blank=True,
                        default=dict,
                        help_text="Additional invoice metadata (JSON)",
                        verbose_name="Metadata",
                    ),
                ),
                (
                    "organization",
                    models.ForeignKey(
                        help_text="Organization this invoice belongs to",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="invoices",
                        to="core.organization",
                        verbose_name="Organization",
                    ),
                ),
                (
                    "subscription",
                    models.ForeignKey(
                        blank=True,
                        help_text="Related subscription (null for one-time purchases)",
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="invoices",
                        to="subscriptions.subscription",
                        verbose_name="Subscription",
                    ),
                ),
            ],
            options={
                "verbose_name": "Invoice",
                "verbose_name_plural": "Invoices",
                "db_table": "invoices",
                "ordering": ["-created_at"],
            },
        ),
        migrations.AddConstraint(
            model_name="invoice",
            constraint=models.UniqueConstraint(
                fields=["organization", "invoice_number"],
                name="invoice_org_number_uniq",
            ),
        ),
        migrations.AddIndex(
            model_name="invoice",
            index=models.Index(
                fields=["organization", "status"], name="invoice_org_status_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="invoice",
            index=models.Index(
                fields=["status", "due_date"], name="invoice_status_due_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="invoice",
            index=models.Index(
                fields=["subscription"], name="invoice_subscription_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="invoice",
            index=models.Index(fields=["invoice_number"], name="invoice_number_idx"),
        ),
        migrations.AddIndex(
            model_name="invoice",
            index=models.Index(
                fields=["external_invoice_id"], name="invoice_ext_inv_id_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="invoice",
            index=models.Index(
                fields=["external_payment_id"], name="invoice_ext_pay_id_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="invoice",
            index=models.Index(fields=["deleted_at"], name="invoice_deleted_idx"),
        ),
        # 5. PlanFeature model (junction table linking Plans to Features)
        migrations.CreateModel(
            name="PlanFeature",
            fields=[
                (
                    "created_at",
                    models.DateTimeField(
                        auto_now_add=True,
                        help_text="Timestamp when record was created",
                        verbose_name="Created at",
                    ),
                ),
                (
                    "updated_at",
                    models.DateTimeField(
                        auto_now=True,
                        help_text="Timestamp when record was last updated",
                        verbose_name="Updated at",
                    ),
                ),
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        help_text="Unique identifier (UUID)",
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "value",
                    models.JSONField(
                        blank=True,
                        default=dict,
                        help_text='Plan-specific feature configuration (JSON). For LIMIT: {"limit": 10}, for BOOLEAN: {"enabled": true}, for USAGE: {"credits": 100, "reset_period": "monthly"}',
                        verbose_name="Value",
                    ),
                ),
                (
                    "is_enabled",
                    models.BooleanField(
                        db_index=True,
                        default=True,
                        help_text="Whether this feature is enabled for this plan",
                        verbose_name="Is enabled",
                    ),
                ),
                (
                    "sort_order",
                    models.PositiveIntegerField(
                        default=0,
                        help_text="Display order within plan (lower numbers appear first)",
                        verbose_name="Sort order",
                    ),
                ),
                (
                    "metadata",
                    models.JSONField(
                        blank=True,
                        default=dict,
                        help_text="Additional metadata for this plan-feature relationship (JSON)",
                        verbose_name="Metadata",
                    ),
                ),
                (
                    "plan",
                    models.ForeignKey(
                        help_text="Plan that includes this feature",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="plan_features",
                        to="subscriptions.plan",
                        verbose_name="Plan",
                    ),
                ),
                (
                    "feature",
                    models.ForeignKey(
                        help_text="Feature included in the plan",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="plan_features",
                        to="subscriptions.feature",
                        verbose_name="Feature",
                    ),
                ),
            ],
            options={
                "verbose_name": "Plan Feature",
                "verbose_name_plural": "Plan Features",
                "db_table": "plan_features",
                "ordering": ["plan", "sort_order", "feature__category"],
            },
        ),
        migrations.AddConstraint(
            model_name="planfeature",
            constraint=models.UniqueConstraint(
                fields=["plan", "feature"], name="planfeature_plan_feature_uniq"
            ),
        ),
        migrations.AddIndex(
            model_name="planfeature",
            index=models.Index(
                fields=["plan", "is_enabled"], name="planfeat_plan_enabled_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="planfeature",
            index=models.Index(fields=["feature"], name="planfeat_feature_idx"),
        ),
        migrations.AddIndex(
            model_name="planfeature",
            index=models.Index(
                fields=["plan", "sort_order"], name="planfeat_plan_sort_idx"
            ),
        ),
        # 6. OrganizationUsage model (resource usage tracking per organization)
        migrations.CreateModel(
            name="OrganizationUsage",
            fields=[
                (
                    "created_at",
                    models.DateTimeField(
                        auto_now_add=True,
                        help_text="Timestamp when record was created",
                        verbose_name="Created at",
                    ),
                ),
                (
                    "updated_at",
                    models.DateTimeField(
                        auto_now=True,
                        help_text="Timestamp when record was last updated",
                        verbose_name="Updated at",
                    ),
                ),
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        help_text="Unique identifier (UUID)",
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "current_usage",
                    models.PositiveIntegerField(
                        default=0,
                        help_text="Current usage count for this period",
                        verbose_name="Current usage",
                    ),
                ),
                (
                    "usage_limit",
                    models.IntegerField(
                        default=-1,
                        help_text="Limit from plan (-1 = unlimited)",
                        verbose_name="Usage limit",
                    ),
                ),
                (
                    "period_start",
                    models.DateTimeField(
                        blank=True,
                        help_text="Start of current tracking period",
                        null=True,
                        verbose_name="Period start",
                    ),
                ),
                (
                    "period_end",
                    models.DateTimeField(
                        blank=True,
                        db_index=True,
                        help_text="End of current tracking period",
                        null=True,
                        verbose_name="Period end",
                    ),
                ),
                (
                    "last_reset_at",
                    models.DateTimeField(
                        blank=True,
                        help_text="When usage was last reset",
                        null=True,
                        verbose_name="Last reset at",
                    ),
                ),
                (
                    "last_usage_at",
                    models.DateTimeField(
                        blank=True,
                        help_text="When usage was last recorded",
                        null=True,
                        verbose_name="Last usage at",
                    ),
                ),
                (
                    "metadata",
                    models.JSONField(
                        blank=True,
                        default=dict,
                        help_text="Additional usage metadata (e.g., usage breakdown, history)",
                        verbose_name="Metadata",
                    ),
                ),
                (
                    "organization",
                    models.ForeignKey(
                        help_text="Organization this usage belongs to",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="usage_records",
                        to="core.organization",
                        verbose_name="Organization",
                    ),
                ),
                (
                    "feature",
                    models.ForeignKey(
                        help_text="Feature being tracked",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="usage_records",
                        to="subscriptions.feature",
                        verbose_name="Feature",
                    ),
                ),
            ],
            options={
                "verbose_name": "Organization Usage",
                "verbose_name_plural": "Organization Usage",
                "db_table": "organization_usage",
                "ordering": ["-updated_at"],
            },
        ),
        migrations.AddConstraint(
            model_name="organizationusage",
            constraint=models.UniqueConstraint(
                fields=["organization", "feature"], name="orgusage_org_feature_uniq"
            ),
        ),
        migrations.AddIndex(
            model_name="organizationusage",
            index=models.Index(
                fields=["organization", "feature"], name="orgusage_org_feat_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="organizationusage",
            index=models.Index(
                fields=["organization", "period_end"], name="orgusage_org_period_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="organizationusage",
            index=models.Index(
                fields=["feature", "period_end"], name="orgusage_feat_period_idx"
            ),
        ),
    ]
