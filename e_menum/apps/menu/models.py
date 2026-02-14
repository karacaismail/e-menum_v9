"""
Django ORM models for the Menu application.

This module defines the menu-related models for E-Menum:
- Theme: Menu styling customization with colors, fonts, and CSS options
- Menu: Restaurant menu container for organizing categories and products
- Category: Product categories with nested support (hierarchical structure)
- Product: Individual menu items with pricing and attributes
- ProductVariant: Size/portion options (e.g., "Small", "Large")
- ProductModifier: Add-on options (e.g., "Extra Cheese", "No Onion")
- Allergen: Platform-level allergen definitions (global, not tenant-specific)
- ProductAllergen: Junction table for product-allergen relationships
- NutritionInfo: One-to-one nutritional data per product

Critical Rules:
- Every query MUST include organization_id for tenant isolation (except Allergen which is platform-level)
- All entities use soft delete (deleted_at timestamp)
- No physical deletions allowed (use soft_delete method)
"""

import uuid

from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.models import (
    Organization,
    SoftDeleteManager,
    SoftDeleteMixin,
    TimeStampedMixin,
)


class LogoPosition(models.TextChoices):
    """Logo position options for theme customization."""
    LEFT = 'left', _('Left')
    CENTER = 'center', _('Center')
    RIGHT = 'right', _('Right')


