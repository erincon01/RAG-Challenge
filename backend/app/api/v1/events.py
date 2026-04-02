"""
Event endpoints.

Provides API endpoints for querying match events.
"""

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status

from app.api.v1.models import EventDetailResponse
from app.core.dependencies import get_event_repository
from app.repositories.base import EventRepository

router = APIRouter()


@router.get(
    "/events",
    response_model=list[EventDetailResponse],
    summary="List events",
    description="Get events for a specific match",
)
async def list_events(
    match_id: int = Query(..., description="Match ID"),
    source: str = Query(
        default="postgres",
        description="Database source: postgres or sqlserver",
    ),
    limit: int | None = Query(default=None, ge=1, le=1000, description="Maximum results"),
    repo: EventRepository = Depends(get_event_repository),
) -> list[EventDetailResponse]:
    """
    List events for a specific match.

    Args:
        match_id: Match ID
        source: Database source (postgres or sqlserver)
        limit: Maximum number of results
        repo: Event repository (injected)

    Returns:
        List of event details
    """
    try:
        events = repo.get_events_by_match(match_id=match_id, limit=limit)

        return [
            EventDetailResponse(
                id=event.id,
                match_id=event.match_id,
                period=event.period,
                minute=event.minute,
                quarter_minute=event.quarter_minute,
                count=event.count,
                summary=event.summary,
                time_description=event.time_description,
            )
            for event in events
        ]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch events: {str(e)}",
        )


@router.get(
    "/events/{event_id}",
    response_model=EventDetailResponse,
    summary="Get event details",
    description="Get detailed information about a specific event",
)
async def get_event(
    event_id: int = Path(..., description="Event ID"),
    source: str = Query(
        default="postgres",
        description="Database source: postgres or sqlserver",
    ),
    repo: EventRepository = Depends(get_event_repository),
) -> EventDetailResponse:
    """
    Get detailed information about a specific event.

    Args:
        event_id: Event ID
        source: Database source (postgres or sqlserver)
        repo: Event repository (injected)

    Returns:
        Event details

    Raises:
        HTTPException: If event not found
    """
    try:
        event = repo.get_event_by_id(event_id)

        if not event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Event with ID {event_id} not found",
            )

        return EventDetailResponse(
            id=event.id,
            match_id=event.match_id,
            period=event.period,
            minute=event.minute,
            quarter_minute=event.quarter_minute,
            count=event.count,
            summary=event.summary,
            time_description=event.time_description,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch event: {str(e)}",
        )
