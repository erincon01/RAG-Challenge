"""
Unit tests for domain entities, enums, exceptions, DTOs, and capabilities.

No external dependencies — pure Python.
"""

import pytest
from datetime import date

from app.domain.entities import (
    SearchAlgorithm,
    EmbeddingModel,
    Competition,
    Season,
    Team,
    Stadium,
    Referee,
    Match,
    Player,
    EventDetail,
    SearchResult,
    SearchRequest,
    ChatResponse,
)
from app.domain.exceptions import (
    DomainException,
    EntityNotFoundError,
    ValidationError,
    DatabaseConnectionError,
    EmbeddingGenerationError,
)
from app.core.capabilities import (
    normalize_source,
    get_source_capabilities,
    validate_search_capabilities,
    SOURCE_CAPABILITIES,
)
from app.api.v1.models import SearchRequest as ApiSearchRequest


# ===========================================================================
# Enums
# ===========================================================================

class TestSearchAlgorithm:
    def test_search_algorithm_enum_contains_all_expected_values(self):
        values = {a.value for a in SearchAlgorithm}
        assert values == {"cosine", "inner_product", "l1_manhattan", "l2_euclidean"}

    def test_search_algorithm_str_comparison_matches_value(self):
        assert SearchAlgorithm.COSINE == "cosine"
        assert SearchAlgorithm.INNER_PRODUCT == "inner_product"


class TestEmbeddingModel:
    def test_embedding_model_enum_contains_all_expected_values(self):
        values = {m.value for m in EmbeddingModel}
        assert values == {
            "text-embedding-ada-002",
            "text-embedding-3-small",
            "text-embedding-3-large",
        }

    def test_embedding_model_str_comparison_matches_value(self):
        assert EmbeddingModel.ADA_002 == "text-embedding-ada-002"
        assert EmbeddingModel.T3_SMALL == "text-embedding-3-small"
        assert EmbeddingModel.T3_LARGE == "text-embedding-3-large"


# ===========================================================================
# Simple entities
# ===========================================================================

class TestCompetition:
    def test_create_competition_valid_args_returns_entity(self):
        c = Competition(competition_id=55, country="Europe", name="UEFA Euro")
        assert c.competition_id == 55
        assert c.country == "Europe"
        assert c.name == "UEFA Euro"


class TestTeam:
    def test_create_team_minimal_args_defaults_none(self):
        t = Team(team_id=100, name="Spain", gender="male", country="Spain")
        assert t.manager is None
        assert t.manager_country is None

    def test_create_team_with_manager_populates_field(self):
        t = Team(team_id=100, name="Spain", gender="male", country="Spain",
                 manager="Luis de la Fuente", manager_country="Spain")
        assert t.manager == "Luis de la Fuente"


class TestMatch:
    def _make_match(self, home_score=2, away_score=1):
        return Match(
            match_id=3943043,
            match_date=date(2024, 7, 14),
            competition=Competition(1, "Europe", "UEFA Euro"),
            season=Season(1, "2024"),
            home_team=Team(100, "Spain", "male", "Spain"),
            away_team=Team(200, "England", "male", "England"),
            home_score=home_score,
            away_score=away_score,
            result="home",
        )

    def test_match_display_name_home_win_format(self):
        m = self._make_match(2, 1)
        assert m.display_name == "Spain (2) - England (1)"

    def test_match_display_name_draw_format(self):
        m = self._make_match(1, 1)
        assert m.display_name == "Spain (1) - England (1)"

    def test_match_optional_fields_default_none(self):
        m = self._make_match()
        assert m.stadium is None
        assert m.referee is None
        assert m.match_week is None
        assert m.json_data is None

    def test_match_with_stadium_and_referee_populated(self):
        m = self._make_match()
        m.stadium = Stadium(1, "Olympiastadion", "Germany")
        m.referee = Referee(1, "Ref A", "France")
        assert m.stadium.name == "Olympiastadion"
        assert m.referee.name == "Ref A"


