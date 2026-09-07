# Django Template

Production-oriented Django + DRF starter: PostgreSQL, Redis, Celery, MinIO (S3-compatible
storage) and Nginx, fully containerized with Docker Compose and managed with **uv**.

- **New here?** [Prerequisites](#prerequisites) → [Quick start](#quick-start) → [What you get](#what-you-get).
- **Starting a project from it?** Work through [docs/adapting.md](docs/adapting.md) once.
- **Something broke?** [Troubleshooting](#troubleshooting).
- **Going to a server?** [docs/deploy.md](docs/deploy.md).

## Tech Stack

- **Python 3.13** / **Django 5.2** / **Django REST Framework**
- **PostgreSQL 17.4** — primary database
- **Redis 8** — Celery broker + Django cache
- **Celery** (+ beat) — async tasks
- **MinIO** — S3-compatible object storage for **static and media** files
- **Nginx** — in-stack reverse proxy to Gunicorn
- **uv** — dependency management & virtualenvs
- **Ruff** — lint + format · **pre-commit** — git hooks
- **structlog** (django-structlog) — structured logging to stdout

## Project Structure

```
├── backend/
│   ├── apps/
│   │   ├── common/          # Shared abstract models, utils, validators, mgmt commands
│   │   └── users/           # Custom User + UserEmail, auth manager, initial migration
│   ├── config/
│   │   ├── settings/        # base.py, third_party.py, dev.py, test.py (ENVIRONMENT selects)
│   │   ├── urls.py · celery.py · wsgi.py · asgi.py
│   ├── scripts/entrypoint.sh# Container boot: compilemessages → migrate → wait_for_storage
│   │                        # → collectstatic → createsuperuserauto → gunicorn
│   ├── tests/               # pytest suite (minimal config, no external services)
│   ├── pyproject.toml · uv.lock (committed)
├── docs/                    # adapting.md · deploy.md · backup.md · uv.md · stdimage.md
├── minio/policies/          # bucket/user policies applied by scripts/ensure_minio.sh
├── nginx/                   # nginx.conf (prod) / nginx.dev.conf
├── scripts/                 # init_env.sh · ensure_minio.sh · dump_all.sh · restore_all.sh
├── .vscode/                 # shared editor config (spell-check words only)
├── docker-compose.yml       # Local production-like (builds from source, gunicorn)
├── docker-compose.dev.yml   # Development (repo bind-mounted, backend idles)
├── docker-compose.prod.yml  # Production deploy (pulls the registry image)
├── docker-compose.test.yml  # Test runner (standalone, what CI runs)
├── Dockerfile / Dockerfile.dev
└── Makefile                 # `make help`
```

## Prerequisites

| Tool | Needed for | Notes |
|---|---|---|
| **Docker** with the Compose plugin (`docker compose`) | everything | Docker Desktop on macOS/Windows; Docker Engine ≥ 20.10 on Linux (`host.docker.internal` is mapped via `extra_hosts`) |
| **make** | all commands | preinstalled on macOS/Linux |
| **openssl** | `make init` generates secrets | preinstalled on macOS/Linux |
| **uv** (optional) | host virtualenv for the editor, running tests without Docker | `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| **ruff** + **pre-commit** on `PATH` (optional) | the git hooks | `uv tool install ruff pre-commit` (or `brew install ruff pre-commit`) |

Free host ports: `8050` (app, `APP_PORT`), `9000`/`9001` (shared MinIO API/console).

## Quick start

```bash
git clone <this repo> myproject && cd myproject
make init                   # ~3-5 min the first time (image build)
make dev createsuperuser    # your admin account
make dev run                # dev server (autoreload) → http://localhost:8050/en/admin/
```

`make init` is one idempotent command that does, in order:

1. `scripts/init_env.sh` — creates `.env` from `.env.example` with every `CHANGE_ME`
   replaced by a generated secret. **Never overwrites an existing `.env`.**
2. `scripts/ensure_minio.sh` — starts the single **shared** host MinIO container if it is
   not running and creates this project's bucket, public-read policy and app user.
3. `docker compose -f docker-compose.dev.yml up -d --build` — Postgres, Redis, nginx and
   an **idle** backend container (`sleep infinity`).
4. `migrate` — applies the shipped migrations (`users/migrations/0001_initial.py`).
5. `collectstatic` — uploads static files to the bucket. Static is served from S3/MinIO
   even in dev, so this is what makes the admin render with CSS.

Then `make dev run` starts `runserver` inside that container in the foreground; Ctrl-C
stops the server, the stack keeps running. Steps 1–5 can also be run separately — see
[First-time setup in detail](#first-time-setup-in-detail).

## What you get

Nothing is mounted at `/` — opening `http://localhost:8050/` gives a **404 by design**.
The routes that exist out of the box:

| URL | What | Notes |
|---|---|---|
| `/healthcheck/` | `{"status": "ok"}` | used by the container healthcheck; exempt from the HTTPS redirect |
| `/en/admin/`, `/ru/admin/` | Django admin | language-prefixed (`i18n_patterns`); `/admin/` alone 404s |
| `/rosetta/` | translation UI | superusers and the "Rosetta Users" group |
| `/__debug__/` | debug toolbar | `ENVIRONMENT=dev` only |
| `http://localhost:9001` | MinIO console | `minioadmin` / `minioadmin` (shared local MinIO) |

DRF, drf-spectacular and django-filter are installed and configured, but **no API routes
or schema views are mounted yet** — add `SpectacularAPIView`/`SpectacularSwaggerView` to
`config/urls.py` together with your first endpoint (a dark Swagger theme is already in
`backend/templates/drf_spectacular/`). Note that `REST_FRAMEWORK` sets **no default
permission class**: the first endpoint you add is world-open until you set
`IsAuthenticated` and an authentication class.

### Everyday commands

```bash
make help                   # the full list
make dev up / down / down-v # start / stop / stop and DROP volumes (database!)
make dev run                # dev server (foreground)
make dev bash               # shell in the backend container (repo mounted at /app)
make dev shell              # Django shell
make dev test               # pytest inside the container
make dev lint / format      # ruff
make dev makemigrations / migrate / createsuperuser / collectstatic
make dev makemessages / compilemessages
make dev logs backend       # tail a service
make dev dbshell            # psql
make flush-cache            # Redis db 1 (Django cache) — safe
make flush-redis            # EVERYTHING incl. queued Celery tasks — deliberate use only
make minio                  # (re)provision this project's bucket on the shared MinIO
make dump [media] / make restore dumps/<ts>   # see docs/backup.md
```

`make dev <target>` runs against `docker-compose.dev.yml`; the same target without a
prefix targets `docker-compose.yml` (local production-like), `make prod <target>` targets
the pull-only production compose. A typo in the target name fails loudly
(`Unknown target`) instead of being swallowed.

## Editor setup

The containers have every dependency installed, but your editor does not see inside
them. Create a host virtualenv once, purely for autocomplete, ruff and pyright:

```bash
cd backend && uv sync       # → backend/.venv (runtime + dev group)
```

- **Interpreter:** point the editor at `backend/.venv/bin/python`. Open the repo root as
  the workspace; `backend/pyrightconfig.json` and `[tool.ruff]` in
  `backend/pyproject.toml` are picked up from there.
- **Ruff:** use the editor's ruff extension/LSP with the config above. Rules and line
  length live in `pyproject.toml`; migrations are excluded.
- **`.vscode/settings.json`** is shared and holds only the spell-check dictionary. There
  is no host-side launch configuration on purpose: the server runs inside the container
  (`make dev run`), and `db`/`redis` ports are not published to the host.
- **Git hooks:** `pre-commit install` (or `make pre-commit-install`). The hooks call
  `ruff` from your `PATH` (`language: system`), so install ruff on the host first.

## Deployment topology (read this first)

This app **always runs behind an external reverse proxy** (the edge). That edge:

- terminates **TLS** and holds the certificates, and
- sets `X-Forwarded-Proto` (and the real client IP in `X-Forwarded-For`).

Django trusts `X-Forwarded-Proto` via `SECURE_PROXY_SSL_HEADER`, so proxied HTTPS
requests are correctly treated as secure. **The in-stack `nginx` must NOT re-set
`X-Forwarded-Proto`** — that line is intentionally left commented in
[`nginx/nginx.conf`](nginx/nginx.conf); re-setting it would overwrite the edge proxy's
value and create a redirect loop under `SECURE_SSL_REDIRECT`.

> **Client-IP trust requirement.** `common.request.get_ip_from_request` uses the **first**
> `X-Forwarded-For` entry. This is only safe if the **edge proxy sets the real client IP as
> the first hop and rejects any client-supplied `X-Forwarded-For`** (otherwise a client can
> spoof its IP). Downstream proxies must only *append* to the header, never reorder. If you
> run this without such an edge proxy, do not trust `X-Forwarded-For`.

Static and media are served by **S3/MinIO**, not by Nginx.

## First-time setup in detail

### 1. Configure environment

```bash
cp .env.example .env        # `make init` does this for you, generating every CHANGE_ME
```

`ENVIRONMENT` must be one of `dev | test | stage | prod` (validated at startup —
`production` or any other value raises instead of silently running insecurely). `DEBUG`
and every security flag are derived from it. In stage/prod `DJANGO_SECRET_KEY` must be
an explicit value of at least 50 characters (`openssl rand -hex 64`).

### 2. Apply migrations

The initial migration for the default `User`/`UserEmail` models **ships with the
template** (`backend/apps/users/migrations/0001_initial.py`), so a fresh clone migrates
and boots out of the box:

```bash
make dev up                 # start the dev stack
make dev migrate            # apply migrations (`make init` does this for you)
```

Adjusting the user models? Edit them and `make dev makemigrations` as usual — the test
`test_migrations_in_sync` fails the suite if models and migrations ever drift. To start
your project from a single clean initial migration instead, delete `0001_initial.py`,
regenerate it, and reset the dev database (`make dev down-v`) — before your first
release, not after.

> **`User.is_active` defaults to `False`.** Only superusers are active out of the box, so
> a newly created regular user **cannot log in** until something sets `is_active=True`
> (the intended trigger is OTP/email verification — a documented `TODO` in
> [`users/models.py`](backend/apps/users/models.py)). Decide your activation flow before
> shipping user signup.

### 3. Provision object storage (one-off; `make init` runs this)

Object storage is **not** part of the compose stack. Locally it's a single **shared**
MinIO container on your host, reused by every project (no per-project MinIO):

```bash
make minio          # ./scripts/ensure_minio.sh
```

This script:
- starts the shared MinIO container (`minio`) if it isn't already running — otherwise
  reuses the existing one, so all your projects share one MinIO;
- creates **this project's** bucket, public-read policy and restricted app user;
- **does nothing** if the project is configured for external/managed storage (i.e. you
  changed `MINIO_ROOT_USER`/`MINIO_ROOT_PASSWORD` away from the `minioadmin` defaults) —
  in that case provision the bucket on your provider instead.

Admin credentials default to `minioadmin` / `minioadmin`.

#### Endpoint vs. public URL

Storage has **two** addresses, and mixing them up is the classic source of "uploads work
but images 404":

| Variable | Used by | Purpose | Example |
|---|---|---|---|
| `DJANGO_MINIO_ENDPOINT` | the backend, server-side | S3 API — uploads, `collectstatic`, dumps | `http://host.docker.internal:9000` |
| `DJANGO_MINIO_CUSTOM_URL` | the browser | prefix of every media/static link | `http://localhost:9000` |

`DJANGO_MINIO_CUSTOM_URL` is **scheme + host + port only** — the bucket path is appended
for you from `DJANGO_MINIO_BUCKET_NAME`, so the link and the bucket can never drift apart:

```
DJANGO_MINIO_CUSTOM_URL=http://localhost:9000
DJANGO_MINIO_BUCKET_NAME=my-bucket
        →  http://localhost:9000/my-bucket/media/photo.jpg
        →  http://localhost:9000/my-bucket/static/css/app.css
```

In production this is the **public** address of your storage, which is usually *not* the
same host as `DJANGO_MINIO_ENDPOINT` (that one may be private/internal). The bucket stays
in the public path, so an edge proxy or CDN in front of MinIO must pass it through
unchanged — a plain pass-through matches, since the backend addresses MinIO path-style
(`/<bucket>/<key>`) anyway.

### 4. Run the dev server

`make dev up` brings the stack online, but the backend container just **idles**
(`sleep infinity`) so you can run migrations/shell/tests against a live DB. Start the
Django dev server (autoreload) explicitly:

```bash
make dev run                # runserver on 0.0.0.0:8000 → open http://localhost:$APP_PORT
```

(There is no need to `make dev run` for `make up` / prod — those serve via Gunicorn from
the entrypoint, which also creates the first admin from `DJANGO_SUPERUSER_*` in `.env`.)

## Production

Production uses a **registry image, not a server-side build**: CI builds the backend
image and pushes it to a container registry; the server only **pulls** it.

```bash
# On the server (needs: docker-compose.prod.yml + ./.env + ./nginx/nginx.conf):
make prod deploy   # = docker compose -f docker-compose.prod.yml pull && up -d
```

> **Before any manual `make prod deploy`** the server must be logged in to the registry —
> GHCR packages are private by default, so an anonymous `pull` fails:
>
> ```bash
> echo "$GHCR_PAT" | docker login ghcr.io -u <github-username> --password-stdin
> ```
>
> `GHCR_PAT` is a **classic** Personal Access Token with the `read:packages` scope only.
> How to create it — and the full zero-to-first-deploy server runbook — is in
> [docs/deploy.md](docs/deploy.md).

`docker-compose.prod.yml` runs `image: ${BACKEND_IMAGE}` (no `build:`). Set `BACKEND_IMAGE`
in `.env` — pin a reproducible build by sha, e.g.
`ghcr.io/<owner>/<repo>:sha-<full-sha>` (a moving `:latest` also works but drifts on the
next push).

For a purely local production-like run that builds from source, `make up` still works
(uses `docker-compose.yml`).

Point `DJANGO_MINIO_*` at your managed MinIO / S3 (the `make minio` shared-local helper
is for development) — note that `DJANGO_MINIO_CUSTOM_URL` is the **public** base URL of
that storage, not the API endpoint (see [Endpoint vs. public URL](#endpoint-vs-public-url)).
Behind your edge reverse proxy, point it at the `nginx` service (host port `APP_PORT`,
default 8050).

## Dependency management (uv)

Dependencies live in `backend/pyproject.toml`; the lockfile `backend/uv.lock` is
**committed** and the Docker images install from it with `uv sync --frozen`. Every
dependency change therefore goes through uv and ships with the updated lock:

```bash
cd backend
uv add <package>            # add a runtime dependency (updates pyproject + uv.lock)
uv add --dev <package>      # add a dev dependency
uv lock --upgrade-package django   # bump one package
make dev build              # rebuild the dev image so the container gets it
```

Editing `pyproject.toml` by hand without re-locking makes the next image build fail with
"lockfile is out of date". Full reference: [docs/uv.md](docs/uv.md).

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `ENVIRONMENT` | `prod` | `dev` / `test` / `stage` / `prod` (validated) |
| `PROJECT_NAME` | `django-template` | Compose project name; dev/test append `-dev`/`-test` |
| `APP_PORT` | `8050` | Host port for the in-stack nginx |
| `DJANGO_SECRET_KEY` | dev-only default | **Required, ≥50 chars in stage/prod** |
| `DJANGO_ALLOWED_HOSTS` | `""` | Comma-separated; `localhost` is appended automatically (container healthcheck) |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | `""` | Comma-separated, with scheme |
| `DJANGO_CORS_ALLOWED_ORIGINS` | `""` | Comma-separated, with scheme |
| `DJANGO_SUPERUSER_USERNAME` / `_PASSWORD` | `admin` / — | First admin, created by the entrypoint; placeholder ⇒ skipped in dev, boot failure in stage/prod |
| `DJANGO_LOG_LEVEL` | `INFO` | `DEBUG`/`INFO`/`WARNING`/`ERROR` |
| `GUNICORN_WORKERS` | `4` | Gunicorn worker count |
| `GUNICORN_TIMEOUT` | `60` | Worker request timeout (s) |
| `POSTGRES_*` | see `.env.example` | Database connection; `POSTGRES_CONN_MAX_AGE` 600 (set 0 behind pgbouncer) |
| `MINIO_ROOT_USER` / `MINIO_ROOT_PASSWORD` | `minioadmin` | Shared local MinIO admin; non-default ⇒ external storage, `make minio` skips |
| `MINIO_BUCKET_NAME` / `MINIO_APP_USER` / `MINIO_APP_PASSWORD` | — | This project's bucket/user, created by `make minio` |
| `DJANGO_MINIO_ENDPOINT` | `http://host.docker.internal:9000` | Server-side S3 API endpoint (shared host MinIO, or your S3) |
| `DJANGO_MINIO_CUSTOM_URL` | `http://localhost:9000` | Browser-facing base URL (scheme + host); the bucket is appended automatically — [details](#endpoint-vs-public-url) |
| `BACKEND_IMAGE` | `ghcr.io/…:latest` | Image pulled by `docker-compose.prod.yml` |
| `COMPOSE_PROFILES` | unset | `backup` enables the prod DB-backup sidecar ([docs/backup.md](docs/backup.md)) |

All `DJANGO_MINIO_*` values have safe defaults so management commands, tests and CI can
import settings without a full MinIO environment. `${VAR}` references inside `.env` are
expanded by Docker Compose (`env_file`), not by Django — they work in the containers, not
for a host-run `manage.py`.

## Logging

Structured logging via `django-structlog` goes to the **container's stdout** (no files).
Dev (`ENVIRONMENT=dev`) uses a colorized console renderer; stage/prod emit one JSON object
per line. The level is controlled by `DJANGO_LOG_LEVEL`. Every line carries a `request_id`
and `user_id` (via `RequestMiddleware`). Docker's json-file logs are capped (10 MB × 5 per
service) in the dev/local/prod compose files.

## Testing

The suite runs in a **minimal configuration** (`config.settings.test`): sqlite in-memory,
locmem cache/email, eager Celery, in-memory storage — **no Postgres/Redis/MinIO required**.
pytest is configured with `--no-migrations` (the schema is built from the models);
`test_migrations_in_sync` separately asserts that `makemigrations --check` is clean.

```bash
make dev test                          # inside the dev container
cd backend && uv run pytest            # on the host (after `uv sync`)
docker compose -f docker-compose.test.yml up --build --exit-code-from backend   # what CI runs
```

Selecting the test settings **forces `ENVIRONMENT=test`**, so the suite behaves
identically on the host, in the dev container (whose `.env` exports `ENVIRONMENT=dev`) and
in CI.

## Code Quality

Ruff is configured in `backend/pyproject.toml` with `E, F, I, UP, B, C4, SIM, DJ, RUF`
(line length 120, migrations excluded). pre-commit runs `ruff check` (no auto-fix) and
`ruff format` on every commit; the hooks use the `ruff` binary on your `PATH`:

```bash
uv tool install ruff pre-commit   # once, on the host
pre-commit install
```

## Internationalization

English (`en`, default) and Russian (`ru`) via `django-modeltranslation`; `django-rosetta`
provides a web translation UI at `/rosetta/`. Admin URLs are language-prefixed.

```bash
make dev makemessages       # extract strings (-l ru -l en)
make dev compilemessages    # compile .mo files (the prod entrypoint does this on boot)
```

## Object storage (django-stdimage)

`User.picture` uses `StdImageField` from a maintained fork that ships default image
variations. See [docs/stdimage.md](docs/stdimage.md) for how to declare and use variations.

## Backup & Restore

A backup is a timestamped directory under `dumps/` with a gzipped `pg_dump`, a
`manifest.json`, and — optionally — a tarball of all S3/MinIO media.

```bash
make dump                  # database + manifest only
make dump media            # database + all S3/MinIO media (slower; downloads the bucket)
make dev dump media        # same, dev stack

make restore dumps/<ts>    # restore DB + media, and rewrite embedded media URLs
make dev restore dumps/<ts>
```

Media lives in object storage, so it is dumped/loaded **through the app**
(`media_dump` / `media_load` management commands), not from a local directory. A restore
into a **different** S3/MinIO rewrites the absolute media URLs embedded in HTML/text
fields. Scheduled production DB backups are an opt-in compose profile. See
[docs/backup.md](docs/backup.md) for the full design.

## Troubleshooting

| Symptom | Cause → fix |
|---|---|
| `http://localhost:8050/` is a 404 | Expected: nothing is mounted at `/`. Use `/en/admin/` or `/healthcheck/` ([What you get](#what-you-get)). |
| Admin loads without CSS | Static is served from the bucket; run `make dev collectstatic` (`make init` does it; repeat after adding static files or upgrading Django). |
| Images/static 404 while uploads succeed | `DJANGO_MINIO_CUSTOM_URL` wrong or containing the bucket path — [Endpoint vs. public URL](#endpoint-vs-public-url). |
| `make minio` hangs, then "MinIO did not respond" | Docker Desktop lost the container's port publishing after sleep/restart. `docker port minio` shows nothing → `docker rm -f minio && make minio` (the data volume is kept). |
| `wait_for_storage`: bucket does not exist | `make minio` for the shared local MinIO, or create the bucket on your provider. The boot fails on purpose instead of crashing in `collectstatic`. |
| `ImproperlyConfigured: ENVIRONMENT must be one of …` | `.env` has `production`, `local`, … — only `dev / test / stage / prod` are accepted. |
| `DJANGO_SECRET_KEY must be a strong, explicit value` | stage/prod with the dev default or < 50 chars → `openssl rand -hex 64`. |
| Backend "unhealthy", nginx never starts (prod) | Read `docker compose logs backend`: missing bucket, placeholder `DJANGO_SUPERUSER_PASSWORD`, weak secret, or Postgres not ready. `localhost` is auto-allowed for the healthcheck, so `DJANGO_ALLOWED_HOSTS` is not the cause. |
| Redirect loop in stage/prod | The edge proxy is not sending `X-Forwarded-Proto: https`, or the in-stack nginx re-sets it — [Deployment topology](#deployment-topology-read-this-first). |
| `createsuperuserauto`: "Skipped: … placeholder" | In dev this is informational; create your admin with `make dev createsuperuser`. In stage/prod it is a hard error — set a real password. |
| New user cannot log in | `User.is_active` defaults to `False` — see [step 2](#2-apply-migrations). |
| Files created by `make dev makemigrations` are owned by root (Linux) | The dev container runs as root and the repo is bind-mounted. `sudo chown -R "$USER" backend/` (macOS Docker Desktop maps ownership automatically). |
| `uv sync --frozen` fails in the image build | `pyproject.toml` changed without re-locking — `cd backend && uv lock`, commit `uv.lock`. |
| `make dev up` says the port is already allocated | Another stack uses `8050` (or `9000`/`9001`) — change `APP_PORT` / `MINIO_PORT` in `.env`. Two clones with the same `PROJECT_NAME` also share volumes and containers. |
| `pre-commit` fails with `ruff: command not found` | Hooks use the host `ruff` — `uv tool install ruff` (or `brew install ruff`). |
| `host.docker.internal` unreachable on Linux | Needs Docker ≥ 20.10; the compose files map it via `extra_hosts: host-gateway`. Check that the shared MinIO publishes `MINIO_PORT` on the host. |

## Adapting this template

Every project-specific name and default (compose project name, bucket, database, registry
image, time zone, CI runner tags, …) is listed with its consequences in
**[docs/adapting.md](docs/adapting.md)**. Go through it once before your first commit.

## CI/CD

Both platforms follow the same model: **build & push the backend image to a registry,
then deploy by pulling it** (the server never builds). Step-by-step server setup and
first deploy: [docs/deploy.md](docs/deploy.md).

**GitHub Actions**
- `.github/workflows/build-push.yml` — on push to `master` and on `v*` tags (or manual):
  runs the test suite (`docker-compose.test.yml`), then builds `./Dockerfile` and pushes
  to **GHCR** (`ghcr.io/<owner>/<repo>`) with tags `latest` (default branch),
  `sha-<full-sha>` (every build), and `vX.Y.Z`/`X.Y.Z` (tags). Uses Buildx + GitHub
  Actions cache. No secrets needed beyond the built-in `GITHUB_TOKEN`.
- `.github/workflows/deploy.yml` — after a successful build on `master`, deploys the exact
  `sha-<full-sha>` just built **only if the repo variable `AUTO_DEPLOY` is `true`** (opt-in:
  unset on the bare template, so the auto path is *skipped*, not failed). Manual
  `workflow_dispatch` with a chosen tag always works. A GitHub-hosted runner **SSHes into
  the server**; the server logs in to GHCR, runs `git reset --hard` to the deployed commit
  (syncs compose + `nginx/nginx.conf`), then `docker compose -f docker-compose.prod.yml
  pull && up -d`. Uses GitHub **Environments** (`prod`/`dev`). Required secrets per
  environment: `SSH_HOST` / `SSH_USER` / `SSH_PORT` / `SSH_KEY` / `SSH_FINGERPRINT` /
  `DEPLOY_PATH` / `GHCR_USER` / `GHCR_PAT` (PAT with `read:packages` only). The server
  keeps its own `./.env` (provisioned out-of-band; CI never touches it — an opt-in snippet
  to let CI write it is in the workflow).

**GitLab CI** (`.gitlab-ci.yml`) — `test → build → deploy`:
- **test** runs `docker-compose.test.yml` (the gate).
- **build** pushes to the GitLab Container Registry with the same tag set
  (`sha-<sha>`, `latest` on the default branch, `vX.Y.Z`/`X.Y.Z` on tags).
- **deploy-dev**/**deploy-prod** SSH to the server and pull the pinned `sha-<sha>` image
  via `docker-compose.prod.yml`. The server authenticates with a **Deploy Token**
  (`CI_DEPLOY_USER`/`CI_DEPLOY_PASSWORD`, scope `read_registry`) so restarts/`pull_policy:
  always` keep working. Required CI vars: `DEV_SSH_KEY`/`DEV_HOST`/`DEV_PORT`/`DEV_USER`/
  `DEV_PATH` (+ `PROD_*`). Jobs run on runners tagged `default`.

A `git tag vX.Y.Z` push runs test → build and pushes the semver image (no auto-deploy).

> Keep only the platform you use; both are provided as a starting point.
