"""
Celery Configuration
https://docs.celeryq.dev/en/latest/userguide/configuration.html
"""

import os

from django.conf import settings

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")


REDIS_HOST = settings.REDIS_HOST
REDIS_PORT = settings.REDIS_PORT

app = Celery(settings.APP_NAME)

# Broker + result backend: Redis db 0. The Django cache lives in db 1 (settings/base.py)
# so `make flush-cache` can clear the cache without dropping queued tasks.
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

# Redis transport tuning. NOTE: broker_heartbeat is AMQP-only and silently ignored by
# the Redis transport — do not add it; socket liveness is health_check_interval's job.
app.conf.broker_transport_options = {
    # How long a reserved-but-unacked message stays invisible before Redis re-delivers
    # it to another worker. Applies to ETA/countdown/retry tasks (and to every task if
    # task_acks_late is enabled). MUST exceed the longest task runtime / ETA delay —
    # task_time_limit is 3h — or such tasks get duplicated.
    "visibility_timeout": 4 * 60 * 60,
    "health_check_interval": 25,  # ping the broker socket every 25s; reconnect if dead
    "socket_keepalive": True,  # TCP keepalive so half-dead connections are detected
    "retry_on_timeout": True,  # retry Redis commands that hit a socket timeout
}

# Beat schedule file
app.conf.beat_schedule_filename = "/tmp/celerybeat-schedule"

# Autodiscover tasks from all installed apps
app.autodiscover_tasks()
