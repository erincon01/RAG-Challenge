"""
Unit tests for SQL Server repository implementations.

Tests helper methods directly and main query methods via mocked pyodbc.
"""

from datetime import date
from unittest.mock import MagicMock, patch

import pytest

from app.repositories.sqlserver import SQLServerMatchRepository, SQLServerEventRepository
from app.domain.entities import Competition, Season, Team, Stadium, Referee, Match, EventDetail


# ---------------------------------------------------------------------------
# Build a mock pyodbc Row object with attribute access
# ---------------------------------------------------------------------------

def _make_row(**kwargs):
    """Build a mock object that supports attribute access, like a pyodbc Row."""
    row = MagicMock()
    for key, value in kwargs.items():
        setattr(row, key, value)
    # hasattr support: make it return True for all defined keys
    return row


def _match_row():
    return _make_row(
        match_id=3943043,
        match_date=date(2024, 7, 14),
        competition_id=55,
        competition_country="Europe",
        competition_name="UEFA Euro",
        season_id=282,
        season_name="2024",
        home_team_id=772,
        home_team_name="Spain",
        home_team_gender="male",
        home_team_country="Spain",
        home_team_manager="Luis de la Fuente",
        home_team_manager_country="Spain",
        away_team_id=768,
        away_team_name="England",
        away_team_gender="male",
        away_team_country="England",
        away_team_manager="Gareth Southgate",
        away_team_manager_country="England",
        home_score=2,
        away_score=1,
        result="home",
        match_week=7,
        stadium_id=3041,
        stadium_name="Olympiastadion",
        stadium_country="Germany",
        referee_id=123,
        referee_name="Francois Letexier",
        referee_country="France",
        json_data='{"id": 3943043}',
    )


def _match_row_no_stadium():
    row = _match_row()
    row.stadium_id = None
    row.stadium_name = None
    row.stadium_country = None
    row.referee_id = None
    row.referee_name = None
    row.referee_country = None
    return row


def _event_row():
    row = _make_row(
        id=1001,
        match_id=3943043,
        period=1,
        minute=10,
        quarter_minute=1,
        count=5,
        json_data='{"events": []}',
        summary="Spain controls possession",
    )
    return row


# ---------------------------------------------------------------------------
# Tests for SQLServerMatchRepository._row_to_match
# ---------------------------------------------------------------------------

class TestSqlServerRowToMatch:
    def setup_method(self):
        self.repo = SQLServerMatchRepository.__new__(SQLServerMatchRepository)

    def test_basic_row_conversion(self):
        match = self.repo._row_to_match(_match_row())
        assert isinstance(match, Match)
        assert match.match_id == 3943043
        assert match.home_score == 2
        assert match.away_score == 1

    def test_competition_populated(self):
        match = self.repo._row_to_match(_match_row())
        assert isinstance(match.competition, Competition)
        assert match.competition.competition_id == 55
        assert match.competition.name == "UEFA Euro"

    def test_season_populated(self):
        match = self.repo._row_to_match(_match_row())
        assert isinstance(match.season, Season)
        assert match.season.name == "2024"

    def test_home_team_populated(self):
        match = self.repo._row_to_match(_match_row())
        assert isinstance(match.home_team, Team)
        assert match.home_team.name == "Spain"

    def test_away_team_populated(self):
        match = self.repo._row_to_match(_match_row())
        assert isinstance(match.away_team, Team)
        assert match.away_team.name == "England"

    def test_stadium_populated_when_present(self):
        match = self.repo._row_to_match(_match_row())
        assert isinstance(match.stadium, Stadium)
        assert match.stadium.name == "Olympiastadion"

    def test_stadium_none_when_absent(self):
        match = self.repo._row_to_match(_match_row_no_stadium())
        assert match.stadium is None

    def test_referee_none_when_absent(self):
        match = self.repo._row_to_match(_match_row_no_stadium())
        assert match.referee is None

    def test_referee_populated_when_present(self):
        match = self.repo._row_to_match(_match_row())
        assert isinstance(match.referee, Referee)
        assert match.referee.name == "Francois Letexier"

    def test_match_week_preserved(self):
        match = self.repo._row_to_match(_match_row())
        assert match.match_week == 7


