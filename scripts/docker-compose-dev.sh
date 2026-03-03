#!/bin/bash

# Wrapper for docker compose with multiple config files
docker compose -f docker-compose.dev.yml "$@"