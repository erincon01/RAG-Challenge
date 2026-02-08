#!/bin/bash
# SQL Server Docker entrypoint wrapper.
# Starts SQL Server in the background, waits until it is ready,
# runs init scripts, and then keeps the process running.

set -e

# Start SQL Server in the background
/opt/mssql/bin/sqlservr &
SQLPID=$!

echo "Waiting for SQL Server to start..."
for i in $(seq 1 60); do
    /opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -P "$MSSQL_SA_PASSWORD" -C -Q "SELECT 1" > /dev/null 2>&1
    if [ $? -eq 0 ]; then
        echo "SQL Server is ready."
        break
    fi
    sleep 1
done

# Run init scripts in order
for f in /docker-entrypoint-initdb.d/*.sql; do
    if [ -f "$f" ]; then
        echo "Running $f ..."
        /opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -P "$MSSQL_SA_PASSWORD" -C -i "$f"
    fi
done

echo "Init scripts completed."

# Wait for SQL Server process
wait $SQLPID
