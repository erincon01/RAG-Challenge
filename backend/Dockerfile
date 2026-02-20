FROM python:3.11-slim-bookworm

WORKDIR /app

# Install system dependencies for pyodbc (SQL Server), psycopg2, and Node.js LTS
RUN apt-get update && apt-get install -y --no-install-recommends \
    bash gnupg2 curl apt-transport-https git ca-certificates \
    # PostgreSQL client libs
    libpq-dev gcc \
    # Node.js LTS (for Claude CLI and tooling)
    && curl -fsSL https://deb.nodesource.com/setup_lts.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    # ODBC Driver 18 for SQL Server
    && curl -fsSL https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor -o /usr/share/keyrings/microsoft-prod.gpg \
    && curl -fsSL https://packages.microsoft.com/config/debian/12/prod.list > /etc/apt/sources.list.d/mssql-release.list \
    && apt-get update \
    && ACCEPT_EULA=Y apt-get install -y --no-install-recommends msodbcsql18 unixodbc-dev \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy shared config module to project root (so import resolution works)
COPY config/ /config/

# Copy backend application code
COPY backend/ .

# Create non-root user (switched at runtime via devcontainer.json remoteUser)
RUN groupadd --gid 1000 appuser \
    && useradd --uid 1000 --gid 1000 --create-home appuser \
    && chown -R appuser:appuser /app /config \
    && mkdir -p /home/appuser/.local/bin \
    && chown -R appuser:appuser /home/appuser

ENV PATH="/home/appuser/.local/bin:${PATH}"

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--loop", "asyncio"]
