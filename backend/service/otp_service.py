"""OTP Service - Handle OTP generation, sending, and verification."""
import secrets
import random
from datetime import datetime, timedelta
from typing import Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import httpx

from models.otp import OTP
from models.user import User
from schemas.otp import (
    OTPSendRequest, OTPVerifyRequest,
    OTPEmailTemplate, OTPWhatsAppTemplate
)
from core.config import settings
from core.redis_client import redis_client


class OTPService:
    """OTP service for verification codes."""
    
    # OTP Configuration
    CODE_LENGTH = 6
    EXPIRY_MINUTES = 10
    MAX_ATTEMPTS = 3
    RESEND_COOLDOWN_MINUTES = 1
    MAX_RESEND_PER_HOUR = 5
    
    def __init__(self, db: Session):
        self.db = db
    
    # ==================== OTP Generation ====================
    
    def generate_otp_code(self) -> str:
        """Generate a random OTP code."""
        if self.CODE_LENGTH == 6:
            return ''.join(str(random.randint(0, 9)) for _ in range(6))
        else:
            return ''.join(secrets.choice('ABCDEFGHJKLMNPQRSTUVWXYZ23456789') for _ in range(self.CODE_LENGTH))
    
    # ==================== OTP Sending ====================
    
    def send_otp(self, request: OTPSendRequest) -> dict:
        """
        Send OTP via email or WhatsApp based on user preference.
        Returns dict with status and masked destination.
        """
        # Validate at least one destination is provided
        if not request.email and not request.phone:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Either email or phone must be provided"
            )
        
        # Check rate limiting for OTP sending
        rate_key = f"otp_send:{request.otp_type}:{request.email or request.phone}"
        allowed, remaining = redis_client.check_rate_limit(
            rate_key,
            self.MAX_RESEND_PER_HOUR,
            3600  # 1 hour window
        )
        
        if not allowed:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many OTP requests. Please try again later."
            )
        
        # Generate OTP
        otp_code = self.generate_otp_code()
        expires_at = datetime.utcnow() + timedelta(minutes=self.EXPIRY_MINUTES)
        
        # Create OTP record
        otp = OTP(
            otp_code=otp_code,
            user_id=request.user_id,
            email=request.email,
            phone=request.phone,
            otp_type=request.otp_type,
            purpose=request.purpose,
            expires_at=expires_at,
            max_attempts=self.MAX_ATTEMPTS
        )
        
        self.db.add(otp)
        self.db.commit()
        self.db.refresh(otp)
        
        # Send OTP via selected method
        if request.email:
            self._send_email_otp(request.email, otp_code, request.otp_type)
            masked_destination = self._mask_email(request.email)
        elif request.phone:
            self._send_whatsapp_otp(request.phone, otp_code, request.otp_type)
            masked_destination = self._mask_phone(request.phone)
        
        return {
            "message": "OTP sent successfully",
            "otp_type": request.otp_type,
            "destination": masked_destination,
            "expires_in": self.EXPIRY_MINUTES * 60,
            "remaining_attempts": self.MAX_ATTEMPTS,
            "next_resend_available": self.RESEND_COOLDOWN_MINUTES * 60
        }
    
    def _send_email_otp(self, email: str, otp_code: str, otp_type: str):
        """Send OTP via email."""
        try:
            # Get email template
            if otp_type in ["email_verification", "verify"]:
                subject, html_body, text_body = OTPEmailTemplate.get_verification_template(
                    otp_code, self.EXPIRY_MINUTES
                )
            else:
                subject, html_body, text_body = OTPEmailTemplate.get_password_reset_template(
                    otp_code, self.EXPIRY_MINUTES
                )
            
            # For development, just log (configure SMTP in production)
            if settings.DEBUG or not settings.SMTP_HOST:
                print(f"[DEV] OTP Email to {email}: {otp_code}")
                return
            
            # Send real email
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"Aarya Clothing <{settings.SMTP_USER}>"
            msg['To'] = email
            
            # Attach both text and HTML versions
            part1 = MIMEText(text_body, 'plain')
            part2 = MIMEText(html_body, 'html')
            msg.attach(part1)
            msg.attach(part2)
            
            # Connect and send
            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
                server.starttls()
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                server.sendmail(settings.SMTP_USER, email, msg.as_string())
            
        except Exception as e:
            print(f"Failed to send email OTP: {e}")
            # In production, raise exception
            if not settings.DEBUG:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to send OTP email"
                )
    
    def _send_whatsapp_otp(self, phone: str, otp_code: str, otp_type: str):
        """Send OTP via WhatsApp."""
        try:
            # Get WhatsApp message
            if otp_type in ["phone_verification", "verify"]:
                message = OTPWhatsAppTemplate.get_verification_message(
                    otp_code, self.EXPIRY_MINUTES
                )
            else:
                message = OTPWhatsAppTemplate.get_password_reset_message(
                    otp_code, self.EXPIRY_MINUTES
                )
            
            # For development, just log
            if settings.DEBUG:
                print(f"[DEV] OTP WhatsApp to {phone}: {otp_code}")
                return
            
            # In production, integrate with WhatsApp Business API
            # Example: Twilio WhatsApp or Meta Cloud API
            # This is a placeholder for WhatsApp integration
            self._send_via_whatsapp_api(phone, message)
            
        except Exception as e:
            print(f"Failed to send WhatsApp OTP: {e}")
            if not settings.DEBUG:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to send OTP via WhatsApp"
                )
    
    def _send_via_whatsapp_api(self, phone: str, message: str):
        """Send WhatsApp message via API (Twilio/Meta)."""
        # Placeholder for WhatsApp API integration
        # Example using Twilio:
        # from twilio.rest import Client
        # client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        # message = client.messages.create(
        #     from_='whatsapp:+14155238886',
        #     body=message,
        #     to=f'whatsapp:{phone}'
        # )
        pass
    
    # ==================== OTP Verification ====================
    
    def verify_otp(self, request: OTPVerifyRequest) -> dict:
        """Verify an OTP code."""
        # Build query
        query = self.db.query(OTP).filter(
            OTP.is_used == False,
            OTP.otp_type == request.otp_type,
            OTP.purpose == request.purpose
        )
        
        if request.email:
            query = query.filter(OTP.email == request.email)
        elif request.phone:
            query = query.filter(OTP.phone == request.phone)
        
        if request.user_id:
            query = query.filter(OTP.user_id == request.user_id)
        
        # Get latest OTP
        otp = query.order_by(OTP.created_at.desc()).first()
        
        if not otp:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="OTP not found or already used"
            )
        
        # Check expiry
        if otp.is_expired:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="OTP has expired"
            )
        
        # Check attempts
        if otp.attempts >= otp.max_attempts:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Too many incorrect attempts. Please request a new OTP."
            )
        
        # Verify code
        if otp.otp_code != request.otp_code:
            otp.increment_attempts()
            self.db.commit()
            
            remaining = otp.remaining_attempts
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Incorrect OTP. {remaining} attempts remaining."
            )
        
        # Mark OTP as used
        otp.mark_used()
        self.db.commit()
        
        # Update user if email/phone verification
        if request.user_id:
            user = self.db.query(User).filter(User.id == request.user_id).first()
            if user:
                if request.otp_type == "email_verification":
                    user.email_verified = True
                elif request.otp_type == "phone_verification":
                    user.phone_verified = True  # Add field to user model
                self.db.commit()
        
        return {
            "valid": True,
            "message": "OTP verified successfully",
            "user_id": request.user_id,
            "is_verified": True
        }
    
    # ==================== OTP Resend ====================
    
    def resend_otp(self, request: OTPResendRequest) -> dict:
        """Resend OTP."""
        # Check resend cooldown
        rate_key = f"otp_resend:{request.otp_type}:{request.email or request.phone}"
        allowed, remaining = redis_client.check_rate_limit(
            rate_key,
            1,
            self.RESEND_COOLDOWN_MINUTES * 60
        )
        
        if not allowed:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Wait {self.RESEND_COOLDOWN_MINUTES} minutes before resending"
            )
        
        # Create new OTP request and send
        send_request = OTPSendRequest(
            email=request.email,
            phone=request.phone,
            otp_type=request.otp_type,
            purpose=request.purpose
        )
        
        return self.send_otp(send_request)
    
    # ==================== OTP Utility Methods ====================
    
    def _mask_email(self, email: str) -> str:
        """Mask email for display."""
        if not email:
            return None
        parts = email.split('@')
        if len(parts) != 2:
            return email
        username, domain = parts
        if len(username) <= 2:
            masked_username = username
        else:
            masked_username = username[0] + '*' * (len(username) - 2) + username[-1]
        return f"{masked_username}@{domain}"
    
    def _mask_phone(self, phone: str) -> str:
        """Mask phone for display."""
        if not phone:
            return None
        if len(phone) <= 4:
            return '*' * len(phone)
        return '*' * (len(phone) - 4) + phone[-4:]
    
    def cleanup_expired_otps(self):
        """Delete expired OTPs (run periodically)."""
        expired_otps = self.db.query(OTP).filter(
            OTP.expires_at < datetime.utcnow()
        ).delete()
        self.db.commit()
        return expired_otps
    
    def validate_otp_format(self, otp_code: str) -> bool:
        """Validate OTP format."""
        if len(otp_code) != self.CODE_LENGTH:
            return False
        return otp_code.isalnum()
