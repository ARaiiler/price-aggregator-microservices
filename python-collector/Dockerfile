# =============================================================================
# Python Data Collector Service
# =============================================================================
# INTERNAL SERVICE — this image must not be published to a public registry
# without stripping all default credential values from the environment.
#
# Build:  docker build -t python-collector .
# Run:    docker run --env-file .env python-collector
# =============================================================================

# ---- Stage 1: dependency builder -------------------------------------------
FROM python:3.11-slim AS builder

WORKDIR /build

# gcc is required by some C-extension wheels (e.g. hiredis)
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt


# ---- Stage 2: lean production image ----------------------------------------
FROM python:3.11-slim

WORKDIR /app

# Copy only the installed packages from the builder stage
COPY --from=builder /install /usr/local

# Copy application source
COPY . .

# Non-root user for least-privilege execution
RUN useradd -m -u 1001 -s /bin/sh appuser && \
    chown -R appuser:appuser /app

USER appuser

# ---------------------------------------------------------------------------
# Runtime environment variable defaults
# ---------------------------------------------------------------------------
# These values are safe fallbacks for local development only.
# Override every variable via docker-compose.yml ``environment:`` block or
# an explicit --env-file argument.  NEVER rely on these defaults in
# production — always supply real values through the orchestrator.
# ---------------------------------------------------------------------------
ENV SERVICE_PORT=8000 \
    LOG_LEVEL=info \
    ENVIRONMENT=production \
    REDIS_HOST=redis \
    REDIS_PORT=6379 \
    REDIS_PASSWORD=""

# Expose the port declared by SERVICE_PORT (document only; actual binding
# is controlled by docker-compose or the container runtime).
EXPOSE 8000

# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------
# Docker calls this command every 30 s to decide whether the container is
# healthy.  Uses the stdlib urllib so no extra dependencies are needed.
# start_period gives uvicorn time to fully start before the first probe.
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD python -c \
        "import urllib.request, os; \
         url = 'http://localhost:' + os.environ.get('SERVICE_PORT','8000') + '/health'; \
         urllib.request.urlopen(url, timeout=4)" \
    || exit 1

# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------
# Shell form (not exec form) so that ${SERVICE_PORT} and ${LOG_LEVEL} are
# expanded by the shell at container start from the live environment,
# allowing the port and log verbosity to be changed without rebuilding.
CMD uvicorn app.main:app \
        --host 0.0.0.0 \
        --port ${SERVICE_PORT:-8000} \
        --log-level ${LOG_LEVEL:-info} \
        --no-access-log
