"""
Django TextChoices enums for orders module.

These enums define the valid values for status fields and other constrained
string fields across the orders domain models (Zone, Table, QRCode, Order, etc.).

Usage:
    from apps.orders.choices import TableStatus, OrderStatus

    class Table(models.Model):
        status = models.CharField(
            max_length=20,
            choices=TableStatus.choices,
            default=TableStatus.AVAILABLE
        )
"""

from django.db import models
from django.utils.translation import gettext_lazy as _


class TableStatus(models.TextChoices):
    """
    Status values for Table availability.

    - AVAILABLE: Table is free and can be assigned to customers
    - OCCUPIED: Table currently has active customers
    - RESERVED: Table is reserved for a future booking
    """
    AVAILABLE = 'AVAILABLE', 'Available'
    OCCUPIED = 'OCCUPIED', 'Occupied'
    RESERVED = 'RESERVED', 'Reserved'


class QRCodeType(models.TextChoices):
    """
    Type values for QR codes.

    - MENU: QR code links directly to a menu (no table context)
    - TABLE: QR code is associated with a specific table
    - CAMPAIGN: QR code is for marketing/promotional campaigns
    """
    MENU = 'MENU', 'Menu'
    TABLE = 'TABLE', 'Table'
    CAMPAIGN = 'CAMPAIGN', 'Campaign'


class OrderStatus(models.TextChoices):
    """
    Status values for Order lifecycle.

    Orders follow this progression:
    PENDING → CONFIRMED → PREPARING → READY → DELIVERED → COMPLETED

    - PENDING: Order received, awaiting confirmation
    - CONFIRMED: Order confirmed by staff
    - PREPARING: Kitchen/bar is preparing the order
    - READY: Order is ready for pickup/delivery
    - DELIVERED: Order has been delivered to customer
    - COMPLETED: Order is fully completed and paid
    - CANCELLED: Order was cancelled (terminal state)
    """
    PENDING = 'PENDING', 'Pending'
    CONFIRMED = 'CONFIRMED', 'Confirmed'
    PREPARING = 'PREPARING', 'Preparing'
    READY = 'READY', 'Ready'
    DELIVERED = 'DELIVERED', 'Delivered'
    COMPLETED = 'COMPLETED', 'Completed'
    CANCELLED = 'CANCELLED', 'Cancelled'


class OrderType(models.TextChoices):
    """
    Type values for Order fulfillment method.

    - DINE_IN: Customer eats at the restaurant
    - TAKEAWAY: Customer picks up the order
    - DELIVERY: Order is delivered to customer's location
    """
    DINE_IN = 'DINE_IN', 'Dine In'
    TAKEAWAY = 'TAKEAWAY', 'Takeaway'
    DELIVERY = 'DELIVERY', 'Delivery'
    ONLINE = 'ONLINE', _('Online')


class OrderItemStatus(models.TextChoices):
    """
    Status values for individual OrderItem lifecycle.

    Items follow this progression:
    PENDING → PREPARING → READY → DELIVERED

    - PENDING: Item is waiting to be prepared
    - PREPARING: Item is being prepared in kitchen/bar
    - READY: Item is ready to be served
    - DELIVERED: Item has been delivered to customer
    - CANCELLED: Item was cancelled from the order
    """
    PENDING = 'PENDING', 'Pending'
    PREPARING = 'PREPARING', 'Preparing'
    READY = 'READY', 'Ready'
    DELIVERED = 'DELIVERED', 'Delivered'
    CANCELLED = 'CANCELLED', 'Cancelled'


class ServiceRequestType(models.TextChoices):
    """
    Type values for ServiceRequest (waiter calls, etc.).

    - WAITER_CALL: Customer is calling the waiter
    - BILL_REQUEST: Customer is requesting the bill
    - HELP: Customer needs assistance
    - OTHER: Other type of request
    """
    WAITER_CALL = 'WAITER_CALL', 'Waiter Call'
    BILL_REQUEST = 'BILL_REQUEST', 'Bill Request'
    HELP = 'HELP', 'Help'
    OTHER = 'OTHER', 'Other'


