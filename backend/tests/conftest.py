# Test configuration and fixtures
import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from database.database import Base, get_db
from main import app
from models.user import User
from service.auth_service import AuthService


# ==================== In-Memory Database ====================

# Create in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# ==================== Fixtures ====================

@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database session for each test."""
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        # Drop tables after test
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    """Create a test client with database dependency override."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


@pytest.fixture
def test_user(db_session):
    """Create a test user."""
    # Hash password
    hashed = AuthService.get_password_hash("testpass123")
    
    user = User(
        email="test@example.com",
        username="testuser",
        full_name="Test User",
        hashed_password=hashed,
        is_active=True,
        email_verified=True
    )
    
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    
    return user


@pytest.fixture
def inactive_user(db_session):
    """Create an inactive test user."""
    hashed = AuthService.get_password_hash("testpass123")
    
    user = User(
        email="inactive@example.com",
        username="inactiveuser",
        full_name="Inactive User",
        hashed_password=hashed,
        is_active=False,
        email_verified=True
    )
    
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    
    return user


@pytest.fixture
def auth_headers(client, test_user):
    """Get authentication headers for test user."""
    response = client.post(
        "/api/v1/auth/login",
        json={
            "username": "testuser",
            "password": "testpass123",
            "remember_me": True
        }
    )
    
    assert response.status_code == 200
    
    # Get cookies from response
    cookies = response.cookies
    
    headers = {
        "Cookie": f"access_token={cookies.get('access_token')}; session_id={cookies.get('session_id')}"
    }
    
    return headers


@pytest.fixture
def mock_redis():
    """Create a mock Redis client."""
    mock = MagicMock()
    
    # Default return values
    mock.ping.return_value = True
    mock.get_session.return_value = None
    mock.check_rate_limit.return_value = (True, 5)
    mock.validate_refresh_token.return_value = True
    mock.get.return_value = None
    
    return mock


@pytest.fixture
def mock_redis_client(mock_redis):
    """Patch the redis_client in the service modules."""
    with patch('service.auth_service.redis_client', mock_redis):
        with patch('service.otp_service.redis_client', mock_redis):
            yield mock_redis


# ==================== Mock Data ====================

MOCK_USER_DATA = {
    "email": "mock@example.com",
    "username": "mockuser",
    "full_name": "Mock User",
    "password": "MockPass123",
    "confirm_password": "MockPass123",
    "phone": "+1234567890"
}

MOCK_LOGIN_DATA = {
    "username": "testuser",
    "password": "testpass123",
    "remember_me": True
}

MOCK_OTP_DATA = {
    "email": "test@example.com",
    "otp_type": "email_verification",
    "purpose": "verify",
    "user_id": 1
}


# ==================== Test Helpers ====================

def assert_response_success(response, status_code=200):
    """Assert that response is successful."""
    assert response.status_code == status_code, f"Expected {status_code}, got {response.status_code}: {response.text}"


def assert_response_error(response, status_code, error_detail=None):
    """Assert that response is an error."""
    assert response.status_code == status_code
    if error_detail:
        assert error_detail in response.json()["detail"]


def extract_cookies(response):
    """Extract cookies from response as a dictionary."""
    return dict(response.cookies)
