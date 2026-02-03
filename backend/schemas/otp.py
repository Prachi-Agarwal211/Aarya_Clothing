"""OTP schemas for API request/response models."""
from pydantic import BaseModel, Field, EmailStr
from typing import Optional
from datetime import datetime


# ==================== OTP Request Schemas ====================

class OTPSendRequest(BaseModel):
    """Request to send OTP."""
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    otp_type: str = Field(..., description="email_verification, phone_verification, password_reset, login")
    purpose: str = Field(..., description="verify, reset, login")
    user_id: Optional[int] = None
    
    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "email": "user@example.com",
                    "otp_type": "email_verification",
                    "purpose": "verify",
                    "user_id": 1
                },
                {
                    "phone": "+1234567890",
                    "otp_type": "phone_verification",
                    "purpose": "verify",
                    "user_id": 1
                }
            ]
        }


class OTPVerifyRequest(BaseModel):
    """Request to verify OTP."""
    otp_code: str = Field(..., min_length=4, max_length=10)
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    otp_type: str
    purpose: str
    user_id: Optional[int] = None


class OTPResendRequest(BaseModel):
    """Request to resend OTP."""
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    otp_type: str
    purpose: str


# ==================== OTP Response Schemas ====================

class OTPSendResponse(BaseModel):
    """Response after sending OTP."""
    message: str
    otp_type: str
    destination: Optional[str] = None  # Masked email/phone
    expires_in: int  # seconds
    remaining_attempts: int
    next_resend_available: int  # seconds


class OTPVerifyResponse(BaseModel):
    """Response after verifying OTP."""
    valid: bool
    message: str
    user_id: Optional[int] = None
    is_verified: Optional[bool] = None


class OTPStatusResponse(BaseModel):
    """OTP status response."""
    otp_type: str
    email: Optional[str] = None
    phone: Optional[str] = None
    is_sent: bool
    is_verified: bool
    expires_at: datetime
    remaining_attempts: int


# ==================== OTP Configuration ====================

class OTPConfig(BaseModel):
    """OTP configuration settings."""
    code_length: int = 6
    expiry_minutes: int = 10
    max_attempts: int = 3
    resend_cooldown_minutes: int = 1
    max_resend_per_hour: int = 5


# ==================== WhatsApp/Email Templates ====================

class OTPEmailTemplate(BaseModel):
    """Email template for OTP."""
    subject: str = "Your Aarya Clothing Verification Code"
    html_template: str
    text_template: str
    
    @classmethod
    def get_verification_template(cls, otp_code: str, expires_minutes: int = 10) -> tuple[str, str]:
        """Get verification email template."""
        subject = "Verify Your Email - Aarya Clothing"
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: #1a1a2e; color: white; padding: 20px; text-align: center; }}
                .otp-box {{ background: #f4f4f4; padding: 30px; text-align: center; margin: 20px 0; }}
                .otp-code {{ font-size: 32px; letter-spacing: 8px; font-weight: bold; color: #1a1a2e; }}
                .footer {{ font-size: 12px; color: #666; text-align: center; margin-top: 20px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Aarya Clothing</h1>
                </div>
                <p>Thank you for registering! Please use the verification code below:</p>
                <div class="otp-box">
                    <div class="otp-code">{otp_code}</div>
                </div>
                <p>This code expires in {expires_minutes} minutes.</p>
                <p>If you didn't request this, please ignore this email.</p>
                <div class="footer">
                    <p>&copy; 2024 Aarya Clothing. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """
        text = f"""
        Aarya Clothing - Email Verification
        
        Your verification code: {otp_code}
        
        This code expires in {expires_minutes} minutes.
        
        If you didn't request this, please ignore this email.
        """
        return subject, html, text
    
    @classmethod
    def get_password_reset_template(cls, otp_code: str, expires_minutes: int = 10) -> tuple[str, str]:
        """Get password reset email template."""
        subject = "Password Reset - Aarya Clothing"
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: #1a1a2e; color: white; padding: 20px; text-align: center; }}
                .otp-box {{ background: #f4f4f4; padding: 30px; text-align: center; margin: 20px 0; }}
                .otp-code {{ font-size: 32px; letter-spacing: 8px; font-weight: bold; color: #1a1a2e; }}
                .footer {{ font-size: 12px; color: #666; text-align: center; margin-top: 20px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Aarya Clothing</h1>
                </div>
                <p>You requested a password reset. Use the code below:</p>
                <div class="otp-box">
                    <div class="otp-code">{otp_code}</div>
                </div>
                <p>This code expires in {expires_minutes} minutes.</p>
                <p class="footer">&copy; 2024 Aarya Clothing</p>
            </div>
        </body>
        </html>
        """
        text = f"""
        Aarya Clothing - Password Reset
        
        Your reset code: {otp_code}
        
        This code expires in {expires_minutes} minutes.
        """
        return subject, html, text


class OTPWhatsAppTemplate(BaseModel):
    """WhatsApp message template for OTP."""
    
    @classmethod
    def get_verification_message(cls, otp_code: str, expires_minutes: int = 10) -> str:
        """Get WhatsApp verification message."""
        return (
            f"Aarya Clothing: Your verification code is *{otp_code}*. "
            f"This code expires in {expires_minutes} minutes. "
            f"Don't share this with anyone."
        )
    
    @classmethod
    def get_password_reset_message(cls, otp_code: str, expires_minutes: int = 10) -> str:
        """Get WhatsApp password reset message."""
        return (
            f"Aarya Clothing: Your password reset code is *{otp_code}*. "
            f"This code expires in {expires_minutes} minutes. "
            f"If you didn't request this, ignore this message."
        )


# ==================== OTP Error Responses ====================

class OTPErrorResponse(BaseModel):
    """OTP error response."""
    detail: str
    error_code: str
    next_retry: Optional[int] = None  # seconds until retry


# ==================== OTP Delivery Preference ====================

class OTPDeliveryPreference(BaseModel):
    """User's OTP delivery preference."""
    user_id: int
    email_enabled: bool = True
    phone_enabled: bool = False
    preferred_method: str = "email"  # email, phone, both
    verified_email: bool = False
    verified_phone: bool = False
    
    class Config:
        from_attributes = True