class ServiceRequestStatus(models.TextChoices):
    """
    Status values for ServiceRequest lifecycle.

    - PENDING: Request received, not yet acknowledged
    - IN_PROGRESS: Staff is handling the request
    - COMPLETED: Request has been fulfilled
    - CANCELLED: Request was cancelled
    """
    PENDING = 'PENDING', 'Pending'
    IN_PROGRESS = 'IN_PROGRESS', 'In Progress'
    COMPLETED = 'COMPLETED', 'Completed'
    CANCELLED = 'CANCELLED', 'Cancelled'


class PaymentStatus(models.TextChoices):
    """
    Status values for order payment.

    - PENDING: Payment not yet received
    - PARTIAL: Partial payment received
    - PAID: Full payment received
    - REFUNDED: Payment was refunded
    - FAILED: Payment attempt failed
    """
    PENDING = 'PENDING', 'Pending'
    PARTIAL = 'PARTIAL', 'Partial'
    PAID = 'PAID', 'Paid'
    REFUNDED = 'REFUNDED', 'Refunded'
    FAILED = 'FAILED', 'Failed'


class PaymentMethod(models.TextChoices):
    """
    Payment method types for orders.

    - CASH: Cash payment
    - CREDIT_CARD: Credit card payment
    - DEBIT_CARD: Debit card payment
    - ONLINE: Online payment (various gateways)
    - WALLET: Digital wallet payment
    - OTHER: Other payment methods
    """
    CASH = 'CASH', 'Cash'
    CREDIT_CARD = 'CREDIT_CARD', 'Credit Card'
    DEBIT_CARD = 'DEBIT_CARD', 'Debit Card'
    ONLINE = 'ONLINE', 'Online'
    WALLET = 'WALLET', 'Wallet'
    OTHER = 'OTHER', 'Other'


class DiscountType(models.TextChoices):
    """
    Type values for Discount.

    - PERCENTAGE: Percentage-based discount
    - FIXED_AMOUNT: Fixed monetary amount discount
    - BUY_X_GET_Y: Buy X get Y free promotion
    - LOYALTY: Loyalty program discount
    - COUPON: Coupon code discount
    - STAFF: Staff discount
    - HAPPY_HOUR: Happy hour time-based discount
    """
    PERCENTAGE = 'PERCENTAGE', _('Percentage')
    FIXED_AMOUNT = 'FIXED_AMOUNT', _('Fixed Amount')
    BUY_X_GET_Y = 'BUY_X_GET_Y', _('Buy X Get Y')
    LOYALTY = 'LOYALTY', _('Loyalty')
    COUPON = 'COUPON', _('Coupon')
    STAFF = 'STAFF', _('Staff')
    HAPPY_HOUR = 'HAPPY_HOUR', _('Happy Hour')


class RefundType(models.TextChoices):
    """
    Type values for Refund.

    - FULL: Full order refund
    - PARTIAL: Partial amount refund
    - ITEM: Individual item refund
    """
    FULL = 'FULL', _('Full Refund')
    PARTIAL = 'PARTIAL', _('Partial Refund')
    ITEM = 'ITEM', _('Item Refund')


class RefundStatus(models.TextChoices):
    """
    Status values for Refund lifecycle.

    - PENDING: Refund requested, awaiting approval
    - APPROVED: Refund approved by manager
    - PROCESSED: Refund has been processed/paid
    - REJECTED: Refund request was rejected
    """
    PENDING = 'PENDING', _('Pending')
    APPROVED = 'APPROVED', _('Approved')
    PROCESSED = 'PROCESSED', _('Processed')
    REJECTED = 'REJECTED', _('Rejected')


class ReservationStatus(models.TextChoices):
    """
    Status values for Reservation lifecycle.

    - PENDING: Reservation requested, awaiting confirmation
    - CONFIRMED: Reservation confirmed by staff
    - SEATED: Guest has arrived and is seated
    - COMPLETED: Reservation completed (guest left)
    - NO_SHOW: Guest did not show up
    - CANCELLED: Reservation was cancelled
    """
    PENDING = 'PENDING', _('Pending')
    CONFIRMED = 'CONFIRMED', _('Confirmed')
    SEATED = 'SEATED', _('Seated')
    COMPLETED = 'COMPLETED', _('Completed')
    NO_SHOW = 'NO_SHOW', _('No Show')
    CANCELLED = 'CANCELLED', _('Cancelled')
