from decouple import config

__all__ = ("STORAGES",)


# Настройки S3 (MinIO), работают если не указать в STORAGES["default"]["OPTIONS"]
AWS_ACCESS_KEY_ID = config("MINIO_APP_USER")
AWS_SECRET_ACCESS_KEY = config("MINIO_APP_PASSWORD")
AWS_STORAGE_BUCKET_NAME = config("MINIO_BUCKET_NAME")
AWS_S3_ENDPOINT_URL = config(
    "DJANGO_MINIO_ENDPOINT"
)  # Внутренний адрес Docker для загрузки
AWS_S3_REGION_NAME = "us-east-1"  # Формальность для MinIO
AWS_S3_ADDRESSING_STYLE = "path"  # Важно для MinIO

# Важно: подпись ссылок.
# Если бакет публичный (как мы сделали), ставим False, чтобы ссылки не протухали.
AWS_QUERYSTRING_AUTH = False


# # Настройка генерации URL
# # Мы хотим, чтобы Django генерировал ссылки вида: http://ваш-сайт.com/media/imagename.jpg
# # А не: http://minio:9000/bucket/imagename.jpg (пользователь туда не достучится)
# AWS_S3_CUSTOM_DOMAIN = f'{config("DOMAIN_NAME", "localhost")}/media'
# AWS_S3_CUSTOM_DOMAIN = f"192.168.0.102:9000/{AWS_STORAGE_BUCKET_NAME}"

protocol_name, custom_domain = config(
    "MINIO_ENDPOINT", default="http://localhost:9000"
).split("://")

AWS_S3_URL_PROTOCOL = f"{protocol_name}:"
AWS_S3_CUSTOM_DOMAIN = f"{custom_domain}/{AWS_STORAGE_BUCKET_NAME}"


STORAGES = {
    "default": {
        "BACKEND": "storages.backends.s3.S3Storage",
        "OPTIONS": {
            "access_key": AWS_ACCESS_KEY_ID,
            "secret_key": AWS_SECRET_ACCESS_KEY,
            "bucket_name": AWS_STORAGE_BUCKET_NAME,
            "endpoint_url": AWS_S3_ENDPOINT_URL,
            "region_name": AWS_S3_REGION_NAME,
            "querystring_auth": AWS_QUERYSTRING_AUTH,
            "addressing_style": AWS_S3_ADDRESSING_STYLE,  # Важно для MinIO
            "url_protocol": AWS_S3_URL_PROTOCOL,
            "custom_domain": AWS_S3_CUSTOM_DOMAIN,
            "file_overwrite": False,
        },
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}
