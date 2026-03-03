#!/usr/bin/env bash
set -euo pipefail

CONTAINER_NAME="minio"
IMAGE="minio/minio:RELEASE.2025-09-07T16-13-09Z-cpuv1"
VOLUME_NAME="minio-data"

MINIO_ROOT_USER="${MINIO_ROOT_USER:-minioadmin}"
MINIO_ROOT_PASSWORD="${MINIO_ROOT_PASSWORD:-minioadmin}"
MINIO_PORT="${MINIO_PORT:-9000}"
MINIO_CONSOLE_PORT="${MINIO_CONSOLE_PORT:-9001}"

if docker inspect "$CONTAINER_NAME" &>/dev/null; then
    STATE=$(docker inspect -f '{{.State.Status}}' "$CONTAINER_NAME")
    if [ "$STATE" = "running" ]; then
        echo "MinIO container '$CONTAINER_NAME' is already running."
        exit 0
    else
        echo "MinIO container '$CONTAINER_NAME' exists but is $STATE. Starting..."
        docker start "$CONTAINER_NAME"
        echo "MinIO container started."
        exit 0
    fi
fi

echo "Creating MinIO container '$CONTAINER_NAME'..."
docker volume create "$VOLUME_NAME" &>/dev/null || true

docker run -d \
    --name "$CONTAINER_NAME" \
    -p "${MINIO_PORT}:9000" \
    -p "${MINIO_CONSOLE_PORT}:9001" \
    -e "MINIO_ROOT_USER=${MINIO_ROOT_USER}" \
    -e "MINIO_ROOT_PASSWORD=${MINIO_ROOT_PASSWORD}" \
    -v "${VOLUME_NAME}:/data" \
    --restart unless-stopped \
    "$IMAGE" server /data --console-address ":9001"

echo "MinIO container created and started."
echo "  API:     http://localhost:${MINIO_PORT}"
echo "  Console: http://localhost:${MINIO_CONSOLE_PORT}"
