"""Table and zone management views for the restaurant owner portal."""

import json
import logging

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_GET, require_POST

logger = logging.getLogger(__name__)


def _get_org(request):
    return getattr(request.user, 'organization', None)


@login_required(login_url='/account/login/')
def table_management(request):
    """Zone and table management page."""
    org = _get_org(request)
    if not org:
        return redirect('accounts:profile')
    from apps.orders.models import Zone, Table

    zones = Zone.objects.filter(
        organization=org, deleted_at__isnull=True,
    ).prefetch_related('tables').order_by('sort_order', 'name')

    total_tables = Table.objects.filter(organization=org, deleted_at__isnull=True).count()
    available_tables = Table.objects.filter(organization=org, deleted_at__isnull=True, status='AVAILABLE').count()
    occupied_tables = Table.objects.filter(organization=org, deleted_at__isnull=True, status='OCCUPIED').count()

    return render(request, 'accounts/tables/management.html', {
        'zones': zones,
        'total_tables': total_tables,
        'available_tables': available_tables,
        'occupied_tables': occupied_tables,
    })


@login_required(login_url='/account/login/')
@require_POST
def zone_create(request):
    """Create a new zone (AJAX)."""
    org = _get_org(request)
    if not org:
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    from apps.orders.models import Zone
    try:
        body = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    name = body.get('name', '').strip()
    if not name:
        return JsonResponse({'error': 'Name is required'}, status=400)
    zone = Zone(
        organization=org, name=name, slug=slugify(name),
        description=body.get('description', ''),
        color=body.get('color', '#6366f1'),
        capacity=body.get('capacity', 0),
        is_active=True,
    )
    zone.save()
    return JsonResponse({'success': True, 'zone': {'id': str(zone.id), 'name': zone.name}}, status=201)


@login_required(login_url='/account/login/')
@require_POST
def zone_edit(request, zone_id):
    """Edit a zone (AJAX)."""
    org = _get_org(request)
    if not org:
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    from apps.orders.models import Zone
    zone = get_object_or_404(Zone, id=zone_id, organization=org, deleted_at__isnull=True)
    try:
        body = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    if 'name' in body:
        zone.name = body['name'].strip()
    if 'description' in body:
        zone.description = body['description']
    if 'color' in body:
        zone.color = body['color']
    if 'capacity' in body:
        zone.capacity = body['capacity']
    if 'is_active' in body:
        zone.is_active = bool(body['is_active'])
    zone.save()
    return JsonResponse({'success': True})


@login_required(login_url='/account/login/')
@require_POST
def zone_delete(request, zone_id):
    """Soft-delete a zone (AJAX)."""
    org = _get_org(request)
    if not org:
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    from apps.orders.models import Zone
    zone = get_object_or_404(Zone, id=zone_id, organization=org, deleted_at__isnull=True)
    zone.soft_delete()
    return JsonResponse({'success': True})


@login_required(login_url='/account/login/')
@require_POST
def table_create(request):
    """Create a new table (AJAX)."""
    org = _get_org(request)
    if not org:
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    from apps.orders.models import Table, Zone
    try:
        body = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    name = body.get('name', '').strip()
    zone_id = body.get('zone_id')
    if not name or not zone_id:
        return JsonResponse({'error': 'Name and zone_id are required'}, status=400)
    zone = get_object_or_404(Zone, id=zone_id, organization=org, deleted_at__isnull=True)
    table = Table(
        organization=org, zone=zone, name=name, slug=slugify(name),
        number=body.get('number', 0),
        capacity=body.get('capacity', 4),
        status='AVAILABLE', is_active=True,
    )
    table.save()
    return JsonResponse({'success': True, 'table': {'id': str(table.id), 'name': table.name}}, status=201)


@login_required(login_url='/account/login/')
@require_POST
def table_edit(request, table_id):
    """Edit a table (AJAX)."""
    org = _get_org(request)
    if not org:
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    from apps.orders.models import Table
    table = get_object_or_404(Table, id=table_id, organization=org, deleted_at__isnull=True)
    try:
        body = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    if 'name' in body:
        table.name = body['name'].strip()
    if 'capacity' in body:
        table.capacity = body['capacity']
    if 'status' in body and body['status'] in ('AVAILABLE', 'OCCUPIED', 'RESERVED'):
        table.status = body['status']
    if 'is_active' in body:
        table.is_active = bool(body['is_active'])
    table.save()
    return JsonResponse({'success': True})


@login_required(login_url='/account/login/')
@require_POST
def table_delete(request, table_id):
    """Soft-delete a table (AJAX)."""
    org = _get_org(request)
    if not org:
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    from apps.orders.models import Table
    table = get_object_or_404(Table, id=table_id, organization=org, deleted_at__isnull=True)
    table.soft_delete()
    return JsonResponse({'success': True})


@login_required(login_url='/account/login/')
@require_GET
def table_api(request):
    """JSON for table status polling (15s)."""
    org = _get_org(request)
    if not org:
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    from apps.orders.models import Zone, Table
    zones = Zone.objects.filter(organization=org, deleted_at__isnull=True).order_by('sort_order')
    data = []
    for zone in zones:
        tables = Table.objects.filter(zone=zone, deleted_at__isnull=True).order_by('sort_order', 'name')
        data.append({
            'id': str(zone.id),
            'name': zone.name,
            'color': zone.color,
            'tables': [{
                'id': str(t.id),
                'name': t.name,
                'number': t.number,
                'capacity': t.capacity,
                'status': t.status,
                'is_active': t.is_active,
            } for t in tables],
        })
    return JsonResponse({'zones': data})
