"""
Shared utilities and components for E-Menum Django application.

This package contains cross-cutting concerns that are shared across
all Django apps in the E-Menum project:

- middleware: Custom middleware (tenant isolation, request logging, etc.)
- permissions: RBAC/ABAC permission classes and utilities
- serializers: Base DRF serializers with common functionality
- views: Base view classes with tenant-aware operations
- utils: General utility functions and helpers

Usage:
    from shared import middleware, permissions
    from shared.views import TenantViewSet
    from shared.serializers import TenantModelSerializer
"""

# Version info
__version__ = "1.0.0"

# Expose submodules for convenient imports
from . import middleware
from . import permissions
from . import serializers
from . import views
from . import utils

__all__ = [
    "middleware",
    "permissions",
    "serializers",
    "views",
    "utils",
    "__version__",
]