class Theme(TimeStampedMixin, SoftDeleteMixin, models.Model):
    """
    Theme model - menu styling customization for organizations.

    Themes define the visual appearance of menus including colors, fonts,
    custom CSS, and branding options. Each organization can have multiple
    themes but only one can be set as default.

    Critical Rules:
    - EVERY query MUST filter by organization (multi-tenant isolation)
    - Use soft_delete() - never call delete() directly
    - Only one theme per organization should be marked as is_default

    Attributes:
        id: UUID primary key (ensures global uniqueness)
        organization: FK to parent Organization (tenant isolation)
        name: Display name of the theme
        slug: URL-friendly identifier (unique within organization)
        description: Optional description of the theme
        primary_color: Primary brand color (hex format)
        secondary_color: Secondary accent color (hex format)
        background_color: Page background color (hex format)
        text_color: Primary text color (hex format)
        accent_color: Optional accent color for highlights (hex format)
        font_family: Primary font family name
        heading_font_family: Optional separate font for headings
        logo_position: Position of logo in menu header (left/center/right)
        custom_css: Optional custom CSS for advanced styling
        settings: JSON field for additional theme settings
        is_default: Whether this is the default theme for the organization
        is_active: Whether the theme is available for use

    Usage:
        # Create a theme
        theme = Theme.objects.create(
            organization=org,
            name="Dark Mode",
            slug="dark-mode",
            primary_color="#3B82F6",
            secondary_color="#10B981",
            background_color="#1F2937",
            text_color="#F9FAFB"
        )

        # Query themes for organization (ALWAYS filter by organization!)
        themes = Theme.objects.filter(organization=org)

        # Get default theme
        default_theme = Theme.objects.filter(organization=org, is_default=True).first()

        # Soft delete theme (NEVER use delete())
        theme.soft_delete()
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name=_('ID'),
        help_text=_('Unique identifier (UUID)')
    )

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='themes',
        verbose_name=_('Organization'),
        help_text=_('Organization this theme belongs to')
    )

    name = models.CharField(
        max_length=100,
        verbose_name=_('Name'),
        help_text=_('Display name of the theme')
    )

    slug = models.SlugField(
        max_length=100,
        verbose_name=_('Slug'),
        help_text=_('URL-friendly identifier (unique within organization)')
    )

    description = models.TextField(
        blank=True,
        null=True,
        verbose_name=_('Description'),
        help_text=_('Optional description of the theme')
    )

    # Color settings (hex format, e.g., #3B82F6)
    primary_color = models.CharField(
        max_length=7,
        default='#3B82F6',
        verbose_name=_('Primary color'),
        help_text=_('Primary brand color (hex format, e.g., #3B82F6)')
    )

    secondary_color = models.CharField(
        max_length=7,
        default='#10B981',
        verbose_name=_('Secondary color'),
        help_text=_('Secondary accent color (hex format)')
    )

    background_color = models.CharField(
        max_length=7,
        default='#FFFFFF',
        verbose_name=_('Background color'),
        help_text=_('Page background color (hex format)')
    )

    text_color = models.CharField(
        max_length=7,
        default='#1F2937',
        verbose_name=_('Text color'),
        help_text=_('Primary text color (hex format)')
    )

    accent_color = models.CharField(
        max_length=7,
        blank=True,
        null=True,
        verbose_name=_('Accent color'),
        help_text=_('Optional accent color for highlights (hex format)')
    )

    # Typography settings
    font_family = models.CharField(
        max_length=100,
        default='Inter',
        verbose_name=_('Font family'),
        help_text=_('Primary font family (e.g., Inter, Roboto, Open Sans)')
    )

    heading_font_family = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name=_('Heading font family'),
        help_text=_('Optional separate font for headings')
    )

    # Layout settings
    logo_position = models.CharField(
        max_length=20,
        choices=LogoPosition.choices,
        default=LogoPosition.LEFT,
        verbose_name=_('Logo position'),
        help_text=_('Position of logo in menu header')
    )

    # Advanced customization
    custom_css = models.TextField(
        blank=True,
        null=True,
        verbose_name=_('Custom CSS'),
        help_text=_('Custom CSS for advanced theme styling')
    )

    settings = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_('Settings'),
        help_text=_('Additional theme settings (JSON)')
    )

    # Status flags
    is_default = models.BooleanField(
        default=False,
        verbose_name=_('Is default'),
        help_text=_('Whether this is the default theme for the organization')
    )

    is_active = models.BooleanField(
        default=True,
        db_index=True,
        verbose_name=_('Is active'),
        help_text=_('Whether the theme is available for use')
    )

    # Managers
    objects = SoftDeleteManager()  # Default: excludes soft-deleted
    all_objects = models.Manager()  # Includes ALL records

    class Meta:
        db_table = 'themes'
        verbose_name = _('Theme')
        verbose_name_plural = _('Themes')
        ordering = ['-is_default', 'name']
        unique_together = [['organization', 'slug']]
        indexes = [
            models.Index(fields=['organization', 'is_active'], name='theme_org_active_idx'),
            models.Index(fields=['organization', 'is_default'], name='theme_org_default_idx'),
            models.Index(fields=['organization', 'deleted_at'], name='theme_org_deleted_idx'),
        ]

    def __str__(self) -> str:
        return f"{self.name} ({self.organization.name})"

    def __repr__(self) -> str:
        return f"<Theme(id={self.id}, name='{self.name}', org='{self.organization.name}')>"

    @property
    def is_available(self) -> bool:
        """Check if theme is active and not deleted."""
        return self.is_active and not self.is_deleted

    def get_setting(self, key: str, default=None):
        """
        Get a value from theme settings.

        Args:
            key: The setting key to retrieve
            default: Default value if key not found

        Returns:
            The setting value or default
        """
        return self.settings.get(key, default)

    def set_setting(self, key: str, value) -> None:
        """
        Set a value in theme settings.

        Args:
            key: The setting key
            value: The value to set
        """
        self.settings[key] = value
        self.save(update_fields=['settings', 'updated_at'])

    def set_as_default(self) -> None:
        """
        Set this theme as the default for the organization.

        Clears is_default flag on all other themes for the same organization
        and sets this theme as default.
        """
        # Clear default flag on other themes
        Theme.objects.filter(
            organization=self.organization,
            is_default=True
        ).exclude(pk=self.pk).update(is_default=False)

        # Set this theme as default
        self.is_default = True
        self.save(update_fields=['is_default', 'updated_at'])

    def get_css_variables(self) -> dict:
        """
        Get CSS custom properties dictionary for the theme.

        Returns:
            Dictionary of CSS variable names and values
        """
        variables = {
            '--primary-color': self.primary_color,
            '--secondary-color': self.secondary_color,
            '--background-color': self.background_color,
            '--text-color': self.text_color,
            '--font-family': self.font_family,
        }

        if self.accent_color:
            variables['--accent-color'] = self.accent_color

        if self.heading_font_family:
            variables['--heading-font-family'] = self.heading_font_family
        else:
            variables['--heading-font-family'] = self.font_family

        return variables

    def get_css_variables_string(self) -> str:
        """
        Get CSS custom properties as a CSS string for inline use.

        Returns:
            CSS string with custom properties (e.g., "--primary-color: #3B82F6;")
        """
        variables = self.get_css_variables()
        return ' '.join(f'{key}: {value};' for key, value in variables.items())


class Menu(TimeStampedMixin, SoftDeleteMixin, models.Model):
    """
    Menu model - restaurant menu container for organizing categories and products.

    Menus are the primary container for organizing a restaurant's offerings.
    Each organization can have multiple menus (e.g., breakfast, lunch, dinner)
    but only one should be set as the default menu.

    Critical Rules:
    - EVERY query MUST filter by organization (multi-tenant isolation)
    - Use soft_delete() - never call delete() directly
    - Only one menu per organization should be marked as is_default
    - Published menus are visible to customers via QR codes

    Attributes:
        id: UUID primary key (ensures global uniqueness)
        organization: FK to parent Organization (tenant isolation)
        name: Display name of the menu
        slug: URL-friendly identifier (unique within organization)
        description: Optional description of the menu
        is_published: Whether the menu is visible to customers
        published_at: Timestamp when menu was published
        is_default: Whether this is the default menu for the organization
        theme: Optional FK to Theme for styling customization
        settings: JSON field for additional menu settings
        sort_order: Display order for menus

    Usage:
        # Create a menu
        menu = Menu.objects.create(
            organization=org,
            name="Dinner Menu",
            slug="dinner-menu",
            description="Evening specials and main courses"
        )

        # Query menus for organization (ALWAYS filter by organization!)
        menus = Menu.objects.filter(organization=org)

        # Get default menu
        default_menu = Menu.objects.filter(organization=org, is_default=True).first()

        # Get published menus
        published = Menu.objects.filter(organization=org, is_published=True)

        # Soft delete menu (NEVER use delete())
        menu.soft_delete()
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name=_('ID'),
        help_text=_('Unique identifier (UUID)')
    )

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='menus',
        verbose_name=_('Organization'),
        help_text=_('Organization this menu belongs to')
    )

    name = models.CharField(
        max_length=100,
        verbose_name=_('Name'),
        help_text=_('Display name of the menu')
    )

    slug = models.SlugField(
        max_length=100,
        verbose_name=_('Slug'),
        help_text=_('URL-friendly identifier (unique within organization)')
    )

    description = models.TextField(
        blank=True,
        null=True,
        verbose_name=_('Description'),
        help_text=_('Optional description of the menu')
    )

    # Publication settings
    is_published = models.BooleanField(
        default=False,
        db_index=True,
        verbose_name=_('Is published'),
        help_text=_('Whether the menu is visible to customers')
    )

    published_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name=_('Published at'),
        help_text=_('Timestamp when the menu was published')
    )

    is_default = models.BooleanField(
        default=False,
        verbose_name=_('Is default'),
        help_text=_('Whether this is the default menu for the organization')
    )

    # Styling
    theme = models.ForeignKey(
        Theme,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='menus',
        verbose_name=_('Theme'),
        help_text=_('Optional theme for styling customization')
    )

    # Additional settings
    settings = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_('Settings'),
        help_text=_('Additional menu settings (JSON)')
    )

    sort_order = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Sort order'),
        help_text=_('Display order for menus (lower numbers appear first)')
    )

    # Managers
    objects = SoftDeleteManager()  # Default: excludes soft-deleted
    all_objects = models.Manager()  # Includes ALL records

    class Meta:
        db_table = 'menus'
        verbose_name = _('Menu')
        verbose_name_plural = _('Menus')
        ordering = ['sort_order', 'name']
        unique_together = [['organization', 'slug']]
        indexes = [
            models.Index(fields=['organization', 'is_published'], name='menu_org_published_idx'),
            models.Index(fields=['organization', 'is_default'], name='menu_org_default_idx'),
            models.Index(fields=['organization', 'deleted_at'], name='menu_org_deleted_idx'),
            models.Index(fields=['organization', 'sort_order'], name='menu_org_sort_idx'),
        ]

    def __str__(self) -> str:
        return f"{self.name} ({self.organization.name})"

    def __repr__(self) -> str:
        return f"<Menu(id={self.id}, name='{self.name}', org='{self.organization.name}')>"

    @property
    def is_available(self) -> bool:
        """Check if menu is published and not deleted."""
        return self.is_published and not self.is_deleted

    def get_setting(self, key: str, default=None):
        """
        Get a value from menu settings.

        Args:
            key: The setting key to retrieve
            default: Default value if key not found

        Returns:
            The setting value or default
        """
        return self.settings.get(key, default)

    def set_setting(self, key: str, value) -> None:
        """
        Set a value in menu settings.

        Args:
            key: The setting key
            value: The value to set
        """
        self.settings[key] = value
        self.save(update_fields=['settings', 'updated_at'])

    def publish(self) -> None:
        """
        Publish the menu, making it visible to customers.

        Sets is_published to True and records the publication timestamp.
        """
        from django.utils import timezone
        self.is_published = True
        self.published_at = timezone.now()
        self.save(update_fields=['is_published', 'published_at', 'updated_at'])

    def unpublish(self) -> None:
        """
        Unpublish the menu, hiding it from customers.

        Sets is_published to False but preserves the published_at timestamp
        for historical reference.
        """
        self.is_published = False
        self.save(update_fields=['is_published', 'updated_at'])

    def set_as_default(self) -> None:
        """
        Set this menu as the default for the organization.

        Clears is_default flag on all other menus for the same organization
        and sets this menu as default.
        """
        # Clear default flag on other menus
        Menu.objects.filter(
            organization=self.organization,
            is_default=True
        ).exclude(pk=self.pk).update(is_default=False)

        # Set this menu as default
        self.is_default = True
        self.save(update_fields=['is_default', 'updated_at'])

    @property
    def category_count(self) -> int:
        """Return the number of active categories in this menu."""
        return self.categories.filter(deleted_at__isnull=True).count()


