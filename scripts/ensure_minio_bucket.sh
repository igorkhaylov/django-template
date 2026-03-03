#!/usr/bin/env bash
set -euo pipefail

MINIO_ROOT_USER="${MINIO_ROOT_USER:-minioadmin}"
MINIO_ROOT_PASSWORD="${MINIO_ROOT_PASSWORD:-minioadmin}"
MINIO_PORT="${MINIO_PORT:-9000}"

BUCKET_NAME="stv-local-bucket"
APP_USER="stv-app"
APP_PASSWORD="${MINIO_APP_PASSWORD:-stv_app_secret_password}"

docker run --rm --network host alpine:latest sh -c '
set -e

MINIO_URL="http://localhost:'"$MINIO_PORT"'"
ALIAS="localminio"
BUCKET_NAME="'"$BUCKET_NAME"'"
APP_USER="'"$APP_USER"'"
APP_PASSWORD="'"$APP_PASSWORD"'"
MINIO_ROOT_USER="'"$MINIO_ROOT_USER"'"
MINIO_ROOT_PASSWORD="'"$MINIO_ROOT_PASSWORD"'"

apk add --no-cache curl >/dev/null 2>&1

ARCH=$(uname -m)
case $ARCH in
    x86_64)  MC_ARCH="amd64" ;;
    aarch64) MC_ARCH="arm64" ;;
    *)       echo "Unknown architecture: $ARCH"; exit 1 ;;
esac
curl -f -s -o /usr/bin/mc "https://dl.min.io/client/mc/release/linux-${MC_ARCH}/mc"
chmod +x /usr/bin/mc

echo "Waiting for MinIO at ${MINIO_URL}..."
until mc alias set "$ALIAS" "$MINIO_URL" "$MINIO_ROOT_USER" "$MINIO_ROOT_PASSWORD" >/dev/null 2>&1; do
    sleep 1
done
echo "MinIO is ready."

if mc ls "$ALIAS/$BUCKET_NAME" >/dev/null 2>&1; then
    echo "Bucket '\''$BUCKET_NAME'\'' already exists."
else
    echo "Creating bucket '\''$BUCKET_NAME'\''..."
    mc mb "$ALIAS/$BUCKET_NAME"
fi

echo "Setting public read policy..."
cat <<POLICY > /tmp/bucket-public-read.json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {"AWS": ["*"]},
      "Action": ["s3:GetObject"],
      "Resource": ["arn:aws:s3:::'"$BUCKET_NAME"'/*"]
    }
  ]
}
POLICY
mc anonymous set-json /tmp/bucket-public-read.json "$ALIAS/$BUCKET_NAME"

echo "Ensuring app user '\''$APP_USER'\''..."
mc admin user add "$ALIAS" "$APP_USER" "$APP_PASSWORD" 2>/dev/null || true

POLICY_NAME="${APP_USER}-policy"
cat <<POLICY > /tmp/user-policy.json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:ListBucketMultipartUploads",
        "s3:ListMultipartUploadParts",
        "s3:PutObject",
        "s3:AbortMultipartUpload",
        "s3:DeleteObject",
        "s3:GetObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::'"$BUCKET_NAME"'",
        "arn:aws:s3:::'"$BUCKET_NAME"'/*"
      ]
    }
  ]
}
POLICY
mc admin policy remove "$ALIAS" "$POLICY_NAME" 2>/dev/null || true
mc admin policy create "$ALIAS" "$POLICY_NAME" /tmp/user-policy.json
mc admin policy attach "$ALIAS" "$POLICY_NAME" --user "$APP_USER" 2>/dev/null || true

echo ""
echo "Bucket '\''$BUCKET_NAME'\'' is ready."
echo "  App user:     $APP_USER"
echo "  App password: $APP_PASSWORD"
echo "  Endpoint:     $MINIO_URL"
'
