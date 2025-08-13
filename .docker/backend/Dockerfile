FROM python:3.13-slim

EXPOSE 8000

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    POETRY_VERSION=2.1.3 \
    POETRY_VIRTUALENVS_CREATE=false \
    PRODUCTION=1


RUN apt-get update && apt-get install -y \
    build-essential \
    python3-dev \
    libpq-dev \
    gcc \
    curl \
    gettext \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*


WORKDIR /app


RUN pip install --no-cache-dir "poetry==$POETRY_VERSION"

COPY ../../backend/pyproject.toml ../../backend/poetry.lock ./

RUN poetry install --no-root --only main

COPY ../../backend/ .

CMD ["python", "infinity"]
# CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
