"""
Core Platform Service - Aarya Clothing
User Management, Authentication, and Session Services

This service handles:
- User registration and management
- Authentication (JWT + Refresh Tokens)
- Cookie-based sessions (24-hour login)
- OTP verification (Email/WhatsApp)
- Session management
- Profile management
"""
import re
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from fastapi import FastAPI, Depends, HTTPException, status, Request, BackgroundTasks, Response
from fastapi.security import OAuth2PasswordBearer
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import Optional

from core.config import settings
from core.redis_client import redis_client
from database.database import get_db, init_db
from models.user import User, UserRole
from schemas.auth import (
    UserCreate, UserResponse, UserUpdate,
    Token, LoginRequest, LoginResponse,
    TokenRefresh, ChangePasswordRequest,
    ForgotPasswordRequest, PasswordResetConfirm
)
from schemas.otp import (
    OTPSendRequest, OTPVerifyRequest, OTPResendRequest,
    OTPSendResponse, OTPVerifyResponse
)
from service.auth_service import AuthService
from service.otp_service import OTPService


# ==================== Lifespan ====================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    init_db()
    
    # Verify Redis connection
    if redis_client.ping():
        print("✓ Redis connected")
    else:
        print("✗ Redis connection failed")
    
    yield
    
    # Shutdown
    pass


# ==================== Cookie Helper ====================

def set_auth_cookies(response: Response, auth_data: dict, remember_me: bool = False):
    """Set authentication cookies on response."""
    tokens = auth_data["tokens"]
    session = auth_data["session"]
    
    # Access token cookie (30 minutes)
    access_max_age = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    
    # Refresh token cookie (24 hours if remember_me)
    refresh_max_age = (
        settings.REFRESH_TOKEN_EXPIRE_MINUTES * 60 
        if remember_me 
        else settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )
    
    # Session cookie (24 hours)
    session_max_age = settings.SESSION_EXPIRE_MINUTES * 60
    
    # Set cookies
    response.set_cookie(
        key="access_token",
        value=tokens["access_token"],
        httponly=settings.COOKIE_HTTPONLY,
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
        max_age=access_max_age,
        path="/"
    )
    
    response.set_cookie(
        key="refresh_token",
        value=tokens["refresh_token"],
        httponly=settings.COOKIE_HTTPONLY,
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
        max_age=refresh_max_age,
        path="/api/v1/auth/refresh"
    )
    
    response.set_cookie(
        key="session_id",
        value=session["session_id"],
        httponly=settings.COOKIE_HTTPONLY,
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
        max_age=session_max_age,
        path="/"
    )


def clear_auth_cookies(response: Response):
    """Clear all authentication cookies."""
    response.delete_cookie("access_token", path="/")
    response.delete_cookie("refresh_token", path="/api/v1/auth/refresh")
    response.delete_cookie("session_id", path="/")


# ==================== FastAPI App ====================

