#!/bin/sh

# This script is run by the supervisor container on startup.

# Apply database migrations
echo "Applying database migrations..."
python manage.py migrate

# Start Gunicorn server
echo "Starting Gunicorn server..."
gunicorn aura.wsgi:application --bind 0.0.0.0:8000

