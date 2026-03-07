# E-Menum Django Configuration Package
# This package contains all Django configuration files including
# settings, URL configurations, WSGI, ASGI, and Celery configurations.

# This will make sure the Celery app is always imported when Django starts
# so that shared_task will use this app.
from .celery import app as celery_app

__all__ = ("celery_app",)

default_app_config = None
