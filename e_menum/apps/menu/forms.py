"""
Admin form classes for the Menu application.

Provides custom form classes that use enhanced widgets
for image upload and gallery management.
"""

from django import forms

from apps.menu.models import Category, Product
from shared.widgets import GalleryUploadWidget, ImageUploadWidget


class ProductAdminForm(forms.ModelForm):
    """
    Custom admin form for Product model.

    Replaces the default URLField text input for 'image' with
    an ImageUploadWidget and the JSONField textarea for 'gallery'
    with a GalleryUploadWidget.
    """

    class Meta:
        model = Product
        fields = "__all__"
        widgets = {
            "image": ImageUploadWidget(subfolder="menu_items"),
            "gallery": GalleryUploadWidget(subfolder="gallery"),
        }


class CategoryAdminForm(forms.ModelForm):
    """
    Custom admin form for Category model.

    Replaces the default URLField text input for 'image'
    with an ImageUploadWidget.
    """

    class Meta:
        model = Category
        fields = "__all__"
        widgets = {
            "image": ImageUploadWidget(subfolder="categories"),
        }