class Category(TimeStampedMixin, SoftDeleteMixin, models.Model):
    """
    Category model - product grouping with nested category support.

    Categories organize products within a menu. They support hierarchical
    structure through self-referential parent relationship, allowing for
    nested subcategories (e.g., "Beverages" > "Hot Drinks" > "Coffee").

    Critical Rules:
    - EVERY query MUST filter by organization (multi-tenant isolation)
    - Use soft_delete() - never call delete() directly
    - Nested categories should be limited to 2-3 levels for UX

    Attributes:
        id: UUID primary key (ensures global uniqueness)
        organization: FK to parent Organization (tenant isolation)
        menu: FK to parent Menu
        parent: Optional FK to parent Category (for nested categories)
        name: Display name of the category
        slug: URL-friendly identifier (unique within menu)
        description: Optional description of the category
        image: Optional URL to category image
        is_active: Whether the category is visible/active
        sort_order: Display order within parent category/menu

    Usage:
        # Create a top-level category
        beverages = Category.objects.create(
            organization=org,
            menu=menu,
            name="Beverages",
            slug="beverages",
            description="Hot and cold drinks"
        )

        # Create a nested category
        hot_drinks = Category.objects.create(
            organization=org,
            menu=menu,
            parent=beverages,
            name="Hot Drinks",
            slug="hot-drinks"
        )

        # Query categories for a menu (ALWAYS filter by organization!)
        categories = Category.objects.filter(
            organization=org,
            menu=menu
        )

        # Get root categories (no parent)
        root_categories = Category.objects.filter(
            organization=org,
            menu=menu,
            parent__isnull=True
        )

        # Get children of a category
        children = category.children.all()

        # Soft delete category (NEVER use delete())
        category.soft_delete()
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name=_('ID'),
        help_text=_('Unique identifier (UUID)')
    )

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='categories',
        verbose_name=_('Organization'),
        help_text=_('Organization this category belongs to')
    )

    menu = models.ForeignKey(
        Menu,
        on_delete=models.CASCADE,
        related_name='categories',
        verbose_name=_('Menu'),
        help_text=_('Menu this category belongs to')
    )

    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children',
        verbose_name=_('Parent category'),
        help_text=_('Parent category for nested structure (null for root categories)')
    )

    name = models.CharField(
        max_length=100,
        verbose_name=_('Name'),
        help_text=_('Display name of the category')
    )

    slug = models.SlugField(
        max_length=100,
        verbose_name=_('Slug'),
        help_text=_('URL-friendly identifier (unique within menu)')
    )

    description = models.TextField(
        blank=True,
        null=True,
        verbose_name=_('Description'),
        help_text=_('Optional description of the category')
    )

    image = models.URLField(
        blank=True,
        null=True,
        max_length=500,
        verbose_name=_('Image URL'),
        help_text=_('URL to category image')
    )

    is_active = models.BooleanField(
        default=True,
        db_index=True,
        verbose_name=_('Is active'),
        help_text=_('Whether the category is visible/active')
    )

    sort_order = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Sort order'),
        help_text=_('Display order within parent category/menu (lower numbers appear first)')
    )

    # Managers
    objects = SoftDeleteManager()  # Default: excludes soft-deleted
    all_objects = models.Manager()  # Includes ALL records

    class Meta:
        db_table = 'categories'
        verbose_name = _('Category')
        verbose_name_plural = _('Categories')
        ordering = ['sort_order', 'name']
        unique_together = [['menu', 'slug']]
        indexes = [
            models.Index(fields=['menu', 'sort_order'], name='category_menu_sort_idx'),
            models.Index(fields=['organization', 'deleted_at'], name='category_org_deleted_idx'),
            models.Index(fields=['parent'], name='category_parent_idx'),
            models.Index(fields=['menu', 'is_active'], name='category_menu_active_idx'),
        ]

    def __str__(self) -> str:
        if self.parent:
            return f"{self.parent.name} > {self.name}"
        return self.name

    def __repr__(self) -> str:
        return f"<Category(id={self.id}, name='{self.name}', menu='{self.menu.name}')>"

    @property
    def is_available(self) -> bool:
        """Check if category is active and not deleted."""
        return self.is_active and not self.is_deleted

    @property
    def is_root(self) -> bool:
        """Check if this is a root category (no parent)."""
        return self.parent is None

    @property
    def depth(self) -> int:
        """
        Calculate the depth of this category in the hierarchy.

        Returns:
            0 for root categories, 1 for first-level children, etc.
        """
        depth = 0
        current = self
        while current.parent is not None:
            depth += 1
            current = current.parent
        return depth

    @property
    def product_count(self) -> int:
        """Return the number of active products in this category."""
        # Note: products relation will be available after Product model is created
        if hasattr(self, 'products'):
            return self.products.filter(deleted_at__isnull=True).count()
        return 0

    def get_ancestors(self) -> list:
        """
        Get all ancestor categories from root to parent.

        Returns:
            List of ancestor Category objects, ordered from root to immediate parent
        """
        ancestors = []
        current = self.parent
        while current is not None:
            ancestors.insert(0, current)
            current = current.parent
        return ancestors

    def get_descendants(self) -> list:
        """
        Get all descendant categories recursively.

        Returns:
            List of all descendant Category objects
        """
        descendants = []
        for child in self.children.all():
            descendants.append(child)
            descendants.extend(child.get_descendants())
        return descendants

    def get_breadcrumb(self) -> list:
        """
        Get breadcrumb path from root to this category.

        Returns:
            List of Category objects representing the path,
            including this category as the last element
        """
        return self.get_ancestors() + [self]

    def get_full_path(self) -> str:
        """
        Get the full path name of this category.

        Returns:
            String like "Beverages > Hot Drinks > Coffee"
        """
        return ' > '.join(cat.name for cat in self.get_breadcrumb())

    def move_to(self, new_parent: 'Category' = None) -> None:
        """
        Move this category to a new parent.

        Args:
            new_parent: The new parent category, or None for root level

        Raises:
            ValueError: If trying to move to self or descendant
        """
        if new_parent is not None:
            if new_parent.id == self.id:
                raise ValueError("Cannot move category to itself")
            if new_parent in self.get_descendants():
                raise ValueError("Cannot move category to one of its descendants")

        self.parent = new_parent
        self.save(update_fields=['parent', 'updated_at'])


class Product(TimeStampedMixin, SoftDeleteMixin, models.Model):
    """
    Product model - individual menu items with pricing and attributes.

    Products are the core menu items that customers view and order.
    Each product belongs to a category and can have variants, modifiers,
    allergen information, and nutritional data.

    Critical Rules:
    - EVERY query MUST filter by organization (multi-tenant isolation)
    - Use soft_delete() - never call delete() directly
    - Product slugs must be unique within their category

    Attributes:
        id: UUID primary key (ensures global uniqueness)
        organization: FK to parent Organization (tenant isolation)
        category: FK to parent Category
        name: Display name of the product
        slug: URL-friendly identifier (unique within category)
        description: Full product description
        short_description: Brief description (max 100 chars) for listings
        base_price: Base price in the default currency
        currency: Currency code (default: TRY)
        image: Main product image URL
        gallery: JSON array of additional image URLs
        is_active: Whether the product is visible
        is_available: Whether the product is in stock
        is_featured: Whether to highlight on menu
        is_chef_recommended: Special chef recommendation flag
        preparation_time: Estimated preparation time in minutes
        calories: Calorie count (optional)
        spicy_level: Spiciness level 0-5 (0=not spicy, 5=very spicy)
        tags: JSON array of tags for filtering
        sort_order: Display order within category

    Usage:
        # Create a product
        product = Product.objects.create(
            organization=org,
            category=category,
            name="Margherita Pizza",
            slug="margherita-pizza",
            description="Classic Italian pizza with tomato and mozzarella",
            short_description="Classic tomato and mozzarella",
            base_price=Decimal("149.90"),
            is_featured=True
        )

        # Query products for category (ALWAYS filter by organization!)
        products = Product.objects.filter(
            organization=org,
            category=category,
            is_active=True,
            is_available=True
        )

        # Get featured products
        featured = Product.objects.filter(
            organization=org,
            is_featured=True,
            is_active=True
        )

        # Get chef recommendations
        chef_picks = Product.objects.filter(
            organization=org,
            is_chef_recommended=True,
            is_active=True
        )

        # Soft delete product (NEVER use delete())
        product.soft_delete()
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name=_('ID'),
        help_text=_('Unique identifier (UUID)')
    )

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='products',
        verbose_name=_('Organization'),
        help_text=_('Organization this product belongs to')
    )

    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name='products',
        verbose_name=_('Category'),
        help_text=_('Category this product belongs to')
    )

    name = models.CharField(
        max_length=200,
        verbose_name=_('Name'),
        help_text=_('Display name of the product')
    )

    slug = models.SlugField(
        max_length=200,
        verbose_name=_('Slug'),
        help_text=_('URL-friendly identifier (unique within category)')
    )

    description = models.TextField(
        blank=True,
        null=True,
        verbose_name=_('Description'),
        help_text=_('Full product description')
    )

    short_description = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name=_('Short description'),
        help_text=_('Brief description for listings (max 100 chars)')
    )

    # Pricing
    base_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=_('Base price'),
        help_text=_('Base price in the default currency')
    )

    currency = models.CharField(
        max_length=3,
        default='TRY',
        verbose_name=_('Currency'),
        help_text=_('Currency code (e.g., TRY, USD, EUR)')
    )

    # Images
    image = models.URLField(
        blank=True,
        null=True,
        max_length=500,
        verbose_name=_('Image URL'),
        help_text=_('Main product image URL')
    )

    gallery = models.JSONField(
        default=list,
        blank=True,
        verbose_name=_('Gallery'),
        help_text=_('Array of additional image URLs')
    )

    # Availability & Status
    is_active = models.BooleanField(
        default=True,
        db_index=True,
        verbose_name=_('Is active'),
        help_text=_('Whether the product is visible on the menu')
    )

    is_available = models.BooleanField(
        default=True,
        db_index=True,
        verbose_name=_('Is available'),
        help_text=_('Whether the product is in stock/available for ordering')
    )

    is_featured = models.BooleanField(
        default=False,
        db_index=True,
        verbose_name=_('Is featured'),
        help_text=_('Whether to highlight this product on the menu')
    )

    is_chef_recommended = models.BooleanField(
        default=False,
        db_index=True,
        verbose_name=_('Is chef recommended'),
        help_text=_('Special chef recommendation flag')
    )

    # Product attributes
    preparation_time = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name=_('Preparation time'),
        help_text=_('Estimated preparation time in minutes')
    )

    calories = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name=_('Calories'),
        help_text=_('Calorie count (kcal)')
    )

    spicy_level = models.PositiveSmallIntegerField(
        default=0,
        verbose_name=_('Spicy level'),
        help_text=_('Spiciness level 0-5 (0=not spicy, 5=very spicy)')
    )

    tags = models.JSONField(
        default=list,
        blank=True,
        verbose_name=_('Tags'),
        help_text=_('Array of tags for filtering (e.g., vegetarian, vegan, gluten-free)')
    )

    sort_order = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Sort order'),
        help_text=_('Display order within category (lower numbers appear first)')
    )

    # Managers
    objects = SoftDeleteManager()  # Default: excludes soft-deleted
    all_objects = models.Manager()  # Includes ALL records

    class Meta:
        db_table = 'products'
        verbose_name = _('Product')
        verbose_name_plural = _('Products')
        ordering = ['sort_order', 'name']
        unique_together = [['category', 'slug']]
        indexes = [
            models.Index(fields=['category', 'sort_order'], name='product_category_sort_idx'),
            models.Index(fields=['organization', 'deleted_at'], name='product_org_deleted_idx'),
            models.Index(
                fields=['organization', 'is_active', 'is_available'],
                name='product_org_active_avail_idx'
            ),
            models.Index(fields=['organization', 'is_featured'], name='product_org_featured_idx'),
            models.Index(
                fields=['organization', 'is_chef_recommended'],
                name='product_org_chef_rec_idx'
            ),
        ]

    def __str__(self) -> str:
        return f"{self.name} ({self.category.name})"

    def __repr__(self) -> str:
        return f"<Product(id={self.id}, name='{self.name}', category='{self.category.name}')>"

    @property
    def is_orderable(self) -> bool:
        """Check if product can be ordered (active, available, not deleted)."""
        return self.is_active and self.is_available and not self.is_deleted

    @property
    def formatted_price(self) -> str:
        """Return formatted price with currency symbol."""
        currency_symbols = {
            'TRY': '₺',
            'USD': '$',
            'EUR': '€',
            'GBP': '£',
        }
        symbol = currency_symbols.get(self.currency, self.currency)
        return f"{symbol}{self.base_price:,.2f}"

    @property
    def gallery_count(self) -> int:
        """Return the number of images in the gallery."""
        return len(self.gallery) if self.gallery else 0

    @property
    def has_gallery(self) -> bool:
        """Check if product has gallery images."""
        return bool(self.gallery)

    def get_all_images(self) -> list:
        """
        Get all product images including main image and gallery.

        Returns:
            List of image URLs, with main image first if exists
        """
        images = []
        if self.image:
            images.append(self.image)
        if self.gallery:
            images.extend(self.gallery)
        return images

    def add_gallery_image(self, image_url: str) -> None:
        """
        Add an image to the gallery.

        Args:
            image_url: URL of the image to add
        """
        if not self.gallery:
            self.gallery = []
        if image_url not in self.gallery:
            self.gallery.append(image_url)
            self.save(update_fields=['gallery', 'updated_at'])

    def remove_gallery_image(self, image_url: str) -> bool:
        """
        Remove an image from the gallery.

        Args:
            image_url: URL of the image to remove

        Returns:
            True if image was removed, False if not found
        """
        if self.gallery and image_url in self.gallery:
            self.gallery.remove(image_url)
            self.save(update_fields=['gallery', 'updated_at'])
            return True
        return False

    def add_tag(self, tag: str) -> None:
        """
        Add a tag to the product.

        Args:
            tag: Tag to add (will be normalized to lowercase)
        """
        normalized_tag = tag.lower().strip()
        if not self.tags:
            self.tags = []
        if normalized_tag not in self.tags:
            self.tags.append(normalized_tag)
            self.save(update_fields=['tags', 'updated_at'])

    def remove_tag(self, tag: str) -> bool:
        """
        Remove a tag from the product.

        Args:
            tag: Tag to remove

        Returns:
            True if tag was removed, False if not found
        """
        normalized_tag = tag.lower().strip()
        if self.tags and normalized_tag in self.tags:
            self.tags.remove(normalized_tag)
            self.save(update_fields=['tags', 'updated_at'])
            return True
        return False

    def has_tag(self, tag: str) -> bool:
        """
        Check if product has a specific tag.

        Args:
            tag: Tag to check

        Returns:
            True if product has the tag
        """
        normalized_tag = tag.lower().strip()
        return self.tags and normalized_tag in self.tags

    def set_availability(self, is_available: bool) -> None:
        """
        Set product availability (in stock / out of stock).

        Args:
            is_available: Whether the product is available
        """
        self.is_available = is_available
        self.save(update_fields=['is_available', 'updated_at'])

    def toggle_featured(self) -> bool:
        """
        Toggle the featured status of the product.

        Returns:
            New featured status
        """
        self.is_featured = not self.is_featured
        self.save(update_fields=['is_featured', 'updated_at'])
        return self.is_featured

    def toggle_chef_recommended(self) -> bool:
        """
        Toggle the chef recommended status of the product.

        Returns:
            New chef recommended status
        """
        self.is_chef_recommended = not self.is_chef_recommended
        self.save(update_fields=['is_chef_recommended', 'updated_at'])
        return self.is_chef_recommended

    def get_spicy_display(self) -> str:
        """
        Get a visual representation of spicy level.

        Returns:
            String with pepper emojis based on spicy level
        """
        if self.spicy_level == 0:
            return _('Not spicy')
        return '🌶️' * self.spicy_level

    @property
    def menu(self):
        """Get the menu this product belongs to via category."""
        return self.category.menu

    @property
    def variant_count(self) -> int:
        """Return the number of active variants for this product."""
        if hasattr(self, 'variants'):
            return self.variants.filter(deleted_at__isnull=True).count()
        return 0

    @property
    def modifier_count(self) -> int:
        """Return the number of active modifiers for this product."""
        if hasattr(self, 'modifiers'):
            return self.modifiers.filter(deleted_at__isnull=True).count()
        return 0

    @property
    def has_variants(self) -> bool:
        """Check if product has any active variants."""
        return self.variant_count > 0

    @property
    def has_modifiers(self) -> bool:
        """Check if product has any active modifiers."""
        return self.modifier_count > 0


