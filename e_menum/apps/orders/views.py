"""
Views for the Orders application.

This module provides ViewSets for order-related models:
- ZoneViewSet: Table zone/section management CRUD
- TableViewSet: Table management CRUD with status actions
- QRCodeViewSet: QR code management CRUD with scan analytics
- OrderViewSet: Order management with workflow actions
- ServiceRequestViewSet: Service request management

API Endpoints:
    /api/v1/zones/              - Zone CRUD
    /api/v1/tables/             - Table CRUD
    /api/v1/qr-codes/           - QR Code CRUD
    /api/v1/orders/             - Order CRUD + workflow actions
    /api/v1/service-requests/   - Service Request CRUD

Multi-Tenancy:
    All ViewSets use BaseTenantViewSet which automatically filters
    querysets by the current organization.

Critical Rules:
    - EVERY query MUST include organization filtering (handled by BaseTenantViewSet)
    - Use soft_delete() - never call delete() directly (handled by SoftDeleteMixin)
    - All responses follow E-Menum standard format (handled by StandardResponseMixin)
"""

import logging

from django.db.models import Prefetch, Q
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from rest_framework import status
from rest_framework.decorators import action

from apps.orders.models import (
    Zone,
    Table,
    QRCode,
    QRScan,
    Order,
    OrderItem,
    ServiceRequest,
)
from apps.orders.choices import (
    TableStatus,
    OrderStatus,
    PaymentStatus,
    ServiceRequestStatus,
)
from apps.orders.serializers import (
    # Zone
    ZoneListSerializer,
    ZoneDetailSerializer,
    ZoneCreateSerializer,
    ZoneUpdateSerializer,
    # Table
    TableListSerializer,
    TableDetailSerializer,
    TableCreateSerializer,
    TableUpdateSerializer,
    # QR Code
    QRCodeListSerializer,
    QRCodeDetailSerializer,
    QRCodeCreateSerializer,
    QRCodeUpdateSerializer,
    # QR Scan
    QRScanSerializer,
    # Order
    OrderListSerializer,
    OrderDetailSerializer,
    OrderCreateSerializer,
    OrderUpdateSerializer,
    # Order Item
    ServiceRequestListSerializer,
    ServiceRequestDetailSerializer,
    ServiceRequestCreateSerializer,
    ServiceRequestUpdateSerializer,
)
from shared.permissions.plan_enforcement import PlanEnforcementMixin
from shared.views.base import (
    BaseTenantViewSet,
)


logger = logging.getLogger(__name__)


# =============================================================================
# ZONE VIEWSET
# =============================================================================

class ZoneViewSet(BaseTenantViewSet):
    """
    ViewSet for zone management.

    Zones organize tables into logical areas like "Garden", "Indoor",
    "VIP Section", etc. This helps staff manage sections and customers
    choose preferred seating areas.

    API Endpoints:
        GET    /api/v1/zones/              - List organization zones
        POST   /api/v1/zones/              - Create a new zone
        GET    /api/v1/zones/{id}/         - Get zone details
        PUT    /api/v1/zones/{id}/         - Update zone
        PATCH  /api/v1/zones/{id}/         - Partial update zone
        DELETE /api/v1/zones/{id}/         - Soft delete zone
        POST   /api/v1/zones/{id}/activate/   - Activate zone
        POST   /api/v1/zones/{id}/deactivate/ - Deactivate zone

    Query Parameters:
        - is_active: Filter by active status (true/false)
        - is_outdoor: Filter by outdoor zones (true/false)
        - is_reservable: Filter by reservable zones (true/false)
        - search: Search by name

    Permissions:
        - Requires authentication
        - Requires organization membership
        - Requires zone.view, zone.create, zone.update, zone.delete permissions
    """

    queryset = Zone.objects.all()
    permission_resource = 'zone'

    def get_serializer_class(self):
        """Return the appropriate serializer based on action."""
        if self.action == 'list':
            return ZoneListSerializer
        elif self.action == 'create':
            return ZoneCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return ZoneUpdateSerializer
        return ZoneDetailSerializer

    def get_queryset(self):
        """Return zones filtered by organization with optional filters."""
        queryset = super().get_queryset()

        # Prefetch tables for count optimization
        queryset = queryset.prefetch_related(
            Prefetch(
                'tables',
                queryset=Table.objects.filter(deleted_at__isnull=True)
            )
        )

        # Apply filters
        for param in ['is_active', 'is_outdoor', 'is_reservable', 'is_smoking_allowed']:
            value = self.request.query_params.get(param)
            if value is not None:
                queryset = queryset.filter(**{param: value.lower() == 'true'})

        # Apply search filter
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(name__icontains=search)

        return queryset.order_by('sort_order', 'name')

    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """
        Activate the zone for seating.

        POST /api/v1/zones/{id}/activate/
        """
        zone = self.get_object()
        zone.activate()

        return self.get_success_response({
            'message': str(_('Zone activated')),
            'is_active': True
        })

    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        """
        Deactivate the zone (not available for seating).

        POST /api/v1/zones/{id}/deactivate/
        """
        zone = self.get_object()
        zone.deactivate()

        return self.get_success_response({
            'message': str(_('Zone deactivated')),
            'is_active': False
        })


