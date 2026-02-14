"""
Django Admin configuration for the Media application.

This module defines admin interfaces for media models:
- MediaFolder
- Media

All admin classes implement multi-tenant filtering where applicable.
"""

from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from apps.media.models import Media, MediaFolder


@admin.register(MediaFolder)
class MediaFolderAdmin(admin.ModelAdmin):
    """Admin interface for MediaFolder management."""

    list_display = [
        'name', 'organization', 'parent', 'is_public',
        'media_count', 'children_count', 'sort_order', 'created_at'
    ]
    list_filter = [
        'is_public', 'organization', 'created_at'
    ]
    search_fields = ['name', 'slug', 'description', 'organization__name']
    readonly_fields = [
        'id', 'created_at', 'updated_at', 'media_count', 'children_count'
    ]
    ordering = ['organization', 'parent', 'sort_order', 'name']
    prepopulated_fields = {'slug': ('name',)}

    fieldsets = (
        (None, {
            'fields': ('id', 'organization', 'parent', 'name', 'slug')
        }),
        (_('Details'), {
            'fields': ('description', 'is_public', 'sort_order')
        }),
        (_('Statistics'), {
            'fields': ('media_count', 'children_count'),
            'classes': ('collapse',)
        }),
        (_('Metadata'), {
            'fields': ('metadata',),
            'classes': ('collapse',)
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at', 'deleted_at'),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        """Filter out soft-deleted folders."""
        qs = super().get_queryset(request)
        return qs.filter(deleted_at__isnull=True)

    @admin.display(description=_('Media Count'))
    def media_count(self, obj):
        """Display the number of media files in this folder."""
        return obj.media_count

    @admin.display(description=_('Subfolders'))
    def children_count(self, obj):
        """Display the number of child folders."""
        return obj.children_count


@admin.register(Media)
class MediaAdmin(admin.ModelAdmin):
    """Admin interface for Media management."""

    list_display = [
        'thumbnail_preview', 'name', 'organization', 'folder',
        'media_type_badge', 'status_badge', 'file_size_display',
        'is_public', 'usage_count', 'created_at'
    ]
    list_filter = [
        'media_type', 'status', 'storage', 'is_public',
        'organization', 'created_at'
    ]
    search_fields = [
        'name', 'original_filename', 'alt_text', 'title',
        'organization__name', 'folder__name'
    ]
    readonly_fields = [
        'id', 'thumbnail_preview_large', 'file_size_display',
        'dimensions', 'duration_formatted', 'human_readable_size',
        'usage_count', 'last_used_at', 'created_at', 'updated_at'
    ]
    ordering = ['-created_at']
    date_hierarchy = 'created_at'
    list_per_page = 50

    fieldsets = (
        (None, {
            'fields': ('id', 'organization', 'folder', 'uploaded_by')
        }),
        (_('File Information'), {
            'fields': (
                'name', 'original_filename', 'media_type', 'status',
                'mime_type', 'storage'
            )
        }),
        (_('Preview'), {
            'fields': ('thumbnail_preview_large',),
            'classes': ('collapse',)
        }),
        (_('URLs'), {
            'fields': ('file_path', 'url', 'thumbnail_url')
        }),
        (_('Dimensions & Size'), {
            'fields': (
                'file_size', 'human_readable_size',
                'width', 'height', 'dimensions',
                'duration', 'duration_formatted'
            ),
            'classes': ('collapse',)
        }),
        (_('SEO & Accessibility'), {
            'fields': ('alt_text', 'title', 'caption', 'is_public')
        }),
        (_('Usage Statistics'), {
            'fields': ('usage_count', 'last_used_at'),
            'classes': ('collapse',)
        }),
        (_('Metadata'), {
            'fields': ('metadata',),
            'classes': ('collapse',)
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at', 'deleted_at'),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        """Filter out soft-deleted media and optimize queries."""
        qs = super().get_queryset(request)
        return qs.filter(deleted_at__isnull=True).select_related(
            'organization', 'folder', 'uploaded_by'
        )

    @admin.display(description=_('Preview'))
    def thumbnail_preview(self, obj):
        """Display a small thumbnail preview."""
        if obj.thumbnail_url:
            return format_html(
                '<img src="{}" style="max-height: 40px; max-width: 60px; '
                'object-fit: cover; border-radius: 4px;" />',
                obj.thumbnail_url
            )
        elif obj.url and obj.is_image:
            return format_html(
                '<img src="{}" style="max-height: 40px; max-width: 60px; '
                'object-fit: cover; border-radius: 4px;" />',
                obj.url
            )
        return format_html(
            '<span style="color: #999;">No preview</span>'
        )

    @admin.display(description=_('Preview'))
    def thumbnail_preview_large(self, obj):
        """Display a larger thumbnail preview for detail view."""
        if obj.thumbnail_url:
            return format_html(
                '<img src="{}" style="max-height: 200px; max-width: 300px; '
                'object-fit: contain; border-radius: 8px; border: 1px solid #ddd;" />',
                obj.thumbnail_url
            )
        elif obj.url and obj.is_image:
            return format_html(
                '<img src="{}" style="max-height: 200px; max-width: 300px; '
                'object-fit: contain; border-radius: 8px; border: 1px solid #ddd;" />',
                obj.url
            )
        return format_html(
            '<span style="color: #999;">No preview available</span>'
        )

    @admin.display(description=_('Type'))
    def media_type_badge(self, obj):
        """Display media type with color-coded badge."""
        colors = {
            'IMAGE': '#3B82F6',     # Blue
            'VIDEO': '#EF4444',     # Red
            'DOCUMENT': '#10B981',  # Green
            'AUDIO': '#8B5CF6',     # Purple
        }
        color = colors.get(obj.media_type, '#6B7280')
        return format_html(
            '<span style="background-color: {}; color: white; '
            'padding: 2px 8px; border-radius: 4px; font-size: 11px; '
            'font-weight: 500;">{}</span>',
            color, obj.get_media_type_display()
        )

    @admin.display(description=_('Status'))
    def status_badge(self, obj):
        """Display status with color-coded badge."""
        colors = {
            'PENDING': '#F59E0B',     # Amber
            'PROCESSING': '#3B82F6',  # Blue
            'READY': '#10B981',       # Green
            'FAILED': '#EF4444',      # Red
        }
        color = colors.get(obj.status, '#6B7280')
        return format_html(
            '<span style="background-color: {}; color: white; '
            'padding: 2px 8px; border-radius: 4px; font-size: 11px; '
            'font-weight: 500;">{}</span>',
            color, obj.get_status_display()
        )

    @admin.display(description=_('Size'))
    def file_size_display(self, obj):
        """Display file size in human-readable format."""
        return obj.human_readable_size

    @admin.display(description=_('Dimensions'))
    def dimensions(self, obj):
        """Display dimensions for images/videos."""
        return obj.dimensions or '-'