class ProductVariant(TimeStampedMixin, SoftDeleteMixin, models.Model):
    """
    ProductVariant model - size/portion options for products.

    Variants represent different sizes or portions of a product,
    each with potentially different pricing. For example, a coffee
    might have "Small", "Medium", and "Large" variants.

    Critical Rules:
    - EVERY query MUST filter by organization (via product lookup)
    - Use soft_delete() - never call delete() directly
    - Only one variant per product should be marked as is_default

    Attributes:
        id: UUID primary key (ensures global uniqueness)
        product: FK to parent Product
        name: Display name of the variant (e.g., "Small", "Large")
        price: Price for this variant (may differ from base price)
        is_default: Whether this is the default selected variant
        is_available: Whether the variant is in stock
        sort_order: Display order within the product

    Usage:
        # Create variants for a product
        small = ProductVariant.objects.create(
            product=coffee,
            name="Small",
            price=Decimal("25.00"),
            is_default=True
        )
        large = ProductVariant.objects.create(
            product=coffee,
            name="Large",
            price=Decimal("35.00")
        )

        # Query variants for a product
        variants = ProductVariant.objects.filter(product=product)

        # Get default variant
        default = ProductVariant.objects.filter(
            product=product,
            is_default=True
        ).first()

        # Soft delete variant (NEVER use delete())
        variant.soft_delete()
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name=_('ID'),
        help_text=_('Unique identifier (UUID)')
    )

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='variants',
        verbose_name=_('Product'),
        help_text=_('Product this variant belongs to')
    )

    name = models.CharField(
        max_length=100,
        verbose_name=_('Name'),
        help_text=_('Display name of the variant (e.g., Small, Large, Regular)')
    )

    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=_('Price'),
        help_text=_('Price for this variant')
    )

    is_default = models.BooleanField(
        default=False,
        db_index=True,
        verbose_name=_('Is default'),
        help_text=_('Whether this is the default selected variant')
    )

    is_available = models.BooleanField(
        default=True,
        db_index=True,
        verbose_name=_('Is available'),
        help_text=_('Whether the variant is in stock/available')
    )

    sort_order = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Sort order'),
        help_text=_('Display order within the product (lower numbers appear first)')
    )

    # Managers
    objects = SoftDeleteManager()  # Default: excludes soft-deleted
    all_objects = models.Manager()  # Includes ALL records

    class Meta:
        db_table = 'product_variants'
        verbose_name = _('Product Variant')
        verbose_name_plural = _('Product Variants')
        ordering = ['sort_order', 'name']
        indexes = [
            models.Index(fields=['product', 'sort_order'], name='variant_product_sort_idx'),
            models.Index(fields=['product', 'is_default'], name='variant_product_default_idx'),
            models.Index(fields=['product', 'deleted_at'], name='variant_product_deleted_idx'),
            models.Index(fields=['product', 'is_available'], name='variant_product_avail_idx'),
        ]

    def __str__(self) -> str:
        return f"{self.product.name} - {self.name}"

    def __repr__(self) -> str:
        return f"<ProductVariant(id={self.id}, name='{self.name}', product='{self.product.name}')>"

    @property
    def is_orderable(self) -> bool:
        """Check if variant can be ordered (available, not deleted)."""
        return self.is_available and not self.is_deleted

    @property
    def formatted_price(self) -> str:
        """Return formatted price with currency symbol."""
        currency_symbols = {
            'TRY': '₺',
            'USD': '$',
            'EUR': '€',
            'GBP': '£',
        }
        currency = self.product.currency
        symbol = currency_symbols.get(currency, currency)
        return f"{symbol}{self.price:,.2f}"

    @property
    def price_difference(self):
        """
        Get the price difference from the base product price.

        Returns:
            Decimal: Positive if variant costs more, negative if less
        """
        return self.price - self.product.base_price

    def set_as_default(self) -> None:
        """
        Set this variant as the default for the product.

        Clears is_default flag on all other variants for the same product
        and sets this variant as default.
        """
        # Clear default flag on other variants
        ProductVariant.objects.filter(
            product=self.product,
            is_default=True
        ).exclude(pk=self.pk).update(is_default=False)

        # Set this variant as default
        self.is_default = True
        self.save(update_fields=['is_default', 'updated_at'])

    def set_availability(self, is_available: bool) -> None:
        """
        Set variant availability (in stock / out of stock).

        Args:
            is_available: Whether the variant is available
        """
        self.is_available = is_available
        self.save(update_fields=['is_available', 'updated_at'])

    @property
    def organization(self):
        """Get the organization this variant belongs to via product."""
        return self.product.organization


class ProductModifier(TimeStampedMixin, SoftDeleteMixin, models.Model):
    """
    ProductModifier model - add-on options for products.

    Modifiers represent optional additions or customizations to a product,
    each with an additional cost. For example, a burger might have
    "Extra Cheese", "Extra Bacon", or "No Onion" modifiers.

    Critical Rules:
    - EVERY query MUST filter by organization (via product lookup)
    - Use soft_delete() - never call delete() directly
    - Modifiers marked as is_required must be selected by the customer

    Attributes:
        id: UUID primary key (ensures global uniqueness)
        product: FK to parent Product
        name: Display name of the modifier (e.g., "Extra Cheese")
        price: Additional cost for this modifier
        is_default: Whether the modifier is pre-selected
        is_required: Whether the customer must select this modifier
        max_quantity: Maximum times this modifier can be added
        sort_order: Display order within the product

    Usage:
        # Create modifiers for a product
        extra_cheese = ProductModifier.objects.create(
            product=burger,
            name="Extra Cheese",
            price=Decimal("15.00"),
            max_quantity=2
        )
        no_onion = ProductModifier.objects.create(
            product=burger,
            name="No Onion",
            price=Decimal("0.00")  # Free modification
        )

        # Query modifiers for a product
        modifiers = ProductModifier.objects.filter(product=product)

        # Get required modifiers
        required = ProductModifier.objects.filter(
            product=product,
            is_required=True
        )

        # Soft delete modifier (NEVER use delete())
        modifier.soft_delete()
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name=_('ID'),
        help_text=_('Unique identifier (UUID)')
    )

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='modifiers',
        verbose_name=_('Product'),
        help_text=_('Product this modifier belongs to')
    )

    name = models.CharField(
        max_length=100,
        verbose_name=_('Name'),
        help_text=_('Display name of the modifier (e.g., Extra Cheese, No Onion)')
    )

    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name=_('Price'),
        help_text=_('Additional cost for this modifier (can be 0 for free mods)')
    )

    is_default = models.BooleanField(
        default=False,
        db_index=True,
        verbose_name=_('Is default'),
        help_text=_('Whether this modifier is pre-selected by default')
    )

    is_required = models.BooleanField(
        default=False,
        db_index=True,
        verbose_name=_('Is required'),
        help_text=_('Whether the customer must select this modifier')
    )

    max_quantity = models.PositiveIntegerField(
        default=1,
        verbose_name=_('Max quantity'),
        help_text=_('Maximum times this modifier can be added to the order')
    )

    sort_order = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Sort order'),
        help_text=_('Display order within the product (lower numbers appear first)')
    )

    # Managers
    objects = SoftDeleteManager()  # Default: excludes soft-deleted
    all_objects = models.Manager()  # Includes ALL records

    class Meta:
        db_table = 'product_modifiers'
        verbose_name = _('Product Modifier')
        verbose_name_plural = _('Product Modifiers')
        ordering = ['sort_order', 'name']
        indexes = [
            models.Index(fields=['product', 'sort_order'], name='modifier_product_sort_idx'),
            models.Index(fields=['product', 'is_required'], name='modifier_product_req_idx'),
            models.Index(fields=['product', 'is_default'], name='modifier_product_default_idx'),
            models.Index(fields=['product', 'deleted_at'], name='modifier_product_deleted_idx'),
        ]

    def __str__(self) -> str:
        return f"{self.product.name} - {self.name}"

    def __repr__(self) -> str:
        return f"<ProductModifier(id={self.id}, name='{self.name}', product='{self.product.name}')>"

    @property
    def is_free(self) -> bool:
        """Check if the modifier has no additional cost."""
        return self.price == 0

    @property
    def formatted_price(self) -> str:
        """Return formatted price with currency symbol."""
        if self.is_free:
            return _('Free')
        currency_symbols = {
            'TRY': '₺',
            'USD': '$',
            'EUR': '€',
            'GBP': '£',
        }
        currency = self.product.currency
        symbol = currency_symbols.get(currency, currency)
        return f"+{symbol}{self.price:,.2f}"

    @property
    def allows_multiple(self) -> bool:
        """Check if multiple quantities of this modifier are allowed."""
        return self.max_quantity > 1

    def set_as_required(self, is_required: bool = True) -> None:
        """
        Set whether this modifier is required.

        Args:
            is_required: Whether the modifier is required
        """
        self.is_required = is_required
        self.save(update_fields=['is_required', 'updated_at'])

    def set_as_default(self, is_default: bool = True) -> None:
        """
        Set whether this modifier is pre-selected by default.

        Args:
            is_default: Whether the modifier is pre-selected
        """
        self.is_default = is_default
        self.save(update_fields=['is_default', 'updated_at'])

    def update_max_quantity(self, max_quantity: int) -> None:
        """
        Update the maximum quantity for this modifier.

        Args:
            max_quantity: New maximum quantity (must be >= 1)

        Raises:
            ValueError: If max_quantity is less than 1
        """
        if max_quantity < 1:
            raise ValueError("max_quantity must be at least 1")
        self.max_quantity = max_quantity
        self.save(update_fields=['max_quantity', 'updated_at'])

    @property
    def organization(self):
        """Get the organization this modifier belongs to via product."""
        return self.product.organization


