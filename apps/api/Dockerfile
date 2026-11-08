FROM python:3.12-slim-bookworm AS base

# Environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PATH="/app/.venv/bin:$PATH" \
    PYTHONPATH="/app/apps/api:/app/packages/contracts"

# Install native system dependencies for WeasyPrint (GTK3/Pango/Cairo) and healthchecks (curl)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpango-1.0-0 \
    libharfbuzz0b \
    libpangoft2-1.0-0 \
    libpangocairo-1.0-0 \
    libcairo2 \
    libgdk-pixbuf-2.0-0 \
    shared-mime-info \
    fonts-dejavu-core \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv from official image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

WORKDIR /app

# Copy dependency manifests first for maximum Docker layer caching
COPY pyproject.toml uv.lock ./
COPY packages/contracts/pyproject.toml ./packages/contracts/
COPY apps/api/pyproject.toml ./apps/api/
COPY apps/cli/pyproject.toml ./apps/cli/

# Copy workspace source code
COPY packages/ ./packages/
COPY apps/ ./apps/

# Synchronize virtual environment with frozen lockfile across all workspace packages
RUN uv sync --frozen --no-dev --all-packages

# Security hardening: Run as non-root user
RUN groupadd -r vulnflow && useradd -r -g vulnflow -u 1000 vulnflow && \
    chown -R vulnflow:vulnflow /app

USER vulnflow

EXPOSE 8000

ENTRYPOINT ["python", "apps/api/entrypoint.py"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
