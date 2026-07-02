#!/usr/bin/env bash
#
# Create a timestamped backup under ./dumps/<ts>/:
#   database.sql.gz  — full pg_dump (gzipped, --clean --if-exists)
#   manifest.json    — media base URL + object counts (used to rewrite URLs on restore)
#   media.tar.gz     — all S3/MinIO media objects (only with the "media" argument)
#
# Media lives in S3/MinIO (not on the container filesystem), so it is dumped THROUGH
# the app with `manage.py media_dump`, not by tarring a local directory.
#
# Usage:
#   make dump                 # database + manifest
#   make dump media           # + media dump from S3/MinIO (slower; downloads the bucket)
#   make dev dump media       # same, dev stack
#   ./scripts/dump_all.sh [media]
#
set -euo pipefail
cd "$(dirname "$0")/.."

COMPOSE="${COMPOSE:-docker compose}"
EXEC="${EXEC:-}"   # extra `docker compose exec` flags (e.g. --workdir /app/backend for the dev stack)

WITH_MEDIA=0
for arg in "$@"; do
  case "$arg" in
    media | --media) WITH_MEDIA=1 ;;
  esac
done

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

TS="$(date +%Y-%m-%d_%H-%M-%S)"
DIR="dumps/${TS}"
mkdir -p "$DIR"
echo "→ Backing up to ${DIR}"

echo "  • database…"
$COMPOSE exec -T db pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" \
  --clean --if-exists --no-owner --no-privileges \
  | gzip >"$DIR/database.sql.gz"

echo "  • manifest…"
$COMPOSE exec -T $EXEC backend python manage.py media_info >"$DIR/manifest.json"

if [ "$WITH_MEDIA" -eq 1 ]; then
  echo "  • media from S3/MinIO (this can take a while)…"
  $COMPOSE exec -T $EXEC backend python manage.py media_dump >"$DIR/media.tar.gz"
fi

echo "✓ Backup complete:"
du -sh "$DIR"/* 2>/dev/null || true
