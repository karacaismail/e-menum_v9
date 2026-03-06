"""Subscription management action views.

Provides views for:
- Plan upgrade (POST)
- EFT/bank transfer payment information (GET)
- Subscription cancellation (POST)
- Invoice PDF download (GET)

All views require login and use the restaurant owner portal layout.
"""

import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_POST

from apps.core.choices import AuditAction
from apps.core.models import AuditLog
from apps.core.views import get_client_ip

logger = logging.getLogger(__name__)

# EFT bank transfer info
EFT_BANK_INFO = {
    'bank_name': 'Ziraat Bankası',
    'account_holder': 'E-Menum Teknoloji A.Ş.',
    'iban': 'TR00 0001 0012 3456 7890 1234 56',
    'branch_code': '1234',
    'account_number': '12345678-90',
    'currency': 'TRY',
    'reference_note': _('Lütfen açıklama kısmına organizasyon ID\'nizi yazınız.'),
}


def _get_org(request):
    """Get the organization for the current user, or None."""
    return getattr(request.user, 'organization', None)


@login_required(login_url='/account/login/')
@require_POST
def subscription_upgrade(request):
    """Upgrade/change subscription plan."""
    org = _get_org(request)
    if not org:
        return redirect('accounts:profile')

    plan_id = request.POST.get('plan_id')
    if not plan_id:
        messages.error(request, _('Plan seçimi gerekli.'))
        return redirect('accounts:subscription')

    from apps.subscriptions.models import Plan, Subscription

    plan = get_object_or_404(Plan, id=plan_id, is_active=True, deleted_at__isnull=True)

    subscription = Subscription.objects.filter(
        organization=org, deleted_at__isnull=True,
    ).select_related('plan').order_by('-created_at').first()

    if subscription:
        try:
            old_plan_name = subscription.plan.name if subscription.plan else 'None'
            subscription.plan = plan
            subscription.current_price = plan.price_monthly
            subscription.save(update_fields=['plan', 'current_price', 'updated_at'])

            AuditLog.log_action(
                action=AuditAction.SUBSCRIPTION_UPDATED,
                resource='subscription',
                resource_id=str(subscription.id),
                user=request.user,
                organization=org,
                description=f'Plan upgraded: {old_plan_name} -> {plan.name}',
                ip_address=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')[:500],
            )

            messages.success(
                request,
                _('Planınız %(plan)s olarak güncellendi.') % {'plan': plan.name},
            )
        except Exception as e:
            logger.error(f'Subscription upgrade failed: {e}')
            messages.error(request, _('Plan güncellenirken bir hata oluştu.'))
    else:
        messages.error(request, _('Aktif abonelik bulunamadı.'))

    return redirect('accounts:subscription')


@login_required(login_url='/account/login/')
def subscription_eft_info(request):
    """Display EFT/bank transfer payment information."""
    org = _get_org(request)
    if not org:
        return redirect('accounts:profile')

    return render(request, 'accounts/subscription_eft.html', {
        'bank_info': EFT_BANK_INFO,
        'organization': org,
    })


@login_required(login_url='/account/login/')
@require_POST
def subscription_cancel(request):
    """Cancel subscription at end of current billing period."""
    org = _get_org(request)
    if not org:
        return redirect('accounts:profile')

    from apps.subscriptions.models import Subscription

    subscription = Subscription.objects.filter(
        organization=org, deleted_at__isnull=True,
    ).order_by('-created_at').first()

    if not subscription:
        messages.error(request, _('Aktif abonelik bulunamadı.'))
        return redirect('accounts:subscription')

    reason = request.POST.get('cancel_reason', '').strip()

    subscription.cancelled_at = timezone.now()
    subscription.cancel_reason = reason
    subscription.cancel_at_period_end = True
    subscription.save(update_fields=[
        'cancelled_at', 'cancel_reason', 'cancel_at_period_end', 'updated_at',
    ])

    AuditLog.log_action(
        action=AuditAction.SUBSCRIPTION_CANCELLED,
        resource='subscription',
        resource_id=str(subscription.id),
        user=request.user,
        organization=org,
        description=f'Subscription cancelled by {request.user.email}. Reason: {reason or "Not specified"}',
        ip_address=get_client_ip(request),
        user_agent=request.META.get('HTTP_USER_AGENT', '')[:500],
    )

    messages.success(request, _('Aboneliğiniz dönem sonunda iptal edilecektir.'))
    return redirect('accounts:subscription')


@login_required(login_url='/account/login/')
def invoice_download_pdf(request, invoice_id):
    """Download invoice as PDF.

    Attempts to use the dedicated invoice PDF service (xhtml2pdf-based).
    Falls back to a simple reportlab-generated PDF if the service is
    unavailable or fails.
    """
    org = _get_org(request)
    if not org:
        return redirect('accounts:profile')

    from apps.subscriptions.models import Invoice

    invoice = get_object_or_404(
        Invoice, id=invoice_id, organization=org, deleted_at__isnull=True,
    )

    # Try to generate PDF via the dedicated service
    try:
        from apps.subscriptions.services.invoice_pdf import generate_invoice_pdf
        buf = generate_invoice_pdf(invoice)
        if buf is not None:
            response = HttpResponse(buf.read(), content_type='application/pdf')
            response['Content-Disposition'] = (
                f'attachment; filename="fatura_{invoice.invoice_number}.pdf"'
            )
            return response
    except ImportError:
        pass
    except Exception as e:
        logger.warning(f'Primary invoice PDF generation failed: {e}')

    # Fallback: simple PDF with reportlab
    try:
        from io import BytesIO
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas

        buf = BytesIO()
        c = canvas.Canvas(buf, pagesize=A4)
        width, height = A4

        c.setFont('Helvetica-Bold', 18)
        c.drawString(50, height - 50, 'FATURA')

        c.setFont('Helvetica', 12)
        y = height - 100
        lines = [
            f'Fatura No: {invoice.invoice_number}',
            f'Organizasyon: {org.name}',
            f'Durum: {invoice.get_status_display()}',
            f'Tutar: {invoice.amount_total} {invoice.currency}',
            f'Tarih: {invoice.created_at.strftime("%d/%m/%Y") if invoice.created_at else "-"}',
        ]
        if invoice.period_start and invoice.period_end:
            lines.append(
                f'Donem: {invoice.period_start.strftime("%d/%m/%Y")} - '
                f'{invoice.period_end.strftime("%d/%m/%Y")}'
            )

        for line in lines:
            c.drawString(50, y, line)
            y -= 25

        c.save()
        buf.seek(0)

        response = HttpResponse(buf.read(), content_type='application/pdf')
        response['Content-Disposition'] = (
            f'attachment; filename="fatura_{invoice.invoice_number}.pdf"'
        )
        return response
    except Exception as e:
        logger.error(f'Invoice PDF generation failed (fallback): {e}')
        messages.error(request, _('PDF oluşturulurken hata oluştu.'))
        return redirect('accounts:invoices')
