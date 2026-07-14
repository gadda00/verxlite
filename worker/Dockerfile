FROM python:3.10-slim AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir poetry==1.8.3

# Copy the API pyproject first so the worker can install the local API package.
COPY pyproject.toml poetry.lock* ./
COPY api/pyproject.toml api/poetry.lock* /tmp/api/

# Install worker deps.
RUN poetry export --without dev --format requirements.txt --output requirements.txt 2>/dev/null \
    && pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir -e /tmp/api

# -------------------------------------------------------------------
# Runtime image
# -------------------------------------------------------------------
FROM python:3.10-slim AS runtime

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends libpq5 \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --uid 1000 verxlite

COPY --from=builder /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY --from=builder /tmp/api /app/api

COPY --chown=verxlite:verxlite . .

ENV PYTHONPATH=/app:/app/api \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

USER verxlite

HEALTHCHECK --interval=60s --timeout=10s --start-period=30s --retries=3 \
  CMD celery -A tasks inspect ping -d "celery@$$HOSTNAME" || exit 1

CMD ["celery", "-A", "tasks", "worker", "--loglevel=info", "--concurrency=2"]
