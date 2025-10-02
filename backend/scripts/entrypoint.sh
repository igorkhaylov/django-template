#!/bin/bash

echo ">>> Generate messages .mo files..."
python manage.py compilemessages

echo ">>> Apply database migrations..."
python manage.py migrate --no-input

echo ">>> Collecting static files..."
python manage.py collectstatic --no-input --clear

echo ">>> Create Superuser..."
python manage.py createsuperuserauto

echo ">>> Starting server..."
gunicorn config.wsgi:application --name ${DJANGO_APP_NAME} --workers ${GUNICORN_WORKERS:-4} --bind 0.0.0.0:8000