class TestEventDetail:
    def _make_event(self, period=1, minute=45, quarter_minute=2):
        return EventDetail(
            id=1, match_id=100,
            period=period, minute=minute, quarter_minute=quarter_minute,
            count=3, json_data='{}',
        )

    def test_time_description_format(self):
        e = self._make_event(period=1, minute=45, quarter_minute=2)
        desc = e.time_description
        assert "Period 1" in desc
        assert "Minute 45" in desc
        # quarter_minute=2 → 15s to 30s
        assert "15" in desc
        assert "30" in desc

    def test_time_description_first_quarter(self):
        e = self._make_event(period=2, minute=60, quarter_minute=1)
        desc = e.time_description
        assert "Period 2" in desc
        assert "00" in desc

    def test_optional_embeddings_default_none(self):
        e = self._make_event()
        assert e.summary is None
        assert e.summary_embedding_ada_002 is None
        assert e.summary_embedding_t3_small is None


class TestPlayer:
    def test_create_player_minimal_args_defaults_none(self):
        p = Player(player_id=1, player_name="Pedri")
        assert p.jersey_number is None
        assert p.country_name is None

    def test_create_player_full_args_populates_all_fields(self):
        p = Player(player_id=1, player_name="Pedri", jersey_number=8,
                   country_id=214, country_name="Spain",
                   position_id=13, position_name="Center Midfield")
        assert p.jersey_number == 8
        assert p.position_name == "Center Midfield"


# ===========================================================================
# SearchRequest domain validation
# ===========================================================================

class TestDomainSearchRequest:
    def test_search_request_no_optionals_uses_defaults(self):
        r = SearchRequest(match_id=1, query="Who scored?")
        assert r.language == "english"
        assert r.search_algorithm == SearchAlgorithm.COSINE
        assert r.embedding_model == EmbeddingModel.T3_SMALL
        assert r.top_n == 10
        assert r.temperature == 0.1
        assert r.include_match_info is True

    def test_top_n_clamped_below(self):
        r = SearchRequest(match_id=1, query="q", top_n=0)
        assert r.top_n == 10

    def test_top_n_clamped_above(self):
        r = SearchRequest(match_id=1, query="q", top_n=999)
        assert r.top_n == 100

    def test_temperature_clamped_negative(self):
        r = SearchRequest(match_id=1, query="q", temperature=-0.5)
        assert r.temperature == 0.1

    def test_temperature_clamped_above_max(self):
        r = SearchRequest(match_id=1, query="q", temperature=3.0)
        assert r.temperature == 0.1

    def test_valid_temperature_preserved(self):
        r = SearchRequest(match_id=1, query="q", temperature=1.5)
        assert r.temperature == 1.5


# ===========================================================================
# API SearchRequest DTO validators
# ===========================================================================

class TestApiSearchRequestDTO:
    def test_api_search_request_valid_args_uses_defaults(self):
        r = ApiSearchRequest(match_id=1, query="Who scored?")
        assert r.search_algorithm == "cosine"
        assert r.embedding_model == "text-embedding-3-small"

    def test_invalid_algorithm_raises(self):
        with pytest.raises(Exception):
            ApiSearchRequest(match_id=1, query="q", search_algorithm="invalid_algo")

    def test_invalid_model_raises(self):
        with pytest.raises(Exception):
            ApiSearchRequest(match_id=1, query="q", embedding_model="gpt-4")

    def test_all_valid_algorithms(self):
        for algo in ["cosine", "inner_product", "l2_euclidean", "l1_manhattan"]:
            r = ApiSearchRequest(match_id=1, query="q", search_algorithm=algo)
            assert r.search_algorithm == algo

    def test_all_valid_models(self):
        for model in ["text-embedding-ada-002", "text-embedding-3-small", "text-embedding-3-large"]:
            r = ApiSearchRequest(match_id=1, query="q", embedding_model=model)
            assert r.embedding_model == model

    def test_empty_query_raises(self):
        with pytest.raises(Exception):
            ApiSearchRequest(match_id=1, query="")


# ===========================================================================
# Domain exceptions
# ===========================================================================

