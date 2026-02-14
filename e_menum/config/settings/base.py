"""
Django base settings for E-Menum Enterprise QR Menu SaaS.

This file contains settings that are common across all environments.
Environment-specific settings are in development.py, staging.py, and production.py

For more information on this file, see
https://docs.djangoproject.com/en/5.0/topics/settings/
"""

import os
from datetime import timedelta
from pathlib import Path

# Try to use django-environ if available, fallback to os.environ
try:
    import environ
    env = environ.Env(
        # Set defaults
        DEBUG=(bool, False),
        ALLOWED_HOSTS=(list, []),
    )
except ImportError:
    # Fallback: create a simple env wrapper using os.environ
    class FallbackEnv:
        def __init__(self):
            pass

        def __call__(self, key, default=None, cast=None):
            value = os.environ.get(key, default)
            if cast and value is not None:
                if cast == bool:
                    return str(value).lower() in ('true', '1', 'yes')
                if cast == int:
                    return int(value)
                if cast == list:
                    return [x.strip() for x in str(value).split(',') if x.strip()]
            return value

        def bool(self, key, default=False):
            return self(key, default, bool)

        def int(self, key, default=0):
            return self(key, default, int)

        def list(self, key, default=None):
            return self(key, default or [], list)

        def db_url(self, default=None):
            """Parse DATABASE_URL into Django database config."""
            db_url = os.environ.get('DATABASE_URL', default)
            if not db_url:
                return None
            # Basic URL parsing for postgresql://user:pass@host:port/db
            if db_url.startswith('postgresql://') or db_url.startswith('postgres://'):
                from urllib.parse import urlparse
                parsed = urlparse(db_url)
                return {
                    'ENGINE': 'django.db.backends.postgresql',
                    'NAME': parsed.path[1:],
                    'USER': parsed.username or '',
                    'PASSWORD': parsed.password or '',
                    'HOST': parsed.hostname or 'localhost',
                    'PORT': str(parsed.port) if parsed.port else '5432',
                }
            return None

    env = FallbackEnv()


# =============================================================================
# PATHS
# =============================================================================

# Build paths inside the project like this: BASE_DIR / 'subdir'.
# BASE_DIR is the e_menum directory (where manage.py lives)
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Read .env file if it exists (development)
ENV_FILE = BASE_DIR.parent / '.env'
if ENV_FILE.exists():
    try:
        environ.Env.read_env(str(ENV_FILE))
    except (NameError, AttributeError):
        # Fallback env doesn't have read_env
        pass


# =============================================================================
# SECURITY SETTINGS
# =============================================================================

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get(
    'DJANGO_SECRET_KEY',
    'django-insecure-change-this-in-production-use-50-char-random-string'
)

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env.bool('DEBUG', default=False)

ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=[])

# CSRF Settings
CSRF_TRUSTED_ORIGINS = env.list('CSRF_TRUSTED_ORIGINS', default=[])

# Security headers (enabled in production)
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = 'DENY'
SECURE_CONTENT_TYPE_NOSNIFF = True


# =============================================================================
# APPLICATION DEFINITION
# =============================================================================

# Django built-in apps
DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

# Third-party apps
# Note: Uncomment as dependencies are installed via requirements.txt
THIRD_PARTY_APPS = [
    # 'rest_framework',
    # 'rest_framework_simplejwt',
    # 'rest_framework_simplejwt.token_blacklist',
    # 'django_filters',
    # 'corsheaders',
    # 'guardian',
]

# E-Menum Local apps (ordered by dependency)
# Note: Uncomment as apps are created
LOCAL_APPS = [
    'apps.core.apps.CoreConfig',
    # 'apps.menu.apps.MenuConfig',
    # 'apps.orders.apps.OrdersConfig',
    # 'apps.subscriptions.apps.SubscriptionsConfig',
    # 'apps.customers.apps.CustomersConfig',
    # 'apps.media.apps.MediaConfig',
    # 'apps.notifications.apps.NotificationsConfig',
    # 'apps.analytics.apps.AnalyticsConfig',
    # 'apps.ai.apps.AiConfig',
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS


# =============================================================================
# MIDDLEWARE CONFIGURATION
# =============================================================================

# CRITICAL: Middleware order matters!
# See spec.md for detailed ordering requirements
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    # 'whitenoise.middleware.WhiteNoiseMiddleware',  # Uncomment when whitenoise installed
    # 'corsheaders.middleware.CorsMiddleware',  # Uncomment when corsheaders installed
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',  # i18n support
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    # TenantMiddleware will be added after core app is created
    # 'shared.middleware.tenant.TenantMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]


# =============================================================================
# URL CONFIGURATION
# =============================================================================

ROOT_URLCONF = 'config.urls'

WSGI_APPLICATION = 'config.wsgi.application'
ASGI_APPLICATION = 'config.asgi.application'


# =============================================================================
# TEMPLATES
# =============================================================================

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            BASE_DIR / 'templates',
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.i18n',
                'django.template.context_processors.media',
                'django.template.context_processors.static',
            ],
        },
    },
]


