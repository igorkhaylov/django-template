# Django Template

Production-oriented Django + DRF starter: PostgreSQL, Redis, Celery, MinIO (S3-compatible
storage) and Nginx, fully containerized with Docker Compose and managed with **uv**.

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
│   │   ├── common/          # Shared abstract models, utils, validators
│   │   └── users/           # Custom User + UserEmail, auth manager
│   ├── config/
│   │   ├── settings/        # base.py, third_party.py, dev.py, test.py
│   │   ├── urls.py · celery.py · wsgi.py · asgi.py
│   ├── scripts/             # Container entrypoints
│   ├── tests/               # pytest suite (minimal-config, no external services)
│   └── pyproject.toml
├── docs/                    # uv.md, stdimage.md
├── minio/                   # MinIO access policies (used by scripts/ensure_minio.sh)
├── nginx/                   # nginx.conf (prod) / nginx.dev.conf
├── scripts/                 # Host-level helpers: ensure_minio.sh, dump/restore
├── docker-compose.yml       # Local production-like (builds from source)
├── docker-compose.dev.yml   # Development (repo bind-mounted)
├── docker-compose.prod.yml  # Production deploy (pulls the registry image)
├── docker-compose.test.yml  # Test runner
├── Dockerfile / Dockerfile.dev
└── Makefile
```

## Deployment topology (read this first)

This app **always runs behind an external reverse proxy** (the edge). That edge:

- terminates **TLS** and holds the certificates, and
- sets `X-Forwarded-Proto` (and the real client IP in `X-Forwarded-For`).

Django trusts `X-Forwarded-Proto` via `SECURE_PROXY_SSL_HEADER`, so proxied HTTPS
requests are correctly treated as secure. **The in-stack `nginx` must NOT re-set
`X-Forwarded-Proto`** — that line is intentionally left commented in
[`nginx/nginx.conf`](nginx/nginx.conf); re-setting it would overwrite the edge proxy's
value.

> **Client-IP trust requirement.** `common.request.get_ip_from_request` uses the **first**
> `X-Forwarded-For` entry. This is only safe if the **edge proxy sets the real client IP as
> the first hop and rejects any client-supplied `X-Forwarded-For`** (otherwise a client can
> spoof its IP). Downstream proxies must only *append* to the header, never reorder. If you
> run this without such an edge proxy, do not trust `X-Forwarded-For`.

Static and media are served by **S3/MinIO**, not by Nginx.

## First-time setup

### 1. Configure environment

```bash
cp .env.example .env
# Edit .env — change every CHANGE_ME. In stage/prod, DJANGO_SECRET_KEY must be a
# strong, explicit value (>= 50 chars): openssl rand -hex 64
```

`ENVIRONMENT` must be one of `dev | test | stage | prod` (validated at startup —
an unrecognized value raises instead of silently running insecurely). `DEBUG` and all
security flags are derived from it.

### 2. Create the initial migrations (important)

This template **ships without user migrations on purpose**. The default `User`/`UserEmail`
models are a starting point — adjust them to your project *first*, then generate the
initial migration so you don't accumulate throwaway migrations later.

```bash
make dev up                 # start the dev stack
make dev makemigrations     # generate migrations for your (adjusted) models
make dev migrate            # apply them
```

> If you skip this, `migrate` has nothing to create and the app can't store users.

> **`User.is_active` defaults to `False`.** Only superusers are active out of the box, so
> a newly created regular user **cannot log in** until something sets `is_active=True`
> (the intended trigger is OTP/email verification — a documented `TODO` in
> [`users/models.py`](backend/apps/users/models.py)). Create your admin with
> `make dev createsuperuser`; decide your activation flow before shipping user signup.

### 3. Provision object storage (manual, one-off)

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

The backend reaches it via `DJANGO_MINIO_ENDPOINT` (default
`http://host.docker.internal:9000` — the host-published shared MinIO). Admin
credentials default to `minioadmin` / `minioadmin`.

### 4. Run the dev server

`make dev up` brings the stack online, but the backend container just **idles**
(`sleep infinity`) so you can run migrations/shell/tests against a live DB. Start the
Django dev server (autoreload) explicitly:

