"""
Match endpoints.

Provides API endpoints for querying matches and competitions.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Path, status

from app.api.v1.models import (
    MatchSummaryResponse,
    MatchDetailResponse,
    CompetitionResponse,
)
from app.domain.entities import Match, Competition
from app.domain.exceptions import EntityNotFoundError
from app.repositories.base import MatchRepository
from app.core.dependencies import get_match_repository

router = APIRouter()


@router.get(
    "/competitions",
    response_model=List[CompetitionResponse],
    summary="List all competitions",
    description="Get a list of all available competitions",
)
async def list_competitions(
    source: str = Query(
        default="postgres",
        description="Database source: postgres or sqlserver",
    ),
    repo: MatchRepository = Depends(get_match_repository),
) -> List[CompetitionResponse]:
    """
    List all available competitions.

    Args:
        source: Database source (postgres or sqlserver)
        repo: Match repository (injected)

    Returns:
        List of competitions
    """
    try:
        competitions = repo.get_competitions()

        return [
            CompetitionResponse(
                competition_id=comp.competition_id,
                country=comp.country,
                name=comp.name,
            )
            for comp in competitions
        ]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch competitions: {str(e)}",
        )


@router.get(
    "/matches",
    response_model=List[MatchSummaryResponse],
    summary="List matches",
    description="Get a list of matches with optional filters",
)
async def list_matches(
    source: str = Query(
        default="postgres",
        description="Database source: postgres or sqlserver",
    ),
    competition_name: Optional[str] = Query(
        default=None, description="Filter by competition name"
    ),
    season_name: Optional[str] = Query(
        default=None, description="Filter by season name"
    ),
    limit: int = Query(default=100, ge=1, le=1000, description="Maximum results"),
    repo: MatchRepository = Depends(get_match_repository),
) -> List[MatchSummaryResponse]:
    """
    List matches with optional filters.

    Args:
        source: Database source (postgres or sqlserver)
        competition_name: Filter by competition name
        season_name: Filter by season name
        limit: Maximum number of results
        repo: Match repository (injected)

    Returns:
        List of match summaries
    """
    try:
        matches = repo.get_all(
            competition_name=competition_name,
            season_name=season_name,
            limit=limit,
        )

        return [
            MatchSummaryResponse(
                match_id=match.match_id,
                match_date=match.match_date,
                competition_name=match.competition.name,
                season_name=match.season.name,
                home_team_name=match.home_team.name,
                away_team_name=match.away_team.name,
                home_score=match.home_score,
                away_score=match.away_score,
                result=match.result,
                display_name=match.display_name,
            )
            for match in matches
        ]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch matches: {str(e)}",
        )


@router.get(
    "/matches/{match_id}",
    response_model=MatchDetailResponse,
    summary="Get match details",
    description="Get detailed information about a specific match",
)
async def get_match(
    match_id: int = Path(..., description="Match ID"),
    source: str = Query(
        default="postgres",
        description="Database source: postgres or sqlserver",
    ),
    repo: MatchRepository = Depends(get_match_repository),
) -> MatchDetailResponse:
    """
    Get detailed information about a specific match.

    Args:
        match_id: Match ID
        source: Database source (postgres or sqlserver)
        repo: Match repository (injected)

    Returns:
        Match details

    Raises:
        HTTPException: If match not found
    """
    try:
        match = repo.get_by_id(match_id)

        if not match:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Match with ID {match_id} not found",
            )

        return MatchDetailResponse(
            match_id=match.match_id,
            match_date=match.match_date,
            competition=CompetitionResponse(
                competition_id=match.competition.competition_id,
                country=match.competition.country,
                name=match.competition.name,
            ),
            season_name=match.season.name,
            home_team=match.home_team,
            away_team=match.away_team,
            home_score=match.home_score,
            away_score=match.away_score,
            result=match.result,
            match_week=match.match_week,
            stadium_name=match.stadium.name if match.stadium else None,
            referee_name=match.referee.name if match.referee else None,
            display_name=match.display_name,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch match: {str(e)}",
        )
