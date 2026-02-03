# Test cases for OTP endpoints
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta


class TestOTPModel:
    """Tests for OTP model."""
    
    def test_otp_model_creation(self, db_session):
        """Test OTP model creation."""
        from models.otp import OTP
        
        otp = OTP(
            otp_code="123456",
            user_id=1,
            email="test@example.com",
            otp_type="email_verification",
            purpose="verify",
            expires_at=datetime.utcnow() + timedelta(minutes=10)
        )
        
        db_session.add(otp)
        db_session.commit()
        db_session.refresh(otp)
        
        assert otp.id is not None
        assert otp.otp_code == "123456"
        assert otp.is_used is False
        assert otp.is_expired is False
    
    def test_otp_is_valid(self, db_session):
        """Test OTP validity check."""
        from models.otp import OTP
        
        otp = OTP(
            otp_code="123456",
            user_id=1,
            email="test@example.com",
            otp_type="email_verification",
            purpose="verify",
            expires_at=datetime.utcnow() + timedelta(minutes=10),
            is_used=False,
            attempts=0,
            max_attempts=3
        )
        
        assert otp.is_valid is True
    
    def test_otp_is_expired(self, db_session):
        """Test OTP expiration."""
        from models.otp import OTP
        
        otp = OTP(
            otp_code="123456",
            user_id=1,
            email="test@example.com",
            otp_type="email_verification",
            purpose="verify",
            expires_at=datetime.utcnow() - timedelta(minutes=1),  # Expired
            is_used=False
        )
        
        assert otp.is_expired is True
        assert otp.is_valid is False
    
    def test_otp_mark_used(self, db_session):
        """Test marking OTP as used."""
        from models.otp import OTP
        
        otp = OTP(
            otp_code="123456",
            user_id=1,
            email="test@example.com",
            otp_type="email_verification",
            purpose="verify",
            expires_at=datetime.utcnow() + timedelta(minutes=10),
            is_used=False
        )
        
        otp.mark_used()
        
        assert otp.is_used is True
        assert otp.used_at is not None
    
    def test_otp_increment_attempts(self, db_session):
        """Test incrementing OTP attempts."""
        from models.otp import OTP
        
        otp = OTP(
            otp_code="123456",
            user_id=1,
            email="test@example.com",
            otp_type="email_verification",
            purpose="verify",
            expires_at=datetime.utcnow() + timedelta(minutes=10),
            attempts=0,
            max_attempts=3
        )
        
        otp.increment_attempts()
        otp.increment_attempts()
        
        assert otp.attempts == 2
        assert otp.remaining_attempts == 1


class TestOTPSchemas:
    """Tests for OTP Pydantic schemas."""
    
    def test_otp_send_request_email(self):
        """Test OTP send request with email."""
        from schemas.otp import OTPSendRequest
        
        request = OTPSendRequest(
            email="test@example.com",
            otp_type="email_verification",
            purpose="verify",
            user_id=1
        )
        
        assert request.email == "test@example.com"
        assert request.otp_type == "email_verification"
        assert request.purpose == "verify"
    
    def test_otp_send_request_phone(self):
        """Test OTP send request with phone."""
        from schemas.otp import OTPSendRequest
        
        request = OTPSendRequest(
            phone="+1234567890",
            otp_type="phone_verification",
            purpose="verify"
        )
        
        assert request.phone == "+1234567890"
        assert request.otp_type == "phone_verification"
    
    def test_otp_verify_request(self):
        """Test OTP verify request."""
        from schemas.otp import OTPVerifyRequest
        
        request = OTPVerifyRequest(
            otp_code="123456",
            email="test@example.com",
            otp_type="email_verification",
            purpose="verify"
        )
        
        assert request.otp_code == "123456"
        assert request.email == "test@example.com"
    
    def test_otp_send_response(self):
        """Test OTP send response."""
        from schemas.otp import OTPSendResponse
        
        response = OTPSendResponse(
            message="OTP sent successfully",
            otp_type="email_verification",
            destination="t***@example.com",
            expires_in=600,
            remaining_attempts=3,
            next_resend_available=60
        )
        
        assert response.message == "OTP sent successfully"
        assert response.expires_in == 600