# =============================================================================
# TABLE VIEWSET
# =============================================================================

class TableViewSet(BaseTenantViewSet):
    """
    ViewSet for table management.

    Tables are physical seating units within zones. Each table has a status
    (available, occupied, reserved), capacity, and can be associated with
    QR codes for digital menu access.

    API Endpoints:
        GET    /api/v1/tables/              - List organization tables
        POST   /api/v1/tables/              - Create a new table
        GET    /api/v1/tables/{id}/         - Get table details
        PUT    /api/v1/tables/{id}/         - Update table
        PATCH  /api/v1/tables/{id}/         - Partial update table
        DELETE /api/v1/tables/{id}/         - Soft delete table
        POST   /api/v1/tables/{id}/set-available/ - Set table as available
        POST   /api/v1/tables/{id}/set-occupied/  - Set table as occupied
        POST   /api/v1/tables/{id}/set-reserved/  - Set table as reserved

    Query Parameters:
        - zone_id: Filter by zone
        - status: Filter by status (AVAILABLE, OCCUPIED, RESERVED)
        - is_active: Filter by active status
        - is_vip: Filter by VIP tables
        - min_capacity: Filter by minimum capacity
        - search: Search by name

    Permissions:
        - Requires authentication
        - Requires organization membership
        - Requires table.view, table.create, table.update, table.delete permissions
    """

    queryset = Table.objects.all()
    permission_resource = 'table'

    def get_serializer_class(self):
        """Return the appropriate serializer based on action."""
        if self.action == 'list':
            return TableListSerializer
        elif self.action == 'create':
            return TableCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return TableUpdateSerializer
        return TableDetailSerializer

    def get_queryset(self):
        """Return tables filtered by organization with optional filters."""
        queryset = super().get_queryset()

        # Optimize with select_related
        queryset = queryset.select_related('zone')

        # For detail view, prefetch related data
        if self.action == 'retrieve':
            queryset = queryset.prefetch_related(
                Prefetch(
                    'qr_codes',
                    queryset=QRCode.objects.filter(deleted_at__isnull=True)
                ),
                Prefetch(
                    'orders',
                    queryset=Order.objects.filter(
                        deleted_at__isnull=True,
                        status__in=[
                            OrderStatus.PENDING,
                            OrderStatus.CONFIRMED,
                            OrderStatus.PREPARING,
                            OrderStatus.READY,
                            OrderStatus.DELIVERED,
                        ]
                    ).order_by('-created_at')[:5]
                )
            )

        # Filter by zone
        zone_id = self.request.query_params.get('zone_id')
        if zone_id:
            queryset = queryset.filter(zone_id=zone_id)

        # Filter by status
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter.upper())

        # Apply boolean filters
        for param in ['is_active', 'is_vip']:
            value = self.request.query_params.get(param)
            if value is not None:
                queryset = queryset.filter(**{param: value.lower() == 'true'})

        # Filter by minimum capacity
        min_capacity = self.request.query_params.get('min_capacity')
        if min_capacity:
            try:
                queryset = queryset.filter(capacity__gte=int(min_capacity))
            except ValueError:
                pass

        # Apply search filter
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(notes__icontains=search)
            )

        return queryset.order_by('zone', 'sort_order', 'number', 'name')

    @action(detail=True, methods=['post'], url_path='set-available')
    def set_available(self, request, pk=None):
        """
        Set the table as available for seating.

        POST /api/v1/tables/{id}/set-available/
        """
        table = self.get_object()
        table.set_available()

        return self.get_success_response({
            'message': str(_('Table set as available')),
            'status': TableStatus.AVAILABLE
        })

    @action(detail=True, methods=['post'], url_path='set-occupied')
    def set_occupied(self, request, pk=None):
        """
        Set the table as occupied by guests.

        POST /api/v1/tables/{id}/set-occupied/
        """
        table = self.get_object()
        table.set_occupied()

        return self.get_success_response({
            'message': str(_('Table set as occupied')),
            'status': TableStatus.OCCUPIED
        })

    @action(detail=True, methods=['post'], url_path='set-reserved')
    def set_reserved(self, request, pk=None):
        """
        Set the table as reserved.

        POST /api/v1/tables/{id}/set-reserved/
        """
        table = self.get_object()
        table.set_reserved()

        return self.get_success_response({
            'message': str(_('Table set as reserved')),
            'status': TableStatus.RESERVED
        })

    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """Activate the table for use."""
        table = self.get_object()
        table.activate()

        return self.get_success_response({
            'message': str(_('Table activated')),
            'is_active': True
        })

    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        """Deactivate the table (not available for use)."""
        table = self.get_object()
        table.deactivate()

        return self.get_success_response({
            'message': str(_('Table deactivated')),
            'is_active': False
        })


