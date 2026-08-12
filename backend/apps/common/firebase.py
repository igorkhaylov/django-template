"""Firebase Admin SDK bootstrap for the optional "push" feature.

Importing this module initializes the Firebase app as a side effect. Nothing
imports it by default, and firebase-admin is NOT a base dependency — it lives
in [project.optional-dependencies] under the "push" extra. To enable pushes:

1. Install the extra: `uv sync --extra push` (for Docker, add `--extra push`
   to EVERY `uv sync` invocation: both branches in the Dockerfile builder
   stage and the one in Dockerfile.dev).
2. Drop the service-account JSON into firebase_credentials/ (both git- and
   docker-ignored) and set FIREBASE_JSON_PATH to it in settings. In prod the
   file is deliberately NOT baked into the image — deliver it at runtime with
   a volume mount on the backend/celery services in docker-compose.prod.yml,
   e.g. `- ./firebase_credentials:/app/firebase_credentials:ro`.
3. Import this module once at startup, e.g. in CommonConfig.ready().
"""

import logging
from pathlib import Path

from django.conf import settings

import firebase_admin
from firebase_admin import credentials

_logger = logging.getLogger(__name__)


if not firebase_admin._apps:
    firebase_json_path = getattr(settings, "FIREBASE_JSON_PATH", None)

    if firebase_json_path and Path(firebase_json_path).exists():
        cred = credentials.Certificate(firebase_json_path)
        firebase_admin.initialize_app(cred)
        _logger.info("Firebase app initialized successfully")
    else:
        _logger.info("Firebase JSON credentials not found, skipping initialization")