class AllergenSeverity(models.TextChoices):
    """Allergen severity levels for product-allergen relationships."""
    CONTAINS = 'contains', _('Contains')
    MAY_CONTAIN = 'may_contain', _('May Contain')
    TRACES = 'traces', _('Traces')


class Allergen(TimeStampedMixin, SoftDeleteMixin, models.Model):
    """
    Allergen model - platform-level allergen definitions.

    Allergens are defined at the platform level (not tenant-specific) and can
    be associated with products through the ProductAllergen junction table.
    This ensures consistent allergen information across all organizations.

    Common allergens include: Gluten, Dairy, Nuts, Peanuts, Soy, Eggs,
    Fish, Shellfish, Sesame, Celery, Mustard, Lupin, Molluscs, Sulphites.

    Note:
    - This is a platform-level model (no organization FK)
    - Standard allergen definitions should be seeded at app initialization
    - Use soft_delete() - never call delete() directly

    Attributes:
        id: UUID primary key (ensures global uniqueness)
        name: Display name of the allergen (e.g., "Gluten", "Nuts")
        slug: URL-friendly identifier (globally unique)
        code: Short code for the allergen (e.g., "GLU", "NUT")
        icon: URL to allergen icon/image
        description: Detailed description of the allergen
        sort_order: Display order for consistent listing
        is_active: Whether the allergen is available for selection

    Usage:
        # Get all active allergens
        allergens = Allergen.objects.filter(is_active=True)

        # Get allergen by code
        gluten = Allergen.objects.filter(code='GLU').first()

        # Get allergen by slug
        nuts = Allergen.objects.filter(slug='nuts').first()

        # Soft delete allergen (NEVER use delete())
        allergen.soft_delete()
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name=_('ID'),
        help_text=_('Unique identifier (UUID)')
    )

    name = models.CharField(
        max_length=100,
        verbose_name=_('Name'),
        help_text=_('Display name of the allergen (e.g., Gluten, Nuts, Dairy)')
    )

    slug = models.SlugField(
        max_length=100,
        unique=True,
        verbose_name=_('Slug'),
        help_text=_('URL-friendly identifier (globally unique)')
    )

    code = models.CharField(
        max_length=10,
        unique=True,
        verbose_name=_('Code'),
        help_text=_('Short code for the allergen (e.g., GLU, NUT, DAI)')
    )

    icon = models.URLField(
        blank=True,
        null=True,
        max_length=500,
        verbose_name=_('Icon URL'),
        help_text=_('URL to allergen icon/image')
    )

    description = models.TextField(
        blank=True,
        null=True,
        verbose_name=_('Description'),
        help_text=_('Detailed description of the allergen and its sources')
    )

    sort_order = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Sort order'),
        help_text=_('Display order for consistent listing (lower numbers appear first)')
    )

    is_active = models.BooleanField(
        default=True,
        db_index=True,
        verbose_name=_('Is active'),
        help_text=_('Whether the allergen is available for selection')
    )

    # Managers
    objects = SoftDeleteManager()  # Default: excludes soft-deleted
    all_objects = models.Manager()  # Includes ALL records

    class Meta:
        db_table = 'allergens'
        verbose_name = _('Allergen')
        verbose_name_plural = _('Allergens')
        ordering = ['sort_order', 'name']
        indexes = [
            models.Index(fields=['code'], name='allergen_code_idx'),
            models.Index(fields=['slug'], name='allergen_slug_idx'),
            models.Index(fields=['is_active'], name='allergen_active_idx'),
            models.Index(fields=['deleted_at'], name='allergen_deleted_idx'),
        ]

    def __str__(self) -> str:
        return f"{self.name} ({self.code})"

    def __repr__(self) -> str:
        return f"<Allergen(id={self.id}, name='{self.name}', code='{self.code}')>"

    @property
    def is_available(self) -> bool:
        """Check if allergen is active and not deleted."""
        return self.is_active and not self.is_deleted


class ProductAllergen(TimeStampedMixin, SoftDeleteMixin, models.Model):
    """
    ProductAllergen model - junction table for product-allergen relationships.

    This model links products to allergens with additional information about
    the severity level (contains, may contain, traces) and optional notes.
    This allows for accurate allergen labeling on menus.

    Critical Rules:
    - EVERY query should consider tenant context via product
    - Use soft_delete() - never call delete() directly
    - A product should not have duplicate allergen entries

    Attributes:
        id: UUID primary key (ensures global uniqueness)
        product: FK to Product (links to tenant via product.organization)
        allergen: FK to platform-level Allergen
        severity: Level of allergen presence (contains/may_contain/traces)
        notes: Optional additional notes about the allergen in this product

    Usage:
        # Add allergen to product
        product_allergen = ProductAllergen.objects.create(
            product=pizza,
            allergen=gluten_allergen,
            severity=AllergenSeverity.CONTAINS,
            notes="Contains wheat flour in the crust"
        )

        # Get all allergens for a product
        product_allergens = ProductAllergen.objects.filter(product=product)

        # Get products containing a specific allergen
        products_with_gluten = ProductAllergen.objects.filter(
            allergen=gluten_allergen,
            product__organization=org
        ).select_related('product')

        # Soft delete (NEVER use delete())
        product_allergen.soft_delete()
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name=_('ID'),
        help_text=_('Unique identifier (UUID)')
    )

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='product_allergens',
        verbose_name=_('Product'),
        help_text=_('Product this allergen association belongs to')
    )

    allergen = models.ForeignKey(
        Allergen,
        on_delete=models.CASCADE,
        related_name='product_allergens',
        verbose_name=_('Allergen'),
        help_text=_('The allergen associated with this product')
    )

    severity = models.CharField(
        max_length=20,
        choices=AllergenSeverity.choices,
        default=AllergenSeverity.CONTAINS,
        verbose_name=_('Severity'),
        help_text=_('Level of allergen presence (contains/may_contain/traces)')
    )

    notes = models.TextField(
        blank=True,
        null=True,
        verbose_name=_('Notes'),
        help_text=_('Optional additional notes about this allergen in the product')
    )

    # Managers
    objects = SoftDeleteManager()  # Default: excludes soft-deleted
    all_objects = models.Manager()  # Includes ALL records

    class Meta:
        db_table = 'product_allergens'
        verbose_name = _('Product Allergen')
        verbose_name_plural = _('Product Allergens')
        ordering = ['allergen__sort_order', 'allergen__name']
        unique_together = [['product', 'allergen']]
        indexes = [
            models.Index(fields=['product', 'allergen'], name='prod_allergen_prod_all_idx'),
            models.Index(fields=['allergen', 'severity'], name='prod_allergen_sev_idx'),
            models.Index(fields=['product', 'deleted_at'], name='prod_allergen_deleted_idx'),
        ]

    def __str__(self) -> str:
        return f"{self.product.name} - {self.allergen.name} ({self.severity})"

    def __repr__(self) -> str:
        return f"<ProductAllergen(product='{self.product.name}', allergen='{self.allergen.name}')>"

    @property
    def organization(self):
        """Get the organization this product allergen belongs to via product."""
        return self.product.organization

    @property
    def severity_display(self) -> str:
        """Get human-readable severity display."""
        return self.get_severity_display()


