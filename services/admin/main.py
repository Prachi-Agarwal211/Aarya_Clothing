"""Aarya Clothing — Admin & Staff Service (Port 8004)."""
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import FastAPI, Depends, HTTPException, status, Query, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, text, case

from core.config import settings
from core.redis_client import redis_client
from database.database import get_db, init_db, Base, engine
from middleware.auth_middleware import require_admin, require_staff, get_current_user
from models.chat import ChatRoom, ChatMessage, ChatStatus, SenderType
from models.landing_config import LandingConfig, LandingImage
from models.analytics import AnalyticsCache, InventoryMovement, StaffTask, StaffNotification
from service.r2_service import r2_service
from schemas.admin import (
    DashboardOverview, InventoryAlert, RevenueAnalytics, RevenueData,
    CustomerAnalytics, TopProduct, TopProductsAnalytics,
    OrderStatusUpdate, BulkOrderUpdate, OrderResponse,
    AddStockRequest, AdjustStockRequest, BulkInventoryUpdate,
    VariantCreate, VariantUpdate, InventoryMovementResponse,
    StaffDashboard, OrderProcessRequest, OrderShipRequest,
    ReservationRelease, TaskComplete,
    UserListItem, UserStatusUpdate,
    ChatRoomCreate, ChatMessageCreate, ChatRoomResponse, ChatMessageResponse,
    LandingConfigUpdate, LandingConfigResponse,
    LandingImageCreate, LandingImageResponse,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    print(f"Starting {settings.SERVICE_NAME}...")
    init_db()
    if redis_client.ping():
        print("Redis connected")
    else:
        print("WARNING: Redis not available")
    yield
    print(f"Shutting down {settings.SERVICE_NAME}...")


app = FastAPI(
    title="Aarya Clothing - Admin & Staff Service",
    description="Dashboard, Analytics, Order/Inventory Management, Chat, Landing Config",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==================== Health ====================

@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "healthy", "service": settings.SERVICE_NAME}


# ==================== Admin Dashboard ====================

@app.get("/api/v1/admin/dashboard/overview", response_model=DashboardOverview, tags=["Admin Dashboard"])
async def get_dashboard_overview(db: Session = Depends(get_db), user: dict = Depends(require_admin)):
    """Aggregate dashboard stats: revenue, orders, customers, inventory alerts."""
    cache_key = "admin:dashboard:overview"
    cached = redis_client.get_cache(cache_key)
    if cached:
        return cached

    total_revenue = db.execute(text("SELECT COALESCE(SUM(total_amount), 0) FROM orders WHERE status NOT IN ('cancelled', 'refunded')")).scalar() or 0
    total_orders = db.execute(text("SELECT COUNT(*) FROM orders")).scalar() or 0
    total_customers = db.execute(text("SELECT COUNT(*) FROM users WHERE role = 'customer'")).scalar() or 0
    total_products = db.execute(text("SELECT COUNT(*) FROM products WHERE is_active = true")).scalar() or 0
    pending_orders = db.execute(text("SELECT COUNT(*) FROM orders WHERE status = 'pending'")).scalar() or 0

    today = datetime.utcnow().date()
    today_revenue = db.execute(text("SELECT COALESCE(SUM(total_amount), 0) FROM orders WHERE DATE(created_at) = :today AND status NOT IN ('cancelled', 'refunded')"), {"today": today}).scalar() or 0
    today_orders = db.execute(text("SELECT COUNT(*) FROM orders WHERE DATE(created_at) = :today"), {"today": today}).scalar() or 0

    low_stock = db.execute(text("SELECT COUNT(*) FROM inventory WHERE quantity <= low_stock_threshold AND quantity > 0")).scalar() or 0
    out_of_stock = db.execute(text("SELECT COUNT(*) FROM inventory WHERE quantity = 0")).scalar() or 0

    recent = db.execute(text("SELECT id, user_id, total_amount, status, created_at FROM orders ORDER BY created_at DESC LIMIT 5")).fetchall()
    recent_orders = [{"id": r[0], "user_id": r[1], "total_amount": float(r[2]), "status": r[3], "created_at": str(r[4])} for r in recent]

    result = DashboardOverview(
        total_revenue=float(total_revenue), total_orders=total_orders,
        total_customers=total_customers, total_products=total_products,
        pending_orders=pending_orders, today_revenue=float(today_revenue),
        today_orders=today_orders,
        inventory_alerts=InventoryAlert(low_stock=low_stock, out_of_stock=out_of_stock),
        recent_orders=recent_orders,
    )
    redis_client.set_cache(cache_key, result.model_dump(), ttl=120)
    return result


# ==================== Analytics ====================

@app.get("/api/v1/admin/analytics/revenue", response_model=RevenueAnalytics, tags=["Analytics"])
async def get_revenue_analytics(
    period: str = Query("30d", regex="^(7d|30d|90d|1y)$"),
    db: Session = Depends(get_db), user: dict = Depends(require_admin),
):
    days = {"7d": 7, "30d": 30, "90d": 90, "1y": 365}[period]
    since = datetime.utcnow() - timedelta(days=days)
    rows = db.execute(text(
        "SELECT DATE(created_at) as day, COALESCE(SUM(total_amount),0), COUNT(*) "
        "FROM orders WHERE created_at >= :since AND status NOT IN ('cancelled','refunded') "
        "GROUP BY DATE(created_at) ORDER BY day"
    ), {"since": since}).fetchall()
    period_data = [RevenueData(period=str(r[0]), revenue=float(r[1]), orders=r[2]) for r in rows]
    total = sum(d.revenue for d in period_data)
    return RevenueAnalytics(total_revenue=total, period_data=period_data)


@app.get("/api/v1/admin/analytics/customers", response_model=CustomerAnalytics, tags=["Analytics"])
async def get_customer_analytics(db: Session = Depends(get_db), user: dict = Depends(require_admin)):
    now = datetime.utcnow()
    total = db.execute(text("SELECT COUNT(*) FROM users WHERE role = 'customer'")).scalar() or 0
    today = db.execute(text("SELECT COUNT(*) FROM users WHERE role='customer' AND DATE(created_at)=:d"), {"d": now.date()}).scalar() or 0
    week = db.execute(text("SELECT COUNT(*) FROM users WHERE role='customer' AND created_at >= :d"), {"d": now - timedelta(days=7)}).scalar() or 0
    month = db.execute(text("SELECT COUNT(*) FROM users WHERE role='customer' AND created_at >= :d"), {"d": now - timedelta(days=30)}).scalar() or 0
    returning = db.execute(text("SELECT COUNT(DISTINCT user_id) FROM orders GROUP BY user_id HAVING COUNT(*) > 1")).scalar() or 0
    return CustomerAnalytics(total_customers=total, new_customers_today=today, new_customers_this_week=week, new_customers_this_month=month, returning_customers=returning)


@app.get("/api/v1/admin/analytics/products/top-selling", response_model=TopProductsAnalytics, tags=["Analytics"])
async def get_top_products(
    period: str = Query("30d"), limit: int = Query(10, le=50),
    db: Session = Depends(get_db), user: dict = Depends(require_admin),
):
    days = {"7d": 7, "30d": 30, "90d": 90, "1y": 365}.get(period, 30)
    since = datetime.utcnow() - timedelta(days=days)
    rows = db.execute(text(
        "SELECT oi.product_id, COALESCE(p.name,'Unknown'), SUM(oi.quantity), SUM(oi.price) "
        "FROM order_items oi LEFT JOIN products p ON p.id=oi.product_id "
        "JOIN orders o ON o.id=oi.order_id "
        "WHERE o.created_at >= :since AND o.status NOT IN ('cancelled','refunded') "
        "GROUP BY oi.product_id, p.name ORDER BY SUM(oi.quantity) DESC LIMIT :lim"
    ), {"since": since, "lim": limit}).fetchall()
    products = [TopProduct(product_id=r[0], product_name=r[1], total_sold=r[2], total_revenue=float(r[3])) for r in rows]
    return TopProductsAnalytics(top_products=products, period=period)


# ==================== Order Management (Admin) ====================

@app.get("/api/v1/admin/orders", tags=["Admin Orders"])
async def list_orders(
    status: Optional[str] = None, page: int = Query(1, ge=1), limit: int = Query(20, le=100),
    db: Session = Depends(get_db), user: dict = Depends(require_admin),
):
    offset = (page - 1) * limit
    where = "WHERE status = :status" if status else ""
    params = {"lim": limit, "off": offset}
    if status:
        params["status"] = status
    total = db.execute(text(f"SELECT COUNT(*) FROM orders {where}"), params).scalar()
    rows = db.execute(text(f"SELECT id, user_id, subtotal, discount_applied, shipping_cost, total_amount, status, shipping_address, transaction_id, created_at FROM orders {where} ORDER BY created_at DESC LIMIT :lim OFFSET :off"), params).fetchall()
    orders = [{"id": r[0], "user_id": r[1], "subtotal": float(r[2] or 0), "discount_applied": float(r[3] or 0), "shipping_cost": float(r[4] or 0), "total_amount": float(r[5]), "status": r[6], "shipping_address": r[7], "transaction_id": r[8], "created_at": str(r[9])} for r in rows]
    return {"orders": orders, "total": total, "page": page, "limit": limit}


@app.get("/api/v1/admin/orders/{order_id}", tags=["Admin Orders"])
async def get_order_detail(order_id: int, db: Session = Depends(get_db), user: dict = Depends(require_admin)):
    order = db.execute(text("SELECT * FROM orders WHERE id = :id"), {"id": order_id}).fetchone()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    items = db.execute(text("SELECT * FROM order_items WHERE order_id = :oid"), {"oid": order_id}).fetchall()
    customer = db.execute(text("SELECT id, email, username, full_name, phone FROM users WHERE id = :uid"), {"uid": order[1]}).fetchone()
    return {
        "order": dict(order._mapping),
        "items": [dict(i._mapping) for i in items],
        "customer": dict(customer._mapping) if customer else None,
    }


@app.put("/api/v1/admin/orders/{order_id}/status", tags=["Admin Orders"])
async def update_order_status(order_id: int, data: OrderStatusUpdate, db: Session = Depends(get_db), user: dict = Depends(require_admin)):
    order = db.execute(text("SELECT id, status FROM orders WHERE id = :id"), {"id": order_id}).fetchone()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    updates = {"status": data.status, "updated_at": datetime.utcnow()}
    if data.status == "shipped":
        updates["shipped_at"] = datetime.utcnow()
    elif data.status == "delivered":
        updates["delivered_at"] = datetime.utcnow()
    elif data.status == "cancelled":
        updates["cancelled_at"] = datetime.utcnow()
        updates["cancellation_reason"] = data.notes
    set_clause = ", ".join(f"{k} = :{k}" for k in updates)
    updates["id"] = order_id
    db.execute(text(f"UPDATE orders SET {set_clause} WHERE id = :id"), updates)
    # Add tracking record
    db.execute(text("INSERT INTO order_tracking (order_id, status, description, tracking_number, updated_by) VALUES (:oid, :s, :d, :tn, :ub)"),
               {"oid": order_id, "s": data.status, "d": data.notes, "tn": data.tracking_number, "ub": user.get("username")})
    db.commit()
    redis_client.invalidate_pattern("admin:dashboard:*")
    return {"message": "Order status updated", "order_id": order_id, "new_status": data.status}


@app.post("/api/v1/admin/orders/bulk-update", tags=["Admin Orders"])
async def bulk_update_orders(data: BulkOrderUpdate, db: Session = Depends(get_db), user: dict = Depends(require_admin)):
    for oid in data.order_ids:
        db.execute(text("UPDATE orders SET status = :s, updated_at = :now WHERE id = :id"), {"s": data.status, "now": datetime.utcnow(), "id": oid})
        db.execute(text("INSERT INTO order_tracking (order_id, status, description, updated_by) VALUES (:oid, :s, :d, :ub)"),
                   {"oid": oid, "s": data.status, "d": data.notes, "ub": user.get("username")})
    db.commit()
    redis_client.invalidate_pattern("admin:dashboard:*")
    return {"message": f"Updated {len(data.order_ids)} orders", "status": data.status}


# ==================== User Management (Admin) ====================

@app.get("/api/v1/admin/users", tags=["Admin Users"])
async def list_users(
    role: Optional[str] = None, search: Optional[str] = None,
    page: int = Query(1, ge=1), limit: int = Query(20, le=100),
    db: Session = Depends(get_db), user: dict = Depends(require_admin),
):
    offset = (page - 1) * limit
    conditions, params = [], {"lim": limit, "off": offset}
    if role:
        conditions.append("u.role = :role")
        params["role"] = role
    if search:
        conditions.append("(u.email ILIKE :search OR u.username ILIKE :search OR u.full_name ILIKE :search)")
        params["search"] = f"%{search}%"
    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
    rows = db.execute(text(f"""
        SELECT u.id, u.email, u.username, u.full_name, u.role, u.is_active, u.created_at,
               COALESCE(o.cnt, 0) as order_count, COALESCE(o.total, 0) as total_spent
        FROM users u LEFT JOIN (SELECT user_id, COUNT(*) cnt, SUM(total_amount) total FROM orders GROUP BY user_id) o ON o.user_id = u.id
        {where} ORDER BY u.created_at DESC LIMIT :lim OFFSET :off
    """), params).fetchall()
    total = db.execute(text(f"SELECT COUNT(*) FROM users u {where}"), params).scalar()
    users = [{"id": r[0], "email": r[1], "username": r[2], "full_name": r[3], "role": str(r[4]), "is_active": r[5], "created_at": str(r[6]), "order_count": r[7], "total_spent": float(r[8])} for r in rows]
    return {"users": users, "total": total, "page": page, "limit": limit}


@app.get("/api/v1/admin/users/{user_id}", tags=["Admin Users"])
async def get_user_detail(user_id: int, db: Session = Depends(get_db), user: dict = Depends(require_admin)):
    u = db.execute(text("SELECT * FROM users WHERE id = :id"), {"id": user_id}).fetchone()
    if not u:
        raise HTTPException(status_code=404, detail="User not found")
    orders = db.execute(text("SELECT id, total_amount, status, created_at FROM orders WHERE user_id = :uid ORDER BY created_at DESC LIMIT 10"), {"uid": user_id}).fetchall()
    return {
        "user": {k: v for k, v in dict(u._mapping).items() if k != "hashed_password"},
        "recent_orders": [dict(o._mapping) for o in orders],
    }


@app.put("/api/v1/admin/users/{user_id}/status", tags=["Admin Users"])
async def update_user_status(user_id: int, data: UserStatusUpdate, db: Session = Depends(get_db), user: dict = Depends(require_admin)):
    db.execute(text("UPDATE users SET is_active = :active WHERE id = :id"), {"active": data.is_active, "id": user_id})
    db.commit()
    return {"message": "User status updated", "user_id": user_id, "is_active": data.is_active}


# ==================== Inventory (Admin) ====================

@app.get("/api/v1/admin/inventory/low-stock", tags=["Admin Inventory"])
async def admin_low_stock(db: Session = Depends(get_db), user: dict = Depends(require_admin)):
    rows = db.execute(text(
        "SELECT i.*, p.name as product_name FROM inventory i JOIN products p ON p.id = i.product_id "
        "WHERE i.quantity <= i.low_stock_threshold ORDER BY i.quantity ASC"
    )).fetchall()
    return {"items": [dict(r._mapping) for r in rows]}


# ==================== Staff Dashboard ====================

@app.get("/api/v1/staff/dashboard", response_model=StaffDashboard, tags=["Staff Dashboard"])
async def get_staff_dashboard(db: Session = Depends(get_db), user: dict = Depends(require_staff)):
    low = db.execute(text("SELECT COUNT(*) FROM inventory WHERE quantity <= low_stock_threshold AND quantity > 0")).scalar() or 0
    oos = db.execute(text("SELECT COUNT(*) FROM inventory WHERE quantity = 0")).scalar() or 0
    pending = db.execute(text("SELECT COUNT(*) FROM orders WHERE status = 'pending'")).scalar() or 0
    stock_tasks = db.execute(text("SELECT COUNT(*) FROM staff_tasks WHERE task_type = 'stock_update' AND status = 'pending'")).scalar() or 0
    order_tasks = db.execute(text("SELECT COUNT(*) FROM staff_tasks WHERE task_type = 'order_processing' AND status = 'pending'")).scalar() or 0
    return StaffDashboard(
        inventory_alerts=InventoryAlert(low_stock=low, out_of_stock=oos),
        pending_orders=pending,
        today_tasks={"stock_updates": stock_tasks, "order_processing": order_tasks},
        quick_actions=["add_stock", "process_orders", "update_inventory", "view_low_stock"],
    )


# ==================== Staff Inventory ====================

@app.get("/api/v1/staff/inventory/low-stock", tags=["Staff Inventory"])
async def staff_low_stock(db: Session = Depends(get_db), user: dict = Depends(require_staff)):
    rows = db.execute(text(
        "SELECT i.*, p.name as product_name FROM inventory i JOIN products p ON p.id = i.product_id "
        "WHERE i.quantity <= i.low_stock_threshold AND i.quantity > 0 ORDER BY i.quantity ASC"
    )).fetchall()
    return {"items": [dict(r._mapping) for r in rows]}


@app.get("/api/v1/staff/inventory/out-of-stock", tags=["Staff Inventory"])
async def staff_out_of_stock(db: Session = Depends(get_db), user: dict = Depends(require_staff)):
    rows = db.execute(text(
        "SELECT i.*, p.name as product_name FROM inventory i JOIN products p ON p.id = i.product_id WHERE i.quantity = 0"
    )).fetchall()
    return {"items": [dict(r._mapping) for r in rows]}


@app.post("/api/v1/staff/inventory/add-stock", tags=["Staff Inventory"])
async def add_stock(data: AddStockRequest, db: Session = Depends(get_db), user: dict = Depends(require_staff)):
    existing = db.execute(text("SELECT id, quantity FROM inventory WHERE product_id = :pid AND sku = :sku"), {"pid": data.product_id, "sku": data.sku}).fetchone()
    if existing:
        new_qty = existing[1] + data.quantity
        db.execute(text("UPDATE inventory SET quantity = :q, updated_at = :now WHERE id = :id"), {"q": new_qty, "now": datetime.utcnow(), "id": existing[0]})
        inv_id = existing[0]
    else:
        result = db.execute(text(
            "INSERT INTO inventory (product_id, sku, quantity, cost_price, created_at, updated_at) "
            "VALUES (:pid, :sku, :qty, :cp, :now, :now) RETURNING id"
        ), {"pid": data.product_id, "sku": data.sku, "qty": data.quantity, "cp": data.cost_price, "now": datetime.utcnow()})
        inv_id = result.scalar()
    # Record movement
    db.execute(text(
        "INSERT INTO inventory_movements (inventory_id, product_id, adjustment, reason, notes, supplier, cost_price, performed_by) "
        "VALUES (:iid, :pid, :adj, 'restock', :notes, :supplier, :cp, :by)"
    ), {"iid": inv_id, "pid": data.product_id, "adj": data.quantity, "notes": data.notes, "supplier": data.supplier, "cp": data.cost_price, "by": user.get("user_id")})
    db.commit()
    redis_client.invalidate_pattern("admin:dashboard:*")
    return {"message": "Stock added", "inventory_id": inv_id, "quantity_added": data.quantity}


@app.post("/api/v1/staff/inventory/adjust-stock", tags=["Staff Inventory"])
async def adjust_stock(data: AdjustStockRequest, db: Session = Depends(get_db), user: dict = Depends(require_staff)):
    inv = db.execute(text("SELECT id, product_id, quantity FROM inventory WHERE id = :id"), {"id": data.inventory_id}).fetchone()
    if not inv:
        raise HTTPException(status_code=404, detail="Inventory item not found")
    new_qty = max(0, inv[2] + data.adjustment)
    db.execute(text("UPDATE inventory SET quantity = :q, updated_at = :now WHERE id = :id"), {"q": new_qty, "now": datetime.utcnow(), "id": data.inventory_id})
    db.execute(text(
        "INSERT INTO inventory_movements (inventory_id, product_id, adjustment, reason, notes, performed_by) "
        "VALUES (:iid, :pid, :adj, :reason, :notes, :by)"
    ), {"iid": data.inventory_id, "pid": inv[1], "adj": data.adjustment, "reason": data.reason, "notes": data.notes, "by": user.get("user_id")})
    db.commit()
    redis_client.invalidate_pattern("admin:dashboard:*")
    return {"message": "Stock adjusted", "inventory_id": data.inventory_id, "new_quantity": new_qty}


@app.get("/api/v1/staff/inventory/movements", tags=["Staff Inventory"])
async def get_movements(
    product_id: Optional[int] = None, page: int = Query(1, ge=1), limit: int = Query(20, le=100),
    db: Session = Depends(get_db), user: dict = Depends(require_staff),
):
    offset = (page - 1) * limit
    where, params = "", {"lim": limit, "off": offset}
    if product_id:
        where = "WHERE im.product_id = :pid"
        params["pid"] = product_id
    rows = db.execute(text(f"""
        SELECT im.*, p.name as product_name FROM inventory_movements im
        JOIN products p ON p.id = im.product_id {where}
        ORDER BY im.created_at DESC LIMIT :lim OFFSET :off
    """), params).fetchall()
    return {"movements": [dict(r._mapping) for r in rows]}


@app.post("/api/v1/staff/inventory/bulk-update", tags=["Staff Inventory"])
async def bulk_update_inventory(data: BulkInventoryUpdate, db: Session = Depends(get_db), user: dict = Depends(require_staff)):
    updated = 0
    for item in data.updates:
        inv_id = item.get("inventory_id")
        if not inv_id:
            continue
        sets, params = [], {"id": inv_id, "now": datetime.utcnow()}
        if "quantity" in item:
            sets.append("quantity = :qty")
            params["qty"] = item["quantity"]
        if "low_stock_threshold" in item:
            sets.append("low_stock_threshold = :thresh")
            params["thresh"] = item["low_stock_threshold"]
        if sets:
            sets.append("updated_at = :now")
            db.execute(text(f"UPDATE inventory SET {', '.join(sets)} WHERE id = :id"), params)
            updated += 1
    db.commit()
    redis_client.invalidate_pattern("admin:dashboard:*")
    return {"message": f"Updated {updated} inventory items"}


# ==================== Product Variants (Staff) ====================

@app.get("/api/v1/staff/products/{product_id}/variants", tags=["Staff Variants"])
async def get_variants(product_id: int, db: Session = Depends(get_db), user: dict = Depends(require_staff)):
    rows = db.execute(text("SELECT * FROM product_variants WHERE product_id = :pid"), {"pid": product_id}).fetchall()
    return {"variants": [dict(r._mapping) for r in rows]}


@app.post("/api/v1/staff/products/{product_id}/variants", tags=["Staff Variants"])
async def create_variant(product_id: int, data: VariantCreate, db: Session = Depends(get_db), user: dict = Depends(require_staff)):
    result = db.execute(text(
        "INSERT INTO product_variants (product_id, sku, size, color, inventory_count, created_at, updated_at) "
        "VALUES (:pid, :sku, :size, :color, :qty, :now, :now) RETURNING id"
    ), {"pid": product_id, "sku": data.sku, "size": data.size, "color": data.color, "qty": data.quantity, "now": datetime.utcnow()})
    db.commit()
    return {"message": "Variant created", "variant_id": result.scalar()}


@app.put("/api/v1/staff/variants/{variant_id}", tags=["Staff Variants"])
async def update_variant(variant_id: int, data: VariantUpdate, db: Session = Depends(get_db), user: dict = Depends(require_staff)):
    sets, params = ["updated_at = :now"], {"id": variant_id, "now": datetime.utcnow()}
    if data.size is not None: sets.append("size = :size"); params["size"] = data.size
    if data.color is not None: sets.append("color = :color"); params["color"] = data.color
    if data.quantity is not None: sets.append("inventory_count = :qty"); params["qty"] = data.quantity
    db.execute(text(f"UPDATE product_variants SET {', '.join(sets)} WHERE id = :id"), params)
    db.commit()
    return {"message": "Variant updated"}


@app.delete("/api/v1/staff/variants/{variant_id}", tags=["Staff Variants"])
async def delete_variant(variant_id: int, db: Session = Depends(get_db), user: dict = Depends(require_staff)):
    db.execute(text("DELETE FROM product_variants WHERE id = :id"), {"id": variant_id})
    db.commit()
    return {"message": "Variant deleted"}


# ==================== Staff Order Processing ====================

@app.get("/api/v1/staff/orders/pending", tags=["Staff Orders"])
async def staff_pending_orders(db: Session = Depends(get_db), user: dict = Depends(require_staff)):
    rows = db.execute(text("SELECT id, user_id, total_amount, status, shipping_address, created_at FROM orders WHERE status = 'pending' ORDER BY created_at ASC")).fetchall()
    return {"orders": [dict(r._mapping) for r in rows]}


@app.get("/api/v1/staff/orders/processing", tags=["Staff Orders"])
async def staff_processing_orders(db: Session = Depends(get_db), user: dict = Depends(require_staff)):
    rows = db.execute(text("SELECT id, user_id, total_amount, status, shipping_address, created_at FROM orders WHERE status = 'processing' ORDER BY created_at ASC")).fetchall()
    return {"orders": [dict(r._mapping) for r in rows]}


@app.put("/api/v1/staff/orders/{order_id}/process", tags=["Staff Orders"])
async def process_order(order_id: int, data: OrderProcessRequest, db: Session = Depends(get_db), user: dict = Depends(require_staff)):
    order = db.execute(text("SELECT id, status FROM orders WHERE id = :id"), {"id": order_id}).fetchone()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if order[1] != "pending":
        raise HTTPException(status_code=400, detail="Only pending orders can be processed")
    db.execute(text("UPDATE orders SET status = 'processing', updated_at = :now WHERE id = :id"), {"now": datetime.utcnow(), "id": order_id})
    db.execute(text("INSERT INTO order_tracking (order_id, status, description, updated_by) VALUES (:oid, 'processing', :notes, :by)"),
               {"oid": order_id, "notes": data.notes, "by": user.get("username")})
    db.commit()
    return {"message": "Order is now processing", "order_id": order_id}


@app.put("/api/v1/staff/orders/{order_id}/ship", tags=["Staff Orders"])
async def ship_order(order_id: int, data: OrderShipRequest, db: Session = Depends(get_db), user: dict = Depends(require_staff)):
    order = db.execute(text("SELECT id, status FROM orders WHERE id = :id"), {"id": order_id}).fetchone()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if order[1] != "processing":
        raise HTTPException(status_code=400, detail="Only processing orders can be shipped")
    db.execute(text("UPDATE orders SET status = 'shipped', shipped_at = :now, updated_at = :now WHERE id = :id"), {"now": datetime.utcnow(), "id": order_id})
    db.execute(text("INSERT INTO order_tracking (order_id, status, description, tracking_number, updated_by) VALUES (:oid, 'shipped', :notes, :tn, :by)"),
               {"oid": order_id, "notes": data.notes, "tn": data.tracking_number, "by": user.get("username")})
    db.commit()
    return {"message": "Order shipped", "order_id": order_id, "tracking_number": data.tracking_number}


@app.post("/api/v1/staff/orders/bulk-process", tags=["Staff Orders"])
async def bulk_process_orders(data: BulkOrderUpdate, db: Session = Depends(get_db), user: dict = Depends(require_staff)):
    processed = 0
    for oid in data.order_ids:
        result = db.execute(text("UPDATE orders SET status = 'processing', updated_at = :now WHERE id = :id AND status = 'pending'"), {"now": datetime.utcnow(), "id": oid})
        if result.rowcount:
            db.execute(text("INSERT INTO order_tracking (order_id, status, description, updated_by) VALUES (:oid, 'processing', :notes, :by)"),
                       {"oid": oid, "notes": data.notes, "by": user.get("username")})
            processed += 1
    db.commit()
    return {"message": f"Processed {processed} orders"}


# ==================== Staff Reservations ====================

@app.get("/api/v1/staff/reservations/pending", tags=["Staff Reservations"])
async def pending_reservations(db: Session = Depends(get_db), user: dict = Depends(require_staff)):
    rows = db.execute(text(
        "SELECT i.id, i.product_id, p.name, i.sku, i.reserved_quantity FROM inventory i "
        "JOIN products p ON p.id = i.product_id WHERE i.reserved_quantity > 0"
    )).fetchall()
    return {"reservations": [dict(r._mapping) for r in rows]}


@app.post("/api/v1/staff/reservations/release", tags=["Staff Reservations"])
async def release_reservation(data: ReservationRelease, db: Session = Depends(get_db), user: dict = Depends(require_staff)):
    for item in data.items:
        inv_id = item.get("inventory_id")
        qty = item.get("quantity", 0)
        db.execute(text("UPDATE inventory SET reserved_quantity = GREATEST(0, reserved_quantity - :qty), quantity = quantity + :qty WHERE id = :id"),
                   {"qty": qty, "id": inv_id})
    db.commit()
    return {"message": "Reservations released"}


@app.post("/api/v1/staff/reservations/confirm", tags=["Staff Reservations"])
async def confirm_reservation(data: ReservationRelease, db: Session = Depends(get_db), user: dict = Depends(require_staff)):
    for item in data.items:
        inv_id = item.get("inventory_id")
        qty = item.get("quantity", 0)
        db.execute(text("UPDATE inventory SET reserved_quantity = GREATEST(0, reserved_quantity - :qty) WHERE id = :id"), {"qty": qty, "id": inv_id})
    db.commit()
    return {"message": "Reservations confirmed (stock deducted)"}


# ==================== Staff Reports ====================

@app.get("/api/v1/staff/reports/inventory/summary", tags=["Staff Reports"])
async def inventory_summary(db: Session = Depends(get_db), user: dict = Depends(require_staff)):
    total_products = db.execute(text("SELECT COUNT(*) FROM products WHERE is_active = true")).scalar() or 0
    total_variants = db.execute(text("SELECT COUNT(*) FROM product_variants")).scalar() or 0
    total_stock = db.execute(text("SELECT COALESCE(SUM(quantity), 0) FROM inventory")).scalar() or 0
    low = db.execute(text("SELECT COUNT(*) FROM inventory WHERE quantity <= low_stock_threshold AND quantity > 0")).scalar() or 0
    oos = db.execute(text("SELECT COUNT(*) FROM inventory WHERE quantity = 0")).scalar() or 0
    top = db.execute(text(
        "SELECT p.name, COALESCE(SUM(ABS(im.adjustment)), 0) as movements FROM inventory_movements im "
        "JOIN products p ON p.id = im.product_id GROUP BY p.name ORDER BY movements DESC LIMIT 5"
    )).fetchall()
    return {
        "total_products": total_products, "total_variants": total_variants,
        "total_stock": total_stock, "low_stock_items": low, "out_of_stock_items": oos,
        "top_moving_products": [{"product_name": r[0], "movements": r[1]} for r in top],
    }


@app.get("/api/v1/staff/reports/orders/processed", tags=["Staff Reports"])
async def processed_orders_report(db: Session = Depends(get_db), user: dict = Depends(require_staff)):
    today = datetime.utcnow().date()
    processed = db.execute(text("SELECT COUNT(*) FROM orders WHERE status = 'processing' AND DATE(updated_at) = :d"), {"d": today}).scalar() or 0
    shipped = db.execute(text("SELECT COUNT(*) FROM orders WHERE status = 'shipped' AND DATE(shipped_at) = :d"), {"d": today}).scalar() or 0
    pending = db.execute(text("SELECT COUNT(*) FROM orders WHERE status = 'pending'")).scalar() or 0
    return {"today_processed": processed, "today_shipped": shipped, "pending_orders": pending}


# ==================== Staff Tasks ====================

@app.get("/api/v1/staff/tasks", tags=["Staff Tasks"])
async def get_tasks(db: Session = Depends(get_db), user: dict = Depends(require_staff)):
    rows = db.execute(text("SELECT * FROM staff_tasks WHERE status != 'completed' ORDER BY CASE priority WHEN 'high' THEN 1 WHEN 'medium' THEN 2 ELSE 3 END, due_time ASC NULLS LAST")).fetchall()
    return {"pending_tasks": [dict(r._mapping) for r in rows]}


@app.post("/api/v1/staff/tasks/{task_id}/complete", tags=["Staff Tasks"])
async def complete_task(task_id: int, data: TaskComplete, db: Session = Depends(get_db), user: dict = Depends(require_staff)):
    db.execute(text("UPDATE staff_tasks SET status = 'completed', completed_at = :now, updated_at = :now WHERE id = :id"),
               {"now": datetime.utcnow(), "id": task_id})
    db.commit()
    return {"message": "Task completed"}


# ==================== Staff Notifications ====================

@app.get("/api/v1/staff/notifications", tags=["Staff Notifications"])
async def get_notifications(db: Session = Depends(get_db), user: dict = Depends(require_staff)):
    uid = user.get("user_id")
    rows = db.execute(text("SELECT * FROM staff_notifications WHERE (user_id = :uid OR user_id IS NULL) AND is_read = false ORDER BY created_at DESC LIMIT 50"), {"uid": uid}).fetchall()
    return {"alerts": [dict(r._mapping) for r in rows]}


@app.put("/api/v1/staff/notifications/{notif_id}/read", tags=["Staff Notifications"])
async def mark_notification_read(notif_id: int, db: Session = Depends(get_db), user: dict = Depends(require_staff)):
    db.execute(text("UPDATE staff_notifications SET is_read = true WHERE id = :id"), {"id": notif_id})
    db.commit()
    return {"message": "Notification marked as read"}


# ==================== Chat ====================

@app.get("/api/v1/admin/chat/rooms", tags=["Chat"])
async def list_chat_rooms(
    status: Optional[str] = None, db: Session = Depends(get_db), user: dict = Depends(require_staff),
):
    where, params = "", {}
    if status:
        where = "WHERE status = :status"
        params["status"] = status
    rows = db.execute(text(f"SELECT * FROM chat_rooms {where} ORDER BY updated_at DESC LIMIT 50"), params).fetchall()
    return {"rooms": [dict(r._mapping) for r in rows]}


@app.get("/api/v1/admin/chat/rooms/{room_id}/messages", tags=["Chat"])
async def get_chat_messages(room_id: int, db: Session = Depends(get_db), user: dict = Depends(require_staff)):
    msgs = db.execute(text("SELECT * FROM chat_messages WHERE room_id = :rid ORDER BY created_at ASC"), {"rid": room_id}).fetchall()
    # Mark as read
    db.execute(text("UPDATE chat_messages SET is_read = true WHERE room_id = :rid AND sender_type != 'staff' AND sender_type != 'admin'"), {"rid": room_id})
    db.commit()
    return {"messages": [dict(m._mapping) for m in msgs]}


@app.post("/api/v1/admin/chat/rooms/{room_id}/messages", tags=["Chat"])
async def send_chat_message(room_id: int, data: ChatMessageCreate, db: Session = Depends(get_db), user: dict = Depends(require_staff)):
    db.execute(text(
        "INSERT INTO chat_messages (room_id, sender_id, sender_type, message) VALUES (:rid, :sid, :st, :msg)"
    ), {"rid": room_id, "sid": user.get("user_id"), "st": data.sender_type, "msg": data.message})
    db.execute(text("UPDATE chat_rooms SET updated_at = :now WHERE id = :rid"), {"now": datetime.utcnow(), "rid": room_id})
    db.commit()
    redis_client.publish("chat:notifications", {"room_id": room_id, "message": data.message})
    return {"message": "Message sent"}


@app.put("/api/v1/admin/chat/rooms/{room_id}/assign", tags=["Chat"])
async def assign_chat_room(room_id: int, db: Session = Depends(get_db), user: dict = Depends(require_staff)):
    db.execute(text("UPDATE chat_rooms SET assigned_to = :uid, status = 'assigned', updated_at = :now WHERE id = :rid"),
               {"uid": user.get("user_id"), "rid": room_id, "now": datetime.utcnow()})
    db.commit()
    return {"message": "Chat room assigned to you"}


@app.put("/api/v1/admin/chat/rooms/{room_id}/close", tags=["Chat"])
async def close_chat_room(room_id: int, db: Session = Depends(get_db), user: dict = Depends(require_staff)):
    db.execute(text("UPDATE chat_rooms SET status = 'closed', closed_at = :now, updated_at = :now WHERE id = :rid"),
               {"rid": room_id, "now": datetime.utcnow()})
    db.commit()
    return {"message": "Chat room closed"}


# ==================== Landing Config ====================

@app.get("/api/v1/admin/landing/config", tags=["Landing Config"])
async def get_landing_config(db: Session = Depends(get_db), user: dict = Depends(require_admin)):
    rows = db.execute(text("SELECT * FROM landing_config ORDER BY section")).fetchall()
    return {"sections": [dict(r._mapping) for r in rows]}


@app.put("/api/v1/admin/landing/config/{section}", tags=["Landing Config"])
async def update_landing_config(section: str, data: LandingConfigUpdate, db: Session = Depends(get_db), user: dict = Depends(require_admin)):
    existing = db.execute(text("SELECT id FROM landing_config WHERE section = :s"), {"s": section}).fetchone()
    if existing:
        updates = {"config": str(data.config), "updated_by": user.get("user_id"), "now": datetime.utcnow(), "s": section}
        if data.is_active is not None:
            db.execute(text("UPDATE landing_config SET config = :config::jsonb, is_active = :active, updated_by = :updated_by, updated_at = :now WHERE section = :s"),
                       {**updates, "active": data.is_active})
        else:
            db.execute(text("UPDATE landing_config SET config = :config::jsonb, updated_by = :updated_by, updated_at = :now WHERE section = :s"), updates)
    else:
        db.execute(text("INSERT INTO landing_config (section, config, updated_by) VALUES (:s, :config::jsonb, :by)"),
                   {"s": section, "config": str(data.config), "by": user.get("user_id")})
    db.commit()
    return {"message": f"Landing config for '{section}' updated"}


@app.get("/api/v1/admin/landing/images", tags=["Landing Config"])
async def get_landing_images(section: Optional[str] = None, db: Session = Depends(get_db), user: dict = Depends(require_admin)):
    if section:
        rows = db.execute(text("SELECT * FROM landing_images WHERE section = :s ORDER BY display_order"), {"s": section}).fetchall()
    else:
        rows = db.execute(text("SELECT * FROM landing_images ORDER BY section, display_order")).fetchall()
    return {"images": [dict(r._mapping) for r in rows]}


@app.post("/api/v1/admin/landing/images", tags=["Landing Config"])
async def add_landing_image(data: LandingImageCreate, db: Session = Depends(get_db), user: dict = Depends(require_admin)):
    """Add a landing image using a pre-existing URL (e.g. from presigned upload)."""
    result = db.execute(text(
        "INSERT INTO landing_images (section, image_url, title, subtitle, link_url, display_order) "
        "VALUES (:s, :url, :title, :sub, :link, :order) RETURNING id"
    ), {"s": data.section, "url": data.image_url, "title": data.title, "sub": data.subtitle, "link": data.link_url, "order": data.display_order})
    db.commit()
    return {"message": "Image added", "image_id": result.scalar()}


@app.post("/api/v1/admin/landing/images/upload", tags=["Landing Config"])
async def upload_landing_image(
    section: str,
    file: UploadFile = File(...),
    title: Optional[str] = None,
    subtitle: Optional[str] = None,
    link_url: Optional[str] = None,
    display_order: int = 0,
    db: Session = Depends(get_db),
    user: dict = Depends(require_admin),
):
    """Upload a landing page image directly to Cloudflare R2 and save metadata."""
    image_url = await r2_service.upload_image(file, folder="landing")

    result = db.execute(text(
        "INSERT INTO landing_images (section, image_url, title, subtitle, link_url, display_order) "
        "VALUES (:s, :url, :title, :sub, :link, :order) RETURNING id"
    ), {"s": section, "url": image_url, "title": title, "sub": subtitle, "link": link_url, "order": display_order})
    db.commit()
    return {"message": "Image uploaded and saved", "image_id": result.scalar(), "image_url": image_url}


@app.delete("/api/v1/admin/landing/images/{image_id}", tags=["Landing Config"])
async def delete_landing_image(image_id: int, db: Session = Depends(get_db), user: dict = Depends(require_admin)):
    """Delete a landing image from both the database and Cloudflare R2."""
    row = db.execute(text("SELECT image_url FROM landing_images WHERE id = :id"), {"id": image_id}).fetchone()
    if row and row[0]:
        await r2_service.delete_image(row[0])
    db.execute(text("DELETE FROM landing_images WHERE id = :id"), {"id": image_id})
    db.commit()
    return {"message": "Image deleted"}


# ==================== Presigned URL (Frontend Direct Upload) ====================

@app.post("/api/v1/admin/upload/presigned-url", tags=["Admin Upload"])
async def get_presigned_upload_url(
    filename: str,
    folder: str = Query("landing", regex="^(landing|banners|categories|products|inventory)$"),
    content_type: str = Query("image/jpeg"),
    user: dict = Depends(require_admin),
):
    """Generate a presigned Cloudflare R2 URL for frontend direct upload.
    
    The frontend can PUT the file directly to the returned upload_url,
    then use the final_url when saving metadata.
    """
    return r2_service.generate_presigned_url(
        filename=filename, folder=folder, content_type=content_type
    )


@app.post("/api/v1/admin/upload/image", tags=["Admin Upload"])
async def upload_admin_image(
    file: UploadFile = File(...),
    folder: str = Query("landing", regex="^(landing|banners|categories|products|inventory)$"),
    user: dict = Depends(require_admin),
):
    """Generic image upload endpoint for any admin-managed asset.
    
    Uploads the file to Cloudflare R2 and returns the public URL.
    Use the returned URL when creating/updating records.
    """
    image_url = await r2_service.upload_image(file, folder=folder)
    return {"image_url": image_url, "folder": folder}


@app.delete("/api/v1/admin/upload/image", tags=["Admin Upload"])
async def delete_admin_image(
    image_url: str,
    user: dict = Depends(require_admin),
):
    """Delete an image from Cloudflare R2 by its URL."""
    deleted = await r2_service.delete_image(image_url)
    return {"deleted": deleted, "image_url": image_url}


# ==================== Quick Actions ====================

@app.get("/api/v1/staff/quick-actions", tags=["Staff"])
async def get_quick_actions():
    return {"actions": [
        {"name": "Add Stock", "endpoint": "/api/v1/staff/inventory/add-stock", "icon": "plus-box"},
        {"name": "Process Orders", "endpoint": "/api/v1/staff/orders/pending", "icon": "package"},
        {"name": "Low Stock Alert", "endpoint": "/api/v1/staff/inventory/low-stock", "icon": "alert"},
        {"name": "Stock Movement", "endpoint": "/api/v1/staff/inventory/movements", "icon": "chart-line"},
    ]}


# ==================== Product Performance Analytics ====================

@app.get("/api/v1/admin/analytics/products/performance", tags=["Analytics"])
async def get_product_performance(
    period: str = Query("30d", regex="^(7d|30d|90d|1y)$"),
    limit: int = Query(20, le=100),
    db: Session = Depends(get_db), user: dict = Depends(require_admin),
):
    """Detailed product performance: views, orders, revenue, conversion."""
    days = {"7d": 7, "30d": 30, "90d": 90, "1y": 365}[period]
    since = datetime.utcnow() - timedelta(days=days)
    rows = db.execute(text("""
        SELECT p.id, p.name, p.sku, p.price, p.total_stock,
               COALESCE(s.total_sold, 0) as total_sold,
               COALESCE(s.total_revenue, 0) as total_revenue,
               COALESCE(s.order_count, 0) as order_count,
               COALESCE(r.avg_rating, 0) as avg_rating,
               COALESCE(r.review_count, 0) as review_count
        FROM products p
        LEFT JOIN (
            SELECT oi.product_id,
                   SUM(oi.quantity) as total_sold,
                   SUM(oi.price) as total_revenue,
                   COUNT(DISTINCT oi.order_id) as order_count
            FROM order_items oi
            JOIN orders o ON o.id = oi.order_id
            WHERE o.created_at >= :since AND o.status NOT IN ('cancelled','refunded')
            GROUP BY oi.product_id
        ) s ON s.product_id = p.id
        LEFT JOIN (
            SELECT product_id, AVG(rating) as avg_rating, COUNT(*) as review_count
            FROM reviews WHERE is_approved = true GROUP BY product_id
        ) r ON r.product_id = p.id
        WHERE p.is_active = true
        ORDER BY total_revenue DESC LIMIT :lim
    """), {"since": since, "lim": limit}).fetchall()

    products = [{
        "id": r[0], "name": r[1], "sku": r[2], "price": float(r[3]),
        "stock": r[4], "total_sold": r[5], "revenue": float(r[6]),
        "order_count": r[7], "avg_rating": round(float(r[8]), 1), "review_count": r[9],
    } for r in rows]

    return {"products": products, "period": period, "total": len(products)}


@app.get("/api/v1/admin/analytics/customers/detailed", tags=["Analytics"])
async def get_detailed_customer_analytics(
    period: str = Query("30d", regex="^(7d|30d|90d|1y)$"),
    db: Session = Depends(get_db), user: dict = Depends(require_admin),
):
    """Detailed customer analytics: LTV, segments, acquisition trends."""
    days = {"7d": 7, "30d": 30, "90d": 90, "1y": 365}[period]
    since = datetime.utcnow() - timedelta(days=days)

    # Registration trend by day
    reg_trend = db.execute(text("""
        SELECT DATE(created_at) as day, COUNT(*) as count
        FROM users WHERE role = 'customer' AND created_at >= :since
        GROUP BY DATE(created_at) ORDER BY day
    """), {"since": since}).fetchall()

    # Top customers by spend
    top_customers = db.execute(text("""
        SELECT u.id, u.username, u.email, COUNT(o.id) as orders, SUM(o.total_amount) as total_spent
        FROM users u JOIN orders o ON o.user_id = u.id
        WHERE o.status NOT IN ('cancelled','refunded') AND o.created_at >= :since
        GROUP BY u.id, u.username, u.email
        ORDER BY total_spent DESC LIMIT 10
    """), {"since": since}).fetchall()

    # Customer segments
    avg_ltv = db.execute(text("""
        SELECT AVG(total) FROM (
            SELECT SUM(total_amount) as total FROM orders
            WHERE status NOT IN ('cancelled','refunded')
            GROUP BY user_id
        ) sub
    """)).scalar() or 0

    high_value = db.execute(text("""
        SELECT COUNT(DISTINCT user_id) FROM orders
        WHERE status NOT IN ('cancelled','refunded')
        GROUP BY user_id HAVING SUM(total_amount) > :threshold
    """), {"threshold": float(avg_ltv) * 2}).scalar() or 0

    return {
        "registration_trend": [{"date": str(r[0]), "count": r[1]} for r in reg_trend],
        "top_customers": [{"id": r[0], "username": r[1], "email": r[2], "orders": r[3], "total_spent": float(r[4])} for r in top_customers],
        "average_ltv": round(float(avg_ltv), 2),
        "high_value_customers": high_value,
        "period": period,
    }


# ==================== Discount / Promotion Management ====================

@app.get("/api/v1/admin/discounts", tags=["Admin Discounts"])
async def list_discounts(
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db), user: dict = Depends(require_admin),
):
    """List all promotions/discounts."""
    where = ""
    if is_active is not None:
        where = f"WHERE is_active = {'true' if is_active else 'false'}"
    rows = db.execute(text(f"SELECT * FROM promotions {where} ORDER BY created_at DESC")).fetchall()
    return {"discounts": [dict(r._mapping) for r in rows]}


