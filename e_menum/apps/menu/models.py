"""
Django ORM models for the Menu application.

This module defines the menu-related models for E-Menum:
- Theme: Menu styling customization with colors, fonts, and CSS options
- Menu: Restaurant menu container (to be added in subtask-4-3)
- Category: Product categories with nested support (to be added in subtask-4-3)
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
