# Этап сборки
FROM python:3.12-slim-bookworm AS builder

# RUN apt-get update && \
#     apt-get install -y --no-install-recommends \
#         build-essential \
#         gcc \
#         libffi-dev \
#         libssl-dev \
#         libpq-dev \
#         && rm -rf /var/lib/apt/lists/*

WORKDIR /app
# COPY requirements.txt .
# RUN pip install --upgrade pip && \
#     pip install --no-cache-dir --prefix=/install -r requirements.txt

# # Финальный минимальный образ
# FROM python:3.12-slim-bookworm

# WORKDIR /app

# # Копируем установленные пакеты
# COPY --from=builder /install /usr/local
# COPY . .

# CMD ["python"]
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