@app.post("/api/v1/admin/discounts", tags=["Admin Discounts"])
async def create_discount(
    code: str, discount_type: str, discount_value: float,
    min_order_value: float = 0, max_discount_amount: Optional[float] = None,
    usage_limit: Optional[int] = None,
    valid_from: Optional[str] = None, valid_until: Optional[str] = None,
    db: Session = Depends(get_db), user: dict = Depends(require_admin),
):
    """Create a new promotion/discount code."""
    result = db.execute(text("""
        INSERT INTO promotions (code, discount_type, discount_value, min_order_value,
            max_discount_amount, usage_limit, valid_from, valid_until, is_active)
        VALUES (:code, :dt, :dv, :mov, :mda, :ul, :vf, :vu, true) RETURNING id
    """), {"code": code.upper(), "dt": discount_type, "dv": discount_value,
           "mov": min_order_value, "mda": max_discount_amount, "ul": usage_limit,
           "vf": valid_from, "vu": valid_until})
    db.commit()
    return {"message": "Discount created", "discount_id": result.scalar(), "code": code.upper()}


@app.put("/api/v1/admin/discounts/{discount_id}", tags=["Admin Discounts"])
async def update_discount(
    discount_id: int, is_active: Optional[bool] = None,
    usage_limit: Optional[int] = None, valid_until: Optional[str] = None,
    db: Session = Depends(get_db), user: dict = Depends(require_admin),
):
    """Update a promotion/discount."""
    sets, params = ["updated_at = :now"], {"id": discount_id, "now": datetime.utcnow()}
    if is_active is not None:
        sets.append("is_active = :active"); params["active"] = is_active
    if usage_limit is not None:
        sets.append("usage_limit = :ul"); params["ul"] = usage_limit
    if valid_until is not None:
        sets.append("valid_until = :vu"); params["vu"] = valid_until
    db.execute(text(f"UPDATE promotions SET {', '.join(sets)} WHERE id = :id"), params)
    db.commit()
    return {"message": "Discount updated"}


