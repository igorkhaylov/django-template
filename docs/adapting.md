# Adapting this template to a new project

A checklist of **every place that carries the template's own name or the author's
defaults**. Work through it once, right after cloning, before the first commit of your
project — renaming a bucket, a database or a registry image later means migrating data.

## 0. Start a fresh history

```bash
git clone git@github.com:igorkhaylov/django-template.git myproject
cd myproject
rm -rf .git && git init && git add -A && git commit -m "[INIT] start from django-template"
```

(On GitHub, **Use this template** does the same without the `rm -rf .git`.)

## 1. Names and identifiers

| Where | What to change | Why it matters |
|---|---|---|
| `.env.example` → `PROJECT_NAME` | your project slug | Docker Compose project name (containers, volumes, network); dev/test append `-dev`/`-test`. **Two clones with the same name share volumes.** |
| `.env.example` → `DJANGO_APP_NAME` | human-readable app name | admin titles, Gunicorn process name, API title |
| `.env.example` → `POSTGRES_DB`, `POSTGRES_USER` | your names | baked into the Postgres volume on first boot; changing later = new volume |
| `.env.example` → `MINIO_BUCKET_NAME`, `MINIO_APP_USER` | unique per project | the **shared** local MinIO holds every project's bucket side by side; a clash means two projects write into one bucket |
| `.env.example` → `BACKEND_IMAGE` **and** `docker-compose.prod.yml` (default in `x-backend-defaults.image` + header comment) | `ghcr.io/<owner>/<repo>` | the registry image your CI pushes; the compose default is what `make prod deploy` pulls when `.env` does not set it |
| `backend/pyproject.toml` → `[project] name`, `authors` | your project / you | shown by `uv`; not used at runtime |
| `LICENSE` | your name / license of choice | the template is MIT with the author's copyright line |
| `README.md` | title + first paragraph | keep the operational sections, they stay true |
| `backend/locale/*/django.po` header comment | project name | cosmetic |
| `.vscode/settings.json` → `cSpell.words` | optional | editor spell-check dictionary only |

If you generated `.env` before renaming, delete it and re-run `make init` (it never
overwrites an existing `.env`), or edit the values by hand.

## 2. Settings defaults

| Setting | File | Template default |
|---|---|---|
| `TIME_ZONE` | `backend/config/settings/base.py` | `Asia/Tashkent` |
| `LANGUAGE_CODE`, `LANGUAGES`, `MODELTRANSLATION_*` | `base.py` | `en` default + `ru`; keep `modeltranslation` first in `INSTALLED_APPS` |
| `SPECTACULAR_SETTINGS` (`DESCRIPTION`, `VERSION`) | `third_party.py` | placeholder text; the schema/Swagger views are **not routed yet** — add them to `config/urls.py` when the first endpoint appears |
| `REST_FRAMEWORK` | `third_party.py` | **no** `DEFAULT_PERMISSION_CLASSES` and empty `DEFAULT_AUTHENTICATION_CLASSES` — the first endpoint you add is world-open by default. Set `IsAuthenticated` + an auth class before shipping an API. |
| `DATA_UPLOAD_MAX_MEMORY_SIZE` / `FILE_UPLOAD_MAX_MEMORY_SIZE` | `base.py` | 10 MB; nginx allows 500 MB bodies (`client_max_body_size`) |
| Celery limits, queues | `backend/config/celery.py` | 3 h task limit, single `celery` queue, 2 worker processes in compose |

## 3. The user model

`users.User` is a custom `AbstractBaseUser` (username login, optional verified emails in
`UserEmail`). Decide **before the first release**:

- **Activation.** `is_active` defaults to `False`; nothing in the template activates a
  regular user (the intended trigger is OTP/email verification, marked `TODO(OTP)` in
  `users/models.py`). Either implement the flow or flip the default to `True`.
- **Fields.** Add/remove fields, then `make dev makemigrations` — the shipped
  `0001_initial.py` is a normal migration you build on. Prefer a single clean initial
  migration? Delete `0001_initial.py`, regenerate it, and reset the dev DB
  (`make dev down-v`) — only ever before the first deploy.
- `tests/test_common.py::test_migrations_in_sync` fails the suite whenever models and
  migrations drift, so a forgotten `makemigrations` cannot reach CI unnoticed.

## 4. CI/CD — keep one platform

Both are wired; delete the one you do not use (`.github/workflows/` **or**
`.gitlab-ci.yml`) so it does not fail on every push.

**GitHub Actions**
- `build-push.yml` needs nothing beyond the built-in `GITHUB_TOKEN`; the image name is
  derived from the repository (lowercased).
- `deploy.yml` needs Environments `prod`/`dev` with the secrets listed in
  [deploy.md](deploy.md#4-let-ci-deploy-github-actions). Auto-deploy on merge is
  **opt-in** via the repository variable `AUTO_DEPLOY=true`; until then every push
  shows the deploy job as *skipped* (grey), which is expected.

**GitLab CI**
- Every job has `tags: [default]` — rename to match your runner's tags or delete the
  `tags:` lines to use any shared runner.
- Variables: `CI_DEPLOY_USER`/`CI_DEPLOY_PASSWORD` (Deploy Token, `read_registry`),
  `DEV_*` / `PROD_*` SSH settings.
- Branch model: `dev` → deploy-dev, `master` → deploy-prod, `vX.Y.Z` tags → build only.

## 5. Optional features (off by default)

| Feature | How to turn on |
|---|---|
| Firebase push notifications | `firebase-admin` is an extra: `uv sync --extra push`, add `--extra push` to every `uv sync` in `Dockerfile` and `Dockerfile.dev`, put the service-account JSON in `firebase_credentials/` (git- and docker-ignored) and import `common.firebase` once at startup. Details in `backend/apps/common/firebase.py`. |
| Scheduled DB backups (prod) | `COMPOSE_PROFILES=backup` in the server's `.env`; see [backup.md](backup.md#automated-database-backups-optional). |
| Debug toolbar | already on in `ENVIRONMENT=dev` only (`settings/dev.py`); mounted at `/__debug__/` |
| Rosetta translation UI | on; `/rosetta/`, superusers and the "Rosetta Users" group (created on `migrate`) |
| WebSockets through nginx | commented `location /ws/` blocks in both nginx configs |

## 6. Things to leave alone (they look odd but are deliberate)

- **`nginx/nginx.conf` does not set `X-Forwarded-Proto`.** The edge proxy in front of
  the stack does; re-setting it here would turn every proxied request into "http" and
  create a redirect loop under `SECURE_SSL_REDIRECT`. See README → Deployment topology.
- **`ENVIRONMENT=production` is rejected on purpose.** Only `dev | test | stage | prod`
  are accepted; anything else raises instead of silently running with `DEBUG=True`.
- **Static files live in the bucket, even in dev.** There is no filesystem fallback, so
  `collectstatic` (run by `make init` and by the prod entrypoint) is what makes the admin
  render with CSS.
- **MinIO is not in `docker-compose*.yml`.** One shared host container serves every
  project on the machine (`make minio`); prod points at managed storage.
- **`make dev up` does not serve HTTP.** The backend container idles so you can run
  migrations/tests freely; `make dev run` starts the dev server.