# =============================================================================
# QR CODE VIEWSET
# =============================================================================

class QRCodeViewSet(PlanEnforcementMixin, BaseTenantViewSet):
    """
    ViewSet for QR code management.

    QR codes are the primary way customers access digital menus. Each QR code
    can be associated with a menu, table, or used for marketing campaigns.

    API Endpoints:
        GET    /api/v1/qr-codes/              - List organization QR codes
        POST   /api/v1/qr-codes/              - Create a new QR code
        GET    /api/v1/qr-codes/{id}/         - Get QR code details
        PUT    /api/v1/qr-codes/{id}/         - Update QR code
        PATCH  /api/v1/qr-codes/{id}/         - Partial update QR code
        DELETE /api/v1/qr-codes/{id}/         - Soft delete QR code
        POST   /api/v1/qr-codes/{id}/activate/   - Activate QR code
        POST   /api/v1/qr-codes/{id}/deactivate/ - Deactivate QR code
        GET    /api/v1/qr-codes/{id}/scans/   - Get scan analytics

    Query Parameters:
        - type: Filter by type (MENU, TABLE, CAMPAIGN)
        - is_active: Filter by active status
        - table_id: Filter by linked table
        - menu_id: Filter by linked menu
        - search: Search by name or code

    Permissions:
        - Requires authentication
        - Requires organization membership
        - Requires qr_code.view, qr_code.create, qr_code.update, qr_code.delete permissions

    Plan Enforcement:
        - Create action checks 'max_qr_codes' limit from subscription plan
    """

    queryset = QRCode.objects.all()
    permission_resource = 'qr_code'

    # Plan enforcement: limit QR code creation per plan
    plan_limit_key = 'max_qr_codes'
    plan_limit_model = QRCode

    def get_serializer_class(self):
        """Return the appropriate serializer based on action."""
        if self.action == 'list':
            return QRCodeListSerializer
        elif self.action == 'create':
            return QRCodeCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return QRCodeUpdateSerializer
        elif self.action == 'scans':
            return QRScanSerializer
        return QRCodeDetailSerializer

    def get_queryset(self):
        """Return QR codes filtered by organization with optional filters."""
        queryset = super().get_queryset()

        # Optimize with select_related
        queryset = queryset.select_related('menu', 'table')

        # Filter by type
        qr_type = self.request.query_params.get('type')
        if qr_type:
            queryset = queryset.filter(type=qr_type.upper())

        # Apply boolean filters
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')

        # Filter by linked entities
        table_id = self.request.query_params.get('table_id')
        if table_id:
            queryset = queryset.filter(table_id=table_id)

        menu_id = self.request.query_params.get('menu_id')
        if menu_id:
            queryset = queryset.filter(menu_id=menu_id)

        # Apply search filter
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(code__icontains=search) |
                Q(description__icontains=search)
            )

        return queryset.order_by('-created_at')

    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """
        Activate the QR code for scanning.

        POST /api/v1/qr-codes/{id}/activate/
        """
        qr_code = self.get_object()
        qr_code.activate()

        return self.get_success_response({
            'message': str(_('QR code activated')),
            'is_active': True
        })

    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        """
        Deactivate the QR code (stops working).

        POST /api/v1/qr-codes/{id}/deactivate/
        """
        qr_code = self.get_object()
        qr_code.deactivate()

        return self.get_success_response({
            'message': str(_('QR code deactivated')),
            'is_active': False
        })

    @action(detail=True, methods=['get'])
    def scans(self, request, pk=None):
        """
        Get scan analytics for this QR code.

        GET /api/v1/qr-codes/{id}/scans/
        """
        qr_code = self.get_object()
        scans = QRScan.objects.filter(
            qr_code=qr_code
        ).order_by('-scanned_at')[:100]

        serializer = QRScanSerializer(scans, many=True)
        return self.get_success_response(serializer.data)


