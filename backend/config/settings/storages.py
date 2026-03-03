from decouple import config

__all__ = ("STORAGES",)


# S3 (MinIO) settings
AWS_ACCESS_KEY_ID = config("DJANGO_MINIO_ACCESS_KEY")
AWS_SECRET_ACCESS_KEY = config("DJANGO_MINIO_SECRET_KEY")
AWS_STORAGE_BUCKET_NAME = config("DJANGO_MINIO_BUCKET_NAME")
AWS_S3_ENDPOINT_URL = config("DJANGO_MINIO_ENDPOINT")  # Internal Docker address
AWS_S3_REGION_NAME = "us-east-1"
AWS_S3_ADDRESSING_STYLE = "path"  # Required for MinIO

# Public bucket: disable query string auth so URLs don't expire
AWS_QUERYSTRING_AUTH = False

protocol_name, custom_domain = config(
    "DJANGO_MINIO_CUSTOM_URL", default="http://localhost:9000"
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
            "addressing_style": AWS_S3_ADDRESSING_STYLE,
            "url_protocol": AWS_S3_URL_PROTOCOL,
            "custom_domain": AWS_S3_CUSTOM_DOMAIN,
            "file_overwrite": False,
        },
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}
