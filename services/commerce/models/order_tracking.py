"""Order tracking models for commerce service."""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from database.database import Base
from models.order import OrderStatus


class OrderTracking(Base):
    """Order tracking/history model for status changes."""
    __tablename__ = "order_tracking"
    
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Status information
    status = Column(Enum(OrderStatus), nullable=False)
    location = Column(String(255), nullable=True)
    notes = Column(Text, nullable=True)
    
    # Staff tracking
    updated_by = Column(Integer, nullable=True)  # Staff user ID who made the update
    
    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    order = relationship("Order", foreign_keys=[order_id])
