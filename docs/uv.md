# uv — dependency & environment management

This project uses [uv](https://docs.astral.sh/uv/) instead of Poetry. Dependencies are
declared in `backend/pyproject.toml` (PEP 621 `[project].dependencies` for runtime,
`[dependency-groups].dev` for dev tools) and pinned in `backend/uv.lock`.

`[tool.uv] package = false` — this is an application, not a library, so uv manages only
the environment and never tries to build/install the project root.

> All commands below are run from `backend/` (where `pyproject.toml` lives), or use
> `uv run --project backend ...`.

## First time

```bash
cd backend
uv lock          # generate uv.lock from pyproject.toml  (commit it!)
uv sync          # create .venv and install runtime + dev dependencies
```

The Docker images install with `uv sync --frozen` (prod adds `--no-dev`), so **a
committed `uv.lock` is required before building**.

## Everyday commands

| Task | Command |
|---|---|
| Install everything (runtime + dev) | `uv sync` |
| Install runtime only | `uv sync --no-dev` |
| Add a runtime dependency | `uv add djangorestframework` |
| Add a dev dependency | `uv add --dev pytest-cov` |
| Add with a version constraint | `uv add "django>=5.2,<6"` |
| Remove a dependency | `uv remove <package>` |
| Refresh the lockfile | `uv lock` |
| Upgrade one package in the lock | `uv lock --upgrade-package django` |
| Upgrade everything | `uv lock --upgrade` |
| Run a command in the env | `uv run python manage.py migrate` |
| Run the test suite | `uv run pytest` |
| Show the dependency tree | `uv tree` |

## Notes

- `uv add` / `uv remove` update **both** `pyproject.toml` and `uv.lock` and sync the env.
- `uv sync --frozen` fails if the lock is out of date — that's intentional in CI/Docker.
- The virtualenv is `backend/.venv` by default. In the dev container it lives at
  `/opt/venv` (set via `UV_PROJECT_ENVIRONMENT`) so the bind-mounted source can't shadow it.
- Git dependency (e.g. `django-stdimage`) is declared as
  `package @ git+https://...@tag` in `[project].dependencies` and locked like any other.
