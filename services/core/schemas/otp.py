"""Schemas for OTP verification."""
from pydantic import BaseModel, Field
from typing import Optional


# ==================== OTP Request Schemas ====================

class OTPSendRequest(BaseModel):
    """Schema for requesting OTP."""
    email: Optional[str] = None
    phone: Optional[str] = None
    otp_type: str = Field(..., description="email_verification, phone_verification, password_reset, login")
    purpose: str = Field(..., description="verify, reset, login")


class OTPVerifyRequest(BaseModel):
    """Schema for verifying OTP."""
    email: Optional[str] = None
    phone: Optional[str] = None
    otp_code: str = Field(..., min_length=4, max_length=10)
    otp_type: str
    purpose: str


class OTPResendRequest(BaseModel):
    """Schema for resending OTP."""
    email: Optional[str] = None
    phone: Optional[str] = None
    otp_type: str
    purpose: str


# ==================== OTP Response Schemas ====================

class OTPSendResponse(BaseModel):
    """Schema for OTP send response."""
    success: bool
    message: str
    expires_in: int  # seconds
    email: Optional[str] = None
    phone: Optional[str] = None


class OTPVerifyResponse(BaseModel):
    """Schema for OTP verify response."""
    success: bool
    message: str
    verified: bool
