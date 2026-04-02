"""
Chat and search endpoints.

Provides semantic search with LLM-powered responses.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.adapters.openai_client import OpenAIAdapter, get_openai_adapter
from app.api.v1.models import (
    CompetitionResponse,
    EventDetailResponse,
    MatchDetailResponse,
    SearchRequest,
    SearchResponse,
    SearchResultResponse,
    TeamResponse,
)
from app.core.capabilities import validate_search_capabilities
from app.core.dependencies import get_event_repository, get_match_repository
from app.domain.entities import (
    EmbeddingModel,
    SearchAlgorithm,
)
from app.domain.entities import (
    SearchRequest as DomainSearchRequest,
)
from app.repositories.base import EventRepository, MatchRepository
from app.services.search_service import SearchService

router = APIRouter()


@router.post(
    "/chat/search",
    response_model=SearchResponse,
    summary="Semantic search with chat response",
    description="Search match events using embeddings and generate an AI-powered response",
)
async def search_and_chat(
    request: SearchRequest,
    source: str = Query(
        default="postgres",
        description="Database source: postgres or sqlserver",
    ),
    match_repo: MatchRepository = Depends(get_match_repository),
    event_repo: EventRepository = Depends(get_event_repository),
    openai_adapter: OpenAIAdapter = Depends(get_openai_adapter),
) -> SearchResponse:
    """
    Perform semantic search and generate a chat response.

    This endpoint:
    1. Translates the query to English if needed
    2. Generates an embedding for the query
    3. Searches for similar match events using vector similarity
    4. Generates an AI-powered response based on the search results

    Args:
        request: Search request with query and parameters
        source: Database source (postgres or sqlserver)
        match_repo: Match repository (injected)
        event_repo: Event repository (injected)
        openai_adapter: OpenAI adapter (injected)

    Returns:
        SearchResponse with answer and search results
    """
    try:
        # Validate requested model/algorithm against source capabilities
        validate_search_capabilities(
            source=source,
            embedding_model=request.embedding_model,
            search_algorithm=request.search_algorithm,
        )

        # Convert API request to domain request
        domain_request = DomainSearchRequest(
            match_id=request.match_id,
            query=request.query,
            language=request.language,
            search_algorithm=SearchAlgorithm(request.search_algorithm),
            embedding_model=EmbeddingModel(request.embedding_model),
            top_n=request.top_n,
            temperature=request.temperature,
            max_input_tokens=request.max_input_tokens,
            max_output_tokens=request.max_output_tokens,
            include_match_info=request.include_match_info,
            system_message=request.system_message,
        )

        # Create service and execute search
        service = SearchService(
            match_repo=match_repo,
            event_repo=event_repo,
            openai_adapter=openai_adapter,
        )

        result = service.search_and_chat(domain_request)

        # Convert domain response to API response
        search_results = [
            SearchResultResponse(
                event=EventDetailResponse(
                    id=sr.event.id,
                    match_id=sr.event.match_id,
                    period=sr.event.period,
                    minute=sr.event.minute,
                    quarter_minute=sr.event.quarter_minute,
                    count=sr.event.count,
                    summary=sr.event.summary,
                    time_description=sr.event.time_description,
                ),
                similarity_score=sr.similarity_score,
                rank=sr.rank,
            )
            for sr in result.search_results
        ]

        match_info = None
        if result.match_info:
            match = result.match_info
            match_info = MatchDetailResponse(
                match_id=match.match_id,
                match_date=match.match_date,
                competition=CompetitionResponse(
                    competition_id=match.competition.competition_id,
                    country=match.competition.country,
                    name=match.competition.name,
                ),
                season_name=match.season.name,
                home_team=TeamResponse(
                    team_id=match.home_team.team_id,
                    name=match.home_team.name,
                    gender=match.home_team.gender,
                    country=match.home_team.country,
                    manager=match.home_team.manager,
                    manager_country=match.home_team.manager_country,
                ),
                away_team=TeamResponse(
                    team_id=match.away_team.team_id,
                    name=match.away_team.name,
                    gender=match.away_team.gender,
                    country=match.away_team.country,
                    manager=match.away_team.manager,
                    manager_country=match.away_team.manager_country,
                ),
                home_score=match.home_score,
                away_score=match.away_score,
                result=match.result,
                match_week=match.match_week,
                stadium_name=match.stadium.name if match.stadium else None,
                referee_name=match.referee.name if match.referee else None,
                display_name=match.display_name,
            )

        return SearchResponse(
            question=result.question,
            normalized_question=result.normalized_question,
            answer=result.answer,
            search_results=search_results,
            match_info=match_info,
            metadata=result.metadata,
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(e)}",
        )
