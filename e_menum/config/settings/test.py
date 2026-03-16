"""
Django test settings for E-Menum project.

Optimized for fast test execution in CI and local environments.
Uses SQLite in-memory, disables unnecessary middleware, and uses
fast password hashing.
"""

from .base import *  # noqa: F401, F403

# =============================================================================
# DEBUG & SECURITY
# =============================================================================

DEBUG = False
SECRET_KEY = "django-insecure-test-key-only-for-ci-testing"
ALLOWED_HOSTS = ["*"]

# =============================================================================
# DATABASE — SQLite in-memory for speed
# =============================================================================

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

# =============================================================================
# CACHING — Local memory
# =============================================================================

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    }
}

# =============================================================================
# PASSWORD HASHING — Fast hasher for tests
# =============================================================================

PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

AUTH_PASSWORD_VALIDATORS = []

# =============================================================================
# EMAIL — In-memory backend
# =============================================================================

EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

# =============================================================================
# CELERY — Eager execution (no broker needed)
# =============================================================================

CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True
CELERY_BROKER_URL = "memory://"
CELERY_RESULT_BACKEND = "cache+memory://"

# =============================================================================
# MEDIA & STATIC — Use in-memory storage
# =============================================================================

DEFAULT_FILE_STORAGE = "django.core.files.storage.InMemoryStorage"
STATICFILES_STORAGE = "django.contrib.staticfiles.storage.StaticFilesStorage"

# =============================================================================
# SECURITY RELAXATION
# =============================================================================

SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
SECURE_SSL_REDIRECT = False

# =============================================================================
# LOGGING — Minimal output during tests
# =============================================================================

LOGGING = {
    "version": 1,
    "disable_existing_loggers": True,
    "handlers": {
        "null": {
            "class": "logging.NullHandler",
        },
    },
    "root": {
        "handlers": ["null"],
        "level": "CRITICAL",
    },
}