@app.delete("/api/v1/admin/discounts/{discount_id}", tags=["Admin Discounts"])
async def delete_discount(discount_id: int, db: Session = Depends(get_db), user: dict = Depends(require_admin)):
    """Delete a discount code."""
    db.execute(text("DELETE FROM promotions WHERE id = :id"), {"id": discount_id})
    db.commit()
    return {"message": "Discount deleted"}


# ==================== Bulk Product Operations ====================

@app.post("/api/v1/admin/products/bulk-update", tags=["Admin Products"])
async def bulk_update_products(
    product_ids: List[int], updates: dict,
    db: Session = Depends(get_db), user: dict = Depends(require_admin),
):
    """Bulk update product fields (price, featured, active, etc.)."""
    allowed_fields = {"price", "mrp", "is_featured", "is_new_arrival", "is_active", "category_id"}
    sets, params = ["updated_at = :now"], {"now": datetime.utcnow()}
    for key, val in updates.items():
        if key in allowed_fields:
            sets.append(f"{key} = :{key}")
            params[key] = val

    if len(sets) == 1:
        raise HTTPException(status_code=400, detail="No valid fields to update")

    updated = 0
    for pid in product_ids:
        params["id"] = pid
        result = db.execute(text(f"UPDATE products SET {', '.join(sets)} WHERE id = :id"), params)
        updated += result.rowcount
    db.commit()
    return {"message": f"Updated {updated} products"}


