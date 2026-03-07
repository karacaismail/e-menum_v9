"""
Factory Boy factories for orders application models.

Provides factories for Zone, Table, QRCode, Order, OrderItem,
and ServiceRequest — the core operational models for restaurant management.

Usage:
    from tests.factories.orders import OrderFactory, TableFactory

    # Create a complete order with items
    order = OrderFactory()

    # Create a table in a specific zone
    table = TableFactory(zone=ZoneFactory(name="Garden"))

    # Create a service request for a table
    sr = ServiceRequestFactory(table=table)
"""

import uuid
from decimal import Decimal

import factory
from django.utils import timezone
from factory.django import DjangoModelFactory

from tests.factories.core import OrganizationFactory


class ZoneFactory(DjangoModelFactory):
    """
    Factory for creating Zone instances.

    Creates an active zone within an organization.

    Examples:
        zone = ZoneFactory()
        zone = ZoneFactory(name="VIP Area", is_outdoor=True)
    """

    class Meta:
        model = "orders.Zone"
        skip_postgeneration_save = True

    organization = factory.SubFactory(OrganizationFactory)
    name = factory.LazyAttribute(lambda o: f"Zone {uuid.uuid4().hex[:6]}")
    slug = factory.LazyAttribute(lambda o: f"zone-{uuid.uuid4().hex[:8]}")
    description = "Test zone for dining"
    color = "#3B82F6"
    capacity = 40
    is_active = True
    is_smoking_allowed = False
    is_outdoor = False
    is_reservable = True
    sort_order = 0
    settings = factory.LazyFunction(dict)


class OutdoorZoneFactory(ZoneFactory):
    """Factory for outdoor/garden zones."""

    name = factory.LazyAttribute(lambda o: f"Garden {uuid.uuid4().hex[:4]}")
    is_outdoor = True
    is_smoking_allowed = True


class TableFactory(DjangoModelFactory):
    """
    Factory for creating Table instances.

    Creates an available table within a zone.

    Examples:
        table = TableFactory()
        table = TableFactory(capacity=6, is_vip=True)
    """

    class Meta:
        model = "orders.Table"
        skip_postgeneration_save = True

    organization = factory.LazyAttribute(lambda o: o.zone.organization)
    zone = factory.SubFactory(ZoneFactory)
    name = factory.LazyAttribute(lambda o: f"Table {uuid.uuid4().hex[:4]}")
    number = factory.Sequence(lambda n: str(n + 1))
    slug = factory.LazyAttribute(lambda o: f"table-{uuid.uuid4().hex[:8]}")
    capacity = 4
    min_capacity = 1
    status = "AVAILABLE"
    is_active = True
    is_vip = False
    sort_order = 0
    settings = factory.LazyFunction(dict)


class VIPTableFactory(TableFactory):
    """Factory for VIP tables."""

    name = factory.LazyAttribute(lambda o: f"VIP {uuid.uuid4().hex[:4]}")
    is_vip = True
    capacity = 6


class OccupiedTableFactory(TableFactory):
    """Factory for occupied tables."""

    status = "OCCUPIED"


class ReservedTableFactory(TableFactory):
    """Factory for reserved tables."""

    status = "RESERVED"


class QRCodeFactory(DjangoModelFactory):
    """
    Factory for creating QRCode instances.

    Creates an active QR code linked to a menu.

    Examples:
        qr = QRCodeFactory()
        qr = QRCodeFactory(type="TABLE", table=table)
    """

    class Meta:
        model = "orders.QRCode"
        skip_postgeneration_save = True

    organization = factory.SubFactory(OrganizationFactory)
    name = factory.LazyAttribute(lambda o: f"QR {uuid.uuid4().hex[:6]}")
    code = factory.LazyAttribute(lambda o: f"qr-{uuid.uuid4().hex[:10]}")
    type = "MENU"
    is_active = True
    settings = factory.LazyFunction(dict)
    metadata = factory.LazyFunction(dict)


