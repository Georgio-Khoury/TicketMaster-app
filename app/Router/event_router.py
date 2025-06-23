# fastapi_backend/routers/event_router.py
from fastapi import APIRouter, Depends, Query
from datetime import datetime
from typing import List, Optional
from app.Models.event import PaginatedEventsResponse, EventFilters
from sqlalchemy.orm import Session
from app.Services.event_service import (
    get_events_service,
    save_event_service,
    get_favorites_service
)
from app.core.database import get_db
from app.Models.event import Event,EventSchema
from app.Models.favorite import Favorite, FavoriteSchema
from app.core.auth import get_current_user

router = APIRouter(prefix="/events", tags=["Events"])

# @router.get("/", response_model=List[EventSchema])
# def get_event_names(db: Session = Depends(get_db)):
#     return get_events_service(db)
@router.get("/", response_model=PaginatedEventsResponse)
def get_events_endpoint(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(10, ge=1, le=100, description="Items per page"),
    name: Optional[str] = Query(None, description="Filter by event name (partial match)"),
    city: Optional[str] = Query(None, description="Filter by city"),
    country: Optional[str] = Query(None, description="Filter by country"),
    venue_name: Optional[str] = Query(None, description="Filter by venue name"),
    start_date_from: Optional[datetime] = Query(None, description="Filter events starting from this date"),
    start_date_to: Optional[datetime] = Query(None, description="Filter events starting before this date"),
    search: Optional[str] = Query(None, description="Search across name, description, and venue"),
    sort_by: str = Query("start_date", description="Sort by field (start_date, name, created_at)"),
    sort_order: str = Query("asc", regex="^(asc|desc)$", description="Sort order"),
    db: Session = Depends(get_db)
):
    filters = EventFilters(
        name=name,
        city=city,
        country=country,
        venue_name=venue_name,
        start_date_from=start_date_from,
        start_date_to=start_date_to,
        search=search
    )
    
    return get_events_service(
        db=db,
        page=page,
        per_page=per_page,
        filters=filters,
        sort_by=sort_by,
        sort_order=sort_order
    )


@router.post("/{event_id}/save", response_model=FavoriteSchema)
def save_event(
    event_id: str,
    db: Session = Depends(get_db),
    user: int = Depends(get_current_user)
):
    return save_event_service(event_id, db, user)


@router.get("/favorites", response_model=List[FavoriteSchema])
def get_favorite_events(
    db: Session = Depends(get_db),
    user: int = Depends(get_current_user)
):
    return get_favorites_service(db, user)