```bash
make dev run                # runserver on 0.0.0.0:8000 → open http://localhost:$APP_PORT
```

`make dev run` runs in the foreground; Ctrl-C stops the server while the rest of the stack
keeps running. (There is no need to `make dev run` for `make up` / prod — those serve via
Gunicorn from the entrypoint.)

Other everyday commands:

```bash
make dev bash               # shell into the backend container
make dev test               # run the test suite
make dev logs backend       # tail logs
```

## Production

Production uses a **registry image, not a server-side build**: CI builds the backend
image and pushes it to a container registry; the server only **pulls** it.

```bash
# On the server (needs: docker-compose.prod.yml + ./.env + ./nginx/nginx.conf):
make prod deploy   # = docker compose -f docker-compose.prod.yml pull && up -d
```

`docker-compose.prod.yml` runs `image: ${BACKEND_IMAGE}` (no `build:`). Set `BACKEND_IMAGE`
in `.env` — pin a reproducible build by sha, e.g.
`ghcr.io/igorkhaylov/django-template:sha-<full-sha>` (a moving `:latest` also works but
drifts on the next push).

For a purely local production-like run that builds from source, `make up` still works
(uses `docker-compose.yml`).

Point `DJANGO_MINIO_*` at your managed MinIO / S3 (the `make minio` shared-local helper
is for development). Behind your edge reverse proxy, point it at the `nginx` service
(host port `APP_PORT`, default 8050).

## Dependency management (uv)

Dependencies live in `backend/pyproject.toml`; the lockfile is `backend/uv.lock`.
See [docs/uv.md](docs/uv.md) for the full command reference. Quick version:

```bash
cd backend
uv lock                     # generate/refresh uv.lock  (REQUIRED before first build)
uv sync                     # install into .venv (incl. dev group)
uv add <package>            # add a runtime dependency
uv add --dev <package>      # add a dev dependency
```

> The Docker images install from `uv.lock` with `uv sync --frozen`, so you must commit a
> lockfile. Generate it once with `cd backend && uv lock`.

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `ENVIRONMENT` | `prod` | `dev` / `test` / `stage` / `prod` (validated) |
| `PROJECT_NAME` | `django-template` | Compose project name; dev/test append `-dev`/`-test` |
| `APP_PORT` | `8050` | Host port for the in-stack nginx |
| `DJANGO_SECRET_KEY` | dev-only default | **Required, ≥50 chars in stage/prod** |
| `DJANGO_ALLOWED_HOSTS` | `""` | Comma-separated |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | `""` | Comma-separated |
| `DJANGO_CORS_ALLOWED_ORIGINS` | `""` | Comma-separated |
| `DJANGO_LOG_LEVEL` | `INFO` | `DEBUG`/`INFO`/`WARNING`/`ERROR` |
| `GUNICORN_WORKERS` | `4` | Gunicorn worker count |
| `GUNICORN_TIMEOUT` | `60` | Worker request timeout (s) |
| `POSTGRES_*` | see `.env.example` | Database connection |
| `MINIO_ROOT_USER` / `MINIO_ROOT_PASSWORD` | `minioadmin` | Shared local MinIO admin; non-default ⇒ external storage, `make minio` skips |
| `MINIO_BUCKET_NAME` / `MINIO_APP_USER` / `MINIO_APP_PASSWORD` | — | This project's bucket/user, created by `make minio` |
| `DJANGO_MINIO_ENDPOINT` | `http://host.docker.internal:9000` | Endpoint the backend uses (shared host MinIO, or your S3) |
| `DJANGO_MINIO_CUSTOM_URL` | `http://localhost:9000` | Public base URL for media/static |

All `DJANGO_MINIO_*` values have safe defaults so management commands, tests and CI can
import settings without a full MinIO environment.

## Logging

Structured logging via `django-structlog` goes to the **container's stdout** (no files).
Dev (`ENVIRONMENT=dev`) uses a colorized console renderer; stage/prod emit one JSON object
per line. The level is controlled by `DJANGO_LOG_LEVEL`. Every line carries a `request_id`
and `user_id` (via `RequestMiddleware`).

## Testing

