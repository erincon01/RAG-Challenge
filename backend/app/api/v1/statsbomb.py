"""StatsBomb catalog discovery endpoints."""

from typing import Any

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel

from app.core.dependencies import StatsBombSvc

router = APIRouter()


class StatsBombCompetitionResponse(BaseModel):
    competition_id: int
    competition_name: str
    season_id: int
    season_name: str
    country_name: str | None = None


class StatsBombMatchResponse(BaseModel):
    match_id: int
    match_date: str | None = None
    competition: dict[str, Any] | None = None
    season: dict[str, Any] | None = None
    home_team: dict[str, Any] | None = None
    away_team: dict[str, Any] | None = None
    home_score: int | None = None
    away_score: int | None = None


@router.get(
    "/statsbomb/competitions",
    response_model=list[StatsBombCompetitionResponse],
    status_code=status.HTTP_200_OK,
    summary="List StatsBomb competitions",
)
async def list_statsbomb_competitions(service: StatsBombSvc = None) -> list[StatsBombCompetitionResponse]:
    """Return competitions catalog from local cache or remote StatsBomb open-data."""
    try:
        raw = service.list_competitions()
        items: list[StatsBombCompetitionResponse] = []
        for row in raw:
            if row.get("competition_id") is None or row.get("season_id") is None:
                continue
            items.append(
                StatsBombCompetitionResponse(
                    competition_id=int(row["competition_id"]),
                    competition_name=row.get("competition_name") or "Unknown",
                    season_id=int(row["season_id"]),
                    season_name=row.get("season_name") or "Unknown",
                    country_name=row.get("country_name"),
                )
            )
        items.sort(key=lambda x: (x.competition_name.lower(), x.season_name.lower()))
        return items
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch StatsBomb competitions: {e}",
        )


@router.get(
    "/statsbomb/matches",
    response_model=list[StatsBombMatchResponse],
    status_code=status.HTTP_200_OK,
    summary="List StatsBomb matches for competition and season",
)
async def list_statsbomb_matches(
    competition_id: int = Query(..., description="StatsBomb competition_id"),
    season_id: int = Query(..., description="StatsBomb season_id"),
    service: StatsBombSvc = None,
) -> list[StatsBombMatchResponse]:
    """Return match catalog for a competition-season pair."""
    try:
        matches = service.list_matches(competition_id=competition_id, season_id=season_id)
        return [
            StatsBombMatchResponse(
                match_id=int(m["match_id"]),
                match_date=m.get("match_date"),
                competition=m.get("competition"),
                season=m.get("season"),
                home_team=m.get("home_team"),
                away_team=m.get("away_team"),
                home_score=m.get("home_score"),
                away_score=m.get("away_score"),
            )
            for m in matches
            if m.get("match_id") is not None
        ]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch StatsBomb matches: {e}",
        )
