"""
PostgreSQL repository implementations.

These implementations use psycopg2 for database access and support pgvector
for similarity search.
"""

import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager
from typing import List, Optional, Dict, Any
import logging

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


class PostgresMatchRepository(MatchRepository):
    """PostgreSQL implementation of MatchRepository."""

    def __init__(self):
        """Initialize repository with database configuration."""
        self.db_config = {
            "host": settings.database.postgres_host,
            "database": settings.database.postgres_database,
            "user": settings.database.postgres_user,
            "password": settings.database.postgres_password,
        }

    @contextmanager
    def get_connection(self):
        """Get a PostgreSQL database connection."""
        conn = None
        try:
            conn = psycopg2.connect(**self.db_config)
            yield conn
            conn.commit()
        except psycopg2.Error as e:
            if conn:
                conn.rollback()
            logger.error(f"Database error: {e}")
            raise DatabaseConnectionError(f"Failed to connect to PostgreSQL: {e}")
        finally:
            if conn:
                conn.close()

    def test_connection(self) -> bool:
        """Test if database connection is working."""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT 1")
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
            WHERE match_id = %s
        """

        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute(query, (match_id,))
                    row = cur.fetchone()

                    if not row:
                        return None

                    return self._row_to_match(dict(row))
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
            WHERE 1=1
        """

        params = []

        if competition_name:
            query += " AND competition_name = %s"
            params.append(competition_name)

        if season_name:
            query += " AND season_name = %s"
            params.append(season_name)

        query += " ORDER BY match_date DESC LIMIT %s"
        params.append(limit)

        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute(query, params)
                    rows = cur.fetchall()
                    return [self._row_to_match(dict(row)) for row in rows]
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
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute(query)
                    rows = cur.fetchall()
                    return [
                        Competition(
                            competition_id=row["competition_id"],
                            country=row["competition_country"],
                            name=row["competition_name"],
                        )
                        for row in rows
                    ]
        except Exception as e:
            logger.error(f"Error fetching competitions: {e}")
            raise

    def _row_to_match(self, row: Dict[str, Any]) -> Match:
        """Convert database row to Match entity."""
        competition = Competition(
            competition_id=row["competition_id"],
            country=row["competition_country"],
            name=row["competition_name"],
        )

        season = Season(season_id=row["season_id"], name=row["season_name"])

        home_team = Team(
            team_id=row["home_team_id"],
            name=row["home_team_name"],
            gender=row["home_team_gender"],
            country=row["home_team_country"],
            manager=row.get("home_team_manager"),
            manager_country=row.get("home_team_manager_country"),
        )

        away_team = Team(
            team_id=row["away_team_id"],
            name=row["away_team_name"],
            gender=row["away_team_gender"],
            country=row["away_team_country"],
            manager=row.get("away_team_manager"),
            manager_country=row.get("away_team_manager_country"),
        )

        stadium = None
        if row.get("stadium_id"):
            stadium = Stadium(
                stadium_id=row["stadium_id"],
                name=row["stadium_name"],
                country=row["stadium_country"],
            )

        referee = None
        if row.get("referee_id"):
            referee = Referee(
                referee_id=row["referee_id"],
                name=row["referee_name"],
                country=row["referee_country"],
            )

        return Match(
            match_id=row["match_id"],
            match_date=row["match_date"],
            competition=competition,
            season=season,
            home_team=home_team,
            away_team=away_team,
            home_score=row["home_score"],
            away_score=row["away_score"],
            result=row["result"],
            match_week=row.get("match_week"),
            stadium=stadium,
            referee=referee,
            json_data=row.get("json_data"),
        )


