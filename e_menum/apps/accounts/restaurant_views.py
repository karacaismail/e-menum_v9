"""Restaurant settings management views."""

import logging
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _

from apps.core.choices import AuditAction
from apps.core.models import AuditLog, Branch
from apps.core.views import get_client_ip

from .forms import RestaurantSettingsForm

logger = logging.getLogger(__name__)


def _get_org(request):
    return getattr(request.user, 'organization', None)


@login_required(login_url='/account/login/')
def restaurant_settings(request):
    """Restaurant settings page - edit org info and branch details."""
    org = _get_org(request)
    if not org:
        return redirect('accounts:profile')

    # Get or create main branch
    branch = Branch.objects.filter(
        organization=org, is_main=True, deleted_at__isnull=True
    ).first()

    if request.method == 'POST':
        form = RestaurantSettingsForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data

            old_name = org.name
            org.name = data['name']
            org.email = data['email']
            org.phone = data.get('phone') or ''
            org.logo = data.get('logo') or ''

            # Regenerate slug if name changed significantly
            if old_name != data['name']:
                new_slug = slugify(data['name'])[:80] or org.slug
                from apps.core.models import Organization
                if not Organization.objects.filter(slug=new_slug).exclude(pk=org.pk).exists():
                    org.slug = new_slug

            org.save()

            # Update or create main branch
            branch_data = {
                'address': data.get('address') or '',
                'city': data.get('city') or '',
                'district': data.get('district') or '',
            }
            if branch:
                for k, v in branch_data.items():
                    setattr(branch, k, v)
                branch.save()
            else:
                Branch.objects.create(
                    organization=org,
                    name=data['name'],
                    slug='main',
                    is_main=True,
                    **branch_data,
                )

            # Audit log
            AuditLog.log_action(
                action=AuditAction.SETTINGS_UPDATED,
                resource='organization',
                resource_id=str(org.id),
                user=request.user,
                organization=org,
                description=f'Restaurant settings updated by {request.user.email}',
                ip_address=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')[:500],
            )

            messages.success(request, _('Restoran ayarları güncellendi.'))
            return redirect('accounts:restaurant-settings')
    else:
        initial = {
            'name': org.name,
            'email': org.email,
            'phone': org.phone or '',
            'logo': org.logo or '',
        }
        if branch:
            initial.update({
                'address': branch.address or '',
                'city': branch.city or '',
                'district': branch.district or '',
            })
        form = RestaurantSettingsForm(initial=initial)

    return render(request, 'accounts/restaurant_settings.html', {
        'form': form,
        'organization': org,
        'branch': branch,
    })
