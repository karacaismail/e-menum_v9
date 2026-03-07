"""
Celery tasks for website form email notifications.

Tasks:
    send_contact_notification      — Sends email to admin when contact form submitted
    send_demo_request_notification — Sends email to admin when demo requested
"""

import logging

from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail
from django.utils.translation import gettext as _

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    name="website.send_contact_notification",
)
def send_contact_notification(self, submission_id: str):
    """
    Send email notification to admin when a new contact form is submitted.

    Args:
        submission_id: UUID of the ContactSubmission record.
    """
    from .models import ContactSubmission

    try:
        submission = ContactSubmission.objects.get(id=submission_id)
    except ContactSubmission.DoesNotExist:
        logger.error("ContactSubmission %s not found — skipping email", submission_id)
        return

    subject = _("[E-Menum] Yeni Iletisim Formu: %(name)s — %(topic)s") % {
        "name": submission.name,
        "topic": submission.get_subject_display(),
    }

    message = _(
        "Yeni iletisim formu gonderildi.\n\n"
        "Ad Soyad: %(name)s\n"
        "E-posta: %(email)s\n"
        "Telefon: %(phone)s\n"
        "Konu: %(subject)s\n"
        "Mesaj:\n%(message)s\n\n"
        "Tarih: %(date)s\n"
        "Admin panelden goruntuleyebilirsiniz."
    ) % {
        "name": submission.name,
        "email": submission.email,
        "phone": submission.phone or "-",
        "subject": submission.get_subject_display(),
        "message": submission.message,
        "date": submission.created_at.strftime("%d.%m.%Y %H:%M"),
    }

    admin_email = getattr(settings, "WEBSITE_ADMIN_EMAIL", settings.DEFAULT_FROM_EMAIL)

    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[admin_email],
            fail_silently=False,
        )
        logger.info("Contact notification sent for submission %s", submission_id)
    except Exception as exc:
        logger.exception("Failed to send contact notification for %s", submission_id)
        raise self.retry(exc=exc)


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    name="website.send_demo_request_notification",
)
def send_demo_request_notification(self, demo_request_id: str):
    """
    Send email notification to admin when a new demo is requested.

    Args:
        demo_request_id: UUID of the DemoRequest record.
    """
    from .models import DemoRequest

    try:
        demo_request = DemoRequest.objects.get(id=demo_request_id)
    except DemoRequest.DoesNotExist:
        logger.error("DemoRequest %s not found — skipping email", demo_request_id)
        return

    subject = _("[E-Menum] Yeni Demo Talebi: %(business)s (%(type)s)") % {
        "business": demo_request.business_name,
        "type": demo_request.get_business_type_display(),
    }

    message = _(
        "Yeni demo talebi alindi.\n\n"
        "Ad Soyad: %(name)s\n"
        "Isletme: %(business)s\n"
        "E-posta: %(email)s\n"
        "Telefon: %(phone)s\n"
        "Isletme Tipi: %(type)s\n"
        "Sube Sayisi: %(branches)d\n"
        "Mesaj: %(message)s\n\n"
        "Tarih: %(date)s\n"
        "Admin panelden durum takibini yapabilirsiniz."
    ) % {
        "name": demo_request.name,
        "business": demo_request.business_name,
        "email": demo_request.email,
        "phone": demo_request.phone,
        "type": demo_request.get_business_type_display(),
        "branches": demo_request.branch_count,
        "message": demo_request.message or "-",
        "date": demo_request.created_at.strftime("%d.%m.%Y %H:%M"),
    }

    admin_email = getattr(settings, "WEBSITE_ADMIN_EMAIL", settings.DEFAULT_FROM_EMAIL)

    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[admin_email],
            fail_silently=False,
        )
        logger.info("Demo request notification sent for %s", demo_request_id)
    except Exception as exc:
        logger.exception("Failed to send demo notification for %s", demo_request_id)
        raise self.retry(exc=exc)
