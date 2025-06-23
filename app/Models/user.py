from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime
from pydantic import BaseModel
from app.core.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    name = Column(String) 
    created_at = Column(DateTime, default=datetime.utcnow)

#pydantic model
class UserSchema(BaseModel):
    id: int
    email: str
    name: str | None = None
    created_at: datetime

    class Config:
        orm_mode = True
        from_attributes = True  # For Pydantic v2 compatibility