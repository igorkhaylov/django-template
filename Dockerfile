FROM python:3.13-slim

ARG DEV=false

EXPOSE 8000

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    POETRY_VERSION=2.1.3 \
    POETRY_VIRTUALENVS_CREATE=false

RUN apt-get update && apt-get install -y \
    build-essential \
    python3-dev \
    libpq-dev \
    gcc \
    curl \
    gettext \
    $([ "$DEV" = "true" ] && echo "git openssh-client") \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

RUN pip install --no-cache-dir "poetry==$POETRY_VERSION" virtualenv --upgrade

COPY ./backend/pyproject.toml ./backend/poetry.lock ./

RUN if [ "$DEV" = "true" ]; then \
        poetry install --no-root --with dev; \
    else \
        poetry install --no-root --only main; \
    fi

COPY ./backend/ .

CMD ["sleep", "infinity"]
