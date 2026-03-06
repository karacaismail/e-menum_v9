"""Forms for product management in the restaurant owner portal."""

from django import forms
from django.utils.translation import gettext_lazy as _


INPUT_CLASS = 'w-full px-4 py-3 rounded-xl border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-primary-500 focus:border-transparent'
CHECKBOX_CLASS = 'h-5 w-5 text-primary-600 border-gray-300 dark:border-gray-600 rounded focus:ring-primary-500'


class ProductForm(forms.Form):
    """Create/edit product form."""
    name = forms.CharField(max_length=200, label=_('Urun Adi'))
    short_description = forms.CharField(max_length=500, required=False, label=_('Kisa Aciklama'))
    description = forms.CharField(required=False, label=_('Detayli Aciklama'), widget=forms.Textarea(attrs={'rows': 4}))
    category = forms.UUIDField(label=_('Kategori'))
    base_price = forms.DecimalField(max_digits=10, decimal_places=2, label=_('Fiyat (TL)'))
    image = forms.URLField(required=False, label=_('Gorsel URL'))
    is_active = forms.BooleanField(required=False, initial=True, label=_('Aktif'))
    is_available = forms.BooleanField(required=False, initial=True, label=_('Mevcut'))
    is_featured = forms.BooleanField(required=False, label=_('One Cikan'))
    is_chef_recommended = forms.BooleanField(required=False, label=_('Sef Onerisi'))
    preparation_time = forms.IntegerField(required=False, label=_('Hazirlama Suresi (dk)'))
    calories = forms.IntegerField(required=False, label=_('Kalori'))
    spicy_level = forms.IntegerField(required=False, min_value=0, max_value=5, label=_('Aci Seviyesi (0-5)'))
    tags = forms.CharField(required=False, label=_('Etiketler'), help_text=_('Virgul ile ayirin'))

    def __init__(self, *args, organization=None, **kwargs):
        super().__init__(*args, **kwargs)
        # Apply Tailwind classes
        for name, field in self.fields.items():
            if isinstance(field, forms.BooleanField):
                field.widget.attrs['class'] = CHECKBOX_CLASS
            elif isinstance(field.widget, forms.Textarea):
                field.widget.attrs['class'] = INPUT_CLASS
            elif isinstance(field.widget, forms.Select):
                field.widget.attrs['class'] = INPUT_CLASS
            else:
                field.widget.attrs['class'] = INPUT_CLASS

        # Populate category choices
        if organization:
            from apps.menu.models import Category
            cats = Category.objects.filter(
                organization=organization,
                deleted_at__isnull=True,
                is_active=True,
            ).select_related('menu').order_by('menu__name', 'sort_order')
            choices = [('', _('Kategori secin'))]
            for c in cats:
                menu_name = c.menu.name if c.menu else '-'
                choices.append((str(c.id), f'{menu_name} > {c.name}'))
            self.fields['category'].widget = forms.Select(
                attrs={'class': INPUT_CLASS},
                choices=choices,
            )


class ProductVariantForm(forms.Form):
    """Inline variant form."""
    name = forms.CharField(max_length=100, label=_('Varyant Adi'))
    price = forms.DecimalField(max_digits=10, decimal_places=2, label=_('Ek Fiyat'))
    is_default = forms.BooleanField(required=False, label=_('Varsayilan'))
    is_available = forms.BooleanField(required=False, initial=True, label=_('Mevcut'))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if isinstance(field, forms.BooleanField):
                field.widget.attrs['class'] = CHECKBOX_CLASS
            else:
                field.widget.attrs['class'] = INPUT_CLASS


class ProductModifierForm(forms.Form):
    """Inline modifier form."""
    name = forms.CharField(max_length=100, label=_('Eklenti Adi'))
    price = forms.DecimalField(max_digits=10, decimal_places=2, label=_('Fiyat'))
    is_required = forms.BooleanField(required=False, label=_('Zorunlu'))
    max_quantity = forms.IntegerField(required=False, initial=1, min_value=1, label=_('Maks. Adet'))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if isinstance(field, forms.BooleanField):
                field.widget.attrs['class'] = CHECKBOX_CLASS
            else:
                field.widget.attrs['class'] = INPUT_CLASS
