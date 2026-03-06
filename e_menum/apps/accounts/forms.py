"""
Forms for the restaurant account portal.

LoginForm          — /account/login/    (email or username + password)
ProfileForm        — /account/profile/  (first_name, last_name, phone, avatar)
PasswordChangeForm — /account/settings/ (current + new + confirm password)
UsernameForm       — /account/settings/ (username setting)
"""

import re

from django import forms
from django.contrib.auth import authenticate
from django.utils.translation import gettext_lazy as _

from apps.core.models import User


# Reusable Tailwind CSS class string (matches existing website/forms.py pattern)
INPUT_CSS = (
    'w-full px-4 py-3 rounded-xl border border-gray-300 dark:border-gray-600 '
    'bg-white dark:bg-gray-800 text-gray-900 dark:text-white '
    'focus:ring-2 focus:ring-primary-500 focus:border-transparent'
)


class LoginForm(forms.Form):
    """
    Login form accepting email or username + password.

    Uses EmailOrUsernameBackend via Django's authenticate() function.
    The backend decides whether the identifier is an email or username
    based on the presence of '@'.
    """

    identifier = forms.CharField(
        label=_('E-posta veya Kullanıcı Adı'),
        max_length=254,
        widget=forms.TextInput(attrs={
            'class': INPUT_CSS,
            'placeholder': _('ornek@email.com veya kullanici_adi'),
            'autofocus': True,
            'autocomplete': 'username',
        }),
    )
    password = forms.CharField(
        label=_('Şifre'),
        widget=forms.PasswordInput(attrs={
            'class': INPUT_CSS,
            'placeholder': _('Şifreniz'),
            'autocomplete': 'current-password',
        }),
    )

    def __init__(self, request=None, *args, **kwargs):
        self.request = request
        self.user_cache = None
        super().__init__(*args, **kwargs)

    def clean(self):
        identifier = self.cleaned_data.get('identifier', '').strip()
        password = self.cleaned_data.get('password', '')

        if identifier and password:
            # authenticate() dispatches to EmailOrUsernameBackend
            self.user_cache = authenticate(
                self.request,
                username=identifier,
                password=password,
            )
            if self.user_cache is None:
                raise forms.ValidationError(
                    _('Geçersiz e-posta/kullanıcı adı veya şifre.'),
                    code='invalid_login',
                )
            elif not self.user_cache.is_active_user:
                raise forms.ValidationError(
                    _('Bu hesap askıya alınmış. Destek ile iletişime geçin.'),
                    code='inactive',
                )
        return self.cleaned_data

    def get_user(self):
        """Return the authenticated user (call after is_valid())."""
        return self.user_cache


class ProfileForm(forms.ModelForm):
    """
    Profile editing form: first name, last name, phone, avatar.

    Used on /account/profile/ page.
    """

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'phone', 'avatar']
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': INPUT_CSS,
                'placeholder': _('Adınız'),
            }),
            'last_name': forms.TextInput(attrs={
                'class': INPUT_CSS,
                'placeholder': _('Soyadınız'),
            }),
            'phone': forms.TextInput(attrs={
                'class': INPUT_CSS,
                'placeholder': _('0555 123 4567'),
            }),
            'avatar': forms.URLInput(attrs={
                'class': INPUT_CSS,
                'placeholder': _('https://...'),
            }),
        }


class PasswordChangeForm(forms.Form):
    """
    Password change form with current password verification.

    Enforces minimum 12 character requirement (matching Django settings).
    """

    current_password = forms.CharField(
        label=_('Mevcut Şifre'),
        widget=forms.PasswordInput(attrs={
            'class': INPUT_CSS,
            'autocomplete': 'current-password',
        }),
    )
    new_password = forms.CharField(
        label=_('Yeni Şifre'),
        min_length=12,
        widget=forms.PasswordInput(attrs={
            'class': INPUT_CSS,
            'autocomplete': 'new-password',
        }),
        help_text=_('En az 12 karakter olmalıdır.'),
    )
    confirm_password = forms.CharField(
        label=_('Yeni Şifre (Tekrar)'),
        widget=forms.PasswordInput(attrs={
            'class': INPUT_CSS,
            'autocomplete': 'new-password',
        }),
    )

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean_current_password(self):
        current = self.cleaned_data['current_password']
        if not self.user.check_password(current):
            raise forms.ValidationError(_('Mevcut şifre yanlış.'))
        return current

    def clean(self):
        cleaned = super().clean()
        new_pw = cleaned.get('new_password')
        confirm = cleaned.get('confirm_password')
        if new_pw and confirm and new_pw != confirm:
            raise forms.ValidationError(
                {'confirm_password': _('Şifreler eşleşmiyor.')}
            )
        if new_pw and new_pw == cleaned.get('current_password'):
            raise forms.ValidationError(
                {'new_password': _('Yeni şifre mevcut şifreden farklı olmalıdır.')}
            )
        return cleaned

    def save(self):
        """Set the new password on the user and save."""
        self.user.set_password(self.cleaned_data['new_password'])
        self.user.save(update_fields=['password', 'updated_at'])
        return self.user


