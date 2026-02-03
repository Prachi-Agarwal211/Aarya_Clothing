"""Authentication schemas for API request/response models."""
from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional
from datetime import datetime
import re


# ==================== User Schemas ====================

class UserBase(BaseModel):
    """Base user schema with common fields."""
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    full_name: str = Field(..., min_length=2, max_length=100)
    phone: Optional[str] = None
    address: Optional[str] = None


class UserCreate(UserBase):
    """Schema for user registration."""
    password: str = Field(..., min_length=8, max_length=128)
    confirm_password: str
    
    @field_validator('confirm_password')
    @classmethod
    def passwords_match(cls, v, info):
        if 'password' in info.data and v != info.data['password']:
            raise ValueError('Passwords do not match')
        return v
    
    @field_validator('password')
    @classmethod
    def validate_password_strength(cls, v):
        """Validate password meets security requirements."""
        from core.config import settings
        
        errors = []
        if settings.PASSWORD_REQUIRE_UPPERCASE and not re.search(r'[A-Z]', v):
            errors.append("Password must contain at least one uppercase letter")
        if settings.PASSWORD_REQUIRE_LOWERCASE and not re.search(r'[a-z]', v):
            errors.append("Password must contain at least one lowercase letter")
        if settings.PASSWORD_REQUIRE_NUMBER and not re.search(r'[0-9]', v):
            errors.append("Password must contain at least one number")
        if settings.PASSWORD_REQUIRE_SPECIAL and not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            errors.append("Password must contain at least one special character")
        
        if errors:
            raise ValueError(' '.join(errors))
        return v


class UserResponse(UserBase):
    """Schema for user data in responses."""
    id: int
    is_active: bool
    is_admin: bool
    email_verified: bool
    created_at: datetime
    last_login: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    """Schema for updating user profile."""
    full_name: Optional[str] = Field(None, min_length=2, max_length=100)
    phone: Optional[str] = None
    address: Optional[str] = None


# ==================== Authentication Schemas ====================

class Token(BaseModel):
    """JWT token response."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenPayload(BaseModel):
    """JWT token payload."""
    sub: str  # User email
    exp: Optional[datetime] = None
    type: str = "access"


class TokenRefresh(BaseModel):
    """Request to refresh access token."""
    refresh_token: str


class LoginRequest(BaseModel):
    """Login request with username/email and password."""
    username: str
    password: str
    remember_me: bool = False


class LoginResponse(BaseModel):
    """Login response with user data and tokens."""
    user: UserResponse
    tokens: Token
    session_id: str


# ==================== Security Schemas ====================

class PasswordResetRequest(BaseModel):
    """Request password reset email."""
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    """Confirm password reset with new password."""
    token: str
    password: str = Field(..., min_length=8, max_length=128)
    confirm_password: str
    
    @field_validator('confirm_password')
    @classmethod
    def passwords_match(cls, v, info):
        if 'password' in info.data and v != info.data['password']:
            raise ValueError('Passwords do not match')
        return v


class ChangePasswordRequest(BaseModel):
    """Change password for authenticated user."""
    current_password: str
    new_password: str = Field(..., min_length=8, max_length=128)
    confirm_new_password: str
    
    @field_validator('confirm_new_password')
    @classmethod
    def passwords_match(cls, v, info):
        if 'new_password' in info.data and v != info.data['new_password']:
            raise ValueError('Passwords do not match')
        return v


# ==================== Error Schemas ====================

class ErrorResponse(BaseModel):
    """Standard error response."""
    detail: str
    error_code: Optional[str] = None


class ValidationErrorResponse(BaseModel):
    """Validation error response."""
    detail: list
    error_code: str = "VALIDATION_ERROR"


class AuthErrorResponse(BaseModel):
    """Authentication error response."""
    detail: str
    error_code: str
    locked_until: Optional[datetime] = None