# =============================================================================
# DATABASE
# =============================================================================

# Default to SQLite for initial setup, environment settings will override
# Production uses PostgreSQL via DATABASE_URL
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Try to use DATABASE_URL if available
DATABASE_URL = os.environ.get('DATABASE_URL')
if DATABASE_URL:
    try:
        # Use dj-database-url if available
        import dj_database_url
        DATABASES['default'] = dj_database_url.config(
            default=DATABASE_URL,
            conn_max_age=600,
            conn_health_checks=True,
        )
    except ImportError:
        # Fallback to manual parsing
        db_config = env.db_url() if hasattr(env, 'db_url') else None
        if db_config:
            DATABASES['default'] = db_config

# Default database options for PostgreSQL
DEFAULT_DATABASE_OPTIONS = {
    'connect_timeout': 10,
}


# =============================================================================
# AUTHENTICATION
# =============================================================================

# Custom User Model
AUTH_USER_MODEL = 'core.User'

# Authentication backends (including django-guardian for object-level permissions)
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    # 'guardian.backends.ObjectPermissionBackend',  # Uncomment when guardian installed
]

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 12,  # Enterprise requirement: min 12 chars
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Password hashing (bcrypt with 12 rounds for enterprise security)
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.BCryptSHA256PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher',
    'django.contrib.auth.hashers.Argon2PasswordHasher',
    'django.contrib.auth.hashers.ScryptPasswordHasher',
]


# =============================================================================
# DJANGO REST FRAMEWORK
# =============================================================================

REST_FRAMEWORK = {
    # Authentication
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',  # For browsable API
    ],

    # Permissions
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],

    # Filtering & Search
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],

    # Pagination
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,

    # Throttling (rate limiting)
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/hour',
        'user': '1000/hour',
    },

    # Parsers & Renderers
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
        'rest_framework.parsers.FormParser',
        'rest_framework.parsers.MultiPartParser',
    ],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    ],

    # Exception handling
    'EXCEPTION_HANDLER': 'shared.utils.exceptions.custom_exception_handler',

    # Versioning
    'DEFAULT_VERSIONING_CLASS': 'rest_framework.versioning.URLPathVersioning',
    'DEFAULT_VERSION': 'v1',
    'ALLOWED_VERSIONS': ['v1'],

    # Date/Time formats
    'DATETIME_FORMAT': '%Y-%m-%dT%H:%M:%S.%fZ',
    'DATE_FORMAT': '%Y-%m-%d',
    'TIME_FORMAT': '%H:%M:%S',

    # Schema
    'DEFAULT_SCHEMA_CLASS': 'rest_framework.schemas.openapi.AutoSchema',
}


# =============================================================================
# JWT CONFIGURATION (Simple JWT)
# =============================================================================

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(
        minutes=env.int('JWT_ACCESS_TOKEN_LIFETIME', default=15)
    ),
    'REFRESH_TOKEN_LIFETIME': timedelta(
        minutes=env.int('JWT_REFRESH_TOKEN_LIFETIME', default=10080)  # 7 days
    ),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,

    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'VERIFYING_KEY': None,
    'AUDIENCE': None,
    'ISSUER': 'e-menum',

    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',

    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',

    'JTI_CLAIM': 'jti',

    'SLIDING_TOKEN_REFRESH_EXP_CLAIM': 'refresh_exp',
    'SLIDING_TOKEN_LIFETIME': timedelta(minutes=15),
    'SLIDING_TOKEN_REFRESH_LIFETIME': timedelta(days=7),
}


# =============================================================================
# CORS CONFIGURATION
# =============================================================================

# CORS headers configuration
CORS_ALLOWED_ORIGINS = env.list('CORS_ALLOWED_ORIGINS', default=[])

CORS_ALLOW_CREDENTIALS = True

CORS_ALLOW_METHODS = [
    'DELETE',
    'GET',
    'OPTIONS',
    'PATCH',
    'POST',
    'PUT',
]

CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
    'x-organization-id',  # For multi-tenant requests
]


# =============================================================================
# CACHE CONFIGURATION
# =============================================================================

# Default cache (can be overridden with Redis in production)
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
    }
}

# Redis cache configuration (if REDIS_URL is set)
REDIS_URL = os.environ.get('REDIS_URL')
if REDIS_URL:
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.redis.RedisCache',
            'LOCATION': REDIS_URL,
            'OPTIONS': {
                'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            },
            'KEY_PREFIX': 'emenum',
        }
    }

# Cache timeouts (in seconds)
CACHE_TIMEOUT_SHORT = 60 * 5  # 5 minutes
CACHE_TIMEOUT_MEDIUM = 60 * 30  # 30 minutes
CACHE_TIMEOUT_LONG = 60 * 60 * 24  # 24 hours


# =============================================================================
# CELERY CONFIGURATION
# =============================================================================

# Celery broker URL (Redis)
CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/0')
CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')

# Celery configuration
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'Europe/Istanbul'
CELERY_ENABLE_UTC = True

