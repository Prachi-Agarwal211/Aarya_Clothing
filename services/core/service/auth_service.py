"""Authentication service for Core Platform."""
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from passlib.context import CryptContext
from jose import jwt, JWTError
from sqlalchemy.orm import Session
from sqlalchemy import or_

from core.config import settings
from core.redis_client import redis_client
from models.user import User


# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    """Authentication service for user management."""
    
    def __init__(self, db: Session):
        """Initialize authentication service."""
        self.db = db
    
    # ==================== Password Operations ====================
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash."""
        return pwd_context.verify(plain_password, hashed_password)
    
    @staticmethod
    def get_password_hash(password: str) -> str:
        """Hash a password."""
        return pwd_context.hash(password)
    
    @staticmethod
    def validate_password(password: str) -> tuple[bool, list[str]]:
        """Validate password against policy."""
        errors = []
        
        if len(password) < settings.PASSWORD_MIN_LENGTH:
            errors.append(f"Password must be at least {settings.PASSWORD_MIN_LENGTH} characters")
        
        if settings.PASSWORD_REQUIRE_UPPERCASE and not any(c.isupper() for c in password):
            errors.append("Password must contain at least one uppercase letter")
        
        if settings.PASSWORD_REQUIRE_LOWERCASE and not any(c.islower() for c in password):
            errors.append("Password must contain at least one lowercase letter")
        
        if settings.PASSWORD_REQUIRE_NUMBER and not any(c.isdigit() for c in password):
            errors.append("Password must contain at least one number")
        
        if settings.PASSWORD_REQUIRE_SPECIAL and not any(c in "!@#$%^&*()_+-=[]{}|;':\",./<>?" for c in password):
            errors.append("Password must contain at least one special character")
        
        return len(errors) == 0, errors
    
    # ==================== User Operations ====================
    
    def create_user(self, user_data) -> User:
        """Create a new user."""
        # Validate password
        valid, errors = self.validate_password(user_data.password)
        if not valid:
            raise ValueError("; ".join(errors))
        
        # Check if user exists
        if self.db.query(User).filter(
            or_(User.email == user_data.email, User.username == user_data.username)
        ).first():
            raise ValueError("User with this email or username already exists")
        
        # Create user
        user = User(
            email=user_data.email,
            username=user_data.username,
            full_name=user_data.full_name,
            hashed_password=self.get_password_hash(user_data.password),
            phone=user_data.phone
        )
        
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        
        return user
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        return self.db.query(User).filter(User.email == email).first()
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username."""
        return self.db.query(User).filter(User.username == username).first()
    
    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID."""
        return self.db.query(User).filter(User.id == user_id).first()
    
    def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """Authenticate a user."""
        user = self.get_user_by_email(username) or self.get_user_by_username(username)
        
        if not user:
            return None
        
        if not self.verify_password(password, user.hashed_password):
            return None
        
        if not user.is_active:
            return None
        
        return user
    
    # ==================== Login Operations ====================
    
    def login(self, username: str, password: str, remember_me: bool = False) -> Dict[str, Any]:
        """Login a user and create session."""
        # Check rate limit
        rate_limit = redis_client.check_rate_limit(
            f"login:{username}",
            limit=settings.LOGIN_RATE_LIMIT,
            window=settings.LOGIN_RATE_WINDOW
        )
        
        if not rate_limit["allowed"]:
            raise ValueError("Too many login attempts. Please try again later.")
        
        # Authenticate user
        user = self.authenticate_user(username, password)
        
        if not user:
            # Record failed attempt
            existing_user = self.get_user_by_email(username) or self.get_user_by_username(username)
            if existing_user:
                self._record_failed_login(existing_user)
            raise ValueError("Invalid username or password")
        
        # Check if account is locked
        if user.locked_until and user.locked_until > datetime.utcnow():
            remaining = (user.locked_until - datetime.utcnow()).seconds // 60
            raise ValueError(f"Account locked. Try again in {remaining} minutes.")
        
        # Reset failed attempts on successful login
        self._reset_failed_login(user)
        
        # Update last login
        user.last_login = datetime.utcnow()
        self.db.commit()
        
        # Generate tokens
        tokens = self._generate_tokens(user)
        
        # Create session
        session_id = secrets.token_urlsafe(32)
        redis_client.create_session(
            session_id=session_id,
            user_id=user.id,
            expires_in=settings.SESSION_EXPIRE_MINUTES
        )
        
        return {
            "user": user,
            "tokens": tokens,
            "session": {"session_id": session_id}
        }
    
    def _record_failed_login(self, user: User) -> None:
        """Record a failed login attempt."""
        user.failed_login_attempts += 1
        
        # Lock account if too many attempts
        if user.failed_login_attempts >= settings.MAX_LOGIN_ATTEMPTS:
            user.locked_until = datetime.utcnow() + timedelta(minutes=settings.ACCOUNT_LOCKOUT_MINUTES)
        
        self.db.commit()
    
    def _reset_failed_login(self, user: User) -> None:
        """Reset failed login attempts."""
        user.failed_login_attempts = 0
        user.locked_until = None
        self.db.commit()
    
    # ==================== Token Operations ====================
    
    def _generate_tokens(self, user: User) -> Dict[str, str]:
        """Generate access and refresh tokens."""
        # Access token
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = jwt.encode(
            {
                "sub": str(user.id),
                "username": user.username,
                "email": user.email,
                "type": "access"
            },
            settings.SECRET_KEY,
            algorithm=settings.ALGORITHM,
            expires_delta=access_token_expires
        )
        
        # Refresh token
        refresh_token_expires = timedelta(minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES if remember_me else settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        refresh_token = jwt.encode(
            {
                "sub": str(user.id),
                "type": "refresh"
            },
            settings.SECRET_KEY,
            algorithm=settings.ALGORITHM,
            expires_delta=refresh_token_expires
        )
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "refresh_token": refresh_token
        }
    
    def refresh_access_token(self, refresh_token: str) -> Dict[str, str]:
        """Refresh access token using refresh token."""
        try:
            payload = jwt.decode(
                refresh_token,
                settings.SECRET_KEY,
                algorithms=[settings.ALGORITHM]
            )
            
            if payload.get("type") != "refresh":
                raise ValueError("Invalid token type")
            
            user_id = int(payload.get("sub"))
            user = self.get_user_by_id(user_id)
            
            if not user or not user.is_active:
                raise ValueError("User not found or inactive")
            
            return self._generate_tokens(user)
        
        except JWTError as e:
            raise ValueError(f"Invalid refresh token: {str(e)}")
    
    # ==================== Logout Operations ====================
    
    def logout(self, user_id: int, refresh_token: str) -> None:
        """Logout a user."""
        # Blacklist the refresh token
        redis_client.blacklist_token(refresh_token, expires_in=1800)
    
    def logout_all(self, user_id: int) -> None:
        """Logout from all devices."""
        # Delete all sessions
        redis_client.delete_user_sessions(user_id)
    
    # ==================== Password Change ====================
    
    def change_password(self, user: User, current_password: str, new_password: str) -> bool:
        """Change user password."""
        if not self.verify_password(current_password, user.hashed_password):
            return False
        
        # Validate new password
        valid, errors = self.validate_password(new_password)
        if not valid:
            raise ValueError("; ".join(errors))
        
        # Update password
        user.hashed_password = self.get_password_hash(new_password)
        self.db.commit()
        
        # Invalidate all sessions
        self.logout_all(user.id)
        
        return True
    
    # ==================== Current User ====================
    
    @staticmethod
    def get_current_user(
        token: str = None,
        request = None
    ) -> Optional[User]:
        """Get current user from token."""
        from database.database import SessionLocal
        
        if not token and request:
            token = request.cookies.get("access_token")
        
        if not token:
            return None
        
        try:
            payload = jwt.decode(
                token,
                settings.SECRET_KEY,
                algorithms=[settings.ALGORITHM]
            )
            
            if payload.get("type") != "access":
                return None
            
            user_id = int(payload.get("sub"))
            
            # Check if token is blacklisted
            if redis_client.is_blacklisted(token):
                return None
            
            db = SessionLocal()
            user = db.query(User).filter(User.id == user_id).first()
            
            if not user or not user.is_active:
                return None
            
            return user
        
        except JWTError:
            return None
