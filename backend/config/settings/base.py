import os
import sys
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured
from django.utils.translation import gettext_lazy as _

from corsheaders.defaults import default_headers, default_methods
from decouple import config

# =============================================================================
# Paths
# =============================================================================

BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.append(os.path.join(BASE_DIR, "apps"))

# =============================================================================
# Core
# =============================================================================

ENVIRONMENT = config("ENVIRONMENT", default="prod")
_ALLOWED_ENVIRONMENTS = ("dev", "test", "stage", "prod")
if ENVIRONMENT not in _ALLOWED_ENVIRONMENTS:
    raise ImproperlyConfigured(
        f"ENVIRONMENT must be one of {_ALLOWED_ENVIRONMENTS}, got {ENVIRONMENT!r}. "
        "DEBUG and all security flags are derived from this single value, so an "
        "unrecognized value (e.g. 'production') would silently run insecurely."
    )

# Single source of truth: derive DEBUG and every security flag from the validated value.
DEBUG = ENVIRONMENT == "dev"
IS_SECURE_ENV = ENVIRONMENT in ("stage", "prod")

APP_NAME = config("DJANGO_APP_NAME", default="AppName")

# A dev-friendly default keeps management commands and tests runnable without a full
# environment; stage/prod must provide a strong, explicit key (validated just below).
SECRET_KEY = config("DJANGO_SECRET_KEY", default="django-insecure-dev-only-change-me")
if IS_SECURE_ENV and (SECRET_KEY.startswith("django-insecure") or len(SECRET_KEY) < 50):
    raise ImproperlyConfigured(
        "DJANGO_SECRET_KEY must be a strong, explicit value of at least 50 chars in "
        "stage/prod. Generate one with: openssl rand -hex 64"
    )

ALLOWED_HOSTS = config(
    "DJANGO_ALLOWED_HOSTS",
    default="",
    cast=lambda v: [x for s in v.split(",") if (x := s.strip())],
)

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# =============================================================================
# Security
# =============================================================================

# This app ALWAYS runs behind a reverse proxy that terminates TLS, holds the
# certificates and sets `X-Forwarded-Proto`. Django trusts that header here, so it
# correctly treats proxied HTTPS requests as secure and SECURE_SSL_REDIRECT does not
# loop. The in-stack nginx must NOT re-set X-Forwarded-Proto — doing so would overwrite
# the edge proxy's value (the line is intentionally left commented in nginx/nginx.conf).
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

SECURE_SSL_REDIRECT = IS_SECURE_ENV
SECURE_REDIRECT_EXEMPT = [r"^healthcheck/"]

SESSION_COOKIE_SECURE = IS_SECURE_ENV
CSRF_COOKIE_SECURE = IS_SECURE_ENV

SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"

# HSTS is only meaningful once TLS terminates correctly at the reverse proxy.
SECURE_HSTS_SECONDS = 31536000 if IS_SECURE_ENV else 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = IS_SECURE_ENV
SECURE_HSTS_PRELOAD = IS_SECURE_ENV

# Cap request body size (Django default is 2.5 MB); large media goes to S3 directly.
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10 MB
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10 MB

CSRF_TRUSTED_ORIGINS = config(
    "DJANGO_CSRF_TRUSTED_ORIGINS",
    default="",
    cast=lambda v: [x for s in v.split(",") if (x := s.strip())],
)

CORS_ALLOWED_ORIGINS = config(
    "DJANGO_CORS_ALLOWED_ORIGINS",
    default="",
    cast=lambda v: [x for s in v.split(",") if (x := s.strip())],
)
CORS_ALLOW_HEADERS = (*default_headers,)
CORS_ALLOW_METHODS = (*default_methods,)
CORS_ALLOW_CREDENTIALS = True

# =============================================================================
# Apps & Middleware
# =============================================================================

INSTALLED_APPS = [
    # Django (modeltranslation must be before admin)
    "modeltranslation",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Third-party
    "django_cleanup.apps.CleanupConfig",
    "rosetta",
    "drf_spectacular",
    "rest_framework",
    "django_filters",
    "corsheaders",
    "django_structlog",
    "stdimage",
    # Local
    "common",
    "users",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    # Binds request_id + user_id to every structlog log line.
    "django_structlog.middlewares.RequestMiddleware",
]

# =============================================================================
# Database
# =============================================================================

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": config("POSTGRES_DB", default="app"),
        "USER": config("POSTGRES_USER", default="app"),
        "PASSWORD": config("POSTGRES_PASSWORD", default="app"),
        "HOST": config("POSTGRES_HOST", default="db"),
        "PORT": config("POSTGRES_PORT", default="5432"),
    }
}

# =============================================================================
# Cache (Redis)
# =============================================================================

REDIS_HOST = config("REDIS_HOST", default="redis")
REDIS_PORT = config("REDIS_PORT", default=6379, cast=int)

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": f"redis://{REDIS_HOST}:{REDIS_PORT}",
        "TIMEOUT": 600,
    }
}

# =============================================================================
# Auth
# =============================================================================

AUTH_USER_MODEL = "users.User"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# =============================================================================
# Templates
# =============================================================================

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

# =============================================================================
# Static & Media
# =============================================================================

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "static"
STATICFILES_DIRS = [BASE_DIR / "static_src"]

MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

# =============================================================================
# Internationalization
# =============================================================================

LANGUAGE_CODE = "en"
TIME_ZONE = "Asia/Tashkent"
USE_I18N = True
USE_TZ = True

LANGUAGES = (
    ("en", _("English")),
    ("ru", _("Русский")),
)

LOCALE_PATHS = [BASE_DIR / "locale/"]

MODELTRANSLATION_DEFAULT_LANGUAGE = "en"
MODELTRANSLATION_LANGUAGES = ("en", "ru")
