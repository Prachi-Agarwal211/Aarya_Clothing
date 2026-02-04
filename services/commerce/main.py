"""
Commerce Service - Aarya Clothing
Product Management, Cart, Orders, Inventory

This service handles:
- Product catalog management
- Shopping cart operations
- Order processing
- Inventory management
"""
from contextlib import asynccontextmanager
from datetime import datetime
from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import Optional, List
import json

from core.config import settings
from core.redis_client import redis_client
from database.database import get_db, init_db
from models.product import Product
from models.order import Order, OrderItem
from schemas.product import ProductCreate, ProductResponse, ProductUpdate
from schemas.order import OrderCreate, OrderResponse, CartItem, CartResponse


# ==================== Lifespan ====================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    init_db()
    
    if redis_client.ping():
        print("✓ Commerce service: Redis connected")
    else:
        print("✗ Commerce service: Redis connection failed")
    
    yield
    
    # Shutdown
    pass


# ==================== FastAPI App ====================

app = FastAPI(
    title="Aarya Clothing - Commerce Service",
    description="Product Management, Cart, Orders, Inventory",
    version="1.0.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==================== Health Check ====================

@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint."""
    redis_status = "healthy" if redis_client.ping() else "unhealthy"
    return {
        "status": "healthy",
        "service": "commerce",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat(),
        "dependencies": {
            "redis": redis_status,
            "database": "healthy"
        }
    }


# ==================== Product Routes ====================

@app.get("/api/v1/products", response_model=List[ProductResponse],
         tags=["Products"])
async def list_products(
    skip: int = 0,
    limit: int = 100,
    category_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """List all products with optional filtering."""
    query = db.query(Product).filter(Product.is_active == True)
    
    if category_id:
        query = query.filter(Product.category_id == category_id)
    
    products = query.offset(skip).limit(limit).all()
    return products


@app.get("/api/v1/products/{product_id}", response_model=ProductResponse,
         tags=["Products"])
async def get_product(product_id: int, db: Session = Depends(get_db)):
    """Get product by ID."""
    product = db.query(Product).filter(
        Product.id == product_id,
        Product.is_active == True
    ).first()
    
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    return product


@app.post("/api/v1/products", response_model=ProductResponse,
          status_code=status.HTTP_201_CREATED,
          tags=["Products"])
async def create_product(
    product_data: ProductCreate,
    db: Session = Depends(get_db)
):
    """Create a new product."""
    product = Product(**product_data.model_dump())
    db.add(product)
    db.commit()
    db.refresh(product)
    
    # Invalidate cache
    redis_client.invalidate_pattern("products:*")
    
    return product


@app.patch("/api/v1/products/{product_id}", response_model=ProductResponse,
          tags=["Products"])
async def update_product(
    product_id: int,
    product_data: ProductUpdate,
    db: Session = Depends(get_db)
):
    """Update a product."""
    product = db.query(Product).filter(Product.id == product_id).first()
    
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    update_data = product_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(product, field, value)
    
    product.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(product)
    
    # Invalidate cache
    redis_client.invalidate_pattern("products:*")
    
    return product


# ==================== Cart Routes ====================

@app.get("/api/v1/cart/{user_id}", response_model=CartResponse,
         tags=["Cart"])
async def get_cart(user_id: int):
    """Get user's shopping cart."""
    cart_key = f"cart:{user_id}"
    cart_data = redis_client.get_cache(cart_key)
    
    if not cart_data:
        return CartResponse(user_id=user_id, items=[], total=0)
    
    return CartResponse(**cart_data)


@app.post("/api/v1/cart/{user_id}/add", response_model=CartResponse,
          tags=["Cart"])
async def add_to_cart(
    user_id: int,
    item: CartItem,
    db: Session = Depends(get_db)
):
    """Add item to cart."""
    # Validate product exists and has inventory
    product = db.query(Product).filter(
        Product.id == item.product_id,
        Product.is_active == True
    ).first()
    
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    # Check inventory (simplified)
    if product.inventory_count < item.quantity:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Insufficient inventory"
        )
    
    # Get current cart
    cart_key = f"cart:{user_id}"
    cart_data = redis_client.get_cache(cart_key) or {
        "user_id": user_id,
        "items": [],
        "total": 0
    }
    
    # Check if item already in cart
    existing_item = next(
        (i for i in cart_data["items"] if i["product_id"] == item.product_id),
        None
    )
    
    if existing_item:
        existing_item["quantity"] += item.quantity
    else:
        cart_data["items"].append({
            "product_id": item.product_id,
            "name": product.name,
            "price": float(product.price),
            "quantity": item.quantity,
            "image_url": product.image_url
        })
    
    # Calculate total
    cart_data["total"] = sum(
        i["price"] * i["quantity"] for i in cart_data["items"]
    )
    
    # Save cart (7 days expiry)
    redis_client.set_cache(cart_key, cart_data, expires_in=168 * 60)
    
    return CartResponse(**cart_data)