class TestDomainExceptions:
    def test_entity_not_found_message(self):
        exc = EntityNotFoundError("Match", 999)
        assert "Match" in str(exc)
        assert "999" in str(exc)
        assert exc.entity_type == "Match"
        assert exc.entity_id == 999

    def test_entity_not_found_is_domain_exception(self):
        exc = EntityNotFoundError("Event", 1)
        assert isinstance(exc, DomainException)

    def test_validation_error_message_preserved(self):
        exc = ValidationError("Invalid algorithm")
        assert isinstance(exc, DomainException)
        assert "Invalid algorithm" in str(exc)

    def test_database_connection_error(self):
        exc = DatabaseConnectionError("Connection refused")
        assert isinstance(exc, DomainException)

    def test_embedding_generation_error(self):
        exc = EmbeddingGenerationError("Rate limit exceeded")
        assert isinstance(exc, DomainException)

    def test_catch_via_base(self):
        with pytest.raises(DomainException):
            raise EntityNotFoundError("Match", 1)


# ===========================================================================
# Capabilities
# ===========================================================================

class TestNormalizeSource:
    @pytest.mark.parametrize("alias,expected", [
        ("postgres", "postgres"),
        ("postgresql", "postgres"),
        ("azure-postgres", "postgres"),
        ("POSTGRES", "postgres"),
        ("sqlserver", "sqlserver"),
        ("sql-server", "sqlserver"),
        ("azure-sql", "sqlserver"),
        ("SQLSERVER", "sqlserver"),
    ])
    def test_normalize_source_known_alias_returns_canonical(self, alias, expected):
        assert normalize_source(alias) == expected

    def test_normalize_source_unknown_alias_returns_as_is(self):
        assert normalize_source("mongodb") == "mongodb"


class TestGetSourceCapabilities:
    def test_get_capabilities_postgres_returns_active_model_and_algos(self):
        caps = get_source_capabilities("postgres")
        assert caps["embedding_models"] == ["text-embedding-3-small"]
        assert "l1_manhattan" in caps["search_algorithms"]
        assert len(caps["search_algorithms"]) == 4

    def test_get_capabilities_sqlserver_returns_active_model(self):
        caps = get_source_capabilities("sqlserver")
        assert caps["embedding_models"] == ["text-embedding-3-small"]
        assert "l1_manhattan" not in caps["search_algorithms"]
        assert len(caps["search_algorithms"]) == 3

    def test_get_capabilities_via_alias_matches_canonical(self):
        assert get_source_capabilities("postgresql") == get_source_capabilities("postgres")

    def test_get_capabilities_unknown_source_raises_error(self):
        with pytest.raises(ValueError, match="Unsupported"):
            get_source_capabilities("redis")


class TestValidateSearchCapabilities:
    def test_postgres_valid_combination_t3_small(self):
        validate_search_capabilities("postgres", "text-embedding-3-small", "l1_manhattan")

    def test_sqlserver_valid_combination_t3_small(self):
        validate_search_capabilities("sqlserver", "text-embedding-3-small", "cosine")

    def test_deprecated_ada_002_rejected_by_capabilities(self):
        with pytest.raises(ValueError, match="Embedding model"):
            validate_search_capabilities("postgres", "text-embedding-ada-002", "cosine")

    def test_deprecated_t3_large_rejected_by_capabilities(self):
        with pytest.raises(ValueError, match="Embedding model"):
            validate_search_capabilities("postgres", "text-embedding-3-large", "cosine")

    def test_sqlserver_l1_not_supported(self):
        with pytest.raises(ValueError, match="Search algorithm"):
            validate_search_capabilities("sqlserver", "text-embedding-3-small", "l1_manhattan")

    def test_invalid_model_raises(self):
        with pytest.raises(ValueError):
            validate_search_capabilities("postgres", "gpt-4-embedding", "cosine")

    def test_invalid_algorithm_raises(self):
        with pytest.raises(ValueError):
            validate_search_capabilities("postgres", "text-embedding-3-small", "bm25")

    def test_all_postgres_algorithms(self):
        for algo in SOURCE_CAPABILITIES["postgres"]["search_algorithms"]:
            validate_search_capabilities("postgres", "text-embedding-3-small", algo)

    def test_all_sqlserver_algorithms(self):
        for algo in SOURCE_CAPABILITIES["sqlserver"]["search_algorithms"]:
            validate_search_capabilities("sqlserver", "text-embedding-3-small", algo)
