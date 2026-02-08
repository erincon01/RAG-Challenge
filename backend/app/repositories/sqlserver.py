"""
SQL Server repository implementations.

These implementations use pyodbc for database access and support
SQL Server's VECTOR type for similarity search.
"""

import pyodbc
from contextlib import contextmanager
from typing import List, Optional, Dict, Any
import logging
import urllib.parse

from app.core.config import get_settings
from app.domain.entities import (
    Match,
    EventDetail,
    SearchRequest,
    SearchResult,
    Competition,
    Season,
    Team,
    Stadium,
    Referee,
    SearchAlgorithm,
    EmbeddingModel,
)
from app.domain.exceptions import (
    DatabaseConnectionError,
    EntityNotFoundError,
)
from app.repositories.base import MatchRepository, EventRepository

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
            password_encoded = urllib.parse.quote_plus(self.password)
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

    def get_by_id(self, match_id: int) -> Optional[Match]:
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
        competition_name: Optional[str] = None,
        season_name: Optional[str] = None,
        limit: int = 100,
    ) -> List[Match]:
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

        params = [limit]

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

    def get_competitions(self) -> List[Competition]:
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
            password_encoded = urllib.parse.quote_plus(self.password)
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

    def get_events_by_match(
        self, match_id: int, limit: Optional[int] = None
    ) -> List[EventDetail]:
        """Get all events for a match."""
        if limit:
            query = """
                SELECT TOP (?)
                    id, match_id, period, minute, quarter_sec,
                    count, json_ as json_data, summary
                FROM event_details_15secs_agg
                WHERE match_id = ?
                ORDER BY period, minute, quarter_sec
            """
            params = (limit, match_id)
        else:
            query = """
                SELECT
                    id, match_id, period, minute, quarter_sec,
                    count, json_ as json_data, summary
                FROM event_details_15secs_agg
                WHERE match_id = ?
                ORDER BY period, minute, quarter_sec
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

    def get_event_by_id(self, event_id: int) -> Optional[EventDetail]:
        """Get a single event by ID."""
        query = """
            SELECT
                id, match_id, period, minute, quarter_sec,
                count, json_ as json_data, summary
            FROM event_details_15secs_agg
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
        self, search_request: SearchRequest, query_embedding: List[float]
    ) -> List[SearchResult]:
        """
        Search events using vector similarity.

        Note: SQL Server uses VECTOR_DISTANCE function for similarity search.
        """
        # Map embedding model to column name
        embedding_column_map = {
            EmbeddingModel.ADA_002: "embedding_ada_002",
            EmbeddingModel.T3_SMALL: "embedding_3_small",
            EmbeddingModel.T3_LARGE: "embedding_3_large",
        }

        # Map search algorithm to SQL Server distance type
        distance_type_map = {
            SearchAlgorithm.COSINE: "cosine",
            SearchAlgorithm.INNER_PRODUCT: "dot",  # Not directly supported, use cosine
            SearchAlgorithm.L2_EUCLIDEAN: "euclidean",
        }

        embedding_column = embedding_column_map.get(search_request.embedding_model)
        distance_type = distance_type_map.get(
            search_request.search_algorithm, "cosine"
        )

        if not embedding_column:
            raise ValueError(
                f"Unsupported embedding model for SQL Server: {search_request.embedding_model}"
            )

        # Convert embedding to SQL Server format (comma-separated string in brackets)
        embedding_str = "[" + ",".join(map(str, query_embedding)) + "]"

        query = f"""
            SELECT TOP (?)
                id, match_id, period, minute, quarter_sec,
                count, json_ as json_data, summary,
                VECTOR_DISTANCE('{distance_type}', {embedding_column}, CAST(? AS VECTOR(1536))) AS similarity_score
            FROM event_details_15secs_agg
            WHERE match_id = ?
              AND {embedding_column} IS NOT NULL
            ORDER BY similarity_score
        """

        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
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
            quarter_minute=row.quarter_sec,  # SQL Server uses quarter_sec
            count=row.count,
            json_data=row.json_data if hasattr(row, "json_data") else None,
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
