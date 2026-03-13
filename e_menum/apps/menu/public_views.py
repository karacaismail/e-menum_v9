"""
Public views for the Menu application (SSR - Server-Side Rendered).

These views render HTML templates for public menu display.
No authentication required — accessible to anonymous users via QR codes.

URL Pattern:
    /m/<menu_slug>/     - Public menu display (menu-v3 UI)
    /m/<menu_slug>/product/<product_id>/  - Product detail view

Features:
- No authentication required (AllowAny)
- Renders full HTML with menu data for SEO/SSR
- Injects JSON data for Alpine.js menu-v3 frontend
- Handles 404 gracefully with user-friendly error page

Usage:
    from apps.menu.public_views import PublicMenuView

    urlpatterns = [
        path('m/<slug:menu_slug>/', PublicMenuView.as_view(), name='public-menu'),
    ]
"""

import json
import logging
from datetime import timedelta
from decimal import Decimal

from django.db.models import Prefetch
from django.http import Http404
from django.shortcuts import render
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.views import View

from apps.menu.models import (
    Allergen,
    Category,
    Menu,
    Product,
    ProductModifier,
    ProductVariant,
)

logger = logging.getLogger(__name__)


class DecimalEncoder(json.JSONEncoder):
    """JSON encoder that handles Decimal types."""

    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super().default(obj)


