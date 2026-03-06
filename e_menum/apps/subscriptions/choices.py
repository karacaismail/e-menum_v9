"""
Django TextChoices enums for subscriptions module.

These enums define the valid values for status fields and other constrained
string fields across the subscriptions domain models (Plan, Subscription, Invoice, etc.).

Usage:
    from apps.subscriptions.choices import SubscriptionStatus, InvoiceStatus

    class Subscription(models.Model):
        status = models.CharField(
            max_length=20,
            choices=SubscriptionStatus.choices,
            default=SubscriptionStatus.TRIALING
        )
"""

from django.db import models


class SubscriptionStatus(models.TextChoices):
    """
    Status values for Subscription lifecycle.

    Subscriptions follow this state machine:

    States:
    - TRIALING: Initial 14-day trial period (free access to paid features)
    - ACTIVE: Paid and active subscription
    - PAST_DUE: Payment failed, 7-day grace period before downgrade
    - CANCELLED: User cancelled, access continues until period end
    - EXPIRED: Period ended, downgraded to Free tier
    - SUSPENDED: Admin action, access blocked immediately

    Transitions:
    - (new) → TRIALING: Organization created
    - TRIALING → ACTIVE: First payment success
    - TRIALING → EXPIRED: Trial ends without payment
    - ACTIVE → ACTIVE: Renewal success
    - ACTIVE → PAST_DUE: Payment failed
    - ACTIVE → CANCELLED: User cancels
    - PAST_DUE → ACTIVE: Payment recovered
    - PAST_DUE → EXPIRED: Grace period ends
    - CANCELLED → EXPIRED: Billing period ends
    - CANCELLED → ACTIVE: User resubscribes
    - EXPIRED → ACTIVE: User resubscribes
    - ANY → SUSPENDED: Admin action
    - SUSPENDED → ACTIVE: Admin resolves
    """
    TRIALING = 'TRIALING', 'Trialing'
    ACTIVE = 'ACTIVE', 'Active'
    PAST_DUE = 'PAST_DUE', 'Past Due'
    CANCELLED = 'CANCELLED', 'Cancelled'
    EXPIRED = 'EXPIRED', 'Expired'
    SUSPENDED = 'SUSPENDED', 'Suspended'


class InvoiceStatus(models.TextChoices):
    """
    Status values for Invoice lifecycle.

    Invoices follow this workflow:
    DRAFT → PENDING → PAID (or VOID/REFUNDED)

    - DRAFT: Invoice being prepared, not yet finalized
    - PENDING: Invoice finalized and sent, awaiting payment
    - PAID: Payment received and confirmed
    - VOID: Invoice cancelled/voided (e.g., duplicate, error)
    - REFUNDED: Invoice paid but subsequently refunded
    - UNCOLLECTIBLE: Invoice unpayable (e.g., bad debt, dispute)
    """
    DRAFT = 'DRAFT', 'Draft'
    PENDING = 'PENDING', 'Pending'
    PAID = 'PAID', 'Paid'
    VOID = 'VOID', 'Void'
    REFUNDED = 'REFUNDED', 'Refunded'
    UNCOLLECTIBLE = 'UNCOLLECTIBLE', 'Uncollectible'


class SubscriptionPaymentMethod(models.TextChoices):
    """
    Payment method types for subscription billing.

    These are different from order payment methods as they represent
    recurring payment methods for subscription billing.

    - CREDIT_CARD: Credit/debit card (most common for subscriptions)
    - BANK_TRANSFER: Bank transfer (EFT/Wire)
    - IYZICO: Iyzico payment gateway (Turkey's leading payment provider)
    - OTHER: Other payment methods
    """
    CREDIT_CARD = 'CREDIT_CARD', 'Credit Card'
    BANK_TRANSFER = 'BANK_TRANSFER', 'Bank Transfer'
    IYZICO = 'IYZICO', 'Iyzico'
    OTHER = 'OTHER', 'Other'


class BillingPeriod(models.TextChoices):
    """
    Billing period options for subscriptions.

    - MONTHLY: Billed every month
    - YEARLY: Billed annually (typically with discount)
    """
    MONTHLY = 'MONTHLY', 'Monthly'
    YEARLY = 'YEARLY', 'Yearly'


class PlanTier(models.TextChoices):
    """
    Plan tier definitions for E-Menum subscription plans.

    Tiers define feature access levels:
    - FREE: Basic features, limited usage (always available)
    - STARTER: Small businesses, essential features (₺2K/ay)
    - GROWTH: Growing businesses, more features (₺4.5K/ay)
    - PROFESSIONAL: Full features, priority support (₺8.5K/ay)
    - BUSINESS: Multi-branch, white-label (₺15K/ay)
    - ENTERPRISE: Custom features, dedicated support (özel fiyat)
    """
    FREE = 'FREE', 'Free'
    STARTER = 'STARTER', 'Starter'
    GROWTH = 'GROWTH', 'Growth'
    PROFESSIONAL = 'PROFESSIONAL', 'Professional'
    BUSINESS = 'BUSINESS', 'Business'
    ENTERPRISE = 'ENTERPRISE', 'Enterprise'


class FeatureCategoryType(models.TextChoices):
    """
    Category types for grouping features in comparison tables.

    Used by the Feature model's category field to provide
    display-friendly group headers on the pricing page.
    """
    MENUS = 'menus', 'Menü & Ürün Yönetimi'
    ORDERS = 'orders', 'Sipariş & Ödeme'
    ANALYTICS = 'analytics', 'Analitik & Raporlama'
    SUPPORT = 'support', 'Destek & Entegrasyon'
    AI = 'ai', 'Yapay Zeka'
    BRANDING = 'branding', 'Marka & Tasarım'
    INTEGRATIONS = 'integrations', 'Entegrasyonlar'
    GENERAL = 'general', 'Genel'


class PlanCardStyle(models.TextChoices):
    """CSS class styles for pricing card appearance."""
    FREE = 'free', 'Free (Slate)'
    STARTER = 'start', 'Starter (Sky Blue)'
    GROWTH = 'grow', 'Growth (Emerald)'
    PROFESSIONAL = 'pro', 'Professional (Accent/Teal)'
    BUSINESS = 'biz', 'Business (Purple)'
    ENTERPRISE = 'ent', 'Enterprise (Gold)'


class PlanCtaStyle(models.TextChoices):
    """CTA button style choices for pricing cards."""
    OUTLINE = 'cta-out', 'Outline'
    PRIMARY = 'cta-prim', 'Primary (Filled)'
    ENTERPRISE = 'cta-ent', 'Enterprise (Gold)'


class PlanRibbonColor(models.TextChoices):
    """Ribbon/highlight color choices for pricing cards."""
    NONE = '', 'Yok'
    TEAL = 'teal', 'Teal (Accent)'
    GOLD = 'gold', 'Gold'
    PURPLE = 'purple', 'Purple'


class FeatureType(models.TextChoices):
    """
    Feature type categorization for plan features.

    - BOOLEAN: Feature is either enabled or disabled
    - LIMIT: Feature has a numeric limit (e.g., max products)
    - USAGE: Feature is metered by usage (e.g., AI generations)
    """
    BOOLEAN = 'BOOLEAN', 'Boolean'
    LIMIT = 'LIMIT', 'Limit'
    USAGE = 'USAGE', 'Usage'
