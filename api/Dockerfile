FROM python:3.10-slim AS builder

WORKDIR /app

# System deps (psycopg2-binary ships its own libpq, so we only need build-essential
# for any source builds).
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry without virtualenv (we'll use the system Python).
RUN pip install --no-cache-dir poetry==1.8.3

# Copy only the dependency manifest first for better layer caching.
COPY pyproject.toml poetry.lock* ./

# Export requirements and install them into the system Python.
# This avoids the Poetry runtime overhead and produces a smaller image.
RUN poetry export --without dev --format requirements.txt --output requirements.txt \
    && pip install --no-cache-dir -r requirements.txt

# -------------------------------------------------------------------
# Runtime image
# -------------------------------------------------------------------
FROM python:3.10-slim AS runtime

WORKDIR /app

# Runtime deps for psycopg2.
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --uid 1000 verxlite

# Copy installed packages from the builder.
COPY --from=builder /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy source code.
COPY --chown=verxlite:verxlite . .

ENV PYTHONPATH=/app \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

USER verxlite

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health', timeout=5)" || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
