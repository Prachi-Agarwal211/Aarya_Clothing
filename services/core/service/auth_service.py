"""Authentication service for Core Platform."""
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from passlib.context import CryptContext
from jose import jwt, JWTError
from sqlalchemy.orm import Session
from sqlalchemy import or_
from fastapi import Request

from core.config import settings
from core.redis_client import redis_client
from models.user import User, UserRole
from service.email_service import email_service


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
        
        # Create user with role
        role = getattr(user_data, 'role', UserRole.CUSTOMER)
        if isinstance(role, str):
            role = UserRole(role)
        
        user = User(
            email=user_data.email,
            username=user_data.username,
            full_name=user_data.full_name,
            hashed_password=self.get_password_hash(user_data.password),
            phone=getattr(user_data, 'phone', None),
            role=role
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
        
        # Generate tokens with remember_me
        tokens = self._generate_tokens(user, remember_me)
        
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
    
    def _generate_tokens(self, user: User, remember_me: bool = False) -> Dict[str, str]:
        """Generate access and refresh tokens with role."""
        now = datetime.utcnow()
        
        # Access token payload with role
        access_token_expires = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_payload = {
            "sub": str(user.id),
            "username": user.username,
            "email": user.email,
            "role": user.role.value if hasattr(user.role, 'value') else str(user.role),
            "type": "access",
            "exp": access_token_expires
        }
        access_token = jwt.encode(
            access_payload,
            settings.SECRET_KEY,
            algorithm=settings.ALGORITHM
        )
        
        # Refresh token payload
        refresh_minutes = settings.REFRESH_TOKEN_EXPIRE_MINUTES if remember_me else settings.ACCESS_TOKEN_EXPIRE_MINUTES * 2
        refresh_token_expires = now + timedelta(minutes=refresh_minutes)
        refresh_payload = {
            "sub": str(user.id),
            "type": "refresh",
            "exp": refresh_token_expires
        }
        refresh_token = jwt.encode(
            refresh_payload,
            settings.SECRET_KEY,
            algorithm=settings.ALGORITHM
        )
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
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
        request: Request = None
    ) -> Optional[User]:
        """Get current user from token."""
        from database.database import SessionLocal
        from fastapi import HTTPException, status
        
        token = None
        if request:
            token = request.cookies.get("access_token")
        
        if not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        try:
            payload = jwt.decode(
                token,
                settings.SECRET_KEY,
                algorithms=[settings.ALGORITHM]
            )
            
            if payload.get("type") != "access":
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token type",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            user_id = int(payload.get("sub"))
            
            # Check if token is blacklisted
            if redis_client.is_blacklisted(token):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token is blacklisted",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            db = SessionLocal()
            user = db.query(User).filter(User.id == user_id).first()
            
            if not user or not user.is_active:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User not found or inactive",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            return user
        
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
    
    # ==================== Password Reset ====================
    
    def request_password_reset(self, email: str, frontend_url: str = "http://localhost:3000") -> Dict[str, Any]:
        """Request password reset via email link (deprecated - use OTP method)."""
        # This method is kept for backward compatibility
        """Request password reset - generates token and sends email."""
        # Rate limiting
        rate_limit = redis_client.check_rate_limit(
            f"password_reset:{email}",
            limit=settings.PASSWORD_RESET_RATE_LIMIT,
            window=settings.PASSWORD_RESET_RATE_WINDOW
        )
        
        if not rate_limit["allowed"]:
            raise ValueError("Too many password reset requests. Please try again later.")
        
        # Find user
        user = self.get_user_by_email(email)
        
        if not user:
            # Don't reveal if user exists - still return success
            return {
                "success": True,
                "message": "If an account with this email exists, a password reset link has been sent."
            }
        
        if not user.is_active:
            return {
                "success": True,
                "message": "If an account with this email exists, a password reset link has been sent."
            }
        
        # Generate reset token
        reset_token = secrets.token_urlsafe(32)
        expires = datetime.utcnow() + timedelta(hours=settings.PASSWORD_RESET_TOKEN_EXPIRE_HOURS)
        
        # Store token in database
        user.password_reset_token = reset_token
        user.password_reset_expires = expires
        self.db.commit()
        
        # Build reset URL
        reset_url = f"{frontend_url}/reset-password?token={reset_token}"
        
        # Send email
        email_service.send_password_reset_email(
            to_email=user.email,
            reset_token=reset_token,
            reset_url=reset_url
        )
        
        return {
            "success": True,
            "message": "If an account with this email exists, a password reset link has been sent."
        }
    
    def verify_reset_token(self, token: str) -> Optional[User]:
        """Verify password reset token and return user if valid."""
        user = self.db.query(User).filter(
            User.password_reset_token == token
        ).first()
        
        if not user:
            return None
        
        if not user.password_reset_expires:
            return None
        
        if user.password_reset_expires < datetime.utcnow():
            # Token expired - clear it
            user.password_reset_token = None
            user.password_reset_expires = None
            self.db.commit()
            return None
        
        return user
    
    def reset_password(self, token: str, new_password: str) -> Dict[str, Any]:
        """Reset password using reset token."""
        user = self.verify_reset_token(token)
        
        if not user:
            raise ValueError("Invalid or expired password reset token.")
        
        # Validate new password
        valid, errors = self.validate_password(new_password)
        if not valid:
            raise ValueError("; ".join(errors))
        
        # Update password
        user.hashed_password = self.get_password_hash(new_password)
        user.password_reset_token = None
        user.password_reset_expires = None
        self.db.commit()
        
        # Invalidate all sessions
        self.logout_all(user.id)
        
        return {
            "success": True,
            "message": "Password has been reset successfully. Please login with your new password."
        }
    
    # ==================== Role-Based Access Helpers ====================
    
    @staticmethod
    def require_role(*allowed_roles: UserRole):
        """Decorator/dependency factory for role-based access."""
        def check_role(user: User) -> bool:
            if user is None:
                return False
            return user.role in allowed_roles
        return check_role
    
    @staticmethod
    def is_admin(user: User) -> bool:
        """Check if user is admin."""
        return user is not None and user.role == UserRole.ADMIN
    
    @staticmethod
    def is_staff_or_admin(user: User) -> bool:
        """Check if user is staff or admin."""
        return user is not None and user.role in [UserRole.ADMIN, UserRole.STAFF]

