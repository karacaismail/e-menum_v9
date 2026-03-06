"""Customer management views for the restaurant owner portal."""

import logging

from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext_lazy as _

logger = logging.getLogger(__name__)


def _get_org(request):
    return getattr(request.user, 'organization', None)


@login_required(login_url='/account/login/')
def customer_list(request):
    """List customers with search and filters."""
    org = _get_org(request)
    if not org:
        return redirect('accounts:profile')
    from apps.customers.models import Customer

    qs = Customer.objects.filter(
        organization=org, deleted_at__isnull=True,
    ).order_by('-created_at')

    search = request.GET.get('q', '').strip()
    if search:
        qs = qs.filter(name__icontains=search)

    sort = request.GET.get('sort', '-created_at')
    if sort in ('name', '-name', 'total_orders', '-total_orders', 'total_spent', '-total_spent', '-last_visit_at'):
        qs = qs.order_by(sort)

    paginator = Paginator(qs, 20)
    page = paginator.get_page(request.GET.get('page', 1))

    return render(request, 'accounts/customers/list.html', {
        'customers': page,
        'search': search,
        'current_sort': sort,
    })


@login_required(login_url='/account/login/')
def customer_detail(request, customer_id):
    """Customer detail — profile, order history, visits, feedback, loyalty."""
    org = _get_org(request)
    if not org:
        return redirect('accounts:profile')
    from apps.customers.models import Customer

    customer = get_object_or_404(Customer, id=customer_id, organization=org, deleted_at__isnull=True)

    # Order history
    orders = []
    try:
        from apps.orders.models import Order
        orders = Order.objects.filter(
            organization=org, deleted_at__isnull=True,
        ).filter(
            # Match by customer FK or customer_info email
            **({'customer': customer} if hasattr(Order, 'customer') else {})
        ).order_by('-created_at')[:20]
    except Exception:
        pass

    # Visits
    visits = []
    try:
        from apps.customers.models import CustomerVisit
        visits = CustomerVisit.objects.filter(
            customer=customer, organization=org,
        ).order_by('-visited_at')[:20]
    except Exception:
        pass

    # Feedback
    feedbacks = []
    try:
        from apps.customers.models import Feedback
        feedbacks = Feedback.objects.filter(
            customer=customer, organization=org, deleted_at__isnull=True,
        ).order_by('-created_at')[:10]
    except Exception:
        pass

    return render(request, 'accounts/customers/detail.html', {
        'customer': customer,
        'orders': orders,
        'visits': visits,
        'feedbacks': feedbacks,
    })
