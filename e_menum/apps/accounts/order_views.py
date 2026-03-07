"""Order management views for the restaurant owner portal."""

import json
import logging

from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_POST

logger = logging.getLogger(__name__)


def _get_org(request):
    return getattr(request.user, 'organization', None)


@login_required(login_url='/account/login/')
def order_list(request):
    """List orders with filters."""
    org = _get_org(request)
    if not org:
        return redirect('accounts:profile')
    from apps.orders.models import Order

    qs = Order.objects.filter(
        organization=org,
        deleted_at__isnull=True,
    ).select_related('table').order_by('-created_at')

    # Filter by status
    status = request.GET.get('status')
    if status:
        qs = qs.filter(status=status)

    # Filter by type
    order_type = request.GET.get('type')
    if order_type:
        qs = qs.filter(type=order_type)

    # Search by order number
    search = request.GET.get('q', '').strip()
    if search:
        qs = qs.filter(order_number__icontains=search)

    paginator = Paginator(qs, 20)
    page = paginator.get_page(request.GET.get('page', 1))

    # Status choices for filter
    status_choices = ['PENDING', 'CONFIRMED', 'PREPARING', 'READY', 'DELIVERED', 'COMPLETED', 'CANCELLED']

    return render(request, 'accounts/orders/list.html', {
        'orders': page,
        'status_choices': status_choices,
        'current_status': status,
        'current_type': order_type,
        'search': search,
    })


@login_required(login_url='/account/login/')
def order_detail(request, order_id):
    """Order detail with items and status timeline."""
    org = _get_org(request)
    if not org:
        return redirect('accounts:profile')
    from apps.orders.models import Order

    order = get_object_or_404(
        Order.objects.select_related('table'),
        id=order_id, organization=org, deleted_at__isnull=True,
    )
    items = order.items.filter(deleted_at__isnull=True).select_related('product')

    # Determine available next status transitions
    transitions = _get_transitions(order.status)

    return render(request, 'accounts/orders/detail.html', {
        'order': order,
        'items': items,
        'transitions': transitions,
    })


@login_required(login_url='/account/login/')
@require_POST
def order_update_status(request, order_id):
    """Update order status (AJAX)."""
    org = _get_org(request)
    if not org:
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    from apps.orders.models import Order

    order = get_object_or_404(Order, id=order_id, organization=org, deleted_at__isnull=True)

    try:
        body = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    action = body.get('action', '')
    valid_actions = {
        'confirm': 'CONFIRMED',
        'prepare': 'PREPARING',
        'ready': 'READY',
        'deliver': 'DELIVERED',
        'complete': 'COMPLETED',
        'cancel': 'CANCELLED',
    }

    if action not in valid_actions:
        return JsonResponse({'error': f'Invalid action: {action}'}, status=400)

    try:
        new_status = valid_actions[action]
        order.status = new_status
        # Set timestamps
        from django.utils import timezone
        now = timezone.now()
        timestamp_map = {
            'CONFIRMED': 'confirmed_at',
            'PREPARING': 'preparing_at',
            'READY': 'ready_at',
            'DELIVERED': 'delivered_at',
            'COMPLETED': 'completed_at',
            'CANCELLED': 'cancelled_at',
        }
        ts_field = timestamp_map.get(new_status)
        if ts_field and hasattr(order, ts_field):
            setattr(order, ts_field, now)
        order.save()
        logger.info("Order %s status changed to %s by %s", order.order_number, new_status, request.user.email)
        return JsonResponse({'success': True, 'status': new_status})
    except Exception as e:
        logger.error("Order status change failed: %s", str(e))
        return JsonResponse({'error': str(e)}, status=400)


@login_required(login_url='/account/login/')
@require_GET
def order_api(request):
    """JSON endpoint for polling orders (15s interval)."""
    org = _get_org(request)
    if not org:
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    from apps.orders.models import Order

    qs = Order.objects.filter(
        organization=org,
        deleted_at__isnull=True,
        status__in=['PENDING', 'CONFIRMED', 'PREPARING', 'READY'],
    ).select_related('table').order_by('-created_at')[:50]

    orders = [{
        'id': str(o.id),
        'order_number': o.order_number,
        'status': o.status,
        'type': o.type,
        'total_amount': float(o.total_amount) if o.total_amount else 0,
        'customer_name': o.customer_name or '-',
        'table_name': o.table.name if o.table else '-',
        'created_at': o.created_at.isoformat() if o.created_at else '',
        'item_count': o.items.filter(deleted_at__isnull=True).count(),
    } for o in qs]

    return JsonResponse({'orders': orders})


def _get_transitions(current_status):
    """Get available status transitions for an order."""
    transitions_map = {
        'PENDING': [('confirm', 'Onayla', 'ph-check-circle', 'bg-blue-600 hover:bg-blue-700'), ('cancel', 'Iptal', 'ph-x-circle', 'bg-red-600 hover:bg-red-700')],
        'CONFIRMED': [('prepare', 'Hazirlaniyor', 'ph-cooking-pot', 'bg-purple-600 hover:bg-purple-700'), ('cancel', 'Iptal', 'ph-x-circle', 'bg-red-600 hover:bg-red-700')],
        'PREPARING': [('ready', 'Hazir', 'ph-bell', 'bg-cyan-600 hover:bg-cyan-700')],
        'READY': [('deliver', 'Teslim', 'ph-package', 'bg-teal-600 hover:bg-teal-700')],
        'DELIVERED': [('complete', 'Tamamla', 'ph-check', 'bg-green-600 hover:bg-green-700')],
    }
    return transitions_map.get(current_status, [])
