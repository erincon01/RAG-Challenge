"""
PostgreSQL repository implementations.

These implementations use psycopg2 for database access and support pgvector
for similarity search.
"""

import logging
from contextlib import contextmanager
from typing import Any

import psycopg2
from psycopg2.extras import RealDictCursor

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
from app.domain.exceptions import (
    DatabaseConnectionError,
)
from app.repositories.base import EventRepository, MatchRepository

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
        competition_name: str | None = None,
        season_name: str | None = None,
        limit: int = 100,
    ) -> list[Match]:
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

        params: list = []

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

    def get_teams(
        self, match_id: int | None = None, limit: int = 500
    ) -> list[dict[str, Any]]:
        """Get team metadata from matches."""
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

        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(query, tuple(params))
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
        except Exception as e:
            logger.error(f"Error fetching teams: {e}")
            raise

    def get_players(
        self, match_id: int | None = None, limit: int = 500
    ) -> list[dict[str, Any]]:
        """Get player roster data."""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        SELECT 1
                        FROM information_schema.tables
                        WHERE table_schema = 'public' AND table_name = %s
                        """,
                        ("players",),
                    )
                    if cur.fetchone() is None:
                        return []

            with self.get_connection() as conn:
                with conn.cursor() as cur:
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
        except Exception as e:
            logger.error(f"Error fetching players: {e}")
            raise

    def get_tables_info(self) -> list[dict[str, Any]]:
        """Get table metadata for PostgreSQL."""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
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
                          AND udt_name = 'vector'
                        ORDER BY table_name, column_name
                        """
                    )

                    embedding_map: dict[str, list[str]] = {}
                    for table_name, column_name in cur.fetchall():
                        embedding_map.setdefault(table_name, []).append(column_name)

                    info: list[dict[str, Any]] = []
                    for table_name in table_names:
                        cur.execute(f'SELECT COUNT(*) FROM "{table_name}"')
                        row_count = int(cur.fetchone()[0] or 0)

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

    def _row_to_match(self, row: dict[str, Any]) -> Match:
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

    def get_tables_info(self) -> list[dict[str, Any]]:
        """Get table metadata for PostgreSQL."""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
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
                          AND udt_name = 'vector'
                        ORDER BY table_name, column_name
                        """
                    )

                    embedding_map: dict[str, list[str]] = {}
                    for table_name, column_name in cur.fetchall():
                        embedding_map.setdefault(table_name, []).append(column_name)

                    info: list[dict[str, Any]] = []
                    for table_name in table_names:
                        cur.execute(f'SELECT COUNT(*) FROM "{table_name}"')
                        row_count = int(cur.fetchone()[0] or 0)

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

    def get_event_by_id(self, event_id: int) -> EventDetail | None:
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
        self, search_request: SearchRequest, query_embedding: list[float]
    ) -> list[SearchResult]:
        """
        Search events using vector similarity.

        Note: This implementation uses pgvector operators for similarity search.
        """
        # Map embedding model to column name
        embedding_column_map = {
            EmbeddingModel.T3_SMALL: "summary_embedding_t3_small",
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
            raise ValueError(
                f"Unsupported embedding model: {search_request.embedding_model}"
            )

        if not operator:
            raise ValueError(
                f"Unsupported search algorithm: {search_request.search_algorithm}"
            )

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

    def _row_to_event(self, row: dict[str, Any]) -> EventDetail:
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
