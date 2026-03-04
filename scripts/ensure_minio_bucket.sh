#!/usr/bin/env bash
set -euo pipefail

# Load environment variables
set -a
source "$(dirname "$0")/../.env"
set +a

MINIO_PORT="${MINIO_PORT:-9000}"

docker run --rm --network host \
    -e MINIO_URL="http://localhost:${MINIO_PORT}" \
    -e MINIO_ROOT_USER="${MINIO_ROOT_USER}" \
    -e MINIO_ROOT_PASSWORD="${MINIO_ROOT_PASSWORD}" \
    -e BUCKET_NAME="${MINIO_BUCKET_NAME}" \
    -e APP_USER="${MINIO_APP_USER}" \
    -e APP_PASSWORD="${MINIO_APP_PASSWORD}" \
    --entrypoint sh \
    minio/mc:latest -c '
set -e

ALIAS="localminio"

echo "Waiting for MinIO at ${MINIO_URL}..."
until mc alias set "$ALIAS" "$MINIO_URL" "$MINIO_ROOT_USER" "$MINIO_ROOT_PASSWORD" >/dev/null 2>&1; do
    sleep 1
done
echo "MinIO is ready."

if mc ls "$ALIAS/$BUCKET_NAME" >/dev/null 2>&1; then
    echo "Bucket $BUCKET_NAME already exists."
else
    echo "Creating bucket $BUCKET_NAME..."
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
      "Resource": ["arn:aws:s3:::${BUCKET_NAME}/*"]
    }
  ]
}
POLICY
mc anonymous set-json /tmp/bucket-public-read.json "$ALIAS/$BUCKET_NAME"

echo "Ensuring app user $APP_USER..."
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
        "arn:aws:s3:::${BUCKET_NAME}",
        "arn:aws:s3:::${BUCKET_NAME}/*"
      ]
    }
  ]
}
POLICY
mc admin policy remove "$ALIAS" "$POLICY_NAME" 2>/dev/null || true
mc admin policy create "$ALIAS" "$POLICY_NAME" /tmp/user-policy.json
mc admin policy attach "$ALIAS" "$POLICY_NAME" --user "$APP_USER" 2>/dev/null || true

echo ""
echo "Bucket $BUCKET_NAME is ready."
echo "  App user:     $APP_USER"
echo "  App password: $APP_PASSWORD"
echo "  Endpoint:     $MINIO_URL"
'
