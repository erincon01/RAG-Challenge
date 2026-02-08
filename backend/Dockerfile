FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for pyodbc (SQL Server) and psycopg2
RUN apt-get update && apt-get install -y --no-install-recommends \
    bash gnupg2 curl apt-transport-https \
    # PostgreSQL client libs
    libpq-dev gcc \
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

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