The suite runs in a **minimal configuration** (`config.settings.test`): sqlite in-memory,
locmem cache/email, eager Celery, in-memory storage — **no Postgres/Redis/MinIO required**.
pytest is configured with `--no-migrations`, so it works even before you create your
initial migrations.

```bash
make dev test               # in the dev container
# or, with deps installed on the host:
cd backend && uv run pytest
```

## Code Quality

Ruff is configured in `backend/pyproject.toml` with `E, F, I, UP, B, C4, SIM, DJ, RUF`.
pre-commit runs ruff (check, no auto-fix) and ruff format on every commit:

```bash
pre-commit install
```

## Internationalization

English (`en`, default) and Russian (`ru`) via `django-modeltranslation`; `django-rosetta`
provides a web translation UI.

```bash
make dev makemessages       # extract strings
make dev compilemessages    # compile .mo files
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

| File | Contents |
|------|----------|
| `database.sql.gz` | full `pg_dump --clean --if-exists` |
| `manifest.json`   | `media_base_url`, object count, total bytes |
| `media.tar.gz`    | every S3/MinIO object except `static/` (only with the `media` arg) |

Media lives in object storage, so it is dumped/loaded **through the app**
(`media_dump` / `media_load` management commands), not from a local directory. A
restore into a **different** S3/MinIO works: it rewrites the absolute media URLs
embedded in HTML/text fields from the backup's `media_base_url` to the current one.
See [docs/backup.md](docs/backup.md) for the full design.

## Adapting this template

1. **Adjust the `users` models** to your needs, then create the initial migration (step 2 above).
2. `docker-compose.yml` / `.env` — set the compose name, ports and all `CHANGE_ME` values.
3. Point your edge reverse proxy at the `nginx` service.

## CI/CD

Both platforms follow the same model: **build & push the backend image to a registry,
then deploy by pulling it** (the server never builds).

**GitHub Actions**
- `.github/workflows/build-push.yml` — on push to `master` and on `v*` tags (or manual):
  builds `./Dockerfile` and pushes to **GHCR** (`ghcr.io/<owner>/<repo>`) with tags
  `latest` (default branch), `sha-<full-sha>` (every build), and `vX.Y.Z`/`X.Y.Z` (tags).
  Uses Buildx + GitHub Actions cache. No secrets needed beyond the built-in `GITHUB_TOKEN`
  (job has `packages: write`).
- `.github/workflows/deploy.yml` — runs automatically after a successful build on `master`
  (deploys the exact `sha-<full-sha>` just built), or manually with a chosen tag. A
  GitHub-hosted runner **SSHes into the server**; the server logs in to GHCR, runs
  `git reset --hard` to the deployed commit (syncs compose + `nginx/nginx.conf`), then
  `docker compose -f docker-compose.prod.yml pull && up -d`. Uses GitHub **Environments**
  (`prod`/`dev`). Required secrets per environment: `SSH_HOST` / `SSH_USER` / `SSH_PORT` /
  `SSH_KEY` / `SSH_FINGERPRINT` / `DEPLOY_PATH` / `GHCR_USER` / `GHCR_PAT` (PAT with
  `read:packages` only). The server keeps its own `./.env` (provisioned out-of-band; CI
  never touches it — an opt-in snippet to let CI write it is in the workflow).

**GitLab CI** (`.gitlab-ci.yml`) — `test → build → deploy`:
- **test** runs `docker-compose.test.yml` (the gate).
- **build** pushes to the GitLab Container Registry with the same tag set
  (`sha-<sha>`, `latest` on the default branch, `vX.Y.Z`/`X.Y.Z` on tags).
- **deploy-dev**/**deploy-prod** SSH to the server and pull the pinned `sha-<sha>` image
  via `docker-compose.prod.yml`. The server authenticates with a **Deploy Token**
  (`CI_DEPLOY_USER`/`CI_DEPLOY_PASSWORD`, scope `read_registry`) so restarts/`pull_policy:
  always` keep working. Required CI vars: `DEV_SSH_KEY`/`DEV_HOST`/`DEV_PORT`/`DEV_USER`/
  `DEV_PATH` (+ `PROD_*`).

A `git tag vX.Y.Z` push runs test → build and pushes the semver image (no auto-deploy).

> Keep only the platform you use; both are provided as a starting point.
