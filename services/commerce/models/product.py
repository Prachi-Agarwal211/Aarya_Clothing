"""Product models for commerce service."""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Numeric, Text, ForeignKey
from sqlalchemy.orm import relationship
from database.database import Base


class Product(Base):
    """Product model."""
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    slug = Column(String(255), unique=True, index=True, nullable=True)
    description = Column(Text, nullable=True)
    short_description = Column(String(500), nullable=True)
    
    # Pricing
    price = Column(Numeric(10, 2), nullable=False)
    mrp = Column(Numeric(10, 2), nullable=True)  # Maximum Retail Price
    
    # Category relationship
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True, index=True)
    brand_id = Column(Integer, nullable=True)
    
    # Legacy single image (for backward compatibility)
    image_url = Column(String(500), nullable=True)
    
    # Status flags
    is_active = Column(Boolean, default=True)
    is_featured = Column(Boolean, default=False)
    is_new_arrival = Column(Boolean, default=False)
    
    # Inventory (deprecated - use Inventory model)
    inventory_count = Column(Integer, default=0)
    
    # SEO
    meta_title = Column(String(255), nullable=True)
    meta_description = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    category = relationship("Category", back_populates="products")
    images = relationship("ProductImage", back_populates="product", cascade="all, delete-orphan", order_by="ProductImage.display_order")
    inventory = relationship("Inventory", back_populates="product", cascade="all, delete-orphan")
    
    @property
    def primary_image(self):
        """Get the primary image URL."""
        for img in self.images:
            if img.is_primary:
                return img.image_url
        return self.images[0].image_url if self.images else self.image_url
    
    @property
    def total_stock(self) -> int:
        """Get total available stock across all variants."""
        return sum(inv.available_quantity for inv in self.inventory)
    
    @property
    def is_on_sale(self) -> bool:
        """Check if product is on sale."""
        return self.mrp is not None and self.mrp > self.price
    
    @property
    def discount_percentage(self) -> int:
        """Calculate discount percentage."""
        if self.mrp and self.mrp > self.price:
            return int((self.mrp - self.price) / self.mrp * 100)
        return 0
