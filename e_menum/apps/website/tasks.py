"""
Celery tasks for website form email notifications.

Tasks:
    send_contact_notification      — Sends email to admin + confirmation to user
    send_demo_request_notification — Sends email to admin + confirmation to user
"""

import logging
import re

from celery import shared_task
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.translation import gettext as _

logger = logging.getLogger(__name__)


def _send_html_email(subject, template_name, context, recipient_list, from_email=None):
    """
    Send an HTML email with plain-text fallback.

    Uses Django template rendering for HTML body and strips tags for plain text.
    Works with any EMAIL_BACKEND (console, SMTP, Anymail/Mailgun).
    """
    from_email = from_email or settings.DEFAULT_FROM_EMAIL

    # Add site_url to context for links in templates
    context.setdefault("site_url", getattr(settings, "SITE_URL", "https://e-menum.net"))

    html_body = render_to_string(template_name, context)

    # Simple plain-text fallback: strip HTML tags
    plain_body = re.sub(r"<[^>]+>", "", html_body)
    plain_body = re.sub(r"\n{3,}", "\n\n", plain_body).strip()

    msg = EmailMultiAlternatives(
        subject=subject,
        body=plain_body,
        from_email=from_email,
        to=recipient_list,
    )
    msg.attach_alternative(html_body, "text/html")
    msg.send(fail_silently=False)


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    name="website.send_contact_notification",
)
def send_contact_notification(self, submission_id: str):
    """
    Send email notification to admin + confirmation to user
    when a new contact form is submitted.

    Args:
        submission_id: UUID of the ContactSubmission record.
    """
    from .models import ContactSubmission

    try:
        submission = ContactSubmission.objects.get(id=submission_id)
    except ContactSubmission.DoesNotExist:
        logger.error("ContactSubmission %s not found — skipping email", submission_id)
        return

    admin_email = getattr(settings, "WEBSITE_ADMIN_EMAIL", settings.DEFAULT_FROM_EMAIL)
    context = {"submission": submission}

    try:
        # 1) Admin notification
        admin_subject = _("[E-Menum] Yeni Iletisim Formu: %(name)s — %(topic)s") % {
            "name": submission.name,
            "topic": submission.get_subject_display(),
        }
        _send_html_email(
            subject=admin_subject,
            template_name="emails/contact_admin.html",
            context=context,
            recipient_list=[admin_email],
        )
        logger.info("Contact admin notification sent for %s", submission_id)

        # 2) User confirmation
        user_subject = _("Mesajiniz Alindi — E-Menum")
        _send_html_email(
            subject=user_subject,
            template_name="emails/contact_confirmation.html",
            context=context,
            recipient_list=[submission.email],
        )
        logger.info("Contact confirmation sent to %s", submission.email)

    except Exception as exc:
        logger.exception("Failed to send contact emails for %s", submission_id)
        raise self.retry(exc=exc)


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    name="website.send_demo_request_notification",
)
def send_demo_request_notification(self, demo_request_id: str):
    """
    Send email notification to admin + confirmation to user
    when a new demo is requested.

    Args:
        demo_request_id: UUID of the DemoRequest record.
    """
    from .models import DemoRequest

    try:
        demo_request = DemoRequest.objects.get(id=demo_request_id)
    except DemoRequest.DoesNotExist:
        logger.error("DemoRequest %s not found — skipping email", demo_request_id)
        return

    admin_email = getattr(settings, "WEBSITE_ADMIN_EMAIL", settings.DEFAULT_FROM_EMAIL)
    context = {"demo_request": demo_request}

    try:
        # 1) Admin notification
        admin_subject = _("[E-Menum] Yeni Demo Talebi: %(business)s (%(type)s)") % {
            "business": demo_request.business_name,
            "type": demo_request.get_business_type_display(),
        }
        _send_html_email(
            subject=admin_subject,
            template_name="emails/demo_request_admin.html",
            context=context,
            recipient_list=[admin_email],
        )
        logger.info("Demo admin notification sent for %s", demo_request_id)

        # 2) User confirmation
        user_subject = _("Demo Talebiniz Alindi — E-Menum")
        _send_html_email(
            subject=user_subject,
            template_name="emails/demo_request_confirmation.html",
            context=context,
            recipient_list=[demo_request.email],
        )
        logger.info("Demo confirmation sent to %s", demo_request.email)

    except Exception as exc:
        logger.exception("Failed to send demo emails for %s", demo_request_id)
        raise self.retry(exc=exc)