@app.post("/api/v1/admin/products/bulk-activate", tags=["Admin Products"])
async def bulk_activate_products(product_ids: List[int], db: Session = Depends(get_db), user: dict = Depends(require_admin)):
    """Activate multiple products at once."""
    for pid in product_ids:
        db.execute(text("UPDATE products SET is_active = true, updated_at = :now WHERE id = :id"), {"now": datetime.utcnow(), "id": pid})
    db.commit()
    return {"message": f"Activated {len(product_ids)} products"}


@app.post("/api/v1/admin/products/bulk-deactivate", tags=["Admin Products"])
async def bulk_deactivate_products(product_ids: List[int], db: Session = Depends(get_db), user: dict = Depends(require_admin)):
    """Deactivate multiple products at once."""
    for pid in product_ids:
        db.execute(text("UPDATE products SET is_active = false, updated_at = :now WHERE id = :id"), {"now": datetime.utcnow(), "id": pid})
    db.commit()
    return {"message": f"Deactivated {len(product_ids)} products"}


# ==================== Export ====================

@app.post("/api/v1/admin/export/orders", tags=["Admin Export"])
async def export_orders(
    status: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    db: Session = Depends(get_db), user: dict = Depends(require_admin),
):
    """Export orders as CSV data."""
    conditions, params = [], {}
    if status:
        conditions.append("o.status = :status"); params["status"] = status
    if date_from:
        conditions.append("o.created_at >= :df"); params["df"] = date_from
    if date_to:
        conditions.append("o.created_at <= :dt"); params["dt"] = date_to
    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""

    rows = db.execute(text(f"""
        SELECT o.id, u.email, u.full_name, o.subtotal, o.discount_applied,
               o.shipping_cost, o.total_amount, o.status, o.promo_code,
               o.shipping_address, o.transaction_id, o.created_at
        FROM orders o LEFT JOIN users u ON u.id = o.user_id {where}
        ORDER BY o.created_at DESC
    """), params).fetchall()

    # Build CSV
    headers = "order_id,email,name,subtotal,discount,shipping,total,status,promo_code,address,transaction_id,created_at"
    csv_rows = [headers]
    for r in rows:
        csv_rows.append(",".join(str(v or "") for v in r))

    return {
        "csv": "\n".join(csv_rows),
        "total_rows": len(rows),
        "format": "csv",
        "exported_at": str(datetime.utcnow()),
    }


@app.post("/api/v1/admin/export/products", tags=["Admin Export"])
async def export_products(
    category_id: Optional[int] = None,
    active_only: bool = True,
    db: Session = Depends(get_db), user: dict = Depends(require_admin),
):
    """Export products as CSV data."""
    conditions, params = [], {}
    if active_only:
        conditions.append("p.is_active = true")
    if category_id:
        conditions.append("p.category_id = :cid"); params["cid"] = category_id
    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""

    rows = db.execute(text(f"""
        SELECT p.id, p.name, p.sku, p.slug, p.price, p.mrp, p.total_stock,
               p.is_featured, p.is_new_arrival, p.is_active,
               c.name as category_name, p.created_at
        FROM products p LEFT JOIN categories c ON c.id = p.category_id {where}
        ORDER BY p.name
    """), params).fetchall()

    headers = "id,name,sku,slug,price,mrp,stock,featured,new_arrival,active,category,created_at"
    csv_rows = [headers]
    for r in rows:
        csv_rows.append(",".join(str(v or "") for v in r))

    return {
        "csv": "\n".join(csv_rows),
        "total_rows": len(rows),
        "format": "csv",
        "exported_at": str(datetime.utcnow()),
    }
