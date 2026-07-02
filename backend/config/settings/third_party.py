from urllib.parse import urlsplit

import structlog
from decouple import config

from .base import APP_NAME, DEBUG

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
# All values have safe defaults so management commands, tests and CI can import
# settings without a full MinIO environment. Override them in .env for real use.
# Static and media are served by S3/MinIO (NOT by nginx).

_minio_access_key = config("DJANGO_MINIO_ACCESS_KEY", default="minioadmin")
_minio_secret_key = config("DJANGO_MINIO_SECRET_KEY", default="minioadmin")
_minio_bucket = config("DJANGO_MINIO_BUCKET_NAME", default="app-bucket")
_minio_endpoint = config("DJANGO_MINIO_ENDPOINT", default="http://host.docker.internal:9000")  # shared host MinIO / S3

# Public URL used to build media/static links. Parsed robustly so a missing/extra
# "://" can't raise at import time.
_custom_url = config("DJANGO_MINIO_CUSTOM_URL", default="http://localhost:9000")
_parsed = urlsplit(_custom_url)
_protocol = _parsed.scheme or "http"
_domain = _parsed.netloc or _parsed.path  # tolerate a bare "host:port" without scheme

_s3_options = {
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
}

STORAGES = {
    "default": {
        "BACKEND": "storages.backends.s3.S3Storage",
        "OPTIONS": _s3_options,
    },
    "staticfiles": {
        "BACKEND": "storages.backends.s3.S3Storage",
        "OPTIONS": {**_s3_options, "location": "static", "file_overwrite": True},
    },
}


# =============================================================================
# Rosetta (translation UI)
# =============================================================================

ROSETTA_MESSAGES_PER_PAGE = 20
ROSETTA_SHOW_AT_ADMIN_PANEL = True


def _rosetta_access_control(user) -> bool:
    return user.is_superuser or user.has_perm("auth.can_change_rosetta_messages")


ROSETTA_ACCESS_CONTROL_FUNCTION = _rosetta_access_control
ROSETTA_LOGIN_URL = "/admin/login/"

# =============================================================================
# Logging (django-structlog -> stdout)
# =============================================================================
# Logs go to the container's stdout only (no files). The level is controlled by
# DJANGO_LOG_LEVEL (default INFO). Dev gets a human-friendly console renderer;
# stage/prod emit one JSON object per line for log shippers.

LOG_LEVEL = config("DJANGO_LOG_LEVEL", default="INFO").upper()

_shared_processors = [
    structlog.contextvars.merge_contextvars,
    structlog.stdlib.add_logger_name,
    structlog.stdlib.add_log_level,
    structlog.stdlib.PositionalArgumentsFormatter(),
    structlog.processors.TimeStamper(fmt="iso"),
    structlog.processors.StackInfoRenderer(),
    structlog.processors.format_exc_info,
    structlog.processors.UnicodeDecoder(),
]

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json": {
            "()": structlog.stdlib.ProcessorFormatter,
            "processor": structlog.processors.JSONRenderer(),
            "foreign_pre_chain": _shared_processors,
        },
        "console": {
            "()": structlog.stdlib.ProcessorFormatter,
            "processor": structlog.dev.ConsoleRenderer(colors=True),
            "foreign_pre_chain": _shared_processors,
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "console" if DEBUG else "json",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": LOG_LEVEL,
    },
    "loggers": {
        "django": {"handlers": ["console"], "level": LOG_LEVEL, "propagate": False},
        "django_structlog": {"handlers": ["console"], "level": LOG_LEVEL, "propagate": False},
        "celery": {"handlers": ["console"], "level": LOG_LEVEL, "propagate": False},
    },
}

structlog.configure(
    processors=[
        *_shared_processors,
        structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
    ],
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)