class NutritionInfo(TimeStampedMixin, SoftDeleteMixin, models.Model):
    """
    NutritionInfo model - one-to-one nutritional data per product.

    This model stores detailed nutritional information for products,
    including standard nutrients (calories, protein, carbs, fat, etc.)
    and allows for custom nutrients via a JSON field.

    Critical Rules:
    - One-to-one relationship with Product
    - EVERY query should consider tenant context via product
    - Use soft_delete() - never call delete() directly
    - Nutrient values are per serving (specified by serving_size)

    Attributes:
        id: UUID primary key (ensures global uniqueness)
        product: OneToOne to Product
        serving_size: Description of serving size (e.g., "100g", "1 portion")
        serving_size_grams: Numeric serving size in grams
        calories: Energy in kcal
        protein: Protein in grams
        carbohydrates: Total carbohydrates in grams
        sugar: Sugar content in grams
        fiber: Dietary fiber in grams
        fat: Total fat in grams
        saturated_fat: Saturated fat in grams
        trans_fat: Trans fat in grams
        cholesterol: Cholesterol in mg
        sodium: Sodium in mg
        potassium: Potassium in mg
        calcium: Calcium in mg (% DV or mg)
        iron: Iron in mg (% DV or mg)
        vitamin_a: Vitamin A (IU or % DV)
        vitamin_c: Vitamin C (mg or % DV)
        custom_nutrients: JSON field for additional nutrients

    Usage:
        # Create nutrition info for a product
        nutrition = NutritionInfo.objects.create(
            product=pizza,
            serving_size="1 slice (125g)",
            serving_size_grams=125,
            calories=285,
            protein=Decimal("12.0"),
            carbohydrates=Decimal("36.0"),
            fat=Decimal("10.5")
        )

        # Get nutrition info for a product
        nutrition = NutritionInfo.objects.filter(product=product).first()
        # Or via the product
        nutrition = product.nutrition_info

        # Soft delete (NEVER use delete())
        nutrition.soft_delete()
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name=_('ID'),
        help_text=_('Unique identifier (UUID)')
    )

    product = models.OneToOneField(
        Product,
        on_delete=models.CASCADE,
        related_name='nutrition_info',
        verbose_name=_('Product'),
        help_text=_('Product this nutrition info belongs to')
    )

    # Serving information
    serving_size = models.CharField(
        max_length=100,
        default='100g',
        verbose_name=_('Serving size'),
        help_text=_('Description of serving size (e.g., "100g", "1 portion", "1 slice")')
    )

    serving_size_grams = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name=_('Serving size (grams)'),
        help_text=_('Numeric serving size in grams for calculations')
    )

    # Energy
    calories = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name=_('Calories'),
        help_text=_('Energy in kcal per serving')
    )

    # Macronutrients (in grams)
    protein = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name=_('Protein'),
        help_text=_('Protein in grams per serving')
    )

    carbohydrates = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name=_('Carbohydrates'),
        help_text=_('Total carbohydrates in grams per serving')
    )

    sugar = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name=_('Sugar'),
        help_text=_('Sugar content in grams per serving')
    )

    fiber = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name=_('Fiber'),
        help_text=_('Dietary fiber in grams per serving')
    )

    fat = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name=_('Fat'),
        help_text=_('Total fat in grams per serving')
    )

    saturated_fat = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name=_('Saturated fat'),
        help_text=_('Saturated fat in grams per serving')
    )

    trans_fat = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name=_('Trans fat'),
        help_text=_('Trans fat in grams per serving')
    )

    # Micronutrients
    cholesterol = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name=_('Cholesterol'),
        help_text=_('Cholesterol in mg per serving')
    )

    sodium = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name=_('Sodium'),
        help_text=_('Sodium in mg per serving')
    )

    potassium = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name=_('Potassium'),
        help_text=_('Potassium in mg per serving')
    )

    calcium = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name=_('Calcium'),
        help_text=_('Calcium in mg per serving')
    )

    iron = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name=_('Iron'),
        help_text=_('Iron in mg per serving')
    )

    # Vitamins
    vitamin_a = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name=_('Vitamin A'),
        help_text=_('Vitamin A in IU or mcg per serving')
    )

    vitamin_c = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name=_('Vitamin C'),
        help_text=_('Vitamin C in mg per serving')
    )

    # Flexible field for additional nutrients
    custom_nutrients = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_('Custom nutrients'),
        help_text=_('Additional nutrients not covered by standard fields (JSON)')
    )

    # Managers
    objects = SoftDeleteManager()  # Default: excludes soft-deleted
    all_objects = models.Manager()  # Includes ALL records

    class Meta:
        db_table = 'nutrition_info'
        verbose_name = _('Nutrition Info')
        verbose_name_plural = _('Nutrition Info')
        indexes = [
            models.Index(fields=['product'], name='nutrition_product_idx'),
            models.Index(fields=['deleted_at'], name='nutrition_deleted_idx'),
        ]

    def __str__(self) -> str:
        return f"Nutrition: {self.product.name}"

    def __repr__(self) -> str:
        return f"<NutritionInfo(product='{self.product.name}', calories={self.calories})>"

    @property
    def organization(self):
        """Get the organization this nutrition info belongs to via product."""
        return self.product.organization

    @property
    def has_macros(self) -> bool:
        """Check if any macronutrient data is available."""
        return any([
            self.protein is not None,
            self.carbohydrates is not None,
            self.fat is not None
        ])

    @property
    def has_vitamins(self) -> bool:
        """Check if any vitamin data is available."""
        return any([
            self.vitamin_a is not None,
            self.vitamin_c is not None
        ])

    @property
    def has_minerals(self) -> bool:
        """Check if any mineral data is available."""
        return any([
            self.calcium is not None,
            self.iron is not None,
            self.sodium is not None,
            self.potassium is not None
        ])

    def get_macros_summary(self) -> dict:
        """
        Get a summary of macronutrients.

        Returns:
            Dictionary with protein, carbs, and fat values (or None if not set)
        """
        return {
            'protein': self.protein,
            'carbohydrates': self.carbohydrates,
            'fat': self.fat,
            'fiber': self.fiber,
            'sugar': self.sugar,
        }

    def get_custom_nutrient(self, key: str, default=None):
        """
        Get a value from custom nutrients.

        Args:
            key: The nutrient key to retrieve
            default: Default value if key not found

        Returns:
            The nutrient value or default
        """
        return self.custom_nutrients.get(key, default)

    def set_custom_nutrient(self, key: str, value) -> None:
        """
        Set a value in custom nutrients.

        Args:
            key: The nutrient key
            value: The value to set
        """
        self.custom_nutrients[key] = value
        self.save(update_fields=['custom_nutrients', 'updated_at'])

    def calculate_calories_from_macros(self) -> int:
        """
        Calculate estimated calories from macronutrients.

        Uses standard conversion factors:
        - Protein: 4 kcal/g
        - Carbohydrates: 4 kcal/g
        - Fat: 9 kcal/g

        Returns:
            Estimated calories, or 0 if no macro data available
        """
        calories = 0
        if self.protein:
            calories += float(self.protein) * 4
        if self.carbohydrates:
            calories += float(self.carbohydrates) * 4
        if self.fat:
            calories += float(self.fat) * 9
        return round(calories)