class PostgresEventRepository(EventRepository):
    """PostgreSQL implementation of EventRepository."""

    def __init__(self):
        """Initialize repository with database configuration."""
        self.db_config = {
            "host": settings.database.postgres_host,
            "database": settings.database.postgres_database,
            "user": settings.database.postgres_user,
            "password": settings.database.postgres_password,
        }

    @contextmanager
    def get_connection(self):
        """Get a PostgreSQL database connection."""
        conn = None
        try:
            conn = psycopg2.connect(**self.db_config)
            yield conn
            conn.commit()
        except psycopg2.Error as e:
            if conn:
                conn.rollback()
            logger.error(f"Database error: {e}")
            raise DatabaseConnectionError(f"Failed to connect to PostgreSQL: {e}")
        finally:
            if conn:
                conn.close()

    def test_connection(self) -> bool:
        """Test if database connection is working."""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT 1")
                    return True
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False

    def get_events_by_match(
        self, match_id: int, limit: Optional[int] = None
    ) -> List[EventDetail]:
        """Get all events for a match."""
        query = """
            SELECT
                id, match_id, period, minute, quarter_minute,
                count, json_ as json_data, summary
            FROM events_details__quarter_minute
            WHERE match_id = %s
            ORDER BY period, minute, quarter_minute
        """

        params = [match_id]
        if limit:
            query += " LIMIT %s"
            params.append(limit)

        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute(query, params)
                    rows = cur.fetchall()
                    return [self._row_to_event(dict(row)) for row in rows]
        except Exception as e:
            logger.error(f"Error fetching events for match {match_id}: {e}")
            raise

    def get_event_by_id(self, event_id: int) -> Optional[EventDetail]:
        """Get a single event by ID."""
        query = """
            SELECT
                id, match_id, period, minute, quarter_minute,
                count, json_ as json_data, summary
            FROM events_details__quarter_minute
            WHERE id = %s
        """

        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute(query, (event_id,))
                    row = cur.fetchone()

                    if not row:
                        return None

                    return self._row_to_event(dict(row))
        except Exception as e:
            logger.error(f"Error fetching event {event_id}: {e}")
            raise

    def search_by_embedding(
        self, search_request: SearchRequest, query_embedding: List[float]
    ) -> List[SearchResult]:
        """
        Search events using vector similarity.

        Note: This implementation uses pgvector operators for similarity search.
        """
        # Map embedding model to column name
        embedding_column_map = {
            EmbeddingModel.ADA_002: "summary_embedding_ada_002",
            EmbeddingModel.T3_SMALL: "summary_embedding_t3_small",
            EmbeddingModel.T3_LARGE: "summary_embedding_t3_large",
        }

        # Map search algorithm to pgvector operator
        operator_map = {
            SearchAlgorithm.COSINE: "<=>",  # Cosine distance
            SearchAlgorithm.INNER_PRODUCT: "<#>",  # Negative inner product
            SearchAlgorithm.L2_EUCLIDEAN: "<->",  # L2 distance
            SearchAlgorithm.L1_MANHATTAN: "<+>",  # L1 distance
        }

        embedding_column = embedding_column_map.get(search_request.embedding_model)
        operator = operator_map.get(search_request.search_algorithm)

        if not embedding_column:
            raise ValueError(f"Unsupported embedding model: {search_request.embedding_model}")

        if not operator:
            raise ValueError(f"Unsupported search algorithm: {search_request.search_algorithm}")

        # Convert embedding to PostgreSQL array format
        embedding_str = "[" + ",".join(map(str, query_embedding)) + "]"

        query = f"""
            SELECT
                id, match_id, period, minute, quarter_minute,
                count, json_ as json_data, summary,
                {embedding_column} {operator} %s::vector AS similarity_score
            FROM events_details__quarter_minute
            WHERE match_id = %s
              AND {embedding_column} IS NOT NULL
            ORDER BY similarity_score
            LIMIT %s
        """

        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute(
                        query,
                        (embedding_str, search_request.match_id, search_request.top_n),
                    )
                    rows = cur.fetchall()

                    results = []
                    for rank, row in enumerate(rows, start=1):
                        event = self._row_to_event(dict(row))
                        results.append(
                            SearchResult(
                                event=event,
                                similarity_score=float(row["similarity_score"]),
                                rank=rank,
                            )
                        )

                    return results
        except Exception as e:
            logger.error(f"Error searching events: {e}")
            raise

    def _row_to_event(self, row: Dict[str, Any]) -> EventDetail:
        """Convert database row to EventDetail entity."""
        return EventDetail(
            id=row["id"],
            match_id=row["match_id"],
            period=row["period"],
            minute=row["minute"],
            quarter_minute=row["quarter_minute"],
            count=row["count"],
            json_data=row["json_data"],
            summary=row.get("summary"),
        )


class PostgresRepositoryFactory:
    """Factory for creating PostgreSQL repository instances."""

    def create_match_repository(self) -> MatchRepository:
        """Create a PostgreSQL match repository instance."""
        return PostgresMatchRepository()

    def create_event_repository(self) -> EventRepository:
        """Create a PostgreSQL event repository instance."""
        return PostgresEventRepository()

