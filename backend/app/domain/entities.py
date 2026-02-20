"""
Domain entities for RAG Challenge.

These are the core business entities representing the domain model.
They are database-agnostic and contain only business logic.
"""

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Optional, List
from enum import Enum


class SearchAlgorithm(str, Enum):
    """Supported similarity search algorithms."""

    COSINE = "cosine"
    INNER_PRODUCT = "inner_product"
    L1_MANHATTAN = "l1_manhattan"
    L2_EUCLIDEAN = "l2_euclidean"


class EmbeddingModel(str, Enum):
    """Supported embedding models."""

    ADA_002 = "text-embedding-ada-002"
    T3_SMALL = "text-embedding-3-small"
    T3_LARGE = "text-embedding-3-large"


@dataclass
class Competition:
    """Competition entity."""

    competition_id: int
    country: str
    name: str


@dataclass
class Season:
    """Season entity."""

    season_id: int
    name: str


@dataclass
class Team:
    """Team entity."""

    team_id: int
    name: str
    gender: str
    country: str
    manager: Optional[str] = None
    manager_country: Optional[str] = None


@dataclass
class Stadium:
    """Stadium entity."""

    stadium_id: int
    name: str
    country: str


@dataclass
class Referee:
    """Referee entity."""

    referee_id: int
    name: str
    country: str


@dataclass
class Match:
    """Match entity."""

    match_id: int
    match_date: date
    competition: Competition
    season: Season
    home_team: Team
    away_team: Team
    home_score: int
    away_score: int
    result: str
    match_week: Optional[int] = None
    stadium: Optional[Stadium] = None
    referee: Optional[Referee] = None
    json_data: Optional[str] = None

    @property
    def display_name(self) -> str:
        """Get display name for the match."""
        return f"{self.home_team.name} ({self.home_score}) - {self.away_team.name} ({self.away_score})"


@dataclass
class Player:
    """Player entity."""

    player_id: int
    player_name: str
    jersey_number: Optional[int] = None
    country_id: Optional[int] = None
    country_name: Optional[str] = None
    position_id: Optional[int] = None
    position_name: Optional[str] = None


@dataclass
class EventDetail:
    """Event detail entity for quarter-minute aggregated events."""

    id: int
    match_id: int
    period: int
    minute: int
    quarter_minute: int
    count: int
    json_data: str
    summary: Optional[str] = None
    summary_embedding_ada_002: Optional[List[float]] = None
    summary_embedding_t3_small: Optional[List[float]] = None
    summary_embedding_t3_large: Optional[List[float]] = None
    summary_embedding_e5: Optional[List[float]] = None

    @property
    def time_description(self) -> str:
        """Get human-readable time description."""
        quarter_start = (self.quarter_minute - 1) * 15
        quarter_end = self.quarter_minute * 15
        return f"Period {self.period}, Minute {self.minute}:{quarter_start:02d}-{quarter_end:02d}"


@dataclass
class SearchResult:
    """Result from semantic search."""

    event: EventDetail
    similarity_score: float
    rank: int


@dataclass
class SearchRequest:
    """Request for semantic search."""

    match_id: int
    query: str
    language: str = "english"
    search_algorithm: SearchAlgorithm = SearchAlgorithm.COSINE
    embedding_model: EmbeddingModel = EmbeddingModel.T3_SMALL
    top_n: int = 10
    temperature: float = 0.1
    max_input_tokens: int = 10000
    max_output_tokens: int = 5000
    include_match_info: bool = True
    system_message: Optional[str] = None

    def __post_init__(self):
        """Validate parameters."""
        if self.top_n < 1:
            self.top_n = 10
        if self.top_n > 100:
            self.top_n = 100
        if self.temperature < 0 or self.temperature > 2:
            self.temperature = 0.1


@dataclass
class ChatResponse:
    """Response from chat/search endpoint."""

    question: str
    normalized_question: str
    answer: str
    search_results: List[SearchResult]
    match_info: Optional[Match] = None
    metadata: dict = field(default_factory=dict)
