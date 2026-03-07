"""Contact and demo request form views."""

import logging

from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.views.generic import FormView

from .mixins import CmsContextMixin
from ..forms import ContactForm, DemoRequestForm
from ..models import FAQ, Testimonial

logger = logging.getLogger(__name__)


class ContactView(CmsContextMixin, FormView):
    """
    Iletisim sayfasi — contact form with DB save + email notification.

    GET  -> renders contact form
    POST -> validates, saves to DB, triggers email task, shows success message
    """

    template_name = "website/contact.html"
    form_class = ContactForm
    success_url = "/iletisim/"
    page_slug = "contact"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["faqs"] = FAQ.objects.filter(
            is_active=True,
            deleted_at__isnull=True,
            page__in=["contact", "both"],
        ).order_by("sort_order")
        return context

    def form_valid(self, form):
        submission = form.save()
        logger.info(
            "New contact submission from %s (%s) — subject: %s",
            submission.name,
            submission.email,
            submission.subject,
        )

        # Trigger async email notification
        try:
            from ..tasks import send_contact_notification

            send_contact_notification.delay(str(submission.id))
        except Exception:
            logger.exception("Failed to queue contact notification email")

        messages.success(
            self.request,
            _("Mesajiniz basariyla gonderildi. En kisa surede size donecegiz."),
        )
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, _("Lutfen formdaki hatalari duzeltiniz."))
        return super().form_invalid(form)


class DemoRequestView(CmsContextMixin, FormView):
    """
    Demo talep sayfasi — demo request form with DB save + email notification.

    GET  -> renders demo request form
    POST -> validates, saves to DB, triggers email task, shows success message
    """

    template_name = "website/demo.html"
    form_class = DemoRequestForm
    success_url = "/demo/"
    page_slug = "demo"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["testimonials"] = Testimonial.objects.filter(
            is_active=True,
            deleted_at__isnull=True,
        ).order_by("sort_order")[:3]
        return context

    def form_valid(self, form):
        demo_request = form.save()
        logger.info(
            "New demo request from %s — business: %s (%s)",
            demo_request.name,
            demo_request.business_name,
            demo_request.business_type,
        )

        # Trigger async email notification
        try:
            from ..tasks import send_demo_request_notification

            send_demo_request_notification.delay(str(demo_request.id))
        except Exception:
            logger.exception("Failed to queue demo request notification email")

        messages.success(
            self.request,
            _(
                "Demo talebiniz alinmistir. Ekibimiz en kisa surede sizinle iletisime gececektir."
            ),
        )
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, _("Lutfen formdaki hatalari duzeltiniz."))
        return super().form_invalid(form)