# =============================================================================
# ORDER VIEWSET
# =============================================================================

class OrderViewSet(BaseTenantViewSet):
    """
    ViewSet for order management.

    Orders capture all aspects of customer transactions including items ordered,
    pricing details, payment status, and fulfillment workflow.

    Status Workflow:
    PENDING → CONFIRMED → PREPARING → READY → DELIVERED → COMPLETED
                                                        ↘ CANCELLED

    API Endpoints:
        GET    /api/v1/orders/              - List organization orders
        POST   /api/v1/orders/              - Create a new order
        GET    /api/v1/orders/{id}/         - Get order details
        PUT    /api/v1/orders/{id}/         - Update order
        PATCH  /api/v1/orders/{id}/         - Partial update order
        DELETE /api/v1/orders/{id}/         - Soft delete order
        POST   /api/v1/orders/{id}/confirm/       - Confirm order
        POST   /api/v1/orders/{id}/prepare/       - Start preparation
        POST   /api/v1/orders/{id}/ready/         - Mark as ready
        POST   /api/v1/orders/{id}/deliver/       - Mark as delivered
        POST   /api/v1/orders/{id}/complete/      - Complete order
        POST   /api/v1/orders/{id}/cancel/        - Cancel order
        POST   /api/v1/orders/{id}/mark-paid/     - Mark as paid

    Query Parameters:
        - status: Filter by status
        - type: Filter by order type
        - payment_status: Filter by payment status
        - table_id: Filter by table
        - customer_id: Filter by customer
        - placed_after: Filter by placement date (ISO format)
        - placed_before: Filter by placement date (ISO format)
        - search: Search by order number

    Permissions:
        - Requires authentication
        - Requires organization membership
        - Requires order.view, order.create, order.update, order.delete permissions
    """

    queryset = Order.objects.all()
    permission_resource = 'order'

    def get_serializer_class(self):
        """Return the appropriate serializer based on action."""
        if self.action == 'list':
            return OrderListSerializer
        elif self.action == 'create':
            return OrderCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return OrderUpdateSerializer
        return OrderDetailSerializer

    def get_queryset(self):
        """Return orders filtered by organization with optional filters."""
        queryset = super().get_queryset()

        # Optimize with select_related and prefetch_related
        queryset = queryset.select_related('table', 'customer', 'placed_by', 'assigned_to')

        # For detail view, prefetch items
        if self.action == 'retrieve':
            queryset = queryset.prefetch_related(
                Prefetch(
                    'items',
                    queryset=OrderItem.objects.filter(deleted_at__isnull=True)
                        .select_related('product', 'variant')
                        .order_by('created_at')
                )
            )

        # Filter by status
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter.upper())

        # Filter by type
        type_filter = self.request.query_params.get('type')
        if type_filter:
            queryset = queryset.filter(type=type_filter.upper())

        # Filter by payment status
        payment_status = self.request.query_params.get('payment_status')
        if payment_status:
            queryset = queryset.filter(payment_status=payment_status.upper())

        # Filter by table
        table_id = self.request.query_params.get('table_id')
        if table_id:
            queryset = queryset.filter(table_id=table_id)

        # Filter by customer
        customer_id = self.request.query_params.get('customer_id')
        if customer_id:
            queryset = queryset.filter(customer_id=customer_id)

        # Filter by date range
        placed_after = self.request.query_params.get('placed_after')
        if placed_after:
            queryset = queryset.filter(placed_at__gte=placed_after)

        placed_before = self.request.query_params.get('placed_before')
        if placed_before:
            queryset = queryset.filter(placed_at__lte=placed_before)

        # Apply search filter
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(order_number__icontains=search)

        return queryset.order_by('-created_at')

    @action(detail=True, methods=['post'])
    def confirm(self, request, pk=None):
        """
        Confirm the order.

        POST /api/v1/orders/{id}/confirm/
        """
        order = self.get_object()
        try:
            order.confirm()
            return self.get_success_response({
                'message': str(_('Order confirmed')),
                'status': OrderStatus.CONFIRMED
            })
        except ValueError as e:
            return self.get_error_response(
                code='INVALID_STATUS_TRANSITION',
                message=str(e),
                status_code=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['post'])
    def prepare(self, request, pk=None):
        """
        Start order preparation.

        POST /api/v1/orders/{id}/prepare/
        """
        order = self.get_object()
        try:
            order.start_preparation()
            return self.get_success_response({
                'message': str(_('Order preparation started')),
                'status': OrderStatus.PREPARING
            })
        except ValueError as e:
            return self.get_error_response(
                code='INVALID_STATUS_TRANSITION',
                message=str(e),
                status_code=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['post'])
    def ready(self, request, pk=None):
        """
        Mark order as ready.

        POST /api/v1/orders/{id}/ready/
        """
        order = self.get_object()
        try:
            order.mark_ready()
            return self.get_success_response({
                'message': str(_('Order marked as ready')),
                'status': OrderStatus.READY
            })
        except ValueError as e:
            return self.get_error_response(
                code='INVALID_STATUS_TRANSITION',
                message=str(e),
                status_code=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['post'])
    def deliver(self, request, pk=None):
        """
        Mark order as delivered.

        POST /api/v1/orders/{id}/deliver/
        """
        order = self.get_object()
        try:
            order.deliver()
            return self.get_success_response({
                'message': str(_('Order delivered')),
                'status': OrderStatus.DELIVERED
            })
        except ValueError as e:
            return self.get_error_response(
                code='INVALID_STATUS_TRANSITION',
                message=str(e),
                status_code=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """
        Complete the order.

        POST /api/v1/orders/{id}/complete/
        """
        order = self.get_object()
        try:
            order.complete()
            return self.get_success_response({
                'message': str(_('Order completed')),
                'status': OrderStatus.COMPLETED
            })
        except ValueError as e:
            return self.get_error_response(
                code='INVALID_STATUS_TRANSITION',
                message=str(e),
                status_code=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """
        Cancel the order.

        POST /api/v1/orders/{id}/cancel/
        Body: {"reason": "Customer request"}
        """
        order = self.get_object()
        reason = request.data.get('reason')

        try:
            order.cancel(reason=reason)
            return self.get_success_response({
                'message': str(_('Order cancelled')),
                'status': OrderStatus.CANCELLED
            })
        except ValueError as e:
            return self.get_error_response(
                code='INVALID_STATUS_TRANSITION',
                message=str(e),
                status_code=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['post'], url_path='mark-paid')
    def mark_paid(self, request, pk=None):
        """
        Mark order as paid.

        POST /api/v1/orders/{id}/mark-paid/
        Body: {"method": "CASH"}  // Optional payment method
        """
        order = self.get_object()
        method = request.data.get('method')

        try:
            order.mark_paid(method=method)
            return self.get_success_response({
                'message': str(_('Order marked as paid')),
                'payment_status': PaymentStatus.PAID,
                'payment_method': method
            })
        except ValueError as e:
            return self.get_error_response(
                code='INVALID_PAYMENT_METHOD',
                message=str(e),
                status_code=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['post'])
    def recalculate(self, request, pk=None):
        """
        Recalculate order totals from items.

        POST /api/v1/orders/{id}/recalculate/
        """
        order = self.get_object()
        order.calculate_totals()

        serializer = OrderDetailSerializer(order, context={'request': request})
        return self.get_success_response(serializer.data)


# =============================================================================
# SERVICE REQUEST VIEWSET
# =============================================================================

class ServiceRequestViewSet(BaseTenantViewSet):
    """
    ViewSet for service request management.

    Service requests are waiter calls, bill requests, and other assistance
    requests from tables.

    API Endpoints:
        GET    /api/v1/service-requests/              - List requests
        POST   /api/v1/service-requests/              - Create request
        GET    /api/v1/service-requests/{id}/         - Get request details
        PUT    /api/v1/service-requests/{id}/         - Update request
        PATCH  /api/v1/service-requests/{id}/         - Partial update
        DELETE /api/v1/service-requests/{id}/         - Soft delete
        POST   /api/v1/service-requests/{id}/acknowledge/ - Acknowledge
        POST   /api/v1/service-requests/{id}/complete/    - Complete

    Query Parameters:
        - status: Filter by status
        - type: Filter by type
        - table_id: Filter by table
        - priority: Filter by priority

    Permissions:
        - Requires authentication
        - Requires organization membership
    """

    queryset = ServiceRequest.objects.all()
    permission_resource = 'service_request'

    def get_serializer_class(self):
        """Return the appropriate serializer based on action."""
        if self.action == 'list':
            return ServiceRequestListSerializer
        elif self.action == 'create':
            return ServiceRequestCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return ServiceRequestUpdateSerializer
        return ServiceRequestDetailSerializer

    def get_queryset(self):
        """Return service requests filtered by organization."""
        queryset = super().get_queryset()

        # Optimize with select_related
        queryset = queryset.select_related('table', 'assigned_to')

        # Filter by status
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter.upper())

        # Filter by type
        type_filter = self.request.query_params.get('type')
        if type_filter:
            queryset = queryset.filter(type=type_filter.upper())

        # Filter by table
        table_id = self.request.query_params.get('table_id')
        if table_id:
            queryset = queryset.filter(table_id=table_id)

        # Filter by priority
        priority = self.request.query_params.get('priority')
        if priority:
            try:
                queryset = queryset.filter(priority=int(priority))
            except ValueError:
                pass

        return queryset.order_by('-priority', '-created_at')

    @action(detail=True, methods=['post'])
    def acknowledge(self, request, pk=None):
        """
        Acknowledge the service request.

        POST /api/v1/service-requests/{id}/acknowledge/
        """
        service_request = self.get_object()

        if service_request.status != ServiceRequestStatus.PENDING:
            return self.get_error_response(
                code='INVALID_STATUS',
                message=_('Service request is not pending'),
                status_code=status.HTTP_400_BAD_REQUEST
            )

        service_request.status = ServiceRequestStatus.IN_PROGRESS
        service_request.acknowledged_at = timezone.now()
        service_request.assigned_to = request.user
        service_request.save(update_fields=[
            'status', 'acknowledged_at', 'assigned_to', 'updated_at'
        ])

        return self.get_success_response({
            'message': str(_('Service request acknowledged')),
            'status': ServiceRequestStatus.IN_PROGRESS
        })

    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """
        Complete the service request.

        POST /api/v1/service-requests/{id}/complete/
        """
        service_request = self.get_object()

        if service_request.status not in [
            ServiceRequestStatus.PENDING,
            ServiceRequestStatus.IN_PROGRESS
        ]:
            return self.get_error_response(
                code='INVALID_STATUS',
                message=_('Service request cannot be completed'),
                status_code=status.HTTP_400_BAD_REQUEST
            )

        service_request.status = ServiceRequestStatus.COMPLETED
        service_request.completed_at = timezone.now()
        service_request.save(update_fields=[
            'status', 'completed_at', 'updated_at'
        ])

        return self.get_success_response({
            'message': str(_('Service request completed')),
            'status': ServiceRequestStatus.COMPLETED
        })


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    'ZoneViewSet',
    'TableViewSet',
    'QRCodeViewSet',
    'OrderViewSet',
    'ServiceRequestViewSet',
]