app = FastAPI(
    title="Aarya Clothing - Core Platform",
    description="User Management, Authentication, Cookie Sessions, OTP Verification",
    version="1.0.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==================== Health Check ====================

@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint."""
    redis_status = "healthy" if redis_client.ping() else "unhealthy"
    return {
        "status": "healthy",
        "service": "core-platform",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat(),
        "dependencies": {
            "redis": redis_status,
            "database": "healthy"
        }
    }


# ==================== Authentication Routes ====================

@app.post("/api/v1/auth/register", response_model=UserResponse, 
          status_code=status.HTTP_201_CREATED,
          tags=["Authentication"])
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """Register a new user."""
    auth_service = AuthService(db)
    return auth_service.create_user(user_data)


@app.post("/api/v1/auth/login", response_model=LoginResponse,
          tags=["Authentication"])
async def login(
    request: LoginRequest,
    response: Response,
    db: Session = Depends(get_db)
):
    """
    Login with username/email and password.
    Sets HTTP-Only cookies for 24-hour session.
    """
    auth_service = AuthService(db)
    
    result = auth_service.login(
        username=request.username,
        password=request.password,
        remember_me=request.remember_me
    )
    
    # Set authentication cookies
    set_auth_cookies(response, result, request.remember_me)
    
    return LoginResponse(
        user=UserResponse.model_validate(result["user"]),
        tokens=Token(**result["tokens"]),
        session_id=result["session"]["session_id"]
    )


@app.post("/api/v1/auth/refresh", response_model=Token,
          tags=["Authentication"])
async def refresh_token(
    response: Response,
    refresh_token: str = None,
    request: Request = None
):
    """
    Refresh access token using refresh token cookie.
    Automatically extends session.
    """
    # Get refresh token from cookie or body
    if refresh_token is None and request:
        refresh_token = request.cookies.get("refresh_token")
    
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token not found"
        )
    
    auth_service = AuthService(None)  # No DB needed for refresh
    
    tokens = auth_service.refresh_access_token(refresh_token)
    
    # Set new access token cookie
    response.set_cookie(
        key="access_token",
        value=tokens["access_token"],
        httponly=settings.COOKIE_HTTPONLY,
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        path="/"
    )
    
    return Token(**tokens)


@app.post("/api/v1/auth/logout", status_code=status.HTTP_200_OK,
          tags=["Authentication"])
async def logout(
    response: Response,
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Logout and clear all authentication cookies."""
    session_id = request.cookies.get("session_id")
    refresh_token = request.cookies.get("refresh_token")
    
    # Get user from session if available
    if session_id:
        session_data = redis_client.get_session(session_id)
        user_id = session_data.get("user_id") if session_data else None
    else:
        user_id = None
    
    # Revoke tokens
    if user_id and refresh_token:
        auth_service = AuthService(db)
        background_tasks.add_task(auth_service.logout, user_id, refresh_token)
    
    # Clear cookies
    clear_auth_cookies(response)
    
    return {"detail": "Successfully logged out"}


@app.post("/api/v1/auth/logout-all", status_code=status.HTTP_200_OK,
          tags=["Authentication"])
async def logout_all(
    response: Response,
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Logout from all devices."""
    session_id = request.cookies.get("session_id")
    
    if session_id:
        session_data = redis_client.get_session(session_id)
        if session_data:
            user_id = session_data.get("user_id")
            if user_id:
                auth_service = AuthService(db)
                background_tasks.add_task(auth_service.logout_all, user_id)
    
    clear_auth_cookies(response)
    
    return {"detail": "Logged out from all devices"}


@app.post("/api/v1/auth/change-password", status_code=status.HTTP_200_OK,
          tags=["Authentication"])
async def change_password(
    password_data: ChangePasswordRequest,
    current_user: User = Depends(AuthService.get_current_user),
    db: Session = Depends(get_db)
):
    """Change password for authenticated user."""
    auth_service = AuthService(db)
    
    success = auth_service.change_password(
        user=current_user,
        current_password=password_data.current_password,
        new_password=password_data.new_password
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )
    
    return {"detail": "Password changed successfully"}


# ==================== Password Reset Routes ====================

@app.post("/api/v1/auth/forgot-password", status_code=status.HTTP_200_OK,
          tags=["Authentication"])
async def forgot_password(
    request_data: ForgotPasswordRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Request password reset email.
    Sends a password reset link to the user's email if it exists.
    """
    auth_service = AuthService(db)
    
    # Get frontend URL from referer or use default
    frontend_url = request.headers.get("origin", "http://localhost:3000")
    
    try:
        result = auth_service.request_password_reset(
            email=request_data.email,
            frontend_url=frontend_url
        )
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=str(e)
        )


@app.post("/api/v1/auth/reset-password", status_code=status.HTTP_200_OK,
          tags=["Authentication"])
async def reset_password(
    request_data: PasswordResetConfirm,
    db: Session = Depends(get_db)
):
    """
    Reset password using token from email.
    """
    auth_service = AuthService(db)
    
    try:
        result = auth_service.reset_password(
            token=request_data.token,
            new_password=request_data.new_password
        )
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@app.get("/api/v1/auth/verify-reset-token/{token}", status_code=status.HTTP_200_OK,
         tags=["Authentication"])
async def verify_reset_token(
    token: str,
    db: Session = Depends(get_db)
):
    """
    Verify if a password reset token is valid.
    """
    auth_service = AuthService(db)
    user = auth_service.verify_reset_token(token)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired password reset token"
        )
    
    return {"valid": True, "email": user.email}


