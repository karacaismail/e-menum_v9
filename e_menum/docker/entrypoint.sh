#!/bin/bash
set -e

echo "========================================"
echo "E-Menum Django Application Starting..."
echo "========================================"
echo "Settings: ${DJANGO_SETTINGS_MODULE}"
echo "Port: ${PORT:-8000}"
echo "========================================"

# ─── Create .env from .env.example if not exists ─────────────
# NOTE: In production Docker, env vars come from docker-compose.prod.yml,
# so a .env file inside the container is optional. If creation fails
# (e.g. permission issue), the app continues with env vars from compose.
if [ -f /app/.env ]; then
    echo ".env file already exists."
elif [ -f /app/.env.example ]; then
    echo "No .env file found. Creating from .env.example..."
    if cp /app/.env.example /app/.env 2>/dev/null; then
        echo ".env file created from .env.example."
    else
        echo "WARNING: Could not create .env (permission denied). Using environment variables from Docker."
    fi
else
    echo "No .env or .env.example found. Using environment variables from Docker."
fi

# ─── Wait for database ──────────────────────────────────────
# Ensure .env has DATABASE_URL when created from .env.example (Docker injects it; persist for Django)
if [ -n "$DATABASE_URL" ] && [ -f /app/.env ]; then
    if ! grep -q '^DATABASE_URL=' /app/.env 2>/dev/null; then
        echo "DATABASE_URL=$DATABASE_URL" >> /app/.env
    fi
fi
# Debug: show which DB host we use (no password)
if [ -n "$DATABASE_URL" ]; then
    _db_host=$(echo "$DATABASE_URL" | sed -n 's|.*@\([^/]*\)/.*|\1|p')
    echo "Database host: ${_db_host:-unknown}"
fi
# Wait for DB using psycopg only (no Django) to avoid loading INSTALLED_APPS (filer, etc.) and "populate() isn't reentrant"
if [ -n "$DATABASE_URL" ]; then
    echo "Checking database connection..."
    python << 'PYEOF'
import os
import sys
import time

url = os.environ.get("DATABASE_URL")
max_retries = 30
retry_interval = 2

for i in range(max_retries):
    try:
        import psycopg
        conn = psycopg.connect(url, connect_timeout=5)
        conn.close()
        print("Database is ready!")
        break
    except Exception as e:
        if i == max_retries - 1:
            print(f"Could not connect to database after {max_retries} attempts: {e}")
            sys.exit(1)
        print(f"Waiting for database... ({i+1}/{max_retries}) last error: {e}")
        time.sleep(retry_interval)
PYEOF
fi

# ─── Run migrations if requested ────────────────────────────
if [ "$DJANGO_MIGRATE" = "true" ]; then
    echo "Running database migrations..."

    # Use safe_migrate with audit logging and advisory locking.
    # Falls back to standard migrate if safe_migrate is not available
    # (e.g. first deploy before management command exists).
    if python manage.py safe_migrate --applied-by "docker-entrypoint" 2>&1; then
        echo "Migrations complete (safe_migrate)."
    else
        SAFE_EXIT=$?
        echo "WARNING: safe_migrate exited with code $SAFE_EXIT"
        echo "Falling back to standard migrate..."
        python manage.py migrate --noinput
        echo "Migrations complete (standard fallback)."
    fi
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
    # Ensure staticfiles directory is writable (volume mounts may be root-owned)
    if [ -d /app/staticfiles ] && [ ! -w /app/staticfiles ]; then
        echo "Fixing staticfiles directory permissions..."
        sudo chown -R emenum:emenum /app/staticfiles 2>/dev/null || true
    fi
    python manage.py collectstatic --noinput
    echo "Static files collected. $(ls /app/staticfiles/ 2>/dev/null | wc -l) items in staticfiles/"
fi

# ─── Seed data if requested (runs once, skips if data exists) ─
if [ "$DJANGO_SEED_DATA" = "true" ]; then
    echo "Checking if seed data is needed..."
    NEEDS_SEED=$(python manage.py shell -c "
from apps.core.models import Role
print('yes' if Role.objects.count() == 0 else 'no')
" 2>/dev/null || echo "yes")

    if [ "$NEEDS_SEED" = "yes" ]; then
        echo "════════════════════════════════════════"
        echo "  Seeding initial data..."
        echo "════════════════════════════════════════"

        echo "[1/5] Seeding demo data (roles, plans, restaurants, products, orders)..."
        python manage.py seed_demo_data 2>&1 || echo "WARNING: seed_demo_data had errors (continuing)"

        echo "[2/5] Seeding CMS content (website pages, blog, FAQ)..."
        python manage.py seed_cms_content 2>&1 || echo "WARNING: seed_cms_content had errors (continuing)"

        echo "[3/5] Seeding SEO data (robots.txt, sitemap)..."
        python manage.py seed_seo_data 2>&1 || echo "WARNING: seed_seo_data had errors (continuing)"

        echo "[4/5] Seeding report definitions (140 reports)..."
        python manage.py seed_report_definitions 2>&1 || echo "WARNING: seed_report_definitions had errors (continuing)"

        echo "[5/5] Seeding shield data (bot whitelist, security rules)..."
        python manage.py seed_shield_data 2>&1 || echo "WARNING: seed_shield_data had errors (continuing)"

        echo "════════════════════════════════════════"
        echo "  Seed data complete!"
        echo "════════════════════════════════════════"
    else
        echo "Seed data already exists (roles found). Skipping."
    fi
fi

echo "Starting application..."

# Execute the main command (gunicorn, celery, etc.)
exec "$@"