class PublicMenuView(View):
    """
    Public menu display view — menu-v3 Alpine.js UI.

    SSR view that renders the menu-v3 template with injected JSON data
    for customers who scan a QR code. No authentication required.

    GET /m/<menu_slug>/

    Context passed to template:
        menu:           Menu instance
        organization:   Organization data (name, logo, settings)
        theme:          Theme instance
        menu_data_json: JSON string consumed by Alpine.js menuApp()
        page_title:     SEO page title
        page_description: SEO meta description
    """

    template_name = "public/menu_v3.html"

    def get(self, request, menu_slug, *args, **kwargs):
        """
        Render the public menu page with menu-v3 UI.

        Args:
            request: HTTP request
            menu_slug: URL slug of the menu to display

        Returns:
            Rendered HTML page or 404
        """
        # Fetch published menu by slug
        try:
            menu = Menu.objects.select_related(
                "organization",
                "theme",
            ).get(
                slug=menu_slug,
                is_published=True,
                deleted_at__isnull=True,
            )
        except Menu.DoesNotExist:
            logger.warning("Public menu not found: slug=%s", menu_slug)
            raise Http404(_("Menu not found"))

        organization = menu.organization
        theme = menu.theme

        # Fetch active categories with products
        categories = Category.objects.filter(
            menu=menu,
            is_active=True,
            deleted_at__isnull=True,
        ).order_by("sort_order", "name")

        # Fetch all active products for this menu in one query.
        # Use Prefetch with filtered querysets so that iterating
        # .all() in the serializer loop uses the prefetch cache
        # instead of issuing a new query per product.
        products = (
            Product.objects.filter(
                category__menu=menu,
                is_active=True,
                deleted_at__isnull=True,
            )
            .select_related(
                "category",
            )
            .prefetch_related(
                Prefetch(
                    "variants",
                    queryset=ProductVariant.objects.filter(
                        deleted_at__isnull=True,
                        is_available=True,
                    ).order_by("sort_order", "name"),
                ),
                Prefetch(
                    "modifiers",
                    queryset=ProductModifier.objects.filter(
                        deleted_at__isnull=True,
                    ).order_by("sort_order", "name"),
                ),
                "product_allergens__allergen",
            )
            .order_by("sort_order", "name")
        )

        # Fetch platform-level allergens for filter sidebar
        allergens = Allergen.objects.filter(
            is_active=True,
            deleted_at__isnull=True,
        ).order_by("sort_order", "name")

        # Build menu-v3 compatible JSON data
        menu_data = self._build_menu_data(
            menu=menu,
            organization=organization,
            theme=theme,
            categories=categories,
            products=products,
            allergens=allergens,
        )

        menu_data_json = json.dumps(menu_data, cls=DecimalEncoder, ensure_ascii=False)

        context = {
            "menu": menu,
            "organization": organization,
            "theme": theme,
            "menu_data_json": menu_data_json,
            "categories_with_products": self._get_categories_with_products(
                categories, products
            ),
            "page_title": f"{menu.name} - {organization.name}",
            "page_description": menu.description or f"{organization.name} dijital menü",
        }

        logger.info("Public menu viewed: slug=%s, org=%s", menu_slug, organization.name)

        return render(request, self.template_name, context)

    def _build_menu_data(
        self, menu, organization, theme, categories, products, allergens
    ):
        """
        Build menu-v3 compatible data structure.

        Serializes Django model instances into the flat JSON format
        expected by the Alpine.js menuApp() function.

        Returns:
            dict: Menu data with categories, products, allergens, theme, currency
        """
        now = timezone.now()
        new_threshold = now - timedelta(days=14)

        # Serialize categories
        categories_data = []
        for cat in categories:
            # Only include categories that have active products
            product_count = sum(
                1 for p in products if str(p.category_id) == str(cat.id)
            )
            if product_count == 0:
                continue

            categories_data.append(
                {
                    "id": str(cat.id),
                    "name": cat.name,
                    "icon": cat.icon or "ph-fill ph-fork-knife",
                    "description": cat.description or "",
                }
            )

        # Serialize products
        products_data = []
        for product in products:
            # Sizes (from variants) — already filtered via Prefetch
            sizes = []
            for variant in product.variants.all():
                sizes.append(
                    {
                        "name": variant.name,
                        "price": float(variant.price - product.base_price),
                    }
                )

            # Extras (modifiers with price > 0)
            extras = []
            # Sauces (modifiers with price == 0)
            sauces = []
            for modifier in product.modifiers.all():
                if modifier.price > 0:
                    extras.append(
                        {
                            "name": modifier.name,
                            "price": float(modifier.price),
                        }
                    )
                else:
                    sauces.append(modifier.name)

            # Allergen IDs for this product — use prefetch cache
            product_allergen_ids = [
                str(pa.allergen_id)
                for pa in product.product_allergens.all()
                if pa.deleted_at is None
            ]

            # Tags-based dietary flags
            tags = product.tags or []
            tags_lower = [t.lower() for t in tags]

            # Determine isNew
            is_new = (
                product.created_at >= new_threshold if product.created_at else False
            )

            products_data.append(
                {
                    "id": str(product.id),
                    "name": product.name,
                    "description": product.description
                    or product.short_description
                    or "",
                    "price": float(product.base_price),
                    "image": product.image_url or product.image or "",
                    "category": str(product.category_id),
                    "rating": float(product.rating),
                    "reviews": product.review_count,
                    "prepTime": product.preparation_time or 15,
                    "calories": product.calories or 0,
                    "popular": product.is_featured,
                    "isNew": is_new,
                    "discount": product.discount_percentage,
                    "vegan": "vegan" in tags_lower,
                    "vegetarian": "vegetarian" in tags_lower
                    or "vejetaryen" in tags_lower,
                    "glutenFree": "gluten-free" in tags_lower
                    or "glutensiz" in tags_lower,
                    "spicy": product.spicy_level >= 2,
                    "allergens": product_allergen_ids,
                    "sizes": sizes,
                    "extras": extras,
                    "sauces": sauces,
                }
            )

        # Serialize allergens
        allergens_data = [
            {
                "id": str(a.id),
                "name": a.name,
            }
            for a in allergens
        ]

        # Theme data (includes layout settings from theme.settings)
        theme_data = {}
        if theme:
            theme_settings = theme.settings or {}
            theme_data = {
                "primaryColor": theme.primary_color,
                "secondaryColor": theme.secondary_color,
                "accentColor": theme.accent_color or theme.secondary_color,
                "primaryColorRgb": theme.primary_color_rgb,
                "layout": theme_settings.get("layout", "wide"),
                "borderRadius": theme_settings.get("border_radius", 12),
                "gridColumns": theme_settings.get("grid_columns", 3),
                "darkMode": theme_settings.get("dark_mode", False),
            }

        # Storefront settings — merge org + menu settings (menu overrides org)
        org_settings = organization.settings or {}
        menu_settings = menu.settings or {}

        # Delivery & order settings
        delivery_fee = menu_settings.get(
            "delivery_fee", org_settings.get("delivery_fee", 15)
        )
        free_delivery_threshold = menu_settings.get(
            "free_delivery_threshold", org_settings.get("free_delivery_threshold", 300)
        )
        tax_rate = menu_settings.get("tax_rate", org_settings.get("tax_rate", 10))
        delivery_time = menu_settings.get(
            "delivery_time", org_settings.get("delivery_time", "30-45 dk")
        )

        # Promo banner settings
        promo_banner = menu_settings.get(
            "promo_banner", org_settings.get("promo_banner", {})
        )

        # Coupon codes (admin-defined)
        coupons = menu_settings.get("coupons", org_settings.get("coupons", {}))

        return {
            "categories": categories_data,
            "products": products_data,
            "allergens": allergens_data,
            "theme": theme_data,
            "currency": menu_settings.get("currency", "TRY"),
            "locale": "tr-TR",
            "organizationName": organization.name,
            "menuName": menu.name,
            "menuDescription": menu.description or "",
            # Storefront config (dynamic, admin-managed)
            "storefront": {
                "deliveryFee": float(delivery_fee),
                "freeDeliveryThreshold": float(free_delivery_threshold),
                "taxRate": float(tax_rate) / 100,  # Convert percentage to decimal
                "deliveryTime": str(delivery_time),
                "promoBanner": promo_banner,
                "coupons": coupons,
            },
        }

    def _get_categories_with_products(self, categories, products):
        """
        Build categories with products list for SSR/SEO fallback.

        Returns:
            list: Categories with their products for server-side rendering
        """
        result = []
        for cat in categories:
            cat_products = [p for p in products if str(p.category_id) == str(cat.id)]
            if cat_products:
                result.append(
                    {
                        "category": cat,
                        "products": cat_products,
                    }
                )
        return result


