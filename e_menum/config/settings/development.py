"""
Django development settings for E-Menum project.

This file contains settings specific to the development environment.
Extends base.py with development-friendly overrides.

Supports two modes:
  - Docker: DATABASE_URL env var → PostgreSQL, REDIS_URL → Redis cache
  - Bare metal: No env vars → SQLite + local memory cache
"""

import os

from .base import *  # noqa: F401, F403

# =============================================================================
# DEBUG & SECURITY
# =============================================================================

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# Allow all hosts in development
ALLOWED_HOSTS = ['*']

# Development secret key (DO NOT use in production!)
SECRET_KEY = os.environ.get(
    'DJANGO_SECRET_KEY',
    'django-insecure-dev-key-for-local-development-only-change-in-prod',
)


# =============================================================================
# DATABASE
# =============================================================================

# If DATABASE_URL is set (Docker), use PostgreSQL; otherwise fall back to SQLite
_DATABASE_URL = os.environ.get('DATABASE_URL')

if _DATABASE_URL:
    try:
        import dj_database_url
        DATABASES = {
            'default': dj_database_url.config(
                default=_DATABASE_URL,
                conn_max_age=0,
                ssl_require=False,
            )
        }
    except ImportError:
        # Manual parse if dj_database_url is not installed
        from urllib.parse import urlparse
        _parsed = urlparse(_DATABASE_URL)
        DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.postgresql',
                'NAME': _parsed.path[1:],
                'USER': _parsed.username or '',
                'PASSWORD': _parsed.password or '',
                'HOST': _parsed.hostname or 'localhost',
                'PORT': str(_parsed.port) if _parsed.port else '5432',
            }
        }
else:
    # Bare metal development — no Docker required
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',  # noqa: F405
        }
    }


# =============================================================================
# CACHING
# =============================================================================

# If REDIS_URL is set (Docker), use Redis cache; otherwise local memory
_REDIS_URL = os.environ.get('REDIS_URL')

if _REDIS_URL:
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.redis.RedisCache',
            'LOCATION': _REDIS_URL,
            'KEY_PREFIX': 'emenum_dev',
        }
    }
else:
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            'LOCATION': 'unique-snowflake',
        }
    }


# =============================================================================
# CELERY
# =============================================================================

# If CELERY_BROKER_URL is set (Docker), use Redis; otherwise run tasks eagerly
_CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL')

if _CELERY_BROKER_URL:
    CELERY_BROKER_URL = _CELERY_BROKER_URL
    CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND', _CELERY_BROKER_URL)
    CELERY_TASK_ALWAYS_EAGER = False
else:
    CELERY_TASK_ALWAYS_EAGER = True
    CELERY_TASK_EAGER_PROPAGATES = True


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
