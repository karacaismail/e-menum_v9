"""
E-Menum Orders Application.

This app provides the order management system:
- Zone: Table groupings (Garden, Indoor, VIP Section)
- Table: Physical restaurant tables with status tracking
- QRCode: Generated QR codes for menus/tables with scan analytics
- QRScan: QR code scan tracking for analytics
- Order: Customer orders with full transaction details
- OrderItem: Individual line items within orders
- ServiceRequest: Waiter call/service requests from tables

Critical Rules:
- Every query MUST include organizationId for tenant isolation
- All entities use soft delete (deleted_at timestamp)
- No physical deletions allowed
- Orders should follow the status lifecycle: PENDING → CONFIRMED → PREPARING → READY → DELIVERED → COMPLETED
"""

default_app_config = 'apps.orders.apps.OrdersConfig'
