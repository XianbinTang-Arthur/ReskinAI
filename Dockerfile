FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md alembic.ini ./
COPY alembic ./alembic
COPY src ./src
COPY frontend ./frontend
COPY deploy/docker/entrypoint.sh /entrypoint.sh

RUN pip install --upgrade pip \
    && pip install ".[postgres,render]" "alembic>=1.13.2,<2.0.0" \
    && chmod +x /entrypoint.sh

RUN useradd --create-home --shell /bin/bash appuser \
    && mkdir -p /app/storage \
    && chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

ENTRYPOINT ["/entrypoint.sh"]
