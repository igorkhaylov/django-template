#!/bin/bash

echo ">>> Starting celery worker with queue name celery..."
celery -A config worker --loglevel=INFO --concurrency=2 -Q celery

