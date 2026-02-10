"""Authentication middleware for Admin service — admin/staff only."""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt
from typing import Optional
from core.config import settings


security = HTTPBearer()


async def verify_jwt_token(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> dict:
    """Verify JWT token from Core service."""
    token = credentials.credentials
    
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
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
    """Get current authenticated user from token."""
    user_id = token_data.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload"
        )
    
    return {
        "user_id": user_id,
        "username": token_data.get("username"),
        "email": token_data.get("email"),
        "role": token_data.get("role", "customer"),
    }


async def require_admin(user: dict = Depends(get_current_user)) -> dict:
    """Require admin role — full dashboard access."""
    if user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return user


async def require_staff(user: dict = Depends(get_current_user)) -> dict:
    """Require staff or admin role — inventory & order operations."""
    if user.get("role") not in ["admin", "staff"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Staff access required"
        )
    return user


async def require_admin_or_staff(user: dict = Depends(get_current_user)) -> dict:
    """Alias for require_staff — admin or staff role."""
    if user.get("role") not in ["admin", "staff"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin or staff access required"
        )
    return user
