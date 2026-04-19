"""
SQL Server repository implementations.

These implementations use pyodbc for database access and support
SQL Server's VECTOR type for similarity search.
"""

import logging
from contextlib import contextmanager
from typing import Any

import pyodbc

from app.core.config import get_settings
from app.domain.entities import (
    Competition,
    EmbeddingModel,
    EventDetail,
    Match,
    Referee,
    SearchAlgorithm,
    SearchRequest,
    SearchResult,
    Season,
    Stadium,
    Team,
)
from app.domain.exceptions import DatabaseConnectionError
from app.repositories.base import EventRepository, MatchRepository

logger = logging.getLogger(__name__)
settings = get_settings()


class SQLServerMatchRepository(MatchRepository):
    """SQL Server implementation of MatchRepository."""

    def __init__(self):
        """Initialize repository with database configuration."""
        self.server = settings.database.sqlserver_host
        self.database = settings.database.sqlserver_database
        self.username = settings.database.sqlserver_user
        self.password = settings.database.sqlserver_password

    @contextmanager
    def get_connection(self):
        """Get a SQL Server database connection."""
        conn = None
        try:
            connection_string = (
                f"DRIVER={{ODBC Driver 18 for SQL Server}};"
                f"SERVER={self.server};"
                f"DATABASE={self.database};"
                f"UID={self.username};"
                f"PWD={self.password};"
                f"TrustServerCertificate=yes;"
            )

            conn = pyodbc.connect(connection_string)
            yield conn
            conn.commit()
        except pyodbc.Error as e:
            if conn:
                conn.rollback()
            logger.error(f"Database error: {e}")
            raise DatabaseConnectionError(f"Failed to connect to SQL Server: {e}")
        finally:
            if conn:
                conn.close()

    def test_connection(self) -> bool:
        """Test if database connection is working."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                return True
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False

    def get_by_id(self, match_id: int) -> Match | None:
        """Get a match by ID."""
        query = """
            SELECT
                match_id, match_date,
                competition_id, competition_country, competition_name,
                season_id, season_name,
                home_team_id, home_team_name, home_team_gender, home_team_country,
                home_team_manager, home_team_manager_country,
                away_team_id, away_team_name, away_team_gender, away_team_country,
                away_team_manager, away_team_manager_country,
                home_score, away_score, result, match_week,
                stadium_id, stadium_name, stadium_country,
                referee_id, referee_name, referee_country,
                json_ as json_data
            FROM matches
            WHERE match_id = ?
        """

        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, (match_id,))
                row = cursor.fetchone()

                if not row:
                    return None

                return self._row_to_match(row)
        except Exception as e:
            logger.error(f"Error fetching match {match_id}: {e}")
            raise

    def get_all(
        self,
        competition_name: str | None = None,
        season_name: str | None = None,
        limit: int = 100,
    ) -> list[Match]:
        """Get all matches with optional filters."""
        query = """
            SELECT TOP (?)
                match_id, match_date,
                competition_id, competition_country, competition_name,
                season_id, season_name,
                home_team_id, home_team_name, home_team_gender, home_team_country,
                home_team_manager, home_team_manager_country,
                away_team_id, away_team_name, away_team_gender, away_team_country,
                away_team_manager, away_team_manager_country,
                home_score, away_score, result, match_week,
                stadium_id, stadium_name, stadium_country,
                referee_id, referee_name, referee_country,
                json_ as json_data
            FROM matches
            WHERE 1=1
        """

        params: list = [limit]

        if competition_name:
            query += " AND competition_name = ?"
            params.insert(1, competition_name)

        if season_name:
            query += " AND season_name = ?"
            params.insert(2 if competition_name else 1, season_name)

        query += " ORDER BY match_date DESC"

        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)
                rows = cursor.fetchall()
                return [self._row_to_match(row) for row in rows]
        except Exception as e:
            logger.error(f"Error fetching matches: {e}")
            raise

    def get_competitions(self) -> list[Competition]:
        """Get all unique competitions."""
        query = """
            SELECT DISTINCT
                competition_id,
                competition_country,
                competition_name
            FROM matches
            ORDER BY competition_name
        """

        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query)
                rows = cursor.fetchall()
                return [
                    Competition(
                        competition_id=row.competition_id,
                        country=row.competition_country,
                        name=row.competition_name,
                    )
                    for row in rows
                ]
        except Exception as e:
            logger.error(f"Error fetching competitions: {e}")
            raise

    def get_teams(
        self, match_id: int | None = None, limit: int = 500
    ) -> list[dict[str, Any]]:
        """Get team metadata from matches."""
        params: list[Any] = []
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

        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, tuple(args))
                rows = cursor.fetchall()
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
        except Exception as e:
            logger.error(f"Error fetching teams: {e}")
            raise

    def get_players(
        self, match_id: int | None = None, limit: int = 500
    ) -> list[dict[str, Any]]:
        """Get player roster data."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT 1
                    FROM sys.tables
                    WHERE name = ?
                    """,
                    ("players",),
                )
                if cursor.fetchone() is None:
                    return []

            with self.get_connection() as conn:
                cursor = conn.cursor()
                if match_id is not None:
                    cursor.execute(
                        """
                        SELECT TOP (?) player_id, player_name, jersey_number, country_name, position_name, team_name
                        FROM players
                        WHERE match_id = ?
                        ORDER BY player_name
                        """,
                        (limit, match_id),
                    )
                else:
                    cursor.execute(
                        """
                        SELECT TOP (?) player_id, player_name, jersey_number, country_name, position_name, team_name
                        FROM players
                        ORDER BY player_name
                        """,
                        (limit,),
                    )
                rows = cursor.fetchall()
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
        except Exception as e:
            logger.error(f"Error fetching players: {e}")
            raise

    def get_tables_info(self) -> list[dict[str, Any]]:
        """Get table metadata for SQL Server."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT name
                    FROM sys.tables
                    ORDER BY name
                    """
                )
                table_names = [r[0] for r in cursor.fetchall()]

                cursor.execute(
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
                for table_name, column_name in cursor.fetchall():
                    embedding_map.setdefault(table_name, []).append(column_name)

                info: list[dict[str, Any]] = []
                for table_name in table_names:
                    cursor.execute(f"SELECT COUNT(*) FROM [{table_name}]")
                    row_count = int(cursor.fetchone()[0] or 0)

                    info.append(
                        {
                            "table": table_name,
                            "row_count": row_count,
                            "embedding_columns": embedding_map.get(table_name, []),
                        }
                    )

                return info
        except Exception as e:
            logger.error(f"Error fetching tables info: {e}")
            raise

    def _row_to_match(self, row) -> Match:
        """Convert database row to Match entity."""
        competition = Competition(
            competition_id=row.competition_id,
            country=row.competition_country,
            name=row.competition_name,
        )

        season = Season(season_id=row.season_id, name=row.season_name)

        home_team = Team(
            team_id=row.home_team_id,
            name=row.home_team_name,
            gender=row.home_team_gender,
            country=row.home_team_country,
            manager=row.home_team_manager,
            manager_country=row.home_team_manager_country,
        )

        away_team = Team(
            team_id=row.away_team_id,
            name=row.away_team_name,
            gender=row.away_team_gender,
            country=row.away_team_country,
            manager=row.away_team_manager,
            manager_country=row.away_team_manager_country,
        )

        stadium = None
        if row.stadium_id:
            stadium = Stadium(
                stadium_id=row.stadium_id,
                name=row.stadium_name,
                country=row.stadium_country,
            )

        referee = None
        if row.referee_id:
            referee = Referee(
                referee_id=row.referee_id,
                name=row.referee_name,
                country=row.referee_country,
            )

        return Match(
            match_id=row.match_id,
            match_date=row.match_date,
            competition=competition,
            season=season,
            home_team=home_team,
            away_team=away_team,
            home_score=row.home_score,
            away_score=row.away_score,
            result=row.result,
            match_week=row.match_week,
            stadium=stadium,
            referee=referee,
            json_data=row.json_data if hasattr(row, "json_data") else None,
        )


class SQLServerEventRepository(EventRepository):
    """SQL Server implementation of EventRepository."""

    def __init__(self):
        """Initialize repository with database configuration."""
        self.server = settings.database.sqlserver_host
        self.database = settings.database.sqlserver_database
        self.username = settings.database.sqlserver_user
        self.password = settings.database.sqlserver_password

    @contextmanager
    def get_connection(self):
        """Get a SQL Server database connection."""
        conn = None
        try:
            connection_string = (
                f"DRIVER={{ODBC Driver 18 for SQL Server}};"
                f"SERVER={self.server};"
                f"DATABASE={self.database};"
                f"UID={self.username};"
                f"PWD={self.password};"
                f"TrustServerCertificate=yes;"
            )

            conn = pyodbc.connect(connection_string)
            yield conn
            conn.commit()
        except pyodbc.Error as e:
            if conn:
                conn.rollback()
            logger.error(f"Database error: {e}")
            raise DatabaseConnectionError(f"Failed to connect to SQL Server: {e}")
        finally:
            if conn:
                conn.close()

    def test_connection(self) -> bool:
        """Test if database connection is working."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                return True
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False

    def get_tables_info(self) -> list[dict[str, Any]]:
        """Get table metadata for SQL Server."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT name
                    FROM sys.tables
                    ORDER BY name
                    """
                )
                table_names = [r[0] for r in cursor.fetchall()]

                cursor.execute(
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
                for table_name, column_name in cursor.fetchall():
                    embedding_map.setdefault(table_name, []).append(column_name)

                info: list[dict[str, Any]] = []
                for table_name in table_names:
                    cursor.execute(f"SELECT COUNT(*) FROM [{table_name}]")
                    row_count = int(cursor.fetchone()[0] or 0)

                    info.append(
                        {
                            "table": table_name,
                            "row_count": row_count,
                            "embedding_columns": embedding_map.get(table_name, []),
                        }
                    )

                return info
        except Exception as e:
            logger.error(f"Error fetching tables info: {e}")
            raise

    def get_events_by_match(
        self, match_id: int, limit: int | None = None
    ) -> list[EventDetail]:
        """Get all events for a match."""
        params: tuple
        if limit:
            query = """
                SELECT TOP (?)
                    id, match_id, period, minute, [_15secs] AS quarter_minute,
                    count, json_ as json_data, summary
                FROM events_details__15secs_agg
                WHERE match_id = ?
                ORDER BY period, minute, [_15secs]
            """
            params = (limit, match_id)
        else:
            query = """
                SELECT
                    id, match_id, period, minute, [_15secs] AS quarter_minute,
                    count, json_ as json_data, summary
                FROM events_details__15secs_agg
                WHERE match_id = ?
                ORDER BY period, minute, [_15secs]
            """
            params = (match_id,)

        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)
                rows = cursor.fetchall()
                return [self._row_to_event(row) for row in rows]
        except Exception as e:
            logger.error(f"Error fetching events for match {match_id}: {e}")
            raise

    def get_event_by_id(self, event_id: int) -> EventDetail | None:
        """Get a single event by ID."""
        query = """
            SELECT
                id, match_id, period, minute, [_15secs] AS quarter_minute,
                count, json_ as json_data, summary
            FROM events_details__15secs_agg
            WHERE id = ?
        """

        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, (event_id,))
                row = cursor.fetchone()

                if not row:
                    return None

                return self._row_to_event(row)
        except Exception as e:
            logger.error(f"Error fetching event {event_id}: {e}")
            raise

    def search_by_embedding(
        self, search_request: SearchRequest, query_embedding: list[float]
    ) -> list[SearchResult]:
        """
        Search events using vector similarity.

        Note: SQL Server uses VECTOR_DISTANCE function for similarity search.
        """
        embedding_column_map = {
            EmbeddingModel.ADA_002: "embedding_ada_002",
            EmbeddingModel.T3_SMALL: "embedding_3_small",
        }

        distance_type_map = {
            SearchAlgorithm.COSINE: "cosine",
            SearchAlgorithm.INNER_PRODUCT: "dot",
            SearchAlgorithm.L2_EUCLIDEAN: "euclidean",
        }

        embedding_column = embedding_column_map.get(search_request.embedding_model)
        distance_type = distance_type_map.get(search_request.search_algorithm)

        if not embedding_column:
            raise ValueError(
                f"Unsupported embedding model for SQL Server: {search_request.embedding_model}"
            )
        if not distance_type:
            raise ValueError(
                f"Unsupported search algorithm for SQL Server: {search_request.search_algorithm}"
            )

        embedding_str = "[" + ",".join(map(str, query_embedding)) + "]"

        query = f"""
            SELECT TOP (?)
                id, match_id, period, minute, [_15secs] AS quarter_minute,
                count, json_ as json_data, summary,
                VECTOR_DISTANCE('{distance_type}', {embedding_column}, CAST(? AS VECTOR(1536))) AS similarity_score
            FROM events_details__15secs_agg
            WHERE match_id = ?
              AND {embedding_column} IS NOT NULL
            ORDER BY similarity_score
        """

        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                # pyodbc promotes long strings (>4000 chars) to ntext,
                # which SQL Server cannot CAST to VECTOR. Force VARCHAR.
                cursor.setinputsizes(
                    [
                        (pyodbc.SQL_INTEGER, 0, 0),
                        (pyodbc.SQL_VARCHAR, 0, 0),
                        (pyodbc.SQL_INTEGER, 0, 0),
                    ]
                )
                cursor.execute(
                    query,
                    (search_request.top_n, embedding_str, search_request.match_id),
                )
                rows = cursor.fetchall()

                results = []
                for rank, row in enumerate(rows, start=1):
                    event = self._row_to_event(row)
                    results.append(
                        SearchResult(
                            event=event,
                            similarity_score=float(row.similarity_score),
                            rank=rank,
                        )
                    )

                return results
        except Exception as e:
            logger.error(f"Error searching events: {e}")
            raise

    def _row_to_event(self, row) -> EventDetail:
        """Convert database row to EventDetail entity."""
        return EventDetail(
            id=row.id,
            match_id=row.match_id,
            period=row.period,
            minute=row.minute,
            quarter_minute=row.quarter_minute,
            count=row.count,
            json_data=row.json_data
            if hasattr(row, "json_data") and row.json_data is not None
            else "",
            summary=row.summary if hasattr(row, "summary") else None,
        )


class SQLServerRepositoryFactory:
    """Factory for creating SQL Server repository instances."""

    def create_match_repository(self) -> MatchRepository:
        """Create a SQL Server match repository instance."""
        return SQLServerMatchRepository()

    def create_event_repository(self) -> EventRepository:
        """Create a SQL Server event repository instance."""
        return SQLServerEventRepository()
