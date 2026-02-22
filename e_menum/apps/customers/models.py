"""
Django ORM models for the Customers application.

This module defines the customer-related models for E-Menum:
- Customer: End customers with profiles and contact information
- CustomerVisit: Visit tracking for analytics and loyalty
- Feedback: Customer feedback with ratings and comments
- LoyaltyPoint: Points ledger for loyalty programs

Critical Rules:
- Every query MUST include organization_id for tenant isolation
- All entities use soft delete (deleted_at timestamp) except LoyaltyPoint
- No physical deletions allowed (use soft_delete method)
- LoyaltyPoint records are append-only for transaction integrity
"""

import uuid

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.core.models import (
    Branch,
    Organization,
    SoftDeleteManager,
    SoftDeleteMixin,
    TimeStampedMixin,
)
from apps.customers.choices import (
    CustomerSource,
    FeedbackStatus,
    FeedbackType,
    LoyaltyPointType,
    NPSCategory,
    NPSChannel,
    PreferenceType,
    VisitSource,
)


class Customer(TimeStampedMixin, SoftDeleteMixin, models.Model):
    """
    Customer model - represents end customers who view menus and place orders.

    Customers are people who interact with the restaurant through the E-Menum
    platform. They can be anonymous (just viewing menus) or registered with
    contact information for loyalty programs and order history.

    Critical Rules:
    - EVERY query MUST filter by organization (multi-tenant isolation)
    - Use soft_delete() - never call delete() directly
    - Email is unique within an organization (not globally)

    Attributes:
        id: UUID primary key (ensures global uniqueness)
        organization: FK to parent Organization (tenant isolation)
        name: Customer's display name
        email: Customer's email address (unique per organization)
        phone: Customer's phone number
        avatar: URL to customer's profile image
        language_preference: Preferred language code (e.g., 'tr', 'en')
        source: How the customer was acquired (QR scan, web, app, etc.)
        notes: Staff notes about the customer
        settings: JSON field for customer preferences
        total_orders: Denormalized order count for quick access
        total_spent: Denormalized total spending for quick access
        loyalty_points_balance: Current loyalty points balance
        first_visit_at: Date of first visit/order
        last_visit_at: Date of most recent visit/order
        marketing_consent: Whether customer consented to marketing
        marketing_consent_at: When marketing consent was given

    Usage:
        # Create a customer
        customer = Customer.objects.create(
            organization=org,
            name="Ahmet Yilmaz",
            email="ahmet@example.com",
            phone="+905551234567",
            source=CustomerSource.QR_SCAN
        )

        # Query customers for organization (ALWAYS filter by organization!)
        customers = Customer.objects.filter(organization=org)

        # Get VIP customers (high spenders)
        vip_customers = Customer.objects.filter(
            organization=org,
            total_spent__gte=10000
        )

        # Soft delete customer (NEVER use delete())
        customer.soft_delete()
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name=_('ID'),
        help_text=_('Unique identifier (UUID)')
    )

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='customers',
        verbose_name=_('Organization'),
        help_text=_('Organization this customer belongs to')
    )

    # Identity
    name = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name=_('Name'),
        help_text=_("Customer's display name")
    )

    email = models.EmailField(
        blank=True,
        null=True,
        verbose_name=_('Email'),
        help_text=_("Customer's email address (unique per organization)")
    )

    phone = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name=_('Phone'),
        help_text=_("Customer's phone number")
    )

    avatar = models.URLField(
        blank=True,
        null=True,
        max_length=500,
        verbose_name=_('Avatar URL'),
        help_text=_("URL to customer's profile image")
    )

    # Preferences
    language_preference = models.CharField(
        max_length=10,
        default='tr',
        verbose_name=_('Language preference'),
        help_text=_("Preferred language code (e.g., 'tr', 'en')")
    )

    # Acquisition
    source = models.CharField(
        max_length=20,
        choices=CustomerSource.choices,
        default=CustomerSource.QR_SCAN,
        verbose_name=_('Source'),
        help_text=_('How the customer was acquired')
    )

    # Staff notes
    notes = models.TextField(
        blank=True,
        null=True,
        verbose_name=_('Notes'),
        help_text=_('Staff notes about the customer')
    )

    # Preferences (JSON)
    settings = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_('Settings'),
        help_text=_('Customer preferences and settings (JSON)')
    )

    # Denormalized counters (updated by triggers/signals)
    total_orders = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Total orders'),
        help_text=_('Total number of orders placed')
    )

    total_spent = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name=_('Total spent'),
        help_text=_('Total amount spent (denormalized)')
    )

    loyalty_points_balance = models.IntegerField(
        default=0,
        verbose_name=_('Loyalty points balance'),
        help_text=_('Current loyalty points balance')
    )

    # Visit tracking
    first_visit_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name=_('First visit at'),
        help_text=_('Date and time of first visit')
    )

    last_visit_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name=_('Last visit at'),
        help_text=_('Date and time of most recent visit')
    )

    # Marketing consent
    marketing_consent = models.BooleanField(
        default=False,
        verbose_name=_('Marketing consent'),
        help_text=_('Whether customer consented to receive marketing communications')
    )

    marketing_consent_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name=_('Marketing consent at'),
        help_text=_('When marketing consent was given')
    )

    # RFM Segmentation fields
    rfm_segment = models.CharField(max_length=50, null=True, blank=True, verbose_name=_('RFM Segment'))
    rfm_recency_score = models.IntegerField(null=True, blank=True, verbose_name=_('RFM Recency Score'))
    rfm_frequency_score = models.IntegerField(null=True, blank=True, verbose_name=_('RFM Frequency Score'))
    rfm_monetary_score = models.IntegerField(null=True, blank=True, verbose_name=_('RFM Monetary Score'))
    lifetime_value = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, verbose_name=_('Lifetime Value'))
    churn_risk_score = models.DecimalField(max_digits=5, decimal_places=4, null=True, blank=True, verbose_name=_('Churn Risk Score'))
    last_visit_date = models.DateField(null=True, blank=True, verbose_name=_('Last Visit Date'))

    # Managers
    objects = SoftDeleteManager()  # Default: excludes soft-deleted
    all_objects = models.Manager()  # Includes ALL records

    class Meta:
        db_table = 'customers'
        verbose_name = _('Customer')
        verbose_name_plural = _('Customers')
        ordering = ['-created_at']
        # Email should be unique within an organization
        unique_together = [['organization', 'email']]
        indexes = [
            models.Index(fields=['organization', 'deleted_at'], name='customer_org_deleted_idx'),
            models.Index(fields=['organization', 'email'], name='customer_org_email_idx'),
            models.Index(fields=['organization', 'phone'], name='customer_org_phone_idx'),
            models.Index(fields=['organization', 'last_visit_at'], name='customer_org_lastvisit_idx'),
            models.Index(fields=['organization', 'total_spent'], name='customer_org_spent_idx'),
        ]

    def __str__(self) -> str:
        if self.name:
            return f"{self.name} ({self.organization.name})"
        if self.email:
            return f"{self.email} ({self.organization.name})"
        return f"Customer {self.id} ({self.organization.name})"

    def __repr__(self) -> str:
        return f"<Customer(id={self.id}, name='{self.name}', org='{self.organization.name}')>"

    @property
    def display_name(self) -> str:
        """Return the best available display name for the customer."""
        if self.name:
            return self.name
        if self.email:
            return self.email.split('@')[0]
        return f"Customer {str(self.id)[:8]}"

    @property
    def is_returning_customer(self) -> bool:
        """Check if customer has made more than one order."""
        return self.total_orders > 1

    @property
    def average_order_value(self):
        """Calculate average order value."""
        if self.total_orders == 0:
            return 0
        return self.total_spent / self.total_orders

    def record_visit(self) -> None:
        """Record a customer visit, updating first/last visit timestamps."""
        now = timezone.now()
        if self.first_visit_at is None:
            self.first_visit_at = now
        self.last_visit_at = now
        self.save(update_fields=['first_visit_at', 'last_visit_at', 'updated_at'])

    def add_loyalty_points(self, points: int, reason: str = None) -> None:
        """
        Add loyalty points to customer's balance.

        Args:
            points: Number of points to add (can be negative for deductions)
            reason: Optional reason for the adjustment
        """
        self.loyalty_points_balance += points
        self.save(update_fields=['loyalty_points_balance', 'updated_at'])

    def grant_marketing_consent(self) -> None:
        """Record that customer has granted marketing consent."""
        self.marketing_consent = True
        self.marketing_consent_at = timezone.now()
        self.save(update_fields=['marketing_consent', 'marketing_consent_at', 'updated_at'])

    def revoke_marketing_consent(self) -> None:
        """Record that customer has revoked marketing consent."""
        self.marketing_consent = False
        self.save(update_fields=['marketing_consent', 'updated_at'])

    def get_setting(self, key: str, default=None):
        """Get a value from customer settings."""
        return self.settings.get(key, default)

    def set_setting(self, key: str, value) -> None:
        """Set a value in customer settings."""
        self.settings[key] = value
        self.save(update_fields=['settings', 'updated_at'])


class CustomerVisit(TimeStampedMixin, models.Model):
    """
    CustomerVisit model - tracks individual customer visits for analytics.

    Each visit record captures when a customer interacted with the restaurant,
    whether through a QR scan, placing an order, or manual check-in. This data
    is used for analytics, loyalty programs, and personalization.

    Attributes:
        id: UUID primary key
        organization: FK to Organization (tenant isolation)
        customer: FK to Customer
        branch: Optional FK to Branch for multi-location tracking
        visited_at: When the visit occurred
        source: How the visit was recorded (QR scan, order, check-in)
        table: Optional FK to Table where customer was seated
        order: Optional FK to Order if visit resulted in an order
        device_info: JSON field with device/browser information
        ip_address: Client IP address
        user_agent: Client user agent string
        duration_minutes: How long the customer stayed (if known)

    Usage:
        # Record a visit
        visit = CustomerVisit.objects.create(
            organization=org,
            customer=customer,
            branch=branch,
            source=VisitSource.QR_SCAN,
            device_info={'os': 'iOS', 'browser': 'Safari'}
        )

        # Get visits for a customer
        visits = CustomerVisit.objects.filter(
            organization=org,
            customer=customer
        ).order_by('-visited_at')

        # Count visits this month
        this_month_visits = CustomerVisit.objects.filter(
            organization=org,
            visited_at__month=timezone.now().month
        ).count()

    Notes:
        - Visit records are NOT soft-deleted (append-only for analytics)
        - This model does NOT use SoftDeleteMixin intentionally
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name=_('ID'),
        help_text=_('Unique identifier (UUID)')
    )

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='customer_visits',
        verbose_name=_('Organization'),
        help_text=_('Organization this visit belongs to')
    )

    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        related_name='visits',
        verbose_name=_('Customer'),
        help_text=_('Customer who made this visit')
    )

    branch = models.ForeignKey(
        Branch,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='customer_visits',
        verbose_name=_('Branch'),
        help_text=_('Branch where the visit occurred')
    )

    visited_at = models.DateTimeField(
        default=timezone.now,
        db_index=True,
        verbose_name=_('Visited at'),
        help_text=_('When the visit occurred')
    )

    source = models.CharField(
        max_length=20,
        choices=VisitSource.choices,
        default=VisitSource.QR_SCAN,
        verbose_name=_('Source'),
        help_text=_('How the visit was recorded')
    )

    # Optional references to related entities
    # Note: These are string references to avoid circular imports
    # They will be resolved when the models are available
    table_id = models.UUIDField(
        null=True,
        blank=True,
        verbose_name=_('Table ID'),
        help_text=_('Table where customer was seated (if applicable)')
    )

    order_id = models.UUIDField(
        null=True,
        blank=True,
        verbose_name=_('Order ID'),
        help_text=_('Order placed during this visit (if applicable)')
    )

    # Device/Session information
    device_info = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_('Device info'),
        help_text=_('Device and browser information (JSON)')
    )

    ip_address = models.GenericIPAddressField(
        blank=True,
        null=True,
        verbose_name=_('IP address'),
        help_text=_('Client IP address')
    )

    user_agent = models.TextField(
        blank=True,
        null=True,
        verbose_name=_('User agent'),
        help_text=_('Client user agent string')
    )

    # Duration tracking
    duration_minutes = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name=_('Duration (minutes)'),
        help_text=_('How long the customer stayed (estimated)')
    )

    class Meta:
        db_table = 'customer_visits'
        verbose_name = _('Customer Visit')
        verbose_name_plural = _('Customer Visits')
        ordering = ['-visited_at']
        indexes = [
            models.Index(fields=['organization', 'visited_at'], name='visit_org_date_idx'),
            models.Index(fields=['customer', 'visited_at'], name='visit_customer_date_idx'),
            models.Index(fields=['organization', 'branch', 'visited_at'], name='visit_org_branch_idx'),
            models.Index(fields=['organization', 'source'], name='visit_org_source_idx'),
        ]

    def __str__(self) -> str:
        return f"Visit by {self.customer.display_name} on {self.visited_at.date()}"

    def __repr__(self) -> str:
        return f"<CustomerVisit(id={self.id}, customer='{self.customer.display_name}', date={self.visited_at.date()})>"


