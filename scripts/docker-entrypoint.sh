#!/bin/bash
set -eo pipefail

echo "=================================================="
echo "PWD301 LMS Production Container Initialization"
echo "=================================================="

# 1. Wait for SQL Server and ensure database exists
echo "[1/4] Checking database connectivity..."
python scripts/wait_for_db.py

# 2. Run database migrations to head
echo "[2/4] Applying database migrations (Flask-Migrate / Alembic)..."
flask db upgrade

# 3. Seed baseline system data (Roles, Root Admin)
echo "[3/4] Ensuring baseline roles and root admin exist..."
flask seed-baseline

# 4. Optional: Seed demo data if SEED_DEMO_DATA is enabled
if [ "${SEED_DEMO_DATA:-false}" = "true" ] || [ "${SEED_DEMO_DATA:-0}" = "1" ]; then
    echo "[4/4] SEED_DEMO_DATA is enabled. Seeding comprehensive demo dataset..."
    flask seed-demo
else
    echo "[4/4] SEED_DEMO_DATA is disabled. Skipping demo data seeding."
fi

echo "=================================================="
echo "PWD301 Initialization Complete. Starting application..."
echo "=================================================="

# Determine reload flag for development
RELOAD_FLAG=""
if [ "${APP_ENV}" = "development" ] || [ "${FLASK_DEBUG}" = "1" ] || [ "${FLASK_DEBUG}" = "true" ]; then
    echo "Development environment detected. Enabling Gunicorn auto-reload (--reload)..."
    RELOAD_FLAG="--reload"
fi

# Execute default Gunicorn server if no command or just 'gunicorn' is passed
if [ "$#" -eq 0 ] || { [ "$1" = "gunicorn" ] && [ "$#" -eq 1 ]; }; then
    echo "Starting Gunicorn WSGI Server on port ${PORT:-5000} (workers=${GUNICORN_WORKERS:-4}, threads=${GUNICORN_THREADS:-2}, timeout=${GUNICORN_TIMEOUT:-120}s)..."
    exec gunicorn \
        ${RELOAD_FLAG} \
        --bind "0.0.0.0:${PORT:-5000}" \
        --workers "${GUNICORN_WORKERS:-4}" \
        --threads "${GUNICORN_THREADS:-2}" \
        --timeout "${GUNICORN_TIMEOUT:-120}" \
        --access-logfile "-" \
        --error-logfile "-" \
        "wsgi:app"
fi

# Otherwise execute custom command (e.g., pytest, bash, flask)
exec "$@"
