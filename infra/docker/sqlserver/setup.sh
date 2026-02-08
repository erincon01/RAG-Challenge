#!/bin/bash
# SQL Server Docker entrypoint wrapper.
# Starts SQL Server in the background, waits until it is ready,
# runs init scripts, and then keeps the process running.

set -euo pipefail

# Start SQL Server in the background
/opt/mssql/bin/sqlservr &
SQLPID=$!

echo "Waiting for SQL Server to start..."
ready=0
for i in $(seq 1 90); do
    if /opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -P "$MSSQL_SA_PASSWORD" -C -Q "SELECT 1" > /dev/null 2>&1; then
        echo "SQL Server is ready."
        ready=1
        break
    fi
    sleep 1
done

if [ "$ready" -ne 1 ]; then
    echo "SQL Server did not become ready in time." >&2
    kill "$SQLPID" >/dev/null 2>&1 || true
    wait "$SQLPID" || true
    exit 1
fi

# Run init scripts in order
for f in /docker-entrypoint-initdb.d/*.sql; do
    if [ -f "$f" ]; then
        echo "Running $f ..."
        /opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -P "$MSSQL_SA_PASSWORD" -C -i "$f"
    fi
done

echo "Init scripts completed."

# Wait for SQL Server process
wait "$SQLPID"
