"""
Django production settings for E-Menum project.

This file contains settings specific to the production environment.
Extends base.py with production-optimized security and performance settings.

IMPORTANT: Never commit sensitive values to this file.
All secrets should come from environment variables.
"""

import logging
import os

from .base import *  # noqa: F401, F403

# =============================================================================
# DEBUG & SECURITY
# =============================================================================

# CRITICAL: Debug must be False in production
DEBUG = False

# SECURITY WARNING: Set this to your actual production domain(s)
ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=[  # noqa: F405
    'e-menum.com',
    'www.e-menum.com',
    'api.e-menum.com',
])

# CSRF trusted origins for production
CSRF_TRUSTED_ORIGINS = env.list('CSRF_TRUSTED_ORIGINS', default=[  # noqa: F405
    'https://e-menum.com',
    'https://www.e-menum.com',
    'https://api.e-menum.com',
])


# =============================================================================
# SECRET KEY
# =============================================================================

# CRITICAL: Secret key MUST be set via environment variable in production
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY')

if not SECRET_KEY:
    raise ValueError(
        'DJANGO_SECRET_KEY environment variable is required in production. '
        'Generate a secure key using: python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"'
    )


# =============================================================================
# DATABASE
# =============================================================================

# Production MUST use PostgreSQL via DATABASE_URL
DATABASE_URL = os.environ.get('DATABASE_URL')

if not DATABASE_URL:
    raise ValueError(
        'DATABASE_URL environment variable is required in production. '
        'Format: postgresql://user:password@host:port/database'
    )

try:
    import dj_database_url
    DATABASES = {
        'default': dj_database_url.config(
            default=DATABASE_URL,
            conn_max_age=600,  # 10 minutes connection pooling
            conn_health_checks=True,
            ssl_require=env.bool('DATABASE_SSL_REQUIRE', default=False),  # noqa: F405
        )
    }
except ImportError:
    # Fallback to manual parsing if dj_database_url not available
    db_config = env.db_url() if hasattr(env, 'db_url') else None  # noqa: F405
    if db_config:
        DATABASES = {'default': db_config}
        DATABASES['default']['CONN_MAX_AGE'] = 600
    else:
        raise ValueError('Unable to parse DATABASE_URL. Install dj-database-url package.')


# =============================================================================
# CACHING
# =============================================================================

# Production uses Redis for caching (required)
REDIS_URL = os.environ.get('REDIS_URL')

if REDIS_URL:
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.redis.RedisCache',
            'LOCATION': REDIS_URL,
            'KEY_PREFIX': 'emenum_prod',
            'OPTIONS': {
                'socket_connect_timeout': 5,
                'socket_timeout': 5,
                'retry_on_timeout': True,
            }
        }
    }
else:
    # Log warning if Redis is not configured
    import logging
    logger = logging.getLogger(__name__)
    logger.warning(
        'REDIS_URL not set in production. Using local memory cache. '
        'This is not recommended for multi-process deployments.'
    )
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            'LOCATION': 'emenum-prod-cache',
        }
    }


# =============================================================================
# EMAIL
# =============================================================================

# Production email configuration
EMAIL_BACKEND = os.environ.get(
    'EMAIL_BACKEND',
    'django.core.mail.backends.smtp.EmailBackend'
)

# Validate email configuration in production
if EMAIL_BACKEND == 'django.core.mail.backends.smtp.EmailBackend':
    if not os.environ.get('EMAIL_HOST'):
        import logging
        logger = logging.getLogger(__name__)
        logger.warning('EMAIL_HOST not set. Email sending may fail.')


# =============================================================================
# SECURITY SETTINGS (Production-Hardened)
# =============================================================================

# XSS Protection
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# HTTPS enforcement
SECURE_SSL_REDIRECT = env.bool('SECURE_SSL_REDIRECT', default=True)  # noqa: F405
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# HTTP Strict Transport Security (HSTS)
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True  # Allow HSTS preload list submission

# Cookie security
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_SAMESITE = 'Lax'

# Session security
SESSION_COOKIE_AGE = 60 * 60 * 24 * 7  # 1 week
SESSION_EXPIRE_AT_BROWSER_CLOSE = False

# Referrer policy
SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'

# Content Security Policy (CSP) headers would be set in nginx/reverse proxy


# =============================================================================
# STATIC FILES
# =============================================================================

# Use WhiteNoise for serving static files efficiently
# Uncomment when whitenoise is installed
# STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Ensure static files are collected
STATIC_ROOT = BASE_DIR / 'staticfiles'  # noqa: F405


# =============================================================================
# MEDIA FILES
# =============================================================================

# In production, consider using S3 or similar for media files
# DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
# AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
# AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
# AWS_STORAGE_BUCKET_NAME = os.environ.get('AWS_STORAGE_BUCKET_NAME')


# =============================================================================
# CORS CONFIGURATION
# =============================================================================

