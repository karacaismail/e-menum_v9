"""Product management views for the restaurant owner portal."""

import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_POST

from .product_forms import ProductForm

logger = logging.getLogger(__name__)


def _get_org(request):
    return getattr(request.user, 'organization', None)


@login_required(login_url='/account/login/')
def product_list(request):
    """List all products with search and filters."""
    org = _get_org(request)
    if not org:
        return redirect('accounts:profile')
    from apps.menu.models import Product, Category, Menu

    qs = Product.objects.filter(
        organization=org,
        deleted_at__isnull=True,
    ).select_related('category', 'category__menu').order_by('-created_at')

    # Search
    search = request.GET.get('q', '').strip()
    if search:
        qs = qs.filter(name__icontains=search)

    # Filter by menu
    menu_id = request.GET.get('menu')
    if menu_id:
        qs = qs.filter(category__menu_id=menu_id)

    # Filter by category
    cat_id = request.GET.get('category')
    if cat_id:
        qs = qs.filter(category_id=cat_id)

    # Filter by status
    status = request.GET.get('status')
    if status == 'active':
        qs = qs.filter(is_active=True)
    elif status == 'inactive':
        qs = qs.filter(is_active=False)
    elif status == 'featured':
        qs = qs.filter(is_featured=True)

    paginator = Paginator(qs, 20)
    page = paginator.get_page(request.GET.get('page', 1))

    # For filter dropdowns
    menus = Menu.objects.filter(organization=org, deleted_at__isnull=True).order_by('name')
    categories = Category.objects.filter(organization=org, deleted_at__isnull=True).order_by('name')

    return render(request, 'accounts/products/list.html', {
        'products': page,
        'menus': menus,
        'categories': categories,
        'search': search,
        'current_menu': menu_id,
        'current_category': cat_id,
        'current_status': status,
    })


@login_required(login_url='/account/login/')
def product_create(request):
    """Create a new product."""
    org = _get_org(request)
    if not org:
        return redirect('accounts:profile')
    from apps.menu.models import Product, Category

    if request.method == 'POST':
        form = ProductForm(request.POST, organization=org)
        if form.is_valid():
            cd = form.cleaned_data
            try:
                category = Category.objects.get(
                    id=cd['category'], organization=org, deleted_at__isnull=True,
                )
            except Category.DoesNotExist:
                messages.error(request, _('Gecersiz kategori.'))
                return render(request, 'accounts/products/form.html', {'form': form, 'is_edit': False})

            tags = [t.strip() for t in cd.get('tags', '').split(',') if t.strip()] if cd.get('tags') else []

            product = Product(
                organization=org,
                category=category,
                name=cd['name'],
                slug=slugify(cd['name']),
                short_description=cd.get('short_description', ''),
                description=cd.get('description', ''),
                base_price=cd['base_price'],
                image=cd.get('image', ''),
                is_active=cd.get('is_active', True),
                is_available=cd.get('is_available', True),
                is_featured=cd.get('is_featured', False),
                is_chef_recommended=cd.get('is_chef_recommended', False),
                preparation_time=cd.get('preparation_time'),
                calories=cd.get('calories'),
                spicy_level=cd.get('spicy_level', 0),
                tags=tags,
            )
            product.save()

            # Handle variants from POST data
            _save_variants(request, product)
            # Handle modifiers from POST data
            _save_modifiers(request, product)
            # Handle allergens
            _save_allergens(request, product)

            messages.success(request, _('Urun basariyla olusturuldu.'))
            return redirect('accounts:product-list')
    else:
        form = ProductForm(organization=org)

    allergens = _get_allergens()
    return render(request, 'accounts/products/form.html', {
        'form': form,
        'is_edit': False,
        'allergens': allergens,
    })


@login_required(login_url='/account/login/')
def product_detail(request, product_id):
    """Product detail page."""
    org = _get_org(request)
    if not org:
        return redirect('accounts:profile')
    from apps.menu.models import Product
    product = get_object_or_404(
        Product.objects.select_related('category', 'category__menu'),
        id=product_id, organization=org, deleted_at__isnull=True,
    )
    variants = product.variants.filter(deleted_at__isnull=True).order_by('sort_order')
    modifiers = product.modifiers.filter(deleted_at__isnull=True).order_by('sort_order')

    return render(request, 'accounts/products/detail.html', {
        'product': product,
        'variants': variants,
        'modifiers': modifiers,
    })


