#!/usr/bin/env bash
#
# Restore a backup created by dump_all.sh.
#   1. Restore the database from database.sql.gz (drops & recreates objects in place
#      via the dump's `--clean --if-exists` statements; no full DROP DATABASE).
#   2. Upload media.tar.gz to the CURRENT S3/MinIO (only if present in the backup).
#   3. Rewrite absolute media URLs embedded in HTML/text from the backup's
#      media_base_url to the current one — so a restore into a DIFFERENT S3
#      (different domain/bucket) keeps every in-content image/file working.
#
# Usage:
#   make restore dumps/<ts>
#   make dev restore dumps/<ts>
#   ./scripts/restore_all.sh dumps/<ts>
#
set -euo pipefail
cd "$(dirname "$0")/.."

COMPOSE="${COMPOSE:-docker compose}"
EXEC="${EXEC:-}"   # extra `docker compose exec` flags (e.g. --workdir /app/backend for the dev stack)
DIR="${1:-}"

if [ -z "$DIR" ] || [ ! -d "$DIR" ]; then
  echo "Usage: ./scripts/restore_all.sh <backup-directory>   (e.g. dumps/2026-06-16_12-00-00)" >&2
  exit 1
fi

ENV_FILE="./.env"
if [ ! -f "$ENV_FILE" ]; then
  echo "Error: $ENV_FILE not found (needed for Postgres credentials)." >&2
  exit 1
fi
set -a
. "$ENV_FILE"
set +a
: "${POSTGRES_USER:?POSTGRES_USER is not set in .env}"
: "${POSTGRES_DB:?POSTGRES_DB is not set in .env}"

echo "→ Restoring from ${DIR}"

if [ -f "$DIR/database.sql.gz" ]; then
  echo "  • database…"
  gunzip -c "$DIR/database.sql.gz" \
    | $COMPOSE exec -T db psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -q -v ON_ERROR_STOP=1
fi

if [ -f "$DIR/media.tar.gz" ]; then
  echo "  • media → S3/MinIO…"
  $COMPOSE exec -T $EXEC backend python manage.py media_load <"$DIR/media.tar.gz"
fi

if [ -f "$DIR/manifest.json" ]; then
  OLD_BASE="$(python3 -c "import json; print(json.load(open('$DIR/manifest.json'))['media_base_url'])")"
  echo "  • rewriting embedded media URLs from ${OLD_BASE} → current S3/MinIO…"
  $COMPOSE exec -T $EXEC backend python manage.py rewrite_media_urls --from "$OLD_BASE"
fi

echo "✓ Restore complete."
