#!/bin/bash

# Load environments from ../.env
set -a
source "$(dirname "$0")/../.env"
set +a

docker compose exec -it db psql -U $POSTGRES_USER -d $POSTGRES_DB
