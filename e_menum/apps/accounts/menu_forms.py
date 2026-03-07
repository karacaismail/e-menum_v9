"""Forms for menu management in the restaurant owner portal."""

from django import forms
from django.utils.translation import gettext_lazy as _


class MenuForm(forms.Form):
    """Create/edit menu form."""

    name = forms.CharField(
        max_length=200,
        label=_("Menu Adi"),
        widget=forms.TextInput(
            attrs={
                "class": "w-full px-4 py-3 rounded-xl border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-primary-500 focus:border-transparent",
                "placeholder": _("ornegin: Ana Menu"),
            }
        ),
    )
    description = forms.CharField(
        required=False,
        label=_("Aciklama"),
        widget=forms.Textarea(
            attrs={
                "class": "w-full px-4 py-3 rounded-xl border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-primary-500 focus:border-transparent",
                "rows": 3,
                "placeholder": _("Menu aciklamasi (opsiyonel)"),
            }
        ),
    )
    theme = forms.UUIDField(
        required=False,
        label=_("Tema"),
        widget=forms.Select(
            attrs={
                "class": "w-full px-4 py-3 rounded-xl border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-primary-500 focus:border-transparent",
            }
        ),
    )

    def __init__(self, *args, organization=None, **kwargs):
        super().__init__(*args, **kwargs)
        if organization:
            from apps.menu.models import Theme

            themes = Theme.objects.filter(
                organization=organization,
                is_active=True,
                deleted_at__isnull=True,
            ).values_list("id", "name")
            choices = [("", _("Tema secin (opsiyonel)"))] + [
                (str(pk), name) for pk, name in themes
            ]
            self.fields["theme"].widget = forms.Select(
                attrs=self.fields["theme"].widget.attrs,
                choices=choices,
            )


class CategoryForm(forms.Form):
    """Create/edit category form."""

    name = forms.CharField(max_length=200, label=_("Kategori Adi"))
    description = forms.CharField(
        required=False, label=_("Aciklama"), widget=forms.Textarea(attrs={"rows": 2})
    )
    icon = forms.CharField(
        required=False,
        max_length=50,
        label=_("Ikon"),
        help_text=_("Phosphor icon sinifi, ornegin: ph-coffee"),
    )
    is_active = forms.BooleanField(required=False, initial=True, label=_("Aktif"))
    parent = forms.UUIDField(required=False, label=_("Ust Kategori"))


class ThemeForm(forms.Form):
    """Create/edit theme form."""

    name = forms.CharField(max_length=200, label=_("Tema Adi"))
    description = forms.CharField(
        required=False, label=_("Aciklama"), widget=forms.Textarea(attrs={"rows": 2})
    )
    primary_color = forms.CharField(
        max_length=7, initial="#1A6B5A", label=_("Ana Renk")
    )
    secondary_color = forms.CharField(
        max_length=7, initial="#22c55e", label=_("Ikincil Renk")
    )
    background_color = forms.CharField(
        max_length=7, initial="#ffffff", label=_("Arka Plan")
    )
    text_color = forms.CharField(max_length=7, initial="#0F1923", label=_("Yazi Rengi"))
    accent_color = forms.CharField(
        max_length=7, initial="#F5A623", label=_("Vurgu Rengi")
    )
    font_family = forms.CharField(
        max_length=100, initial="Inter", required=False, label=_("Font")
    )
    logo_position = forms.ChoiceField(
        choices=[("left", _("Sol")), ("center", _("Orta")), ("right", _("Sag"))],
        initial="left",
        label=_("Logo Pozisyonu"),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Apply Tailwind input classes to all fields
        input_class = "w-full px-4 py-3 rounded-xl border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-primary-500 focus:border-transparent"
        color_class = "h-12 w-full rounded-xl border border-gray-300 dark:border-gray-600 cursor-pointer"
        for name, field in self.fields.items():
            if "color" in name:
                field.widget = forms.TextInput(
                    attrs={"type": "color", "class": color_class}
                )
            elif isinstance(field.widget, forms.Textarea):
                field.widget.attrs["class"] = input_class
            elif isinstance(field.widget, forms.Select):
                field.widget.attrs["class"] = input_class
            else:
                field.widget.attrs["class"] = input_class
