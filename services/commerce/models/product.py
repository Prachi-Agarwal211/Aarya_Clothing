"""Product models for commerce service."""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Numeric, Text
from database.database import Base


class Product(Base):
    """Product model."""
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    price = Column(Numeric(10, 2), nullable=False)
    category_id = Column(Integer, nullable=True)
    brand_id = Column(Integer, nullable=True)
    image_url = Column(String(500), nullable=True)
    inventory_count = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
