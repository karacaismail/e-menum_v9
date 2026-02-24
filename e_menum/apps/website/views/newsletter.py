"""Newsletter signup view (AJAX POST)."""
import logging

from django.http import JsonResponse
from django.utils.translation import gettext_lazy as _
from django.views import View

from ..forms import NewsletterForm

logger = logging.getLogger(__name__)


class NewsletterView(View):
    """
    Newsletter signup — handles AJAX POST from footer form.

    Returns JSON response for frontend handling.
    """

    def post(self, request, *args, **kwargs):
        form = NewsletterForm(request.POST)
        if form.is_valid():
            # Check if already subscribed
            from ..models import NewsletterSubscriber
            email = form.cleaned_data['email']
            subscriber, created = NewsletterSubscriber.objects.get_or_create(
                email=email,
                defaults={
                    'is_active': True,
                    'language': request.LANGUAGE_CODE or 'tr',
                },
            )

            if not created and not subscriber.is_active:
                # Re-activate previously unsubscribed
                subscriber.is_active = True
                subscriber.save(update_fields=['is_active', 'updated_at'])
                created = True

            if created:
                logger.info('New newsletter subscriber: %s', email)
                return JsonResponse({
                    'success': True,
                    'message': str(_('Bultenimize basariyla abone oldunuz!')),
                })
            else:
                return JsonResponse({
                    'success': True,
                    'message': str(_('Bu e-posta adresi zaten abone.')),
                })
        else:
            return JsonResponse({
                'success': False,
                'message': str(_('Gecerli bir e-posta adresi giriniz.')),
                'errors': form.errors,
            }, status=400)
