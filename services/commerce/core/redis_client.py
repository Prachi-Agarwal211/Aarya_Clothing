"""Redis client for commerce service."""
import json
import redis
from typing import Optional, Any, Dict
from core.config import settings


class RedisClient:
    """Redis client for commerce operations."""
    
    def __init__(self):
        self.client = redis.Redis.from_url(
            settings.REDIS_URL,
            db=settings.REDIS_DB,
            decode_responses=True
        )
    
    def ping(self) -> bool:
        try:
            return self.client.ping()
        except redis.ConnectionError:
            return False
    
    # Cart Operations
    def get_cart(self, user_id: int) -> Optional[Dict]:
        """Get user's cart."""
        data = self.client.get(f"cart:{user_id}")
        if data:
            return json.loads(data)
        return None
    
    def set_cart(self, user_id: int, cart_data: Dict, expires_in: int = 168 * 60):
        """Save user's cart."""
        self.client.setex(f"cart:{user_id}", expires_in, json.dumps(cart_data))
    
    def delete_cart(self, user_id: int):
        """Delete user's cart."""
        self.client.delete(f"cart:{user_id}")
    
    # Cache Operations
    def set_cache(self, key: str, value: Any, expires_in: int = 300):
        self.client.setex(f"cache:{key}", expires_in, json.dumps(value))
    
    def get_cache(self, key: str) -> Optional[Any]:
        data = self.client.get(f"cache:{key}")
        if data:
            return json.loads(data)
        return None
    
    def delete_cache(self, key: str):
        self.client.delete(f"cache:{key}")
    
    def invalidate_pattern(self, pattern: str) -> int:
        keys = self.client.keys(f"cache:{pattern}")
        if keys:
            return self.client.delete(*keys)
        return 0
    
    # Inventory Locking
    def lock_inventory(self, product_id: int, quantity: int, timeout: int = 300) -> bool:
        """Lock inventory for a product."""
        key = f"inventory_lock:{product_id}"
        return self.client.set(key, quantity, nx=True, ex=timeout)
    
    def unlock_inventory(self, product_id: int):
        """Unlock inventory."""
        self.client.delete(f"inventory_lock:{product_id}")
    
    # ==================== Rate Limiting ====================
    
    def check_rate_limit(self, key: str, limit: int = 5, window: int = 300) -> Dict[str, Any]:
        """
        Check rate limit using sliding window algorithm.
        
        Args:
            key: Rate limit key (e.g., "login:email@example.com")
            limit: Maximum requests allowed in window
            window: Time window in seconds
            
        Returns:
            Dict with 'allowed' (bool) and 'remaining' (int)
        """
        rate_key = f"rate_limit:{key}"
        now = self.client.time()[0]  # Current timestamp
        window_start = now - window
        
        # Remove old entries outside window
        self.client.zremrangebyscore(rate_key, 0, window_start)
        
        # Count current requests in window
        current_count = self.client.zcard(rate_key)
        
        if current_count < limit:
            # Add current request
            self.client.zadd(rate_key, {str(now): now})
            self.client.expire(rate_key, window)
            
            return {
                "allowed": True,
                "remaining": limit - current_count - 1,
                "reset_after": window
            }
        else:
            # Get oldest entry to calculate reset time
            oldest = self.client.zrange(rate_key, 0, 0, withscores=True)
            reset_after = 0
            if oldest:
                reset_after = int(oldest[0][1] + window - now)
            
            return {
                "allowed": False,
                "remaining": 0,
                "reset_after": max(1, reset_after)
            }
    
    def blacklist_token(self, token: str, expires_in: int = 1800) -> bool:
        """
        Add token to blacklist.
        
        Args:
            token: JWT token to blacklist
            expires_in: Seconds until token expires
            
        Returns:
            True if successful
        """
        try:
            self.client.setex(f"blacklist:{token}", expires_in, "1")
            return True
        except Exception:
            return False
    
    def is_blacklisted(self, token: str) -> bool:
        """Check if token is blacklisted."""
        try:
            return self.client.exists(f"blacklist:{token}") > 0
        except Exception:
            return False
    
    # ==================== Session Operations ====================
    
    def create_session(self, session_id: str, user_id: int, expires_in: int = 1440) -> bool:
        """Create a new session."""
        try:
            session_data = {
                "user_id": user_id,
                "created_at": "now()"
            }
            self.client.hset(f"session:{session_id}", mapping=session_data)
            self.client.expire(f"session:{session_id}", expires_in)
            return True
        except Exception:
            return False
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session data."""
        try:
            data = self.client.hgetall(f"session:{session_id}")
            return data if data else None
        except Exception:
            return None
    
    def delete_session(self, session_id: str) -> bool:
        """Delete a session."""
        try:
            self.client.delete(f"session:{session_id}")
            return True
        except Exception:
            return False
    
    def delete_user_sessions(self, user_id: int) -> int:
        """Delete all sessions for a user."""
        try:
            # Find all session keys for this user
            pattern = f"session:*"
            keys = self.client.keys(pattern)
            deleted = 0
            for key in keys:
                data = self.client.hgetall(key)
                if data and data.get("user_id") == str(user_id):
                    self.client.delete(key)
                    deleted += 1
            return deleted
        except Exception:
            return 0


redis_client = RedisClient()
