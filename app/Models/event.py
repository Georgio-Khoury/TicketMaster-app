from sqlalchemy import Column, String, DateTime, Text, JSON
from datetime import datetime
from app.core.database import Base
from pydantic import BaseModel
from typing import List, Optional

class Event(Base):
    __tablename__ = "events"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    start_date = Column(DateTime)
    venue_name = Column(String)
    city = Column(String)
    country = Column(String)
    url = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

#pydantic model
class EventSchema(BaseModel):
    id: str
    name: str
    description: str | None = None
    start_date: datetime | None = None
    venue_name: str | None = None
    city: str | None = None
    country: str | None = None
    url: str | None = None
    created_at: datetime | None = None
    class Config:
        orm_mode = True
        from_attributes = True  # For Pydantic v2 compatibility

class PaginatedEventsResponse(BaseModel):
    events: List[EventSchema]
    total: int
    page: int
    per_page: int
    total_pages: int
    has_next: bool
    has_prev: bool
    class Config:
        orm_mode = True
        from_attributes = True  # For Pydantic v2 compatibility

# Query parameters model
class EventFilters(BaseModel):
    name: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    venue_name: Optional[str] = None
    start_date_from: Optional[datetime] = None
    start_date_to: Optional[datetime] = None
    search: Optional[str] = None

    
    class Config:
        orm_mode = True
        from_attributes = True  # For Pydantic v2 compatibility