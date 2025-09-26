#!/bin/bash

set -e

# Проверка аргументов
if [ -z "$1" ]; then
  echo "❌ Укажите путь к директории с дампами: ./scripts/restore_django.sh /path/to/dumps/..."
  exit 1
fi

RESTORE_DIR="$1"
DB_CONTAINER="db"
BACKEND_CONTAINER="backend"
SQL_DUMP_FILE="${RESTORE_DIR}/backup.sql"
MEDIA_ARCHIVE="${RESTORE_DIR}/media_backup.tar.gz"
TMP_DUMP_PATH="/tmp/restore_dump.sql"
TMP_TAR_PATH="/tmp/restore_files.tar.gz"

# Загрузка переменных окружения
set -a
source "$(dirname "$0")/../.env"
set +a

echo "📂 Используем дампы из: $RESTORE_DIR"

# Проверка наличия файлов
if [ ! -f "$SQL_DUMP_FILE" ]; then
  echo "❌ Не найден файл дампа базы: $SQL_DUMP_FILE"
  exit 1
fi

if [ ! -f "$MEDIA_ARCHIVE" ]; then
  echo "❌ Не найден архив медиафайлов: $MEDIA_ARCHIVE"
  exit 1
fi

# --- Восстановление медиафайлов Django ---
echo "📦 Восстановление медиафайлов Django..."
docker compose cp "$MEDIA_ARCHIVE" "${BACKEND_CONTAINER}:${TMP_TAR_PATH}"

docker compose exec -T "$BACKEND_CONTAINER" bash -c "
  echo '🧹 Очистка старого содержимого /app/media...'
  rm -rf /app/media/*

  echo '📦 Распаковка архивированных медиафайлов...'
  tar --no-same-owner -xzf $TMP_TAR_PATH -C /app

  echo '🧽 Попытка удалить временный архив...'
  rm -f $TMP_TAR_PATH || echo '⚠️ Не удалось удалить временный архив, возможно из-за прав (это не критично)'
"

echo "✅ Медиафайлы Django восстановлены"

# --- Остановка сервисов Django перед восстановлением базы ---
echo "🛑 Остановка сервисов Django перед восстановлением..."
# docker compose stop backend backend-celery-worker-default backend-celery-worker-ai_chat_queue backend-celery-beat
docker compose stop

# --- Восстановление базы данных ---
docker compose up $DB_CONTAINER -d
echo "🧩 Восстановление базы данных '$POSTGRES_DB'..."

docker compose cp "$SQL_DUMP_FILE" "${DB_CONTAINER}:${TMP_DUMP_PATH}"

docker compose exec -T "$DB_CONTAINER" bash -c "
  echo '🗑️ Принудительное удаление базы...'
  psql -U $POSTGRES_USER -d postgres -c \"
    SELECT pg_terminate_backend(pid)
    FROM pg_stat_activity
    WHERE datname = '$POSTGRES_DB' AND pid <> pg_backend_pid();
  \"

  psql -U $POSTGRES_USER -d postgres -c 'DROP DATABASE IF EXISTS \"$POSTGRES_DB\";'
  psql -U $POSTGRES_USER -d postgres -c 'CREATE DATABASE \"$POSTGRES_DB\" OWNER \"$POSTGRES_USER\";'

  echo '📥 Восстановление из дампа...'
  pg_restore -U $POSTGRES_USER -d \"$POSTGRES_DB\" \"$TMP_DUMP_PATH\"

  echo '🧽 Удаление временного SQL-файла...'
  rm -f \"$TMP_DUMP_PATH\"
"

echo "✅ База данных восстановлена"

# --- Запуск сервисов Django после восстановления ---
echo "🔁 Перезапуск сервисов Django..."
docker compose start

echo "🎉 Восстановление завершено успешно!"
