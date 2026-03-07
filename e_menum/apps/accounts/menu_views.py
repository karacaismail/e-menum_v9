"""Menu management views for the restaurant owner portal."""

import json
import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_POST

from .menu_forms import MenuForm, ThemeForm

logger = logging.getLogger(__name__)


def _get_org(request):
    """Get organization or redirect to profile."""
    org = getattr(request.user, 'organization', None)
    return org


# ─── MENU CRUD ──────────────────────────────────────────────────────────────

@login_required(login_url='/account/login/')
def menu_list(request):
    """List all menus for the organization."""
    org = _get_org(request)
    if not org:
        return redirect('accounts:profile')
    from apps.menu.models import Menu
    menus = Menu.objects.filter(
        organization=org,
        deleted_at__isnull=True,
    ).select_related('theme').order_by('sort_order', '-created_at')
    return render(request, 'accounts/menus/list.html', {'menus': menus})


@login_required(login_url='/account/login/')
def menu_create(request):
    """Create a new menu."""
    org = _get_org(request)
    if not org:
        return redirect('accounts:profile')
    from apps.menu.models import Menu, Theme

    if request.method == 'POST':
        form = MenuForm(request.POST, organization=org)
        if form.is_valid():
            theme = None
            if form.cleaned_data.get('theme'):
                try:
                    theme = Theme.objects.get(
                        id=form.cleaned_data['theme'],
                        organization=org,
                        deleted_at__isnull=True,
                    )
                except Theme.DoesNotExist:
                    pass
            menu = Menu(
                organization=org,
                name=form.cleaned_data['name'],
                slug=slugify(form.cleaned_data['name']),
                description=form.cleaned_data.get('description', ''),
                theme=theme,
            )
            menu.save()
            messages.success(request, _('Menu basariyla olusturuldu.'))
            return redirect('accounts:menu-detail', menu_id=menu.id)
    else:
        form = MenuForm(organization=org)

    return render(request, 'accounts/menus/form.html', {'form': form, 'is_edit': False})


@login_required(login_url='/account/login/')
def menu_detail(request, menu_id):
    """Menu detail — shows categories and products."""
    org = _get_org(request)
    if not org:
        return redirect('accounts:profile')
    from apps.menu.models import Menu, Category
    menu = get_object_or_404(Menu, id=menu_id, organization=org, deleted_at__isnull=True)
    categories = Category.objects.filter(
        menu=menu,
        organization=org,
        deleted_at__isnull=True,
    ).prefetch_related('products').order_by('sort_order', 'name')

    return render(request, 'accounts/menus/detail.html', {
        'menu': menu,
        'categories': categories,
    })


@login_required(login_url='/account/login/')
def menu_edit(request, menu_id):
    """Edit an existing menu."""
    org = _get_org(request)
    if not org:
        return redirect('accounts:profile')
    from apps.menu.models import Menu, Theme
    menu = get_object_or_404(Menu, id=menu_id, organization=org, deleted_at__isnull=True)

    if request.method == 'POST':
        form = MenuForm(request.POST, organization=org)
        if form.is_valid():
            menu.name = form.cleaned_data['name']
            menu.description = form.cleaned_data.get('description', '')
            theme = None
            if form.cleaned_data.get('theme'):
                try:
                    theme = Theme.objects.get(
                        id=form.cleaned_data['theme'],
                        organization=org,
                        deleted_at__isnull=True,
                    )
                except Theme.DoesNotExist:
                    pass
            menu.theme = theme
            menu.save()
            messages.success(request, _('Menu guncellendi.'))
            return redirect('accounts:menu-detail', menu_id=menu.id)
    else:
        form = MenuForm(
            initial={
                'name': menu.name,
                'description': menu.description,
                'theme': str(menu.theme_id) if menu.theme_id else '',
            },
            organization=org,
        )

    return render(request, 'accounts/menus/form.html', {
        'form': form,
        'menu': menu,
        'is_edit': True,
    })


@login_required(login_url='/account/login/')
@require_POST
def menu_delete(request, menu_id):
    """Soft-delete a menu."""
    org = _get_org(request)
    if not org:
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    from apps.menu.models import Menu
    menu = get_object_or_404(Menu, id=menu_id, organization=org, deleted_at__isnull=True)
    menu.soft_delete()
    messages.success(request, _('Menu silindi.'))
    return redirect('accounts:menu-list')


@login_required(login_url='/account/login/')
@require_POST
def menu_publish(request, menu_id):
    """Toggle menu publish status (AJAX)."""
    org = _get_org(request)
    if not org:
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    from apps.menu.models import Menu
    menu = get_object_or_404(Menu, id=menu_id, organization=org, deleted_at__isnull=True)
    if menu.is_published:
        menu.unpublish()
    else:
        menu.publish()
    menu.save()
    return JsonResponse({
        'success': True,
        'is_published': menu.is_published,
    })


@login_required(login_url='/account/login/')
@require_POST
def menu_set_default(request, menu_id):
    """Set a menu as default (AJAX)."""
    org = _get_org(request)
    if not org:
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    from apps.menu.models import Menu
    menu = get_object_or_404(Menu, id=menu_id, organization=org, deleted_at__isnull=True)
    menu.set_as_default()
    return JsonResponse({'success': True})


# ─── CATEGORY CRUD (AJAX) ──────────────────────────────────────────────────

