"""Analytics views and API for the restaurant owner portal."""

import logging
from datetime import timedelta

from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Count, Sum
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_GET

logger = logging.getLogger(__name__)


def _get_org(request):
    return getattr(request.user, 'organization', None)


@login_required(login_url='/account/login/')
def analytics_overview(request):
    """Main analytics page with charts."""
    org = _get_org(request)
    if not org:
        return redirect('accounts:profile')
    return render(request, 'accounts/analytics/overview.html')


@login_required(login_url='/account/login/')
@require_GET
def analytics_qr_scans_api(request):
    """QR scan analytics with device and time breakdown."""
    org = _get_org(request)
    if not org:
        return JsonResponse({'error': 'Unauthorized'}, status=403)

    days = int(request.GET.get('days', 30))
    days = min(days, 90)
    since = timezone.now() - timedelta(days=days)

    try:
        from apps.orders.models import QRScan

        # Daily totals
        daily = []
        for i in range(days - 1, -1, -1):
            day = (timezone.now() - timedelta(days=i)).date()
            count = QRScan.objects.filter(
                organization=org, scanned_at__date=day,
            ).count()
            daily.append({'date': day.isoformat(), 'count': count})

        # Device breakdown
        devices = list(QRScan.objects.filter(
            organization=org, scanned_at__gte=since,
        ).values('device_type').annotate(count=Count('id')))

        # Peak hours
        from django.db.models.functions import ExtractHour
        hours = list(QRScan.objects.filter(
            organization=org, scanned_at__gte=since,
        ).annotate(hour=ExtractHour('scanned_at')).values('hour').annotate(count=Count('id')).order_by('hour'))

        return JsonResponse({
            'daily': daily,
            'devices': devices,
            'peak_hours': hours,
        })
    except Exception as e:
        logger.error("Analytics QR scan error: %s", str(e))
        return JsonResponse({'daily': [], 'devices': [], 'peak_hours': []})


@login_required(login_url='/account/login/')
@require_GET
def analytics_revenue_api(request):
    """Revenue analytics."""
    org = _get_org(request)
    if not org:
        return JsonResponse({'error': 'Unauthorized'}, status=403)

    days = int(request.GET.get('days', 30))
    days = min(days, 90)

    try:
        from apps.orders.models import Order

        # Daily revenue
        daily = []
        for i in range(days - 1, -1, -1):
            day = (timezone.now() - timedelta(days=i)).date()
            result = Order.objects.filter(
                organization=org, status='COMPLETED', completed_at__date=day, deleted_at__isnull=True,
            ).aggregate(total=Sum('total_amount'), avg=Avg('total_amount'), count=Count('id'))
            daily.append({
                'date': day.isoformat(),
                'total': float(result['total'] or 0),
                'avg': float(result['avg'] or 0),
                'count': result['count'],
            })

        # Payment method distribution
        payment_methods = list(Order.objects.filter(
            organization=org, status='COMPLETED', deleted_at__isnull=True,
            completed_at__gte=timezone.now() - timedelta(days=days),
        ).values('payment_method').annotate(
            count=Count('id'), total=Sum('total_amount'),
        ))

        return JsonResponse({
            'daily': daily,
            'payment_methods': [{
                'method': pm['payment_method'] or 'UNKNOWN',
                'count': pm['count'],
                'total': float(pm['total'] or 0),
            } for pm in payment_methods],
        })
    except Exception as e:
        logger.error("Analytics revenue error: %s", str(e))
        return JsonResponse({'daily': [], 'payment_methods': []})


@login_required(login_url='/account/login/')
@require_GET
def analytics_products_api(request):
    """Product performance analytics."""
    org = _get_org(request)
    if not org:
        return JsonResponse({'error': 'Unauthorized'}, status=403)

    days = int(request.GET.get('days', 30))
    since = timezone.now() - timedelta(days=days)

    try:
        from apps.orders.models import OrderItem

        # Top sellers
        top_sellers = list(OrderItem.objects.filter(
            order__organization=org, order__deleted_at__isnull=True,
            order__created_at__gte=since, deleted_at__isnull=True,
        ).values('product__name', 'product__category__name').annotate(
            total_orders=Count('id'), total_quantity=Sum('quantity'),
            total_revenue=Sum('total_price'),
        ).order_by('-total_orders')[:20])

        # Category breakdown
        categories = list(OrderItem.objects.filter(
            order__organization=org, order__deleted_at__isnull=True,
            order__created_at__gte=since, deleted_at__isnull=True,
        ).values('product__category__name').annotate(
            count=Count('id'), revenue=Sum('total_price'),
        ).order_by('-revenue')[:10])

        return JsonResponse({
            'top_sellers': [{
                'name': p['product__name'] or '-',
                'category': p['product__category__name'] or '-',
                'orders': p['total_orders'],
                'quantity': p['total_quantity'],
                'revenue': float(p['total_revenue'] or 0),
            } for p in top_sellers],
            'categories': [{
                'name': c['product__category__name'] or '-',
                'count': c['count'],
                'revenue': float(c['revenue'] or 0),
            } for c in categories],
        })
    except Exception as e:
        logger.error("Analytics products error: %s", str(e))
        return JsonResponse({'top_sellers': [], 'categories': []})


@login_required(login_url='/account/login/')
@require_GET
def analytics_customers_api(request):
    """Customer insights analytics."""
    org = _get_org(request)
    if not org:
        return JsonResponse({'error': 'Unauthorized'}, status=403)

    days = int(request.GET.get('days', 30))
    since = timezone.now() - timedelta(days=days)

    try:
        from apps.customers.models import Customer

        total = Customer.objects.filter(organization=org, deleted_at__isnull=True).count()
        new_customers = Customer.objects.filter(
            organization=org, deleted_at__isnull=True,
            created_at__gte=since,
        ).count()
        returning = Customer.objects.filter(
            organization=org, deleted_at__isnull=True,
            total_orders__gte=2,
        ).count()

        # Top spenders
        top_spenders = list(Customer.objects.filter(
            organization=org, deleted_at__isnull=True,
        ).order_by('-total_spent')[:10].values('name', 'email', 'total_orders', 'total_spent'))

        return JsonResponse({
            'total': total,
            'new_customers': new_customers,
            'returning': returning,
            'top_spenders': [{
                'name': c['name'] or c['email'] or '-',
                'orders': c['total_orders'],
                'spent': float(c['total_spent'] or 0),
            } for c in top_spenders],
        })
    except Exception as e:
        logger.error("Analytics customers error: %s", str(e))
        return JsonResponse({'total': 0, 'new_customers': 0, 'returning': 0, 'top_spenders': []})
