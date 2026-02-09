"""Authentication middleware for Commerce service."""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt
from typing import Optional
from datetime import datetime, timedelta
from core.config import settings


security = HTTPBearer()


async def verify_jwt_token(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> dict:
    """
    Verify JWT token from Core service.
    Shared secret with Core service for verification.
    """
    token = credentials.credentials
    
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=["HS256"]
        )
        
        # Check expiration
        exp = payload.get("exp")
        if exp and datetime.fromtimestamp(exp) < datetime.utcnow():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired"
            )
        
        return payload
    
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired"
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token"
        )


async def get_current_user(token_data: dict = Depends(verify_jwt_token)) -> dict:
    """
    Get current authenticated user from token.
    Returns user data from JWT payload.
    """
    user_id = token_data.get("user_id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload"
        )
    
    return {
        "user_id": user_id,
        "email": token_data.get("email"),
        "role": token_data.get("role", "user"),
        "name": token_data.get("name")
    }


async def require_admin(user: dict = Depends(get_current_user)) -> dict:
    """
    Require admin role for endpoint access.
    Raises 403 if user is not admin.
    """
    if user.get("role") not in ["admin", "staff"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin or staff access required"
        )
    return user


async def require_staff(user: dict = Depends(get_current_user)) -> dict:
    """
    Require staff or admin role for endpoint access.
    Raises 403 if user is regular user.
    """
    if user.get("role") not in ["admin", "staff"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Staff access required"
        )
    return user


# Optional authentication (allows both authenticated and anonymous)
async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False))
) -> Optional[dict]:
    """
    Get current user if authenticated, None otherwise.
    Useful for endpoints that work for both authenticated and anonymous users.
    """
    if not credentials:
        return None
    
    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.SECRET_KEY,
            algorithms=["HS256"]
        )
        
        user_id = payload.get("user_id")
        if not user_id:
            return None
        
        return {
            "user_id": user_id,
            "email": payload.get("email"),
            "role": payload.get("role", "user"),
            "name": payload.get("name")
        }
    except:
        return None
