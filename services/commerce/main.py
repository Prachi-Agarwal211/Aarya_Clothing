"""
Commerce Service - Aarya Clothing
Product Management, Categories, Cart, Orders, Inventory

This service handles:
- Product catalog management
- Category hierarchy management
- Shopping cart operations
- Order processing
- Inventory management
- Image uploads to Cloudflare R2
- Wishlist management
- Promotions/Coupons
- Reviews and ratings
- Address management
- Returns and refunds
"""
from contextlib import asynccontextmanager
from datetime import datetime
from fastapi import FastAPI, Depends, HTTPException, status, Request, UploadFile, File, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import Optional, List
from decimal import Decimal
import json

from core.config import settings
from core.redis_client import redis_client
from database.database import get_db, init_db

# Models
from models.product import Product
from models.category import Category
from models.product_image import ProductImage
from models.inventory import Inventory
from models.order import Order, OrderItem, OrderStatus
from models.address import Address, AddressType
from models.review import Review
from models.order_tracking import OrderTracking
from models.return_request import ReturnRequest, ReturnStatus, ReturnReason

# Schemas
from schemas.product import ProductCreate, ProductResponse, ProductUpdate, ProductDetailResponse
from schemas.category import CategoryCreate, CategoryUpdate, CategoryResponse, CategoryWithChildren, CategoryTree
from schemas.product_image import ProductImageCreate, ProductImageResponse
from schemas.inventory import InventoryCreate, InventoryUpdate, InventoryResponse, StockAdjustment, LowStockItem
from schemas.order import OrderCreate, OrderResponse, CartItem, CartResponse
from schemas.wishlist import WishlistItemCreate, WishlistItemResponse, WishlistResponse
from schemas.promotion import PromotionCreate, PromotionUpdate, PromotionResponse, PromotionValidateRequest, PromotionValidateResponse
from schemas.address import AddressCreate, AddressUpdate, AddressResponse
from schemas.review import ReviewCreate, ReviewResponse
from schemas.order_tracking import OrderTrackingCreate, OrderTrackingResponse
from schemas.return_request import ReturnRequestCreate, ReturnRequestUpdate, ReturnRequestResponse
from schemas.error import ErrorResponse, PaginatedResponse

# Services
from service.category_service import CategoryService
from service.inventory_service import InventoryService
from service.r2_service import r2_service
from service.wishlist_service import WishlistService
from service.promotion_service import PromotionService
from service.product_service import ProductService
from service.cart_service import CartService
from service.order_service import OrderService
from service.address_service import AddressService
from service.review_service import ReviewService
from service.order_tracking_service import OrderTrackingService
from service.return_service import ReturnService

# Middleware
from middleware.auth_middleware import (
    get_current_user,
    get_current_user_optional,
    require_admin,
    require_staff
)



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
    description="Product Management, Categories, Cart, Orders, Inventory",
    version="2.0.0",
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
        "version": "2.0.0",
        "timestamp": datetime.utcnow().isoformat(),
        "dependencies": {
            "redis": redis_status,
            "database": "healthy"
        }
    }


# ==================== Category Routes ====================

@app.get("/api/v1/categories", response_model=List[CategoryResponse],
         tags=["Categories"])
async def list_categories(
    parent_id: Optional[int] = None,
    featured_only: bool = False,
    db: Session = Depends(get_db)
):
    """List categories with optional filtering."""
    category_service = CategoryService(db)
    
    if featured_only:
        categories = db.query(Category).filter(
            Category.is_featured == True,
            Category.is_active == True
        ).order_by(Category.display_order).all()
    elif parent_id is not None:
        categories = category_service.get_category_tree(parent_id)
    else:
        categories = category_service.get_all_categories()
    
    return categories


@app.get("/api/v1/categories/tree", response_model=CategoryTree,
         tags=["Categories"])
async def get_category_tree(db: Session = Depends(get_db)):
    """Get full category tree structure."""
    category_service = CategoryService(db)
    root_categories = category_service.get_root_categories()
    
    return CategoryTree(categories=root_categories)


@app.get("/api/v1/categories/{category_id}", response_model=CategoryWithChildren,
         tags=["Categories"])
async def get_category(category_id: int, db: Session = Depends(get_db)):
    """Get category by ID with children."""
    category_service = CategoryService(db)
    category = category_service.get_category_by_id(category_id)
    
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )
    
    return category


