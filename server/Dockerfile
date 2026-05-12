# syntax=docker/dockerfile:1.7
# Multi-stage: builder com toolchain (build-essential, libpq-dev) -> runtime
# slim sem essas deps. Reduz imagem final em ~250MB e diminui surface area.

FROM python:3.12-slim AS builder

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    UV_LINK_MODE=copy

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app
COPY pyproject.toml uv.lock* ./
# --frozen falha se lockfile desatualizado (boa pratica em CI/prod).
RUN uv sync --frozen --no-dev --no-install-project

# ─── Runtime stage ──────────────────────────────────────────────────────────

FROM python:3.12-slim AS runtime

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/app/.venv/bin:$PATH"

# Apenas runtime deps: libpq5 (asyncpg eh puro Python mas algumas libs podem
# precisar) + curl (HEALTHCHECK).
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 curl \
    && rm -rf /var/lib/apt/lists/* \
    # Cria user non-root (UID 1000) — mata escalada caso container vire RCE.
    && groupadd --system --gid 1000 sentinelbr \
    && useradd --system --uid 1000 --gid sentinelbr --shell /sbin/nologin --no-create-home sentinelbr

WORKDIR /app
COPY --from=builder /app/.venv /app/.venv
COPY --chown=sentinelbr:sentinelbr app ./app

USER sentinelbr

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -fsS http://localhost:8000/api/v1/health || exit 1

# Direto via uvicorn (sem `uv run`) — nao precisa de uv em runtime.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