# Task execution settings
CELERY_TASK_SOFT_TIME_LIMIT = 300  # 5 minutes
CELERY_TASK_TIME_LIMIT = 600  # 10 minutes
CELERY_TASK_ACKS_LATE = True
CELERY_TASK_REJECT_ON_WORKER_LOST = True

# Worker settings
CELERY_WORKER_PREFETCH_MULTIPLIER = 1
CELERY_WORKER_CONCURRENCY = env.int('CELERY_WORKER_CONCURRENCY', default=4)

# Result backend settings
CELERY_RESULT_EXPIRES = 60 * 60 * 24  # 24 hours

# Task retry settings
CELERY_TASK_DEFAULT_RETRY_DELAY = 60  # 1 minute
CELERY_TASK_MAX_RETRIES = 3

# Beat scheduler (for periodic tasks)
CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'


# =============================================================================
# INTERNATIONALIZATION (i18n)
# =============================================================================

LANGUAGE_CODE = 'tr'  # Turkish as default

TIME_ZONE = 'Europe/Istanbul'

USE_I18N = True
USE_L10N = True
USE_TZ = True

# Available languages
LANGUAGES = [
    ('tr', 'Turkce'),
    ('en', 'English'),
]

LOCALE_PATHS = [
    BASE_DIR / 'locale',
]


# =============================================================================
# STATIC FILES
# =============================================================================

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

# WhiteNoise for serving static files
# Note: Uncomment when whitenoise is installed
# STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'


# =============================================================================
# MEDIA FILES
# =============================================================================

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# File upload settings
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10 MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10 MB


# =============================================================================
# DEFAULT PRIMARY KEY
# =============================================================================

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# =============================================================================
# DJANGO GUARDIAN
# =============================================================================

# Guardian configuration for object-level permissions
ANONYMOUS_USER_NAME = None  # Disable anonymous user


# =============================================================================
# EMAIL CONFIGURATION
# =============================================================================

EMAIL_BACKEND = os.environ.get(
    'EMAIL_BACKEND',
    'django.core.mail.backends.console.EmailBackend'
)
EMAIL_HOST = os.environ.get('EMAIL_HOST', 'localhost')
EMAIL_PORT = env.int('EMAIL_PORT', default=587)
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')
EMAIL_USE_TLS = env.bool('EMAIL_USE_TLS', default=True)
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'noreply@e-menum.com')


# =============================================================================
# LOGGING
# =============================================================================

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
        'json': {
            'format': '{"level": "%(levelname)s", "time": "%(asctime)s", "module": "%(module)s", "message": "%(message)s"}',
        },
    },
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse',
        },
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
        'console_verbose': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': os.environ.get('DJANGO_LOG_LEVEL', 'INFO'),
            'propagate': False,
        },
        'django.request': {
            'handlers': ['console_verbose', 'mail_admins'],
            'level': 'ERROR',
            'propagate': False,
        },
        'django.security': {
            'handlers': ['console_verbose', 'mail_admins'],
            'level': 'ERROR',
            'propagate': False,
        },
        'django.db.backends': {
            'handlers': ['console'],
            'level': os.environ.get('DB_LOG_LEVEL', 'WARNING'),
            'propagate': False,
        },
        'apps': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'celery': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}


# =============================================================================
# E-MENUM APPLICATION SETTINGS
# =============================================================================

# Multi-tenancy settings
EMENUM_TENANT_HEADER = 'X-Organization-ID'
EMENUM_TENANT_COOKIE = 'emenum_org_id'

# API settings
EMENUM_API_VERSION = 'v1'
EMENUM_API_PREFIX = f'/api/{EMENUM_API_VERSION}'

# Pagination defaults
EMENUM_DEFAULT_PAGE_SIZE = 20
EMENUM_MAX_PAGE_SIZE = 100

# Plan limits (from spec)
EMENUM_PLAN_LIMITS = {
    'FREE': {
        'menus': 1,
        'products': 50,
        'qr_codes': 3,
        'users': 2,
        'storage_mb': 100,
        'ai_credits': 0,
    },
    'STARTER': {
        'menus': 3,
        'products': 200,
        'qr_codes': 10,
        'users': 5,
        'storage_mb': 500,
        'ai_credits': 100,
    },
    'PROFESSIONAL': {
        'menus': 10,
        'products': 500,
        'qr_codes': 50,
        'users': 15,
        'storage_mb': 2048,
        'ai_credits': 500,
    },
    'BUSINESS': {
        'menus': 25,
        'products': 1000,
        'qr_codes': 100,
        'users': 30,
        'storage_mb': 5120,
        'ai_credits': 1000,
    },
    'ENTERPRISE': {
        'menus': -1,  # Unlimited
        'products': -1,
        'qr_codes': -1,
        'users': -1,
        'storage_mb': 20480,
        'ai_credits': -1,
    },
}

# Session settings
SESSION_COOKIE_AGE = 60 * 60 * 24 * 7  # 1 week
SESSION_COOKIE_SECURE = not DEBUG
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'

# CSRF settings
CSRF_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = 'Lax'
