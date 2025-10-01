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
        _logger.info("🔥 Firebase App 1 успешно инициализирован!")
    else:
        _logger.info("⚠️ Firebase App 1 JSON credentials не найдены!")

# TODO func for convert all dict data to string, cause All keys and values in the dictionary must be strings.
# TODO MulticastMessage.tokens must not contain more than 500 tokens, if more, split on several messages
