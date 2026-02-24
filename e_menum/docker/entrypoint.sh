#!/bin/bash
set -e

echo "========================================"
echo "E-Menum Django Application Starting..."
echo "========================================"
echo "Settings: ${DJANGO_SETTINGS_MODULE}"
echo "Port: ${PORT:-8000}"
echo "========================================"

# ─── Wait for database ──────────────────────────────────────
if [ -n "$DATABASE_URL" ]; then
    echo "Checking database connection..."
    python << 'PYEOF'
import sys
import time

max_retries = 30
retry_interval = 2

for i in range(max_retries):
    try:
        import django
        import os
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')
        django.setup()
        from django.db import connection
        connection.ensure_connection()
        print("Database is ready!")
        break
    except Exception as e:
        if i == max_retries - 1:
            print(f"Could not connect to database after {max_retries} attempts: {e}")
            sys.exit(1)
        print(f"Waiting for database... ({i+1}/{max_retries})")
        time.sleep(retry_interval)
PYEOF
fi

# ─── Run migrations if requested ────────────────────────────
if [ "$DJANGO_MIGRATE" = "true" ]; then
    echo "Running database migrations..."
    python manage.py migrate --noinput
    echo "Migrations complete."
fi

# ─── Create superuser if requested ──────────────────────────
if [ "$DJANGO_CREATE_SUPERUSER" = "true" ] && [ -n "$DJANGO_SUPERUSER_EMAIL" ]; then
    echo "Creating superuser if not exists..."
    python manage.py shell -c "
from apps.core.models import User
if not User.objects.filter(email='${DJANGO_SUPERUSER_EMAIL}').exists():
    User.objects.create_superuser(
        email='${DJANGO_SUPERUSER_EMAIL}',
        password='${DJANGO_SUPERUSER_PASSWORD:-admin123}',
        first_name='Admin',
        last_name='User',
    )
    print('Superuser created.')
else:
    print('Superuser already exists.')
" 2>/dev/null || echo "Superuser creation skipped."
fi

# ─── Collect static files if requested ──────────────────────
if [ "$DJANGO_COLLECTSTATIC" = "true" ]; then
    echo "Collecting static files..."
    python manage.py collectstatic --noinput
fi

echo "Starting application..."

# Execute the main command (gunicorn, celery, etc.)
exec "$@"
