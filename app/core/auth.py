
# core/auth.py
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2AuthorizationCodeBearer, HTTPAuthorizationCredentials, HTTPBearer
from authlib.integrations.starlette_client import OAuth
from starlette.config import Config
from starlette.middleware.sessions import SessionMiddleware
from starlette.requests import Request
from jose import jwt, JWTError
from datetime import datetime, timedelta
from typing import Optional, Dict
from app.core.database import get_db
from sqlalchemy.orm import Session
from app.Services.user_service import UserService
import os
import secrets
from app.Models.user import User, UserSchema

config = Config('.env')
GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID', config('GOOGLE_CLIENT_ID', default=''))
GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET', config('GOOGLE_CLIENT_SECRET', default=''))
SECRET_KEY = os.getenv('SECRET_KEY', config('SECRET_KEY', default='your-secret-key-here'))
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 30

oauth = OAuth()
oauth.register(
    name='google',
    client_id=GOOGLE_CLIENT_ID,
    client_secret=GOOGLE_CLIENT_SECRET,
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={
        'scope': 'openid email profile',
        'response_type': 'code',
    },
  
    authorize_params={
        'access_type': 'offline',
        'response_type': 'code',
        'prompt': 'consent',
    }
)
security = HTTPBearer()

oauth2_scheme = OAuth2AuthorizationCodeBearer(
    authorizationUrl="https://accounts.google.com/o/oauth2/auth",
    tokenUrl="https://accounts.google.com/o/oauth2/token",
)

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: dict) -> str:
    """Create JWT refresh token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    
    to_encode.update({
        "exp": expire,
        "type": "refresh",
        "jti": secrets.token_urlsafe(32)  # Unique token ID for revocation
    })
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt
    
def verify_token(token: str) -> Optional[dict]:
    """Verify and decode JWT token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None
    
def create_token_pair(user_data: dict) -> Dict[str, str]:
    """Create both access and refresh tokens"""
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    access_token = create_access_token(
        data=user_data,
        expires_delta=access_token_expires
    )
    
    refresh_token = create_refresh_token(data=user_data)
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> UserSchema:
    """
    Dependency to get current authenticated user from JWT token
    Use this in your route dependencies like: user = Depends(get_current_user)
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # Verify the token
    payload = verify_token(credentials.credentials)
    if payload is None:
        raise credentials_exception
    
    # Get user email from token
    email = payload.get("sub")
    user_id = payload.get("user_id")
    
    if email is None:
        raise credentials_exception
    
    # Get user from database
    user_service = UserService(db)
    user = user_service.get_user_by_email(email)
    
    if user is None:
        raise credentials_exception
    
    return user


async def refresh_access_token(
    refresh_token: str,
    db: Session = Depends(get_db)
) -> Dict[str, str]:
    """
    Generate new access token using refresh token
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid refresh token",
    )
    
    # Verify refresh token
    payload = verify_token(refresh_token, "refresh")
    if payload is None:
        raise credentials_exception
    
    # Get user info from token
    email = payload.get("sub")
    user_id = payload.get("user_id")
    
    if email is None:
        raise credentials_exception
    
    # Verify user still exists
    user_service = UserService(db)
    user = user_service.get_user_by_email(email)
    
    if user is None:
        raise credentials_exception
    
    # Create new token pair
    user_data = {
        "sub": user.email,
        "user_id": str(user.id),
        "name": user.name
    }
    
    return create_token_pair(user_data)