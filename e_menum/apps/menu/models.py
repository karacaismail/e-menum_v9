"""
Django ORM models for the Menu application.

This module defines the menu-related models for E-Menum:
- Theme: Menu styling customization with colors, fonts, and CSS options
- Menu: Restaurant menu container for organizing categories and products
- Category: Product categories with nested support (hierarchical structure)
- Product: Individual menu items (to be added in subtask-4-4)
- ProductVariant: Size/portion options (to be added in subtask-4-5)
- ProductModifier: Add-on options (to be added in subtask-4-5)
- Allergen: Platform-level allergen definitions (to be added in subtask-4-6)
- ProductAllergen: Junction table for product-allergen relationships (to be added in subtask-4-6)
- NutritionInfo: One-to-one nutritional data per product (to be added in subtask-4-6)

Critical Rules:
- Every query MUST include organization_id for tenant isolation
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
