"""Commerce Service configuration."""
from pydantic_settings import BaseSettings
from typing import Optional, List
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    SERVICE_NAME: str = "aarya-commerce"
    ENVIRONMENT: str = "development"
    DEBUG: bool = False
    
    # Database
    DATABASE_URL: str = "postgresql://postgres:password@localhost/aarya_clothing"
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379"
    REDIS_DB: int = 0
    
    # Commerce Settings
    CART_TTL_HOURS: int = 168  # 7 days
    ORDER_TIMEOUT_MINUTES: int = 15
    INVENTORY_LOCK_TIMEOUT: int = 300
    
    # Cloudflare R2 Storage Settings
    R2_ACCOUNT_ID: str = ""
    R2_ACCESS_KEY_ID: str = ""
    R2_SECRET_ACCESS_KEY: str = ""
    R2_BUCKET_NAME: str = "aarya-clothing-images"
    R2_PUBLIC_URL: str = ""  # Public bucket URL or custom domain
    R2_REGION: str = "auto"
    
    # CORS
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000"]
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


@lru_cache()
def get_settings() -> "Settings":
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
