"""Order models for commerce service."""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Numeric, DateTime, ForeignKey, Text, Enum
from sqlalchemy.orm import relationship
import enum
from database.database import Base


class OrderStatus(str, enum.Enum):
    """Order status enumeration."""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
    RETURNED = "returned"
    REFUNDED = "refunded"


class Order(Base):
    """Order model with comprehensive tracking."""
    __tablename__ = "orders"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    
    # Payment integration
    transaction_id = Column(String(255), nullable=True, index=True)  # Links to payment service
    
    # Pricing
    subtotal = Column(Numeric(10, 2), nullable=False)
    discount_applied = Column(Numeric(10, 2), default=0)
    promo_code = Column(String(50), nullable=True)
    shipping_cost = Column(Numeric(10, 2), default=0)
    total_amount = Column(Numeric(10, 2), nullable=False)
    
    # Status
    status = Column(Enum(OrderStatus), default=OrderStatus.PENDING, nullable=False, index=True)
    
    # Shipping
    shipping_address = Column(Text, nullable=True)
    shipping_method = Column(String(100), default='standard')
    tracking_number = Column(String(100), nullable=True)
    
    # Notes
    order_notes = Column(Text, nullable=True)
    
    # Cancellation
    cancelled_at = Column(DateTime, nullable=True)
    cancellation_reason = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    shipped_at = Column(DateTime, nullable=True)
    delivered_at = Column(DateTime, nullable=True)
    
    # Relationships
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")


class OrderItem(Base):
    """Order item model with inventory tracking."""
    __tablename__ = "order_items"
    
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id = Column(Integer, nullable=False, index=True)
    inventory_id = Column(Integer, ForeignKey("inventory.id"), nullable=True)  # Tracks specific variant
    
    # Product details (snapshot at time of order)
    product_name = Column(String(255), nullable=False)
    sku = Column(String(50), nullable=True)
    size = Column(String(20), nullable=True)
    color = Column(String(50), nullable=True)
    
    # Pricing
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Numeric(10, 2), nullable=False)
    price = Column(Numeric(10, 2), nullable=False)  # unit_price * quantity
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    order = relationship("Order", back_populates="items")
