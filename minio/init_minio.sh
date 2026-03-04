#!/bin/sh
set -e
set -x

echo "🛠 Installing dependencies (curl, sed)..."
apk add --no-cache curl sed

echo "⬇️ Downloading MinIO Client (mc)..."
# Определяем архитектуру (amd64 или arm64) для скачивания правильной версии
ARCH=$(uname -m)
case $ARCH in
    x86_64)  MC_ARCH="amd64" ;;
    aarch64) MC_ARCH="arm64" ;;
    *)       echo "❌ Unknown architecture: $ARCH"; exit 1 ;;
esac

# Скачиваем mc и даем права на выполнение
curl -f -s -o /usr/bin/mc "https://dl.min.io/client/mc/release/linux-${MC_ARCH}/mc"
chmod +x /usr/bin/mc

echo "⏳ Waiting for MinIO to be ready..."
# Цикл ожидания доступности сервера
until mc alias set myminio http://minio:9000 "$MINIO_ROOT_USER" "$MINIO_ROOT_PASSWORD"; do
  echo "zzz... MinIO is not ready yet. Sleeping 1s..."
  sleep 1
done

echo "✅ MinIO is up and auth is working!"

# 1. Создание бакета
echo "📦 Creating bucket: $MINIO_BUCKET_NAME"
mc mb myminio/"$MINIO_BUCKET_NAME" --ignore-existing

# 2. Настройка Public Access (через sed)
if [ -f /policies/bucket-public-read.json ]; then
    echo "🔓 Setting public policy..."
    # Теперь sed точно есть, и эта команда сработает
    sed "s/bucket_name/$MINIO_BUCKET_NAME/g" /policies/bucket-public-read.json > /tmp/bucket-public-read.json
    mc anonymous set-json /tmp/bucket-public-read.json myminio/"$MINIO_BUCKET_NAME"
else
    echo "⚠️ Warning: bucket-public-read.json not found"
fi

# 3. Создание пользователя
echo "👤 Creating user: $MINIO_APP_USER"
mc admin user add myminio "$MINIO_APP_USER" "$MINIO_APP_PASSWORD"

# 4. Применение политик пользователя (через sed)
if [ -f /policies/user-app.json ]; then
    echo "📜 Applying user policies..."
    sed "s/bucket_name/$MINIO_BUCKET_NAME/g" /policies/user-app.json > /tmp/user-app.json
    
    mc admin policy remove myminio zamon-app-policy || true
    mc admin policy create myminio zamon-app-policy /tmp/user-app.json
    mc admin policy attach myminio zamon-app-policy --user "$MINIO_APP_USER"
else
    echo "⚠️ Warning: user-app.json not found"
fi

echo "🎉 MinIO init complete!"
exit 0

