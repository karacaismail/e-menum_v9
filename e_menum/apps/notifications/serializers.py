"""
Serializers for the Notifications application.

Provides serializers for:
- Notification: Read/list/detail serializers for user notifications

API Endpoints:
    /api/v1/notifications/          - List notifications
    /api/v1/notifications/{id}/     - Get notification detail
    /api/v1/notifications/{id}/read/ - Mark as read
    /api/v1/notifications/read-all/  - Mark all as read
"""

from rest_framework import serializers

from apps.notifications.models import Notification


class NotificationListSerializer(serializers.ModelSerializer):
    """
    Serializer for listing notifications.

    Lightweight representation for list views.
    """

    is_read = serializers.SerializerMethodField()
    is_expired = serializers.SerializerMethodField()
    is_urgent = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = [
            'id',
            'notification_type',
            'status',
            'priority',
            'channel',
            'title',
            'message',
            'is_read',
            'is_expired',
            'is_urgent',
            'action_url',
            'image_url',
            'read_at',
            'created_at',
        ]
        read_only_fields = fields

    def get_is_read(self, obj) -> bool:
        """Check if notification has been read."""
        return obj.is_read

    def get_is_expired(self, obj) -> bool:
        """Check if notification has expired."""
        return obj.is_expired

    def get_is_urgent(self, obj) -> bool:
        """Check if notification is urgent."""
        return obj.is_urgent


class NotificationDetailSerializer(serializers.ModelSerializer):
    """
    Detailed serializer for single notification view.

    Includes all fields for complete information display.
    """

    is_read = serializers.SerializerMethodField()
    is_expired = serializers.SerializerMethodField()
    is_urgent = serializers.SerializerMethodField()
    is_sent = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = [
            'id',
            'notification_type',
            'status',
            'priority',
            'channel',
            'title',
            'message',
            'data',
            'metadata',
            'is_read',
            'is_expired',
            'is_urgent',
            'is_sent',
            'action_url',
            'image_url',
            'read_at',
            'sent_at',
            'delivered_at',
            'scheduled_for',
            'expires_at',
            'created_at',
            'updated_at',
        ]
        read_only_fields = fields

    def get_is_read(self, obj) -> bool:
        return obj.is_read

    def get_is_expired(self, obj) -> bool:
        return obj.is_expired

    def get_is_urgent(self, obj) -> bool:
        return obj.is_urgent

    def get_is_sent(self, obj) -> bool:
        return obj.is_sent


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    'NotificationListSerializer',
    'NotificationDetailSerializer',
]
