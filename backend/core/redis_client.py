"""Redis client for session management and caching."""
import redis
import json
from typing import Optional, Dict, Any
from datetime import timedelta
from core.config import settings


class RedisClient:
    """Redis client wrapper for session and token management."""
    
    def __init__(self):
        self._client: Optional[redis.Redis] = None
    
    @property
    def client(self) -> redis.Redis:
        """Get or create Redis client."""
        if self._client is None:
            self._client = redis.from_url(
                settings.REDIS_URL,
                db=settings.REDIS_DB,
                decode_responses=True,
            )
        return self._client
    
    # ==================== Session Management ====================
    
    def set_session(self, session_id: str, data: Dict[str, Any], 
                   expires_in: int = 3600) -> bool:
        """Store session data."""
        key = f"session:{session_id}"
        self.client.setex(key, expires_in, json.dumps(data))
        return True
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve session data."""
        key = f"session:{session_id}"
        data = self.client.get(key)
        if data:
            return json.loads(data)
        return None
    
    def delete_session(self, session_id: str) -> bool:
        """Delete session."""
        key = f"session:{session_id}"
        self.client.delete(key)
        return True
    
    # ==================== Refresh Token Storage ====================
    
    def store_refresh_token(self, user_id: int, token: str, 
                           expires_in: int = 604800) -> bool:
        """Store refresh token for user."""
        key = f"refresh_token:{user_id}:{token}"
        self.client.setex(key, expires_in, "valid")
        
        # Also maintain a set of valid tokens per user
        set_key = f"user_refresh_tokens:{user_id}"
        self.client.sadd(set_key, token)
        self.client.expire(set_key, expires_in)
        return True
    
    def validate_refresh_token(self, user_id: int, token: str) -> bool:
        """Check if refresh token is valid."""
        key = f"refresh_token:{user_id}:{token}"
        return self.client.exists(key) == 1
    
    def revoke_refresh_token(self, user_id: int, token: str) -> bool:
        """Revoke a specific refresh token."""
        key = f"refresh_token:{user_id}:{token}"
        set_key = f"user_refresh_tokens:{user_id}"
        
        self.client.delete(key)
        self.client.srem(set_key, token)
        return True
    
    def revoke_all_user_tokens(self, user_id: int) -> int:
        """Revoke all refresh tokens for a user."""
        set_key = f"user_refresh_tokens:{user_id}"
        tokens = self.client.smembers(set_key)
        
        count = 0
        for token in tokens:
            key = f"refresh_token:{user_id}:{token}"
            self.client.delete(key)
            count += 1
        
        self.client.delete(set_key)
        return count
    
    # ==================== Token Blacklist ====================
    
    def blacklist_token(self, token: str, expires_in: int = 3600) -> bool:
        """Blacklist an access token."""
        key = f"blacklist:{token}"
        self.client.setex(key, expires_in, "1")
        return True
    
    def is_token_blacklisted(self, token: str) -> bool:
        """Check if token is blacklisted."""
        key = f"blacklist:{token}"
        return self.client.exists(key) == 1
    
    # ==================== Rate Limiting ====================
    
    def check_rate_limit(self, key: str, limit: int, 
                        window: int) -> tuple[bool, int]:
        """
        Check rate limit using sliding window.
        Returns (allowed, remaining_attempts).
        """
        rate_key = f"rate_limit:{key}"
        current = self.client.get(rate_key)
        
        if current is None:
            self.client.setex(rate_key, window, limit - 1)
            return True, limit - 1
        
        remaining = int(current)
        if remaining <= 0:
            return False, 0
        
        self.client.decr(rate_key)
        return True, remaining - 1
    
    # ==================== Login Attempt Tracking ====================
    
    def record_login_attempt(self, identifier: str) -> int:
        """Record a failed login attempt and return count."""
        key = f"login_attempts:{identifier}"
        count = self.client.incr(key)
        self.client.expire(key, settings.LOGIN_RATE_WINDOW)
        return count
    
    def get_login_attempts(self, identifier: str) -> int:
        """Get failed login attempt count."""
        key = f"login_attempts:{identifier}"
        count = self.client.get(key)
        return int(count) if count else 0
    
    def clear_login_attempts(self, identifier: str):
        """Clear login attempts after successful login."""
        key = f"login_attempts:{identifier}"
        self.client.delete(key)
    
    # ==================== Health Check ====================
    
    def ping(self) -> bool:
        """Check if Redis is available."""
        try:
            return self.client.ping()
        except redis.ConnectionError:
            return False


# Global Redis client instance
redis_client = RedisClient()
