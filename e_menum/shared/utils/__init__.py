"""
Utility functions and helpers for E-Menum Django application.

This module provides general-purpose utility functions used
across the application:

- Slug generation with uniqueness validation
- UUID utilities (validation, generation)
- Date/time helpers (timezone-aware operations)
- String manipulation (truncation, sanitization)
- Pagination utilities
- Error code definitions and helpers

Common Utilities:
    - generate_unique_slug(model, field, value): Generate unique slug
    - soft_delete(instance): Mark instance as deleted
    - is_valid_uuid(value): Validate UUID string format
    - get_client_ip(request): Extract client IP from request
    - paginate_queryset(queryset, page, per_page): Manual pagination

Error Codes:
    Centralized error code definitions for consistent API responses.
    Format: RESOURCE_ACTION_ERROR (e.g., MENU_NOT_FOUND, ORDER_INVALID_STATUS)

Usage:
    from shared.utils import generate_unique_slug, soft_delete

    slug = generate_unique_slug(Menu, 'slug', 'My Menu Name')
    soft_delete(menu_instance)
"""

# Utility functions will be implemented in separate files
# and exported here for clean imports

from shared.utils.exceptions import (
    ErrorCodes,
    AppException,
    AuthenticationException,
    PermissionException,
    ResourceNotFoundException,
    BusinessLogicException,
    custom_exception_handler,
)

__all__ = [
    'ErrorCodes',
    'AppException',
    'AuthenticationException',
    'PermissionException',
    'ResourceNotFoundException',
    'BusinessLogicException',
    'custom_exception_handler',
]
