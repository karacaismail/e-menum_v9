# =============================================================================
# E-Menum Django - Production Dockerfile
# Multi-stage build for optimized production deployment
# =============================================================================

# -----------------------------------------------------------------------------
# Stage 1: Builder - Install dependencies and compile Python packages
# -----------------------------------------------------------------------------
FROM python:3.11-slim-bookworm AS builder

# Set environment variables for build
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Upgrade pip and install wheel
RUN pip install --upgrade pip wheel setuptools

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt


# -----------------------------------------------------------------------------
# Stage 2: Production - Minimal runtime image
# -----------------------------------------------------------------------------
FROM python:3.11-slim-bookworm AS production

# Labels for container metadata
LABEL maintainer="E-Menum Team" \
      version="1.0" \
      description="E-Menum Django Application - Production Image"

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1 \
    # Virtual environment path
    PATH="/opt/venv/bin:$PATH" \
    # Django settings
    DJANGO_SETTINGS_MODULE=config.settings.production \
    # Application paths
    APP_HOME=/app \
    # Gunicorn settings
    GUNICORN_WORKERS=3 \
    GUNICORN_THREADS=2 \
    GUNICORN_TIMEOUT=120 \
    GUNICORN_GRACEFUL_TIMEOUT=30 \
    GUNICORN_KEEPALIVE=5 \
    # Port
    PORT=8000

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    # PostgreSQL client library (required by psycopg)
    libpq5 \
    # For curl health checks
    curl \
    # For proper signal handling
    tini \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create non-root user for security
# Using fixed UID/GID for consistency across deployments
RUN groupadd --gid 1000 emenum \
    && useradd --uid 1000 --gid emenum --shell /bin/bash --create-home emenum

# Set work directory
WORKDIR ${APP_HOME}

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv

# Copy application code
COPY --chown=emenum:emenum . .

# Create directories for static and media files
RUN mkdir -p staticfiles media logs \
    && chown -R emenum:emenum staticfiles media logs

# Collect static files
# Using a temporary secret key for collectstatic (not used at runtime)
RUN DJANGO_SECRET_KEY='build-time-secret-for-collectstatic' \
    DATABASE_URL='postgresql://localhost/dummy' \
    python manage.py collectstatic --noinput --clear

# Create entrypoint script
RUN cat > /entrypoint.sh << 'EOF'
#!/bin/bash
set -e

echo "E-Menum Django Application Starting..."

# Wait for database to be ready (optional, can be handled by k8s/docker-compose)
if [ -n "$DATABASE_URL" ]; then
    echo "Checking database connection..."
    python -c "
import os
import sys
import time
import dj_database_url
from django.db import connection

config = dj_database_url.config()
max_retries = 30
retry_interval = 2

for i in range(max_retries):
    try:
        connection.ensure_connection()
        print('Database is ready!')
        break
    except Exception as e:
        if i == max_retries - 1:
            print(f'Could not connect to database after {max_retries} attempts')
            sys.exit(1)
        print(f'Waiting for database... ({i+1}/{max_retries})')
        time.sleep(retry_interval)
"
fi

# Run database migrations if DJANGO_MIGRATE is set
if [ "$DJANGO_MIGRATE" = "true" ]; then
    echo "Running database migrations..."
    python manage.py migrate --noinput
fi

# Execute the main command
exec "$@"
EOF

RUN chmod +x /entrypoint.sh

# Switch to non-root user
USER emenum

# Expose port
EXPOSE ${PORT}

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl --fail http://localhost:${PORT}/health/ || exit 1

# Use tini as init system for proper signal handling
ENTRYPOINT ["/usr/bin/tini", "--", "/entrypoint.sh"]

# Default command: run gunicorn
CMD gunicorn config.wsgi:application \
    --bind 0.0.0.0:${PORT} \
    --workers ${GUNICORN_WORKERS} \
    --threads ${GUNICORN_THREADS} \
    --timeout ${GUNICORN_TIMEOUT} \
    --graceful-timeout ${GUNICORN_GRACEFUL_TIMEOUT} \
    --keep-alive ${GUNICORN_KEEPALIVE} \
    --worker-class gthread \
    --worker-tmp-dir /dev/shm \
    --access-logfile - \
    --error-logfile - \
    --capture-output \
    --enable-stdio-inheritance \
    --log-level info \
    --forwarded-allow-ips '*'


# -----------------------------------------------------------------------------
# Stage 3: Development - Extended image for local development
# -----------------------------------------------------------------------------
FROM production AS development

# Switch to root for installing dev dependencies
USER root

# Set development environment
ENV DJANGO_SETTINGS_MODULE=config.settings.development \
    DEBUG=true

# Install development dependencies
COPY requirements-dev.txt .
RUN pip install -r requirements-dev.txt

# Create .bashrc with useful aliases
RUN cat >> /home/emenum/.bashrc << 'EOF'
alias ll='ls -la'
alias manage='python manage.py'
alias migrate='python manage.py migrate'
alias makemigrations='python manage.py makemigrations'
alias shell='python manage.py shell_plus'
alias test='pytest'
EOF

# Switch back to non-root user
USER emenum

# Override command for development (use runserver)
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]


# -----------------------------------------------------------------------------
# Stage 4: Celery Worker - For running background tasks
# -----------------------------------------------------------------------------
FROM production AS celery-worker

# Override command for Celery worker
CMD celery -A config worker \
    --loglevel=info \
    --concurrency=2 \
    --max-tasks-per-child=50 \
    --pool=prefork


# -----------------------------------------------------------------------------
# Stage 5: Celery Beat - For running periodic tasks
# -----------------------------------------------------------------------------
FROM production AS celery-beat

# Override command for Celery beat
CMD celery -A config beat \
    --loglevel=info \
    --scheduler django_celery_beat.schedulers:DatabaseScheduler