@login_required(login_url='/account/login/')
@require_POST
def category_create(request, menu_id):
    """Create a new category in a menu (AJAX)."""
    org = _get_org(request)
    if not org:
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    from apps.menu.models import Menu, Category
    menu = get_object_or_404(Menu, id=menu_id, organization=org, deleted_at__isnull=True)

    try:
        body = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    name = body.get('name', '').strip()
    if not name:
        return JsonResponse({'error': 'Name is required'}, status=400)

    parent = None
    parent_id = body.get('parent')
    if parent_id:
        try:
            parent = Category.objects.get(
                id=parent_id, menu=menu, organization=org, deleted_at__isnull=True,
            )
        except Category.DoesNotExist:
            pass

    cat = Category(
        organization=org,
        menu=menu,
        name=name,
        slug=slugify(name),
        description=body.get('description', ''),
        icon=body.get('icon', ''),
        parent=parent,
        is_active=body.get('is_active', True),
    )
    cat.save()
    return JsonResponse({
        'success': True,
        'category': {
            'id': str(cat.id),
            'name': cat.name,
            'slug': cat.slug,
            'is_active': cat.is_active,
            'product_count': 0,
        },
    }, status=201)


@login_required(login_url='/account/login/')
@require_POST
def category_edit(request, category_id):
    """Edit a category (AJAX)."""
    org = _get_org(request)
    if not org:
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    from apps.menu.models import Category
    cat = get_object_or_404(Category, id=category_id, organization=org, deleted_at__isnull=True)

    try:
        body = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    if 'name' in body:
        cat.name = body['name'].strip()
    if 'description' in body:
        cat.description = body['description']
    if 'icon' in body:
        cat.icon = body['icon']
    if 'is_active' in body:
        cat.is_active = bool(body['is_active'])
    cat.save()
    return JsonResponse({'success': True})


@login_required(login_url='/account/login/')
@require_POST
def category_delete(request, category_id):
    """Soft-delete a category (AJAX)."""
    org = _get_org(request)
    if not org:
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    from apps.menu.models import Category
    cat = get_object_or_404(Category, id=category_id, organization=org, deleted_at__isnull=True)
    cat.soft_delete()
    return JsonResponse({'success': True})


@login_required(login_url='/account/login/')
@require_POST
def category_reorder(request, menu_id):
    """Reorder categories in a menu (AJAX)."""
    org = _get_org(request)
    if not org:
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    from apps.menu.models import Menu, Category
    get_object_or_404(Menu, id=menu_id, organization=org, deleted_at__isnull=True)

    try:
        body = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    order = body.get('order', [])
    for idx, cat_id in enumerate(order):
        Category.objects.filter(
            id=cat_id, organization=org, deleted_at__isnull=True,
        ).update(sort_order=idx)
    return JsonResponse({'success': True})


# ─── THEME CRUD ─────────────────────────────────────────────────────────────

@login_required(login_url='/account/login/')
def theme_list(request):
    """List all themes for the organization."""
    org = _get_org(request)
    if not org:
        return redirect('accounts:profile')
    from apps.menu.models import Theme
    themes = Theme.objects.filter(
        organization=org,
        deleted_at__isnull=True,
    ).order_by('-is_default', '-created_at')
    return render(request, 'accounts/themes/list.html', {'themes': themes})


@login_required(login_url='/account/login/')
def theme_create(request):
    """Create a new theme."""
    org = _get_org(request)
    if not org:
        return redirect('accounts:profile')
    from apps.menu.models import Theme

    if request.method == 'POST':
        form = ThemeForm(request.POST)
        if form.is_valid():
            theme = Theme(
                organization=org,
                name=form.cleaned_data['name'],
                slug=slugify(form.cleaned_data['name']),
                description=form.cleaned_data.get('description', ''),
                primary_color=form.cleaned_data['primary_color'],
                secondary_color=form.cleaned_data['secondary_color'],
                background_color=form.cleaned_data['background_color'],
                text_color=form.cleaned_data['text_color'],
                accent_color=form.cleaned_data['accent_color'],
                font_family=form.cleaned_data.get('font_family', 'Inter'),
                logo_position=form.cleaned_data.get('logo_position', 'left'),
            )
            theme.save()
            messages.success(request, _('Tema olusturuldu.'))
            return redirect('accounts:theme-list')
    else:
        form = ThemeForm()

    return render(request, 'accounts/themes/form.html', {'form': form, 'is_edit': False})


@login_required(login_url='/account/login/')
def theme_edit(request, theme_id):
    """Edit an existing theme."""
    org = _get_org(request)
    if not org:
        return redirect('accounts:profile')
    from apps.menu.models import Theme
    theme = get_object_or_404(Theme, id=theme_id, organization=org, deleted_at__isnull=True)

    if request.method == 'POST':
        form = ThemeForm(request.POST)
        if form.is_valid():
            for field_name in form.cleaned_data:
                if hasattr(theme, field_name):
                    setattr(theme, field_name, form.cleaned_data[field_name])
            theme.save()
            messages.success(request, _('Tema guncellendi.'))
            return redirect('accounts:theme-list')
    else:
        initial = {}
        for field_name in ThemeForm().fields:
            if hasattr(theme, field_name):
                initial[field_name] = getattr(theme, field_name)
        form = ThemeForm(initial=initial)

    return render(request, 'accounts/themes/form.html', {
        'form': form,
        'theme': theme,
        'is_edit': True,
    })


@login_required(login_url='/account/login/')
@require_POST
def theme_delete(request, theme_id):
    """Soft-delete a theme."""
    org = _get_org(request)
    if not org:
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    from apps.menu.models import Theme
    theme = get_object_or_404(Theme, id=theme_id, organization=org, deleted_at__isnull=True)
    theme.soft_delete()
    messages.success(request, _('Tema silindi.'))
    return redirect('accounts:theme-list')
