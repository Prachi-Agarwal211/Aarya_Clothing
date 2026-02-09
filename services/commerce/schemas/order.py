"""Order schemas for commerce service."""
from pydantic import BaseModel
from typing import List, Optional
from decimal import Decimal


class CartItem(BaseModel):
    """Cart item schema."""
    product_id: int
    quantity: int = 1


class CartItemResponse(BaseModel):
    """Cart item response schema."""
    product_id: int
    name: str
    price: float
    quantity: int
    image_url: Optional[str] = None


class CartResponse(BaseModel):
    """Cart response schema."""
    user_id: int
    items: List[CartItemResponse]
    total: float


class OrderCreate(BaseModel):
    """Schema for creating an order."""
    user_id: int
    shipping_address: str


class OrderItemResponse(BaseModel):
    """Order item response schema."""
    id: int
    product_id: int
    quantity: int
    price: float
    
    class Config:
        from_attributes = True


class OrderUpdate(BaseModel):
    """Schema for updating an order."""
    status: Optional[str] = None
    shipping_address: Optional[str] = None


class OrderResponse(BaseModel):
    """Order response schema."""
    id: int
    user_id: int
    total_amount: Decimal
    status: str
    shipping_address: Optional[str] = None
    created_at: str
    updated_at: str
    items: List[OrderItemResponse] = []
    
    class Config:
        from_attributes = True
