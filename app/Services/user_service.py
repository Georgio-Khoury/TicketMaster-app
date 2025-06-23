# services/user_service.py
from sqlalchemy.orm import Session
from app.Repository.user_repository import UserRepository
from app.Models.user import User, UserSchema
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

class UserService:
    def __init__(self, db: Session):
        self.db = db
        self.user_repository = UserRepository(db)
    
    def authenticate_or_create_user(self, google_user_info: Dict[str, Any]) -> Optional[UserSchema]:
        """
        Authenticate user from Google OAuth and create if doesn't exist
        
        Args:
            google_user_info: Dictionary containing user info from Google OAuth
            
        Returns:
            UserSchema object or None if operation failed
        """
        try:
            email = google_user_info.get('email')
            name = google_user_info.get('name', '')
            
            if not email:
                logger.error("No email provided in Google user info")
                return None
            
            # Get or create user
            user = self.user_repository.get_or_create_user(email=email, name=name)
            
            if not user:
                logger.error(f"Failed to get or create user for email: {email}")
                return None
            
            # Convert to Pydantic model
            return UserSchema.from_orm(user)
            
        except Exception as e:
            logger.error(f"Error in authenticate_or_create_user: {e}")
            return None
    
    def get_user_by_email(self, email: str) -> Optional[UserSchema]:
        """Get user by email"""
        try:
            user = self.user_repository.get_user_by_email(email)
            if user:
                return UserSchema.from_orm(user)
            return None
        except Exception as e:
            logger.error(f"Error getting user by email {email}: {e}")
            return None
    
    def update_user_profile(self, user_id: int, update_data: Dict[str, Any]) -> Optional[UserSchema]:
        """Update user profile information"""
        try:
            user = self.user_repository.update_user(user_id, **update_data)
            if user:
                return UserSchema.from_orm(user)
            return None
        except Exception as e:
            logger.error(f"Error updating user profile {user_id}: {e}")
            return None
    
    def create_user_session_data(self, user: UserSchema, google_user_info: Dict[str, Any]) -> Dict[str, Any]:
        """Create session data for authenticated user"""
        return {
            'user_id': user.id,
            'email': user.email,
            'name': user.name or google_user_info.get('name', ''),
            'picture': google_user_info.get('picture', ''),
        }