# syntax=docker/dockerfile:1
# ==============================================================================
# PWD301 Online Course Management Platform - Production Multi-Stage Dockerfile
# ==============================================================================
# Stage 1: Build stage (compile wheels and prepare dependencies)
# ==============================================================================
FROM python:3.12.12-slim-bookworm AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    pkg-config \
    libcairo2-dev \
    curl \
    gnupg \
    unixodbc-dev \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.lock .
RUN pip install --upgrade pip setuptools wheel \
    && pip wheel --no-cache-dir --wheel-dir /build/wheels --require-hashes -r requirements.lock

# Fixed complete MathJax fonts render TeX without network access at request time.
FROM node:24.16.0-bookworm-slim AS math-builder
WORKDIR /math
COPY tools/pdf-math/package.json tools/pdf-math/package-lock.json ./
RUN npm ci --omit=dev --ignore-scripts --no-audit --no-fund

# ==============================================================================
# Stage 2: Final runtime stage (minimal footprint, non-root user)
# ==============================================================================
FROM python:3.12.12-slim-bookworm AS final

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=5000 \
    APP_ENV=production \
    PYTHONPATH=/app/src:/app \
    FLASK_APP=pwd301

WORKDIR /app

# Install runtime system dependencies and Microsoft ODBC Driver 18
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gnupg \
    unixodbc \
    ca-certificates \
    ffmpeg \
    fonts-dejavu-core \
    fonts-freefont-ttf \
    fonts-noto-cjk \
    chromium \
    libcairo2 \
    libfreetype6 \
    && curl -fsSL https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor -o /usr/share/keyrings/microsoft-prod.gpg \
    && curl -fsSL https://packages.microsoft.com/config/debian/12/prod.list > /etc/apt/sources.list.d/mssql-release.list \
    && apt-get update \
    && ACCEPT_EULA=Y apt-get install -y --no-install-recommends msodbcsql18 \
    && rm -rf /var/lib/apt/lists/*

# Install pre-compiled wheels from builder stage using bind mount (avoids intermediate layer)
RUN --mount=type=bind,from=builder,source=/build/wheels,target=/wheels \
    pip install --no-cache-dir /wheels/*

# Isolated Node binary and mathjax node_modules for local server-side MathJax SVG rendering
COPY --from=math-builder /usr/local/bin/node /usr/local/bin/node
COPY --from=math-builder /math/node_modules /app/tools/pdf-math/node_modules

# Security Invariant: Create non-root system user and group (UID 10001)
RUN groupadd -g 10001 appgroup && \
    useradd -u 10001 -g appgroup -s /bin/bash -m appuser

# Create persistent storage directories with proper permissions
RUN mkdir -p /app/storage /app/quarantine /app/backups /app/exports /app/instance /app/scripts /app/tools/pdf-math && \
    chown -R appuser:appgroup /app

# Selective Copy: Copy ONLY necessary runtime files into container (Preventing Docker bloat)
COPY --chown=appuser:appgroup src/ /app/src/
COPY --chown=appuser:appgroup migrations/ /app/migrations/
COPY --chown=appuser:appgroup frontend/ /app/frontend/
COPY --chown=appuser:appgroup wsgi.py pyproject.toml /app/
COPY --chown=appuser:appgroup tools/pdf-math/render.cjs tools/pdf-math/package.json /app/tools/pdf-math/
COPY --chown=appuser:appgroup scripts/docker-entrypoint.sh \
     scripts/wait_for_db.py \
     scripts/run_worker.py \
     scripts/worker_healthcheck.py /app/scripts/

# Ensure entrypoint script is executable
RUN chmod +x /app/scripts/docker-entrypoint.sh

USER appuser

EXPOSE 5000

HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

ENTRYPOINT ["/app/scripts/docker-entrypoint.sh"]
CMD ["gunicorn"]
