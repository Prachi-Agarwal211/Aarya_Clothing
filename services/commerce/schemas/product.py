"""Product schemas for commerce service."""
from pydantic import BaseModel
from typing import Optional
from decimal import Decimal


class ProductBase(BaseModel):
    """Base product schema."""
    name: str
    description: Optional[str] = None
    price: Decimal
    category_id: Optional[int] = None
    brand_id: Optional[int] = None
    image_url: Optional[str] = None


class ProductCreate(ProductBase):
    """Schema for creating a product."""
    inventory_count: int = 0


class ProductUpdate(BaseModel):
    """Schema for updating a product."""
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[Decimal] = None
    category_id: Optional[int] = None
    brand_id: Optional[int] = None
    image_url: Optional[str] = None
    inventory_count: Optional[int] = None
    is_active: Optional[bool] = None


class ProductResponse(ProductBase):
    """Schema for product response."""
    id: int
    inventory_count: int
    is_active: bool
    created_at: str
    updated_at: str
    
    class Config:
        from_attributes = True
