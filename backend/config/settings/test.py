"""Test settings — runnable with NO external services.

Used by pytest via `DJANGO_SETTINGS_MODULE = "config.settings.test"` (pyproject.toml).
Everything heavy (Postgres, Redis, S3/MinIO, real email, Celery broker) is swapped for
in-memory/local backends so the suite runs anywhere (pytest builds the schema straight
from the models via --no-migrations, so it is independent of migration state).
"""

import os

# Force ENVIRONMENT=test regardless of what the surrounding environment exports (the dev
# container carries ENVIRONMENT=dev from .env). See config/settings/__init__.py.
os.environ["ENVIRONMENT"] = "test"

from .base import *
from .third_party import *

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.InMemoryStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
}

CACHES = {
    "default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"},
}

EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

# Run Celery tasks synchronously in-process.
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

# Quieter logs during tests.
LOG_LEVEL = "WARNING"
LOGGING["root"]["level"] = "WARNING"
