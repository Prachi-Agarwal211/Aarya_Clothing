"""Redis client for admin service."""
import json
import redis
from typing import Optional, Any, Dict
from core.config import settings


class RedisClient:
    """Redis client for admin service caching and real-time features."""
    
    def __init__(self):
        self.client = redis.Redis.from_url(
            settings.REDIS_URL,
            db=settings.REDIS_DB,
            decode_responses=True
        )
    
    def ping(self) -> bool:
        try:
            return self.client.ping()
        except Exception:
            return False
    
    def get_cache(self, key: str) -> Optional[Any]:
        """Get cached data."""
        try:
            data = self.client.get(key)
            return json.loads(data) if data else None
        except Exception:
            return None
    
    def set_cache(self, key: str, data: Any, ttl: int = 300) -> bool:
        """Set cache with TTL (default 5 minutes)."""
        try:
            self.client.setex(key, ttl, json.dumps(data, default=str))
            return True
        except Exception:
            return False
    
    def delete_cache(self, key: str) -> bool:
        """Delete cached data."""
        try:
            self.client.delete(key)
            return True
        except Exception:
            return False
    
    def invalidate_pattern(self, pattern: str) -> int:
        """Delete all keys matching a pattern."""
        try:
            keys = self.client.keys(pattern)
            if keys:
                return self.client.delete(*keys)
            return 0
        except Exception:
            return 0
    
    def publish(self, channel: str, message: Any) -> bool:
        """Publish message to a Redis channel (for real-time notifications)."""
        try:
            self.client.publish(channel, json.dumps(message, default=str))
            return True
        except Exception:
            return False


redis_client = RedisClient()
