"""
Celery Configuration
https://docs.celeryq.dev/en/latest/userguide/configuration.html
"""

import os

from celery import Celery
from django.conf import settings

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")


REDIS_HOST = settings.REDIS_HOST
REDIS_PORT = settings.REDIS_PORT

app = Celery(settings.APP_NAME)

# Broker + result backend
app.conf.broker_url = f"redis://{REDIS_HOST}:{REDIS_PORT}/0"
app.conf.result_backend = f"redis://{REDIS_HOST}:{REDIS_PORT}/0"

# Core settings
app.conf.timezone = settings.TIME_ZONE
app.conf.task_track_started = True
app.conf.task_soft_time_limit = 3 * 60 * 60  # soft limit (warning)
app.conf.task_time_limit = 3 * 60 * 60 + 60  # hard limit (kill after 60s grace)
app.conf.task_default_queue = "celery"

# Serialization
app.conf.accept_content = ["application/json"]
app.conf.task_serializer = "json"
app.conf.result_accept_content = ["application/json"]
app.conf.result_serializer = "json"

# Broker reconnect options
app.conf.broker_connection_retry_on_startup = True
app.conf.broker_connection_max_retries = None
app.conf.broker_connection_retry = True
app.conf.broker_connection_timeout = 4.0
app.conf.broker_heartbeat = 10

# Beat schedule file
app.conf.beat_schedule_filename = "celerybeat-schedule"

# Autodiscover tasks from all installed apps
app.autodiscover_tasks()
