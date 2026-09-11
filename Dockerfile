# ==============================================================================
# PWD301 Online Course Management Platform - Production Multi-Stage Dockerfile
# ==============================================================================
# Stage 1: Build stage (compile wheels and prepare dependencies)
# ==============================================================================
FROM python:3.12-slim-bookworm AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    gnupg \
    unixodbc-dev \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip \
    && pip wheel --no-cache-dir --wheel-dir /build/wheels -r requirements.txt

# ==============================================================================
# Stage 2: Final runtime stage (minimal footprint, non-root user)
# ==============================================================================
FROM python:3.12-slim-bookworm AS final

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
    && curl -fsSL https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor -o /usr/share/keyrings/microsoft-prod.gpg \
    && curl -fsSL https://packages.microsoft.com/config/debian/12/prod.list > /etc/apt/sources.list.d/mssql-release.list \
    && apt-get update \
    && ACCEPT_EULA=Y apt-get install -y --no-install-recommends msodbcsql18 \
    && rm -rf /var/lib/apt/lists/*

# Copy pre-compiled wheels from builder stage and install
COPY --from=builder /build/wheels /wheels
RUN pip install --no-cache-dir /wheels/* && rm -rf /wheels

# Security Invariant: Create non-root system user and group (UID 10001)
RUN groupadd -g 10001 appgroup && \
    useradd -u 10001 -g appgroup -s /bin/bash -m appuser

# Create persistent storage directories with proper permissions
RUN mkdir -p /app/storage /app/quarantine /app/backups /app/exports /app/instance && \
    chown -R appuser:appgroup /app

# Copy application code into container
COPY --chown=appuser:appgroup . /app

# Install the application package
RUN pip install --no-cache-dir --no-deps --no-build-isolation -e .

# Ensure entrypoint script is executable
RUN chmod +x /app/scripts/docker-entrypoint.sh

USER appuser

EXPOSE 5000

HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

ENTRYPOINT ["/app/scripts/docker-entrypoint.sh"]
CMD ["gunicorn"]