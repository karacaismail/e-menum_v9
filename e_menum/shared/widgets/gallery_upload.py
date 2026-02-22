"""
GalleryUploadWidget - Custom Django widget for multi-image gallery management.

Renders a gallery grid interface with:
- Thumbnail grid of existing images
- Delete button per image
- "Add images" button (multi-file select)
- Drag & drop zone for bulk upload
- Manual URL entry
- Upload progress for each file

Works with JSONField (stores array of URL strings).
Uses Alpine.js for interactivity (already loaded in admin).
"""

import json

from django import forms


class GalleryUploadWidget(forms.HiddenInput):
    """
    Enhanced gallery widget for Django admin.

    Replaces the default JSON textarea with a visual gallery grid
    that supports multi-file upload, preview, and reordering.

    The widget stores a JSON array of URL strings (compatible with JSONField).
    File uploads are handled via AJAX to /admin/api/upload/.
    """

    template_name = 'admin/widgets/gallery_upload.html'

    def __init__(self, attrs=None, subfolder='gallery'):
        self.subfolder = subfolder
        super().__init__(attrs=attrs)

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        # Ensure value is a JSON string for the template
        if value is None:
            json_value = '[]'
        elif isinstance(value, str):
            # Validate it's valid JSON
            try:
                json.loads(value)
                json_value = value
            except (json.JSONDecodeError, TypeError):
                json_value = '[]'
        elif isinstance(value, list):
            json_value = json.dumps(value)
        else:
            json_value = '[]'

        context['widget']['json_value'] = json_value
        context['widget']['subfolder'] = self.subfolder
        return context

    def format_value(self, value):
        """Format the value for the hidden input."""
        if value is None:
            return '[]'
        if isinstance(value, list):
            return json.dumps(value)
        if isinstance(value, str):
            try:
                json.loads(value)
                return value
            except (json.JSONDecodeError, TypeError):
                return '[]'
        return '[]'
