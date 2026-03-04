import json
import logging
from datetime import datetime
from zoneinfo import ZoneInfo

from decouple import config

from .base import APP_NAME, BASE_DIR, TIME_ZONE

# =============================================================================
# Django REST Framework
# =============================================================================

REST_FRAMEWORK = {
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_AUTHENTICATION_CLASSES": (
        # "rest_framework.authentication.SessionAuthentication",
        # "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_FILTER_BACKENDS": ["django_filters.rest_framework.DjangoFilterBackend"],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.LimitOffsetPagination",
    "PAGE_SIZE": 100,
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
        "rest_framework.renderers.BrowsableAPIRenderer",
    ],
}

SPECTACULAR_SETTINGS = {
    "TITLE": f"{APP_NAME} API",
    "DESCRIPTION": "Project description",
    "VERSION": "0.0.1",
    "SERVE_INCLUDE_SCHEMA": False,
    "SERVE_PERMISSIONS": ["rest_framework.permissions.IsAdminUser"],
    "SERVE_AUTHENTICATION": [
        "rest_framework.authentication.SessionAuthentication",
    ],
}

# =============================================================================
# Storage (S3 / MinIO)
# =============================================================================

_minio_access_key = config("DJANGO_MINIO_ACCESS_KEY")
_minio_secret_key = config("DJANGO_MINIO_SECRET_KEY")
_minio_bucket = config("DJANGO_MINIO_BUCKET_NAME")
_minio_endpoint = config("DJANGO_MINIO_ENDPOINT")  # Internal Docker address

_protocol, _domain = config("DJANGO_MINIO_CUSTOM_URL", default="http://localhost:9000").split("://")

STORAGES = {
    "default": {
        "BACKEND": "storages.backends.s3.S3Storage",
        "OPTIONS": {
            "access_key": _minio_access_key,
            "secret_key": _minio_secret_key,
            "bucket_name": _minio_bucket,
            "endpoint_url": _minio_endpoint,
            "region_name": "us-east-1",
            "querystring_auth": False,  # Public bucket: URLs don't expire
            "addressing_style": "path",  # Required for MinIO
            "url_protocol": f"{_protocol}:",
            "custom_domain": f"{_domain}/{_minio_bucket}",
            "file_overwrite": False,
        },
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}

# =============================================================================
# Rosetta (translation UI)
# =============================================================================

ROSETTA_MESSAGES_PER_PAGE = 20
ROSETTA_SHOW_AT_ADMIN_PANEL = True
ROSETTA_ACCESS_CONTROL_FUNCTION = lambda user: user.is_superuser or user.has_perm("auth.can_change_rosetta_messages")
ROSETTA_LOGIN_URL = "/admin/login/"

# =============================================================================
# Logging
# =============================================================================

_LOG_DIR = BASE_DIR / "logs"
_LOG_DIR.mkdir(parents=True, exist_ok=True)


class _JsonFormatter(logging.Formatter):
    def format(self, record):
        log_message = {
            "level": record.levelname,
            "module": record.module,
            "timestamp": datetime.fromtimestamp(record.created, tz=ZoneInfo(TIME_ZONE)).isoformat(),
        }
        if isinstance(record.msg, dict):
            log_message["message"] = record.msg
        else:
            log_message["message"] = record.getMessage()
        return json.dumps(log_message, ensure_ascii=False)


LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json": {"()": _JsonFormatter},
        "verbose": {
            "format": "{levelname} {asctime} {module} {message}",
            "style": "{",
            "datefmt": "%Y-%m-%dT%H:%M:%S%z",
        },
        "simple": {
            "format": "{levelname} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
        "error_file": {
            "level": "ERROR",
            "class": "logging.FileHandler",
            "filename": _LOG_DIR / "error.log",
            "formatter": "verbose",
        },
        "file_json": {
            "level": "DEBUG",
            "class": "logging.FileHandler",
            "filename": _LOG_DIR / "file_json.log",
            "formatter": "json",
        },
    },
    "loggers": {
        "django": {
            "handlers": ["console", "error_file"],
            "level": "INFO",
            "propagate": False,
        },
        "file_json": {
            "handlers": ["file_json"],
            "level": "DEBUG",
            "propagate": True,
        },
    },
}
