# If "dev" is passed, use dev compose file
# Usage: make up / make dev up / make dev logs backend
ifneq ($(filter dev,$(MAKECMDGOALS)),)
  COMPOSE := docker compose -f docker-compose.dev.yml
else
  COMPOSE := docker compose
endif

# Extra args: MAKECMDGOALS minus "dev" — target name ($@) is filtered in recipes
ARGS = $(filter-out dev $@,$(MAKECMDGOALS))

.PHONY: dev up down down-v build logs shell dbshell migrate makemigrations test lint format flush-redis dump restore bash bash-db bash-nginx collectstatic createsuperuser

dev:
	@:

# Docker
up:
	$(COMPOSE) up -d --build

down:
	$(COMPOSE) down

down-v:
	$(COMPOSE) down -v

build:
	$(COMPOSE) build

logs:
	$(COMPOSE) logs -f $(ARGS)

# Django commands
shell:
	$(COMPOSE) exec backend python manage.py shell

dbshell:
	$(COMPOSE) exec db psql -U $${POSTGRES_USER:-django_template_user} -d $${POSTGRES_DB:-django_template}

migrate:
	$(COMPOSE) exec backend python manage.py migrate

makemigrations:
	$(COMPOSE) exec backend python manage.py makemigrations

collectstatic:
	$(COMPOSE) exec backend python manage.py collectstatic --no-input

createsuperuser:
	$(COMPOSE) exec backend python manage.py createsuperuser

# Quality
test:
	$(COMPOSE) exec backend pytest

lint:
	$(COMPOSE) exec backend ruff check .

format:
	$(COMPOSE) exec backend ruff format .

# Connect to containers
bash:
	$(COMPOSE) exec -it backend bash

bash-db:
	$(COMPOSE) exec -it db bash

bash-nginx:
	$(COMPOSE) exec -it nginx sh

# Utilities
flush-redis:
	$(COMPOSE) exec redis redis-cli FLUSHALL

dump:
	./scripts/dump_all.sh

restore:
	@echo "Usage: ./scripts/restore_all.sh <dump-directory>"

# Catch extra arguments passed to targets (e.g. make logs backend)
%:
	@:
