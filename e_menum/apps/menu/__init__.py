"""
E-Menum Menu Application.

This app provides the complete menu management system:
- Menu: Main menu entity with branding and settings
- Category: Menu sections with ordering and visibility
- Product: Menu items with variants, modifiers, and pricing
- Allergen: Food allergen definitions and product mappings
- Theme: Menu visual customization and styling

Critical Rules:
- Every query MUST include organizationId for tenant isolation
- All entities use soft delete (deleted_at timestamp)
- No physical deletions allowed
- Products must have at least one variant (base variant)
"""

default_app_config = 'apps.menu.apps.MenuConfig'