@app.delete("/api/v1/cart/{user_id}/remove/{product_id}",
            response_model=CartResponse,
            tags=["Cart"])
async def remove_from_cart(user_id: int, product_id: int):
    """Remove item from cart."""
    cart_key = f"cart:{user_id}"
    cart_data = redis_client.get_cache(cart_key)
    
    if not cart_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cart not found"
        )
    
    cart_data["items"] = [
        i for i in cart_data["items"] if i["product_id"] != product_id
    ]
    
    # Recalculate total
    cart_data["total"] = sum(
        i["price"] * i["quantity"] for i in cart_data["items"]
    )
    
    redis_client.set_cache(cart_key, cart_data, expires_in=168 * 60)
    
    return CartResponse(**cart_data)


@app.delete("/api/v1/cart/{user_id}/clear", response_model=CartResponse,
           tags=["Cart"])
async def clear_cart(user_id: int):
    """Clear user's shopping cart."""
    cart_key = f"cart:{user_id}"
    redis_client.delete_cache(cart_key)
    
    return CartResponse(user_id=user_id, items=[], total=0)


# ==================== Order Routes ====================

@app.post("/api/v1/orders", response_model=OrderResponse,
          status_code=status.HTTP_201_CREATED,
          tags=["Orders"])
async def create_order(
    order_data: OrderCreate,
    db: Session = Depends(get_db)
):
    """Create a new order."""
    # Get cart
    cart_key = f"cart:{order_data.user_id}"
    cart_data = redis_client.get_cache(cart_key)
    
    if not cart_data or not cart_data["items"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cart is empty"
        )
    
    # Create order
    order = Order(
        user_id=order_data.user_id,
        total_amount=cart_data["total"],
        status="pending",
        shipping_address=order_data.shipping_address
    )
    
    db.add(order)
    db.flush()
    
    # Create order items
    for item in cart_data["items"]:
        order_item = OrderItem(
            order_id=order.id,
            product_id=item["product_id"],
            quantity=item["quantity"],
            price=item["price"]
        )
        db.add(order_item)
    
    db.commit()
    db.refresh(order)
    
    # Clear cart
    redis_client.delete_cache(cart_key)
    
    return order


@app.get("/api/v1/orders/{user_id}", response_model=List[OrderResponse],
         tags=["Orders"])
async def get_user_orders(user_id: int, db: Session = Depends(get_db)):
    """Get all orders for a user."""
    orders = db.query(Order).filter(
        Order.user_id == user_id
    ).order_by(Order.created_at.desc()).all()
    
    return orders


@app.get("/api/v1/orders/{order_id}/details", response_model=OrderResponse,
         tags=["Orders"])
async def get_order_details(order_id: int, db: Session = Depends(get_db)):
    """Get order details with items."""
    order = db.query(Order).filter(Order.id == order_id).first()
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    return order


# ==================== Run Server ====================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8010,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )
