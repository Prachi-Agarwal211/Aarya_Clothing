"""OTP (One-Time Password) model for verification."""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from database.database import Base


class OTP(Base):
    """OTP model for email and phone verification."""
    
    __tablename__ = "otps"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # OTP identifier
    otp_code = Column(String(10), nullable=False, index=True)
    
    # User reference (optional - for unauthenticated flows)
    user_id = Column(Integer, nullable=True, index=True)
    email = Column(String(255), nullable=True, index=True)
    phone = Column(String(20), nullable=True, index=True)
    
    # OTP details
    otp_type = Column(String(20), nullable=False)  # email_verification, phone_verification, password_reset, login
    purpose = Column(String(50), nullable=False)  # verify, reset, login
    
    # Status
    is_used = Column(Boolean, default=False)
    attempts = Column(Integer, default=0)
    max_attempts = Column(Integer, default=3)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
    used_at = Column(DateTime, nullable=True)
    
    # Metadata
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    
    def __repr__(self):
        return f"<OTP(id={self.id}, type={self.otp_type}, email={self.email})>"
    
    @property
    def is_expired(self) -> bool:
        """Check if OTP has expired."""
        return datetime.utcnow() > self.expires_at
    
    @property
    def is_valid(self) -> bool:
        """Check if OTP is valid for use."""
        return (
            not self.is_used and
            not self.is_expired and
            self.attempts < self.max_attempts
        )
    
    def increment_attempts(self):
        """Increment attempt counter."""
        self.attempts += 1
    
    def mark_used(self):
        """Mark OTP as used."""
        self.is_used = True
        self.used_at = datetime.utcnow()
    
    @property
    def remaining_attempts(self) -> int:
        """Get remaining attempts."""
        return max(0, self.max_attempts - self.attempts)
