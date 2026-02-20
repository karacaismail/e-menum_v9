"""
Public views for the Menu application (SSR - Server-Side Rendered).

These views render HTML templates for public menu display.
No authentication required — accessible to anonymous users via QR codes.

URL Pattern:
    /m/<menu_slug>/     - Public menu display
    /m/<menu_slug>/<category_slug>/  - Category-specific view (optional)

Features:
- No authentication required (AllowAny)
- Renders full HTML with menu data for SEO/SSR
- Caches menu data for performance
- Handles 404 gracefully with user-friendly error page

Usage:
    from apps.menu.public_views import PublicMenuView

    urlpatterns = [
        path('m/<slug:menu_slug>/', PublicMenuView.as_view(), name='public-menu'),
    ]
"""

import logging

from django.shortcuts import render, get_object_or_404
from django.http import Http404
from django.views import View
from django.utils.translation import gettext_lazy as _

from apps.menu.models import Menu, Category, Product

logger = logging.getLogger(__name__)


class PublicMenuView(View):
    """
    Public menu display view.

    SSR view that renders the full menu HTML for customers who scan a QR code.
    No authentication required.

    GET /m/<menu_slug>/

    Context passed to template:
        menu:       Menu instance
        categories: List of active categories with their products
        organization: Organization data (name, logo, settings)
    """

    template_name = 'public/menu.html'

    def get(self, request, menu_slug, *args, **kwargs):
        """
        Render the public menu page.

        Args:
            request: HTTP request
            menu_slug: URL slug of the menu to display

        Returns:
            Rendered HTML page or 404
        """
        # Fetch published menu by slug
        try:
            menu = Menu.objects.select_related(
                'organization',
                'theme',
            ).get(
                slug=menu_slug,
                is_published=True,
                deleted_at__isnull=True,
            )
        except Menu.DoesNotExist:
            logger.warning("Public menu not found: slug=%s", menu_slug)
            raise Http404(_('Menu not found'))

        organization = menu.organization

        # Fetch active categories with products
        categories = Category.objects.filter(
            menu=menu,
            is_active=True,
            deleted_at__isnull=True,
        ).prefetch_related(
            'products',
        ).order_by('sort_order', 'name')

        # Build categories with products list
        categories_with_products = []
        for category in categories:
            products = Product.objects.filter(
                category=category,
                is_active=True,
                deleted_at__isnull=True,
            ).prefetch_related(
                'variants',
                'modifiers',
                'product_allergens__allergen',
            ).order_by('sort_order', 'name')

            if products.exists():
                categories_with_products.append({
                    'category': category,
                    'products': products,
                })

        context = {
            'menu': menu,
            'organization': organization,
            'categories': categories_with_products,
            'theme': menu.theme,
            'page_title': f"{menu.name} - {organization.name}",
            'page_description': menu.description or f"Digital menu of {organization.name}",
        }

        logger.info(
            "Public menu viewed: slug=%s, org=%s",
            menu_slug,
            organization.name
        )

        return render(request, self.template_name, context)


class PublicMenuDetailView(View):
    """
    Public menu product detail view.

    Displays detailed information about a specific product.
    No authentication required.

    GET /m/<menu_slug>/product/<product_id>/
    """

    template_name = 'public/menu_detail.html'

    def get(self, request, menu_slug, product_id=None, *args, **kwargs):
        """Render the product detail page."""
        try:
            menu = Menu.objects.select_related(
                'organization',
                'theme',
            ).get(
                slug=menu_slug,
                is_published=True,
                deleted_at__isnull=True,
            )
        except Menu.DoesNotExist:
            raise Http404(_('Menu not found'))

        if product_id:
            try:
                product = Product.objects.select_related(
                    'category',
                    'category__menu',
                ).prefetch_related(
                    'variants',
                    'modifiers',
                    'product_allergens__allergen',
                    'nutrition_info',
                ).get(
                    id=product_id,
                    category__menu=menu,
                    is_active=True,
                    deleted_at__isnull=True,
                )
            except Product.DoesNotExist:
                raise Http404(_('Product not found'))
        else:
            product = None

        context = {
            'menu': menu,
            'organization': menu.organization,
            'product': product,
            'theme': menu.theme,
            'page_title': f"{product.name if product else menu.name} - {menu.organization.name}",
        }

        return render(request, self.template_name, context)


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    'PublicMenuView',
    'PublicMenuDetailView',
]
