# syntax=docker/dockerfile:1
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
    PATH="/opt/venv/bin:$PATH" \
    DJANGO_SETTINGS_MODULE=config.settings.production \
    APP_HOME=/app \
    GUNICORN_WORKERS=3 \
    GUNICORN_THREADS=2 \
    GUNICORN_TIMEOUT=120 \
    GUNICORN_GRACEFUL_TIMEOUT=30 \
    GUNICORN_KEEPALIVE=5 \
    PORT=8000

# Install runtime dependencies only (libpq5, curl, tini)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    tini \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create non-root user for security
# Using fixed UID/GID for consistency across deployments
RUN groupadd --gid 1000 emenum \
    && useradd --uid 1000 --gid emenum --shell /bin/bash --create-home emenum

# Set work directory
WORKDIR /app

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
    REDIS_URL='redis://localhost:6379/0' \
    python manage.py collectstatic --noinput --clear 2>/dev/null || true

# Copy entrypoint script (external file avoids heredoc parse issues)
COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Switch to non-root user
USER emenum

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl --fail http://localhost:8000/health/ || exit 1

# Use tini as init system for proper signal handling
ENTRYPOINT ["/usr/bin/tini", "--", "/entrypoint.sh"]

# Default command: run gunicorn
CMD ["gunicorn", "config.wsgi:application", \
     "--bind", "0.0.0.0:8000", \
     "--workers", "3", \
     "--threads", "2", \
     "--timeout", "120", \
     "--graceful-timeout", "30", \
     "--keep-alive", "5", \
     "--worker-class", "gthread", \
     "--worker-tmp-dir", "/dev/shm", \
     "--access-logfile", "-", \
     "--error-logfile", "-", \
     "--capture-output", \
     "--enable-stdio-inheritance", \
     "--log-level", "info", \
     "--forwarded-allow-ips", "*"]


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
RUN pip install -r requirements-dev.txt 2>/dev/null || true

# Create .bashrc with useful aliases (echo avoids heredoc parse issues)
RUN echo 'alias ll="ls -la"' >> /home/emenum/.bashrc \
    && echo 'alias manage="python manage.py"' >> /home/emenum/.bashrc \
    && echo 'alias migrate="python manage.py migrate"' >> /home/emenum/.bashrc \
    && echo 'alias makemigrations="python manage.py makemigrations"' >> /home/emenum/.bashrc \
    && echo 'alias shell="python manage.py shell_plus"' >> /home/emenum/.bashrc \
    && echo 'alias test="pytest"' >> /home/emenum/.bashrc

# Switch back to non-root user
USER emenum

# Override command for development (use runserver)
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]


# -----------------------------------------------------------------------------
# Stage 4: Celery Worker - For running background tasks
# -----------------------------------------------------------------------------
FROM production AS celery-worker

# Override command for Celery worker
CMD ["celery", "-A", "config", "worker", \
     "--loglevel=info", \
     "--concurrency=2", \
     "--max-tasks-per-child=50", \
     "--pool=prefork"]


# -----------------------------------------------------------------------------
# Stage 5: Celery Beat - For running periodic tasks
# -----------------------------------------------------------------------------
FROM production AS celery-beat

# Override command for Celery beat
CMD ["celery", "-A", "config", "beat", \
     "--loglevel=info", \
     "--scheduler", "django_celery_beat.schedulers:DatabaseScheduler"]
