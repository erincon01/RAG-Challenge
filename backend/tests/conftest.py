"""
Root conftest.py — shared fixtures for all test levels.

Provides:
  - FastAPI TestClient with all dependencies overridden
  - Factory helpers for domain entities
  - Shared mock builders
"""

from datetime import date
from typing import List, Optional
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.domain.entities import (
    Competition,
    Season,
    Team,
    Stadium,
    Referee,
    Match,
    Player,
    EventDetail,
    SearchResult,
    ChatResponse,
    SearchRequest,
    SearchAlgorithm,
    EmbeddingModel,
)
from app.repositories.base import MatchRepository, EventRepository


# ---------------------------------------------------------------------------
# Domain entity factories
# ---------------------------------------------------------------------------

def make_competition(competition_id: int = 1, country: str = "Europe", name: str = "UEFA Euro") -> Competition:
    return Competition(competition_id=competition_id, country=country, name=name)


def make_season(season_id: int = 1, name: str = "2024") -> Season:
    return Season(season_id=season_id, name=name)


def make_team(
    team_id: int = 100,
    name: str = "Spain",
    gender: str = "male",
    country: str = "Spain",
    manager: Optional[str] = None,
) -> Team:
    return Team(team_id=team_id, name=name, gender=gender, country=country, manager=manager)


def make_stadium(stadium_id: int = 1, name: str = "Olympiastadion", country: str = "Germany") -> Stadium:
    return Stadium(stadium_id=stadium_id, name=name, country=country)


def make_referee(referee_id: int = 1, name: str = "Referee A", country: str = "France") -> Referee:
    return Referee(referee_id=referee_id, name=name, country=country)


def make_match(
    match_id: int = 3943043,
    home_score: int = 2,
    away_score: int = 1,
    result: str = "home",
    include_stadium: bool = False,
    include_referee: bool = False,
) -> Match:
    return Match(
        match_id=match_id,
        match_date=date(2024, 7, 14),
        competition=make_competition(),
        season=make_season(),
        home_team=make_team(100, "Spain"),
        away_team=make_team(200, "England"),
        home_score=home_score,
        away_score=away_score,
        result=result,
        match_week=1,
        stadium=make_stadium() if include_stadium else None,
        referee=make_referee() if include_referee else None,
    )


def make_event(
    event_id: int = 1,
    match_id: int = 3943043,
    period: int = 1,
    minute: int = 10,
    quarter_minute: int = 1,
    summary: Optional[str] = "Spain controls possession in midfield",
) -> EventDetail:
    return EventDetail(
        id=event_id,
        match_id=match_id,
        period=period,
        minute=minute,
        quarter_minute=quarter_minute,
        count=5,
        json_data='{"events": []}',
        summary=summary,
    )


def make_search_result(event: Optional[EventDetail] = None, rank: int = 1) -> SearchResult:
    return SearchResult(
        event=event or make_event(),
        similarity_score=0.92,
        rank=rank,
    )


def make_search_request(match_id: int = 3943043, query: str = "Who scored the first goal?") -> SearchRequest:
    return SearchRequest(match_id=match_id, query=query)


def make_chat_response(
    question: str = "Who scored?",
    answer: str = "Spain scored through Oyarzabal.",
    results: Optional[List[SearchResult]] = None,
) -> ChatResponse:
    return ChatResponse(
        question=question,
        normalized_question=question,
        answer=answer,
        search_results=results or [make_search_result()],
        match_info=make_match(),
        metadata={"results_count": 1},
    )


# ---------------------------------------------------------------------------
# Mock repository factories
# ---------------------------------------------------------------------------

def make_mock_match_repo(
    match: Optional[Match] = None,
    matches: Optional[List[Match]] = None,
    competitions: Optional[List[Competition]] = None,
) -> MagicMock:
    repo = MagicMock(spec=MatchRepository)
    repo.get_by_id.return_value = match or make_match()
    repo.get_all.return_value = matches if matches is not None else [make_match()]
    repo.get_competitions.return_value = competitions if competitions is not None else [make_competition()]
    repo.test_connection.return_value = True
    return repo


def make_mock_event_repo(
    events: Optional[List[EventDetail]] = None,
    event: Optional[EventDetail] = None,
    search_results: Optional[List[SearchResult]] = None,
) -> MagicMock:
    repo = MagicMock(spec=EventRepository)
    repo.get_events_by_match.return_value = events if events is not None else [make_event()]
    repo.get_event_by_id.return_value = event or make_event()
    repo.search_by_embedding.return_value = search_results if search_results is not None else [make_search_result()]
    repo.test_connection.return_value = True
    return repo


def make_mock_openai_adapter() -> MagicMock:
    adapter = MagicMock()
    adapter.create_embedding.return_value = [0.1] * 1536
    adapter.create_embeddings_batch.return_value = [[0.1] * 1536]
    adapter.create_chat_completion.return_value = "Test answer from AI."
    adapter.translate_to_english.return_value = "Who scored the first goal?"
    return adapter


# ---------------------------------------------------------------------------
# FastAPI TestClient with overridden dependencies
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_match_repo() -> MagicMock:
    return make_mock_match_repo()


@pytest.fixture
def mock_event_repo() -> MagicMock:
    return make_mock_event_repo()


@pytest.fixture
def mock_openai_adapter() -> MagicMock:
    return make_mock_openai_adapter()


@pytest.fixture
def client(mock_match_repo, mock_event_repo, mock_openai_adapter) -> TestClient:
    """TestClient with all external dependencies mocked."""
    from app.main import app
    from app.core.dependencies import get_match_repository, get_event_repository
    from app.adapters.openai_client import get_openai_adapter
    from app.repositories.postgres import PostgresEventRepository
    from app.repositories.sqlserver import SQLServerEventRepository

    app.dependency_overrides[get_match_repository] = lambda source="postgres": mock_match_repo
    app.dependency_overrides[get_event_repository] = lambda source="postgres": mock_event_repo
    app.dependency_overrides[get_openai_adapter] = lambda: mock_openai_adapter

    with TestClient(app, raise_server_exceptions=False) as c:
        yield c

    app.dependency_overrides.clear()