class Feedback(TimeStampedMixin, SoftDeleteMixin, models.Model):
    """
    Feedback model - captures customer feedback and ratings.

    Feedback can be associated with a specific order or be general feedback
    about the establishment. It includes ratings, comments, and status tracking
    for staff follow-up.

    Critical Rules:
    - EVERY query MUST filter by organization (multi-tenant isolation)
    - Use soft_delete() - never call delete() directly
    - Customer reference is optional (anonymous feedback allowed)

    Attributes:
        id: UUID primary key
        organization: FK to Organization (tenant isolation)
        customer: Optional FK to Customer (can be anonymous)
        order: Optional FK to Order (if feedback is about specific order)
        feedback_type: Type of feedback (service, food, general, etc.)
        rating: Overall rating (1-5 scale)
        comment: Free-text feedback comment
        status: Processing status (pending, reviewed, responded, archived)
        staff_response: Staff response to the feedback
        responded_by: User who responded
        responded_at: When the response was made
        is_public: Whether feedback can be shown publicly
        metadata: Additional metadata (JSON)

    Usage:
        # Create feedback for an order
        feedback = Feedback.objects.create(
            organization=org,
            customer=customer,
            order=order,
            feedback_type=FeedbackType.FOOD,
            rating=5,
            comment="Delicious food, great service!"
        )

        # Get pending feedback
        pending = Feedback.objects.filter(
            organization=org,
            status=FeedbackStatus.PENDING
        )

        # Get average rating
        avg_rating = Feedback.objects.filter(
            organization=org,
            deleted_at__isnull=True
        ).aggregate(Avg('rating'))['rating__avg']
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name=_('ID'),
        help_text=_('Unique identifier (UUID)')
    )

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='feedbacks',
        verbose_name=_('Organization'),
        help_text=_('Organization this feedback belongs to')
    )

    customer = models.ForeignKey(
        Customer,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='feedbacks',
        verbose_name=_('Customer'),
        help_text=_('Customer who gave this feedback (null for anonymous)')
    )

    # Order reference (string FK to avoid circular import)
    order_id = models.UUIDField(
        null=True,
        blank=True,
        verbose_name=_('Order ID'),
        help_text=_('Order this feedback is about (if applicable)')
    )

    # Feedback content
    feedback_type = models.CharField(
        max_length=20,
        choices=FeedbackType.choices,
        default=FeedbackType.GENERAL,
        verbose_name=_('Feedback type'),
        help_text=_('Category of feedback')
    )

    rating = models.PositiveSmallIntegerField(
        verbose_name=_('Rating'),
        help_text=_('Rating on a 1-5 scale')
    )

    comment = models.TextField(
        blank=True,
        null=True,
        verbose_name=_('Comment'),
        help_text=_('Customer feedback comment')
    )

    # Status and response
    status = models.CharField(
        max_length=20,
        choices=FeedbackStatus.choices,
        default=FeedbackStatus.PENDING,
        db_index=True,
        verbose_name=_('Status'),
        help_text=_('Processing status of the feedback')
    )

    staff_response = models.TextField(
        blank=True,
        null=True,
        verbose_name=_('Staff response'),
        help_text=_('Response from staff to the feedback')
    )

    responded_by_id = models.UUIDField(
        null=True,
        blank=True,
        verbose_name=_('Responded by'),
        help_text=_('User who responded to this feedback')
    )

    responded_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Responded at'),
        help_text=_('When the response was made')
    )

    # Visibility
    is_public = models.BooleanField(
        default=False,
        verbose_name=_('Is public'),
        help_text=_('Whether this feedback can be shown publicly')
    )

    # Additional data
    metadata = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_('Metadata'),
        help_text=_('Additional metadata (JSON)')
    )

    # Managers
    objects = SoftDeleteManager()  # Default: excludes soft-deleted
    all_objects = models.Manager()  # Includes ALL records

    class Meta:
        db_table = 'feedbacks'
        verbose_name = _('Feedback')
        verbose_name_plural = _('Feedbacks')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['organization', 'status'], name='feedback_org_status_idx'),
            models.Index(fields=['organization', 'deleted_at'], name='feedback_org_deleted_idx'),
            models.Index(fields=['organization', 'rating'], name='feedback_org_rating_idx'),
            models.Index(fields=['customer', 'created_at'], name='feedback_customer_idx'),
            models.Index(fields=['organization', 'feedback_type'], name='feedback_org_type_idx'),
        ]

    def __str__(self) -> str:
        customer_name = self.customer.display_name if self.customer else 'Anonymous'
        return f"Feedback from {customer_name} - {self.rating}/5"

    def __repr__(self) -> str:
        return f"<Feedback(id={self.id}, rating={self.rating}, status={self.status})>"

    @property
    def is_positive(self) -> bool:
        """Check if this is positive feedback (4-5 stars)."""
        return self.rating >= 4

    @property
    def is_negative(self) -> bool:
        """Check if this is negative feedback (1-2 stars)."""
        return self.rating <= 2

    @property
    def has_response(self) -> bool:
        """Check if staff has responded to this feedback."""
        return self.staff_response is not None and len(self.staff_response) > 0

    def respond(self, response: str, user_id: str) -> None:
        """
        Add a staff response to this feedback.

        Args:
            response: The response text
            user_id: ID of the user responding
        """
        self.staff_response = response
        self.responded_by_id = user_id
        self.responded_at = timezone.now()
        self.status = FeedbackStatus.RESPONDED
        self.save(update_fields=[
            'staff_response', 'responded_by_id', 'responded_at',
            'status', 'updated_at'
        ])

    def mark_reviewed(self) -> None:
        """Mark this feedback as reviewed."""
        self.status = FeedbackStatus.REVIEWED
        self.save(update_fields=['status', 'updated_at'])

    def archive(self) -> None:
        """Archive this feedback."""
        self.status = FeedbackStatus.ARCHIVED
        self.save(update_fields=['status', 'updated_at'])

    def make_public(self) -> None:
        """Make this feedback visible to the public."""
        self.is_public = True
        self.save(update_fields=['is_public', 'updated_at'])

    def make_private(self) -> None:
        """Hide this feedback from public view."""
        self.is_public = False
        self.save(update_fields=['is_public', 'updated_at'])


class LoyaltyPoint(TimeStampedMixin, models.Model):
    """
    LoyaltyPoint model - tracks loyalty point transactions.

    This is a ledger-style model where each record represents a transaction
    (points earned, redeemed, expired, etc.). The customer's current balance
    is calculated from the sum of all transactions (or cached in Customer model).

    Attributes:
        id: UUID primary key
        organization: FK to Organization (tenant isolation)
        customer: FK to Customer
        transaction_type: Type of transaction (earned, redeemed, bonus, etc.)
        points: Number of points (positive for credit, negative for debit)
        balance_after: Customer's balance after this transaction
        order: Optional FK to Order (if points from/for an order)
        description: Human-readable description of the transaction
        expires_at: When these points expire (if applicable)
        metadata: Additional transaction data (JSON)

    Usage:
        # Record earned points
        transaction = LoyaltyPoint.objects.create(
            organization=org,
            customer=customer,
            transaction_type=LoyaltyPointType.EARNED,
            points=100,
            balance_after=customer.loyalty_points_balance + 100,
            order_id=order.id,
            description="Points earned from order #12345"
        )

        # Redeem points
        redemption = LoyaltyPoint.objects.create(
            organization=org,
            customer=customer,
            transaction_type=LoyaltyPointType.REDEEMED,
            points=-500,  # Negative for redemption
            balance_after=customer.loyalty_points_balance - 500,
            description="Redeemed for free coffee"
        )

        # Get transaction history
        history = LoyaltyPoint.objects.filter(
            customer=customer
        ).order_by('-created_at')

    Notes:
        - LoyaltyPoint records are NEVER deleted (append-only ledger)
        - This model does NOT use SoftDeleteMixin intentionally
        - Points can be negative (for redemptions/expirations)
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name=_('ID'),
        help_text=_('Unique identifier (UUID)')
    )

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='loyalty_points',
        verbose_name=_('Organization'),
        help_text=_('Organization this transaction belongs to')
    )

    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        related_name='loyalty_transactions',
        verbose_name=_('Customer'),
        help_text=_('Customer this transaction is for')
    )

    # Transaction details
    transaction_type = models.CharField(
        max_length=20,
        choices=LoyaltyPointType.choices,
        verbose_name=_('Transaction type'),
        help_text=_('Type of loyalty point transaction')
    )

    points = models.IntegerField(
        verbose_name=_('Points'),
        help_text=_('Number of points (positive for credit, negative for debit)')
    )

    balance_after = models.IntegerField(
        verbose_name=_('Balance after'),
        help_text=_("Customer's points balance after this transaction")
    )

    # Related order (string FK to avoid circular import)
    order_id = models.UUIDField(
        null=True,
        blank=True,
        verbose_name=_('Order ID'),
        help_text=_('Order associated with this transaction (if applicable)')
    )

    # Description
    description = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name=_('Description'),
        help_text=_('Human-readable description of the transaction')
    )

    # Expiration (for earned points)
    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Expires at'),
        help_text=_('When these points expire (null = never)')
    )

    # Additional data
    metadata = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_('Metadata'),
        help_text=_('Additional transaction data (JSON)')
    )

    class Meta:
        db_table = 'loyalty_points'
        verbose_name = _('Loyalty Point')
        verbose_name_plural = _('Loyalty Points')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['organization', 'customer'], name='loyalty_org_customer_idx'),
            models.Index(fields=['customer', 'created_at'], name='loyalty_customer_date_idx'),
            models.Index(fields=['organization', 'transaction_type'], name='loyalty_org_type_idx'),
            models.Index(fields=['expires_at'], name='loyalty_expires_idx'),
        ]

    def __str__(self) -> str:
        sign = '+' if self.points > 0 else ''
        return f"{sign}{self.points} points for {self.customer.display_name}"

    def __repr__(self) -> str:
        return f"<LoyaltyPoint(id={self.id}, type={self.transaction_type}, points={self.points})>"

    @property
    def is_credit(self) -> bool:
        """Check if this is a credit transaction (points added)."""
        return self.points > 0

    @property
    def is_debit(self) -> bool:
        """Check if this is a debit transaction (points removed)."""
        return self.points < 0

    @property
    def is_expired(self) -> bool:
        """Check if these points have expired."""
        if self.expires_at is None:
            return False
        return timezone.now() > self.expires_at

    @property
    def absolute_points(self) -> int:
        """Return the absolute value of points."""
        return abs(self.points)


