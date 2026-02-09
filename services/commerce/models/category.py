"""Category models for commerce service."""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from database.database import Base


class Category(Base):
    """Category model for product categorization with hierarchical support."""
    __tablename__ = "categories"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    slug = Column(String(100), unique=True, index=True, nullable=False)
    description = Column(Text, nullable=True)
    
    # Hierarchical structure (parent-child relationships)
    parent_id = Column(Integer, ForeignKey("categories.id"), nullable=True, index=True)
    
    # Display settings
    image_url = Column(String(500), nullable=True)
    display_order = Column(Integer, default=0)
    
    # Status flags
    is_active = Column(Boolean, default=True)
    is_featured = Column(Boolean, default=False)  # For homepage sections
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    parent = relationship("Category", remote_side=[id], back_populates="children")
    children = relationship("Category", back_populates="parent", cascade="all, delete-orphan")
    products = relationship("Product", back_populates="category")
    
    @property
    def is_root(self) -> bool:
        """Check if this is a root category (no parent)."""
        return self.parent_id is None
    
    @property
    def depth(self) -> int:
        """Get the depth level of this category (0 for root)."""
        depth = 0
        current = self
        while current.parent_id is not None:
            depth += 1
            current = current.parent
            if depth > 10:  # Safety limit
                break
        return depth
