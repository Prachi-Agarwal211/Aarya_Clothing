# Test cases for API endpoints
import pytest
from unittest.mock import patch, MagicMock
import json


class TestHealthEndpoint:
    """Tests for health check endpoint."""
    
    def test_health_check_success(self, client):
        """Test health check returns healthy status."""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "core-platform"
        assert "timestamp" in data
        assert "dependencies" in data


class TestRegistrationEndpoint:
    """Tests for user registration endpoint."""
    
    def test_register_success(self, client):
        """Test successful user registration."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "newuser@example.com",
                "username": "newuser",
                "full_name": "New User",
                "password": "SecurePass123",
                "confirm_password": "SecurePass123"
            }
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "newuser@example.com"
        assert data["username"] == "newuser"
        assert data["is_active"] is False  # Requires OTP verification
    
    def test_register_duplicate_email(self, client, test_user):
        """Test registration fails with duplicate email."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "test@example.com",  # Already exists
                "username": "newuser",
                "full_name": "New User",
                "password": "SecurePass123",
                "confirm_password": "SecurePass123"
            }
        )
        
        assert response.status_code == 400
        assert "Email already registered" in response.json()["detail"]
    
    def test_register_duplicate_username(self, client, test_user):
        """Test registration fails with duplicate username."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "newuser@example.com",
                "username": "testuser",  # Already exists
                "full_name": "New User",
                "password": "SecurePass123",
                "confirm_password": "SecurePass123"
            }
        )
        
        assert response.status_code == 400
        assert "Username already taken" in response.json()["detail"]
    
    def test_register_password_mismatch(self, client):
        """Test registration fails with password mismatch."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "newuser@example.com",
                "username": "newuser",
                "full_name": "New User",
                "password": "SecurePass123",
                "confirm_password": "DifferentPass456"
            }
        )
        
        assert response.status_code == 422  # Validation error
    
    def test_register_weak_password(self, client):
        """Test registration fails with weak password."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "newuser@example.com",
                "username": "newuser",
                "full_name": "New User",
                "password": "weak",
                "confirm_password": "weak"
            }
        )
        
        assert response.status_code == 422  # Validation error


class TestLoginEndpoint:
    """Tests for login endpoint with cookies."""
    
    def test_login_success(self, client, test_user):
        """Test successful login sets cookies."""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "username": "testuser",
                "password": "testpass123",
                "remember_me": True
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "user" in data
        assert "tokens" in data
        assert "session_id" in data
        
        # Check cookies are set
        assert "access_token" in response.cookies
        assert "refresh_token" in response.cookies
        assert "session_id" in response.cookies
    
    def test_login_wrong_password(self, client, test_user):
        """Test login fails with wrong password."""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "username": "testuser",
                "password": "wrongpassword"
            }
        )
        
        assert response.status_code == 401
        assert "Invalid credentials" in response.json()["detail"]
    
    def test_login_nonexistent_user(self, client):
        """Test login fails with non-existent user."""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "username": "nonexistent",
                "password": "password123"
            }
        )
        
        assert response.status_code == 401
    
    def test_login_unverified_email(self, client, db_session):
        """Test login fails if email not verified."""
        from models.user import User
        from service.auth_service import AuthService
        
        # Create unverified user
        hashed = AuthService.get_password_hash("testpass123")
        user = User(
            email="unverified@example.com",
            username="unverifieduser",
            full_name="Unverified User",
            hashed_password=hashed,
            is_active=True,
            email_verified=False
        )
        db_session.add(user)
        db_session.commit()
        
        response = client.post(
            "/api/v1/auth/login",
            json={
                "username": "unverifieduser",
                "password": "testpass123"
            }
        )
        
        assert response.status_code == 403
        assert "verify your email" in response.json()["detail"]
    
    def test_login_inactive_user(self, client, inactive_user):
        """Test login fails for inactive user."""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "username": "inactiveuser",
                "password": "testpass123"
            }
        )
        
        assert response.status_code == 401


class TestProtectedEndpoints:
    """Tests for protected endpoints requiring authentication."""
    
    def test_get_current_user_authenticated(self, client, auth_headers):
        """Test getting current user with valid auth."""
        response = client.get(
            "/api/v1/users/me",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "test@example.com"
        assert data["username"] == "testuser"
    
    def test_get_current_user_unauthenticated(self, client):
        """Test getting current user without auth fails."""
        response = client.get("/api/v1/users/me")
        
        assert response.status_code == 401
    
    def test_update_current_user(self, client, auth_headers):
        """Test updating current user profile."""
        response = client.patch(
            "/api/v1/users/me",
            headers=auth_headers,
            json={
                "full_name": "Updated Name",
                "phone": "+1234567890"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["full_name"] == "Updated Name"
        assert data["phone"] == "+1234567890"


class TestLogoutEndpoint:
    """Tests for logout endpoint."""
    
    def test_logout_clears_cookies(self, client, auth_headers):
        """Test logout clears authentication cookies."""
        response = client.post(
            "/api/v1/auth/logout",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        
        # Check cookies are cleared (empty or expired)
        assert response.cookies.get("access_token", "") == ""
        assert response.cookies.get("refresh_token", "") == ""
        assert response.cookies.get("session_id", "") == ""


class TestRateLimiting:
    """Tests for rate limiting on auth endpoints."""
    
    @patch('service.auth_service.redis_client')
    def test_login_rate_limited(self, mock_redis, client, test_user):
        """Test login is rate limited after too many attempts."""
        # Mock rate limit exceeded
        mock_redis.check_rate_limit.return_value = (False, 0)
        
        response = client.post(
            "/api/v1/auth/login",
            json={
                "username": "testuser",
                "password": "testpass123"
            }
        )
        
        assert response.status_code == 429
        assert "Too many login attempts" in response.json()["detail"]


class TestPasswordValidation:
    """Tests for password strength validation."""
    
    def test_password_weak_short(self, client):
        """Test registration fails with short password."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "test@example.com",
                "username": "testuser",
                "full_name": "Test User",
                "password": "abc",  # Too short
                "confirm_password": "abc"
            }
        )
        
        assert response.status_code == 422
    
    def test_password_no_uppercase(self, client):
        """Test registration fails without uppercase."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "test@example.com",
                "username": "testuser",
                "full_name": "Test User",
                "password": "lowercase123",  # No uppercase
                "confirm_password": "lowercase123"
            }
        )
        
        assert response.status_code == 422
    
    def test_password_no_number(self, client):
        """Test registration fails without number."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "test@example.com",
                "username": "testuser",
                "full_name": "Test User",
                "password": "NoNumbersHere",  # No number
                "confirm_password": "NoNumbersHere"
            }
        )
        
        assert response.status_code == 422
