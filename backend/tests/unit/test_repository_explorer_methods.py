"""Unit tests for repository get_teams, get_players, get_tables_info methods."""

from contextlib import contextmanager
from unittest.mock import MagicMock, patch

import pytest

from app.repositories.postgres import PostgresMatchRepository, PostgresEventRepository
from app.repositories.sqlserver import SQLServerMatchRepository, SQLServerEventRepository


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

@contextmanager
def _mock_pg_connection(rows, fetchall_sequence=None):
    """Create a mock Postgres connection context with cursor returning rows."""
    cursor = MagicMock()
    if fetchall_sequence is not None:
        cursor.fetchall = MagicMock(side_effect=fetchall_sequence)
    else:
        cursor.fetchall.return_value = rows
    cursor.fetchone.return_value = rows[0] if rows else None
    cursor.__enter__ = MagicMock(return_value=cursor)
    cursor.__exit__ = MagicMock(return_value=False)

    conn = MagicMock()
    conn.cursor.return_value = cursor
    conn.__enter__ = MagicMock(return_value=conn)
    conn.__exit__ = MagicMock(return_value=False)
    yield conn, cursor


@contextmanager
def _mock_sql_connection(rows, fetchall_sequence=None):
    """Create a mock SQL Server connection context with cursor returning rows."""
    cursor = MagicMock()
    if fetchall_sequence is not None:
        cursor.fetchall = MagicMock(side_effect=fetchall_sequence)
    else:
        cursor.fetchall.return_value = rows
    cursor.fetchone.return_value = rows[0] if rows else None
    cursor.__enter__ = MagicMock(return_value=cursor)
    cursor.__exit__ = MagicMock(return_value=False)

    conn = MagicMock()
    conn.cursor.return_value = cursor
    conn.__enter__ = MagicMock(return_value=conn)
    conn.__exit__ = MagicMock(return_value=False)
    yield conn, cursor


# ---------------------------------------------------------------------------
# PostgresMatchRepository — get_teams
# ---------------------------------------------------------------------------

class TestPostgresGetTeams:
    def test_get_teams_returns_list_of_dicts(self):
        repo = PostgresMatchRepository.__new__(PostgresMatchRepository)
        rows = [(1, "Spain", "male", "Spain"), (2, "England", "male", "England")]
        with _mock_pg_connection(rows) as (conn, _):
            repo.get_connection = MagicMock(return_value=contextmanager(lambda: (yield conn))())
            result = repo.get_teams()
        assert len(result) == 2
        assert result[0]["team_id"] == 1
        assert result[0]["name"] == "Spain"

    def test_get_teams_filters_none_rows(self):
        repo = PostgresMatchRepository.__new__(PostgresMatchRepository)
        rows = [(1, "Spain", "male", "Spain"), (None, None, None, None)]
        with _mock_pg_connection(rows) as (conn, _):
            repo.get_connection = MagicMock(return_value=contextmanager(lambda: (yield conn))())
            result = repo.get_teams()
        assert len(result) == 1

    def test_get_teams_with_match_id_filter(self):
        repo = PostgresMatchRepository.__new__(PostgresMatchRepository)
        rows = [(1, "Spain", "male", "Spain")]
        with _mock_pg_connection(rows) as (conn, cursor):
            repo.get_connection = MagicMock(return_value=contextmanager(lambda: (yield conn))())
            result = repo.get_teams(match_id=123)
        assert len(result) == 1
        assert cursor.execute.called


# ---------------------------------------------------------------------------
# PostgresMatchRepository — get_players
# ---------------------------------------------------------------------------