@login_required(login_url='/account/login/')
def product_edit(request, product_id):
    """Edit an existing product."""
    org = _get_org(request)
    if not org:
        return redirect('accounts:profile')
    from apps.menu.models import Product, Category

    product = get_object_or_404(Product, id=product_id, organization=org, deleted_at__isnull=True)

    if request.method == 'POST':
        form = ProductForm(request.POST, organization=org)
        if form.is_valid():
            cd = form.cleaned_data
            try:
                category = Category.objects.get(
                    id=cd['category'], organization=org, deleted_at__isnull=True,
                )
            except Category.DoesNotExist:
                messages.error(request, _('Gecersiz kategori.'))
                return render(request, 'accounts/products/form.html', {
                    'form': form, 'product': product, 'is_edit': True,
                })

            product.category = category
            product.name = cd['name']
            product.short_description = cd.get('short_description', '')
            product.description = cd.get('description', '')
            product.base_price = cd['base_price']
            product.image = cd.get('image', '')
            product.is_active = cd.get('is_active', True)
            product.is_available = cd.get('is_available', True)
            product.is_featured = cd.get('is_featured', False)
            product.is_chef_recommended = cd.get('is_chef_recommended', False)
            product.preparation_time = cd.get('preparation_time')
            product.calories = cd.get('calories')
            product.spicy_level = cd.get('spicy_level', 0)
            tags = [t.strip() for t in cd.get('tags', '').split(',') if t.strip()] if cd.get('tags') else []
            product.tags = tags
            product.save()

            _save_variants(request, product)
            _save_modifiers(request, product)
            _save_allergens(request, product)

            messages.success(request, _('Urun guncellendi.'))
            return redirect('accounts:product-detail', product_id=product.id)
    else:
        initial = {
            'name': product.name,
            'short_description': product.short_description,
            'description': product.description,
            'category': str(product.category_id),
            'base_price': product.base_price,
            'image': product.image,
            'is_active': product.is_active,
            'is_available': product.is_available,
            'is_featured': product.is_featured,
            'is_chef_recommended': product.is_chef_recommended,
            'preparation_time': product.preparation_time,
            'calories': product.calories,
            'spicy_level': product.spicy_level,
            'tags': ', '.join(product.tags) if product.tags else '',
        }
        form = ProductForm(initial=initial, organization=org)

    allergens = _get_allergens()
    existing_allergens = []
    try:
        from apps.menu.models import ProductAllergen
        existing_allergens = list(
            ProductAllergen.objects.filter(
                product=product, deleted_at__isnull=True,
            ).values_list('allergen_id', flat=True)
        )
    except Exception:
        pass

    return render(request, 'accounts/products/form.html', {
        'form': form,
        'product': product,
        'is_edit': True,
        'allergens': allergens,
        'existing_allergens': [str(a) for a in existing_allergens],
    })


@login_required(login_url='/account/login/')
@require_POST
def product_delete(request, product_id):
    """Soft-delete a product."""
    org = _get_org(request)
    if not org:
        return redirect('accounts:profile')
    from apps.menu.models import Product
    product = get_object_or_404(Product, id=product_id, organization=org, deleted_at__isnull=True)
    product.soft_delete()
    messages.success(request, _('Urun silindi.'))
    return redirect('accounts:product-list')


@login_required(login_url='/account/login/')
@require_POST
def product_toggle_active(request, product_id):
    """Toggle product active status (AJAX)."""
    org = _get_org(request)
    if not org:
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    from apps.menu.models import Product
    product = get_object_or_404(Product, id=product_id, organization=org, deleted_at__isnull=True)
    product.is_active = not product.is_active
    product.save(update_fields=['is_active', 'updated_at'])
    return JsonResponse({'success': True, 'is_active': product.is_active})


@login_required(login_url='/account/login/')
@require_POST
def product_toggle_featured(request, product_id):
    """Toggle product featured status (AJAX)."""
    org = _get_org(request)
    if not org:
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    from apps.menu.models import Product
    product = get_object_or_404(Product, id=product_id, organization=org, deleted_at__isnull=True)
    product.is_featured = not product.is_featured
    product.save(update_fields=['is_featured', 'updated_at'])
    return JsonResponse({'success': True, 'is_featured': product.is_featured})


# ─── Helpers ────────────────────────────────────────────────────────────────

def _get_allergens():
    try:
        from apps.menu.models import Allergen
        return list(Allergen.objects.filter(
            is_active=True, deleted_at__isnull=True,
        ).order_by('name'))
    except Exception:
        return []


def _save_variants(request, product):
    """Save variant data from POST form array fields."""
    from apps.menu.models import ProductVariant
    # Clear existing variants
    ProductVariant.objects.filter(product=product, deleted_at__isnull=True).update(
        deleted_at=product.updated_at,
    )
    # Re-create from POST
    names = request.POST.getlist('variant_name')
    prices = request.POST.getlist('variant_price')
    defaults = request.POST.getlist('variant_default')
    for i, name in enumerate(names):
        if not name.strip():
            continue
        try:
            price = float(prices[i]) if i < len(prices) else 0
        except (ValueError, IndexError):
            price = 0
        ProductVariant.objects.create(
            product=product,
            name=name.strip(),
            price=price,
            is_default=str(i) in defaults,
            is_available=True,
            sort_order=i,
        )


def _save_modifiers(request, product):
    """Save modifier data from POST form array fields."""
    from apps.menu.models import ProductModifier
    ProductModifier.objects.filter(product=product, deleted_at__isnull=True).update(
        deleted_at=product.updated_at,
    )
    names = request.POST.getlist('modifier_name')
    prices = request.POST.getlist('modifier_price')
    for i, name in enumerate(names):
        if not name.strip():
            continue
        try:
            price = float(prices[i]) if i < len(prices) else 0
        except (ValueError, IndexError):
            price = 0
        ProductModifier.objects.create(
            product=product,
            name=name.strip(),
            price=price,
            is_required=False,
            max_quantity=1,
            sort_order=i,
        )


def _save_allergens(request, product):
    """Save allergen selections from POST checkbox fields."""
    from apps.menu.models import ProductAllergen
    ProductAllergen.objects.filter(product=product, deleted_at__isnull=True).update(
        deleted_at=product.updated_at,
    )
    allergen_ids = request.POST.getlist('allergens')
    for aid in allergen_ids:
        try:
            ProductAllergen.objects.create(
                product=product,
                allergen_id=aid,
            )
        except Exception:
            pass
