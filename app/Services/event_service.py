# fastapi_backend/services/event_service.py
from typing import List
from fastapi import HTTPException,  Query
from typing import Optional

from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, func
from app.Repository.event_repository import get_events, save_event_repository, get_favorites_repository, event_exists, favorite_exists, get_total_count, apply_sorting, apply_pagination
from app.Repository.user_repository import UserRepository
from app.Models.event import EventSchema, Event
from app.Models.favorite import FavoriteSchema
from app.Models.event import PaginatedEventsResponse, EventFilters

# def get_events_service(db: Session) -> List[EventSchema]:
#     try:
#         return get_events(db)
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Error fetching event names: {str(e)}")
def get_events_service(
        db: Session,
        page: int = 1,
        per_page: int = 10,
        filters: Optional[EventFilters] = None,
        sort_by: str = "start_date",
        sort_order: str = "asc"
    ) -> PaginatedEventsResponse:
        try:
            # Build base query with filters
            query = get_events(db, filters)
            
            # Get total count before pagination
            total = get_total_count(query)
            
            # Apply sorting
            query = apply_sorting(query, sort_by, sort_order)
            
            # Apply pagination and execute query
            events = apply_pagination(query, page, per_page)
            
            # Calculate pagination metadata
            total_pages = (total + per_page - 1) // per_page
            has_next = page < total_pages
            has_prev = page > 1
            
            return PaginatedEventsResponse(
                events=events,
                total=total,
                page=page,
                per_page=per_page,
                total_pages=total_pages,
                has_next=has_next,
                has_prev=has_prev
            )
            
        except Exception as e:
            raise HTTPException(
                status_code=500, 
                detail=f"Error fetching events: {str(e)}"
            )
def get_events_with_pagination(
    db: Session,
    page: int,
    per_page: int,
    filters: EventFilters = None,
    sort_by: str = "start_date",
    sort_order: str = "asc"
) -> PaginatedEventsResponse:
    # Start with base query
    query = db.query(Event)
    
    # Apply filters
    if filters:
        filter_conditions = []
        
        if filters.name:
            filter_conditions.append(Event.name.ilike(f"%{filters.name}%"))
        
        if filters.city:
            filter_conditions.append(Event.city.ilike(f"%{filters.city}%"))
        
        if filters.country:
            filter_conditions.append(Event.country.ilike(f"%{filters.country}%"))
        
        if filters.venue_name:
            filter_conditions.append(Event.venue_name.ilike(f"%{filters.venue_name}%"))
        
        if filters.start_date_from:
            filter_conditions.append(Event.start_date >= filters.start_date_from)
        
        if filters.start_date_to:
            filter_conditions.append(Event.start_date <= filters.start_date_to)
        
        if filters.search:
            # Search across multiple fields
            search_term = f"%{filters.search}%"
            search_conditions = or_(
                Event.name.ilike(search_term),
                Event.description.ilike(search_term),
                Event.venue_name.ilike(search_term),
                Event.city.ilike(search_term)
            )
            filter_conditions.append(search_conditions)
        
        if filter_conditions:
            query = query.filter(and_(*filter_conditions))
    
    # Get total count before pagination
    total = query.count()
    
    # Apply sorting
    sort_column = getattr(Event, sort_by, Event.start_date)
    if sort_order.lower() == "desc":
        query = query.order_by(sort_column.desc())
    else:
        query = query.order_by(sort_column.asc())
    
    # Apply pagination
    offset = (page - 1) * per_page
    events = query.offset(offset).limit(per_page).all()
    
    # Calculate pagination metadata
    total_pages = (total + per_page - 1) // per_page
    has_next = page < total_pages
    has_prev = page > 1
    
    return PaginatedEventsResponse(
        events=events,
        total=total,
        page=page,
        per_page=per_page,
        total_pages=total_pages,
        has_next=has_next,
        has_prev=has_prev
    )

    

def save_event_service(event_id: str, db: Session, user: int) -> FavoriteSchema:
    try:
        if not event_exists(event_id, db):
            raise HTTPException(status_code=404, detail=f"Event with id {event_id} not found")
        elif favorite_exists(event_id, user, db):
            raise HTTPException(status_code=400, detail="Event already saved by user")
        else:
            return save_event_repository(event_id, db, user)
    except HTTPException:
        raise    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving event: {str(e)}")


def get_favorites_service(db: Session, user: int) -> List[FavoriteSchema]:
    try:
        if not UserRepository.user_exists(user, db):
            raise HTTPException(status_code=404, detail=f"User with id {user} not found")
        return get_favorites_repository(db, user)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching favorites: {str(e)}")