class TestPostgresGetPlayers:
    def test_get_players_returns_list_when_table_exists(self):
        repo = PostgresMatchRepository.__new__(PostgresMatchRepository)
        table_check_row = (1,)
        player_rows = [(10, "Pedri", 8, "Spain", "Midfielder", "Spain")]

        call_count = [0]
        conns = []

        def make_conn(fetchone_val, fetchall_val):
            cursor = MagicMock()
            cursor.fetchone.return_value = fetchone_val
            cursor.fetchall.return_value = fetchall_val
            cursor.__enter__ = MagicMock(return_value=cursor)
            cursor.__exit__ = MagicMock(return_value=False)
            c = MagicMock()
            c.cursor.return_value = cursor
            c.__enter__ = MagicMock(return_value=c)
            c.__exit__ = MagicMock(return_value=False)
            return c

        conn1 = make_conn(table_check_row, [])
        conn2 = make_conn(None, player_rows)

        def get_conn_side_effect():
            call_count[0] += 1
            if call_count[0] == 1:
                return contextmanager(lambda: (yield conn1))()
            return contextmanager(lambda: (yield conn2))()

        repo.get_connection = MagicMock(side_effect=get_conn_side_effect)
        result = repo.get_players()
        assert len(result) == 1
        assert result[0]["player_name"] == "Pedri"

    def test_get_players_returns_empty_when_table_missing(self):
        repo = PostgresMatchRepository.__new__(PostgresMatchRepository)
        cursor = MagicMock()
        cursor.fetchone.return_value = None
        cursor.__enter__ = MagicMock(return_value=cursor)
        cursor.__exit__ = MagicMock(return_value=False)
        conn = MagicMock()
        conn.cursor.return_value = cursor
        conn.__enter__ = MagicMock(return_value=conn)
        conn.__exit__ = MagicMock(return_value=False)
        repo.get_connection = MagicMock(return_value=contextmanager(lambda: (yield conn))())
        result = repo.get_players()
        assert result == []


# ---------------------------------------------------------------------------
# PostgresMatchRepository — get_tables_info
# ---------------------------------------------------------------------------

class TestPostgresGetTablesInfo:
    def test_get_tables_info_returns_table_metadata(self):
        repo = PostgresMatchRepository.__new__(PostgresMatchRepository)

        cursor = MagicMock()
        call_count = [0]

        def fetchall_side_effect():
            call_count[0] += 1
            if call_count[0] == 1:
                return [("matches",), ("events",)]
            elif call_count[0] == 2:
                return [("events", "embedding")]
            return []

        def fetchone_side_effect():
            return (42,)

        cursor.fetchall = MagicMock(side_effect=fetchall_side_effect)
        cursor.fetchone = MagicMock(side_effect=fetchone_side_effect)
        cursor.__enter__ = MagicMock(return_value=cursor)
        cursor.__exit__ = MagicMock(return_value=False)
        conn = MagicMock()
        conn.cursor.return_value = cursor
        conn.__enter__ = MagicMock(return_value=conn)
        conn.__exit__ = MagicMock(return_value=False)
        repo.get_connection = MagicMock(return_value=contextmanager(lambda: (yield conn))())
        result = repo.get_tables_info()
        assert len(result) == 2
        assert result[0]["table"] == "matches"
        assert result[0]["row_count"] == 42
        assert result[1]["embedding_columns"] == ["embedding"]


# ---------------------------------------------------------------------------
# SQLServerMatchRepository — get_teams
# ---------------------------------------------------------------------------

class TestSQLServerGetTeams:
    def test_get_teams_returns_list_of_dicts(self):
        repo = SQLServerMatchRepository.__new__(SQLServerMatchRepository)
        rows = [(1, "Spain", "male", "Spain"), (2, "England", "male", "England")]
        with _mock_sql_connection(rows) as (conn, _):
            repo.get_connection = MagicMock(return_value=contextmanager(lambda: (yield conn))())
            result = repo.get_teams()
        assert len(result) == 2
        assert result[0]["name"] == "Spain"

    def test_get_teams_with_match_id_filter(self):
        repo = SQLServerMatchRepository.__new__(SQLServerMatchRepository)
        rows = [(1, "Spain", "male", "Spain")]
        with _mock_sql_connection(rows) as (conn, cursor):
            repo.get_connection = MagicMock(return_value=contextmanager(lambda: (yield conn))())
            result = repo.get_teams(match_id=456)
        assert len(result) == 1


# ---------------------------------------------------------------------------
# SQLServerMatchRepository — get_players
# ---------------------------------------------------------------------------