class UsernameForm(forms.ModelForm):
    """
    Username setting/changing form.

    Validates: 3-30 characters, lowercase letters, digits and underscores only.
    """

    class Meta:
        model = User
        fields = ['username']
        widgets = {
            'username': forms.TextInput(attrs={
                'class': INPUT_CSS,
                'placeholder': _('kullanici_adi'),
            }),
        }

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if username:
            username = username.lower().strip()
            if not re.match(r'^[a-z0-9_]{3,30}$', username):
                raise forms.ValidationError(
                    _('Kullanıcı adı 3-30 karakter, sadece küçük harf, rakam ve alt çizgi içermelidir.')
                )
        return username or None  # Store NULL if empty


class RegistrationForm(forms.Form):
    """Self-service registration form for restaurant owners."""

    first_name = forms.CharField(
        label=_('Ad'),
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': INPUT_CSS,
            'placeholder': _('Adınız'),
        }),
    )
    last_name = forms.CharField(
        label=_('Soyad'),
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': INPUT_CSS,
            'placeholder': _('Soyadınız'),
        }),
    )
    email = forms.EmailField(
        label=_('E-posta'),
        widget=forms.EmailInput(attrs={
            'class': INPUT_CSS,
            'placeholder': _('ornek@email.com'),
        }),
    )
    phone = forms.CharField(
        label=_('Telefon'),
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            'class': INPUT_CSS,
            'placeholder': _('0555 123 4567'),
        }),
    )
    business_name = forms.CharField(
        label=_('İşletme Adı'),
        max_length=255,
        widget=forms.TextInput(attrs={
            'class': INPUT_CSS,
            'placeholder': _('Restoran / Kafe adınız'),
        }),
    )
    password = forms.CharField(
        label=_('Şifre'),
        min_length=12,
        widget=forms.PasswordInput(attrs={
            'class': INPUT_CSS,
            'placeholder': _('En az 12 karakter'),
            'autocomplete': 'new-password',
        }),
        help_text=_('En az 12 karakter olmalıdır.'),
    )
    confirm_password = forms.CharField(
        label=_('Şifre (Tekrar)'),
        widget=forms.PasswordInput(attrs={
            'class': INPUT_CSS,
            'placeholder': _('Şifrenizi tekrar giriniz'),
            'autocomplete': 'new-password',
        }),
    )

    def clean_email(self):
        email = self.cleaned_data['email'].lower().strip()
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError(_('Bu e-posta adresi zaten kayıtlı.'))
        return email

    def clean(self):
        cleaned = super().clean()
        pw = cleaned.get('password')
        confirm = cleaned.get('confirm_password')
        if pw and confirm and pw != confirm:
            raise forms.ValidationError(
                {'confirm_password': _('Şifreler eşleşmiyor.')}
            )
        return cleaned


class RestaurantSettingsForm(forms.Form):
    """Restaurant/organization settings form for owners."""

    name = forms.CharField(
        label=_('İşletme Adı'),
        max_length=255,
        widget=forms.TextInput(attrs={
            'class': INPUT_CSS,
            'placeholder': _('Restoran / Kafe adınız'),
        }),
    )
    email = forms.EmailField(
        label=_('İletişim E-posta'),
        widget=forms.EmailInput(attrs={
            'class': INPUT_CSS,
            'placeholder': _('info@restoran.com'),
        }),
    )
    phone = forms.CharField(
        label=_('Telefon'),
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            'class': INPUT_CSS,
            'placeholder': _('0212 123 4567'),
        }),
    )
    logo = forms.URLField(
        label=_('Logo URL'),
        max_length=500,
        required=False,
        widget=forms.URLInput(attrs={
            'class': INPUT_CSS,
            'placeholder': _('https://...'),
        }),
    )
    address = forms.CharField(
        label=_('Adres'),
        required=False,
        widget=forms.Textarea(attrs={
            'class': INPUT_CSS,
            'rows': 3,
            'placeholder': _('Restoran adresi'),
        }),
    )
    city = forms.CharField(
        label=_('Şehir'),
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': INPUT_CSS,
            'placeholder': _('İstanbul'),
        }),
    )
    district = forms.CharField(
        label=_('İlçe'),
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': INPUT_CSS,
            'placeholder': _('Kadıköy'),
        }),
    )
