"""
ImageUploadWidget - Custom Django widget for single image upload.

Renders an enhanced image upload interface with:
- Image preview when URL is populated
- Drag & drop upload zone
- Browse button for file picker
- Upload progress bar
- Manual URL input fallback
- Delete button to clear the image

Works with URLField (stores URL string, not file object).
Uses Alpine.js for interactivity (already loaded in admin).
"""

from django import forms


class ImageUploadWidget(forms.URLInput):
    """
    Enhanced image upload widget for Django admin.

    Replaces the default URLInput with a visual upload interface
    that supports drag & drop, file browser, and preview.

    The widget stores a URL string (compatible with URLField).
    File uploads are handled via AJAX to /admin/api/upload/.
    """

    template_name = 'admin/widgets/image_upload.html'

    def __init__(self, attrs=None, subfolder='menu_items'):
        self.subfolder = subfolder
        default_attrs = {
            'class': 'vURLField image-upload-url-input',
        }
        if attrs:
            default_attrs.update(attrs)
        super().__init__(attrs=default_attrs)

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        context['widget']['subfolder'] = self.subfolder
        return context
