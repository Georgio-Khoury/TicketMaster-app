from sqlalchemy import Column, Integer, ForeignKey, DateTime, UniqueConstraint, String
from datetime import datetime
from pydantic import BaseModel
from app.core.database import Base

class Favorite(Base):
    __tablename__ = "favorites"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    event_id = Column(String, ForeignKey("events.id", ondelete="CASCADE"))
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("user_id", "event_id", name="uq_user_event"),
    )

#pydantic model
class FavoriteSchema(BaseModel):
    id: int
    user_id: int
    event_id: str
    created_at: datetime

    class Config:
        orm_mode = True
        from_attributes = True  # For Pydantic v2 compatibility

