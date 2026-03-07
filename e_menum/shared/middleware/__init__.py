"""
Custom middleware for E-Menum Django application.

This module contains middleware classes that handle cross-cutting concerns:

- TenantMiddleware: Multi-tenant context injection (organization scoping)
- RequestLoggingMiddleware: Request/response logging for debugging
- RateLimitMiddleware: API rate limiting per organization/user

Middleware Order (Critical):
    The middleware order in settings/base.py is critical:
    1. SecurityMiddleware
    2. WhiteNoiseMiddleware (after SecurityMiddleware)
    3. CorsMiddleware (before CommonMiddleware)
    4. SessionMiddleware
    5. CommonMiddleware
    6. CsrfViewMiddleware
    7. AuthenticationMiddleware
    8. TenantMiddleware (AFTER AuthenticationMiddleware - needs user context)
    9. MessageMiddleware
    10. XFrameOptionsMiddleware

Usage:
    # In settings/base.py:
    MIDDLEWARE = [
        ...
        'shared.middleware.tenant.TenantMiddleware',
        ...
    ]
"""

# Middleware classes implemented in separate files and exported here for clean imports

from shared.middleware.tenant import (
    TenantMiddleware,
    TenantContextMixin,
    get_current_organization,
    set_current_organization,
)

__all__ = [
    "TenantMiddleware",
    "TenantContextMixin",
    "get_current_organization",
    "set_current_organization",
]
