# Generated manually for E-Menum Menu Module
# This migration creates all menu-related models

import uuid
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    """
    Initial migration for the menu module.

    Creates:
    - Theme: Menu styling customization with colors, fonts, and CSS
    - Menu: Restaurant menu container for organizing categories and products
    - Category: Product categories with nested support (hierarchical structure)
    - Product: Individual menu items with pricing and attributes
    - ProductVariant: Size/portion options (e.g., "Small", "Large")
    - ProductModifier: Add-on options (e.g., "Extra Cheese", "No Onion")
    - Allergen: Platform-level allergen definitions (global, not tenant-specific)
    - ProductAllergen: Junction table for product-allergen relationships
    - NutritionInfo: One-to-one nutritional data per product
    """

    initial = True

    dependencies = [
        ("core", "0001_initial"),
    ]

    operations = [
        # 1. Theme model (menu styling customization)
        migrations.CreateModel(
            name="Theme",
            fields=[
                (
                    "created_at",
                    models.DateTimeField(
                        auto_now_add=True,
                        help_text="Timestamp when record was created",
                        verbose_name="Created at",
                    ),
                ),
                (
                    "updated_at",
                    models.DateTimeField(
                        auto_now=True,
                        help_text="Timestamp when record was last updated",
                        verbose_name="Updated at",
                    ),
                ),
                (
                    "deleted_at",
                    models.DateTimeField(
                        blank=True,
                        db_index=True,
                        help_text="Timestamp when record was soft-deleted (null = active)",
                        null=True,
                        verbose_name="Deleted at",
                    ),
                ),
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        help_text="Unique identifier (UUID)",
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "name",
                    models.CharField(
                        help_text="Display name of the theme",
                        max_length=100,
                        verbose_name="Name",
                    ),
                ),
                (
                    "slug",
                    models.SlugField(
                        help_text="URL-friendly identifier (unique within organization)",
                        max_length=100,
                        verbose_name="Slug",
                    ),
                ),
                (
                    "description",
                    models.TextField(
                        blank=True,
                        help_text="Optional description of the theme",
                        null=True,
                        verbose_name="Description",
                    ),
                ),
                (
                    "primary_color",
                    models.CharField(
                        default="#3B82F6",
                        help_text="Primary brand color (hex format, e.g., #3B82F6)",
                        max_length=7,
                        verbose_name="Primary color",
                    ),
                ),
                (
                    "secondary_color",
                    models.CharField(
                        default="#10B981",
                        help_text="Secondary accent color (hex format)",
                        max_length=7,
                        verbose_name="Secondary color",
                    ),
                ),
                (
                    "background_color",
                    models.CharField(
                        default="#FFFFFF",
                        help_text="Page background color (hex format)",
                        max_length=7,
                        verbose_name="Background color",
                    ),
                ),
                (
                    "text_color",
                    models.CharField(
                        default="#1F2937",
                        help_text="Primary text color (hex format)",
                        max_length=7,
                        verbose_name="Text color",
                    ),
                ),
                (
                    "accent_color",
                    models.CharField(
                        blank=True,
                        help_text="Optional accent color for highlights (hex format)",
                        max_length=7,
                        null=True,
                        verbose_name="Accent color",
                    ),
                ),
                (
                    "font_family",
                    models.CharField(
                        default="Inter",
                        help_text="Primary font family (e.g., Inter, Roboto, Open Sans)",
                        max_length=100,
                        verbose_name="Font family",
                    ),
                ),
                (
                    "heading_font_family",
                    models.CharField(
                        blank=True,
                        help_text="Optional separate font for headings",
                        max_length=100,
                        null=True,
                        verbose_name="Heading font family",
                    ),
                ),
                (
                    "logo_position",
                    models.CharField(
                        choices=[
                            ("left", "Left"),
                            ("center", "Center"),
                            ("right", "Right"),
                        ],
                        default="left",
                        help_text="Position of logo in menu header",
                        max_length=20,
                        verbose_name="Logo position",
                    ),
                ),
                (
                    "custom_css",
                    models.TextField(
                        blank=True,
                        help_text="Custom CSS for advanced theme styling",
                        null=True,
                        verbose_name="Custom CSS",
                    ),
                ),
                (
                    "settings",
                    models.JSONField(
                        blank=True,
                        default=dict,
                        help_text="Additional theme settings (JSON)",
                        verbose_name="Settings",
                    ),
                ),
                (
                    "is_default",
                    models.BooleanField(
                        default=False,
                        help_text="Whether this is the default theme for the organization",
                        verbose_name="Is default",
                    ),
                ),
                (
                    "is_active",
                    models.BooleanField(
                        db_index=True,
                        default=True,
                        help_text="Whether the theme is available for use",
                        verbose_name="Is active",
                    ),
                ),
                (
                    "organization",
                    models.ForeignKey(
                        help_text="Organization this theme belongs to",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="themes",
                        to="core.organization",
                        verbose_name="Organization",
                    ),
                ),
            ],
            options={
                "verbose_name": "Theme",
                "verbose_name_plural": "Themes",
                "db_table": "themes",
                "ordering": ["-is_default", "name"],
            },
        ),
        migrations.AddConstraint(
            model_name="theme",
            constraint=models.UniqueConstraint(
                fields=["organization", "slug"], name="theme_org_slug_uniq"
            ),
        ),
        migrations.AddIndex(
            model_name="theme",
            index=models.Index(
                fields=["organization", "is_active"], name="theme_org_active_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="theme",
            index=models.Index(
                fields=["organization", "is_default"], name="theme_org_default_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="theme",
            index=models.Index(
                fields=["organization", "deleted_at"], name="theme_org_deleted_idx"
            ),
        ),
        # 2. Menu model (restaurant menu container)
        migrations.CreateModel(
            name="Menu",
            fields=[
                (
                    "created_at",
                    models.DateTimeField(
                        auto_now_add=True,
                        help_text="Timestamp when record was created",
                        verbose_name="Created at",
                    ),
                ),
                (
                    "updated_at",
                    models.DateTimeField(
                        auto_now=True,
                        help_text="Timestamp when record was last updated",
                        verbose_name="Updated at",
                    ),
                ),
                (
                    "deleted_at",
                    models.DateTimeField(
                        blank=True,
                        db_index=True,
                        help_text="Timestamp when record was soft-deleted (null = active)",
                        null=True,
                        verbose_name="Deleted at",
                    ),
                ),
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        help_text="Unique identifier (UUID)",
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "name",
                    models.CharField(
                        help_text="Display name of the menu",
                        max_length=100,
                        verbose_name="Name",
                    ),
                ),
                (
                    "slug",
                    models.SlugField(
                        help_text="URL-friendly identifier (unique within organization)",
                        max_length=100,
                        verbose_name="Slug",
                    ),
                ),
                (
                    "description",
                    models.TextField(
                        blank=True,
                        help_text="Optional description of the menu",
                        null=True,
                        verbose_name="Description",
                    ),
                ),
                (
                    "is_published",
                    models.BooleanField(
                        db_index=True,
                        default=False,
                        help_text="Whether the menu is visible to customers",
                        verbose_name="Is published",
                    ),
                ),
                (
                    "published_at",
                    models.DateTimeField(
                        blank=True,
                        help_text="Timestamp when the menu was published",
                        null=True,
                        verbose_name="Published at",
                    ),
                ),
                (
                    "is_default",
                    models.BooleanField(
                        default=False,
                        help_text="Whether this is the default menu for the organization",
                        verbose_name="Is default",
                    ),
                ),
                (
                    "settings",
                    models.JSONField(
                        blank=True,
                        default=dict,
                        help_text="Additional menu settings (JSON)",
                        verbose_name="Settings",
                    ),
                ),
                (
                    "sort_order",
                    models.PositiveIntegerField(
                        default=0,
                        help_text="Display order for menus (lower numbers appear first)",
                        verbose_name="Sort order",
                    ),
                ),
                (
                    "organization",
                    models.ForeignKey(
                        help_text="Organization this menu belongs to",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="menus",
                        to="core.organization",
                        verbose_name="Organization",
                    ),
                ),
                (
                    "theme",
                    models.ForeignKey(
                        blank=True,
                        help_text="Optional theme for styling customization",
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="menus",
                        to="menu.theme",
                        verbose_name="Theme",
                    ),
                ),
            ],
            options={
                "verbose_name": "Menu",
                "verbose_name_plural": "Menus",
                "db_table": "menus",
                "ordering": ["sort_order", "name"],
            },
        ),
        migrations.AddConstraint(
            model_name="menu",
            constraint=models.UniqueConstraint(
                fields=["organization", "slug"], name="menu_org_slug_uniq"
            ),
        ),
        migrations.AddIndex(
            model_name="menu",
            index=models.Index(
                fields=["organization", "is_published"], name="menu_org_published_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="menu",
            index=models.Index(
                fields=["organization", "is_default"], name="menu_org_default_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="menu",
            index=models.Index(
                fields=["organization", "deleted_at"], name="menu_org_deleted_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="menu",
            index=models.Index(
                fields=["organization", "sort_order"], name="menu_org_sort_idx"
            ),
        ),
        # 3. Category model (product grouping with nested support)
        migrations.CreateModel(
            name="Category",
            fields=[
                (
                    "created_at",
                    models.DateTimeField(
                        auto_now_add=True,
                        help_text="Timestamp when record was created",
                        verbose_name="Created at",
                    ),
                ),
                (
                    "updated_at",
                    models.DateTimeField(
                        auto_now=True,
                        help_text="Timestamp when record was last updated",
                        verbose_name="Updated at",
                    ),
                ),
                (
                    "deleted_at",
                    models.DateTimeField(
                        blank=True,
                        db_index=True,
                        help_text="Timestamp when record was soft-deleted (null = active)",
                        null=True,
                        verbose_name="Deleted at",
                    ),
                ),
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        help_text="Unique identifier (UUID)",
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "name",
                    models.CharField(
                        help_text="Display name of the category",
                        max_length=100,
                        verbose_name="Name",
                    ),
                ),
                (
                    "slug",
                    models.SlugField(
                        help_text="URL-friendly identifier (unique within menu)",
                        max_length=100,
                        verbose_name="Slug",
                    ),
                ),
                (
                    "description",
                    models.TextField(
                        blank=True,
                        help_text="Optional description of the category",
                        null=True,
                        verbose_name="Description",
                    ),
                ),
                (
                    "image",
                    models.URLField(
                        blank=True,
                        help_text="URL to category image",
                        max_length=500,
                        null=True,
                        verbose_name="Image URL",
                    ),
                ),
                (
                    "is_active",
                    models.BooleanField(
                        db_index=True,
                        default=True,
                        help_text="Whether the category is visible/active",
                        verbose_name="Is active",
                    ),
                ),
                (
                    "sort_order",
                    models.PositiveIntegerField(
                        default=0,
                        help_text="Display order within parent category/menu (lower numbers appear first)",
                        verbose_name="Sort order",
                    ),
                ),
                (
                    "menu",
                    models.ForeignKey(
                        help_text="Menu this category belongs to",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="categories",
                        to="menu.menu",
                        verbose_name="Menu",
                    ),
                ),
                (
                    "organization",
                    models.ForeignKey(
                        help_text="Organization this category belongs to",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="categories",
                        to="core.organization",
                        verbose_name="Organization",
                    ),
                ),
                (
                    "parent",
                    models.ForeignKey(
                        blank=True,
                        help_text="Parent category for nested structure (null for root categories)",
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="children",
                        to="menu.category",
                        verbose_name="Parent category",
                    ),
                ),
            ],
            options={
                "verbose_name": "Category",
                "verbose_name_plural": "Categories",
                "db_table": "categories",
                "ordering": ["sort_order", "name"],
            },
        ),
        migrations.AddConstraint(
            model_name="category",
            constraint=models.UniqueConstraint(
                fields=["menu", "slug"], name="category_menu_slug_uniq"
            ),
        ),
        migrations.AddIndex(
            model_name="category",
            index=models.Index(
                fields=["menu", "sort_order"], name="category_menu_sort_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="category",
            index=models.Index(
                fields=["organization", "deleted_at"], name="category_org_deleted_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="category",
            index=models.Index(fields=["parent"], name="category_parent_idx"),
        ),
        migrations.AddIndex(
            model_name="category",
            index=models.Index(
                fields=["menu", "is_active"], name="category_menu_active_idx"
            ),
        ),
        # 4. Product model (individual menu items)
        migrations.CreateModel(
            name="Product",
            fields=[
                (
                    "created_at",
                    models.DateTimeField(
                        auto_now_add=True,
                        help_text="Timestamp when record was created",
                        verbose_name="Created at",
                    ),
                ),
                (
                    "updated_at",
                    models.DateTimeField(
                        auto_now=True,
                        help_text="Timestamp when record was last updated",
                        verbose_name="Updated at",
                    ),
                ),
                (
                    "deleted_at",
                    models.DateTimeField(
                        blank=True,
                        db_index=True,
                        help_text="Timestamp when record was soft-deleted (null = active)",
                        null=True,
                        verbose_name="Deleted at",
                    ),
                ),
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        help_text="Unique identifier (UUID)",
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "name",
                    models.CharField(
                        help_text="Display name of the product",
                        max_length=200,
                        verbose_name="Name",
                    ),
                ),
                (
                    "slug",
                    models.SlugField(
                        help_text="URL-friendly identifier (unique within category)",
                        max_length=200,
                        verbose_name="Slug",
                    ),
                ),
                (
                    "description",
                    models.TextField(
                        blank=True,
                        help_text="Full product description",
                        null=True,
                        verbose_name="Description",
                    ),
                ),
                (
                    "short_description",
                    models.CharField(
                        blank=True,
                        help_text="Brief description for listings (max 100 chars)",
                        max_length=100,
                        null=True,
                        verbose_name="Short description",
                    ),
                ),
                (
                    "base_price",
                    models.DecimalField(
                        decimal_places=2,
                        help_text="Base price in the default currency",
                        max_digits=10,
                        verbose_name="Base price",
                    ),
                ),
                (
                    "currency",
                    models.CharField(
                        default="TRY",
                        help_text="Currency code (e.g., TRY, USD, EUR)",
                        max_length=3,
                        verbose_name="Currency",
                    ),
                ),
                (
                    "image",
                    models.URLField(
                        blank=True,
                        help_text="Main product image URL",
                        max_length=500,
                        null=True,
                        verbose_name="Image URL",
                    ),
                ),
                (
                    "gallery",
                    models.JSONField(
                        blank=True,
                        default=list,
                        help_text="Array of additional image URLs",
                        verbose_name="Gallery",
                    ),
                ),
                (
                    "is_active",
                    models.BooleanField(
                        db_index=True,
                        default=True,
                        help_text="Whether the product is visible on the menu",
                        verbose_name="Is active",
                    ),
                ),
                (
                    "is_available",
                    models.BooleanField(
                        db_index=True,
                        default=True,
                        help_text="Whether the product is in stock/available for ordering",
                        verbose_name="Is available",
                    ),
                ),
                (
                    "is_featured",
                    models.BooleanField(
                        db_index=True,
                        default=False,
                        help_text="Whether to highlight this product on the menu",
                        verbose_name="Is featured",
                    ),
                ),
                (
                    "is_chef_recommended",
                    models.BooleanField(
                        db_index=True,
                        default=False,
                        help_text="Special chef recommendation flag",
                        verbose_name="Is chef recommended",
                    ),
                ),
                (
                    "preparation_time",
                    models.PositiveIntegerField(
                        blank=True,
                        help_text="Estimated preparation time in minutes",
                        null=True,
                        verbose_name="Preparation time",
                    ),
                ),
                (
                    "calories",
                    models.PositiveIntegerField(
                        blank=True,
                        help_text="Calorie count (kcal)",
                        null=True,
                        verbose_name="Calories",
                    ),
                ),
                (
                    "spicy_level",
                    models.PositiveSmallIntegerField(
                        default=0,
                        help_text="Spiciness level 0-5 (0=not spicy, 5=very spicy)",
                        verbose_name="Spicy level",
                    ),
                ),
                (
                    "tags",
                    models.JSONField(
                        blank=True,
                        default=list,
                        help_text="Array of tags for filtering (e.g., vegetarian, vegan, gluten-free)",
                        verbose_name="Tags",
                    ),
                ),
                (
                    "sort_order",
                    models.PositiveIntegerField(
                        default=0,
                        help_text="Display order within category (lower numbers appear first)",
                        verbose_name="Sort order",
                    ),
                ),
                (
                    "category",
                    models.ForeignKey(
                        help_text="Category this product belongs to",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="products",
                        to="menu.category",
                        verbose_name="Category",
                    ),
                ),
                (
                    "organization",
                    models.ForeignKey(
                        help_text="Organization this product belongs to",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="products",
                        to="core.organization",
                        verbose_name="Organization",
                    ),
                ),
            ],
            options={
                "verbose_name": "Product",
                "verbose_name_plural": "Products",
                "db_table": "products",
                "ordering": ["sort_order", "name"],
            },
        ),
        migrations.AddConstraint(
            model_name="product",
            constraint=models.UniqueConstraint(
                fields=["category", "slug"], name="product_category_slug_uniq"
            ),
        ),
        migrations.AddIndex(
            model_name="product",
            index=models.Index(
                fields=["category", "sort_order"], name="product_category_sort_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="product",
            index=models.Index(
                fields=["organization", "deleted_at"], name="product_org_deleted_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="product",
            index=models.Index(
                fields=["organization", "is_active", "is_available"],
                name="product_org_active_avail_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="product",
            index=models.Index(
                fields=["organization", "is_featured"], name="product_org_featured_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="product",
            index=models.Index(
                fields=["organization", "is_chef_recommended"],
                name="product_org_chef_rec_idx",
            ),
        ),
        # 5. ProductVariant model (size/portion options)
        migrations.CreateModel(
            name="ProductVariant",
            fields=[
                (
                    "created_at",
                    models.DateTimeField(
                        auto_now_add=True,
                        help_text="Timestamp when record was created",
                        verbose_name="Created at",
                    ),
                ),
                (
                    "updated_at",
                    models.DateTimeField(
                        auto_now=True,
                        help_text="Timestamp when record was last updated",
                        verbose_name="Updated at",
                    ),
                ),
                (
                    "deleted_at",
                    models.DateTimeField(
                        blank=True,
                        db_index=True,
                        help_text="Timestamp when record was soft-deleted (null = active)",
                        null=True,
                        verbose_name="Deleted at",
                    ),
                ),
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        help_text="Unique identifier (UUID)",
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "name",
                    models.CharField(
                        help_text="Display name of the variant (e.g., Small, Large, Regular)",
                        max_length=100,
                        verbose_name="Name",
                    ),
                ),
                (
                    "price",
                    models.DecimalField(
                        decimal_places=2,
                        help_text="Price for this variant",
                        max_digits=10,
                        verbose_name="Price",
                    ),
                ),
                (
                    "is_default",
                    models.BooleanField(
                        db_index=True,
                        default=False,
                        help_text="Whether this is the default selected variant",
                        verbose_name="Is default",
                    ),
                ),
                (
                    "is_available",
                    models.BooleanField(
                        db_index=True,
                        default=True,
                        help_text="Whether the variant is in stock/available",
                        verbose_name="Is available",
                    ),
                ),
                (
                    "sort_order",
                    models.PositiveIntegerField(
                        default=0,
                        help_text="Display order within the product (lower numbers appear first)",
                        verbose_name="Sort order",
                    ),
                ),
                (
                    "product",
                    models.ForeignKey(
                        help_text="Product this variant belongs to",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="variants",
                        to="menu.product",
                        verbose_name="Product",
                    ),
                ),
            ],
            options={
                "verbose_name": "Product Variant",
                "verbose_name_plural": "Product Variants",
                "db_table": "product_variants",
                "ordering": ["sort_order", "name"],
            },
        ),
        migrations.AddIndex(
            model_name="productvariant",
            index=models.Index(
                fields=["product", "sort_order"], name="variant_product_sort_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="productvariant",
            index=models.Index(
                fields=["product", "is_default"], name="variant_product_default_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="productvariant",
            index=models.Index(
                fields=["product", "deleted_at"], name="variant_product_deleted_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="productvariant",
            index=models.Index(
                fields=["product", "is_available"], name="variant_product_avail_idx"
            ),
        ),
        # 6. ProductModifier model (add-on options)
        migrations.CreateModel(
            name="ProductModifier",
            fields=[
                (
                    "created_at",
                    models.DateTimeField(
                        auto_now_add=True,
                        help_text="Timestamp when record was created",
                        verbose_name="Created at",
                    ),
                ),
                (
                    "updated_at",
                    models.DateTimeField(
                        auto_now=True,
                        help_text="Timestamp when record was last updated",
                        verbose_name="Updated at",
                    ),
                ),
                (
                    "deleted_at",
                    models.DateTimeField(
                        blank=True,
                        db_index=True,
                        help_text="Timestamp when record was soft-deleted (null = active)",
                        null=True,
                        verbose_name="Deleted at",
                    ),
                ),
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        help_text="Unique identifier (UUID)",
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "name",
                    models.CharField(
                        help_text="Display name of the modifier (e.g., Extra Cheese, No Onion)",
                        max_length=100,
                        verbose_name="Name",
                    ),
                ),
                (
                    "price",
                    models.DecimalField(
                        decimal_places=2,
                        default=0,
                        help_text="Additional cost for this modifier (can be 0 for free mods)",
                        max_digits=10,
                        verbose_name="Price",
                    ),
                ),
                (
                    "is_default",
                    models.BooleanField(
                        db_index=True,
                        default=False,
                        help_text="Whether this modifier is pre-selected by default",
                        verbose_name="Is default",
                    ),
                ),
                (
                    "is_required",
                    models.BooleanField(
                        db_index=True,
                        default=False,
                        help_text="Whether the customer must select this modifier",
                        verbose_name="Is required",
                    ),
                ),
                (
                    "max_quantity",
                    models.PositiveIntegerField(
                        default=1,
                        help_text="Maximum times this modifier can be added to the order",
                        verbose_name="Max quantity",
                    ),
                ),
                (
                    "sort_order",
                    models.PositiveIntegerField(
                        default=0,
                        help_text="Display order within the product (lower numbers appear first)",
                        verbose_name="Sort order",
                    ),
                ),
                (
                    "product",
                    models.ForeignKey(
                        help_text="Product this modifier belongs to",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="modifiers",
                        to="menu.product",
                        verbose_name="Product",
                    ),
                ),
            ],
            options={
                "verbose_name": "Product Modifier",
                "verbose_name_plural": "Product Modifiers",
                "db_table": "product_modifiers",
                "ordering": ["sort_order", "name"],
            },
        ),
        migrations.AddIndex(
            model_name="productmodifier",
            index=models.Index(
                fields=["product", "sort_order"], name="modifier_product_sort_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="productmodifier",
            index=models.Index(
                fields=["product", "is_required"], name="modifier_product_req_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="productmodifier",
            index=models.Index(
                fields=["product", "is_default"], name="modifier_product_default_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="productmodifier",
            index=models.Index(
                fields=["product", "deleted_at"], name="modifier_product_deleted_idx"
            ),
        ),
        # 7. Allergen model (platform-level allergen definitions)
        migrations.CreateModel(
            name="Allergen",
            fields=[
                (
                    "created_at",
                    models.DateTimeField(
                        auto_now_add=True,
                        help_text="Timestamp when record was created",
                        verbose_name="Created at",
                    ),
                ),
                (
                    "updated_at",
                    models.DateTimeField(
                        auto_now=True,
                        help_text="Timestamp when record was last updated",
                        verbose_name="Updated at",
                    ),
                ),
                (
                    "deleted_at",
                    models.DateTimeField(
                        blank=True,
                        db_index=True,
                        help_text="Timestamp when record was soft-deleted (null = active)",
                        null=True,
                        verbose_name="Deleted at",
                    ),
                ),
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        help_text="Unique identifier (UUID)",
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "name",
                    models.CharField(
                        help_text="Display name of the allergen (e.g., Gluten, Nuts, Dairy)",
                        max_length=100,
                        verbose_name="Name",
                    ),
                ),
                (
                    "slug",
                    models.SlugField(
                        help_text="URL-friendly identifier (globally unique)",
                        max_length=100,
                        unique=True,
                        verbose_name="Slug",
                    ),
                ),
                (
                    "code",
                    models.CharField(
                        help_text="Short code for the allergen (e.g., GLU, NUT, DAI)",
                        max_length=10,
                        unique=True,
                        verbose_name="Code",
                    ),
                ),
                (
                    "icon",
                    models.URLField(
                        blank=True,
                        help_text="URL to allergen icon/image",
                        max_length=500,
                        null=True,
                        verbose_name="Icon URL",
                    ),
                ),
                (
                    "description",
                    models.TextField(
                        blank=True,
                        help_text="Detailed description of the allergen and its sources",
                        null=True,
                        verbose_name="Description",
                    ),
                ),
                (
                    "sort_order",
                    models.PositiveIntegerField(
                        default=0,
                        help_text="Display order for consistent listing (lower numbers appear first)",
                        verbose_name="Sort order",
                    ),
                ),
                (
                    "is_active",
                    models.BooleanField(
                        db_index=True,
                        default=True,
                        help_text="Whether the allergen is available for selection",
                        verbose_name="Is active",
                    ),
                ),
            ],
            options={
                "verbose_name": "Allergen",
                "verbose_name_plural": "Allergens",
                "db_table": "allergens",
                "ordering": ["sort_order", "name"],
            },
        ),
        migrations.AddIndex(
            model_name="allergen",
            index=models.Index(fields=["code"], name="allergen_code_idx"),
        ),
        migrations.AddIndex(
            model_name="allergen",
            index=models.Index(fields=["slug"], name="allergen_slug_idx"),
        ),
        migrations.AddIndex(
            model_name="allergen",
            index=models.Index(fields=["is_active"], name="allergen_active_idx"),
        ),
        migrations.AddIndex(
            model_name="allergen",
            index=models.Index(fields=["deleted_at"], name="allergen_deleted_idx"),
        ),
        # 8. ProductAllergen model (junction table for product-allergen relationships)
        migrations.CreateModel(
            name="ProductAllergen",
            fields=[
                (
                    "created_at",
                    models.DateTimeField(
                        auto_now_add=True,
                        help_text="Timestamp when record was created",
                        verbose_name="Created at",
                    ),
                ),
                (
                    "updated_at",
                    models.DateTimeField(
                        auto_now=True,
                        help_text="Timestamp when record was last updated",
                        verbose_name="Updated at",
                    ),
                ),
                (
                    "deleted_at",
                    models.DateTimeField(
                        blank=True,
                        db_index=True,
                        help_text="Timestamp when record was soft-deleted (null = active)",
                        null=True,
                        verbose_name="Deleted at",
                    ),
                ),
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        help_text="Unique identifier (UUID)",
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "severity",
                    models.CharField(
                        choices=[
                            ("contains", "Contains"),
                            ("may_contain", "May Contain"),
                            ("traces", "Traces"),
                        ],
                        default="contains",
                        help_text="Level of allergen presence (contains/may_contain/traces)",
                        max_length=20,
                        verbose_name="Severity",
                    ),
                ),
                (
                    "notes",
                    models.TextField(
                        blank=True,
                        help_text="Optional additional notes about this allergen in the product",
                        null=True,
                        verbose_name="Notes",
                    ),
                ),
                (
                    "allergen",
                    models.ForeignKey(
                        help_text="The allergen associated with this product",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="product_allergens",
                        to="menu.allergen",
                        verbose_name="Allergen",
                    ),
                ),
                (
                    "product",
                    models.ForeignKey(
                        help_text="Product this allergen association belongs to",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="product_allergens",
                        to="menu.product",
                        verbose_name="Product",
                    ),
                ),
            ],
            options={
                "verbose_name": "Product Allergen",
                "verbose_name_plural": "Product Allergens",
                "db_table": "product_allergens",
                "ordering": ["allergen__sort_order", "allergen__name"],
            },
        ),
        migrations.AddConstraint(
            model_name="productallergen",
            constraint=models.UniqueConstraint(
                fields=["product", "allergen"], name="prod_allergen_prod_all_uniq"
            ),
        ),
        migrations.AddIndex(
            model_name="productallergen",
            index=models.Index(
                fields=["product", "allergen"], name="prod_allergen_prod_all_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="productallergen",
            index=models.Index(
                fields=["allergen", "severity"], name="prod_allergen_sev_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="productallergen",
            index=models.Index(
                fields=["product", "deleted_at"], name="prod_allergen_deleted_idx"
            ),
        ),
        # 9. NutritionInfo model (one-to-one nutritional data per product)
        migrations.CreateModel(
            name="NutritionInfo",
            fields=[
                (
                    "created_at",
                    models.DateTimeField(
                        auto_now_add=True,
                        help_text="Timestamp when record was created",
                        verbose_name="Created at",
                    ),
                ),
                (
                    "updated_at",
                    models.DateTimeField(
                        auto_now=True,
                        help_text="Timestamp when record was last updated",
                        verbose_name="Updated at",
                    ),
                ),
                (
                    "deleted_at",
                    models.DateTimeField(
                        blank=True,
                        db_index=True,
                        help_text="Timestamp when record was soft-deleted (null = active)",
                        null=True,
                        verbose_name="Deleted at",
                    ),
                ),
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        help_text="Unique identifier (UUID)",
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "serving_size",
                    models.CharField(
                        default="100g",
                        help_text='Description of serving size (e.g., "100g", "1 portion", "1 slice")',
                        max_length=100,
                        verbose_name="Serving size",
                    ),
                ),
                (
                    "serving_size_grams",
                    models.DecimalField(
                        blank=True,
                        decimal_places=2,
                        help_text="Numeric serving size in grams for calculations",
                        max_digits=8,
                        null=True,
                        verbose_name="Serving size (grams)",
                    ),
                ),
                (
                    "calories",
                    models.PositiveIntegerField(
                        blank=True,
                        help_text="Energy in kcal per serving",
                        null=True,
                        verbose_name="Calories",
                    ),
                ),
                (
                    "protein",
                    models.DecimalField(
                        blank=True,
                        decimal_places=2,
                        help_text="Protein in grams per serving",
                        max_digits=8,
                        null=True,
                        verbose_name="Protein",
                    ),
                ),
                (
                    "carbohydrates",
                    models.DecimalField(
                        blank=True,
                        decimal_places=2,
                        help_text="Total carbohydrates in grams per serving",
                        max_digits=8,
                        null=True,
                        verbose_name="Carbohydrates",
                    ),
                ),
                (
                    "sugar",
                    models.DecimalField(
                        blank=True,
                        decimal_places=2,
                        help_text="Sugar content in grams per serving",
                        max_digits=8,
                        null=True,
                        verbose_name="Sugar",
                    ),
                ),
                (
                    "fiber",
                    models.DecimalField(
                        blank=True,
                        decimal_places=2,
                        help_text="Dietary fiber in grams per serving",
                        max_digits=8,
                        null=True,
                        verbose_name="Fiber",
                    ),
                ),
                (
                    "fat",
                    models.DecimalField(
                        blank=True,
                        decimal_places=2,
                        help_text="Total fat in grams per serving",
                        max_digits=8,
                        null=True,
                        verbose_name="Fat",
                    ),
                ),
                (
                    "saturated_fat",
                    models.DecimalField(
                        blank=True,
                        decimal_places=2,
                        help_text="Saturated fat in grams per serving",
                        max_digits=8,
                        null=True,
                        verbose_name="Saturated fat",
                    ),
                ),
                (
                    "trans_fat",
                    models.DecimalField(
                        blank=True,
                        decimal_places=2,
                        help_text="Trans fat in grams per serving",
                        max_digits=8,
                        null=True,
                        verbose_name="Trans fat",
                    ),
                ),
                (
                    "cholesterol",
                    models.DecimalField(
                        blank=True,
                        decimal_places=2,
                        help_text="Cholesterol in mg per serving",
                        max_digits=8,
                        null=True,
                        verbose_name="Cholesterol",
                    ),
                ),
                (
                    "sodium",
                    models.DecimalField(
                        blank=True,
                        decimal_places=2,
                        help_text="Sodium in mg per serving",
                        max_digits=8,
                        null=True,
                        verbose_name="Sodium",
                    ),
                ),
                (
                    "potassium",
                    models.DecimalField(
                        blank=True,
                        decimal_places=2,
                        help_text="Potassium in mg per serving",
                        max_digits=8,
                        null=True,
                        verbose_name="Potassium",
                    ),
                ),
                (
                    "calcium",
                    models.DecimalField(
                        blank=True,
                        decimal_places=2,
                        help_text="Calcium in mg per serving",
                        max_digits=8,
                        null=True,
                        verbose_name="Calcium",
                    ),
                ),
                (
                    "iron",
                    models.DecimalField(
                        blank=True,
                        decimal_places=2,
                        help_text="Iron in mg per serving",
                        max_digits=8,
                        null=True,
                        verbose_name="Iron",
                    ),
                ),
                (
                    "vitamin_a",
                    models.DecimalField(
                        blank=True,
                        decimal_places=2,
                        help_text="Vitamin A in IU or mcg per serving",
                        max_digits=8,
                        null=True,
                        verbose_name="Vitamin A",
                    ),
                ),
                (
                    "vitamin_c",
                    models.DecimalField(
                        blank=True,
                        decimal_places=2,
                        help_text="Vitamin C in mg per serving",
                        max_digits=8,
                        null=True,
                        verbose_name="Vitamin C",
                    ),
                ),
                (
                    "custom_nutrients",
                    models.JSONField(
                        blank=True,
                        default=dict,
                        help_text="Additional nutrients not covered by standard fields (JSON)",
                        verbose_name="Custom nutrients",
                    ),
                ),
                (
                    "product",
                    models.OneToOneField(
                        help_text="Product this nutrition info belongs to",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="nutrition_info",
                        to="menu.product",
                        verbose_name="Product",
                    ),
                ),
            ],
            options={
                "verbose_name": "Nutrition Info",
                "verbose_name_plural": "Nutrition Info",
                "db_table": "nutrition_info",
            },
        ),
        migrations.AddIndex(
            model_name="nutritioninfo",
            index=models.Index(fields=["product"], name="nutrition_product_idx"),
        ),
        migrations.AddIndex(
            model_name="nutritioninfo",
            index=models.Index(fields=["deleted_at"], name="nutrition_deleted_idx"),
        ),
    ]
