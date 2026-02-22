"""
E-Menum Django Settings Package

This package contains environment-specific Django settings modules:
- base.py: Common settings for all environments
- development.py: Development environment settings
- staging.py: Staging environment settings
- production.py: Production environment settings

The settings module to use is determined by the DJANGO_SETTINGS_MODULE
environment variable, which should be set to one of:
- config.settings.development
- config.settings.staging
- config.settings.production

For local development, use:
    export DJANGO_SETTINGS_MODULE=config.settings.development

For production, use:
    export DJANGO_SETTINGS_MODULE=config.settings.production

Note: This file intentionally does not import settings to avoid side effects.
Settings are imported via manage.py or WSGI/ASGI entry points.
"""

# Version of the settings package
__version__ = '1.0.0'

# Default settings module hint (used by IDE tools)
# Actual settings loading is done by Django based on DJANGO_SETTINGS_MODULE
default_app_config = 'config.settings.development'
