"""QR code management views for the restaurant owner portal."""

import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_POST

logger = logging.getLogger(__name__)

# MIME types for QR downloads
DOWNLOAD_CONTENT_TYPES = {
    'png': 'image/png',
    'svg': 'image/svg+xml',
    'jpg': 'image/jpeg',
    'pdf': 'application/pdf',
}

PRINT_SIZE_LABELS = {
    '10x20cm': '10x20 cm',
    'A5': 'A5',
    'A4': 'A4',
    '15x30cm': '15x30 cm',
    '20x40cm': '20x40 cm',
}


def _get_org(request):
    return getattr(request.user, 'organization', None)


@login_required(login_url='/account/login/')
def qrcode_list(request):
    """List all QR codes."""
    org = _get_org(request)
    if not org:
        return redirect('accounts:profile')
    from apps.orders.models import QRCode

    qs = QRCode.objects.filter(
        organization=org, deleted_at__isnull=True,
    ).select_related('menu', 'table').order_by('-created_at')

    # Filter by type
    qr_type = request.GET.get('type')
    if qr_type:
        qs = qs.filter(type=qr_type)

    return render(request, 'accounts/qrcodes/list.html', {
        'qrcodes': qs[:100],
        'current_type': qr_type,
    })


@login_required(login_url='/account/login/')
def qrcode_detail(request, qr_id):
    """QR code detail with scan analytics."""
    org = _get_org(request)
    if not org:
        return redirect('accounts:profile')
    from apps.orders.models import QRCode, QRScan

    qr = get_object_or_404(QRCode, id=qr_id, organization=org, deleted_at__isnull=True)
    scans = QRScan.objects.filter(qr_code=qr).order_by('-scanned_at')[:50]
    total_scans = QRScan.objects.filter(qr_code=qr).count()
    unique_scans = QRScan.objects.filter(qr_code=qr, is_unique=True).count()

    # Device breakdown
    from django.db.models import Count
    device_stats = QRScan.objects.filter(qr_code=qr).values('device_type').annotate(count=Count('id'))

    return render(request, 'accounts/qrcodes/detail.html', {
        'qr': qr,
        'scans': scans,
        'total_scans': total_scans,
        'unique_scans': unique_scans,
        'device_stats': list(device_stats),
        'download_formats': DOWNLOAD_CONTENT_TYPES,
        'download_sizes': [128, 256, 512, 1024],
        'print_sizes': PRINT_SIZE_LABELS,
    })


@login_required(login_url='/account/login/')
@require_POST
def qrcode_create(request):
    """Generate a new QR code."""
    org = _get_org(request)
    if not org:
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    from apps.orders.models import QRCode
    import uuid

    qr_type = request.POST.get('type', 'MENU')
    name = request.POST.get('name', '').strip()
    menu_id = request.POST.get('menu_id')
    table_id = request.POST.get('table_id')

    code = str(uuid.uuid4())[:8].upper()

    qr = QRCode(
        organization=org,
        type=qr_type,
        code=code,
        name=name or f'QR-{code}',
        is_active=True,
    )
    if menu_id:
        qr.menu_id = menu_id
    if table_id:
        qr.table_id = table_id
    qr.save()
    messages.success(request, _('QR kod olusturuldu.'))
    return redirect('accounts:qrcode-detail', qr_id=qr.id)


@login_required(login_url='/account/login/')
@require_POST
def qrcode_toggle(request, qr_id):
    """Activate/deactivate a QR code (AJAX)."""
    org = _get_org(request)
    if not org:
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    from apps.orders.models import QRCode
    qr = get_object_or_404(QRCode, id=qr_id, organization=org, deleted_at__isnull=True)
    qr.is_active = not qr.is_active
    qr.save(update_fields=['is_active', 'updated_at'])
    return JsonResponse({'success': True, 'is_active': qr.is_active})


@login_required(login_url='/account/login/')
def qrcode_download(request, qr_id):
    """Download QR code in specified format and size.

    Query params:
        format: png | svg | jpg | pdf (default: png)
        size: 128 | 256 | 512 | 1024 (default: 512)
    """
    org = _get_org(request)
    if not org:
        return redirect('accounts:profile')
    from apps.orders.models import QRCode
    from apps.orders.services.qr_generator import QRGeneratorService

    qr = get_object_or_404(QRCode, id=qr_id, organization=org, deleted_at__isnull=True)

    fmt = request.GET.get('format', 'png').lower()
    if fmt not in DOWNLOAD_CONTENT_TYPES:
        fmt = 'png'

    try:
        size = int(request.GET.get('size', 512))
    except (ValueError, TypeError):
        size = 512
    if size not in (128, 256, 512, 1024):
        size = 512

    buf = QRGeneratorService.download_qr(qr, format=fmt, size=size)

    content_type = DOWNLOAD_CONTENT_TYPES[fmt]
    filename = f'qr_{qr.code}_{size}px.{fmt}'

    response = HttpResponse(buf.read(), content_type=content_type)
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


@login_required(login_url='/account/login/')
def qrcode_download_print(request, qr_id):
    """Download print-ready PDF design.

    Query params:
        design_size: 10x20cm | A5 | A4 | 15x30cm | 20x40cm (default: A4)
    """
    org = _get_org(request)
    if not org:
        return redirect('accounts:profile')
    from apps.orders.models import QRCode
    from apps.orders.services.qr_generator import QRGeneratorService

    qr = get_object_or_404(QRCode, id=qr_id, organization=org, deleted_at__isnull=True)

    design_size = request.GET.get('design_size', 'A4')
    if design_size not in PRINT_SIZE_LABELS:
        design_size = 'A4'

    buf = QRGeneratorService.download_print_design(qr, design_size=design_size)

    filename = f'qr_{qr.code}_print_{design_size}.pdf'
    response = HttpResponse(buf.read(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response
