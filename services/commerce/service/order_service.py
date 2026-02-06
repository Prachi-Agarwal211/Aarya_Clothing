"""Order service for managing order operations."""
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc
from fastapi import HTTPException, status
from decimal import Decimal
from datetime import datetime

from models.order import Order, OrderItem, OrderStatus
from models.product import Product
from models.inventory import Inventory
from service.inventory_service import InventoryService
from service.cart_service import CartService
from service.promotion_service import PromotionService
from schemas.order import OrderCreate, OrderUpdate


class OrderService:
    """Service for order management operations."""
    
    def __init__(self, db: Session):
        """Initialize order service."""
        self.db = db
        self.inventory_service = InventoryService(db)
        self.cart_service = CartService(db)
        self.promotion_service = PromotionService(db)
    
    def get_user_orders(
        self,
        user_id: int,
        skip: int = 0,
        limit: int = 50
    ) -> List[Order]:
        """Get all orders for a user with pagination."""
        return self.db.query(Order).filter(
            Order.user_id == user_id
        ).order_by(desc(Order.created_at)).offset(skip).limit(limit).all()
    
    def get_order_by_id(self, order_id: int, user_id: Optional[int] = None) -> Optional[Order]:
        """Get order by ID with optional user validation."""
        query = self.db.query(Order).filter(Order.id == order_id)
        
        if user_id:
            query = query.filter(Order.user_id == user_id)
        
        return query.first()
    
    def create_order(
        self,
        user_id: int,
        shipping_address: str,
        promo_code: Optional[str] = None,
        order_notes: Optional[str] = None,
        transaction_id: Optional[str] = None
    ) -> Order:
        """
        Create order from user's cart.
        
        Flow:
        1. Get cart
        2. Validate cart not empty
        3. Confirm stock reservations
        4. Apply promo code if provided
        5. Calculate totals
        6. Create order + order items
        7. Confirm inventory reservations
        8. Record promo usage
        9. Clear cart
        """
        # Get cart
        cart = self.cart_service.get_cart(user_id)
        
        if not cart.get("items") or len(cart["items"]) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cart is empty"
            )
        
        # Confirm all reservations are still valid
        try:
            self.cart_service.confirm_cart_for_checkout(user_id)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        
        # Calculate subtotal
        subtotal = Decimal(sum(
            item["price"] * item["quantity"] for item in cart["items"]
        ))
        
        # Apply promotion if provided
        discount_applied = Decimal(0)
        if promo_code:
            validation = self.promotion_service.validate_promotion(
                code=promo_code,
                user_id=user_id,
                order_total=subtotal
            )
            
            if validation["valid"]:
                discount_applied = validation["discount_amount"]
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=validation["message"]
                )
        
        # Calculate totals
        shipping_cost = Decimal(0)  # TODO: Calculate based on shipping method
        total_amount = subtotal - discount_applied + shipping_cost
        
        # Create order
        order = Order(
            user_id=user_id,
            transaction_id=transaction_id,
            subtotal=subtotal,
            discount_applied=discount_applied,
            promo_code=promo_code,
            shipping_cost=shipping_cost,
            total_amount=total_amount,
            status=OrderStatus.PENDING,
            shipping_address=shipping_address,
            order_notes=order_notes
        )
        
        self.db.add(order)
        self.db.flush()  # Get order ID
        
        # Create order items
        for cart_item in cart["items"]:
            # Get product and inventory
            product = self.db.query(Product).filter(
                Product.id == cart_item["product_id"]
            ).first()
            
            inventory = None
            if cart_item.get("sku"):
                inventory = self.db.query(Inventory).filter(
                    Inventory.sku == cart_item["sku"]
                ).first()
            
            order_item = OrderItem(
                order_id=order.id,
                product_id=cart_item["product_id"],
                inventory_id=inventory.id if inventory else None,
                product_name=cart_item["name"],
                sku=cart_item.get("sku"),
                size=inventory.size if inventory else None,
                color=inventory.color if inventory else None,
                quantity=cart_item["quantity"],
                unit_price=Decimal(cart_item["price"]),
                price=Decimal(cart_item["price"]) * cart_item["quantity"]
            )
            
            self.db.add(order_item)
            
            # Confirm inventory reservation (reduce stock + reserved_quantity)
            if cart_item.get("sku"):
                self.inventory_service.confirm_reservation(
                    cart_item["sku"],
                    cart_item["quantity"]
                )
        
        # Record promotion usage
        if promo_code:
            self.promotion_service.record_usage(
                code=promo_code,
                user_id=user_id,
                order_id=order.id
            )
        
        self.db.commit()
        self.db.refresh(order)
        
        # Clear cart
        self.cart_service.clear_cart(user_id, release_reservations=False)  # Already confirmed
        
        return order
    
    def update_order_status(
        self,
        order_id: int,
        new_status: OrderStatus,
        tracking_number: Optional[str] = None,
        admin_notes: Optional[str] = None
    ) -> Order:
        """
        Update order status with validation.
        
        Status transitions:
        PENDING → CONFIRMED, CANCELLED
        CONFIRMED → PROCESSING, CANCELLED
        PROCESSING → SHIPPED
        SHIPPED → DELIVERED
        DELIVERED → RETURNED
        CANCELLED → (terminal)
        """
        order = self.get_order_by_id(order_id)
        
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found"
            )
        
        # Validate status transition
        valid_transitions = {
            OrderStatus.PENDING: [OrderStatus.CONFIRMED, OrderStatus.CANCELLED],
            OrderStatus.CONFIRMED: [OrderStatus.PROCESSING, OrderStatus.CANCELLED],
            OrderStatus.PROCESSING: [OrderStatus.SHIPPED],
            OrderStatus.SHIPPED: [OrderStatus.DELIVERED],
            OrderStatus.DELIVERED: [OrderStatus.RETURNED],
            OrderStatus.CANCELLED: [],  # Terminal
            OrderStatus.RETURNED: [OrderStatus.REFUNDED],
            OrderStatus.REFUNDED: []  # Terminal
        }
        
        if new_status not in valid_transitions.get(order.status, []):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot transition from {order.status.value} to {new_status.value}"
            )
        
        # Update status
        order.status = new_status
        
        # Set timestamps
        if new_status == OrderStatus.SHIPPED:
            order.shipped_at = datetime.utcnow()
            if tracking_number:
                order.tracking_number = tracking_number
        elif new_status == OrderStatus.DELIVERED:
            order.delivered_at = datetime.utcnow()
        elif new_status == OrderStatus.CANCELLED:
            order.cancelled_at = datetime.utcnow()
            if admin_notes:
                order.cancellation_reason = admin_notes
        
        self.db.commit()
        self.db.refresh(order)
        
        return order
    
    def cancel_order(self, order_id: int, user_id: int, reason: Optional[str] = None) -> Order:
        """
        Cancel order and release inventory.
        Only allowed for PENDING or CONFIRMED orders.
        """
        order = self.get_order_by_id(order_id, user_id=user_id)
        
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found"
            )
        
        # Check if cancellable
        if order.status not in [OrderStatus.PENDING, OrderStatus.CONFIRMED]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot cancel order with status {order.status.value}"
            )
        
        # Release inventory back to stock
        failed_restores = []
        for item in order.items:
            if item.sku:
                # Add quantity back to inventory
                try:
                    self.inventory_service.adjust_stock(
                        item.sku,
                        item.quantity,
                        f"Order #{order_id} cancelled"
                    )
                except Exception as e:
                    failed_restores.append({"sku": item.sku, "error": str(e)})
        
        # Update order status
        order.status = OrderStatus.CANCELLED
        order.cancelled_at = datetime.utcnow()
        order.cancellation_reason = reason or "Cancelled by user"
        
        self.db.commit()
        self.db.refresh(order)
        
        return order
    
    def get_all_orders(
        self,
        status: Optional[OrderStatus] = None,
        skip: int = 0,
        limit: int = 50
    ) -> List[Order]:
        """Get all orders with optional status filter (admin)."""
        query = self.db.query(Order)
        
        if status:
            query = query.filter(Order.status == status)
        
        return query.order_by(desc(Order.created_at)).offset(skip).limit(limit).all()
