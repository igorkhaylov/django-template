# Django Template

Production-ready Django REST Framework template with PostgreSQL, Redis, Celery, MinIO (S3-compatible storage), and Nginx — fully containerized with Docker Compose.

## Tech Stack

- **Python 3.13** / **Django 5.2** / **DRF**
- **PostgreSQL 17.4** — primary database
- **Redis 8** — Celery broker and cache
- **Celery** — async task queue with beat scheduler
- **MinIO** — S3-compatible object storage for media files
- **Nginx** — reverse proxy and static file serving
- **Poetry 2.1.3** — dependency management
- **Ruff** — linter and formatter
- **pre-commit** — git hooks for code quality

## Project Structure

```
├── backend/
│   ├── apps/
│   │   ├── common/          # Shared models, utilities, validators
│   │   └── users/           # User model and authentication
│   ├── config/
│   │   ├── settings/        # Split settings (base, dev, third_party)
│   │   ├── urls.py
│   │   ├── celery.py
│   │   └── wsgi.py / asgi.py
│   ├── scripts/             # Container entrypoints
│   ├── templates/
│   └── pyproject.toml
├── minio/                   # MinIO init script and access policies
├── nginx/                   # Nginx configs (prod and dev)
├── scripts/                 # Host-level utility scripts
├── .devcontainer/           # VS Code devcontainer config
├── docker-compose.yml       # Production
├── docker-compose.dev.yml   # Development
├── Dockerfile               # Production image
├── Dockerfile.dev           # Development image
└── Makefile
```

## Getting Started

### 1. Clone and configure environment

```bash
cp .env.example .env
# Edit .env — change all CHANGE_ME values
# Generate a secret key: openssl rand -hex 64
```

### 2. Start services

**Production:**
```bash
make up
```

**Development (with devcontainer):**
Open the project in VS Code and use "Reopen in Container". The devcontainer will:
- Start all services via `docker-compose.dev.yml`
- Install pre-commit hooks automatically
- Mount your SSH keys for git operations

**Development (without devcontainer):**
```bash
make dev up
make dev bash          # enter the backend container
pre-commit install     # set up git hooks
python manage.py runserver 0.0.0.0:8000
```

### 3. Create a new app

```bash
cd apps
python ../manage.py startapp my_app
```

Then add `"apps.my_app"` to `INSTALLED_APPS` in `config/settings/base.py`.

## Environment Variables

Copy `.env.example` to `.env` and configure. Key variables:

| Variable | Default | Description |
|---|---|---|
| `ENVIRONMENT` | `prod` | `dev`, `test`, `stage`, or `prod` |
| `DJANGO_SECRET_KEY` | — | **Required.** Generate with `openssl rand -hex 64` |
| `DJANGO_ALLOWED_HOSTS` | `""` | Comma-separated allowed hosts |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | `""` | Comma-separated CSRF trusted origins |
| `DJANGO_CORS_ALLOWED_ORIGINS` | `""` | Comma-separated CORS allowed origins |
| `DJANGO_SUPERUSER_USERNAME` | — | Auto-created superuser username |
| `DJANGO_SUPERUSER_PASSWORD` | — | Auto-created superuser password |
| `POSTGRES_DB` | — | **Required.** Database name |
| `POSTGRES_USER` | — | **Required.** Database user |
| `POSTGRES_PASSWORD` | — | **Required.** Database password |
| `POSTGRES_HOST` | `db` | Database host |
| `POSTGRES_PORT` | `5432` | Database port |
| `GUNICORN_WORKERS` | `4` | Number of Gunicorn workers |

### MinIO Variables

MinIO uses two layers of configuration:

- `MINIO_*` — configure the MinIO container and setup scripts directly
- `DJANGO_MINIO_*` — configure Django's S3 storage backend (read by `python-decouple`)

| Variable | Default | Description |
|---|---|---|
| `MINIO_ENDPOINT` | — | Public MinIO URL (e.g. `http://localhost:9050`) |
| `MINIO_ROOT_USER` | `minioadmin` | MinIO admin user |
| `MINIO_ROOT_PASSWORD` | — | MinIO admin password |
| `MINIO_BUCKET_NAME` | — | Bucket name for media files |
| `MINIO_APP_USER` | — | App-level MinIO user (limited permissions) |
| `MINIO_APP_PASSWORD` | — | App-level MinIO password |
| `DJANGO_MINIO_ENDPOINT` | — | Internal MinIO URL for container-to-container communication (`http://minio:9000`) |
| `DJANGO_MINIO_CUSTOM_URL` | `http://localhost:9000` | Public URL used in generated media file URLs |

