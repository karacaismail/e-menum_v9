"""
URL patterns for the Media application.
"""

from django.urls import path

from apps.media.views import (
    MediaDeleteView,
    MediaDetailView,
    MediaFolderDetailView,
    MediaFolderListCreateView,
    MediaListView,
    MediaUploadView,
)

app_name = 'media'

urlpatterns = [
    # Folders
    path('folders/', MediaFolderListCreateView.as_view(), name='folder-list-create'),
    path('folders/<uuid:pk>/', MediaFolderDetailView.as_view(), name='folder-detail'),
    # Media files
    path('', MediaListView.as_view(), name='media-list'),
    path('upload/', MediaUploadView.as_view(), name='media-upload'),
    path('<uuid:pk>/', MediaDetailView.as_view(), name='media-detail'),
    path('<uuid:pk>/delete/', MediaDeleteView.as_view(), name='media-delete'),
]
