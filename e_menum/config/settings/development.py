"""
Django development settings for E-Menum project.

This file contains settings specific to the development environment.
Extends base.py with development-friendly overrides.
"""

from .base import *  # noqa: F401, F403

# =============================================================================
# DEBUG & SECURITY
# =============================================================================

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# Allow all hosts in development
ALLOWED_HOSTS = ['*']

# Development secret key (DO NOT use in production!)
SECRET_KEY = 'django-insecure-dev-key-for-local-development-only-change-in-prod'


# =============================================================================
# DATABASE
# =============================================================================

# Database - SQLite for development (easy setup, no external dependencies)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',  # noqa: F405
    }
}


# =============================================================================
# CACHING
# =============================================================================

# Use local memory cache in development
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
    }
}


# =============================================================================
# EMAIL
# =============================================================================

# Email backend for development - print to console
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'


# =============================================================================
# LOGGING
# =============================================================================

# Simplified logging for development
LOGGING['root']['level'] = 'DEBUG'  # noqa: F405
LOGGING['loggers']['django']['level'] = 'DEBUG'  # noqa: F405


# =============================================================================
# SECURITY RELAXATION (Development Only!)
# =============================================================================

# Disable password validation in development for easier testing
AUTH_PASSWORD_VALIDATORS = []

# Allow HTTP (not just HTTPS) in development
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

# CORS - Allow all origins in development
# CORS_ALLOW_ALL_ORIGINS = True  # Uncomment when corsheaders is installed


# =============================================================================
# INTERNAL IPS (required for debug context processor → Tailwind CDN in dev)
# =============================================================================

INTERNAL_IPS = ['127.0.0.1', 'localhost']

# DEBUG TOOLBAR (Optional)
# =============================================================================

# Uncomment when django-debug-toolbar is installed
# INSTALLED_APPS += ['debug_toolbar']  # noqa: F405
# MIDDLEWARE.insert(0, 'debug_toolbar.middleware.DebugToolbarMiddleware')  # noqa: F405


# =============================================================================
# DJANGO EXTENSIONS (Optional)
# =============================================================================

# Uncomment when django-extensions is installed
# INSTALLED_APPS += ['django_extensions']  # noqa: F405
