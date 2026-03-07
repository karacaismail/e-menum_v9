"""
Custom Django form widgets for E-Menum admin.

Provides enhanced widgets for image upload and gallery management
that integrate with the admin's dark theme and Alpine.js interactivity.

Widgets:
- ImageUploadWidget: Single image upload with preview, drag & drop
- GalleryUploadWidget: Multi-image gallery with grid preview

Usage:
    from shared.widgets import ImageUploadWidget, GalleryUploadWidget

    class ProductAdminForm(forms.ModelForm):
        class Meta:
            widgets = {
                'image': ImageUploadWidget(),
                'gallery': GalleryUploadWidget(),
            }
"""

from shared.widgets.image_upload import ImageUploadWidget
from shared.widgets.gallery_upload import GalleryUploadWidget

__all__ = [
    "ImageUploadWidget",
    "GalleryUploadWidget",
]
