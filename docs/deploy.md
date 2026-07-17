# Deploy runbook: zero → first deploy → CI

How to take a server from nothing to a running stack, and then let CI deploy to it.
GitHub-flavored throughout; the GitLab equivalents are noted [at the end](#gitlab-ci).

**The model** (same as [README → CI/CD](../README.md#cicd)): CI builds the backend image
and pushes it to **GHCR**; the server **only pulls** — it never builds. The server holds
three things: a git checkout of this repo (for `docker-compose.prod.yml` +
`nginx/nginx.conf` + `Makefile`), its own `./.env`, and a Docker login to the registry.

---

## 1. Create a registry pull token (GHCR_PAT)

The image `ghcr.io/<owner>/<repo>` is **private by default**, so the server cannot pull
it anonymously — every `make prod deploy` needs a logged-in Docker. You authenticate
with a GitHub **Personal Access Token (classic)**:

1. GitHub → your avatar → **Settings** → **Developer settings** →
   **Personal access tokens** → **Tokens (classic)** → **Generate new token (classic)**.
2. Name it after its purpose (e.g. `server-pull myproject`), set an expiration you can
   live with (you'll rotate it), and tick **only** the **`read:packages`** scope.
   Nothing else — this token will live on the server, so keep it read-only.
3. Generate and copy the token — GitHub shows it once.

> Use a **classic** token: GHCR's registry authentication does not accept fine-grained
> tokens for package pulls. `read:packages` is the whole point of this token — do not
> reuse a personal do-everything PAT here.

Log the server in (once; Docker persists it in `~/.docker/config.json`):

```bash
echo "$GHCR_PAT" | docker login ghcr.io -u <github-username> --password-stdin
```

Notes:
- The stored credential is only base64-encoded, not encrypted — that's another reason
  the token must be `read:packages`-only.
- To rotate: generate a new token, re-run `docker login`, delete the old token in GitHub.
- The CI deploy workflow logs in and **logs out** on every run by itself; this manual
  login is for `make prod deploy` runs and for `pull_policy: always` on restarts.

## 2. Provision the server

```bash
# Docker Engine + compose plugin (Debian/Ubuntu; see docs.docker.com for others):
curl -fsSL https://get.docker.com | sh

# The deploy checkout — the path becomes DEPLOY_PATH for CI:
git clone git@github.com:<owner>/<repo>.git /srv/<project>
cd /srv/<project>
```

Create the production `./.env` (it stays on the server; CI never touches it). Start from
`.env.example` and set at minimum:

| Variable | Value in prod |
|---|---|
| `ENVIRONMENT` | `prod` (turns on all security flags) |
| `DJANGO_SECRET_KEY` | strong, ≥ 50 chars: `openssl rand -hex 64` |
| `DJANGO_ALLOWED_HOSTS` / `DJANGO_CSRF_TRUSTED_ORIGINS` / `DJANGO_CORS_ALLOWED_ORIGINS` | your real domain(s) |
| `DJANGO_SUPERUSER_PASSWORD` | strong — placeholder values make the boot **fail** in prod |
| `POSTGRES_PASSWORD` | strong |
| `BACKEND_IMAGE` | `ghcr.io/<owner>/<repo>:latest`, or pin `:sha-<full-sha>` |
| `MINIO_ROOT_USER` / `MINIO_ROOT_PASSWORD` | anything non-default (signals "external storage") |
| `DJANGO_MINIO_*` | endpoint/bucket/credentials of your real S3/MinIO |
| `APP_PORT` | host port your edge proxy will target (default `8050`) |

**Provision the object-storage bucket before the first boot.** Static and media are
served from S3/MinIO with no filesystem fallback, and the entrypoint's
`wait_for_storage` **fails the boot on purpose** if the bucket is missing or
unreachable. Create the bucket + app credentials on your provider first.

## 3. First deploy

```bash
cd /srv/<project>
docker login ghcr.io ...   # step 1, if not done yet
make prod deploy           # = docker compose -f docker-compose.prod.yml pull && up -d
```

Verify:

```bash
docker compose -f docker-compose.prod.yml ps      # backend/celery/... should be "healthy"
docker compose -f docker-compose.prod.yml logs -f backend
curl -s http://localhost:${APP_PORT:-8050}/healthcheck/   # {"status": "ok"}
```

Point your **edge reverse proxy** (the one terminating TLS) at `APP_PORT`. It must set
`X-Forwarded-Proto` and put the real client IP first in `X-Forwarded-For` — see
[README → Deployment topology](../README.md#deployment-topology-read-this-first).

## 4. Let CI deploy (GitHub Actions)

`.github/workflows/deploy.yml` SSHes into the server and repeats step 3 (plus
`git reset --hard` to the deployed commit, so compose/nginx config stay in sync).

Create a **dedicated deploy keypair** (never reuse your personal key):

```bash
ssh-keygen -t ed25519 -f deploy_key -C "deploy <project>" -N ""
ssh-copy-id -i deploy_key.pub -p <port> <user>@<host>   # or append to authorized_keys
```

Pin the server's host key fingerprint:

```bash
ssh-keyscan -p <port> <host> 2>/dev/null | ssh-keygen -lf -   # take the SHA256:... value
```

In the GitHub repo, create **Environments** `prod` (and `dev` if used) and add the
secrets per environment:

| Secret | Value |
|---|---|
| `SSH_HOST` / `SSH_PORT` / `SSH_USER` | server address, SSH port, deploy user |
| `SSH_KEY` | contents of the private `deploy_key` |
| `SSH_FINGERPRINT` | the `SHA256:...` host-key fingerprint from above |
| `DEPLOY_PATH` | the checkout path, e.g. `/srv/<project>` |
| `GHCR_USER` / `GHCR_PAT` | GitHub username + the `read:packages` token from step 1 |

Two ways to trigger:

- **Manual (always available):** Actions → *Deploy* → *Run workflow* → pick the
  environment and an image tag (`latest`, or `sha-<full-sha>` to pin).
- **Auto on merge (opt-in):** set the repository **variable** `AUTO_DEPLOY=true`
  (Settings → Secrets and variables → Actions → **Variables**). Every successful
  master build then deploys its exact `sha-<full-sha>`. Leave it unset on the bare
  template / on projects that deploy manually — the job is skipped, not failed.

## 5. Rollback

Images stay on the server ~72 h (`docker image prune --filter until=72h` runs after each
deploy), and every build is also in the registry forever by `sha-` tag:

```bash
# Via CI: Actions → Deploy → Run workflow → image_tag = sha-<previous-sha>
# Or on the server:
BACKEND_IMAGE=ghcr.io/<owner>/<repo>:sha-<previous-sha> make prod deploy
```

(Only the image rolls back — an already-applied irreversible DB migration does not.
Check `dumps/`/db-backups before risky releases; see [backup.md](backup.md).)

## GitLab CI

Same model, different plumbing (`.gitlab-ci.yml`): the image goes to the GitLab
registry; the server authenticates with a project **Deploy Token** (scope
`read_registry`) instead of a PAT — Settings → Repository → Deploy tokens. CI/CD
variables: `CI_DEPLOY_USER`/`CI_DEPLOY_PASSWORD` (the deploy token) plus
`DEV_SSH_KEY`/`DEV_HOST`/`DEV_PORT`/`DEV_USER`/`DEV_PATH` (and `PROD_*`). Deploys pin
`sha-$CI_COMMIT_SHA` automatically on the `dev`/`master` branches.
