"""Cart service with inventory reservation support."""
from typing import List, Optional, Dict
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from decimal import Decimal
import json

from core.redis_client import redis_client
from models.product import Product
from models.inventory import Inventory
from service.inventory_service import InventoryService


class CartService:
    """Service for shopping cart management with stock reservation."""
    
    CART_KEY_PREFIX = "cart:"
    RESERVATION_KEY_PREFIX = "cart:reservation:"
    RESERVATION_TTL = 900  # 15 minutes in seconds
    
    def __init__(self, db: Session):
        """Initialize cart service."""
        self.db = db
        self.inventory_service = InventoryService(db)
    
    def get_cart(self, user_id: int) -> Dict:
        """Get user's cart."""
        cart_key = f"{self.CART_KEY_PREFIX}{user_id}"
        cart_data = redis_client.get_cache(cart_key)
        
        if not cart_data:
            return {
                "user_id": user_id,
                "items": [],
                "subtotal": 0,
                "discount": 0,
                "promo_code": None,
                "total": 0
            }
        
        return cart_data
    
    def add_to_cart(
        self,
        user_id: int,
        product_id: int,
        quantity: int = 1,
        sku: Optional[str] = None
    ) -> Dict:
        """
        Add item to cart with inventory reservation.
        Reserves stock for 15 minutes.
        """
        # Validate product
        product = self.db.query(Product).filter(
            Product.id == product_id,
            Product.is_active == True
        ).first()
        
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found"
            )
        
        # Get inventory
        if sku:
            inventory = self.db.query(Inventory).filter(
                Inventory.sku == sku
            ).first()
            if not inventory:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="SKU not found"
                )
        else:
            # Get first available inventory
            inventory = self.db.query(Inventory).filter(
                Inventory.product_id == product_id
            ).first()
        
        # Check stock availability
        if inventory:
            available = inventory.quantity - inventory.reserved_quantity
            if available < quantity:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Only {available} items available"
                )
            
            # Reserve stock
            try:
                self.inventory_service.reserve_stock(inventory.sku, quantity)
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=str(e)
                )
            
            # Set reservation expiry
            reservation_key = f"{self.RESERVATION_KEY_PREFIX}{user_id}:{product_id}"
            redis_client.set_cache(
                reservation_key,
                {"sku": inventory.sku, "quantity": quantity},
                expires_in=int(self.RESERVATION_TTL / 60)  # Convert to minutes
            )
        
        # Get current cart
        cart = self.get_cart(user_id)
        
        # Check if item already in cart
        existing_item = next(
            (item for item in cart["items"] if item["product_id"] == product_id),
            None
        )
        
        if existing_item:
            existing_item["quantity"] += quantity
        else:
            cart["items"].append({
                "product_id": product_id,
                "name": product.name,
                "price": float(product.price),
                "quantity": quantity,
                "sku": inventory.sku if inventory else None,
                "image_url": product.primary_image or product.image_url
            })
        
        # Recalculate totals
        cart["subtotal"] = sum(
            item["price"] * item["quantity"] for item in cart["items"]
        )
        cart["total"] = cart["subtotal"] - cart.get("discount", 0)
        
        # Save cart
        cart_key = f"{self.CART_KEY_PREFIX}{user_id}"
        redis_client.set_cache(cart_key, cart, expires_in=7 * 24 * 60)  # 7 days
        
        return cart
    
    def update_quantity(
        self,
        user_id: int,
        product_id: int,
        new_quantity: int
    ) -> Dict:
        """Update item quantity in cart."""
        cart = self.get_cart(user_id)
        
        item = next(
            (item for item in cart["items"] if item["product_id"] == product_id),
            None
        )
        
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Item not in cart"
            )
        
        old_quantity = item["quantity"]
        quantity_diff = new_quantity - old_quantity
        
        # Update reservation if needed
        if item.get("sku") and quantity_diff != 0:
            try:
                if quantity_diff > 0:
                    self.inventory_service.reserve_stock(item["sku"], quantity_diff)
                else:
                    self.inventory_service.release_stock(item["sku"], abs(quantity_diff))
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=str(e)
                )
        
        item["quantity"] = new_quantity
        
        # Recalculate
        cart["subtotal"] = sum(
            item["price"] * item["quantity"] for item in cart["items"]
        )
        cart["total"] = cart["subtotal"] - cart.get("discount", 0)
        
        # Save
        cart_key = f"{self.CART_KEY_PREFIX}{user_id}"
        redis_client.set_cache(cart_key, cart, expires_in=7 * 24 * 60)
        
        return cart
    
    def remove_from_cart(self, user_id: int, product_id: int) -> Dict:
        """Remove item from cart and release reservation."""
        cart = self.get_cart(user_id)
        
        item = next(
            (item for item in cart["items"] if item["product_id"] == product_id),
            None
        )
        
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Item not in cart"
            )
        
        # Release reservation
        if item.get("sku"):
            try:
                self.inventory_service.release_stock(item["sku"], item["quantity"])
            except:
                pass  # Best effort release
        
        # Remove reservation key
        reservation_key = f"{self.RESERVATION_KEY_PREFIX}{user_id}:{product_id}"
        redis_client.delete_cache(reservation_key)
        
        # Remove from cart
        cart["items"] = [
            i for i in cart["items"]if i["product_id"] != product_id
        ]
        
        # Recalculate
        cart["subtotal"] = sum(
            item["price"] * item["quantity"] for item in cart["items"]
        )
        cart["total"] = cart["subtotal"] - cart.get("discount", 0)
        
        # Save
        cart_key = f"{self.CART_KEY_PREFIX}{user_id}"
        redis_client.set_cache(cart_key, cart, expires_in=7 * 24 * 60)
        
        return cart
    
    def clear_cart(self, user_id: int, release_reservations: bool = True) -> Dict:
        """Clear cart and optionally release all reservations."""
        if release_reservations:
            cart = self.get_cart(user_id)
            
            # Release all reservations
            for item in cart["items"]:
                if item.get("sku"):
                    try:
                        self.inventory_service.release_stock(item["sku"], item["quantity"])
                    except:
                        pass
        
        # Delete cart
        cart_key = f"{self.CART_KEY_PREFIX}{user_id}"
        redis_client.delete_cache(cart_key)
        
        return {
            "user_id": user_id,
            "items": [],
            "subtotal": 0,
            "discount": 0,
            "promo_code": None,
            "total": 0
        }
    
    def apply_promotion(self, user_id: int, promo_code: str, discount_amount: Decimal) -> Dict:
        """Apply promotion code to cart."""
        cart = self.get_cart(user_id)
        
        cart["promo_code"] = promo_code
        cart["discount"] = float(discount_amount)
        cart["total"] = max(0, cart["subtotal"] - cart["discount"])
        
        # Save
        cart_key = f"{self.CART_KEY_PREFIX}{user_id}"
        redis_client.set_cache(cart_key, cart, expires_in=7 * 24 * 60)
        
        return cart
    
    def confirm_cart_for_checkout(self, user_id: int) -> bool:
        """
        Validate cart and confirm all reservations are still valid.
        Should be called during checkout.
        """
        cart = self.get_cart(user_id)
        
        for item in cart["items"]:
            if item.get("sku"):
                # Check reservation still valid
                reservation_key = f"{self.RESERVATION_KEY_PREFIX}{user_id}:{item['product_id']}"
                reservation = redis_client.get_cache(reservation_key)
                
                if not reservation:
                    # Reservation expired, try to re-reserve
                    try:
                        self.inventory_service.reserve_stock(item["sku"], item["quantity"])
                        redis_client.set_cache(
                            reservation_key,
                            {"sku": item["sku"], "quantity": item["quantity"]},
                            expires_in=int(self.RESERVATION_TTL / 60)
                        )
                    except:
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Product '{item['name']}' is no longer available"
                        )
        
        return True
