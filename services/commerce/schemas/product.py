"""Product schemas for commerce service."""
from pydantic import BaseModel
from typing import Optional, List
from decimal import Decimal
from datetime import datetime

from schemas.product_image import ProductImageResponse
from schemas.inventory import InventoryResponse
from schemas.category import CategoryResponse


class ProductBase(BaseModel):
    """Base product schema."""
    name: str
    slug: Optional[str] = None
    description: Optional[str] = None
    short_description: Optional[str] = None
    price: Decimal
    compare_at_price: Optional[Decimal] = None
    category_id: Optional[int] = None
    brand_id: Optional[int] = None
    image_url: Optional[str] = None  # Legacy single image
    is_featured: bool = False
    is_new_arrival: bool = False
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None


class ProductCreate(ProductBase):
    """Schema for creating a product."""
    inventory_count: int = 0


class ProductUpdate(BaseModel):
    """Schema for updating a product."""
    name: Optional[str] = None
    slug: Optional[str] = None
    description: Optional[str] = None
    short_description: Optional[str] = None
    price: Optional[Decimal] = None
    compare_at_price: Optional[Decimal] = None
    category_id: Optional[int] = None
    brand_id: Optional[int] = None
    image_url: Optional[str] = None
    inventory_count: Optional[int] = None
    is_active: Optional[bool] = None
    is_featured: Optional[bool] = None
    is_new_arrival: Optional[bool] = None
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None


class ProductResponse(ProductBase):
    """Schema for product response."""
    id: int
    inventory_count: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ProductDetailResponse(ProductResponse):
    """Detailed product response with images and inventory."""
    images: List[ProductImageResponse] = []
    inventory: List[InventoryResponse] = []
    category: Optional[CategoryResponse] = None
    primary_image: Optional[str] = None
    total_stock: int = 0
    is_on_sale: bool = False
    
    class Config:
        from_attributes = True
