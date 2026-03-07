"""
Django staging settings for E-Menum project.

This file contains settings specific to the staging environment.
Extends base.py with staging-specific overrides.

Staging is designed to closely mirror production while allowing
for some debugging capabilities.
"""

import os

from .base import *  # noqa: F401, F403

# =============================================================================
# DEBUG & SECURITY
# =============================================================================

# Staging uses DEBUG=False to mimic production behavior
DEBUG = False

# SECURITY WARNING: Set this to your actual staging domain(s)
ALLOWED_HOSTS = env.list(
    "ALLOWED_HOSTS",
    default=[  # noqa: F405
        f"staging.{SITE_DOMAIN}",  # noqa: F405
        f"staging-api.{SITE_DOMAIN}",  # noqa: F405
    ],
)

# CSRF trusted origins for staging
CSRF_TRUSTED_ORIGINS = env.list(
    "CSRF_TRUSTED_ORIGINS",
    default=[  # noqa: F405
        f"https://staging.{SITE_DOMAIN}",  # noqa: F405
        f"https://staging-api.{SITE_DOMAIN}",  # noqa: F405
    ],
)


# =============================================================================
# SECRET KEY
# =============================================================================

# SECURITY WARNING: keep the secret key used in production secret!
# In staging, this should be set via environment variable
SECRET_KEY = os.environ.get(
    "DJANGO_SECRET_KEY",
    "django-insecure-staging-key-change-this-via-environment-variable",
)


# =============================================================================
# DATABASE
# =============================================================================

# Staging uses PostgreSQL via DATABASE_URL
# If DATABASE_URL is not set, fallback to SQLite for testing
DATABASE_URL = os.environ.get("DATABASE_URL")

if DATABASE_URL:
    try:
        import dj_database_url

        DATABASES = {
            "default": dj_database_url.config(
                default=DATABASE_URL,
                conn_max_age=60,
                conn_health_checks=True,
            )
        }
    except ImportError:
        # Use fallback parser from base.py
        db_config = env.db_url() if hasattr(env, "db_url") else None  # noqa: F405
        if db_config:
            DATABASES = {"default": db_config}
else:
    # Fallback to SQLite if no DATABASE_URL (for testing)
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db_staging.sqlite3",  # noqa: F405
        }
    }


# =============================================================================
# CACHING
# =============================================================================

# Staging uses Redis for caching if available
REDIS_URL = os.environ.get("REDIS_URL")

if REDIS_URL:
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.redis.RedisCache",
            "LOCATION": REDIS_URL,
            "KEY_PREFIX": "emenum_staging",
            "OPTIONS": {
                "socket_connect_timeout": 5,
                "socket_timeout": 5,
            },
        }
    }
else:
    # Fallback to local memory cache
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "emenum-staging-cache",
        }
    }


# =============================================================================
# EMAIL
# =============================================================================

# Staging email configuration - use actual SMTP but consider using a test inbox
EMAIL_BACKEND = os.environ.get(
    "EMAIL_BACKEND", "django.core.mail.backends.smtp.EmailBackend"
)


# =============================================================================
# SECURITY SETTINGS
# =============================================================================

# Enable security features for staging (mimics production)
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"

# HTTPS settings - enable if staging uses HTTPS
SECURE_SSL_REDIRECT = env.bool("SECURE_SSL_REDIRECT", default=True)  # noqa: F405
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# HSTS settings (shorter duration for staging)
SECURE_HSTS_SECONDS = 3600  # 1 hour (shorter than production)
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = False  # Don't preload in staging

# Cookie security
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True


# =============================================================================
# STATIC FILES
# =============================================================================

# Use WhiteNoise for serving static files efficiently
# Uncomment when whitenoise is installed
# STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'


# =============================================================================
# CORS CONFIGURATION
# =============================================================================

# Staging-specific CORS settings
CORS_ALLOWED_ORIGINS = env.list(
    "CORS_ALLOWED_ORIGINS",
    default=[  # noqa: F405
        f"https://staging.{SITE_DOMAIN}",  # noqa: F405
    ],
)


# =============================================================================
# LOGGING
# =============================================================================

# Staging logging - more verbose than production, less than development
LOGGING["root"]["level"] = "INFO"  # noqa: F405
LOGGING["loggers"]["django"]["level"] = "INFO"  # noqa: F405
LOGGING["loggers"]["apps"]["level"] = "DEBUG"  # noqa: F405

# Add file logging for staging
LOGGING["handlers"]["file"] = {  # noqa: F405
    "class": "logging.handlers.RotatingFileHandler",
    "filename": os.path.join(BASE_DIR.parent, "logs", "staging.log"),  # noqa: F405
    "maxBytes": 10 * 1024 * 1024,  # 10 MB
    "backupCount": 5,
    "formatter": "verbose",  # noqa: F405
}


# =============================================================================
# CELERY
# =============================================================================

# Celery configuration for staging
CELERY_TASK_ALWAYS_EAGER = env.bool("CELERY_TASK_ALWAYS_EAGER", default=False)  # noqa: F405


# =============================================================================
# SENTRY (Error Tracking)
# =============================================================================

# Sentry configuration for staging
SENTRY_DSN = os.environ.get("SENTRY_DSN")
if SENTRY_DSN:
    try:
        import sentry_sdk
        from sentry_sdk.integrations.django import DjangoIntegration
        from sentry_sdk.integrations.celery import CeleryIntegration
        from sentry_sdk.integrations.redis import RedisIntegration

        sentry_sdk.init(
            dsn=SENTRY_DSN,
            integrations=[
                DjangoIntegration(),
                CeleryIntegration(),
                RedisIntegration(),
            ],
            environment="staging",
            traces_sample_rate=0.2,  # 20% of transactions for performance monitoring
            send_default_pii=False,  # Don't send PII data
        )
    except ImportError:
        pass  # Sentry SDK not installed


# =============================================================================
# DEBUG TOOLBAR (Conditionally enabled in staging)
# =============================================================================

# Allow debug toolbar for specific IPs in staging
STAGING_DEBUG_IPS = env.list("STAGING_DEBUG_IPS", default=[])  # noqa: F405

if STAGING_DEBUG_IPS:
    try:
        import debug_toolbar  # noqa: F401

        INSTALLED_APPS += ["debug_toolbar"]  # noqa: F405
        MIDDLEWARE.insert(0, "debug_toolbar.middleware.DebugToolbarMiddleware")  # noqa: F405
        INTERNAL_IPS = STAGING_DEBUG_IPS
    except ImportError:
        pass
