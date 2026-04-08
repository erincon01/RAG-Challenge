# syntax=docker/dockerfile:1.7

# =========================================================================
# RUNTIME (production)
# -------------------------------------------------------------------------
# This stage ships to production. It must contain ONLY what the running
# FastAPI backend needs at runtime. Do NOT add dev tooling (git, node,
# editors, debuggers) here — put them in the `devcontainer` stage below.
# =========================================================================
FROM python:3.11-slim-bookworm AS runtime

WORKDIR /app

# System deps for the running app:
#   - ca-certificates: TLS for outbound calls (OpenAI, StatsBomb, etc.)
#   - curl: kept because it's tiny and msodbcsql18 install needs it
#   - libpq-dev + gcc: build psycopg2 from source
#   - msodbcsql18 + unixodbc-dev: pyodbc driver for SQL Server
#
# gnupg2 and apt-transport-https are installed ONLY to add the Microsoft
# apt repository key, then purged in the same layer to keep the final
# image lean and to reduce production attack surface.
RUN apt-get update && apt-get install -y --no-install-recommends \
        ca-certificates \
        curl \
        libpq-dev \
        gcc \
        gnupg2 \
        apt-transport-https \
    && curl -fsSL https://packages.microsoft.com/keys/microsoft.asc \
        | gpg --dearmor -o /usr/share/keyrings/microsoft-prod.gpg \
    && curl -fsSL https://packages.microsoft.com/config/debian/12/prod.list \
        > /etc/apt/sources.list.d/mssql-release.list \
    && apt-get update \
    && ACCEPT_EULA=Y apt-get install -y --no-install-recommends \
        msodbcsql18 \
        unixodbc-dev \
    && apt-get purge -y --auto-remove gnupg2 apt-transport-https \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy shared config module to project root (so import resolution works)
COPY config/ /config/

# Copy backend application code
COPY backend/ .

# Create non-root user with stable UID/GID 1000 so bind mounts from the host
# and from the devcontainer stage share ownership consistently.
RUN groupadd --gid 1000 appuser \
    && useradd --uid 1000 --gid 1000 --create-home appuser \
    && chown -R appuser:appuser /app /config \
    && mkdir -p /home/appuser/.local/bin \
    && chown -R appuser:appuser /home/appuser

ENV PATH="/home/appuser/.local/bin:${PATH}"

# Run as non-root by default in production
USER appuser

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--loop", "asyncio"]


# =========================================================================
# DEVCONTAINER (dev only)
# -------------------------------------------------------------------------
# This stage is built ONLY when VS Code Dev Containers loads
# `.devcontainer/docker-compose.override.yml`, which selects it via
# `build.target: devcontainer`. Plain `docker compose up` never touches
# this stage, so the tools below never land in production.
#
# Reuses the runtime stage as its base, so the lean production layers are
# shared and cached between both images.
# =========================================================================
FROM runtime AS devcontainer

USER root

# Dev-only tooling:
#   - git, openssh-client: source control from inside the container
#   - gnupg2, apt-transport-https: reinstated for apt ops inside the container
#   - less, procps: interactive use (paging, ps/top)
#   - nodejs (LTS): required by the Claude CLI and other dev tooling
RUN apt-get update && apt-get install -y --no-install-recommends \
        git \
        gnupg2 \
        apt-transport-https \
        openssh-client \
        less \
        procps \
    && curl -fsSL https://deb.nodesource.com/setup_lts.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Back to non-root for interactive dev use. VS Code honors this via
# `remoteUser: appuser` in devcontainer.json.
USER appuser
WORKDIR /workspace
