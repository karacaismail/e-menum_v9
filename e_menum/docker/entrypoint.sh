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

echo "Starting application..."

# ─── Web container: start gunicorn in background, run seeds after listen, then hold ─
if [ "$DJANGO_SEED_DATA" = "true" ] && [ "${1:-}" = "gunicorn" ]; then
    PORT="${PORT:-8000}"
    echo "Gunicorn will start first; seeds will run after server is listening on port $PORT."
    # Start main command (gunicorn) in background
    "$@" &
    GUNICORN_PID=$!
    trap "kill -TERM $GUNICORN_PID 2>/dev/null; exit 0" SIGTERM SIGINT

    # Wait until server is listening (max 60s)
    echo "Waiting for server to listen on port $PORT..."
    for i in $(seq 1 30); do
        if curl -sf "http://127.0.0.1:${PORT}/health/" >/dev/null 2>&1; then
            echo "Server is listening. Running seed data if needed..."
            NEEDS_SEED=$(python manage.py shell -c "
from apps.core.models import Role
print('yes' if Role.objects.count() == 0 else 'no')
" 2>/dev/null || echo "yes")
            if [ "$NEEDS_SEED" = "yes" ]; then
                echo "[1/11] seed_roles..."
                python manage.py seed_roles 2>&1 || true
                echo "[2/11] seed_plans..."
                python manage.py seed_plans 2>&1 || true
                echo "[3/11] seed_allergens..."
                python manage.py seed_allergens 2>&1 || true
                echo "[4/11] seed_menu_data..."
                python manage.py seed_menu_data 2>&1 || true
                echo "[5/11] seed_extra_orgs..."
                python manage.py seed_extra_orgs 2>&1 || true
                echo "[6/11] seed_all_data..."
                python manage.py seed_all_data 2>&1 || true
                echo "[7/11] seed_demo_data..."
                python manage.py seed_demo_data 2>&1 || true
                echo "[8/11] seed_cms_content..."
                python manage.py seed_cms_content 2>&1 || true
                echo "[9/11] seed_seo_data..."
                python manage.py seed_seo_data 2>&1 || true
                echo "[10/11] seed_report_definitions..."
                python manage.py seed_report_definitions 2>&1 || true
                echo "[11/11] seed_shield_data..."
                python manage.py seed_shield_data 2>&1 || true
                echo "Seed data complete."
            else
                echo "Seed data already exists (roles found). Skipping."
            fi
            break
        fi
        [ $i -eq 30 ] && echo "WARNING: Server did not become ready in time; skipping seed."
        sleep 2
    done

    wait $GUNICORN_PID
    exit $?
fi

# Execute the main command (gunicorn, celery, etc.) – default path
exec "$@"
