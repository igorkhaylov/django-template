import json
import logging
from datetime import datetime
from zoneinfo import ZoneInfo

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
        log_message["timestamp"] = datetime.fromtimestamp(
            record.created, tz=ZoneInfo(TIME_ZONE)
        ).isoformat()

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
