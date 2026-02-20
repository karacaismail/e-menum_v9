"""
URL configuration for the Notifications application.

Routes:
    GET    /api/v1/notifications/              - List user notifications
    GET    /api/v1/notifications/{id}/         - Get notification detail
    DELETE /api/v1/notifications/{id}/         - Soft delete notification
    POST   /api/v1/notifications/{id}/read/    - Mark as read
    POST   /api/v1/notifications/read-all/     - Mark all as read
    POST   /api/v1/notifications/{id}/archive/ - Archive notification
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from apps.notifications.views import NotificationViewSet


app_name = 'notifications'

router = DefaultRouter()
router.register(r'notifications', NotificationViewSet, basename='notification')

urlpatterns = [
    path('', include(router.urls)),
]