class TestOTPService:
    """Tests for OTP service."""
    
    @patch('service.otp_service.redis_client')
    def test_generate_otp_code(self, mock_redis, db_session):
        """Test OTP code generation."""
        from service.otp_service import OTPService
        
        service = OTPService(db_session)
        otp_code = service.generate_otp_code()
        
        assert len(otp_code) == 6
        assert otp_code.isdigit()
    
    @patch('service.otp_service.redis_client')
    def test_send_otp_requires_destination(self, mock_redis, db_session):
        """Test OTP send requires email or phone."""
        from service.otp_service import OTPService
        from schemas.otp import OTPSendRequest
        from fastapi import HTTPException
        
        service = OTPService(db_session)
        
        request = OTPSendRequest(
            otp_type="email_verification",
            purpose="verify"
        )
        
        with pytest.raises(HTTPException) as exc_info:
            service.send_otp(request)
        
        assert exc_info.value.status_code == 400
        assert "email or phone must be provided" in str(exc_info.value.detail)
    
    @patch('service.otp_service.redis_client')
    def test_send_otp_rate_limited(self, mock_redis, db_session):
        """Test OTP send respects rate limiting."""
        from service.otp_service import OTPService
        from schemas.otp import OTPSendRequest
        from fastapi import HTTPException
        
        # Mock rate limit exceeded
        mock_redis.check_rate_limit.return_value = (False, 0)
        
        service = OTPService(db_session)
        
        request = OTPSendRequest(
            email="test@example.com",
            otp_type="email_verification",
            purpose="verify"
        )
        
        with pytest.raises(HTTPException) as exc_info:
            service.send_otp(request)
        
        assert exc_info.value.status_code == 429
    
    @patch('service.otp_service.redis_client')
    def test_otp_verification_success(self, mock_redis, db_session):
        """Test successful OTP verification."""
        from service.otp_service import OTPService
        from schemas.otp import OTPVerifyRequest
        from models.otp import OTP
        from datetime import timedelta
        
        # Create OTP in database
        otp = OTP(
            otp_code="123456",
            user_id=1,
            email="test@example.com",
            otp_type="email_verification",
            purpose="verify",
            expires_at=datetime.utcnow() + timedelta(minutes=10)
        )
        db_session.add(otp)
        db_session.commit()
        
        service = OTPService(db_session)
        
        request = OTPVerifyRequest(
            otp_code="123456",
            email="test@example.com",
            otp_type="email_verification",
            purpose="verify"
        )
        
        result = service.verify_otp(request)
        
        assert result["valid"] is True
        assert result["message"] == "OTP verified successfully"
    
    @patch('service.otp_service.redis_client')
    def test_otp_verification_wrong_code(self, mock_redis, db_session):
        """Test OTP verification with wrong code."""
        from service.otp_service import OTPService
        from schemas.otp import OTPVerifyRequest
        from models.otp import OTP
        from datetime import timedelta
        from fastapi import HTTPException
        
        # Create OTP in database
        otp = OTP(
            otp_code="123456",
            user_id=1,
            email="test@example.com",
            otp_type="email_verification",
            purpose="verify",
            expires_at=datetime.utcnow() + timedelta(minutes=10)
        )
        db_session.add(otp)
        db_session.commit()
        
        service = OTPService(db_session)
        
        request = OTPVerifyRequest(
            otp_code="wrongcode",
            email="test@example.com",
            otp_type="email_verification",
            purpose="verify"
        )
        
        with pytest.raises(HTTPException) as exc_info:
            service.verify_otp(request)
        
        assert exc_info.value.status_code == 400
        assert "Incorrect OTP" in str(exc_info.value.detail)