# ---------------------------------------------------------------------------
# Tests for SQLServerEventRepository._row_to_event
# ---------------------------------------------------------------------------

class TestSqlServerRowToEvent:
    def setup_method(self):
        self.repo = SQLServerEventRepository.__new__(SQLServerEventRepository)

    def test_basic_event_conversion(self):
        event = self.repo._row_to_event(_event_row())
        assert isinstance(event, EventDetail)
        assert event.id == 1001
        assert event.match_id == 3943043

    def test_event_period_and_minute(self):
        event = self.repo._row_to_event(_event_row())
        assert event.period == 1
        assert event.minute == 10
        assert event.quarter_minute == 1

    def test_event_json_data(self):
        event = self.repo._row_to_event(_event_row())
        assert event.json_data == '{"events": []}'

    def test_event_summary(self):
        event = self.repo._row_to_event(_event_row())
        assert event.summary == "Spain controls possession"

    def test_event_json_data_empty_when_none(self):
        row = _event_row()
        row.json_data = None
        event = self.repo._row_to_event(row)
        assert event.json_data == ""


# ---------------------------------------------------------------------------
# Tests for SQLServerMatchRepository query methods (mocked pyodbc)
# ---------------------------------------------------------------------------

class TestSqlServerMatchRepositoryQueries:
    @patch("app.repositories.sqlserver.pyodbc.connect")
    def test_test_connection_returns_true(self, mock_connect):
        repo = SQLServerMatchRepository()
        with patch.object(repo, "get_connection") as mock_gc:
            conn = MagicMock()
            cursor = MagicMock()
            conn.cursor.return_value = cursor
            mock_gc.return_value.__enter__ = MagicMock(return_value=conn)
            mock_gc.return_value.__exit__ = MagicMock(return_value=False)
            result = repo.test_connection()
        assert result is True

    @patch("app.repositories.sqlserver.pyodbc.connect")
    def test_test_connection_returns_false_on_error(self, mock_connect):
        repo = SQLServerMatchRepository()
        with patch.object(repo, "get_connection") as mock_gc:
            mock_gc.side_effect = Exception("failed")
            result = repo.test_connection()
        assert result is False

    @patch("app.repositories.sqlserver.pyodbc.connect")
    def test_get_by_id_returns_match(self, mock_connect):
        repo = SQLServerMatchRepository()
        with patch.object(repo, "get_connection") as mock_gc:
            conn = MagicMock()
            cursor = MagicMock()
            cursor.fetchone.return_value = _match_row()
            conn.cursor.return_value = cursor
            mock_gc.return_value.__enter__ = MagicMock(return_value=conn)
            mock_gc.return_value.__exit__ = MagicMock(return_value=False)

            result = repo.get_by_id(3943043)

        assert result is not None
        assert result.match_id == 3943043

    @patch("app.repositories.sqlserver.pyodbc.connect")
    def test_get_by_id_returns_none_when_not_found(self, mock_connect):
        repo = SQLServerMatchRepository()
        with patch.object(repo, "get_connection") as mock_gc:
            conn = MagicMock()
            cursor = MagicMock()
            cursor.fetchone.return_value = None
            conn.cursor.return_value = cursor
            mock_gc.return_value.__enter__ = MagicMock(return_value=conn)
            mock_gc.return_value.__exit__ = MagicMock(return_value=False)

            result = repo.get_by_id(99999)

        assert result is None

    @patch("app.repositories.sqlserver.pyodbc.connect")
    def test_get_all_no_filters(self, mock_connect):
        repo = SQLServerMatchRepository()
        with patch.object(repo, "get_connection") as mock_gc:
            conn = MagicMock()
            cursor = MagicMock()
            cursor.fetchall.return_value = [_match_row(), _match_row_no_stadium()]
            conn.cursor.return_value = cursor
            mock_gc.return_value.__enter__ = MagicMock(return_value=conn)
            mock_gc.return_value.__exit__ = MagicMock(return_value=False)

            results = repo.get_all()

        assert len(results) == 2
        assert all(isinstance(m, Match) for m in results)

    @patch("app.repositories.sqlserver.pyodbc.connect")
    def test_get_all_with_competition_filter(self, mock_connect):
        repo = SQLServerMatchRepository()
        with patch.object(repo, "get_connection") as mock_gc:
            conn = MagicMock()
            cursor = MagicMock()
            cursor.fetchall.return_value = [_match_row()]
            conn.cursor.return_value = cursor
            mock_gc.return_value.__enter__ = MagicMock(return_value=conn)
            mock_gc.return_value.__exit__ = MagicMock(return_value=False)

            results = repo.get_all(competition_name="UEFA Euro")

        assert len(results) == 1

    @patch("app.repositories.sqlserver.pyodbc.connect")
    def test_get_all_with_both_filters(self, mock_connect):
        repo = SQLServerMatchRepository()
        with patch.object(repo, "get_connection") as mock_gc:
            conn = MagicMock()
            cursor = MagicMock()
            cursor.fetchall.return_value = [_match_row()]
            conn.cursor.return_value = cursor
            mock_gc.return_value.__enter__ = MagicMock(return_value=conn)
            mock_gc.return_value.__exit__ = MagicMock(return_value=False)

            results = repo.get_all(competition_name="UEFA Euro", season_name="2024")

        assert len(results) == 1

    @patch("app.repositories.sqlserver.pyodbc.connect")
    def test_get_competitions(self, mock_connect):
        comp_row = _make_row(
            competition_id=55,
            competition_country="Europe",
            competition_name="UEFA Euro",
        )
        repo = SQLServerMatchRepository()
        with patch.object(repo, "get_connection") as mock_gc:
            conn = MagicMock()
            cursor = MagicMock()
            cursor.fetchall.return_value = [comp_row]
            conn.cursor.return_value = cursor
            mock_gc.return_value.__enter__ = MagicMock(return_value=conn)
            mock_gc.return_value.__exit__ = MagicMock(return_value=False)

            results = repo.get_competitions()

        assert len(results) == 1
        assert isinstance(results[0], Competition)
        assert results[0].name == "UEFA Euro"