@app.get("/api/v1/categories/slug/{slug}", response_model=CategoryWithChildren,
         tags=["Categories"])
async def get_category_by_slug(slug: str, db: Session = Depends(get_db)):
    """Get category by slug with children."""
    category_service = CategoryService(db)
    category = category_service.get_category_by_slug(slug)
    
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )
    
    return category


# ==================== Admin Category Routes ====================

@app.post("/api/v1/admin/categories", response_model=CategoryResponse,
          status_code=status.HTTP_201_CREATED,
          tags=["Admin - Categories"])
async def create_category(
    category_data: CategoryCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin)
):
    """Create a new category (admin only)."""
    category_service = CategoryService(db)
    return category_service.create_category(category_data)


@app.patch("/api/v1/admin/categories/{category_id}", response_model=CategoryResponse,
           tags=["Admin - Categories"])
async def update_category(
    category_id: int,
    category_data: CategoryUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin)
):
    """Update a category (admin only)."""
    category_service = CategoryService(db)
    return category_service.update_category(category_id, category_data)


@app.delete("/api/v1/admin/categories/{category_id}",
            status_code=status.HTTP_204_NO_CONTENT,
            tags=["Admin - Categories"])
async def delete_category(
    category_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin)
):
    """Delete a category (admin only)."""
    category_service = CategoryService(db)
    category_service.delete_category(category_id)
    return


# ==================== Product Routes ====================

@app.get("/api/v1/products", response_model=List[ProductResponse],
         tags=["Products"])
async def list_products(
    skip: int = 0,
    limit: int = 100,
    category_id: Optional[int] = None,
    new_arrivals: bool = False,
    featured: bool = False,
    db: Session = Depends(get_db)
):
    """List all products with optional filtering."""
    query = db.query(Product).filter(Product.is_active == True)
    
    if category_id:
        query = query.filter(Product.category_id == category_id)
    
    if new_arrivals:
        query = query.filter(Product.is_new_arrival == True)
    
    if featured:
        query = query.filter(Product.is_featured == True)
    
    products = query.offset(skip).limit(limit).all()
    return products


@app.get("/api/v1/products/new-arrivals", response_model=List[ProductResponse],
         tags=["Products"])
async def get_new_arrivals(
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """Get new arrival products."""
    products = db.query(Product).filter(
        Product.is_new_arrival == True,
        Product.is_active == True
    ).order_by(Product.created_at.desc()).limit(limit).all()
    
    return products


@app.get("/api/v1/products/{product_id}", response_model=ProductDetailResponse,
         tags=["Products"])
async def get_product(product_id: int, db: Session = Depends(get_db)):
    """Get product by ID with full details."""
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


# ==================== Admin Product Routes ====================

@app.post("/api/v1/admin/products", response_model=ProductResponse,
          status_code=status.HTTP_201_CREATED,
          tags=["Admin - Products"])
async def create_product(
    product_data: ProductCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin)
):
    """Create a new product (admin only)."""
    product_service = ProductService(db)
    product = product_service.create_product(product_data)
    
    # Invalidate cache
    redis_client.invalidate_pattern("products:*")
    
    return product


@app.patch("/api/v1/admin/products/{product_id}", response_model=ProductResponse,
          tags=["Admin - Products"])
async def update_product(
    product_id: int,
    product_data: ProductUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin)
):
    """Update a product (admin only)."""
    product_service = ProductService(db)
    product = product_service.update_product(product_id, product_data)
    
    # Invalidate cache
    redis_client.invalidate_pattern("products:*")
    
    return product


# ==================== Product Image Routes ====================

@app.post("/api/v1/admin/products/{product_id}/images",
          response_model=ProductImageResponse,
          status_code=status.HTTP_201_CREATED,
          tags=["Admin - Product Images"])
async def upload_product_image(
    product_id: int,
    file: UploadFile = File(...),
    alt_text: Optional[str] = None,
    is_primary: bool = False,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin)
):
    """Upload product image (admin only)."""
    # Validate product exists
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    # Upload to R2
    image_url = await r2_service.upload_image(file, folder="products")
    
    # Create image record
    image = ProductImage(
        product_id=product_id,
        image_url=image_url,
        alt_text=alt_text or product.name,
        is_primary=is_primary,
        display_order=len(product.images)
    )
    
    # If this is the primary image, unset others
    if is_primary:
        db.query(ProductImage).filter(
            ProductImage.product_id == product_id
        ).update({ProductImage.is_primary: False})
    
    db.add(image)
    db.commit()
    db.refresh(image)
    
    return image


