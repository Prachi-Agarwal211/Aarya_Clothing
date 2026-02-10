"""Admin Service configuration."""
from pydantic_settings import BaseSettings
from typing import Optional, List
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    SERVICE_NAME: str = "aarya-admin"
    ENVIRONMENT: str = "development"
    DEBUG: bool = False
    
    # Database (shared with other services)
    DATABASE_URL: str = "postgresql://postgres:password@localhost/aarya_clothing"
    DATABASE_POOL_SIZE: int = 5
    DATABASE_MAX_OVERFLOW: int = 10
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379"
    REDIS_DB: int = 0
    
    # Security (shared with Core service)
    SECRET_KEY: str = "your-super-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    
    # Service URLs
    CORE_SERVICE_URL: str = "http://localhost:8001"
    COMMERCE_SERVICE_URL: str = "http://localhost:8002"
    PAYMENT_SERVICE_URL: str = "http://localhost:8003"
    
    # Cloudflare R2 Storage Settings
    R2_ACCOUNT_ID: str = ""
    R2_ACCESS_KEY_ID: str = ""
    R2_SECRET_ACCESS_KEY: str = ""
    R2_BUCKET_NAME: str = "aarya-clothing-images"
    R2_PUBLIC_URL: str = ""  # Public bucket URL or custom domain
    R2_REGION: str = "auto"
    
    # CORS
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:3001",
        "https://aaryaclothing.cloud"
    ]
    
    model_config = {"env_file": ".env", "extra": "allow"}


@lru_cache()
def get_settings():
    return Settings()


settings = get_settings()
