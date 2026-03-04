#!/bin/bash

DUMPS_BASE_DIR="dumps"
TIMESTAMP=$(date +"%Y-%m-%d_%H-%M-%S")
DUMP_DIR="$DUMPS_BASE_DIR/${TIMESTAMP}"
DB_CONTAINER="db"
BACKEND_CONTAINER="backend"

# Load environment variables
set -a
source "$(dirname "$0")/../.env"
set +a

DB_DUMP_FILE="${DUMP_DIR}/backup.sql"
MEDIA_FILES_TAR="${DUMP_DIR}/media_backup.tar.gz"

DOCKER_DB_DUMP_FILE="/tmp/backup_${TIMESTAMP}.sql"
DOCKER_MEDIA_TAR_FILE="/tmp/media_files_${TIMESTAMP}.tar.gz"

echo "Creating dump directory: ${DUMP_DIR}"
mkdir -p "$DUMP_DIR"

echo "Creating database dump inside '${DB_CONTAINER}' container..."
docker compose exec -T "$DB_CONTAINER" pg_dump \
    -U "$POSTGRES_USER" \
    --no-owner \
    --no-acl \
    -F c \
    -b \
    -f "$DOCKER_DB_DUMP_FILE" \
    "$POSTGRES_DB"

if [ $? -ne 0 ]; then
    echo "Error: database dump failed!"
    exit 1
fi

echo "Copying database dump to host..."
docker compose cp "${DB_CONTAINER}:${DOCKER_DB_DUMP_FILE}" "$DB_DUMP_FILE" || {
    echo "Error: failed to copy database dump!"
    exit 1
}

docker compose exec -T "$DB_CONTAINER" rm "$DOCKER_DB_DUMP_FILE"

echo "Database dump saved: $DB_DUMP_FILE"

# -------------- Django media files dump --------------

echo "Archiving Django media files from '${BACKEND_CONTAINER}:/app/media'..."
docker compose exec -T "$BACKEND_CONTAINER" tar -czf "$DOCKER_MEDIA_TAR_FILE" -C /app media

if [ $? -ne 0 ]; then
    echo "Error: media files archiving failed!"
    exit 1
fi

echo "Copying media archive to host..."
docker compose cp "${BACKEND_CONTAINER}:${DOCKER_MEDIA_TAR_FILE}" "$MEDIA_FILES_TAR" || {
    echo "Error: failed to copy media archive!"
    exit 1
}

docker compose exec -T "$BACKEND_CONTAINER" rm "$DOCKER_MEDIA_TAR_FILE"

echo "Django media archive saved: $MEDIA_FILES_TAR"

echo "Backup completed successfully!"