# Production CORS settings - strict whitelist
CORS_ALLOWED_ORIGINS = env.list('CORS_ALLOWED_ORIGINS', default=[  # noqa: F405
    'https://e-menum.com',
    'https://www.e-menum.com',
])

# Disable CORS allow all origins in production
CORS_ALLOW_ALL_ORIGINS = False


# =============================================================================
# LOGGING (Production-Optimized)
# =============================================================================

# Production logging configuration with JSON format for log aggregation
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'json': {
            'format': '{"level": "%(levelname)s", "time": "%(asctime)s", "module": "%(module)s", "process": %(process)d, "message": "%(message)s"}',
        },
    },
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'json',  # JSON format for production
        },
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler',
            'include_html': False,
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'WARNING',  # Only warnings and above in production
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False,
        },
        'django.request': {
            'handlers': ['console', 'mail_admins'],
            'level': 'ERROR',
            'propagate': False,
        },
        'django.security': {
            'handlers': ['console', 'mail_admins'],
            'level': 'ERROR',
            'propagate': False,
        },
        'django.db.backends': {
            'handlers': ['console'],
            'level': 'ERROR',  # Only log DB errors in production
            'propagate': False,
        },
        'apps': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'celery': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False,
        },
    },
}


# =============================================================================
# CELERY (Production Configuration)
# =============================================================================

# Celery broker must be Redis in production
CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL')
CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND')

# Task execution settings (production-tuned)
CELERY_TASK_ALWAYS_EAGER = False  # Never run tasks synchronously in production
CELERY_TASK_SOFT_TIME_LIMIT = 300  # 5 minutes soft limit
CELERY_TASK_TIME_LIMIT = 600  # 10 minutes hard limit

# Worker settings
CELERY_WORKER_PREFETCH_MULTIPLIER = 4  # Better throughput in production


# =============================================================================
# SENTRY (Error Tracking - Required in Production)
# =============================================================================

SENTRY_DSN = os.environ.get('SENTRY_DSN')
if SENTRY_DSN:
    try:
        import sentry_sdk
        from sentry_sdk.integrations.django import DjangoIntegration
        from sentry_sdk.integrations.celery import CeleryIntegration
        from sentry_sdk.integrations.redis import RedisIntegration
        from sentry_sdk.integrations.logging import LoggingIntegration

        # Configure Sentry logging integration
        sentry_logging = LoggingIntegration(
            level=logging.INFO,  # Capture info and above as breadcrumbs
            event_level=logging.ERROR,  # Send errors as events
        )

        sentry_sdk.init(
            dsn=SENTRY_DSN,
            integrations=[
                DjangoIntegration(),
                CeleryIntegration(),
                RedisIntegration(),
                sentry_logging,
            ],
            environment='production',
            traces_sample_rate=0.1,  # 10% of transactions for performance monitoring
            profiles_sample_rate=0.1,  # 10% profiling (if enabled)
            send_default_pii=False,  # CRITICAL: Don't send PII data
            attach_stacktrace=True,
            release=os.environ.get('RELEASE_VERSION', 'unknown'),
        )
    except ImportError:
        import logging
        logger = logging.getLogger(__name__)
        logger.warning('Sentry SDK not installed. Error tracking disabled.')
else:
    import logging
    logger = logging.getLogger(__name__)
    logger.warning(
        'SENTRY_DSN not set in production. Error tracking disabled. '
        'This is not recommended for production deployments.'
    )


# =============================================================================
# REST FRAMEWORK (Production Overrides)
# =============================================================================

# Disable browsable API in production for security
REST_FRAMEWORK['DEFAULT_RENDERER_CLASSES'] = [  # noqa: F405
    'rest_framework.renderers.JSONRenderer',
]

# Stricter throttling in production
REST_FRAMEWORK['DEFAULT_THROTTLE_RATES'] = {  # noqa: F405
    'anon': '50/hour',  # Stricter for anonymous users
    'user': '1000/hour',
}


# =============================================================================
# ADMIN CUSTOMIZATION
# =============================================================================

# Customize admin URL for security (optional)
# ADMIN_URL = os.environ.get('ADMIN_URL', 'admin/')


# =============================================================================
# PERFORMANCE OPTIMIZATIONS
# =============================================================================

# Template caching (enabled by default when DEBUG=False)
# TEMPLATES[0]['OPTIONS']['loaders'] = [
#     ('django.template.loaders.cached.Loader', [
#         'django.template.loaders.filesystem.Loader',
#         'django.template.loaders.app_directories.Loader',
#     ]),
# ]


# =============================================================================
# HEALTH CHECK ENDPOINT
# =============================================================================

# Allow health check endpoint from load balancer
# Add to ALLOWED_HOSTS if using internal health checks
HEALTH_CHECK_PATH = os.environ.get('HEALTH_CHECK_PATH', '/health/')
