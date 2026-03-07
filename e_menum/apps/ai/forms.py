"""
Admin form classes for the AI application.

Provides a custom form for AIProviderConfig with:
- Masked API key input (password field with show/hide toggle)
- Provider choices grouped by category (Text / Image)
- Encryption on save, keep-existing on blank submit
"""

from django import forms
from django.utils.translation import gettext_lazy as _

from apps.ai.models import (
    AIProviderConfig,
    ImageProvider,
    TextProvider,
)


class AIProviderConfigForm(forms.ModelForm):
    """
    Custom admin form for AIProviderConfig.

    Handles:
    - API key as a plain text input that gets encrypted on save
    - Provider choices grouped by category (Text Generation / Image Generation)
    - Masked display of existing API keys via placeholder
    """

    api_key = forms.CharField(
        required=False,
        widget=forms.PasswordInput(
            attrs={
                "class": "vTextField",
                "autocomplete": "off",
                "placeholder": _("Enter API key..."),
                "style": (
                    "font-family: monospace; padding: 8px 12px; "
                    "background: rgba(255,255,255,0.05); "
                    "border: 1px solid rgba(255,255,255,0.1); "
                    "border-radius: 6px; color: #e2e8f0; font-size: 13px;"
                ),
                "x-ref": "apiKeyInput",
            }
        ),
        label=_("API Key"),
        help_text=_(
            "Enter the API key for this provider. "
            "Leave blank to keep the existing key unchanged."
        ),
    )

    class Meta:
        model = AIProviderConfig
        fields = [
            "name",
            "category",
            "provider",
            "api_key",
            "default_model",
            "api_base_url",
            "is_active",
            "is_default",
            "priority",
            "settings",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # If editing existing provider with a key, show masked placeholder
        if self.instance and self.instance.pk and self.instance.has_api_key:
            self.fields["api_key"].widget.attrs["placeholder"] = (
                self.instance.api_key_masked
            )
            self.fields["api_key"].help_text = _(
                "Existing key is stored (%(masked)s). "
                "Enter a new key to replace it, or leave blank to keep."
            ) % {"masked": self.instance.api_key_masked}

        # Build combined provider choices grouped by category
        all_choices = [("", _("--- Select Provider ---"))]
        all_choices.append((_("Text Generation"), list(TextProvider.choices)))
        all_choices.append((_("Image Generation"), list(ImageProvider.choices)))
        self.fields["provider"].widget = forms.Select(choices=all_choices)

    def clean_api_key(self):
        """Return the raw API key value (empty string means 'keep existing')."""
        return self.cleaned_data.get("api_key", "").strip()

    def save(self, commit=True):
        instance = super().save(commit=False)

        raw_key = self.cleaned_data.get("api_key", "")
        if raw_key:
            # New key provided — encrypt and store
            instance.set_api_key(raw_key)
        # If empty, keep existing encrypted key (do nothing)

        if commit:
            instance.save()
        return instance