# ---------------------------------------------------------------------------
# Tests for SQLServerEventRepository query methods (mocked pyodbc)
# ---------------------------------------------------------------------------

class TestSqlServerEventRepositoryQueries:
    @patch("app.repositories.sqlserver.pyodbc.connect")
    def test_test_connection_returns_true(self, mock_connect):
        repo = SQLServerEventRepository()
        with patch.object(repo, "get_connection") as mock_gc:
            conn = MagicMock()
            cursor = MagicMock()
            conn.cursor.return_value = cursor
            mock_gc.return_value.__enter__ = MagicMock(return_value=conn)
            mock_gc.return_value.__exit__ = MagicMock(return_value=False)
            result = repo.test_connection()
        assert result is True

    @patch("app.repositories.sqlserver.pyodbc.connect")
    def test_get_events_by_match_no_limit(self, mock_connect):
        repo = SQLServerEventRepository()
        with patch.object(repo, "get_connection") as mock_gc:
            conn = MagicMock()
            cursor = MagicMock()
            cursor.fetchall.return_value = [_event_row(), _event_row()]
            conn.cursor.return_value = cursor
            mock_gc.return_value.__enter__ = MagicMock(return_value=conn)
            mock_gc.return_value.__exit__ = MagicMock(return_value=False)

            results = repo.get_events_by_match(3943043)

        assert len(results) == 2

    @patch("app.repositories.sqlserver.pyodbc.connect")
    def test_get_events_by_match_with_limit(self, mock_connect):
        repo = SQLServerEventRepository()
        with patch.object(repo, "get_connection") as mock_gc:
            conn = MagicMock()
            cursor = MagicMock()
            cursor.fetchall.return_value = [_event_row()]
            conn.cursor.return_value = cursor
            mock_gc.return_value.__enter__ = MagicMock(return_value=conn)
            mock_gc.return_value.__exit__ = MagicMock(return_value=False)

            results = repo.get_events_by_match(3943043, limit=1)

        assert len(results) == 1

    @patch("app.repositories.sqlserver.pyodbc.connect")
    def test_get_event_by_id_found(self, mock_connect):
        repo = SQLServerEventRepository()
        with patch.object(repo, "get_connection") as mock_gc:
            conn = MagicMock()
            cursor = MagicMock()
            cursor.fetchone.return_value = _event_row()
            conn.cursor.return_value = cursor
            mock_gc.return_value.__enter__ = MagicMock(return_value=conn)
            mock_gc.return_value.__exit__ = MagicMock(return_value=False)

            result = repo.get_event_by_id(1001)

        assert result is not None
        assert result.id == 1001

    @patch("app.repositories.sqlserver.pyodbc.connect")
    def test_get_event_by_id_not_found(self, mock_connect):
        repo = SQLServerEventRepository()
        with patch.object(repo, "get_connection") as mock_gc:
            conn = MagicMock()
            cursor = MagicMock()
            cursor.fetchone.return_value = None
            conn.cursor.return_value = cursor
            mock_gc.return_value.__enter__ = MagicMock(return_value=conn)
            mock_gc.return_value.__exit__ = MagicMock(return_value=False)

            result = repo.get_event_by_id(99999)

        assert result is None

    @patch("app.repositories.sqlserver.pyodbc.connect")
    def test_search_by_embedding_returns_results(self, mock_connect):
        from app.domain.entities import EmbeddingModel, SearchAlgorithm, SearchRequest

        req = SearchRequest(
            match_id=3943043,
            query="who scored?",
            embedding_model=EmbeddingModel.ADA_002,
            search_algorithm=SearchAlgorithm.COSINE,
            top_n=3,
        )
        query_embedding = [0.1] * 1536

        row = _event_row()
        row.similarity_score = 0.12

        repo = SQLServerEventRepository()
        with patch.object(repo, "get_connection") as mock_gc:
            conn = MagicMock()
            cursor = MagicMock()
            cursor.fetchall.return_value = [row]
            conn.cursor.return_value = cursor
            mock_gc.return_value.__enter__ = MagicMock(return_value=conn)
            mock_gc.return_value.__exit__ = MagicMock(return_value=False)

            results = repo.search_by_embedding(req, query_embedding)

        assert len(results) == 1
        assert results[0].rank == 1
        assert results[0].similarity_score == 0.12
        assert results[0].event.id == 1001

    @patch("app.repositories.sqlserver.pyodbc.connect")
    def test_search_by_embedding_empty_rows(self, mock_connect):
        from app.domain.entities import EmbeddingModel, SearchAlgorithm, SearchRequest

        req = SearchRequest(
            match_id=3943043,
            query="no results",
            embedding_model=EmbeddingModel.T3_SMALL,
            search_algorithm=SearchAlgorithm.L2_EUCLIDEAN,
            top_n=5,
        )
        query_embedding = [0.0] * 1536

        repo = SQLServerEventRepository()
        with patch.object(repo, "get_connection") as mock_gc:
            conn = MagicMock()
            cursor = MagicMock()
            cursor.fetchall.return_value = []
            conn.cursor.return_value = cursor
            mock_gc.return_value.__enter__ = MagicMock(return_value=conn)
            mock_gc.return_value.__exit__ = MagicMock(return_value=False)

            results = repo.search_by_embedding(req, query_embedding)

        assert results == []

    @patch("app.repositories.sqlserver.pyodbc.connect")
    def test_search_by_embedding_inner_product(self, mock_connect):
        from app.domain.entities import EmbeddingModel, SearchAlgorithm, SearchRequest

        req = SearchRequest(
            match_id=1,
            query="test",
            embedding_model=EmbeddingModel.ADA_002,
            search_algorithm=SearchAlgorithm.INNER_PRODUCT,
            top_n=2,
        )

        row1 = _event_row()
        row1.similarity_score = 0.05
        row2 = _event_row()
        row2.id = 1002
        row2.similarity_score = 0.08

        repo = SQLServerEventRepository()
        with patch.object(repo, "get_connection") as mock_gc:
            conn = MagicMock()
            cursor = MagicMock()
            cursor.fetchall.return_value = [row1, row2]
            conn.cursor.return_value = cursor
            mock_gc.return_value.__enter__ = MagicMock(return_value=conn)
            mock_gc.return_value.__exit__ = MagicMock(return_value=False)

            results = repo.search_by_embedding(req, query_embedding=[0.1] * 1536)

        assert len(results) == 2
        assert results[0].rank == 1
        assert results[1].rank == 2

    def test_search_by_embedding_unsupported_model_raises(self):
        from app.domain.entities import SearchRequest

        req_mock = MagicMock()
        req_mock.embedding_model = "unsupported_model"
        req_mock.search_algorithm = "cosine"
        req_mock.match_id = 1
        req_mock.top_n = 5

        repo = SQLServerEventRepository()
        with pytest.raises(ValueError, match="Unsupported embedding model"):
            repo.search_by_embedding(req_mock, [0.1])

    def test_search_by_embedding_unsupported_algorithm_raises(self):
        from app.domain.entities import EmbeddingModel, SearchRequest

        req_mock = MagicMock()
        req_mock.embedding_model = EmbeddingModel.ADA_002
        req_mock.search_algorithm = "bad_algo"
        req_mock.match_id = 1
        req_mock.top_n = 5

        repo = SQLServerEventRepository()
        with pytest.raises(ValueError, match="Unsupported search algorithm"):
            repo.search_by_embedding(req_mock, [0.1])

    def test_search_by_embedding_t3_large_raises(self):
        """T3_LARGE is not in the SQL Server embedding column map."""
        from app.domain.entities import EmbeddingModel, SearchAlgorithm, SearchRequest

        req = SearchRequest(
            match_id=1,
            query="test",
            embedding_model=EmbeddingModel.T3_LARGE,
            search_algorithm=SearchAlgorithm.COSINE,
            top_n=5,
        )
        repo = SQLServerEventRepository()
        with pytest.raises(ValueError, match="Unsupported embedding model"):
            repo.search_by_embedding(req, [0.1] * 1536)