class TestOTPTemplates:
    """Tests for OTP email/WhatsApp templates."""
    
    def test_email_verification_template(self):
        """Test email verification template generation."""
        from schemas.otp import OTPEmailTemplate
        
        subject, html, text = OTPEmailTemplate.get_verification_template(
            otp_code="123456",
            expires_minutes=10
        )
        
        assert "Aarya Clothing" in subject or "Verification" in subject
        assert "123456" in html
        assert "123456" in text
        assert "10" in html or "10" in text
    
    def test_password_reset_template(self):
        """Test password reset template generation."""
        from schemas.otp import OTPEmailTemplate
        
        subject, html, text = OTPEmailTemplate.get_password_reset_template(
            otp_code="123456",
            expires_minutes=10
        )
        
        assert "Password" in subject or "Reset" in subject
        assert "123456" in html
        assert "123456" in text
    
    def test_whatsapp_verification_message(self):
        """Test WhatsApp verification message."""
        from schemas.otp import OTPWhatsAppTemplate
        
        message = OTPWhatsAppTemplate.get_verification_message(
            otp_code="123456",
            expires_minutes=10
        )
        
        assert "123456" in message
        assert "Aarya Clothing" in message
    
    def test_whatsapp_password_reset_message(self):
        """Test WhatsApp password reset message."""
        from schemas.otp import OTPWhatsAppTemplate
        
        message = OTPWhatsAppTemplate.get_password_reset_message(
            otp_code="123456",
            expires_minutes=10
        )
        
        assert "123456" in message
        assert "reset" in message.lower()


class TestOTPEndpoints:
    """Tests for OTP API endpoints."""
    
    @patch('service.otp_service.redis_client')
    def test_send_otp_endpoint(self, mock_redis, client, test_user):
        """Test OTP send endpoint."""
        mock_redis.check_rate_limit.return_value = (True, 5)
        
        response = client.post(
            "/api/v1/auth/send-otp",
            json={
                "email": "test@example.com",
                "otp_type": "email_verification",
                "purpose": "verify",
                "user_id": test_user.id
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "destination" in data
        assert "expires_in" in data
    
    @patch('service.otp_service.redis_client')
    def test_send_otp_no_destination(self, mock_redis, client):
        """Test OTP send fails without destination."""
        response = client.post(
            "/api/v1/auth/send-otp",
            json={
                "otp_type": "email_verification",
                "purpose": "verify"
            }
        )
        
        assert response.status_code == 400
    
    def test_verify_otp_endpoint(self, client, db_session):
        """Test OTP verify endpoint."""
        from models.otp import OTP
        from datetime import timedelta
        
        # Create OTP
        otp = OTP(
            otp_code="123456",
            user_id=1,
            email="test@example.com",
            otp_type="email_verification",
            purpose="verify",
            expires_at=datetime.utcnow() + timedelta(minutes=10)
        )
        db_session.add(otp)
        db_session.commit()
        
        response = client.post(
            "/api/v1/auth/verify-otp",
            json={
                "otp_code": "123456",
                "email": "test@example.com",
                "otp_type": "email_verification",
                "purpose": "verify"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is True
    
    def test_verify_otp_wrong_code(self, client, db_session):
        """Test OTP verify fails with wrong code."""
        from models.otp import OTP
        from datetime import timedelta
        
        # Create OTP
        otp = OTP(
            otp_code="123456",
            user_id=1,
            email="test@example.com",
            otp_type="email_verification",
            purpose="verify",
            expires_at=datetime.utcnow() + timedelta(minutes=10)
        )
        db_session.add(otp)
        db_session.commit()
        
        response = client.post(
            "/api/v1/auth/verify-otp",
            json={
                "otp_code": "wrongcode",
                "email": "test@example.com",
                "otp_type": "email_verification",
                "purpose": "verify"
            }
        )
        
        assert response.status_code == 400
        assert "Incorrect OTP" in response.json()["detail"]
