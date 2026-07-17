# Usage:
#   make init               # FIRST RUN: .env + generated secrets, MinIO bucket, dev stack, migrate
#   make dev up             # start the development stack (containers up; backend idle)
#   make dev run            # run the Django dev server (autoreload) — reach it at APP_PORT
#   make up                 # local production-like stack (builds + serves via gunicorn)
#   make prod deploy        # SERVER: pull the registry image and (re)start (no build)
#   make dev makemigrations # run a manage.py command in the dev stack
#   make dev logs backend   # tail logs of a service
#   make minio              # provision bucket on the SHARED local MinIO (host service)
#
# DEV WORKFLOW: `make dev up` brings the stack online but the backend just idles
# (`sleep infinity`) so you can run migrations/shell/tests freely against a live DB.
# It does NOT serve HTTP by itself — start the server explicitly with `make dev run`
# (foreground, autoreload), then open http://localhost:$APP_PORT.
#
# Prefix selects the compose file:
#   dev  -> docker-compose.dev.yml   (repo bind-mounted at /app, manage.py at /app/backend -> EXEC)
#   prod -> docker-compose.prod.yml  (pulls the prebuilt image; never builds)
#   none -> docker-compose.yml       (local, builds from source)

ifneq ($(filter dev,$(MAKECMDGOALS)),)
  COMPOSE := docker compose -f docker-compose.dev.yml
  EXEC := --workdir /app/backend
else ifneq ($(filter prod,$(MAKECMDGOALS)),)
  COMPOSE := docker compose -f docker-compose.prod.yml
  EXEC :=
else
  COMPOSE := docker compose
  EXEC :=
endif

# Extra args: MAKECMDGOALS minus "dev"/"prod" and the target name ($@).
ARGS = $(filter-out dev prod $@,$(MAKECMDGOALS))

# Every real target — used for .PHONY and for the typo guard below.
KNOWN_TARGETS := help init up run down down-v build pull deploy logs shell dbshell \
        migrate makemigrations makemessages compilemessages collectstatic \
        createsuperuser test lint format pre-commit-install minio flush-redis \
        dump restore bash bash-db bash-nginx

.PHONY: dev prod $(KNOWN_TARGETS)

# Typo guard: the first goal after the dev/prod prefix must be a real target. Without
# this the catch-all `%:` at the bottom silently swallows typos (`make dev migrat`
# would exit 0 doing nothing). Extra words AFTER a real target (`make logs backend`,
# `make restore dumps/<ts>`) still pass through the catch-all as arguments.
PRIMARY_GOAL := $(firstword $(filter-out dev prod,$(MAKECMDGOALS)))
ifneq ($(PRIMARY_GOAL),)
  ifeq ($(filter $(PRIMARY_GOAL),$(KNOWN_TARGETS)),)
    $(error Unknown target '$(PRIMARY_GOAL)' — run 'make help' for the list)
  endif
endif

help:
	@echo "First run:   make init    # .env + generated secrets, MinIO bucket, dev stack, migrate"
	@echo "Prefix a target with 'dev' (development) or 'prod' (pull-based deploy):"
	@echo "  dev up      then  dev run        # start stack, then serve (autoreload) at APP_PORT"
	@echo "  up / down / down-v / build / logs [service]"
	@echo "  prod pull / prod deploy          # server: pull the registry image and (re)start"
	@echo "  shell dbshell bash bash-db bash-nginx"
	@echo "  migrate makemigrations makemessages compilemessages collectstatic createsuperuser"
	@echo "  test lint format pre-commit-install"
	@echo "  minio flush-redis dump restore"

dev:
	@:

prod:
	@:

