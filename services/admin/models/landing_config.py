"""Landing page configuration models."""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, JSON
from database.database import Base


class LandingConfig(Base):
    """Landing page section configuration (JSONB-based)."""
    __tablename__ = "landing_config"
    
    id = Column(Integer, primary_key=True, index=True)
    section = Column(String(100), unique=True, nullable=False)
    config = Column(JSON, nullable=False, default={})
    is_active = Column(Boolean, default=True)
    updated_by = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class LandingImage(Base):
    """Landing page media assets."""
    __tablename__ = "landing_images"
    
    id = Column(Integer, primary_key=True, index=True)
    section = Column(String(100), nullable=False, index=True)
    image_url = Column(String(500), nullable=False)
    title = Column(String(255))
    subtitle = Column(String(255))
    link_url = Column(String(500))
    display_order = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
