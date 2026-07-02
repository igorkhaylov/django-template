# syntax=docker/dockerfile:1

# ----------------------------- builder -----------------------------
# Builds the virtualenv at /opt/venv from the locked dependencies.
FROM python:3.13-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=0 \
    UV_PROJECT_ENVIRONMENT=/opt/venv

# build-essential/gcc/libpq-dev for any source builds; git for the django-stdimage
# git dependency.
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential python3-dev libpq-dev gcc git \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir uv

# Set to "true" to include the dev dependency group (used by the test image).
ARG INSTALL_DEV=false

WORKDIR /app
COPY backend/pyproject.toml backend/uv.lock ./
RUN if [ "$INSTALL_DEV" = "true" ]; then uv sync --frozen; else uv sync --frozen --no-dev; fi

# ----------------------------- runtime -----------------------------
FROM python:3.13-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH"

# gettext -> compilemessages (msgfmt); curl -> container healthcheck.
RUN apt-get update && apt-get install -y --no-install-recommends \
    gettext curl \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --uid 1000 app

WORKDIR /app
COPY --from=builder /opt/venv /opt/venv
COPY backend/ .
RUN chown -R app:app /app
USER app

EXPOSE 8000

# The command (scripts/entrypoint.sh) is provided by docker-compose.
