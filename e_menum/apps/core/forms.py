"""
Admin form classes for the Core application.

Provides custom form classes that use enhanced widgets
for image upload (e.g. Organization logo).
"""

from django import forms

from apps.core.models import Organization
from shared.widgets import ImageUploadWidget


class OrganizationAdminForm(forms.ModelForm):
    """
    Custom admin form for Organization model.

    Replaces the default URLField text input for 'logo'
    with an ImageUploadWidget.
    """

    class Meta:
        model = Organization
        fields = '__all__'
        widgets = {
            'logo': ImageUploadWidget(subfolder='logos'),
        }