@app.delete("/api/v1/admin/products/{product_id}/images/{image_id}",
            status_code=status.HTTP_204_NO_CONTENT,
            tags=["Admin - Product Images"])
async def delete_product_image(
    product_id: int,
    image_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin)
):
    """Delete product image (admin only)."""
    image = db.query(ProductImage).filter(
        ProductImage.id == image_id,
        ProductImage.product_id == product_id
    ).first()
    
    if not image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Image not found"
        )
    
    # Delete from R2
    await r2_service.delete_image(image.image_url)
    
    # Delete from database
    db.delete(image)
    db.commit()
    
    return


# ==================== Inventory Routes ====================

@app.get("/api/v1/admin/inventory", response_model=List[InventoryResponse],
         tags=["Admin - Inventory"])
async def list_inventory(
    product_id: Optional[int] = None,
    low_stock_only: bool = False,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_staff)
):
    """List inventory (admin/staff only)."""
    query = db.query(Inventory)
    
    if product_id:
        query = query.filter(Inventory.product_id == product_id)
    
    if low_stock_only:
        query = query.filter(
            Inventory.quantity - Inventory.reserved_quantity <= Inventory.low_stock_threshold
        )
    
    inventory_items = query.all()
    return inventory_items


@app.post("/api/v1/admin/inventory", response_model=InventoryResponse,
          status_code=status.HTTP_201_CREATED,
          tags=["Admin - Inventory"])
async def create_inventory(
    inventory_data: InventoryCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_staff)
):
    """Create inventory record (admin/staff only)."""
    inventory_service = InventoryService(db)
    return inventory_service.create_inventory(inventory_data)


@app.patch("/api/v1/admin/inventory/{inventory_id}", response_model=InventoryResponse,
           tags=["Admin - Inventory"])
async def update_inventory(
    inventory_id: int,
    inventory_data: InventoryUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_staff)
):
    """Update inventory (admin/staff only)."""
    inventory_service = InventoryService(db)
    return inventory_service.update_inventory(inventory_id, inventory_data)


@app.post("/api/v1/admin/inventory/adjust", response_model=InventoryResponse,
          tags=["Admin - Inventory"])
async def adjust_stock(
    adjustment_data: StockAdjustment,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_staff)
):
    """Adjust stock quantity (admin/staff only)."""
    inventory_service = InventoryService(db)
    return inventory_service.adjust_stock(
        adjustment_data.sku,
        adjustment_data.adjustment,
        adjustment_data.reason
    )


@app.get("/api/v1/admin/inventory/low-stock", response_model=List[LowStockItem],
         tags=["Admin - Inventory"])
async def get_low_stock_items(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_staff)
):
    """Get low stock alerts (admin/staff only)."""
    inventory_service = InventoryService(db)
    return inventory_service.get_low_stock_items()


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
    
    # Check inventory (simplified - check total stock)
    if product.total_stock < item.quantity:
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
            "image_url": product.primary_image or product.image_url
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


# ==================== Wishlist Routes ====================

@app.get("/api/v1/wishlist/{user_id}", response_model=WishlistResponse,
         tags=["Wishlist"])
async def get_wishlist(user_id: int, db: Session = Depends(get_db)):
    """Get user's wishlist."""
    wishlist_service = WishlistService(db)
    items = wishlist_service.get_user_wishlist(user_id)
    
    return WishlistResponse(
        user_id=user_id,
        items=items,
        total_items=len(items)
    )


@app.post("/api/v1/wishlist/{user_id}/add", response_model=WishlistItemResponse,
          status_code=status.HTTP_201_CREATED,
          tags=["Wishlist"])
async def add_to_wishlist(
    user_id: int,
    item: WishlistItemCreate,
    db: Session = Depends(get_db)
):
    """Add product to wishlist."""
    wishlist_service = WishlistService(db)
    return wishlist_service.add_to_wishlist(user_id, item.product_id)