# ---------------------------------------------------------------------------
# Exception-path tests — cover the "except Exception: raise" blocks
# ---------------------------------------------------------------------------

class TestSQLServerMatchRepositoryExceptions:
    def test_get_by_id_propagates_exception(self):
        repo = SQLServerMatchRepository()
        with patch.object(repo, "get_connection") as mock_gc:
            mock_gc.side_effect = RuntimeError("DB error")
            with pytest.raises(RuntimeError):
                repo.get_by_id(999)

    def test_get_all_propagates_exception(self):
        repo = SQLServerMatchRepository()
        with patch.object(repo, "get_connection") as mock_gc:
            mock_gc.side_effect = RuntimeError("DB error")
            with pytest.raises(RuntimeError):
                repo.get_all()

    def test_get_competitions_propagates_exception(self):
        repo = SQLServerMatchRepository()
        with patch.object(repo, "get_connection") as mock_gc:
            mock_gc.side_effect = RuntimeError("DB error")
            with pytest.raises(RuntimeError):
                repo.get_competitions()


class TestSQLServerEventRepositoryExceptions:
    def test_get_events_by_match_propagates_exception(self):
        repo = SQLServerEventRepository()
        with patch.object(repo, "get_connection") as mock_gc:
            mock_gc.side_effect = RuntimeError("DB error")
            with pytest.raises(RuntimeError):
                repo.get_events_by_match(999)

    def test_get_event_by_id_propagates_exception(self):
        repo = SQLServerEventRepository()
        with patch.object(repo, "get_connection") as mock_gc:
            mock_gc.side_effect = RuntimeError("DB error")
            with pytest.raises(RuntimeError):
                repo.get_event_by_id(999)

    def test_search_by_embedding_propagates_exception(self):
        from app.domain.entities import EmbeddingModel, SearchAlgorithm, SearchRequest

        req = SearchRequest(
            match_id=1,
            query="test",
            embedding_model=EmbeddingModel.ADA_002,
            search_algorithm=SearchAlgorithm.COSINE,
            top_n=5,
        )
        repo = SQLServerEventRepository()
        with patch.object(repo, "get_connection") as mock_gc:
            mock_gc.side_effect = RuntimeError("DB error")
            with pytest.raises(RuntimeError):
                repo.search_by_embedding(req, [0.1] * 1536)