# ==================== OTP Routes ====================

@app.post("/api/v1/auth/send-otp", response_model=OTPSendResponse,
          tags=["OTP Verification"])
async def send_otp(
    request: OTPSendRequest,
    db: Session = Depends(get_db)
):
    """Send OTP via email or WhatsApp."""
    otp_service = OTPService(db)
    return otp_service.send_otp(request)


@app.post("/api/v1/auth/verify-otp", response_model=OTPVerifyResponse,
          tags=["OTP Verification"])
async def verify_otp(
    request: OTPVerifyRequest,
    db: Session = Depends(get_db)
):
    """Verify OTP code."""
    otp_service = OTPService(db)
    return otp_service.verify_otp(request)


@app.post("/api/v1/auth/resend-otp", response_model=OTPSendResponse,
          tags=["OTP Verification"])
async def resend_otp(
    request: OTPResendRequest,
    db: Session = Depends(get_db)
):
    """Resend OTP (with rate limiting)."""
    otp_service = OTPService(db)
    return otp_service.resend_otp(request)


# ==================== User Routes ====================

@app.get("/api/v1/users/me", response_model=UserResponse,
         tags=["Users"])
async def get_current_user_info(
    current_user: User = Depends(AuthService.get_current_user)
):
    """Get current authenticated user's information."""
    return current_user


@app.patch("/api/v1/users/me", response_model=UserResponse,
           tags=["Users"])
async def update_current_user(
    user_data: UserUpdate,
    current_user: User = Depends(AuthService.get_current_user),
    db: Session = Depends(get_db)
):
    """Update current user's profile."""
    update_data = user_data.model_dump(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(current_user, field, value)
    
    current_user.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(current_user)
    
    return current_user


@app.get("/api/v1/users/{user_id}", response_model=UserResponse,
         tags=["Users"])
async def get_user_by_id(
    user_id: int,
    current_user: User = Depends(AuthService.get_current_user),
    db: Session = Depends(get_db)
):
    """Get user by ID (admin or self only)."""
    if current_user.id != user_id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this user"
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return user


# ==================== Admin Routes ====================

@app.get("/api/v1/admin/users", response_model=list[UserResponse],
         tags=["Admin"])
async def list_users(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(AuthService.get_current_user),
    db: Session = Depends(get_db)
):
    """List all users (admin only)."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    users = db.query(User).offset(skip).limit(limit).all()
    return users


@app.patch("/api/v1/admin/users/{user_id}/activate", 
           response_model=UserResponse,
           tags=["Admin"])
async def activate_user(
    user_id: int,
    current_user: User = Depends(AuthService.get_current_user),
    db: Session = Depends(get_db)
):
    """Activate a user account (admin only)."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user.is_active = True
    user.failed_login_attempts = 0
    user.locked_until = None
    db.commit()
    db.refresh(user)
    
    return user


@app.patch("/api/v1/admin/users/{user_id}/deactivate", 
           response_model=UserResponse,
           tags=["Admin"])
async def deactivate_user(
    user_id: int,
    current_user: User = Depends(AuthService.get_current_user),
    db: Session = Depends(get_db)
):
    """Deactivate a user account (admin only)."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user.is_active = False
    db.commit()
    db.refresh(user)
    
    # Revoke all user sessions
    auth_service = AuthService(db)
    auth_service.logout_all(user.id)
    
    return user


# ==================== Run Server ====================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8001,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )
