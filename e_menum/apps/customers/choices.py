"""
Django TextChoices enums for customers module.

These enums define the valid values for status fields and other constrained
string fields across the customers domain models (Customer, Feedback, LoyaltyPoint, etc.).

Usage:
    from apps.customers.choices import FeedbackType, FeedbackStatus

    class Feedback(models.Model):
        feedback_type = models.CharField(
            max_length=20,
            choices=FeedbackType.choices,
            default=FeedbackType.GENERAL
        )
"""

from django.db import models


class FeedbackType(models.TextChoices):
    """
    Type values for customer feedback.

    - GENERAL: General feedback about the establishment
    - SERVICE: Feedback about service quality
    - FOOD: Feedback about food quality
    - AMBIANCE: Feedback about ambiance/atmosphere
    - CLEANLINESS: Feedback about cleanliness
    - VALUE: Feedback about value for money
    - OTHER: Other type of feedback
    """
    GENERAL = 'GENERAL', 'General'
    SERVICE = 'SERVICE', 'Service'
    FOOD = 'FOOD', 'Food'
    AMBIANCE = 'AMBIANCE', 'Ambiance'
    CLEANLINESS = 'CLEANLINESS', 'Cleanliness'
    VALUE = 'VALUE', 'Value'
    OTHER = 'OTHER', 'Other'


class FeedbackStatus(models.TextChoices):
    """
    Status values for feedback processing.

    - PENDING: Feedback submitted, awaiting review
    - REVIEWED: Feedback has been reviewed by staff
    - RESPONDED: Staff has responded to the feedback
    - ARCHIVED: Feedback is archived (no further action)
    """
    PENDING = 'PENDING', 'Pending'
    REVIEWED = 'REVIEWED', 'Reviewed'
    RESPONDED = 'RESPONDED', 'Responded'
    ARCHIVED = 'ARCHIVED', 'Archived'


class LoyaltyPointType(models.TextChoices):
    """
    Type values for loyalty point transactions.

    - EARNED: Points earned from purchases
    - REDEEMED: Points redeemed for rewards
    - BONUS: Bonus points from promotions
    - EXPIRED: Points that have expired
    - ADJUSTMENT: Manual adjustment by staff
    - REFERRAL: Points from referral program
    """
    EARNED = 'EARNED', 'Earned'
    REDEEMED = 'REDEEMED', 'Redeemed'
    BONUS = 'BONUS', 'Bonus'
    EXPIRED = 'EXPIRED', 'Expired'
    ADJUSTMENT = 'ADJUSTMENT', 'Adjustment'
    REFERRAL = 'REFERRAL', 'Referral'


class CustomerSource(models.TextChoices):
    """
    Source of customer acquisition.

    - QR_SCAN: Customer registered via QR code scan
    - WEB: Customer registered via website
    - APP: Customer registered via mobile app
    - STAFF: Customer added manually by staff
    - IMPORT: Customer imported from external system
    - REFERRAL: Customer referred by another customer
    """
    QR_SCAN = 'QR_SCAN', 'QR Scan'
    WEB = 'WEB', 'Website'
    APP = 'APP', 'Mobile App'
    STAFF = 'STAFF', 'Staff Entry'
    IMPORT = 'IMPORT', 'Import'
    REFERRAL = 'REFERRAL', 'Referral'


class VisitSource(models.TextChoices):
    """
    Source of customer visit tracking.

    - QR_SCAN: Visit initiated via QR code scan
    - ORDER: Visit recorded from placing an order
    - CHECK_IN: Manual check-in by customer
    - STAFF: Staff recorded the visit
    """
    QR_SCAN = 'QR_SCAN', 'QR Scan'
    ORDER = 'ORDER', 'Order'
    CHECK_IN = 'CHECK_IN', 'Check-in'
    STAFF = 'STAFF', 'Staff Entry'
