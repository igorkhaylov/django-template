#!/bin/bash

set -e

if [ -z "$1" ]; then
  echo "Usage: ./scripts/restore_all.sh /path/to/dumps/..."
  exit 1
fi

RESTORE_DIR="$1"
DB_CONTAINER="db"
BACKEND_CONTAINER="backend"
SQL_DUMP_FILE="${RESTORE_DIR}/backup.sql"
MEDIA_ARCHIVE="${RESTORE_DIR}/media_backup.tar.gz"
TMP_DUMP_PATH="/tmp/restore_dump.sql"
TMP_TAR_PATH="/tmp/restore_files.tar.gz"

# Load environment variables
set -a
source "$(dirname "$0")/../.env"
set +a

echo "Restoring from: $RESTORE_DIR"

if [ ! -f "$SQL_DUMP_FILE" ]; then
  echo "Error: database dump not found: $SQL_DUMP_FILE"
  exit 1
fi

if [ ! -f "$MEDIA_ARCHIVE" ]; then
  echo "Error: media archive not found: $MEDIA_ARCHIVE"
  exit 1
fi

# --- Restore Django media files ---
echo "Restoring Django media files..."
docker compose cp "$MEDIA_ARCHIVE" "${BACKEND_CONTAINER}:${TMP_TAR_PATH}"

docker compose exec -T "$BACKEND_CONTAINER" bash -c "
  echo 'Cleaning old /app/media contents...'
  rm -rf /app/media/*

  echo 'Extracting media archive...'
  tar --no-same-owner -xzf $TMP_TAR_PATH -C /app

  rm -f $TMP_TAR_PATH || echo 'Warning: could not remove temp archive (non-critical)'
"

echo "Django media files restored"

# --- Stop services before database restore ---
echo "Stopping services before database restore..."
docker compose stop

# --- Restore database ---
docker compose up $DB_CONTAINER -d
echo "Restoring database '$POSTGRES_DB'..."

docker compose cp "$SQL_DUMP_FILE" "${DB_CONTAINER}:${TMP_DUMP_PATH}"

docker compose exec -T "$DB_CONTAINER" bash -c "
  echo 'Terminating active connections and dropping database...'
  psql -U $POSTGRES_USER -d postgres -c \"
    SELECT pg_terminate_backend(pid)
    FROM pg_stat_activity
    WHERE datname = '$POSTGRES_DB' AND pid <> pg_backend_pid();
  \"

  psql -U $POSTGRES_USER -d postgres -c 'DROP DATABASE IF EXISTS \"$POSTGRES_DB\";'
  psql -U $POSTGRES_USER -d postgres -c 'CREATE DATABASE \"$POSTGRES_DB\" OWNER \"$POSTGRES_USER\";'

  echo 'Restoring from dump...'
  pg_restore -U $POSTGRES_USER -d \"$POSTGRES_DB\" \"$TMP_DUMP_PATH\"

  rm -f \"$TMP_DUMP_PATH\"
"

echo "Database restored"

# --- Restart services ---
echo "Restarting services..."
docker compose start

echo "Restore completed successfully!"
