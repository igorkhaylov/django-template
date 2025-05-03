import json
import logging
from datetime import datetime

import pytz

from .base import BASE_DIR
from .localization import TIME_ZONE

BASE_LOG_DIR = BASE_DIR / "logs"

BASE_LOG_DIR.mkdir(parents=True, exist_ok=True)


__all__ = ("LOGGING",)


class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_message = {
            "level": record.levelname,
            "module": record.module,
        }
        # log_message["timestamp"] = datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat()
        log_message["timestamp"] = datetime.fromtimestamp(
            record.created, tz=pytz.timezone(TIME_ZONE)
        ).isoformat()

        # Если message — словарь, добавляем его напрямую
        if isinstance(record.msg, dict):
            log_message["message"] = record.msg
        else:
            log_message["message"] = record.getMessage()

        return json.dumps(log_message, ensure_ascii=False)


LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json": {
            "()": JsonFormatter,
        },
        "verbose": {
            "format": "{levelname} {asctime} {module} {message}",
            "style": "{",
            "datefmt": "%Y-%m-%dT%H:%M:%S%z",  # ISO 8601 формат
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
            "formatter": "verbose",  # "simple",
        },
        "error_file": {
            "level": "ERROR",
            "class": "logging.FileHandler",
            "filename": BASE_LOG_DIR / "error.log",
            "formatter": "verbose",
        },
        "file_json": {
            "level": "DEBUG",
            "class": "logging.FileHandler",
            "filename": BASE_LOG_DIR / "file_json.log",
            "formatter": "json",
        },
    },
    "loggers": {
        "django": {
            # "handlers": ["console", "error_file"],
            "handlers": ["console", "error_file"],
            "level": "INFO",  # DEBUG, INFO, WARNING, ERROR, CRITICAL
            "propagate": False,  # propagate=True, логи будут передаваться родительским логгерам
        },
        "file_json": {
            "handlers": ["file_json"],
            "level": "DEBUG",  # DEBUG, INFO, WARNING, ERROR, CRITICAL
            "propagate": True,  # propagate=True, логи будут передаваться родительским логгерам
        },
    },
}
