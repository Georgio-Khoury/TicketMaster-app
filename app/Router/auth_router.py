# routers/auth_router.py
from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import RedirectResponse, JSONResponse
from datetime import timedelta
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.Services.user_service import UserService
from app.core.auth import (
    oauth, 
    create_token_pair,  
    refresh_access_token,  
    SECRET_KEY, 
    ALGORITHM, 
    ACCESS_TOKEN_EXPIRE_MINUTES
)
from pydantic import BaseModel
import httpx
import logging

# Set up logging to see what's happening
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])

# Pydantic models for request/response
class RefreshTokenRequest(BaseModel):
    refresh_token: str

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int
    user_info: dict

@router.get("/login/google")
async def login_google(request: Request):
    redirect_uri = request.url_for('auth_google')
    return await oauth.google.authorize_redirect(request, redirect_uri)


@router.get("/google/callback")
async def auth_google(request: Request, db: Session = Depends(get_db)):
    try:
        # Step 1: Exchange authorization code for tokens
        token = await oauth.google.authorize_access_token(request)
        logger.info(f"Token keys received: {list(token.keys())}")
        user_info = None
        
        # Method 1: Try to parse ID token if it exists
        if 'id_token' in token:
            try:
                logger.info("Attempting to parse ID token...")
                user_info = await oauth.google.parse_id_token(request, token)
                logger.info("Successfully parsed ID token")
            except Exception as e:
                logger.warning(f"Failed to parse ID token: {e}")
        
        # Method 2: Fallback to Google's userinfo endpoint
        if not user_info and 'access_token' in token:
            try:
                logger.info("Fetching user info from Google API...")
                async with httpx.AsyncClient() as client:
                    response = await client.get(
                        'https://www.googleapis.com/oauth2/v2/userinfo',
                        headers={'Authorization': f'Bearer {token["access_token"]}'}
                    )
                    
                    if response.status_code == 200:
                        user_info = response.json()
                        logger.info("Successfully fetched user info from API")
                    else:
                        logger.error(f"Failed to fetch user info: {response.status_code} - {response.text}")
                        
            except Exception as e:
                logger.error(f"Error fetching user info: {e}")
        
        # Method 3: Try OpenID Connect userinfo endpoint as final fallback
        if not user_info and 'access_token' in token:
            try:
                logger.info("Trying OpenID Connect userinfo endpoint...")
                async with httpx.AsyncClient() as client:
                    response = await client.get(
                        'https://openidconnect.googleapis.com/v1/userinfo',
                        headers={'Authorization': f'Bearer {token["access_token"]}'}
                    )
                    
                    if response.status_code == 200:
                        user_info = response.json()
                        logger.info("Successfully fetched user info from OpenID Connect")
                    else:
                        logger.error(f"OpenID Connect failed: {response.status_code} - {response.text}")
                        
            except Exception as e:
                logger.error(f"Error with OpenID Connect: {e}")
        
        # Check if we got user info
        if not user_info:
            logger.error("Failed to get user information from all methods")
            raise HTTPException(
                status_code=400,
                detail="Failed to retrieve user information from Google"
            )
        
        # Validate required fields
        if not user_info.get('email'):
            logger.error("No email found in user info")
            raise HTTPException(
                status_code=400,
                detail="No email address found in Google account"
            )
        
        # Initialize user service and authenticate/create user
        user_service = UserService(db)
        user = user_service.authenticate_or_create_user(user_info)
        
        if not user:
            logger.error("Failed to authenticate or create user")
            raise HTTPException(
                status_code=500,
                detail="Failed to authenticate user"
            )
        
        # Create token pair (access + refresh tokens)
        token_data = {
            "sub": user.email,
            "user_id": str(user.id),
            "name": user.name or user_info.get("name", "")
        }
        
        tokens = create_token_pair(token_data)
        
        # Create session data
        session_data = user_service.create_user_session_data(user, user_info)
        request.session['user'] = session_data
        
        logger.info(f"Successfully authenticated user: {user.email} (ID: {user.id})")
        
        return JSONResponse({
            "access_token": tokens["access_token"],
            "refresh_token": tokens["refresh_token"],
            "token_type": tokens["token_type"],
            "expires_in": tokens["expires_in"],
            "user_info": {
                "id": user.id,
                "email": user.email,
                "name": user.name or user_info.get("name", ""),
                "picture": user_info.get("picture", "")
            }
        })
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Unexpected authentication error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Authentication failed: {str(e)}"
        )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    token_request: RefreshTokenRequest,
    db: Session = Depends(get_db)
):
    try:
        logger.info("Attempting to refresh access token")
        
        # Use the refresh_access_token function from auth.py
        tokens = await refresh_access_token(token_request.refresh_token, db)
        
        # Get user info for response
        user_service = UserService(db)
        # Extract email from the new access token to get user info
        from app.core.auth import verify_token
        payload = verify_token(tokens["access_token"], "access")
        
        if payload:
            user = user_service.get_user_by_email(payload.get("sub"))
            user_info = {
                "id": user.id,
                "email": user.email,
                "name": user.name,
                "picture": getattr(user, 'picture', '')
            } if user else {}
        else:
            user_info = {}
        
        logger.info("Successfully refreshed access token")
        
        return JSONResponse({
            "access_token": tokens["access_token"],
            "refresh_token": tokens["refresh_token"],
            "token_type": tokens["token_type"],
            "expires_in": tokens["expires_in"],
            "user_info": user_info
        })
        
    except HTTPException as he:
        logger.error(f"HTTP error during token refresh: {he.detail}")
        raise he
    except Exception as e:
        logger.error(f"Unexpected error during token refresh: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to refresh token"
        )


@router.get("/validate")
async def validate_token(request: Request, db: Session = Depends(get_db)):

    try:
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(
                status_code=401,
                detail="Missing or invalid authorization header"
            )
        
        token = auth_header.split(" ")[1]
        
        from app.core.auth import verify_token
        payload = verify_token(token, "access")
        
        if not payload:
            raise HTTPException(
                status_code=401,
                detail="Invalid or expired token"
            )
        
        # Get user info
        user_service = UserService(db)
        user = user_service.get_user_by_email(payload.get("sub"))
        
        if not user:
            raise HTTPException(
                status_code=401,
                detail="User not found"
            )
        
        return {
            "valid": True,
            "user": {
                "id": user.id,
                "email": user.email,
                "name": user.name,
                "picture": getattr(user, 'picture', '')
            },
            "expires_at": payload.get("exp")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error validating token: {e}")
        raise HTTPException(
            status_code=500,
            detail="Token validation failed"
        )