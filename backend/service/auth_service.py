"""Authentication service with JWT, Refresh Tokens, Cookie Sessions, and Security Features."""
import uuid
import secrets
from datetime import datetime, timedelta
from typing import Optional
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from database.database import get_db
from models.user import User
from schemas.auth import Token, TokenPayload, UserCreate
from core.config import settings
from core.redis_client import redis_client


# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme for token extraction
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="api/v1/auth/login",
    auto_error=True
)


class AuthService:
    """Authentication service handling all auth operations."""
    
    def __init__(self, db: Session):
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
    
    # ==================== User Management ====================
    
    def create_user(self, user_data: UserCreate) -> User:
        """Create a new user with hashed password."""
        # Check if user exists
        if self.get_user_by_email(user_data.email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        if self.get_user_by_username(user_data.username):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken"
            )
        
        # Create user (inactive until email verified)
        hashed_password = self.get_password_hash(user_data.password)
        db_user = User(
            email=user_data.email,
            username=user_data.username,
            full_name=user_data.full_name,
            hashed_password=hashed_password,
            phone=user_data.phone,
            address=user_data.address,
            is_active=False  # Require OTP verification
        )
        
        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)
        
        return db_user
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        return self.db.query(User).filter(User.email == email).first()
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username."""
        return self.db.query(User).filter(User.username == username).first()
    
    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID."""
        return self.db.query(User).filter(User.id == user_id).first()
    
    # ==================== Session Management ====================
    
    def create_session(self, user: User) -> dict:
        """Create a new session for the user."""
        session_id = str(uuid.uuid4())
        
        # Session data
        session_data = {
            "user_id": user.id,
            "email": user.email,
            "username": user.username,
            "is_admin": user.is_admin,
            "created_at": datetime.utcnow().isoformat(),
            "expires_at": (datetime.utcnow() + timedelta(minutes=settings.SESSION_EXPIRE_MINUTES)).isoformat()
        }
        
        # Store session in Redis
        redis_client.set_session(
            session_id=session_id,
            data=session_data,
            expires_in=settings.SESSION_EXPIRE_MINUTES * 60  # Convert to seconds
        )
        
        return {
            "session_id": session_id,
            "expires_in": settings.SESSION_EXPIRE_MINUTES * 60
        }
    
    def validate_session(self, session_id: str) -> Optional[dict]:
        """Validate a session from Redis."""
        return redis_client.get_session(session_id)
    
    def delete_session(self, session_id: str) -> bool:
        """Delete a session."""
        return redis_client.delete_session(session_id)
    
    # ==================== Authentication ====================
    
    def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """Authenticate user with username/email and password."""
        user = self.db.query(User).filter(
            (User.email == username) | (User.username == username)
        ).first()
        
        if not user:
            return None
        
        if user.is_locked:
            return None
        
        if not self.verify_password(password, user.hashed_password):
            return None
        
        return user
    
    def login(self, username: str, password: str, 
             remember_me: bool = False) -> dict:
        """
        Login user and create session.
        Returns session info with cookies ready to set.
        """
        # Check rate limiting
        allowed, remaining = redis_client.check_rate_limit(
            f"login:{username}",
            settings.LOGIN_RATE_LIMIT,
            settings.LOGIN_RATE_WINDOW
        )
        
        if not allowed:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many login attempts. Please try again later."
            )
        
        # Authenticate user
        user = self.authenticate_user(username, password)
        
        if not user:
            attempts = redis_client.record_login_attempt(username)
            remaining_attempts = settings.MAX_LOGIN_ATTEMPTS - attempts
            
            if remaining_attempts <= 0:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Account locked due to too many failed attempts."
                )
            
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid credentials. {remaining_attempts} attempts remaining."
            )
        
        # Check if email is verified
        if not user.email_verified:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Please verify your email before logging in."
            )
        
        # Clear failed attempts on success
        redis_client.clear_login_attempts(username)
        
        # Reset user's failed attempts counter
        user.reset_failed_attempts()
        self.db.commit()
        
        # Generate tokens
        tokens = self._create_token_pair(user, remember_me)
        
        # Create session
        session = self.create_session(user)
        
        # Store refresh token in Redis
        expires_seconds = settings.REFRESH_TOKEN_EXPIRE_MINUTES * 60
        redis_client.store_refresh_token(
            user.id,
            tokens['refresh_token'],
            expires_seconds
        )
        
        return {
            "user": user,
            "tokens": tokens,
            "session": session,
            "expires_in": session["expires_in"]
        }
    
    def logout(self, user_id: int, refresh_token: str = None) -> bool:
        """Logout user by revoking refresh token and deleting session."""
        if refresh_token:
            redis_client.revoke_refresh_token(user_id, refresh_token)
        return True
    
    def logout_all(self, user_id: int) -> int:
        """Logout from all devices by revoking all tokens."""
        return redis_client.revoke_all_user_tokens(user_id)
    
    # ==================== Token Operations ====================
    
    def _create_token_pair(self, user: User, 
                          remember_me: bool = False) -> dict:
        """Create access and refresh token pair."""
        
        # Access token (30 minutes)
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = self._create_access_token(
            data={"sub": user.email, "type": "access"},
            expires_delta=access_token_expires
        )
        
        # Refresh token (24 hours if remember_me, else 30 minutes)
        if remember_me:
            refresh_expires = timedelta(minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES)
        else:
            refresh_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        
        refresh_token = self._create_refresh_token(
            user_id=user.id,
            expires_delta=refresh_expires
        )
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": int(access_token_expires.total_seconds())
        }
    
    def _create_access_token(self, data: dict, 
                            expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT access token."""
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(
                minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
            )
        
        to_encode.update({"exp": expire, "type": "access"})
        encoded_jwt = jwt.encode(
            to_encode, 
            settings.SECRET_KEY, 
            algorithm=settings.ALGORITHM
        )
        return encoded_jwt
    
    def _create_refresh_token(self, user_id: int,
                             expires_delta: Optional[timedelta] = None) -> str:
        """Create refresh token."""
        to_encode = {
            "sub": str(user_id),
            "type": "refresh",
            "jti": secrets.token_urlsafe(32)
        }
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(
                minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES
            )
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(
            to_encode,
            settings.SECRET_KEY,
            algorithm=settings.ALGORITHM
        )
        return encoded_jwt
    
    def refresh_access_token(self, refresh_token: str) -> dict:
        """Refresh access token using refresh token."""
        try:
            payload = jwt.decode(
                refresh_token,
                settings.SECRET_KEY,
                algorithms=[settings.ALGORITHM]
            )
            
            if payload.get("type") != "refresh":
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token type"
                )
            
            user_id = int(payload.get("sub"))
            
            if not redis_client.validate_refresh_token(user_id, refresh_token):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Refresh token has been revoked"
                )
            
            user = self.get_user_by_id(user_id)
            if not user or not user.is_active:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User not found or inactive"
                )
            
            # Create new token pair
            tokens = self._create_token_pair(user, remember_me=False)
            
            # Store new refresh token
            redis_client.store_refresh_token(
                user.id,
                tokens['refresh_token'],
                settings.REFRESH_TOKEN_EXPIRE_MINUTES * 60
            )
            redis_client.revoke_refresh_token(user.id, refresh_token)
            
            return tokens
            
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token"
            )
    
    # ==================== Token Validation ====================
    
    @staticmethod
    async def get_current_user(
        token: str = Depends(oauth2_scheme),
        db: Session = Depends(get_db)
    ) -> User:
        """Get current user from JWT token."""
        
        if redis_client.is_token_blacklisted(token):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has been revoked",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
        try:
            payload = jwt.decode(
                token, 
                settings.SECRET_KEY, 
                algorithms=[settings.ALGORITHM]
            )
            
            if payload.get("type") != "access":
                raise credentials_exception
            
            email: str = payload.get("sub")
            if email is None:
                raise credentials_exception
                
        except JWTError:
            raise credentials_exception
        
        user = db.query(User).filter(User.email == email).first()
        if user is None:
            raise credentials_exception
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is inactive"
            )
        
        if user.is_locked:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is locked"
            )
        
        return user
    
    @staticmethod
    async def get_current_user_optional(
        token: Optional[str] = Depends(
            OAuth2PasswordBearer(tokenUrl="api/v1/auth/login", auto_error=False)
        ),
        db: Session = Depends(get_db)
    ) -> Optional[User]:
        """Get current user if token is present, None otherwise."""
        if token is None:
            return None
        
        try:
            return await AuthService.get_current_user(token, db)
        except HTTPException:
            return None
    
    # ==================== Password Management ====================
    
    def change_password(self, user: User, current_password: str,
                       new_password: str) -> bool:
        """Change user password."""
        if not self.verify_password(current_password, user.hashed_password):
            return False
        
        user.hashed_password = self.get_password_hash(new_password)
        self.db.commit()
        
        # Revoke all sessions
        self.logout_all(user.id)
        
        return True
    
    def validate_password_strength(self, password: str) -> tuple[bool, list[str]]:
        """Validate password meets requirements."""
        errors = []
        
        if len(password) < settings.PASSWORD_MIN_LENGTH:
            errors.append(f"Password must be at least {settings.PASSWORD_MIN_LENGTH} characters")
        
        if settings.PASSWORD_REQUIRE_UPPERCASE and not re.search(r'[A-Z]', password):
            errors.append("Password must contain at least one uppercase letter")
        
        if settings.PASSWORD_REQUIRE_LOWERCASE and not re.search(r'[a-z]', password):
            errors.append("Password must contain at least one lowercase letter")
        
        if settings.PASSWORD_REQUIRE_NUMBER and not re.search(r'[0-9]', password):
            errors.append("Password must contain at least one number")
        
        if settings.PASSWORD_REQUIRE_SPECIAL and not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            errors.append("Password must contain at least one special character")
        
        return len(errors) == 0, errors