class CustomerPreference(TimeStampedMixin, SoftDeleteMixin, models.Model):
    """
    CustomerPreference model - stores individual customer preferences.

    Preferences can be manually set or auto-detected by the system.
    Each preference has a type, key, and value (e.g., type=DIETARY, key='vegetarian', value='true').

    Critical Rules:
    - EVERY query MUST filter by organization (multi-tenant isolation)
    - Use soft_delete() - never call delete() directly

    Attributes:
        id: UUID primary key
        organization: FK to Organization (tenant isolation)
        customer: FK to Customer
        preference_type: Category of preference (DIETARY, ALLERGEN, SEATING, etc.)
        key: Preference key identifier (e.g., 'vegetarian', 'window_seat')
        value: Preference value (e.g., 'true', 'always')
        auto_detected: Whether this preference was automatically detected
        confidence: Confidence score for auto-detected preferences (0-1)
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name=_('ID'),
        help_text=_('Unique identifier (UUID)')
    )

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='customer_preferences',
        verbose_name=_('Organization'),
        help_text=_('Organization this preference belongs to')
    )

    customer = models.ForeignKey(
        'Customer',
        on_delete=models.CASCADE,
        related_name='preferences',
        verbose_name=_('Customer'),
        help_text=_('Customer this preference belongs to')
    )

    preference_type = models.CharField(
        max_length=20,
        choices=PreferenceType.choices,
        verbose_name=_('Preference type'),
        help_text=_('Category of preference')
    )

    key = models.CharField(
        max_length=100,
        verbose_name=_('Key'),
        help_text=_("Preference key identifier (e.g., 'vegetarian', 'window_seat')")
    )

    value = models.CharField(
        max_length=255,
        verbose_name=_('Value'),
        help_text=_("Preference value (e.g., 'true', 'always')")
    )

    auto_detected = models.BooleanField(
        default=False,
        verbose_name=_('Auto detected'),
        help_text=_('Whether this preference was automatically detected')
    )

    confidence = models.DecimalField(
        max_digits=5,
        decimal_places=4,
        null=True,
        blank=True,
        verbose_name=_('Confidence'),
        help_text=_('Confidence score for auto-detected preferences (0-1)')
    )

    # Managers
    objects = SoftDeleteManager()  # Default: excludes soft-deleted
    all_objects = models.Manager()  # Includes ALL records

    class Meta:
        db_table = 'customer_preferences'
        verbose_name = _('Customer Preference')
        verbose_name_plural = _('Customer Preferences')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['organization', 'deleted_at'], name='custpref_org_deleted_idx'),
        ]

    def __str__(self) -> str:
        return f"{self.customer.display_name} - {self.preference_type}: {self.key}={self.value}"

    def __repr__(self) -> str:
        return f"<CustomerPreference(id={self.id}, type='{self.preference_type}', key='{self.key}')>"


class NPSSurvey(TimeStampedMixin, models.Model):
    """
    NPSSurvey model - captures Net Promoter Score survey responses.

    NPS surveys are immutable once submitted. The category (Promoter, Passive,
    Detractor) is auto-calculated based on the score:
    - 9-10: Promoter
    - 7-8: Passive
    - 0-6: Detractor

    Critical Rules:
    - EVERY query MUST filter by organization (multi-tenant isolation)
    - Survey data is immutable - NO soft delete, NO updates
    - Category is auto-calculated from score

    Attributes:
        id: UUID primary key
        organization: FK to Organization (tenant isolation)
        customer: Optional FK to Customer (can be anonymous)
        order_id: Optional UUID reference to Order (not FK to avoid circular)
        score: NPS score (0-10)
        comment: Optional free-text comment
        category: Auto-calculated NPS category (PROMOTER, PASSIVE, DETRACTOR)
        channel: Channel through which survey was collected
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name=_('ID'),
        help_text=_('Unique identifier (UUID)')
    )

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='nps_surveys',
        verbose_name=_('Organization'),
        help_text=_('Organization this survey belongs to')
    )

    customer = models.ForeignKey(
        Customer,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='nps_surveys',
        verbose_name=_('Customer'),
        help_text=_('Customer who submitted this survey (null for anonymous)')
    )

    order_id = models.UUIDField(
        null=True,
        blank=True,
        verbose_name=_('Order ID'),
        help_text=_('Order this survey is about (if applicable)')
    )

    score = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(10)],
        verbose_name=_('Score'),
        help_text=_('NPS score (0-10)')
    )

    comment = models.TextField(
        null=True,
        blank=True,
        verbose_name=_('Comment'),
        help_text=_('Optional free-text comment')
    )

    category = models.CharField(
        max_length=20,
        choices=NPSCategory.choices,
        verbose_name=_('Category'),
        help_text=_('NPS category (auto-calculated from score)')
    )

    channel = models.CharField(
        max_length=20,
        choices=NPSChannel.choices,
        verbose_name=_('Channel'),
        help_text=_('Channel through which survey was collected')
    )

    class Meta:
        db_table = 'nps_surveys'
        verbose_name = _('NPS Survey')
        verbose_name_plural = _('NPS Surveys')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['organization', 'created_at'], name='nps_org_created_idx'),
        ]

    def __str__(self) -> str:
        customer_name = self.customer.display_name if self.customer else 'Anonymous'
        return f"NPS {self.score}/10 from {customer_name} ({self.category})"

    def __repr__(self) -> str:
        return f"<NPSSurvey(id={self.id}, score={self.score}, category='{self.category}')>"

    def save(self, *args, **kwargs):
        """Auto-calculate NPS category from score before saving."""
        if self.score >= 9:
            self.category = NPSCategory.PROMOTER
        elif self.score >= 7:
            self.category = NPSCategory.PASSIVE
        else:
            self.category = NPSCategory.DETRACTOR
        super().save(*args, **kwargs)
