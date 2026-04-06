"""
API DTOs (Data Transfer Objects) for request and response models.

These Pydantic models define the structure of API requests and responses.
They are separate from domain entities to allow API versioning and
transformation without affecting the domain layer.
"""

from datetime import date
from typing import Any

from pydantic import BaseModel, Field, field_validator


# Competition models
class CompetitionResponse(BaseModel):
    """Response model for competition."""

    competition_id: int
    country: str
    name: str

    class Config:
        from_attributes = True


# Team models
class TeamResponse(BaseModel):
    """Response model for team."""

    team_id: int
    name: str
    gender: str
    country: str
    manager: str | None = None
    manager_country: str | None = None

    class Config:
        from_attributes = True


# Match models
class MatchSummaryResponse(BaseModel):
    """Summary response model for match (list view)."""

    match_id: int
    match_date: date
    competition_name: str
    season_name: str
    home_team_name: str
    away_team_name: str
    home_score: int
    away_score: int
    result: str
    display_name: str

    class Config:
        from_attributes = True


class MatchDetailResponse(BaseModel):
    """Detailed response model for match (single view)."""

    match_id: int
    match_date: date
    competition: CompetitionResponse
    season_name: str
    home_team: TeamResponse
    away_team: TeamResponse
    home_score: int
    away_score: int
    result: str
    match_week: int | None = None
    stadium_name: str | None = None
    referee_name: str | None = None
    display_name: str

    class Config:
        from_attributes = True


# Event models
class EventDetailResponse(BaseModel):
    """Response model for event detail."""

    id: int
    match_id: int
    period: int
    minute: int
    quarter_minute: int
    count: int
    summary: str | None = None
    time_description: str

    class Config:
        from_attributes = True


class SearchResultResponse(BaseModel):
    """Response model for search result."""

    event: EventDetailResponse
    similarity_score: float
    rank: int

    class Config:
        from_attributes = True


# Search request/response models
class SearchRequest(BaseModel):
    """Request model for semantic search."""

    match_id: int = Field(..., description="Match ID to search")
    query: str = Field(..., min_length=1, description="Search query")
    language: str = Field(default="english", description="Query language")
    search_algorithm: str = Field(
        default="cosine",
        description="Similarity algorithm: cosine, inner_product, l2_euclidean",
    )
    embedding_model: str = Field(
        default="text-embedding-3-small",
        description="Embedding model: text-embedding-ada-002, text-embedding-3-small, text-embedding-3-large",
    )
    top_n: int = Field(default=10, ge=1, le=100, description="Number of results")
    temperature: float = Field(default=0.1, ge=0, le=2, description="LLM temperature")
    max_input_tokens: int = Field(default=10000, description="Max input tokens")
    max_output_tokens: int = Field(default=5000, description="Max output tokens")
    include_match_info: bool = Field(
        default=True, description="Include match information in response"
    )
    system_message: str | None = Field(
        default=None, description="Custom system message for LLM"
    )

    @field_validator("search_algorithm")
    @classmethod
    def validate_algorithm(cls, v: str) -> str:
        """Validate search algorithm."""
        allowed = ["cosine", "inner_product", "l2_euclidean", "l1_manhattan"]
        if v.lower() not in allowed:
            raise ValueError(f"Algorithm must be one of: {', '.join(allowed)}")
        return v.lower()

    @field_validator("embedding_model")
    @classmethod
    def validate_model(cls, v: str) -> str:
        """Validate embedding model."""
        allowed = [
            "text-embedding-ada-002",
            "text-embedding-3-small",
            "text-embedding-3-large",
        ]
        if v not in allowed:
            raise ValueError(f"Model must be one of: {', '.join(allowed)}")
        return v


class SearchResponse(BaseModel):
    """Response model for search."""

    question: str
    normalized_question: str
    answer: str
    search_results: list[SearchResultResponse]
    match_info: MatchDetailResponse | None = None
    metadata: dict = Field(default_factory=dict)

    class Config:
        from_attributes = True


# Pagination models
class PaginatedResponse(BaseModel):
    """Generic paginated response."""

    total: int
    page: int
    page_size: int
    items: list[Any]