## MinIO Setup

MinIO provides S3-compatible object storage for media files.

**In Docker Compose (production):** The `minio-init` service in `docker-compose.yml` runs automatically on `make up`. It creates the bucket, sets up a public-read policy, creates an app-level user with restricted permissions, and applies the access policy.

**Standalone (local development without compose):** Use the helper scripts:

```bash
# Start a standalone MinIO container (creates volume, exposes ports 9000/9001)
./scripts/ensure_minio.sh

# Create bucket, set policies, and create app user (reads credentials from .env)
./scripts/ensure_minio_bucket.sh
```

The bucket is configured with:
- **Public read** — anonymous `GetObject` access (media files are publicly accessible)
- **App user policy** — `ListBucket`, `PutObject`, `GetObject`, `DeleteObject` and multipart upload operations

## Makefile

All commands support a `dev` prefix to target `docker-compose.dev.yml`:

```bash
make up              # production
make dev up          # development
make dev logs backend
```

| Command | Description |
|---|---|
| `make up` | Build and start all containers |
| `make down` | Stop containers |
| `make down-v` | Stop containers and remove volumes |
| `make build` | Build images |
| `make logs [service]` | Tail container logs |
| `make shell` | Django shell |
| `make dbshell` | PostgreSQL shell |
| `make migrate` | Run database migrations |
| `make makemigrations` | Generate migration files |
| `make collectstatic` | Collect static files |
| `make createsuperuser` | Create Django superuser |
| `make test` | Run pytest |
| `make lint` | Run ruff check |
| `make format` | Run ruff format |
| `make pre-commit-install` | Install pre-commit git hooks |
| `make bash` | Shell into backend container |
| `make bash-db` | Shell into database container |
| `make bash-nginx` | Shell into nginx container |
| `make flush-redis` | Flush all Redis data |
| `make dump` | Full backup (database + media) |
| `make restore` | Print restore usage |

## Backup and Restore

**Backup** creates a timestamped directory with a PostgreSQL dump and media archive:

```bash
make dump
# or
./scripts/dump_all.sh
# Output: dumps/<timestamp>/backup.sql + media_backup.tar.gz
```

**Restore** from a backup directory:

```bash
./scripts/restore_all.sh dumps/<timestamp>
```

This will stop services, drop and recreate the database, restore the SQL dump, restore media files, and restart everything.

## Code Quality

**Ruff** is configured in `backend/pyproject.toml` with rules: `E`, `F`, `I`, `UP`, `B` (pycodestyle, pyflakes, isort, pyupgrade, bugbear).

**pre-commit** runs ruff check (with auto-fix) and ruff format on every commit. Hooks are installed automatically in the devcontainer, or manually:

```bash
pre-commit install
```

## Internationalization

The project supports English and Russian (`ru` is the default translation language). Uses `django-modeltranslation` for model field translations and `django-rosetta` for a web-based translation UI.

```bash
# Generate locale files
python manage.py makemessages -l ru -l en --ignore venv

# Compile locale files
python manage.py compilemessages

# Populate translation fields (if model field *_ru doesn't exist yet)
python manage.py update_translation_fields
```

## Adapting This Template

When creating a new project from this template, update:

1. **`docker-compose.yml`** — change the compose project name and nginx port
2. **`.env`** — change all `CHANGE_ME` values, update ports in `MINIO_ENDPOINT` and `DJANGO_CSRF_TRUSTED_ORIGINS`
3. **`.devcontainer/devcontainer.json`** — change the name and forwarded ports

## CI/CD

### GitHub Actions (`.github/workflows/cicd.yml`)

Deploys via Docker Compose on self-hosted runners. Triggered manually with environment selection (`prod`/`dev`). Before deploying, it runs a full backup via `dump_all.sh`.

Requires GitHub secrets: `PROD_ENV` / `DEV_ENV` (full `.env` file contents).

### GitLab CI (`.gitlab-ci.yml`)

Three-stage pipeline: **test** → **build** → **deploy**.

- **test** — runs `docker-compose.test.yml`
- **build** — builds and pushes image to GitLab Container Registry
- **deploy** — SSHes into the target server, pulls the image, and restarts services

Requires CI variables: `DEV_SSH_KEY`, `DEV_HOST`, `DEV_PORT`, `DEV_USER`, `DEV_PATH` (and `PROD_*` equivalents).