class PublicMenuDetailView(View):
    """
    Public menu product detail view.

    Displays detailed information about a specific product.
    No authentication required.

    GET /m/<menu_slug>/product/<product_id>/
    """

    template_name = "public/menu_detail.html"

    def get(self, request, menu_slug, product_id=None, *args, **kwargs):
        """Render the product detail page."""
        try:
            menu = Menu.objects.select_related(
                "organization",
                "theme",
            ).get(
                slug=menu_slug,
                is_published=True,
                deleted_at__isnull=True,
            )
        except Menu.DoesNotExist:
            raise Http404(_("Menu not found"))

        if product_id:
            try:
                product = (
                    Product.objects.select_related(
                        "category",
                        "category__menu",
                    )
                    .prefetch_related(
                        "variants",
                        "modifiers",
                        "product_allergens__allergen",
                        "nutrition_info",
                    )
                    .get(
                        id=product_id,
                        category__menu=menu,
                        is_active=True,
                        deleted_at__isnull=True,
                    )
                )
            except Product.DoesNotExist:
                raise Http404(_("Product not found"))
        else:
            product = None

        context = {
            "menu": menu,
            "organization": menu.organization,
            "product": product,
            "theme": menu.theme,
            "page_title": f"{product.name if product else menu.name} - {menu.organization.name}",
        }

        return render(request, self.template_name, context)


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    "PublicMenuView",
    "PublicMenuDetailView",
]
