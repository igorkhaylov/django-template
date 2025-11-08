#!/bin/bash

echo ">>> Starting celery beat..."
celery -A config beat --loglevel=info