@app.delete("/api/v1/wishlist/{user_id}/remove/{product_id}",
            status_code=status.HTTP_204_NO_CONTENT,
            tags=["Wishlist"])
async def remove_from_wishlist(
    user_id: int,
    product_id: int,
    db: Session = Depends(get_db)
):
    """Remove product from wishlist."""
    wishlist_service = WishlistService(db)
    wishlist_service.remove_from_wishlist(user_id, product_id)
    return


@app.delete("/api/v1/wishlist/{user_id}/clear",
            status_code=status.HTTP_204_NO_CONTENT,
            tags=["Wishlist"])
async def clear_wishlist(user_id: int, db: Session = Depends(get_db)):
    """Clear user's wishlist."""
    wishlist_service = WishlistService(db)
    wishlist_service.clear_wishlist(user_id)
    return


@app.get("/api/v1/wishlist/{user_id}/check/{product_id}",
         tags=["Wishlist"])
async def check_in_wishlist(
    user_id: int,
    product_id: int,
    db: Session = Depends(get_db)
):
    """Check if product is in wishlist."""
    wishlist_service = WishlistService(db)
    in_wishlist = wishlist_service.is_in_wishlist(user_id, product_id)
    return {"in_wishlist": in_wishlist}


# ==================== Promotion Routes ====================

@app.post("/api/v1/promotions/validate", response_model=PromotionValidateResponse,
          tags=["Promotions"])
async def validate_promotion(
    validation_request: PromotionValidateRequest,
    db: Session = Depends(get_db)
):
    """Validate a promotion code."""
    promotion_service = PromotionService(db)
    result = promotion_service.validate_promotion(
        validation_request.code,
        validation_request.user_id,
        validation_request.order_total
    )
    
    return PromotionValidateResponse(**result)


# ==================== Admin Promotion Routes ====================

@app.get("/api/v1/admin/promotions", response_model=List[PromotionResponse],
         tags=["Admin - Promotions"])
async def list_promotions(
    active_only: bool = False,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin)
):
    """List all promotions (admin only)."""
    promotion_service = PromotionService(db)
    return promotion_service.get_all_promotions(active_only)


@app.get("/api/v1/admin/promotions/{code}", response_model=PromotionResponse,
         tags=["Admin - Promotions"])
async def get_promotion(
    code: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin)
):
    """Get promotion by code (admin only)."""
    promotion_service = PromotionService(db)
    promotion = promotion_service.get_promotion_by_code(code)
    
    if not promotion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Promotion not found"
        )
    
    return promotion


@app.post("/api/v1/admin/promotions", response_model=PromotionResponse,
          status_code=status.HTTP_201_CREATED,
          tags=["Admin - Promotions"])
async def create_promotion(
    promotion_data: PromotionCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin)
):
    """Create a new promotion (admin only)."""
    promotion_service = PromotionService(db)
    return promotion_service.create_promotion(promotion_data)


@app.patch("/api/v1/admin/promotions/{promotion_id}", response_model=PromotionResponse,
           tags=["Admin - Promotions"])
async def update_promotion(
    promotion_id: int,
    promotion_data: PromotionUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin)
):
    """Update a promotion (admin only)."""
    promotion_service = PromotionService(db)
    return promotion_service.update_promotion(promotion_id, promotion_data)


@app.delete("/api/v1/admin/promotions/{promotion_id}",
            status_code=status.HTTP_204_NO_CONTENT,
            tags=["Admin - Promotions"])
async def delete_promotion(
    promotion_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin)
):
    """Delete a promotion (admin only)."""
    promotion_service = PromotionService(db)
    promotion_service.delete_promotion(promotion_id)
    return


# ==================== Product Search ====================

@app.get("/api/v1/products/search", response_model=List[ProductResponse],
         tags=["Products"])
