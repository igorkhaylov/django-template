#!/bin/bash

# Load environments from ../.env
set -a
source "$(dirname "$0")/../.env"
set +a

docker compose exec -i redis redis-cli FLUSHALL
