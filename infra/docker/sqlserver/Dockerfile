FROM mcr.microsoft.com/mssql/server:2025-latest

USER root

# Install mssql-tools18 for sqlcmd
RUN apt-get update \
    && ACCEPT_EULA=Y apt-get install -y mssql-tools18 unixodbc-dev \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Copy init scripts and entrypoint
COPY initdb/ /docker-entrypoint-initdb.d/
COPY setup.sh /setup.sh
RUN chmod +x /setup.sh

USER mssql

ENTRYPOINT ["/setup.sh"]
