#!/usr/bin/env bash
set -euo pipefail

echo "[post-create] Installing Python dependencies (backend + frontend)..."
python -m pip install --upgrade pip >/dev/null
python -m pip install -r /app/backend/requirements.txt -r /app/frontend/requirements.txt >/dev/null

echo "[post-create] Waiting for databases and applying idempotent bootstrap (schema + seed)..."
python - <<'PY'
import os
import re
import time
from pathlib import Path

import psycopg2
import pyodbc

REPO_ROOT = Path("/app")

PG_HOST = os.getenv("DB_SERVER_AZURE_POSTGRES", "postgres")
PG_DB = os.getenv("DB_NAME_AZURE_POSTGRES", "rag_challenge")
PG_USER = os.getenv("DB_USER_AZURE_POSTGRES", "postgres")
PG_PASSWORD = os.getenv("DB_PASSWORD_AZURE_POSTGRES", "postgres_local_pwd")

SQL_HOST = os.getenv("DB_SERVER_AZURE", "sqlserver")
SQL_DB = os.getenv("DB_NAME_AZURE", "rag_challenge")
SQL_USER = os.getenv("DB_USER_AZURE", "sa")
SQL_PASSWORD = os.getenv("DB_PASSWORD_AZURE", "SqlServer_Local_Pwd123!")


def wait_for_postgres(max_attempts: int = 60, sleep_s: int = 2):
    for attempt in range(1, max_attempts + 1):
        try:
            conn = psycopg2.connect(
                host=PG_HOST,
                database=PG_DB,
                user=PG_USER,
                password=PG_PASSWORD,
            )
            conn.close()
            return
        except Exception:
            if attempt == max_attempts:
                raise
            time.sleep(sleep_s)


def wait_for_sqlserver(max_attempts: int = 60, sleep_s: int = 2):
    conn_str = (
        "DRIVER={ODBC Driver 18 for SQL Server};"
        f"SERVER={SQL_HOST};"
        f"DATABASE={SQL_DB};"
        f"UID={SQL_USER};"
        f"PWD={SQL_PASSWORD};"
        "TrustServerCertificate=yes;"
    )
    for attempt in range(1, max_attempts + 1):
        try:
            conn = pyodbc.connect(conn_str, timeout=5)
            conn.close()
            return
        except Exception:
            if attempt == max_attempts:
                raise
            time.sleep(sleep_s)


def split_sqlserver_batches(sql_text: str):
    return [part.strip() for part in re.split(r"^\s*GO\s*$", sql_text, flags=re.MULTILINE | re.IGNORECASE) if part.strip()]


wait_for_postgres()
wait_for_sqlserver()

# PostgreSQL: re-apply portable init scripts (idempotent) and seed minimal data.
with psycopg2.connect(host=PG_HOST, database=PG_DB, user=PG_USER, password=PG_PASSWORD) as pg_conn:
    with pg_conn.cursor() as cur:
        for sql_file in [
            REPO_ROOT / "infra/docker/postgres/initdb/01-extensions.sql",
            REPO_ROOT / "infra/docker/postgres/initdb/02-schema.sql",
        ]:
            cur.execute(sql_file.read_text(encoding="utf-8"))

        cur.execute(
            """
            INSERT INTO matches (
                match_id, match_date,
                competition_id, competition_country, competition_name,
                season_id, season_name,
                home_team_id, home_team_name, home_team_gender, home_team_country,
                away_team_id, away_team_name, away_team_gender, away_team_country,
                home_score, away_score, result, match_week,
                json_
            )
            SELECT
                900001, DATE '2024-07-14',
                1, 'Europe', 'UEFA Euro',
                1, '2024',
                100, 'Spain', 'male', 'Spain',
                200, 'England', 'male', 'England',
                2, 1, 'home', 1,
                '{"seed": true}'
            WHERE NOT EXISTS (
                SELECT 1 FROM matches WHERE match_id = 900001
            )
            """
        )

        cur.execute(
            """
            INSERT INTO events_details__quarter_minute (
                match_id, period, minute, quarter_minute, count, json_, summary, summary_script
            )
            SELECT
                900001, 1, 10, 2, 1,
                '{"event":"seed"}',
                'Seed event for devcontainer smoke tests',
                'Seed script'
            WHERE NOT EXISTS (
                SELECT 1
                FROM events_details__quarter_minute
                WHERE match_id = 900001 AND period = 1 AND minute = 10 AND quarter_minute = 2
            )
            """
        )

# SQL Server: re-apply portable schema script and seed minimal data.
sql_conn_str = (
    "DRIVER={ODBC Driver 18 for SQL Server};"
    f"SERVER={SQL_HOST};"
    f"DATABASE={SQL_DB};"
    f"UID={SQL_USER};"
    f"PWD={SQL_PASSWORD};"
    "TrustServerCertificate=yes;"
)
with pyodbc.connect(sql_conn_str, autocommit=True) as sql_conn:
    cur = sql_conn.cursor()

    schema_sql = (REPO_ROOT / "infra/docker/sqlserver/initdb/01-schema.sql").read_text(encoding="utf-8")
    for batch in split_sqlserver_batches(schema_sql):
        cur.execute(batch)

    cur.execute(
        """
        IF NOT EXISTS (SELECT 1 FROM matches WHERE match_id = 900001)
        BEGIN
            INSERT INTO matches (
                match_id, match_date,
                competition_id, competition_country, competition_name,
                season_id, season_name,
                home_team_id, home_team_name, home_team_gender, home_team_country,
                away_team_id, away_team_name, away_team_gender, away_team_country,
                home_score, away_score, result, match_week,
                json_
            ) VALUES (
                900001, '2024-07-14',
                1, 'Europe', 'UEFA Euro',
                1, '2024',
                100, 'Spain', 'male', 'Spain',
                200, 'England', 'male', 'England',
                2, 1, 'home', 1,
                '{"seed": true}'
            )
        END
        """
    )

    cur.execute(
        """
        IF NOT EXISTS (
            SELECT 1
            FROM events_details__15secs_agg
            WHERE match_id = 900001 AND period = 1 AND minute = 10 AND _15secs = 2
        )
        BEGIN
            INSERT INTO events_details__15secs_agg (
                match_id, period, minute, _15secs, count, json_, summary
            ) VALUES (
                900001, 1, 10, 2, 1, '{"event":"seed"}', 'Seed event for devcontainer smoke tests'
            )
        END
        """
    )

print("[post-create] Database bootstrap completed.")
PY

echo "[post-create] Completed."
