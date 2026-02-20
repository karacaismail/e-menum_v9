"""
Views for the Notifications application.

This module provides ViewSets for notification-related operations:
- NotificationViewSet: List, retrieve, mark-as-read, archive notifications

API Endpoints:
    GET    /api/v1/notifications/              - List user notifications
    GET    /api/v1/notifications/{id}/         - Get notification detail
    DELETE /api/v1/notifications/{id}/         - Soft delete notification
    POST   /api/v1/notifications/{id}/read/    - Mark notification as read
    POST   /api/v1/notifications/read-all/     - Mark all notifications as read
    POST   /api/v1/notifications/{id}/archive/ - Archive notification

Multi-Tenancy:
    All queries automatically filter by organization (via BaseTenantViewSet).

Critical Rules:
    - Users can only see their OWN notifications (additional filtering by user)
    - Use soft_delete() - never call delete() directly
"""

import logging

from django.db import models
from django.utils.translation import gettext_lazy as _
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.notifications.models import Notification
from apps.notifications.choices import NotificationStatus
from apps.notifications.serializers import (
    NotificationListSerializer,
    NotificationDetailSerializer,
)
from shared.views.base import BaseTenantViewSet


logger = logging.getLogger(__name__)


class NotificationViewSet(BaseTenantViewSet):
    """
    ViewSet for notification management.

    Users can only view and manage their own notifications.
    Organization-level filtering is handled by BaseTenantViewSet.

    API Endpoints:
        GET    /api/v1/notifications/              - List user notifications
        GET    /api/v1/notifications/{id}/         - Get notification detail
        DELETE /api/v1/notifications/{id}/         - Soft delete (archive)
        POST   /api/v1/notifications/{id}/read/    - Mark as read
        POST   /api/v1/notifications/read-all/     - Mark all as read
        POST   /api/v1/notifications/{id}/archive/ - Archive notification

    Query Parameters:
        - status: Filter by status (PENDING, SENT, DELIVERED, READ, ARCHIVED, FAILED)
        - notification_type: Filter by type (ORDER, SYSTEM, PROMOTION, PAYMENT, FEEDBACK, SECURITY, GENERAL)
        - priority: Filter by priority (LOW, NORMAL, HIGH, URGENT)
        - unread: Filter unread only (true/false)

    Permissions:
        - Requires authentication
        - Requires organization membership
        - Users can only see their own notifications
    """

    queryset = Notification.objects.all()
    permission_resource = 'notification'
    # Notifications are read-only from API perspective (system creates them)
    http_method_names = ['get', 'delete', 'head', 'options', 'post']

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'list':
            return NotificationListSerializer
        return NotificationDetailSerializer

    def get_queryset(self):
        """
        Return notifications filtered by:
        1. Organization (via BaseTenantViewSet)
        2. Current user (users only see their own notifications)
        3. Optional query parameter filters
        """
        queryset = super().get_queryset()

        # Critical: users only see their own notifications
        queryset = queryset.filter(user=self.request.user)

        # Apply status filter
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter.upper())

        # Apply type filter
        notification_type = self.request.query_params.get('notification_type')
        if notification_type:
            queryset = queryset.filter(
                notification_type=notification_type.upper()
            )

        # Apply priority filter
        priority = self.request.query_params.get('priority')
        if priority:
            queryset = queryset.filter(priority=priority.upper())

        # Filter unread notifications
        unread = self.request.query_params.get('unread')
        if unread and unread.lower() == 'true':
            queryset = queryset.filter(
                status__in=[
                    NotificationStatus.PENDING,
                    NotificationStatus.SENT,
                    NotificationStatus.DELIVERED,
                ]
            )

        return queryset.order_by('-created_at')

    @action(detail=True, methods=['post'])
    def read(self, request, pk=None):
        """
        Mark a notification as read.

        POST /api/v1/notifications/{id}/read/
            Response (200):
                {
                    "success": true,
                    "data": {
                        "message": "Notification marked as read"
                    }
                }
        """
        notification = self.get_object()

        if not notification.is_read:
            notification.mark_as_read()
            logger.info(
                "Notification %s marked as read by user %s",
                notification.id,
                request.user.id
            )

        return self.get_success_response({
            'message': str(_('Notification marked as read')),
            'read_at': notification.read_at.isoformat() if notification.read_at else None,
        })

    @action(detail=False, methods=['post'], url_path='read-all')
    def read_all(self, request):
        """
        Mark all unread notifications as read for the current user.

        POST /api/v1/notifications/read-all/
            Response (200):
                {
                    "success": true,
                    "data": {
                        "message": "All notifications marked as read",
                        "count": 5
                    }
                }
        """
        from django.utils import timezone

        organization = self.get_organization()
        if not organization:
            return self.get_error_response(
                code='FORBIDDEN',
                message=str(_('Organization context required')),
                status_code=status.HTTP_403_FORBIDDEN
            )

        now = timezone.now()
        count = Notification.objects.filter(
            organization=organization,
            user=request.user,
            status__in=[
                NotificationStatus.PENDING,
                NotificationStatus.SENT,
                NotificationStatus.DELIVERED,
            ],
            deleted_at__isnull=True,
        ).update(
            status=NotificationStatus.READ,
            read_at=now,
        )

        logger.info(
            "Marked %d notifications as read for user %s",
            count,
            request.user.id
        )

        return self.get_success_response({
            'message': str(_('All notifications marked as read')),
            'count': count,
        })

    @action(detail=True, methods=['post'])
    def archive(self, request, pk=None):
        """
        Archive a notification.

        POST /api/v1/notifications/{id}/archive/
            Response (200):
                {
                    "success": true,
                    "data": {
                        "message": "Notification archived"
                    }
                }
        """
        notification = self.get_object()
        notification.archive()

        return self.get_success_response({
            'message': str(_('Notification archived')),
        })


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    'NotificationViewSet',
]
