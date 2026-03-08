"""
Forms for website marketing pages.

ContactForm     — /iletisim/ contact page
DemoRequestForm — /demo/ demo request page
NewsletterForm  — Footer newsletter signup
"""

from django import forms
from django.utils.translation import gettext_lazy as _

from shared.widgets import ImageUploadWidget

from .models import ContactSubmission, DemoRequest, NewsletterSubscriber


class ContactForm(forms.ModelForm):
    """Contact form with honeypot spam protection."""

    # Honeypot field — hidden, bots fill it, humans don't
    website = forms.CharField(required=False, widget=forms.HiddenInput())

    class Meta:
        model = ContactSubmission
        fields = ["name", "email", "phone", "subject", "message"]
        widgets = {
            "name": forms.TextInput(
                attrs={
                    "class": "w-full px-4 py-3 rounded-xl border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-primary-500 focus:border-transparent",
                    "placeholder": _("Adiniz Soyadiniz"),
                }
            ),
            "email": forms.EmailInput(
                attrs={
                    "class": "w-full px-4 py-3 rounded-xl border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-primary-500 focus:border-transparent",
                    "placeholder": _("ornek@email.com"),
                }
            ),
            "phone": forms.TextInput(
                attrs={
                    "class": "w-full px-4 py-3 rounded-xl border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-primary-500 focus:border-transparent",
                    "placeholder": _("0555 123 4567"),
                }
            ),
            "subject": forms.Select(
                attrs={
                    "class": "w-full px-4 py-3 rounded-xl border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-primary-500 focus:border-transparent",
                }
            ),
            "message": forms.Textarea(
                attrs={
                    "class": "w-full px-4 py-3 rounded-xl border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-primary-500 focus:border-transparent",
                    "rows": 5,
                    "placeholder": _("Mesajinizi yazin..."),
                }
            ),
        }

    def clean(self):
        cleaned_data = super().clean()
        # Honeypot check — if filled, it's a bot
        if cleaned_data.get("website"):
            raise forms.ValidationError(_("Spam algilandi."))
        return cleaned_data


class DemoRequestForm(forms.ModelForm):
    """Demo request form with honeypot spam protection."""

    website = forms.CharField(required=False, widget=forms.HiddenInput())

    class Meta:
        model = DemoRequest
        fields = [
            "name",
            "business_name",
            "email",
            "phone",
            "business_type",
            "branch_count",
            "message",
        ]
        widgets = {
            "name": forms.TextInput(
                attrs={
                    "class": "w-full px-4 py-3 rounded-xl border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-primary-500 focus:border-transparent",
                    "placeholder": _("Adiniz Soyadiniz"),
                }
            ),
            "business_name": forms.TextInput(
                attrs={
                    "class": "w-full px-4 py-3 rounded-xl border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-primary-500 focus:border-transparent",
                    "placeholder": _("Isletme adi"),
                }
            ),
            "email": forms.EmailInput(
                attrs={
                    "class": "w-full px-4 py-3 rounded-xl border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-primary-500 focus:border-transparent",
                    "placeholder": _("ornek@email.com"),
                }
            ),
            "phone": forms.TextInput(
                attrs={
                    "class": "w-full px-4 py-3 rounded-xl border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-primary-500 focus:border-transparent",
                    "placeholder": _("0555 123 4567"),
                }
            ),
            "business_type": forms.Select(
                attrs={
                    "class": "w-full px-4 py-3 rounded-xl border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-primary-500 focus:border-transparent",
                }
            ),
            "branch_count": forms.NumberInput(
                attrs={
                    "class": "w-full px-4 py-3 rounded-xl border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-primary-500 focus:border-transparent",
                    "min": 1,
                    "max": 500,
                }
            ),
            "message": forms.Textarea(
                attrs={
                    "class": "w-full px-4 py-3 rounded-xl border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-primary-500 focus:border-transparent",
                    "rows": 4,
                    "placeholder": _("Eklemek istediginiz bir not var mi?"),
                }
            ),
        }

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get("website"):
            raise forms.ValidationError(_("Spam algilandi."))
        return cleaned_data


class NewsletterForm(forms.ModelForm):
    """Simple newsletter signup form."""

    class Meta:
        model = NewsletterSubscriber
        fields = ["email"]
        widgets = {
            "email": forms.EmailInput(
                attrs={
                    "class": "w-full px-4 py-3 rounded-xl border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-primary-500 focus:border-transparent",
                    "placeholder": _("E-posta adresiniz"),
                }
            ),
        }


# =============================================================================
# ADMIN FORMS
# =============================================================================


class SiteSettingsAdminForm(forms.ModelForm):
    """SiteSettings admin form with image upload widgets for logo fields."""

    class Meta:
        from .models import SiteSettings

        model = SiteSettings
        fields = "__all__"
        widgets = {
            "logo_url": ImageUploadWidget(subfolder="site_assets"),
            "logo_icon_url": ImageUploadWidget(subfolder="site_assets"),
            "logo_dark_url": ImageUploadWidget(subfolder="site_assets"),
            "favicon_url": ImageUploadWidget(subfolder="site_assets"),
        }


class BlogPostAdminForm(forms.ModelForm):
    """BlogPost admin form with image upload widget for cover image."""

    class Meta:
        from .models import BlogPost

        model = BlogPost
        fields = "__all__"
        widgets = {
            "cover_image_url": ImageUploadWidget(subfolder="site_assets"),
        }