async def search_products(
    q: str = Query(..., min_length=1, description="Search query"),
    category_id: Optional[int] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Search products by name, description, or SKU."""
    product_service = ProductService(db)
    return product_service.search_products(
        query=q,
        category_id=category_id,
        min_price=min_price,
        max_price=max_price,
        skip=skip,
        limit=limit
    )


# ==================== Order Routes ====================

@app.post("/api/v1/orders", response_model=OrderResponse,
          status_code=status.HTTP_201_CREATED,
          tags=["Orders"])
async def create_order(
    order_data: OrderCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create a new order from cart."""
    order_service = OrderService(db)
    return order_service.create_order(
        user_id=current_user["user_id"],
        shipping_address=order_data.shipping_address,
        promo_code=order_data.promo_code,
        order_notes=order_data.notes
    )


@app.get("/api/v1/orders", response_model=List[OrderResponse],
         tags=["Orders"])
async def list_orders(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """List current user's orders."""
    order_service = OrderService(db)
    return order_service.get_user_orders(
        user_id=current_user["user_id"],
        skip=skip,
        limit=limit
    )


@app.get("/api/v1/orders/{order_id}", response_model=OrderResponse,
         tags=["Orders"])
async def get_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get order details."""
    order_service = OrderService(db)
    order = order_service.get_order_by_id(order_id, user_id=current_user["user_id"])
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    return order


@app.post("/api/v1/orders/{order_id}/cancel", response_model=OrderResponse,
          tags=["Orders"])
async def cancel_order(
    order_id: int,
    reason: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Cancel an order."""
    order_service = OrderService(db)
    return order_service.cancel_order(
        order_id=order_id,
        user_id=current_user["user_id"],
        reason=reason
    )


@app.get("/api/v1/orders/{order_id}/tracking", response_model=List[OrderTrackingResponse],
         tags=["Orders"])
async def get_order_tracking(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get order tracking history."""
    # Verify order belongs to user
    order_service = OrderService(db)
    order = order_service.get_order_by_id(order_id, user_id=current_user["user_id"])
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    tracking_service = OrderTrackingService(db)
    return tracking_service.get_order_tracking(order_id)


# ==================== Admin Order Routes ====================

@app.get("/api/v1/admin/orders", response_model=List[OrderResponse],
         tags=["Admin - Orders"])
async def list_all_orders(
    status_filter: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_staff)
):
    """List all orders (admin/staff)."""
    order_service = OrderService(db)
    order_status = OrderStatus(status_filter) if status_filter else None
    return order_service.get_all_orders(status=order_status, skip=skip, limit=limit)


@app.patch("/api/v1/admin/orders/{order_id}/status", response_model=OrderResponse,
           tags=["Admin - Orders"])
async def update_order_status(
    order_id: int,
    new_status: str,
    tracking_number: Optional[str] = None,
    notes: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_staff)
):
    """Update order status (admin/staff)."""
    order_service = OrderService(db)
    order = order_service.update_order_status(
        order_id=order_id,
        new_status=OrderStatus(new_status),
        tracking_number=tracking_number,
        admin_notes=notes
    )
    
    # Add tracking entry
    tracking_service = OrderTrackingService(db)
    tracking_service.add_tracking_entry(
        order_id=order_id,
        status=OrderStatus(new_status),
        notes=notes,
        updated_by=current_user["user_id"]
    )
    
    return order


# ==================== Address Routes ====================

@app.post("/api/v1/addresses", response_model=AddressResponse,
          status_code=status.HTTP_201_CREATED,
          tags=["Addresses"])
async def create_address(
    address_data: AddressCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create a new address."""
    address_service = AddressService(db)
    return address_service.create_address(current_user["user_id"], address_data)


@app.get("/api/v1/addresses", response_model=List[AddressResponse],
         tags=["Addresses"])
async def list_addresses(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """List current user's addresses."""
    address_service = AddressService(db)
    return address_service.get_user_addresses(current_user["user_id"])


@app.get("/api/v1/addresses/{address_id}", response_model=AddressResponse,
         tags=["Addresses"])
async def get_address(
    address_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get address by ID."""
    address_service = AddressService(db)
    address = address_service.get_address_by_id(address_id, current_user["user_id"])
    
    if not address:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Address not found"
        )
    
    return address


@app.patch("/api/v1/addresses/{address_id}", response_model=AddressResponse,
           tags=["Addresses"])
async def update_address(
    address_id: int,
    address_data: AddressUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Update an address."""
    address_service = AddressService(db)
    return address_service.update_address(
        address_id,
        current_user["user_id"],
        address_data
    )


@app.delete("/api/v1/addresses/{address_id}",
            status_code=status.HTTP_204_NO_CONTENT,
            tags=["Addresses"])
async def delete_address(
    address_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Delete an address."""
    address_service = AddressService(db)
    address_service.delete_address(address_id, current_user["user_id"])
    return


# ==================== Review Routes ====================

@app.post("/api/v1/reviews", response_model=ReviewResponse,
          status_code=status.HTTP_201_CREATED,
          tags=["Reviews"])
async def create_review(
    review_data: ReviewCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create a product review."""
    review_service = ReviewService(db)
    return review_service.create_review(current_user["user_id"], review_data)


@app.get("/api/v1/products/{product_id}/reviews", response_model=List[ReviewResponse],
         tags=["Reviews"])
async def get_product_reviews(
    product_id: int,
    approved_only: bool = True,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Get reviews for a product."""
    review_service = ReviewService(db)
    return review_service.get_product_reviews(
        product_id,
        approved_only=approved_only,
        skip=skip,
        limit=limit
    )


@app.post("/api/v1/reviews/{review_id}/helpful",
          tags=["Reviews"])
async def mark_review_helpful(
    review_id: int,
    db: Session = Depends(get_db)
):
    """Mark a review as helpful."""
    review_service = ReviewService(db)
    review_service.mark_helpful(review_id)
    return {"message": "Review marked as helpful"}


@app.delete("/api/v1/reviews/{review_id}",
            status_code=status.HTTP_204_NO_CONTENT,
            tags=["Reviews"])
async def delete_review(
    review_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Delete own review."""
    review_service = ReviewService(db)
    review_service.delete_review(review_id, current_user["user_id"])
    return


@app.post("/api/v1/admin/reviews/{review_id}/approve",
          response_model=ReviewResponse,
          tags=["Admin - Reviews"])
async def approve_review(
    review_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_staff)
):
    """Approve a review (admin/staff)."""
    review_service = ReviewService(db)
    return review_service.approve_review(review_id)


# ==================== Return Routes ====================

@app.post("/api/v1/returns", response_model=ReturnRequestResponse,
          status_code=status.HTTP_201_CREATED,
          tags=["Returns"])
async def create_return_request(
    return_data: ReturnRequestCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create a return request."""
    return_service = ReturnService(db)
    return return_service.create_return(current_user["user_id"], return_data)


@app.get("/api/v1/returns", response_model=List[ReturnRequestResponse],
         tags=["Returns"])
async def list_returns(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """List current user's return requests."""
    return_service = ReturnService(db)
    return return_service.get_user_returns(
        current_user["user_id"],
        skip=skip,
        limit=limit
    )


@app.get("/api/v1/returns/{return_id}", response_model=ReturnRequestResponse,
         tags=["Returns"])
async def get_return(
    return_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get return request details."""
    return_service = ReturnService(db)
    return_request = return_service.get_return_by_id(
        return_id,
        user_id=current_user["user_id"]
    )
    
    if not return_request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Return request not found"
        )
    
    return return_request


# ==================== Admin Return Routes ====================

@app.get("/api/v1/admin/returns", response_model=List[ReturnRequestResponse],
         tags=["Admin - Returns"])
async def list_all_returns(
    status_filter: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_staff)
):
    """List all return requests (admin/staff)."""
    return_service = ReturnService(db)
    return_status = ReturnStatus(status_filter) if status_filter else None
    return return_service.get_all_returns(status=return_status, skip=skip, limit=limit)


@app.post("/api/v1/admin/returns/{return_id}/approve",
          response_model=ReturnRequestResponse,
          tags=["Admin - Returns"])
async def approve_return(
    return_id: int,
    refund_amount: Optional[float] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_staff)
):
    """Approve a return request (admin/staff)."""
    return_service = ReturnService(db)
    return return_service.approve_return(
        return_id,
        approved_by=current_user["user_id"],
        refund_amount=Decimal(refund_amount) if refund_amount else None
    )


@app.post("/api/v1/admin/returns/{return_id}/reject",
          response_model=ReturnRequestResponse,
          tags=["Admin - Returns"])
async def reject_return(
    return_id: int,
    reason: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_staff)
):
    """Reject a return request (admin/staff)."""
    return_service = ReturnService(db)
    return return_service.reject_return(
        return_id,
        approved_by=current_user["user_id"],
        rejection_reason=reason
    )


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

