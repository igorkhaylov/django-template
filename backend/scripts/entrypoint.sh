#!/bin/bash
set -e

echo ">>> Compiling translation .mo files..."
python manage.py compilemessages

echo ">>> Applying database migrations..."
python manage.py migrate --no-input

echo ">>> Waiting for object storage (S3/MinIO) to be ready..."
# Static AND media are served from S3/MinIO with no local-filesystem fallback, so the
# bucket is a hard dependency. Fail fast with a clear message if it is missing/unreachable
# instead of letting collectstatic crash mid-boot with a cryptic boto error.
# (For the shared local MinIO, provision the bucket once with `make minio`.)
python manage.py wait_for_storage

echo ">>> Collecting static files..."
# No --clear: never wipes the bucket on boot.
python manage.py collectstatic --no-input

echo ">>> Ensuring superuser..."
python manage.py createsuperuserauto

echo ">>> Starting Gunicorn..."
exec gunicorn config.wsgi:application \
    --name "${DJANGO_APP_NAME}" \
    --workers "${GUNICORN_WORKERS:-4}" \
    --timeout "${GUNICORN_TIMEOUT:-60}" \
    --graceful-timeout "${GUNICORN_GRACEFUL_TIMEOUT:-30}" \
    --worker-tmp-dir /dev/shm \
    --bind 0.0.0.0:8000 \
    --access-logfile - \
    --error-logfile -
