"""Schemas for admin dashboard, analytics, orders, customers, and inventory."""
from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional, List, Any, Dict
from enum import Enum


# ==================== Dashboard ====================

class InventoryAlert(BaseModel):
    low_stock: int = 0
    out_of_stock: int = 0

class DashboardOverview(BaseModel):
    total_revenue: float = 0
    total_orders: int = 0
    total_customers: int = 0
    total_products: int = 0
    pending_orders: int = 0
    today_revenue: float = 0
    today_orders: int = 0
    inventory_alerts: InventoryAlert = InventoryAlert()
    recent_orders: List[Dict[str, Any]] = []


# ==================== Analytics ====================

class RevenueData(BaseModel):
    period: str
    revenue: float
    orders: int

class RevenueAnalytics(BaseModel):
    total_revenue: float
    period_data: List[RevenueData]
    growth_percentage: Optional[float] = None

class CustomerAnalytics(BaseModel):
    total_customers: int
    new_customers_today: int
    new_customers_this_week: int
    new_customers_this_month: int
    returning_customers: int

class TopProduct(BaseModel):
    product_id: int
    product_name: str
    total_sold: int
    total_revenue: float

class TopProductsAnalytics(BaseModel):
    top_products: List[TopProduct]
    period: str


# ==================== Orders ====================

class OrderStatusUpdate(BaseModel):
    status: str
    tracking_number: Optional[str] = None
    courier: Optional[str] = None
    estimated_delivery: Optional[str] = None
    notes: Optional[str] = None

class BulkOrderUpdate(BaseModel):
    order_ids: List[int]
    status: str
    notes: Optional[str] = None

class OrderResponse(BaseModel):
    id: int
    user_id: int
    subtotal: float = 0
    discount_applied: float = 0
    shipping_cost: float = 0
    total_amount: float
    status: str
    shipping_address: Optional[str] = None
    transaction_id: Optional[str] = None
    created_at: Optional[datetime] = None
    items: List[Dict[str, Any]] = []
    customer: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True


# ==================== Inventory ====================

class AddStockRequest(BaseModel):
    product_id: int
    sku: str
    quantity: int = Field(gt=0)
    cost_price: Optional[float] = None
    supplier: Optional[str] = None
    notes: Optional[str] = None

class AdjustStockRequest(BaseModel):
    inventory_id: int
    adjustment: int  # Negative = removal, Positive = addition
    reason: str  # damaged_items, return, correction, transfer
    notes: Optional[str] = None

class BulkInventoryUpdate(BaseModel):
    updates: List[Dict[str, Any]]

class VariantCreate(BaseModel):
    sku: str
    size: Optional[str] = None
    color: Optional[str] = None
    quantity: int = 0
    price: Optional[float] = None
    barcode: Optional[str] = None

class VariantUpdate(BaseModel):
    size: Optional[str] = None
    color: Optional[str] = None
    quantity: Optional[int] = None
    price: Optional[float] = None
    barcode: Optional[str] = None

class InventoryMovementResponse(BaseModel):
    id: int
    inventory_id: int
    product_id: int
    adjustment: int
    reason: str
    notes: Optional[str] = None
    supplier: Optional[str] = None
    performed_by: Optional[int] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ==================== Staff ====================

class StaffDashboard(BaseModel):
    inventory_alerts: InventoryAlert
    pending_orders: int
    today_tasks: Dict[str, int]
    quick_actions: List[str]

class OrderProcessRequest(BaseModel):
    status: str = "processing"
    items: Optional[List[Dict[str, Any]]] = None
    notes: Optional[str] = None

class OrderShipRequest(BaseModel):
    tracking_number: str
    courier: str
    estimated_delivery: Optional[str] = None
    notes: Optional[str] = None

class ReservationRelease(BaseModel):
    order_id: int
    items: List[Dict[str, Any]]
    reason: str

class TaskComplete(BaseModel):
    notes: Optional[str] = None


# ==================== Users ====================

class UserListItem(BaseModel):
    id: int
    email: str
    username: str
    full_name: str
    role: str
    is_active: bool
    created_at: Optional[datetime] = None
    order_count: int = 0
    total_spent: float = 0

    class Config:
        from_attributes = True

class UserStatusUpdate(BaseModel):
    is_active: bool


# ==================== Chat ====================

class ChatRoomCreate(BaseModel):
    customer_id: int
    customer_name: Optional[str] = None
    customer_email: Optional[str] = None
    subject: Optional[str] = None
    priority: str = "medium"
    order_id: Optional[int] = None

class ChatMessageCreate(BaseModel):
    message: str
    sender_type: str = "staff"

class ChatRoomResponse(BaseModel):
    id: int
    customer_id: int
    customer_name: Optional[str] = None
    customer_email: Optional[str] = None
    assigned_to: Optional[int] = None
    subject: Optional[str] = None
    status: str
    priority: str
    order_id: Optional[int] = None
    created_at: Optional[datetime] = None
    last_message: Optional[str] = None

    class Config:
        from_attributes = True

class ChatMessageResponse(BaseModel):
    id: int
    room_id: int
    sender_id: Optional[int] = None
    sender_type: str
    message: str
    is_read: bool
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ==================== Landing Config ====================

class LandingConfigUpdate(BaseModel):
    config: Dict[str, Any]
    is_active: Optional[bool] = None

class LandingConfigResponse(BaseModel):
    id: int
    section: str
    config: Dict[str, Any]
    is_active: bool
    updated_by: Optional[int] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class LandingImageCreate(BaseModel):
    section: str
    image_url: str
    title: Optional[str] = None
    subtitle: Optional[str] = None
    link_url: Optional[str] = None
    display_order: int = 0

class LandingImageResponse(BaseModel):
    id: int
    section: str
    image_url: str
    title: Optional[str] = None
    subtitle: Optional[str] = None
    link_url: Optional[str] = None
    display_order: int
    is_active: bool
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True
