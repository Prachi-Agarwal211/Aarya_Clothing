"""Redis client for session management and caching."""
import json
import redis
from typing import Optional, Dict, Any
from datetime import datetime
from core.config import settings


class RedisClient:
    """Redis client for session and cache operations."""
    
    def __init__(self):
        """Initialize Redis connection."""
        self.client = redis.Redis.from_url(
            settings.REDIS_URL,
            db=settings.REDIS_DB,
            decode_responses=True
        )
    
    def ping(self) -> bool:
        """Check Redis connection."""
        try:
            return self.client.ping()
        except redis.ConnectionError:
            return False
    
    # Session Management
    def create_session(
        self,
        session_id: str,
        user_id: int,
        user_agent: str = None,
        ip_address: str = None,
        expires_in: int = 1440  # 24 hours in minutes
    ) -> Dict[str, Any]:
        """Create a new session."""
        session_data = {
            "user_id": user_id,
            "user_agent": user_agent,
            "ip_address": ip_address,
            "created_at": datetime.utcnow().isoformat(),
            "last_activity": datetime.utcnow().isoformat()
        }
        
        self.client.setex(
            f"session:{session_id}",
            expires_in * 60,
            json.dumps(session_data)
        )
        
        # Add to user's session set
        self.client.sadd(f"user_sessions:{user_id}", session_id)
        self.client.expire(f"user_sessions:{user_id}", expires_in * 60)
        
        return session_data
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session data."""
        data = self.client.get(f"session:{session_id}")
        if data:
            return json.loads(data)
        return None
    
    def delete_session(self, session_id: str) -> bool:
        """Delete a session."""
        data = self.client.get(f"session:{session_id}")
        if data:
            session_data = json.loads(data)
            user_id = session_data.get("user_id")
            
            # Delete session
            self.client.delete(f"session:{session_id}")
            
            # Remove from user's session set
            if user_id:
                self.client.srem(f"user_sessions:{user_id}", session_id)
            
            return True
        return False
    
    def delete_user_sessions(self, user_id: int) -> int:
        """Delete all sessions for a user."""
        session_ids = self.client.smembers(f"user_sessions:{user_id}")
        deleted_count = 0
        
        for session_id in session_ids:
            self.client.delete(f"session:{session_id}")
            deleted_count += 1
        
        self.client.delete(f"user_sessions:{user_id}")
        return deleted_count
    
    def get_user_sessions(self, user_id: int) -> list:
        """Get all session IDs for a user."""
        return list(self.client.smembers(f"user_sessions:{user_id}"))
    
    # Token Blacklist (for logout)
    def blacklist_token(self, token: str, expires_in: int = 1800) -> None:
        """Add token to blacklist."""
        self.client.setex(f"blacklist:{token}", expires_in, "1")
    
    def is_blacklisted(self, token: str) -> bool:
        """Check if token is blacklisted."""
        return self.client.exists(f"blacklist:{token}") > 0
    
    # Rate Limiting
    def check_rate_limit(
        self,
        key: str,
        limit: int = 5,
        window: int = 300  # 5 minutes
    ) -> Dict[str, Any]:
        """Check rate limit for a key."""
        current = self.client.incr(f"ratelimit:{key}")
        
        if current == 1:
            self.client.expire(f"ratelimit:{key}", window)
        
        return {
            "allowed": current <= limit,
            "current": current,
            "limit": limit,
            "remaining": max(0, limit - current)
        }
    
    # OTP Storage
    def set_otp(self, key: str, otp: str, expires_in: int = 600) -> None:
        """Store OTP code."""
        self.client.setex(f"otp:{key}", expires_in, otp)
    
    def get_otp(self, key: str) -> Optional[str]:
        """Get OTP code."""
        return self.client.get(f"otp:{key}")
    
    def delete_otp(self, key: str) -> None:
        """Delete OTP code."""
        self.client.delete(f"otp:{key}")
    
    def increment_otp_attempts(self, key: str, max_attempts: int = 3) -> int:
        """Increment OTP verification attempts."""
        attempts = self.client.incr(f"otp_attempts:{key}")
        
        if attempts == 1:
            # Set expiry for attempts counter (15 minutes)
            self.client.expire(f"otp_attempts:{key}", 900)
        
        return attempts
    
    def get_otp_attempts(self, key: str) -> int:
        """Get OTP verification attempts."""
        attempts = self.client.get(f"otp_attempts:{key}")
        return int(attempts) if attempts else 0
    
    def clear_otp_attempts(self, key: str) -> None:
        """Clear OTP verification attempts."""
        self.client.delete(f"otp_attempts:{key}")
    
    # Cache Operations
    def set_cache(self, key: str, value: Any, expires_in: int = 300) -> None:
        """Set cached value."""
        self.client.setex(f"cache:{key}", expires_in, json.dumps(value))
    
    def get_cache(self, key: str) -> Optional[Any]:
        """Get cached value."""
        data = self.client.get(f"cache:{key}")
        if data:
            return json.loads(data)
        return None
    
    def delete_cache(self, key: str) -> None:
        """Delete cached value."""
        self.client.delete(f"cache:{key}")
    
    def invalidate_pattern(self, pattern: str) -> int:
        """Delete all keys matching pattern."""
        keys = self.client.keys(f"cache:{pattern}")
        if keys:
            return self.client.delete(*keys)
        return 0


# Global redis client instance
redis_client = RedisClient()