class OrderFactory(DjangoModelFactory):
    """
    Factory for creating Order instances.

    Creates a pending dine-in order with auto-generated order number.

    Examples:
        order = OrderFactory()
        order = OrderFactory(status="CONFIRMED", table=table)
    """

    class Meta:
        model = "orders.Order"
        skip_postgeneration_save = True

    organization = factory.SubFactory(OrganizationFactory)
    table = None
    customer = None
    order_number = factory.LazyAttribute(
        lambda o: f"ORD-{uuid.uuid4().hex[:8].upper()}"
    )
    status = "PENDING"
    type = "DINE_IN"
    payment_status = "PENDING"
    payment_method = "CASH"
    subtotal = Decimal("100.00")
    tax_amount = Decimal("10.00")
    discount_amount = Decimal("0.00")
    total_amount = Decimal("110.00")
    currency = "TRY"
    guest_count = 2
    notes = ""
    special_instructions = ""
    customer_info = factory.LazyFunction(dict)
    metadata = factory.LazyFunction(dict)

    @factory.lazy_attribute
    def placed_at(self):
        return timezone.now()


class ConfirmedOrderFactory(OrderFactory):
    """Factory for confirmed orders."""

    status = "CONFIRMED"

    @factory.lazy_attribute
    def confirmed_at(self):
        return timezone.now()


class PreparingOrderFactory(OrderFactory):
    """Factory for orders being prepared."""

    status = "PREPARING"

    @factory.lazy_attribute
    def confirmed_at(self):
        return timezone.now()

    @factory.lazy_attribute
    def preparing_at(self):
        return timezone.now()


class ReadyOrderFactory(OrderFactory):
    """Factory for ready orders."""

    status = "READY"

    @factory.lazy_attribute
    def confirmed_at(self):
        return timezone.now()

    @factory.lazy_attribute
    def preparing_at(self):
        return timezone.now()

    @factory.lazy_attribute
    def ready_at(self):
        return timezone.now()


class CompletedOrderFactory(OrderFactory):
    """Factory for completed orders."""

    status = "COMPLETED"
    payment_status = "PAID"

    @factory.lazy_attribute
    def confirmed_at(self):
        return timezone.now()

    @factory.lazy_attribute
    def completed_at(self):
        return timezone.now()


class CancelledOrderFactory(OrderFactory):
    """Factory for cancelled orders."""

    status = "CANCELLED"
    cancel_reason = "Customer requested cancellation"

    @factory.lazy_attribute
    def cancelled_at(self):
        return timezone.now()


class OrderItemFactory(DjangoModelFactory):
    """
    Factory for creating OrderItem instances.

    Creates a line item within an order.

    Examples:
        item = OrderItemFactory(order=order)
    """

    class Meta:
        model = "orders.OrderItem"
        skip_postgeneration_save = True

    order = factory.SubFactory(OrderFactory)
    product = None
    variant = None
    quantity = 1
    unit_price = Decimal("50.00")
    total_price = Decimal("50.00")
    currency = "TRY"
    status = "PENDING"
    notes = ""
    is_gift = False
    modifiers = factory.LazyFunction(dict)
    metadata = factory.LazyFunction(dict)


class ServiceRequestFactory(DjangoModelFactory):
    """
    Factory for creating ServiceRequest instances.

    Creates a pending waiter call for a table.

    Examples:
        sr = ServiceRequestFactory(table=table)
        sr = ServiceRequestFactory(type="BILL_REQUEST")
    """

    class Meta:
        model = "orders.ServiceRequest"
        skip_postgeneration_save = True

    organization = factory.LazyAttribute(lambda o: o.table.organization)
    table = factory.SubFactory(TableFactory)
    order = None
    customer = None
    type = "WAITER_CALL"
    status = "PENDING"
    message = ""
    priority = 3
    assigned_to = None
    metadata = factory.LazyFunction(dict)


class BillRequestFactory(ServiceRequestFactory):
    """Factory for bill request service requests."""

    type = "BILL_REQUEST"
    message = "Bill please"


class HelpRequestFactory(ServiceRequestFactory):
    """Factory for help service requests."""

    type = "HELP"
    priority = 4
    message = "Need assistance"
