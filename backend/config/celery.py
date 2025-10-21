"""
Docs Configuration
https://docs.celeryq.dev/en/latest/userguide/configuration.html
"""

import os

from celery import Celery, shared_task
from celery.schedules import crontab
from django.conf import settings

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")


REDIS_HOST = settings.REDIS_HOST
REDIS_PORT = settings.REDIS_PORT

app = Celery(settings.APP_NAME)

# app.config_from_object("django.conf:settings", namespace="CELERY")

# --- Настройки Celery (вместо settings.py) ---

# --- Подключение broker + backend ---
app.conf.broker_url = f"redis://{REDIS_HOST}:{REDIS_PORT}/0"
app.conf.result_backend = f"redis://{REDIS_HOST}:{REDIS_PORT}/0"

# --- Основные настройки ---
app.conf.timezone = "Asia/Tashkent"
app.conf.task_track_started = True
task_soft_time_limit = 3 * 60 * 60  # предупреждение
task_time_limit = 3 * 60 * 60 + 60  # принудительное убийство

app.conf.task_default_queue = "celery"  # Название очереди по умолчанию, если не задано

# --- Форматы ---
app.conf.accept_content = ["application/json"]
app.conf.task_serializer = "json"
app.conf.result_accept_content = ["application/json"]
app.conf.result_serializer = "json"


# --- Broker reconnect options ---
app.conf.broker_connection_retry_on_startup = True
app.conf.broker_connection_max_retries = None
app.conf.broker_connection_retry = True
app.conf.broker_connection_timeout = 4.0
app.conf.broker_heartbeat = 10

# --- Beat schedule file ---
app.conf.beat_schedule_filename = "celerybeat-schedule"

# --- Autodiscover ---
app.autodiscover_tasks()


@shared_task
def print_hello():
    print("Hello from Celery!")


app.conf.beat_schedule = {
    "print_hello": {
        "task": "config.celery.print_hello",
        # "schedule": crontab(hour="*", minute=0),  # Execute every hour at 0 minute
        "schedule": 10,  # Execute every 10 seconds
        "args": [],
        "kwargs": {},
        "options": {
            "queue": "celery",
        },
    },
}
