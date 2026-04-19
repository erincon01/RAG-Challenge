#!/bin/bash
set -eu

echo "============================================"
echo "[post-create] RAG Challenge - Dev Container"
echo "============================================"

# ── 1. Python dependencies ─────────────────────────────────────────────
echo "[post-create] Installing Python dependencies..."
pip install --user -q -r /app/requirements.txt 2>/dev/null || {
    echo "  [warn] pip install failed — trying with --break-system-packages"
    pip install --user -q --break-system-packages -r /app/requirements.txt
}

# ── 2. Database bootstrap (idempotent) ─────────────────────────────────
echo "[post-create] Bootstrapping databases..."
python - <<'PY'
import os
import re
import socket
import time
from pathlib import Path

import psycopg2
import pyodbc

REPO_ROOT = Path("/workspace")

PG_HOST = os.getenv("POSTGRES_HOST", "postgres")
PG_DB = os.getenv("POSTGRES_DB", "rag_challenge")
PG_USER = os.getenv("POSTGRES_USER", "postgres")
PG_PASSWORD = os.getenv("POSTGRES_PASSWORD", "postgres_local_pwd")

SQL_HOST = os.getenv("SQLSERVER_HOST", "sqlserver")
SQL_DB = os.getenv("SQLSERVER_DB", "rag_challenge")
SQL_USER = os.getenv("SQLSERVER_USER", "sa")
SQL_PASSWORD = os.getenv("SQLSERVER_PASSWORD", "SqlServer_Local_Pwd123!")


def is_host_reachable(host: str, port: int) -> bool:
    try:
        sock = socket.create_connection((host, port), timeout=3)
        sock.close()
        return True
    except (OSError, socket.timeout):
        return False


def wait_for_db(name: str, connect_fn, max_attempts: int = 30, sleep_s: int = 2):
    for attempt in range(1, max_attempts + 1):
        try:
            conn = connect_fn()
            conn.close()
            return True
        except Exception:
            if attempt == max_attempts:
                print(f"  [warn] {name} not ready after {max_attempts * sleep_s}s — skipping.")
                return False
            time.sleep(sleep_s)


def split_sqlserver_batches(sql_text: str):
    return [
        part.strip()
        for part in re.split(r"^\s*GO\s*$", sql_text, flags=re.MULTILINE | re.IGNORECASE)
        if part.strip()
    ]


# ── PostgreSQL (only if running) ──────────────────────────────────────
if is_host_reachable(PG_HOST, 5432):
    print(f"  PostgreSQL detected at {PG_HOST}:5432 — waiting...")
    pg_ok = wait_for_db(
        "PostgreSQL",
        lambda: psycopg2.connect(host=PG_HOST, database=PG_DB, user=PG_USER, password=PG_PASSWORD),
    )
    if pg_ok:
        with psycopg2.connect(host=PG_HOST, database=PG_DB, user=PG_USER, password=PG_PASSWORD) as conn:
            with conn.cursor() as cur:
                # Re-apply schema (idempotent) to pick up any migrations
                schema_file = REPO_ROOT / "infra/docker/postgres/initdb/02-schema.sql"
                if schema_file.exists():
                    cur.execute(schema_file.read_text(encoding="utf-8"))
        print("  PostgreSQL bootstrap done.")
else:
    print("  PostgreSQL not reachable — skipping.")

# ── SQL Server (only if running) ──────────────────────────────────────
if is_host_reachable(SQL_HOST, 1433):
    print(f"  SQL Server detected at {SQL_HOST}:1433 — waiting...")
    sql_conn_str = (
        "DRIVER={ODBC Driver 18 for SQL Server};"
        f"SERVER={SQL_HOST};"
        f"DATABASE={SQL_DB};"
        f"UID={SQL_USER};"
        f"PWD={SQL_PASSWORD};"
        "TrustServerCertificate=yes;"
    )
    sql_ok = wait_for_db(
        "SQL Server",
        lambda: pyodbc.connect(sql_conn_str, timeout=5),
    )
    if sql_ok:
        with pyodbc.connect(sql_conn_str, autocommit=True) as conn:
            cur = conn.cursor()

            schema_sql = (REPO_ROOT / "infra/docker/sqlserver/initdb/01-schema.sql").read_text(encoding="utf-8")
            for batch in split_sqlserver_batches(schema_sql):
                cur.execute(batch)
        print("  SQL Server bootstrap done.")
else:
    print("  SQL Server not reachable — skipping.")

print("[post-create] Database bootstrap completed.")
PY

# ── 3. Seed dataset (idempotent, no API key required) ────────────────
echo "[post-create] Loading seed dataset (Euro 2024 + WC 2022 finals)..."
(
    cd /app && python -m scripts.seed_load --source both
) || {
    echo "  [warn] Seed load failed — dashboard will be empty on first open."
    echo "  [warn] You can retry with: make seed"
    echo "  [warn] Or: cd /app && python -m scripts.seed_load --source both"
}

echo "[post-create] Done."
