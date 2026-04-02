"""Data explorer service for teams, players and table metadata."""

from __future__ import annotations

from contextlib import contextmanager
from typing import Any

import psycopg2
import pyodbc

from app.core.capabilities import normalize_source
from app.core.config import get_settings


class DataExplorerService:
    """Read-only service for operational data exploration endpoints."""

    def __init__(self):
        self.settings = get_settings()

    @contextmanager
    def _get_connection(self, source: str):
        src = normalize_source(source)
        conn = None
        try:
            if src == "postgres":
                conn = psycopg2.connect(
                    host=self.settings.database.postgres_host,
                    database=self.settings.database.postgres_database,
                    user=self.settings.database.postgres_user,
                    password=self.settings.database.postgres_password,
                )
            elif src == "sqlserver":
                conn = pyodbc.connect(
                    "DRIVER={ODBC Driver 18 for SQL Server};"
                    f"SERVER={self.settings.database.sqlserver_host};"
                    f"DATABASE={self.settings.database.sqlserver_database};"
                    f"UID={self.settings.database.sqlserver_user};"
                    f"PWD={self.settings.database.sqlserver_password};"
                    "TrustServerCertificate=yes;"
                )
            else:
                raise ValueError(f"Unsupported source: {source}")
            yield conn
        finally:
            if conn:
                conn.close()

    def get_teams(self, source: str, match_id: int | None = None, limit: int = 500) -> list[dict[str, Any]]:
        src = normalize_source(source)
        with self._get_connection(src) as conn:
            cur = conn.cursor()

            if src == "postgres":
                params: list[Any] = []
                where_clause = ""
                if match_id is not None:
                    where_clause = "WHERE match_id = %s"
                    params.append(match_id)

                query = f"""
                    SELECT team_id, name, gender, country
                    FROM (
                        SELECT home_team_id AS team_id, home_team_name AS name, home_team_gender AS gender, home_team_country AS country
                        FROM matches
                        {where_clause}
                        UNION
                        SELECT away_team_id AS team_id, away_team_name AS name, away_team_gender AS gender, away_team_country AS country
                        FROM matches
                        {where_clause}
                    ) t
                    ORDER BY name
                    LIMIT %s
                """
                if match_id is not None:
                    params.extend([match_id])
                params.append(limit)
                cur.execute(query, tuple(params))
            else:
                params = []
                where_clause = ""
                if match_id is not None:
                    where_clause = "WHERE match_id = ?"
                    params.append(match_id)

                query = f"""
                    SELECT TOP (?) team_id, name, gender, country
                    FROM (
                        SELECT home_team_id AS team_id, home_team_name AS name, home_team_gender AS gender, home_team_country AS country
                        FROM matches
                        {where_clause}
                        UNION
                        SELECT away_team_id AS team_id, away_team_name AS name, away_team_gender AS gender, away_team_country AS country
                        FROM matches
                        {where_clause}
                    ) t
                    ORDER BY name
                """
                args: list[Any] = [limit]
                args.extend(params)
                if match_id is not None:
                    args.extend([match_id])
                cur.execute(query, tuple(args))

            rows = cur.fetchall()
            return [
                {
                    "team_id": int(row[0]),
                    "name": row[1],
                    "gender": row[2],
                    "country": row[3],
                }
                for row in rows
                if row[0] is not None
            ]

    def _table_exists(self, conn, source: str, table_name: str) -> bool:
        src = normalize_source(source)
        cur = conn.cursor()
        if src == "postgres":
            cur.execute(
                """
                SELECT 1
                FROM information_schema.tables
                WHERE table_schema = 'public' AND table_name = %s
                """,
                (table_name,),
            )
        else:
            cur.execute(
                """
                SELECT 1
                FROM sys.tables
                WHERE name = ?
                """,
                (table_name,),
            )
        return cur.fetchone() is not None

    def get_players(self, source: str, match_id: int | None = None, limit: int = 500) -> list[dict[str, Any]]:
        src = normalize_source(source)
        with self._get_connection(src) as conn:
            if not self._table_exists(conn, src, "players"):
                return []

            cur = conn.cursor()
            if src == "postgres":
                if match_id is not None:
                    cur.execute(
                        """
                        SELECT player_id, player_name, jersey_number, country_name, position_name, team_name
                        FROM players
                        WHERE match_id = %s
                        ORDER BY player_name
                        LIMIT %s
                        """,
                        (match_id, limit),
                    )
                else:
                    cur.execute(
                        """
                        SELECT player_id, player_name, jersey_number, country_name, position_name, team_name
                        FROM players
                        ORDER BY player_name
                        LIMIT %s
                        """,
                        (limit,),
                    )
            else:
                if match_id is not None:
                    cur.execute(
                        """
                        SELECT TOP (?) player_id, player_name, jersey_number, country_name, position_name, team_name
                        FROM players
                        WHERE match_id = ?
                        ORDER BY player_name
                        """,
                        (limit, match_id),
                    )
                else:
                    cur.execute(
                        """
                        SELECT TOP (?) player_id, player_name, jersey_number, country_name, position_name, team_name
                        FROM players
                        ORDER BY player_name
                        """,
                        (limit,),
                    )

            rows = cur.fetchall()
            return [
                {
                    "player_id": int(row[0]),
                    "player_name": row[1],
                    "jersey_number": row[2],
                    "country_name": row[3],
                    "position_name": row[4],
                    "team_name": row[5],
                }
                for row in rows
                if row[0] is not None
            ]

    def get_tables_info(self, source: str) -> list[dict[str, Any]]:
        src = normalize_source(source)
        with self._get_connection(src) as conn:
            cur = conn.cursor()

            if src == "postgres":
                cur.execute(
                    """
                    SELECT table_name
                    FROM information_schema.tables
                    WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
                    ORDER BY table_name
                    """
                )
                table_names = [r[0] for r in cur.fetchall()]

                cur.execute(
                    """
                    SELECT table_name, column_name
                    FROM information_schema.columns
                    WHERE table_schema = 'public'
                      AND (
                        udt_name = 'vector'
                        OR column_name LIKE '%embedding%'
                      )
                    ORDER BY table_name, column_name
                    """
                )
            else:
                cur.execute(
                    """
                    SELECT name
                    FROM sys.tables
                    ORDER BY name
                    """
                )
                table_names = [r[0] for r in cur.fetchall()]

                cur.execute(
                    """
                    SELECT t.name, c.name
                    FROM sys.columns c
                    JOIN sys.tables t ON c.object_id = t.object_id
                    LEFT JOIN sys.types ty ON c.user_type_id = ty.user_type_id
                    WHERE ty.name = 'vector' OR c.name LIKE '%embedding%'
                    ORDER BY t.name, c.name
                    """
                )

            embedding_map: dict[str, list[str]] = {}
            for table_name, column_name in cur.fetchall():
                embedding_map.setdefault(table_name, []).append(column_name)

            info: list[dict[str, Any]] = []
            for table_name in table_names:
                count_cursor = conn.cursor()
                if src == "postgres":
                    count_cursor.execute(f'SELECT COUNT(*) FROM "{table_name}"')
                else:
                    count_cursor.execute(f"SELECT COUNT(*) FROM [{table_name}]")
                row_count = int(count_cursor.fetchone()[0] or 0)

                info.append(
                    {
                        "table": table_name,
                        "row_count": row_count,
                        "embedding_columns": embedding_map.get(table_name, []),
                    }
                )

            return info
