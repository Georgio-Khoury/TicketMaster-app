# fastapi_backend/repositories/event_repository.py
from typing import List
from sqlalchemy.orm import Session
from app.Models.event import Event, EventSchema
from app.Models.favorite import Favorite, FavoriteSchema
from sqlalchemy import or_, and_, func
from app.Models.event import PaginatedEventsResponse, EventFilters

def get_events(db: Session, filters: EventFilters = None):
        """Builds the base query with filters applied"""
        query = db.query(Event)
        
        if not filters:
            return query
            
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
            
        return query
def save_event_repository(event_id: str, db: Session, user: int) -> FavoriteSchema:
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise ValueError(f"Event with id {event_id} not found")
    
    # Assuming you have a Favorite model to save the favorite event
    favorite = Favorite(user_id=user.id, event_id=event.id)
    db.add(favorite)
    db.commit()
    db.refresh(favorite)
    
    return FavoriteSchema.from_orm(favorite)  # Convert to EventSchema for response

def get_favorites_repository(db: Session, user: int) -> List[FavoriteSchema]:
    """
    Get all favorite events for the current user.
    """
    favorites = db.query(Favorite).filter(Favorite.user_id == user.id).all()
    return [FavoriteSchema.from_orm(favorite) for favorite in favorites]  # Convert to FavoriteSchema for response

#check if the event exists
def event_exists(event_id: str, db: Session) -> bool:
    """
    Check if an event exists in the database.
    """
    return db.query(Event).filter(Event.id == event_id).first() is not None

#check if the favorite exists
def favorite_exists(event_id: str, user: int, db: Session) -> bool:
    """
    Check if a favorite event exists for the user.
    """
    return db.query(Favorite).filter(Favorite.event_id == event_id, Favorite.user_id == user.id).first() is not None

def get_total_count(query):
        """Returns the total count of records"""
        return query.count()

def apply_sorting(query, sort_by: str = "start_date", sort_order: str = "asc"):
        """Applies sorting to the query"""
        sort_column = getattr(Event, sort_by, Event.start_date)
        if sort_order.lower() == "desc":
            return query.order_by(sort_column.desc())
        return query.order_by(sort_column.asc())

def apply_pagination(query, page: int, per_page: int):
        """Applies pagination to the query"""
        offset = (page - 1) * per_page
        return query.offset(offset).limit(per_page).all()