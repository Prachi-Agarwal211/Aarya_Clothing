# Test cases for authentication endpoints
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime

from service.auth_service import AuthService


class TestPasswordHashing:
    """Tests for password hashing functions."""
    
    def test_password_hash_creates_hash(self):
        """Test that password hashing creates a bcrypt hash."""
        password = "TestPassword123"
        hashed = AuthService.get_password_hash(password)
        
        assert hashed != password
        assert hashed.startswith("$2b$")  # bcrypt prefix
        assert len(hashed) == 60  # bcrypt hash length
    
    def test_password_verify_success(self):
        """Test successful password verification."""
        password = "TestPassword123"
        hashed = AuthService.get_password_hash(password)
        
        assert AuthService.verify_password(password, hashed) is True
    
    def test_password_verify_failure(self):
        """Test failed password verification."""
        password = "TestPassword123"
        wrong_password = "WrongPassword456"
        hashed = AuthService.get_password_hash(password)
        
        assert AuthService.verify_password(wrong_password, hashed) is False
    
    def test_different_passwords_create_different_hashes(self):
        """Test that different passwords create different hashes."""
        password1 = "Password123"
        password2 = "Password456"
        
        hash1 = AuthService.get_password_hash(password1)
        hash2 = AuthService.get_password_hash(password2)
        
        assert hash1 != hash2
    
    def test_same_password_different_hashes(self):
        """Test that same password creates different hashes (salt)."""
        password = "TestPassword123"
        
        hash1 = AuthService.get_password_hash(password)
        hash2 = AuthService.get_password_hash(password)
        
        # bcrypt includes random salt, so hashes should differ
        assert hash1 != hash2
        
        # But both should verify successfully
        assert AuthService.verify_password(password, hash1) is True
        assert AuthService.verify_password(password, hash2) is True


class TestUserCreation:
    """Tests for user creation."""
    
    def test_create_user_success(self, db_session):
        """Test successful user creation."""
        auth_service = AuthService(db_session)
        
        from schemas.auth import UserCreate
        
        user_data = UserCreate(
            email="newuser@example.com",
            username="newuser",
            full_name="New User",
            password="SecurePass123",
            confirm_password="SecurePass123"
        )
        
        user = auth_service.create_user(user_data)
        
        assert user.id is not None
        assert user.email == "newuser@example.com"
        assert user.username == "newuser"
        assert user.full_name == "New User"
        assert user.hashed_password != "SecurePass123"
        assert user.is_active is False  # Requires OTP verification
        assert user.email_verified is False
    
    def test_create_user_duplicate_email(self, db_session, test_user):
        """Test user creation fails with duplicate email."""
        auth_service = AuthService(db_session)
        
        from schemas.auth import UserCreate
        from fastapi import HTTPException
        
        user_data = UserCreate(
            email="test@example.com",  # Duplicate email
            username="newuser",
            full_name="New User",
            password="SecurePass123",
            confirm_password="SecurePass123"
        )
        
        with pytest.raises(HTTPException) as exc_info:
            auth_service.create_user(user_data)
        
        assert exc_info.value.status_code == 400
        assert "Email already registered" in str(exc_info.value.detail)
    
    def test_create_user_duplicate_username(self, db_session, test_user):
        """Test user creation fails with duplicate username."""
        auth_service = AuthService(db_session)
        
        from schemas.auth import UserCreate
        from fastapi import HTTPException
        
        user_data = UserCreate(
            email="newuser@example.com",
            username="testuser",  # Duplicate username
            full_name="New User",
            password="SecurePass123",
            confirm_password="SecurePass123"
        )
        
        with pytest.raises(HTTPException) as exc_info:
            auth_service.create_user(user_data)
        
        assert exc_info.value.status_code == 400
        assert "Username already taken" in str(exc_info.value.detail)


class TestUserAuthentication:
    """Tests for user authentication."""
    
    def test_authenticate_user_success(self, db_session, test_user):
        """Test successful user authentication."""
        auth_service = AuthService(db_session)
        
        user = auth_service.authenticate_user("testuser", "testpass123")
        
        assert user is not None
        assert user.id == test_user.id
        assert user.email == test_user.email
    
    def test_authenticate_user_wrong_password(self, db_session, test_user):
        """Test authentication with wrong password."""
        auth_service = AuthService(db_session)
        
        user = auth_service.authenticate_user("testuser", "wrongpassword")
        
        assert user is None
    
    def test_authenticate_user_nonexistent(self, db_session):
        """Test authentication with non-existent user."""
        auth_service = AuthService(db_session)
        
        user = auth_service.authenticate_user("nonexistent", "password")
        
        assert user is None
    
    def test_authenticate_user_inactive(self, db_session, inactive_user):
        """Test authentication with inactive user."""
        auth_service = AuthService(db_session)
        
        user = auth_service.authenticate_user("inactiveuser", "testpass123")
        
        assert user is None


class TestTokenGeneration:
    """Tests for JWT token generation."""
    
    def test_create_access_token(self, db_session, test_user):
        """Test access token creation."""
        auth_service = AuthService(db_session)
        
        token = auth_service._create_access_token(
            data={"sub": test_user.email},
            expires_delta=None
        )
        
        assert token is not None
        assert len(token) > 0
        # JWT format: header.payload.signature
        parts = token.split(".")
        assert len(parts) == 3
    
    def test_create_refresh_token(self, db_session, test_user):
        """Test refresh token creation."""
        auth_service = AuthService(db_session)
        
        token = auth_service._create_refresh_token(
            user_id=test_user.id,
            expires_delta=None
        )
        
        assert token is not None
        assert len(token) > 0
        parts = token.split(".")
        assert len(parts) == 3


class TestUserModel:
    """Tests for User model."""
    
    def test_user_locked_property_false(self, db_session, test_user):
        """Test is_locked property when not locked."""
        assert test_user.is_locked is False
    
    def test_user_locked_property_true(self, db_session, test_user):
        """Test is_locked property when locked."""
        from datetime import datetime, timedelta
        
        test_user.locked_until = datetime.utcnow() + timedelta(minutes=30)
        db_session.commit()
        
        assert test_user.is_locked is True
    
    def test_increment_failed_attempts(self, db_session, test_user):
        """Test incrementing failed login attempts."""
        initial = test_user.failed_login_attempts
        
        test_user.increment_failed_attempts()
        
        assert test_user.failed_login_attempts == initial + 1
    
    def test_reset_failed_attempts(self, db_session, test_user):
        """Test resetting failed login attempts."""
        test_user.failed_login_attempts = 5
        db_session.commit()
        
        test_user.reset_failed_attempts()
        
        assert test_user.failed_login_attempts == 0
        assert test_user.locked_until is None
        assert test_user.last_login is not None
