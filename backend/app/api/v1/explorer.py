"""Data exploration endpoints for teams, players and table metadata."""

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel

from app.core.capabilities import normalize_source
from app.core.dependencies import ExplorerSvc

router = APIRouter()


class TeamExplorerResponse(BaseModel):
    team_id: int
    name: str
    gender: str | None = None
    country: str | None = None


class PlayerExplorerResponse(BaseModel):
    player_id: int
    player_name: str
    jersey_number: int | None = None
    country_name: str | None = None
    position_name: str | None = None
    team_name: str | None = None


class TableInfoResponse(BaseModel):
    table: str
    row_count: int
    embedding_columns: list[str]


@router.get(
    "/teams",
    response_model=list[TeamExplorerResponse],
    status_code=status.HTTP_200_OK,
    summary="List teams",
)
async def list_teams(
    source: str = Query(default="postgres", description="Database source"),
    match_id: int | None = Query(default=None, description="Optional match filter"),
    limit: int = Query(default=500, ge=1, le=5000),
    service: ExplorerSvc = None,
) -> list[TeamExplorerResponse]:
    try:
        rows = service.get_teams(source=normalize_source(source), match_id=match_id, limit=limit)
        return [TeamExplorerResponse(**row) for row in rows]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch teams: {e}",
        )


@router.get(
    "/players",
    response_model=list[PlayerExplorerResponse],
    status_code=status.HTTP_200_OK,
    summary="List players",
)
async def list_players(
    source: str = Query(default="postgres", description="Database source"),
    match_id: int | None = Query(default=None, description="Optional match filter"),
    limit: int = Query(default=500, ge=1, le=5000),
    service: ExplorerSvc = None,
) -> list[PlayerExplorerResponse]:
    try:
        rows = service.get_players(source=normalize_source(source), match_id=match_id, limit=limit)
        return [PlayerExplorerResponse(**row) for row in rows]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch players: {e}",
        )


@router.get(
    "/tables-info",
    response_model=list[TableInfoResponse],
    status_code=status.HTTP_200_OK,
    summary="List table metadata",
)
async def list_tables_info(
    source: str = Query(default="postgres", description="Database source"),
    service: ExplorerSvc = None,
) -> list[TableInfoResponse]:
    try:
        rows = service.get_tables_info(source=normalize_source(source))
        return [TableInfoResponse(**row) for row in rows]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch tables info: {e}",
        )