# --- First-time setup ---
# One command from a fresh clone to a migrated dev stack: create .env with generated
# secrets (never overwrites an existing one), provision the shared MinIO bucket, start
# the DEV stack and apply migrations. Targets the dev compose explicitly, so no `dev`
# prefix is needed. Safe to re-run. Then: `make dev createsuperuser`, `make dev run`.
DEV_COMPOSE := docker compose -f docker-compose.dev.yml
init:
	./scripts/init_env.sh
	./scripts/ensure_minio.sh
	$(DEV_COMPOSE) up -d --build
	$(DEV_COMPOSE) exec --workdir /app/backend backend python manage.py migrate
	@echo ""
	@echo "Done. Next steps:"
	@echo "  make dev createsuperuser    # create your admin account"
	@echo "  make dev run                # dev server -> http://localhost:8050 (APP_PORT)"

# --- Docker lifecycle ---
up:
	$(COMPOSE) up -d --build

# Dev only: run the Django dev server in the foreground (autoreload) inside the
# already-running backend container. Reachable via nginx at http://localhost:$APP_PORT.
# Run `make dev up` first. Ctrl-C stops the server; the stack keeps running.
run:
	$(COMPOSE) exec $(EXEC) backend python manage.py runserver 0.0.0.0:8000

down:
	$(COMPOSE) down

down-v:
	$(COMPOSE) down -v

build:
	$(COMPOSE) build

pull:
	$(COMPOSE) pull

# Server-side deploy: pull the prebuilt image from the registry and (re)start.
# Usage on the server:  make prod deploy
# Pin a tag by exporting BACKEND_IMAGE (or set it in .env) before running.
deploy:
	$(COMPOSE) pull
	$(COMPOSE) up -d

logs:
	$(COMPOSE) logs -f $(ARGS)

# --- Django management ---
shell:
	$(COMPOSE) exec $(EXEC) backend python manage.py shell

dbshell:
	$(COMPOSE) exec db psql -U $${POSTGRES_USER:-app} -d $${POSTGRES_DB:-app}

migrate:
	$(COMPOSE) exec $(EXEC) backend python manage.py migrate

makemigrations:
	$(COMPOSE) exec $(EXEC) backend python manage.py makemigrations

makemessages:
	$(COMPOSE) exec $(EXEC) backend python manage.py makemessages -l ru -l en --ignore .venv

compilemessages:
	$(COMPOSE) exec $(EXEC) backend python manage.py compilemessages

collectstatic:
	$(COMPOSE) exec $(EXEC) backend python manage.py collectstatic --no-input

createsuperuser:
	$(COMPOSE) exec $(EXEC) backend python manage.py createsuperuser

# --- Quality ---
test:
	$(COMPOSE) exec $(EXEC) backend pytest

lint:
	$(COMPOSE) exec $(EXEC) backend ruff check .

format:
	$(COMPOSE) exec $(EXEC) backend ruff format .

pre-commit-install:
	pre-commit install

# --- MinIO (provision object storage against the SHARED local MinIO) ---
# Starts the single shared host MinIO if needed, then creates this project's bucket +
# app user + policy. Skips entirely if the project points at external/managed storage.
# Not prefixed with `dev`: it manages a host-level service, independent of the stack.
minio:
	./scripts/ensure_minio.sh

# --- Utilities ---
flush-redis:
	$(COMPOSE) exec redis redis-cli FLUSHALL

# Backup / restore (DB + manifest always; add "media" to also dump S3/MinIO media).
# Examples: make dump | make dump media | make dev dump media
#           make restore dumps/<ts> | make dev restore dumps/<ts>
dump:
	COMPOSE="$(COMPOSE)" EXEC="$(EXEC)" ./scripts/dump_all.sh $(ARGS)

restore:
	COMPOSE="$(COMPOSE)" EXEC="$(EXEC)" ./scripts/restore_all.sh $(ARGS)

# --- Container shells ---
bash:
	$(COMPOSE) exec -it $(EXEC) backend bash

bash-db:
	$(COMPOSE) exec -it db bash

bash-nginx:
	$(COMPOSE) exec -it nginx sh

# Catch extra arguments (e.g. `make logs backend`) so make doesn't error on them.
%:
	@:
