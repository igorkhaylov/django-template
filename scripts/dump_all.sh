#!/bin/bash

DUMPS_BASE_DIR="dumps"
TIMESTAMP=$(date +"%Y-%m-%d_%H-%M-%S")
DUMP_DIR="$DUMPS_BASE_DIR/${TIMESTAMP}"
DB_CONTAINER="db"
BACKEND_CONTAINER="backend"

# Load environments from ../.env
set -a
source "$(dirname "$0")/../.env"
set +a

DB_DUMP_FILE="${DUMP_DIR}/backup.sql"
MEDIA_FILES_TAR="${DUMP_DIR}/media_backup.tar.gz"

DOCKER_DB_DUMP_FILE="/tmp/backup_${TIMESTAMP}.sql"
DOCKER_MEDIA_TAR_FILE="/tmp/media_files_${TIMESTAMP}.tar.gz"

echo "Создание директории дампа: ${DUMP_DIR}"
mkdir -p "$DUMP_DIR"

echo "Создание дампа базы данных внутри контейнера '${DB_CONTAINER}'..."
docker compose exec -T "$DB_CONTAINER" pg_dump \
    -U "$POSTGRES_USER" \
    --no-owner \
    --no-acl \
    -F c \
    -b \
    -f "$DOCKER_DB_DUMP_FILE" \
    "$POSTGRES_DB"

if [ $? -ne 0 ]; then
    echo "❌ Ошибка создания дампа БД!"
    exit 1
fi

echo "Копирование дампа БД на хост..."
docker compose cp "${DB_CONTAINER}:${DOCKER_DB_DUMP_FILE}" "$DB_DUMP_FILE" || {
    echo "❌ Ошибка копирования дампа БД!"
    exit 1
}

docker compose exec -T "$DB_CONTAINER" rm "$DOCKER_DB_DUMP_FILE"

echo "✅ Дамп БД успешно сохранён: $DB_DUMP_FILE"

# -------------- Дамп медиафайлов Django --------------

echo "Создание архива медиафайлов Django из '${BACKEND_CONTAINER}:/app/media'..."
docker compose exec -T "$BACKEND_CONTAINER" tar -czf "$DOCKER_MEDIA_TAR_FILE" -C /app media

if [ $? -ne 0 ]; then
    echo "❌ Ошибка архивации медиафайлов!"
    exit 1
fi

echo "Копирование архива медиафайлов на хост..."
docker compose cp "${BACKEND_CONTAINER}:${DOCKER_MEDIA_TAR_FILE}" "$MEDIA_FILES_TAR" || {
    echo "❌ Ошибка копирования архива медиафайлов!"
    exit 1
}

docker compose exec -T "$BACKEND_CONTAINER" rm "$DOCKER_MEDIA_TAR_FILE"

echo "✅ Архив медиафайлов Django сохранён: $MEDIA_FILES_TAR"

echo "🎉 Резервное копирование завершено успешно!"
