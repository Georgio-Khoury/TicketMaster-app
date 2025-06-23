# repositories/user_repository.py
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.Models.user import User
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class UserRepository:
    def __init__(self, db: Session):
        self.db = db
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email address"""
        try:
            return self.db.query(User).filter(User.email == email).first()
        except Exception as e:
            logger.error(f"Error fetching user by email {email}: {e}")
            return None
    
    def create_user(self, email: str, name: str = None) -> Optional[User]:
        """Create a new user"""
        try:
            user = User(email=email, name=name)
            self.db.add(user)
            self.db.commit()
            self.db.refresh(user)
            logger.info(f"Created new user: {email}")
            return user
        except IntegrityError as e:
            logger.warning(f"User with email {email} already exists")
            self.db.rollback()
            # If user already exists, fetch and return existing user
            return self.get_user_by_email(email)
        except Exception as e:
            logger.error(f"Error creating user {email}: {e}")
            self.db.rollback()
            return None
    
    def get_or_create_user(self, email: str, name: str = None) -> Optional[User]:
        """Get existing user or create new one if doesn't exist"""
        user = self.get_user_by_email(email)
        if not user:
            user = self.create_user(email, name)
        else:
            # Update name if provided and different
            if name and user.name != name:
                user.name = name
                try:
                    self.db.commit()
                    self.db.refresh(user)
                    logger.info(f"Updated name for user {email}")
                except Exception as e:
                    logger.error(f"Error updating user name: {e}")
                    self.db.rollback()
        return user
    
    def update_user(self, user_id: int, **kwargs) -> Optional[User]:
        """Update user information"""
        try:
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                return None
            
            for key, value in kwargs.items():
                if hasattr(user, key):
                    setattr(user, key, value)
            
            self.db.commit()
            self.db.refresh(user)
            logger.info(f"Updated user {user.email}")
            return user
        except Exception as e:
            logger.error(f"Error updating user {user_id}: {e}")
            self.db.rollback()
            return None
    #check if user exists by id
    def user_exists(self, user_id: int) -> bool:
        """Check if user exists by ID"""
        try:
            return self.db.query(User).filter(User.id == user_id).first() is not None
        except Exception as e:
            logger.error(f"Error checking if user exists {user_id}: {e}")
            return False