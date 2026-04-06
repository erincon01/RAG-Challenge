"""
Match endpoints.

Provides API endpoints for querying matches and competitions.
"""

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status

from app.api.v1.models import (
    CompetitionResponse,
    MatchDetailResponse,
    MatchSummaryResponse,
    TeamResponse,
)
from app.core.dependencies import get_match_repository
from app.repositories.base import MatchRepository

router = APIRouter()


@router.get(
    "/competitions",
    response_model=list[CompetitionResponse],
    summary="List all competitions",
    description="Get a list of all available competitions",
)
async def list_competitions(
    source: str = Query(
        default="postgres",
        description="Database source: postgres or sqlserver",
    ),
    repo: MatchRepository = Depends(get_match_repository),
) -> list[CompetitionResponse]:
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
    response_model=list[MatchSummaryResponse],
    summary="List matches",
    description="Get a list of matches with optional filters",
)
async def list_matches(
    source: str = Query(
        default="postgres",
        description="Database source: postgres or sqlserver",
    ),
    competition_name: str | None = Query(
        default=None, description="Filter by competition name"
    ),
    season_name: str | None = Query(default=None, description="Filter by season name"),
    limit: int = Query(default=100, ge=1, le=1000, description="Maximum results"),
    repo: MatchRepository = Depends(get_match_repository),
) -> list[MatchSummaryResponse]:
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
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch match: {str(e)}",
        )
