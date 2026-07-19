#!/bin/bash
set -e

echo "Running migrations..."
python manage.py migrate --noinput

echo "Creating default users..."
python manage.py crear_usuarios || true

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Starting Gunicorn..."
exec gunicorn config.wsgi --bind 0.0.0.0:${PORT:-8000}
