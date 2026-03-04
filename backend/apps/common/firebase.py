import logging
from pathlib import Path

import firebase_admin
from django.conf import settings
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