class TestSQLServerGetPlayers:
    def test_get_players_returns_list_when_table_exists(self):
        repo = SQLServerMatchRepository.__new__(SQLServerMatchRepository)
        player_rows = [(10, "Pedri", 8, "Spain", "Midfielder", "Spain")]

        call_count = [0]

        def make_conn(fetchone_val, fetchall_val):
            cursor = MagicMock()
            cursor.fetchone.return_value = fetchone_val
            cursor.fetchall.return_value = fetchall_val
            cursor.__enter__ = MagicMock(return_value=cursor)
            cursor.__exit__ = MagicMock(return_value=False)
            c = MagicMock()
            c.cursor.return_value = cursor
            c.__enter__ = MagicMock(return_value=c)
            c.__exit__ = MagicMock(return_value=False)
            return c

        conn1 = make_conn((1,), [])
        conn2 = make_conn(None, player_rows)

        def get_conn_side_effect():
            call_count[0] += 1
            if call_count[0] == 1:
                return contextmanager(lambda: (yield conn1))()
            return contextmanager(lambda: (yield conn2))()

        repo.get_connection = MagicMock(side_effect=get_conn_side_effect)
        result = repo.get_players()
        assert len(result) == 1
        assert result[0]["player_name"] == "Pedri"

    def test_get_players_returns_empty_when_table_missing(self):
        repo = SQLServerMatchRepository.__new__(SQLServerMatchRepository)
        cursor = MagicMock()
        cursor.fetchone.return_value = None
        cursor.__enter__ = MagicMock(return_value=cursor)
        cursor.__exit__ = MagicMock(return_value=False)
        conn = MagicMock()
        conn.cursor.return_value = cursor
        conn.__enter__ = MagicMock(return_value=conn)
        conn.__exit__ = MagicMock(return_value=False)
        repo.get_connection = MagicMock(return_value=contextmanager(lambda: (yield conn))())
        result = repo.get_players()
        assert result == []


# ---------------------------------------------------------------------------
# SQLServerMatchRepository — get_tables_info
# ---------------------------------------------------------------------------

class TestSQLServerGetTablesInfo:
    def test_get_tables_info_returns_table_metadata(self):
        repo = SQLServerMatchRepository.__new__(SQLServerMatchRepository)

        cursor = MagicMock()
        call_count = [0]

        def fetchall_side_effect():
            call_count[0] += 1
            if call_count[0] == 1:
                return [("matches",), ("events",)]
            elif call_count[0] == 2:
                return [("events", "embedding")]
            return []

        cursor.fetchall = MagicMock(side_effect=fetchall_side_effect)
        cursor.fetchone = MagicMock(return_value=(42,))
        cursor.__enter__ = MagicMock(return_value=cursor)
        cursor.__exit__ = MagicMock(return_value=False)
        conn = MagicMock()
        conn.cursor.return_value = cursor
        conn.__enter__ = MagicMock(return_value=conn)
        conn.__exit__ = MagicMock(return_value=False)
        repo.get_connection = MagicMock(return_value=contextmanager(lambda: (yield conn))())
        result = repo.get_tables_info()
        assert len(result) == 2
        assert result[0]["table"] == "matches"
        assert result[0]["row_count"] == 42


# ---------------------------------------------------------------------------
# EventRepository — get_tables_info (both implementations)
# ---------------------------------------------------------------------------

class TestEventRepoGetTablesInfo:
    def test_postgres_event_repo_get_tables_info(self):
        repo = PostgresEventRepository.__new__(PostgresEventRepository)
        cursor = MagicMock()
        cursor.fetchall = MagicMock(side_effect=[
            [("events",)],
            [],
        ])
        cursor.fetchone = MagicMock(return_value=(10,))
        cursor.__enter__ = MagicMock(return_value=cursor)
        cursor.__exit__ = MagicMock(return_value=False)
        conn = MagicMock()
        conn.cursor.return_value = cursor
        conn.__enter__ = MagicMock(return_value=conn)
        conn.__exit__ = MagicMock(return_value=False)
        repo.get_connection = MagicMock(return_value=contextmanager(lambda: (yield conn))())
        result = repo.get_tables_info()
        assert len(result) == 1
        assert result[0]["table"] == "events"

    def test_sqlserver_event_repo_get_tables_info(self):
        repo = SQLServerEventRepository.__new__(SQLServerEventRepository)
        cursor = MagicMock()
        cursor.fetchall = MagicMock(side_effect=[
            [("events",)],
            [],
        ])
        cursor.fetchone = MagicMock(return_value=(10,))
        cursor.__enter__ = MagicMock(return_value=cursor)
        cursor.__exit__ = MagicMock(return_value=False)
        conn = MagicMock()
        conn.cursor.return_value = cursor
        conn.__enter__ = MagicMock(return_value=conn)
        conn.__exit__ = MagicMock(return_value=False)
        repo.get_connection = MagicMock(return_value=contextmanager(lambda: (yield conn))())
        result = repo.get_tables_info()
        assert len(result) == 1
