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


redis_client = RedisClient()
