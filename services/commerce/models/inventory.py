"""Inventory models for commerce service."""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, UniqueConstraint, Numeric, Text
from sqlalchemy.orm import relationship
from database.database import Base


class Inventory(Base):
    """Inventory model for tracking product stock by SKU/variant."""
    __tablename__ = "inventory"
    
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # SKU and variant info
    sku = Column(String(50), unique=True, index=True, nullable=False)
    size = Column(String(20), nullable=True)  # XS, S, M, L, XL, etc.
    color = Column(String(50), nullable=True)
    
    # Stock counts
    quantity = Column(Integer, default=0)
    reserved_quantity = Column(Integer, default=0)  # Reserved for pending orders
    low_stock_threshold = Column(Integer, default=10)
    
    # Variant-specific pricing (overrides product price)
    price = Column(Numeric(10, 2), nullable=True)  # Variant-specific price
    description = Column(Text, nullable=True)  # Variant-specific description
    
    # Additional variant attributes
    weight = Column(Numeric(10, 3), nullable=True)  # Weight in kg
    barcode = Column(String(100), nullable=True)  # UPC/EAN barcode
    
    # Timestamps
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    product = relationship("Product", back_populates="inventory")
    
    # Unique constraint: product + size + color combination
    __table_args__ = (
        UniqueConstraint('product_id', 'size', 'color', name='uq_inventory_variant'),
    )
    
    @property
    def available_quantity(self) -> int:
        """Get available (non-reserved) quantity."""
        return max(0, self.quantity - self.reserved_quantity)
    
    @property
    def is_low_stock(self) -> bool:
        """Check if stock is below threshold."""
        return self.available_quantity <= self.low_stock_threshold
    
    @property
    def is_out_of_stock(self) -> bool:
        """Check if completely out of stock."""
        return self.available_quantity <= 0
    
    @property
    def effective_price(self) -> float:
        """Get effective price (variant price or product price)."""
        if self.price is not None:
            return float(self.price)
        if self.product:
            return float(self.product.price)
        return 0.0
