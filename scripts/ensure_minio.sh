#!/usr/bin/env bash
#
# Provision object storage for THIS project against a single, SHARED local MinIO.
#
# Model:
#   * There is ONE local MinIO container on the host (name: "minio"), reused by every
#     project on this machine — no per-project MinIO, no duplication.
#   * This script starts that shared MinIO if it isn't running yet; if it already
#     exists it is reused and we only create this project's bucket + app user + policy.
#   * If the project is configured to use EXTERNAL storage (managed MinIO / real S3),
#     i.e. the MinIO root credentials are not the local defaults, local MinIO is not
#     needed and the script exits without doing anything.
#
# Usage: ./scripts/ensure_minio.sh        (or: make minio)
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"

# Load .env if present (gives us the MINIO_* / DJANGO_MINIO_* values).
if [ -f "$REPO_ROOT/.env" ]; then
    set -a
    # shellcheck disable=SC1091
    . "$REPO_ROOT/.env"
    set +a
fi

# --- Configuration (with local-dev defaults) ---------------------------------
CONTAINER_NAME="${MINIO_CONTAINER_NAME:-minio}"
IMAGE="${MINIO_IMAGE:-pgsty/minio:RELEASE.2026-04-17T00-00-00Z}"
MC_IMAGE="${MINIO_MC_IMAGE:-minio/mc:latest}"
VOLUME_NAME="${MINIO_VOLUME_NAME:-minio-data}"

MINIO_ROOT_USER="${MINIO_ROOT_USER:-minioadmin}"
MINIO_ROOT_PASSWORD="${MINIO_ROOT_PASSWORD:-minioadmin}"
MINIO_PORT="${MINIO_PORT:-9000}"
MINIO_CONSOLE_PORT="${MINIO_CONSOLE_PORT:-9001}"

# Per-project resources to create on the shared MinIO.
BUCKET="${MINIO_BUCKET_NAME:?MINIO_BUCKET_NAME is required}"
APP_USER="${MINIO_APP_USER:?MINIO_APP_USER is required}"
APP_PASSWORD="${MINIO_APP_PASSWORD:?MINIO_APP_PASSWORD is required}"
POLICY_NAME="${APP_USER}-policy"

# --- External storage? Then there's nothing to do locally --------------------
# The shared local MinIO is administered with the default minioadmin/minioadmin root
# credentials. Non-default root credentials mean the project points at an external /
# managed MinIO (or real S3) administered elsewhere — skip local provisioning.
if [ "$MINIO_ROOT_USER" != "minioadmin" ] || [ "$MINIO_ROOT_PASSWORD" != "minioadmin" ]; then
    echo "External object storage configured (non-default MinIO root credentials)."
    echo "Local MinIO is not needed — skipping. Provision the bucket on your provider instead."
    exit 0
fi

if ! command -v docker >/dev/null 2>&1; then
    echo "ERROR: docker is required but not found on PATH." >&2
    exit 1
fi

# --- 1. Ensure the single shared MinIO container is running ------------------
if docker inspect "$CONTAINER_NAME" >/dev/null 2>&1; then
    state="$(docker inspect -f '{{.State.Status}}' "$CONTAINER_NAME")"
    if [ "$state" = "running" ]; then
        echo "Shared MinIO container '$CONTAINER_NAME' is already running — reusing it."
    else
        echo "Shared MinIO container '$CONTAINER_NAME' exists ($state) — starting it..."
        docker start "$CONTAINER_NAME" >/dev/null
    fi
else
    echo "Creating shared MinIO container '$CONTAINER_NAME'..."
    docker volume create "$VOLUME_NAME" >/dev/null 2>&1 || true
    docker run -d \
        --name "$CONTAINER_NAME" \
        -p "${MINIO_PORT}:9000" \
        -p "${MINIO_CONSOLE_PORT}:9001" \
        -e "MINIO_ROOT_USER=${MINIO_ROOT_USER}" \
        -e "MINIO_ROOT_PASSWORD=${MINIO_ROOT_PASSWORD}" \
        -v "${VOLUME_NAME}:/data" \
        --restart unless-stopped \
        "$IMAGE" server /data --console-address ":9001" >/dev/null
    echo "Shared MinIO started:"
    echo "  API:     http://localhost:${MINIO_PORT}"
    echo "  Console: http://localhost:${MINIO_CONSOLE_PORT}"
fi

# --- 2. Create this project's bucket + app user + policy ---------------------
# Run mc in a one-off container. It reaches the host-published MinIO via
# host.docker.internal (works on Docker Desktop; the --add-host maps it on Linux).
#
# Policy JSON is rendered HERE on the host (the `bucket_name` placeholder is replaced
# with the real bucket name using pure bash, no external tools) and passed to the
# container as env vars — the official minio/mc image ships no sed/awk to substitute it.
echo "Provisioning bucket '$BUCKET' and app user '$APP_USER' on the shared MinIO..."

render_policy() { # print the policy file with `bucket_name` replaced; nothing if absent
    local file="$1" content
    [ -f "$file" ] || return 0
    content="$(cat "$file")"
    printf '%s' "${content//bucket_name/$BUCKET}"
}
PUBLIC_POLICY="$(render_policy "$REPO_ROOT/minio/policies/bucket-public-read.json")"
USER_POLICY="$(render_policy "$REPO_ROOT/minio/policies/user-app.json")"

docker run --rm \
    --add-host=host.docker.internal:host-gateway \
    -e "MINIO_HOST=http://host.docker.internal:${MINIO_PORT}" \
    -e "MINIO_ROOT_USER=${MINIO_ROOT_USER}" \
    -e "MINIO_ROOT_PASSWORD=${MINIO_ROOT_PASSWORD}" \
    -e "BUCKET=${BUCKET}" \
    -e "APP_USER=${APP_USER}" \
    -e "APP_PASSWORD=${APP_PASSWORD}" \
    -e "POLICY_NAME=${POLICY_NAME}" \
    -e "PUBLIC_POLICY=${PUBLIC_POLICY}" \
    -e "USER_POLICY=${USER_POLICY}" \
    --entrypoint sh \
    "$MC_IMAGE" -c '
set -e
echo "  Waiting for MinIO at $MINIO_HOST ..."
until mc alias set local "$MINIO_HOST" "$MINIO_ROOT_USER" "$MINIO_ROOT_PASSWORD" >/dev/null 2>&1; do
    sleep 1
done

echo "  Ensuring bucket $BUCKET ..."
mc mb --ignore-existing "local/$BUCKET"

if [ -n "$PUBLIC_POLICY" ]; then
    echo "  Applying public-read policy ..."
    printf "%s" "$PUBLIC_POLICY" > /tmp/public.json
    mc anonymous set-json /tmp/public.json "local/$BUCKET"
fi

echo "  Ensuring app user $APP_USER ..."
mc admin user add local "$APP_USER" "$APP_PASSWORD" 2>/dev/null || true

if [ -n "$USER_POLICY" ]; then
    echo "  Applying user policy $POLICY_NAME ..."
    printf "%s" "$USER_POLICY" > /tmp/user.json
    mc admin policy create local "$POLICY_NAME" /tmp/user.json 2>/dev/null || \
        mc admin policy update local "$POLICY_NAME" /tmp/user.json
    mc admin policy attach local "$POLICY_NAME" --user "$APP_USER" 2>/dev/null || true
fi
'

echo "Done. Bucket '$BUCKET' is ready on the shared local MinIO."
echo "  App user:    $APP_USER"
echo "  Endpoint:    http://localhost:${MINIO_PORT}  (containers: http://host.docker.internal:${MINIO_PORT})"
