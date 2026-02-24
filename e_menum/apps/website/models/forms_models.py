"""Form submission models — ContactSubmission, DemoRequest, NewsletterSubscriber."""

from django.db import models
from django.utils.translation import gettext_lazy as _

from .base import TimeStampedModel


# =============================================================================
# CONTACT SUBMISSION
# =============================================================================

class ContactSubmission(TimeStampedModel):
    """Stores contact form submissions from /iletisim/ page."""

    class SubjectChoices(models.TextChoices):
        GENERAL = 'general', _('Genel Bilgi')
        SALES = 'sales', _('Satis')
        SUPPORT = 'support', _('Teknik Destek')
        PARTNERSHIP = 'partnership', _('Is Birligi')
        PRESS = 'press', _('Basin & Medya')
        OTHER = 'other', _('Diger')

    name = models.CharField(_('ad soyad'), max_length=100)
    email = models.EmailField(_('e-posta'))
    phone = models.CharField(_('telefon'), max_length=20, blank=True)
    subject = models.CharField(
        _('konu'),
        max_length=50,
        choices=SubjectChoices.choices,
        default=SubjectChoices.GENERAL,
    )
    message = models.TextField(_('mesaj'))
    is_read = models.BooleanField(_('okundu'), default=False)

    class Meta:
        verbose_name = _('Iletisim Formu')
        verbose_name_plural = _('Iletisim Formlari')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} — {self.get_subject_display()} ({self.created_at:%Y-%m-%d})"


# =============================================================================
# DEMO REQUEST
# =============================================================================

class DemoRequest(TimeStampedModel):
    """Stores demo request submissions from /demo/ page."""

    class BusinessTypeChoices(models.TextChoices):
        # A — Oturarak Yemek
        RESTAURANT = 'restaurant', _('Restoran')
        LOKANTA = 'lokanta', _('Lokanta / Ev Yemekleri')
        FINE_DINING = 'fine_dining', _('Fine Dining')
        MEYHANE = 'meyhane', _('Meyhane / Balik Restoran')
        STEAKHOUSE = 'steakhouse', _('Steakhouse / Izgara')
        # B — Hizli Servis
        FAST_FOOD = 'fast_food', _('Fast Food')
        KEBAB = 'kebab', _('Kebapci / Pideci / Lahmacuncu')
        DONER = 'doner', _('Donerci / Cigerci')
        BOREK = 'borek', _('Borekci / Mantici')
        # C — Pastane / Firin
        BAKERY = 'bakery', _('Pastane / Firincilik')
        # D — Icecek Odakli
        CAFE = 'cafe', _('Kafe / Kahve Dukkani')
        NARGILE = 'nargile', _('Nargile Kafe')
        PUB_BAR = 'pub_bar', _('Pub / Bar / Biraevi')
        SMOOTHIE = 'smoothie', _('Smoothie / Juice Bar')
        # E — Turist / Sezonluk
        BEACH_CLUB = 'beach_club', _('Beach Club / Havuz Bar')
        HOTEL = 'hotel', _('Otel / Tatil Koyu')
        # F — Coklu Sube
        CHAIN = 'chain', _('Zincir Isletme')
        FRANCHISE = 'franchise', _('Franchise')
        # G — Kurumsal
        CATERING = 'catering', _('Catering / Toplu Yemek')
        KANTIN = 'kantin', _('Kantin / Yemekhane')
        FOOD_COURT = 'food_court', _('Food Court')
        # Genel
        OTHER = 'other', _('Diger')

    class StatusChoices(models.TextChoices):
        PENDING = 'pending', _('Beklemede')
        CONTACTED = 'contacted', _('Iletisime Gecildi')
        DEMO_DONE = 'demo_done', _('Demo Yapildi')
        CONVERTED = 'converted', _('Musteri Oldu')
        REJECTED = 'rejected', _('Vazgecti')

    name = models.CharField(_('ad soyad'), max_length=100)
    business_name = models.CharField(_('isletme adi'), max_length=200)
    email = models.EmailField(_('e-posta'))
    phone = models.CharField(_('telefon'), max_length=20)
    business_type = models.CharField(
        _('isletme tipi'),
        max_length=50,
        choices=BusinessTypeChoices.choices,
        default=BusinessTypeChoices.RESTAURANT,
    )
    branch_count = models.PositiveIntegerField(_('sube sayisi'), default=1)
    message = models.TextField(_('mesaj'), blank=True)
    status = models.CharField(
        _('durum'),
        max_length=20,
        choices=StatusChoices.choices,
        default=StatusChoices.PENDING,
    )
    notes = models.TextField(_('admin notlari'), blank=True)

    class Meta:
        verbose_name = _('Demo Talebi')
        verbose_name_plural = _('Demo Talepleri')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.business_name} — {self.name} ({self.get_status_display()})"


# =============================================================================
# NEWSLETTER SUBSCRIBER
# =============================================================================

class NewsletterSubscriber(TimeStampedModel):
    """Stores newsletter email subscriptions."""

    email = models.EmailField(_('e-posta'), unique=True)
    is_active = models.BooleanField(_('aktif'), default=True)
    language = models.CharField(_('dil'), max_length=5, default='tr')

    class Meta:
        verbose_name = _('Bulten Abonesi')
        verbose_name_plural = _('Bulten Aboneleri')
        ordering = ['-created_at']

    def __str__(self):
        status = 'aktif' if self.is_active else 'pasif'
        return f"{self.email} ({status})"
