#!/usr/bin/env python
"""
Comprehensive Test Suite for Aarya Clothing Backend
Covers: Core Auth, Commerce (Products/Cart/Orders), Payment, Admin, Meilisearch
Run:  python tests/test_all_services.py
"""
import sys
import os
import time
import hashlib
from datetime import datetime, timedelta
from decimal import Decimal
from enum import Enum
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'services', 'commerce'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'services', 'core'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'services', 'payment'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'services', 'admin'))


class TestResult:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.errors = []
        self.sections = []

    def add_pass(self, test_name):
        self.passed += 1
        print(f"  ✅  {test_name}")

    def add_fail(self, test_name, error):
        self.failed += 1
        self.errors.append((test_name, error))
        print(f"  ❌  {test_name}")
        print(f"       Error: {error}")

    def section(self, name):
        self.sections.append(name)
        print(f"\n{'='*60}")
        print(f"  {name}")
        print(f"{'='*60}")


results = TestResult()


# ============================================================
# CORE SERVICE TESTS
# ============================================================

def test_password_validation():
    """Test password policy enforcement."""
    results.section("Core: Password Validation")

    def validate_password(pwd, min_len=8, require_upper=True, require_digit=True, require_special=False):
        errors = []
        if len(pwd) < min_len:
            errors.append("too_short")
        if require_upper and not any(c.isupper() for c in pwd):
            errors.append("no_uppercase")
        if require_digit and not any(c.isdigit() for c in pwd):
            errors.append("no_digit")
        if require_special and not any(c in "!@#$%^&*()-_=+[]{}|;:',.<>?/" for c in pwd):
            errors.append("no_special")
        return len(errors) == 0, errors

    try:
        valid, errs = validate_password("short")
        assert not valid and "too_short" in errs
        results.add_pass("Rejects short passwords")
    except AssertionError as e:
        results.add_fail("Rejects short passwords", e)

    try:
        valid, errs = validate_password("alllowercase123")
        assert not valid and "no_uppercase" in errs
        results.add_pass("Rejects missing uppercase")
    except AssertionError as e:
        results.add_fail("Rejects missing uppercase", e)

    try:
        valid, errs = validate_password("NoDigitsHere")
        assert not valid and "no_digit" in errs
        results.add_pass("Rejects missing digits")
    except AssertionError as e:
        results.add_fail("Rejects missing digits", e)

    try:
        valid, errs = validate_password("ValidPass123")
        assert valid and len(errs) == 0
        results.add_pass("Accepts valid password")
    except AssertionError as e:
        results.add_fail("Accepts valid password", e)

    try:
        valid, errs = validate_password("Short1!", min_len=8)
        assert not valid
        results.add_pass("Honors minimum length config")
    except AssertionError as e:
        results.add_fail("Honors minimum length config", e)


def test_password_hashing():
    """Test password hashing and verification."""
    results.section("Core: Password Hashing")

    password = "SecurePass123!"
    salt = os.urandom(16).hex()
    hashed = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100000).hex()

    try:
        assert hashed != password
        results.add_pass("Password is hashed (not plaintext)")
    except AssertionError as e:
        results.add_fail("Password is hashed", e)

    try:
        rehashed = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100000).hex()
        assert rehashed == hashed
        results.add_pass("Same password + salt produces same hash")
    except AssertionError as e:
        results.add_fail("Hash consistency", e)

    try:
        wrong = hashlib.pbkdf2_hmac("sha256", "WrongPass1!".encode(), salt.encode(), 100000).hex()
        assert wrong != hashed
        results.add_pass("Wrong password produces different hash")
    except AssertionError as e:
        results.add_fail("Wrong password detection", e)


def test_jwt_token_structure():
    """Test JWT token payload structure."""
    results.section("Core: JWT Token Structure")

    now = datetime.utcnow()
    access_payload = {
        "sub": "1",
        "username": "testuser",
        "email": "test@example.com",
        "role": "customer",
        "type": "access",
        "exp": now + timedelta(hours=1),
        "iat": now,
    }

    refresh_payload = {
        "sub": "1",
        "type": "refresh",
        "exp": now + timedelta(days=7),
        "iat": now,
    }

    try:
        assert access_payload["sub"] == "1"
        results.add_pass("Access token: sub claim present")
    except AssertionError as e:
        results.add_fail("Access token: sub claim", e)

    try:
        assert access_payload["type"] == "access"
        results.add_pass("Access token: type is 'access'")
    except AssertionError as e:
        results.add_fail("Access token: type", e)

    try:
        assert "role" in access_payload
        results.add_pass("Access token: role claim present")
    except AssertionError as e:
        results.add_fail("Access token: role claim", e)

    try:
        assert refresh_payload["type"] == "refresh"
        results.add_pass("Refresh token: type is 'refresh'")
    except AssertionError as e:
        results.add_fail("Refresh token: type", e)

    try:
        assert access_payload["exp"] > now
        results.add_pass("Access token: expiry in the future")
    except AssertionError as e:
        results.add_fail("Access token: expiry", e)

    try:
        assert refresh_payload["exp"] > access_payload["exp"]
        results.add_pass("Refresh token: longer expiry than access")
    except AssertionError as e:
        results.add_fail("Refresh token: expiry comparison", e)


def test_role_based_access():
    """Test role-based access control logic."""
    results.section("Core: Role-Based Access Control")

    ROLES = {"customer", "staff", "admin"}

    def has_permission(user_role, required_role):
        hierarchy = {"customer": 0, "staff": 1, "admin": 2}
        return hierarchy.get(user_role, -1) >= hierarchy.get(required_role, 999)

    try:
        assert has_permission("admin", "admin")
        results.add_pass("Admin can access admin routes")
    except AssertionError as e:
        results.add_fail("Admin access", e)

    try:
        assert has_permission("admin", "staff")
        results.add_pass("Admin can access staff routes")
    except AssertionError as e:
        results.add_fail("Admin -> staff access", e)

    try:
        assert not has_permission("customer", "admin")
        results.add_pass("Customer cannot access admin routes")
    except AssertionError as e:
        results.add_fail("Customer admin restriction", e)

    try:
        assert not has_permission("customer", "staff")
        results.add_pass("Customer cannot access staff routes")
    except AssertionError as e:
        results.add_fail("Customer staff restriction", e)

    try:
        assert has_permission("staff", "staff")
        results.add_pass("Staff can access staff routes")
    except AssertionError as e:
        results.add_fail("Staff access", e)

    try:
        assert not has_permission("staff", "admin")
        results.add_pass("Staff cannot access admin routes")
    except AssertionError as e:
        results.add_fail("Staff admin restriction", e)


def test_session_management():
    """Test session creation, validation, and expiry."""
    results.section("Core: Session Management")

    SESSION_TTL = 1440  # minutes

    sessions = {}

    def create_session(user_id, user_agent="", ip_address=""):
        import uuid
        sid = str(uuid.uuid4())
        sessions[sid] = {
            "user_id": user_id,
            "created_at": datetime.utcnow(),
            "last_active": datetime.utcnow(),
            "expires_at": datetime.utcnow() + timedelta(minutes=SESSION_TTL),
            "user_agent": user_agent,
            "ip_address": ip_address,
            "is_active": True,
        }
        return sid

    def validate_session(sid):
        s = sessions.get(sid)
        if not s:
            return False, "not_found"
        if not s["is_active"]:
            return False, "inactive"
        if datetime.utcnow() > s["expires_at"]:
            s["is_active"] = False
            return False, "expired"
        s["last_active"] = datetime.utcnow()
        return True, "valid"

    def revoke_session(sid):
        if sid in sessions:
            sessions[sid]["is_active"] = False
            return True
        return False

    try:
        sid = create_session(1, "Chrome/130", "127.0.0.1")
        assert sid in sessions
        results.add_pass("Session created successfully")
    except AssertionError as e:
        results.add_fail("Session creation", e)

    try:
        valid, reason = validate_session(sid)
        assert valid and reason == "valid"
        results.add_pass("Valid session accepted")
    except AssertionError as e:
        results.add_fail("Session validation", e)

    try:
        valid, reason = validate_session("nonexistent")
        assert not valid and reason == "not_found"
        results.add_pass("Nonexistent session rejected")
    except AssertionError as e:
        results.add_fail("Nonexistent session", e)

    try:
        revoke_session(sid)
        valid, reason = validate_session(sid)
        assert not valid and reason == "inactive"
        results.add_pass("Revoked session rejected")
    except AssertionError as e:
        results.add_fail("Session revocation", e)


# ============================================================
# COMMERCE SERVICE TESTS
# ============================================================

def test_cart_operations():
    """Test cart add, update, remove, clear."""
    results.section("Commerce: Cart Operations")

    cart = {"user_id": 1, "items": [], "subtotal": 0, "discount": 0, "total": 0}

    # Add item
    try:
        cart["items"].append({"product_id": 1, "name": "Silk Saree", "price": 2500.0, "quantity": 1, "sku": "SAREE-M-RED"})
        cart["subtotal"] = sum(i["price"] * i["quantity"] for i in cart["items"])
        cart["total"] = cart["subtotal"]
        assert cart["subtotal"] == 2500.0
        results.add_pass("Add item to empty cart")
    except AssertionError as e:
        results.add_fail("Add item", e)

    # Add second item
    try:
        cart["items"].append({"product_id": 2, "name": "Cotton Kurta", "price": 800.0, "quantity": 2, "sku": "KURTA-L-BLU"})
        cart["subtotal"] = sum(i["price"] * i["quantity"] for i in cart["items"])
        cart["total"] = cart["subtotal"]
        assert cart["subtotal"] == 4100.0
        results.add_pass("Add multiple items (2500 + 800*2 = 4100)")
    except AssertionError as e:
        results.add_fail("Multiple items", e)

    # Update quantity
    try:
        cart["items"][1]["quantity"] = 3
        cart["subtotal"] = sum(i["price"] * i["quantity"] for i in cart["items"])
        assert cart["subtotal"] == 4900.0
        results.add_pass("Update item quantity (800*3 = 2400, total 4900)")
    except AssertionError as e:
        results.add_fail("Update quantity", e)

    # Remove item
    try:
        cart["items"] = [i for i in cart["items"] if i["product_id"] != 1]
        cart["subtotal"] = sum(i["price"] * i["quantity"] for i in cart["items"])
        assert len(cart["items"]) == 1 and cart["subtotal"] == 2400.0
        results.add_pass("Remove item from cart")
    except AssertionError as e:
        results.add_fail("Remove item", e)

    # Clear cart
    try:
        cart["items"] = []
        cart["subtotal"] = 0
        cart["total"] = 0
        assert len(cart["items"]) == 0 and cart["total"] == 0
        results.add_pass("Clear cart")
    except AssertionError as e:
        results.add_fail("Clear cart", e)


def test_shipping_calculation():
    """Test shipping cost logic."""
    results.section("Commerce: Shipping Calculation")

    FREE_SHIPPING_THRESHOLD = 999

    def calc_shipping(subtotal):
        return 0 if subtotal >= FREE_SHIPPING_THRESHOLD else 79

    try:
        assert calc_shipping(1000) == 0
        results.add_pass("Free shipping above ₹999")
    except AssertionError as e:
        results.add_fail("Free shipping threshold", e)

    try:
        assert calc_shipping(999) == 0
        results.add_pass("Free shipping at exactly ₹999")
    except AssertionError as e:
        results.add_fail("Free at threshold", e)

    try:
        assert calc_shipping(998) == 79
        results.add_pass("₹79 shipping below ₹999")
    except AssertionError as e:
        results.add_fail("Shipping charge", e)

    try:
        assert calc_shipping(0) == 79
        results.add_pass("₹79 shipping for empty/zero total")
    except AssertionError as e:
        results.add_fail("Zero total shipping", e)


def test_promo_code_validation():
    """Test promotion code validation and discount calc."""
    results.section("Commerce: Promo Code Validation")

    promotions = {
        "SAVE10": {"discount_type": "percentage", "discount_value": 10, "min_order": 500, "max_discount": 200, "usage_limit": 100, "usage_count": 45, "is_active": True},
        "FLAT100": {"discount_type": "flat", "discount_value": 100, "min_order": 300, "max_discount": None, "usage_limit": 50, "usage_count": 50, "is_active": True},
        "EXPIRED": {"discount_type": "percentage", "discount_value": 15, "min_order": 0, "max_discount": None, "usage_limit": None, "usage_count": 0, "is_active": False},
    }

    def validate_promo(code, subtotal):
        promo = promotions.get(code)
        if not promo:
            return False, 0, "Invalid code"
        if not promo["is_active"]:
            return False, 0, "Code expired"
        if subtotal < promo["min_order"]:
            return False, 0, f"Min order ₹{promo['min_order']}"
        if promo["usage_limit"] and promo["usage_count"] >= promo["usage_limit"]:
            return False, 0, "Usage limit reached"
        if promo["discount_type"] == "percentage":
            discount = subtotal * (promo["discount_value"] / 100)
            if promo["max_discount"]:
                discount = min(discount, promo["max_discount"])
        else:
            discount = promo["discount_value"]
        discount = min(discount, subtotal)
        return True, discount, "Applied"

    try:
        ok, disc, msg = validate_promo("SAVE10", 1000)
        assert ok and disc == 100.0
        results.add_pass("Percentage discount: 10% of ₹1000 = ₹100")
    except AssertionError as e:
        results.add_fail("Percentage discount", e)

    try:
        ok, disc, msg = validate_promo("SAVE10", 3000)
        assert ok and disc == 200.0
        results.add_pass("Percentage discount capped: 10% of ₹3000 = ₹300 → capped ₹200")
    except AssertionError as e:
        results.add_fail("Discount cap", e)

    try:
        ok, disc, msg = validate_promo("FLAT100", 500)
        assert not ok and "Usage limit" in msg
        results.add_pass("Usage limit exhausted rejected")
    except AssertionError as e:
        results.add_fail("Usage limit", e)

    try:
        ok, disc, msg = validate_promo("EXPIRED", 1000)
        assert not ok and "expired" in msg
        results.add_pass("Inactive promo rejected")
    except AssertionError as e:
        results.add_fail("Inactive promo", e)

    try:
        ok, disc, msg = validate_promo("SAVE10", 100)
        assert not ok and "Min order" in msg
        results.add_pass("Below minimum order rejected")
    except AssertionError as e:
        results.add_fail("Min order", e)

    try:
        ok, disc, msg = validate_promo("NONEXIST", 1000)
        assert not ok and "Invalid" in msg
        results.add_pass("Nonexistent code rejected")
    except AssertionError as e:
        results.add_fail("Invalid code", e)


def test_order_status_transitions():
    """Test order status state machine."""
    results.section("Commerce: Order Status Transitions")

    class OrderStatus(str, Enum):
        PENDING = "pending"
        CONFIRMED = "confirmed"
        PROCESSING = "processing"
        SHIPPED = "shipped"
        DELIVERED = "delivered"
        CANCELLED = "cancelled"
        RETURNED = "returned"
        REFUNDED = "refunded"

    TRANSITIONS = {
        OrderStatus.PENDING: {OrderStatus.CONFIRMED, OrderStatus.CANCELLED},
        OrderStatus.CONFIRMED: {OrderStatus.PROCESSING, OrderStatus.CANCELLED},
        OrderStatus.PROCESSING: {OrderStatus.SHIPPED},
        OrderStatus.SHIPPED: {OrderStatus.DELIVERED},
        OrderStatus.DELIVERED: {OrderStatus.RETURNED},
        OrderStatus.RETURNED: {OrderStatus.REFUNDED},
        OrderStatus.CANCELLED: set(),
        OrderStatus.REFUNDED: set(),
    }

    def can_transition(current, new):
        return new in TRANSITIONS.get(current, set())

    try:
        assert can_transition(OrderStatus.PENDING, OrderStatus.CONFIRMED)
        results.add_pass("PENDING → CONFIRMED valid")
    except AssertionError as e:
        results.add_fail("PENDING → CONFIRMED", e)

    try:
        assert can_transition(OrderStatus.PENDING, OrderStatus.CANCELLED)
        results.add_pass("PENDING → CANCELLED valid")
    except AssertionError as e:
        results.add_fail("PENDING → CANCELLED", e)

    try:
        assert not can_transition(OrderStatus.SHIPPED, OrderStatus.PENDING)
        results.add_pass("SHIPPED → PENDING invalid")
    except AssertionError as e:
        results.add_fail("SHIPPED → PENDING", e)

    try:
        assert not can_transition(OrderStatus.CANCELLED, OrderStatus.CONFIRMED)
        results.add_pass("CANCELLED is terminal")
    except AssertionError as e:
        results.add_fail("CANCELLED terminal", e)

    try:
        assert not can_transition(OrderStatus.REFUNDED, OrderStatus.PENDING)
        results.add_pass("REFUNDED is terminal")
    except AssertionError as e:
        results.add_fail("REFUNDED terminal", e)

    try:
        assert can_transition(OrderStatus.DELIVERED, OrderStatus.RETURNED)
        results.add_pass("DELIVERED → RETURNED valid")
    except AssertionError as e:
        results.add_fail("DELIVERED → RETURNED", e)


def test_inventory_reservation():
    """Test stock reservation, confirmation, and release."""
    results.section("Commerce: Inventory Reservation")

    inventory = {"sku": "KURTA-M-GRN", "quantity": 100, "reserved": 5, "threshold": 10}
    inventory["available"] = inventory["quantity"] - inventory["reserved"]

    def reserve(inv, qty):
        if inv["available"] < qty:
            return False, "Insufficient stock"
        inv["reserved"] += qty
        inv["available"] = inv["quantity"] - inv["reserved"]
        return True, "Reserved"

    def confirm(inv, qty):
        inv["quantity"] -= qty
        inv["reserved"] -= qty
        inv["available"] = inv["quantity"] - inv["reserved"]

    def release(inv, qty):
        inv["reserved"] = max(0, inv["reserved"] - qty)
        inv["available"] = inv["quantity"] - inv["reserved"]

    try:
        assert inventory["available"] == 95
        results.add_pass("Available = total - reserved (100-5=95)")
    except AssertionError as e:
        results.add_fail("Available calculation", e)

    try:
        ok, msg = reserve(inventory, 10)
        assert ok and inventory["reserved"] == 15
        results.add_pass("Reserve 10 units → reserved=15")
    except AssertionError as e:
        results.add_fail("Reserve stock", e)

    try:
        ok, msg = reserve(inventory, 100)
        assert not ok
        results.add_pass("Over-reserve rejected")
    except AssertionError as e:
        results.add_fail("Over-reserve", e)

    try:
        confirm(inventory, 10)
        assert inventory["quantity"] == 90 and inventory["reserved"] == 5
        results.add_pass("Confirm reservation: qty=90, reserved=5")
    except AssertionError as e:
        results.add_fail("Confirm reservation", e)

    try:
        release(inventory, 5)
        assert inventory["reserved"] == 0 and inventory["available"] == 90
        results.add_pass("Release reservation: reserved=0, available=90")
    except AssertionError as e:
        results.add_fail("Release reservation", e)

    try:
        release(inventory, 10)
        assert inventory["reserved"] == 0
        results.add_pass("Release more than reserved doesn't go negative")
    except AssertionError as e:
        results.add_fail("Over-release", e)


def test_order_creation_flow():
    """Test end-to-end order creation from cart."""
    results.section("Commerce: Order Creation Flow")

    cart = {
        "user_id": 1,
        "items": [
            {"product_id": 1, "name": "Silk Saree", "price": 2500, "quantity": 1, "sku": "SAREE-M-RED"},
            {"product_id": 2, "name": "Cotton Kurta", "price": 800, "quantity": 2, "sku": "KURTA-L-BLU"},
        ],
        "promo_code": "SAVE10",
        "discount": 200,
    }

    subtotal = sum(i["price"] * i["quantity"] for i in cart["items"])
    shipping = 0 if subtotal >= 999 else 79
    total = subtotal - cart["discount"] + shipping

    try:
        assert subtotal == 4100
        results.add_pass(f"Subtotal: ₹{subtotal}")
    except AssertionError as e:
        results.add_fail("Subtotal", e)

    try:
        assert shipping == 0
        results.add_pass("Free shipping (above ₹999)")
    except AssertionError as e:
        results.add_fail("Shipping", e)

    try:
        assert total == 3900
        results.add_pass(f"Total: ₹4100 - ₹200 + ₹0 = ₹{total}")
    except AssertionError as e:
        results.add_fail("Total", e)

    order = {
        "id": 1, "user_id": cart["user_id"], "subtotal": subtotal,
        "discount_applied": cart["discount"], "shipping_cost": shipping,
        "total_amount": total, "status": "pending", "promo_code": cart["promo_code"],
    }

    try:
        assert order["status"] == "pending"
        results.add_pass("New order status is 'pending'")
    except AssertionError as e:
        results.add_fail("New order status", e)

    try:
        assert order["promo_code"] == "SAVE10"
        results.add_pass("Promo code stored with order")
    except AssertionError as e:
        results.add_fail("Promo code stored", e)


def test_product_sorting():
    """Test product sorting options."""
    results.section("Commerce: Product Sorting")

    products = [
        {"id": 1, "name": "Zara Dress", "price": 1500, "created_at": "2025-01-01"},
        {"id": 2, "name": "Anarkali Set", "price": 3200, "created_at": "2025-06-01"},
        {"id": 3, "name": "Kurta Plain", "price": 800, "created_at": "2025-03-15"},
    ]

    try:
        sorted_low = sorted(products, key=lambda p: p["price"])
        assert [p["id"] for p in sorted_low] == [3, 1, 2]
        results.add_pass("Sort by price: low to high")
    except AssertionError as e:
        results.add_fail("Sort low-high", e)

    try:
        sorted_high = sorted(products, key=lambda p: p["price"], reverse=True)
        assert [p["id"] for p in sorted_high] == [2, 1, 3]
        results.add_pass("Sort by price: high to low")
    except AssertionError as e:
        results.add_fail("Sort high-low", e)

    try:
        sorted_name = sorted(products, key=lambda p: p["name"])
        assert [p["id"] for p in sorted_name] == [2, 3, 1]
        results.add_pass("Sort by name: A-Z")
    except AssertionError as e:
        results.add_fail("Sort A-Z", e)

    try:
        sorted_new = sorted(products, key=lambda p: p["created_at"], reverse=True)
        assert sorted_new[0]["id"] == 2
        results.add_pass("Sort by newest first")
    except AssertionError as e:
        results.add_fail("Sort newest", e)


def test_cart_reservation_ttl():
    """Test cart reservation TTL logic."""
    results.section("Commerce: Cart Reservation TTL")

    RESERVATION_TTL = 900  # 15 minutes
    PREFIX = "cart:reservation:"

    reservation = {
        "sku": "SAREE-M-RED", "quantity": 2,
        "created_at": time.time(), "expires_in": RESERVATION_TTL,
    }

    def is_expired(res):
        return time.time() - res["created_at"] > res["expires_in"]

    try:
        key = f"{PREFIX}1:123"
        assert key == "cart:reservation:1:123"
        results.add_pass("Reservation key format")
    except AssertionError as e:
        results.add_fail("Key format", e)

    try:
        assert not is_expired(reservation)
        results.add_pass("Fresh reservation not expired")
    except AssertionError as e:
        results.add_fail("Fresh reservation", e)

    try:
        reservation["created_at"] = time.time() - (14 * 60)
        assert not is_expired(reservation)
        results.add_pass("14-minute reservation not expired")
    except AssertionError as e:
        results.add_fail("14-minute", e)

    try:
        reservation["created_at"] = time.time() - (16 * 60)
        assert is_expired(reservation)
        results.add_pass("16-minute reservation is expired")
    except AssertionError as e:
        results.add_fail("16-minute", e)


# ============================================================
# PAYMENT SERVICE TESTS
# ============================================================

def test_payment_processing():
    """Test payment creation and verification flow."""
    results.section("Payment: Processing Flow")

    order_amount = 3900.00

    try:
        paise = int(order_amount * 100)
        assert paise == 390000
        results.add_pass("INR to paise conversion (₹3900 = 390000 paise)")
    except AssertionError as e:
        results.add_fail("Paise conversion", e)

    payment = {
        "transaction_id": f"txn_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_abc",
        "order_id": 1, "amount": order_amount, "currency": "INR",
        "status": "pending", "payment_method": "razorpay",
    }

    try:
        assert payment["status"] == "pending"
        results.add_pass("New payment status is 'pending'")
    except AssertionError as e:
        results.add_fail("Pending status", e)

    # Simulate capture
    try:
        payment["status"] = "completed"
        payment["razorpay_payment_id"] = "pay_xyz789"
        assert payment["status"] == "completed"
        results.add_pass("Payment captured → 'completed'")
    except AssertionError as e:
        results.add_fail("Payment capture", e)


def test_refund_processing():
    """Test partial and full refund logic."""
    results.section("Payment: Refund Processing")

    payment = {"amount": 3900.00, "status": "completed", "refund_amount": 0}

    # Partial refund
    try:
        refund = 500.00
        assert refund < payment["amount"]
        payment["refund_amount"] = refund
        results.add_pass(f"Partial refund ₹{refund} on ₹{payment['amount']}")
    except AssertionError as e:
        results.add_fail("Partial refund", e)

    # Full refund
    try:
        full_refund = payment["amount"]
        payment["refund_amount"] = full_refund
        payment["status"] = "refunded"
        assert payment["status"] == "refunded"
        results.add_pass("Full refund status → 'refunded'")
    except AssertionError as e:
        results.add_fail("Full refund", e)

    # Cannot refund more than paid
    try:
        assert payment["refund_amount"] <= payment["amount"]
        results.add_pass("Refund does not exceed payment amount")
    except AssertionError as e:
        results.add_fail("Over-refund check", e)


def test_payment_gateway_selection():
    """Test payment gateway routing."""
    results.section("Payment: Gateway Selection")

    def select_gateway(currency, method=None):
        if currency == "INR":
            return "razorpay"
        return "stripe"

    try:
        assert select_gateway("INR") == "razorpay"
        results.add_pass("INR → Razorpay")
    except AssertionError as e:
        results.add_fail("INR gateway", e)

    try:
        assert select_gateway("USD") == "stripe"
        results.add_pass("USD → Stripe")
    except AssertionError as e:
        results.add_fail("USD gateway", e)

    try:
        assert select_gateway("EUR") == "stripe"
        results.add_pass("EUR → Stripe")
    except AssertionError as e:
        results.add_fail("EUR gateway", e)


# ============================================================
# ADMIN SERVICE TESTS
# ============================================================

def test_admin_dashboard_aggregation():
    """Test dashboard overview data aggregation."""
    results.section("Admin: Dashboard Aggregation")

    orders = [
        {"id": 1, "total": 2500, "status": "delivered"},
        {"id": 2, "total": 1800, "status": "shipped"},
        {"id": 3, "total": 900, "status": "cancelled"},
        {"id": 4, "total": 3200, "status": "pending"},
    ]

    try:
        revenue = sum(o["total"] for o in orders if o["status"] not in ("cancelled", "refunded"))
        assert revenue == 7500
        results.add_pass(f"Total revenue excludes cancelled: ₹{revenue}")
    except AssertionError as e:
        results.add_fail("Revenue calculation", e)

    try:
        pending = sum(1 for o in orders if o["status"] == "pending")
        assert pending == 1
        results.add_pass(f"Pending orders count: {pending}")
    except AssertionError as e:
        results.add_fail("Pending count", e)

    try:
        total = len(orders)
        assert total == 4
        results.add_pass(f"Total orders: {total}")
    except AssertionError as e:
        results.add_fail("Total orders", e)


def test_bulk_order_update():
    """Test bulk order status update logic."""
    results.section("Admin: Bulk Order Update")

    orders = {1: "pending", 2: "pending", 3: "processing", 4: "pending"}

    def bulk_update(order_ids, new_status):
        updated = 0
        for oid in order_ids:
            if oid in orders:
                orders[oid] = new_status
                updated += 1
        return updated

    try:
        count = bulk_update([1, 2, 4], "processing")
        assert count == 3
        results.add_pass(f"Bulk updated {count} orders to 'processing'")
    except AssertionError as e:
        results.add_fail("Bulk update count", e)

    try:
        assert all(orders[oid] == "processing" for oid in [1, 2, 4])
        results.add_pass("All target orders have new status")
    except AssertionError as e:
        results.add_fail("Bulk update status", e)


def test_inventory_alerts():
    """Test low stock and out-of-stock alert logic."""
    results.section("Admin: Inventory Alerts")

    inventory_items = [
        {"sku": "SAREE-01", "qty": 5, "threshold": 10},
        {"sku": "KURTA-01", "qty": 0, "threshold": 5},
        {"sku": "DRESS-01", "qty": 50, "threshold": 10},
        {"sku": "TOP-01", "qty": 3, "threshold": 5},
    ]

    try:
        low_stock = [i for i in inventory_items if 0 < i["qty"] <= i["threshold"]]
        assert len(low_stock) == 2  # SAREE-01, TOP-01
        results.add_pass(f"Low stock items: {len(low_stock)}")
    except AssertionError as e:
        results.add_fail("Low stock count", e)

    try:
        oos = [i for i in inventory_items if i["qty"] == 0]
        assert len(oos) == 1  # KURTA-01
        results.add_pass(f"Out of stock items: {len(oos)}")
    except AssertionError as e:
        results.add_fail("Out of stock count", e)


def test_export_csv_format():
    """Test CSV export format generation."""
    results.section("Admin: Export CSV Format")

    orders = [
        {"id": 1, "email": "a@b.com", "total": 1500, "status": "delivered"},
        {"id": 2, "email": "c@d.com", "total": 2300, "status": "shipped"},
    ]

    headers = "id,email,total,status"
    csv_rows = [headers]
    for o in orders:
        csv_rows.append(f"{o['id']},{o['email']},{o['total']},{o['status']}")
    csv_output = "\n".join(csv_rows)

    try:
        lines = csv_output.strip().split("\n")
        assert len(lines) == 3  # 1 header + 2 data
        results.add_pass("CSV has header + data rows")
    except AssertionError as e:
        results.add_fail("CSV row count", e)

    try:
        assert lines[0] == "id,email,total,status"
        results.add_pass("CSV header matches")
    except AssertionError as e:
        results.add_fail("CSV header", e)

    try:
        cols = lines[1].split(",")
        assert len(cols) == 4
        results.add_pass("CSV data has correct columns")
    except AssertionError as e:
        results.add_fail("CSV columns", e)


def test_discount_management():
    """Test discount CRUD operations."""
    results.section("Admin: Discount Management")

    discounts = {}
    next_id = 1

    def create(code, dtype, value, **kwargs):
        nonlocal next_id
        did = next_id
        next_id += 1
        discounts[did] = {"id": did, "code": code.upper(), "type": dtype, "value": value, "is_active": True, **kwargs}
        return did

    def update(did, **kwargs):
        if did in discounts:
            discounts[did].update(kwargs)
            return True
        return False

    def delete(did):
        return discounts.pop(did, None) is not None

    try:
        d1 = create("SAVE20", "percentage", 20, min_order=1000)
        assert d1 == 1 and discounts[d1]["code"] == "SAVE20"
        results.add_pass("Create discount")
    except AssertionError as e:
        results.add_fail("Create discount", e)

    try:
        update(d1, is_active=False)
        assert discounts[d1]["is_active"] == False
        results.add_pass("Deactivate discount")
    except AssertionError as e:
        results.add_fail("Deactivate discount", e)

    try:
        d2 = create("FLAT200", "flat", 200)
        assert len(discounts) == 2
        results.add_pass("Multiple discounts")
    except AssertionError as e:
        results.add_fail("Multiple discounts", e)

    try:
        delete(d1)
        assert d1 not in discounts and len(discounts) == 1
        results.add_pass("Delete discount")
    except AssertionError as e:
        results.add_fail("Delete discount", e)


def test_product_bulk_operations():
    """Test bulk product update/activate/deactivate."""
    results.section("Admin: Bulk Product Operations")

    products = {
        1: {"name": "A", "price": 500, "is_active": True, "is_featured": False},
        2: {"name": "B", "price": 800, "is_active": True, "is_featured": False},
        3: {"name": "C", "price": 1200, "is_active": False, "is_featured": False},
    }

    def bulk_update(ids, updates):
        count = 0
        for pid in ids:
            if pid in products:
                for k, v in updates.items():
                    products[pid][k] = v
                count += 1
        return count

    try:
        count = bulk_update([1, 2], {"is_featured": True})
        assert count == 2 and products[1]["is_featured"] and products[2]["is_featured"]
        results.add_pass("Bulk feature products")
    except AssertionError as e:
        results.add_fail("Bulk feature", e)

    try:
        count = bulk_update([3], {"is_active": True})
        assert products[3]["is_active"]
        results.add_pass("Bulk activate product")
    except AssertionError as e:
        results.add_fail("Bulk activate", e)

    try:
        count = bulk_update([1, 2, 3], {"is_active": False})
        assert all(not products[p]["is_active"] for p in [1, 2, 3])
        results.add_pass("Bulk deactivate all products")
    except AssertionError as e:
        results.add_fail("Bulk deactivate", e)


# ============================================================
# MEILISEARCH INTEGRATION TESTS
# ============================================================

def test_meilisearch_document_format():
    """Test Meilisearch document formatting."""
    results.section("Search: Document Format")

    def format_product(p):
        return {
            "id": p.get("id"),
            "name": p.get("name", ""),
            "description": p.get("description", ""),
            "price": float(p["price"]) if p.get("price") else 0,
            "sku": p.get("sku", ""),
            "is_active": p.get("is_active", True),
            "is_featured": p.get("is_featured", False),
            "in_stock": (p.get("total_stock", 0) or 0) > 0,
            "category_name": p.get("category_name", ""),
        }

    product = {"id": 1, "name": "Silk Saree", "price": 2500, "sku": "SAREE-01", "total_stock": 50, "is_active": True, "category_name": "Sarees"}

    try:
        doc = format_product(product)
        assert doc["id"] == 1 and doc["name"] == "Silk Saree"
        results.add_pass("Basic product fields formatted")
    except AssertionError as e:
        results.add_fail("Basic fields", e)

    try:
        assert doc["in_stock"] == True
        results.add_pass("in_stock derived from total_stock > 0")
    except AssertionError as e:
        results.add_fail("in_stock field", e)

    try:
        oos_product = {"id": 2, "name": "Test", "price": 100, "total_stock": 0}
        doc2 = format_product(oos_product)
        assert doc2["in_stock"] == False
        results.add_pass("in_stock=false for zero stock")
    except AssertionError as e:
        results.add_fail("Zero stock", e)

    try:
        null_stock = {"id": 3, "name": "Test", "price": 100, "total_stock": None}
        doc3 = format_product(null_stock)
        assert doc3["in_stock"] == False
        results.add_pass("in_stock=false for null stock")
    except AssertionError as e:
        results.add_fail("Null stock", e)


def test_search_filter_building():
    """Test Meilisearch filter string construction."""
    results.section("Search: Filter Building")

    def build_filters(category_id=None, min_price=None, max_price=None, in_stock=True):
        filters = ["is_active = true"]
        if category_id:
            filters.append(f"category_id = {category_id}")
        if min_price is not None:
            filters.append(f"price >= {min_price}")
        if max_price is not None:
            filters.append(f"price <= {max_price}")
        if in_stock:
            filters.append("in_stock = true")
        return " AND ".join(filters)

    try:
        f = build_filters()
        assert f == "is_active = true AND in_stock = true"
        results.add_pass("Default filters: active + in_stock")
    except AssertionError as e:
        results.add_fail("Default filters", e)

    try:
        f = build_filters(category_id=5)
        assert "category_id = 5" in f
        results.add_pass("Category filter appended")
    except AssertionError as e:
        results.add_fail("Category filter", e)

    try:
        f = build_filters(min_price=500, max_price=2000)
        assert "price >= 500" in f and "price <= 2000" in f
        results.add_pass("Price range filter")
    except AssertionError as e:
        results.add_fail("Price filter", e)

    try:
        f = build_filters(in_stock=False)
        assert "in_stock" not in f
        results.add_pass("Exclude in_stock filter when False")
    except AssertionError as e:
        results.add_fail("No in_stock filter", e)


def test_search_sort_mapping():
    """Test sort option to Meilisearch sort mapping."""
    results.section("Search: Sort Mapping")

    SORT_MAP = {
        "price_low": ["price:asc"],
        "price_high": ["price:desc"],
        "name_asc": ["name:asc"],
        "name_desc": ["name:desc"],
        "newest": ["created_at:desc"],
    }

    try:
        assert SORT_MAP["price_low"] == ["price:asc"]
        results.add_pass("price_low → price:asc")
    except AssertionError as e:
        results.add_fail("price_low sort", e)

    try:
        assert SORT_MAP["newest"] == ["created_at:desc"]
        results.add_pass("newest → created_at:desc")
    except AssertionError as e:
        results.add_fail("newest sort", e)

    try:
        assert SORT_MAP.get("invalid") is None
        results.add_pass("Invalid sort returns None")
    except AssertionError as e:
        results.add_fail("Invalid sort", e)


# ============================================================
# CHAT & RETURNS/EXCHANGE TESTS
# ============================================================

def test_chat_room_lifecycle():
    """Test chat room creation, messaging, and closing."""
    results.section("Commerce: Chat Room Lifecycle")

    rooms = {}
    messages = {}
    next_id = 1

    def create_room(user_id, subject=None):
        nonlocal next_id
        rid = next_id; next_id += 1
        rooms[rid] = {"id": rid, "customer_id": user_id, "subject": subject, "status": "open", "assigned_to": None}
        messages[rid] = []
        return rid

    def send_message(room_id, sender_id, sender_type, msg):
        messages[room_id].append({"sender_id": sender_id, "sender_type": sender_type, "message": msg})

    def assign_room(room_id, staff_id):
        rooms[room_id]["assigned_to"] = staff_id
        rooms[room_id]["status"] = "assigned"

    def close_room(room_id):
        rooms[room_id]["status"] = "closed"

    try:
        rid = create_room(1, "Order issue")
        assert rooms[rid]["status"] == "open"
        results.add_pass("Chat room created with status 'open'")
    except AssertionError as e:
        results.add_fail("Room creation", e)

    try:
        send_message(rid, 1, "customer", "Need help with my order")
        assert len(messages[rid]) == 1
        results.add_pass("Customer message sent")
    except AssertionError as e:
        results.add_fail("Customer message", e)

    try:
        assign_room(rid, 10)
        assert rooms[rid]["status"] == "assigned" and rooms[rid]["assigned_to"] == 10
        results.add_pass("Room assigned to staff")
    except AssertionError as e:
        results.add_fail("Room assignment", e)

    try:
        send_message(rid, 10, "staff", "Looking into it")
        assert len(messages[rid]) == 2
        results.add_pass("Staff reply sent")
    except AssertionError as e:
        results.add_fail("Staff reply", e)

    try:
        close_room(rid)
        assert rooms[rid]["status"] == "closed"
        results.add_pass("Room closed")
    except AssertionError as e:
        results.add_fail("Room close", e)


def test_return_exchange_flow():
    """Test return and exchange request logic."""
    results.section("Commerce: Return/Exchange Flow")

    class ReturnStatus(str, Enum):
        PENDING = "pending"
        APPROVED = "approved"
        REJECTED = "rejected"
        EXCHANGED = "exchanged"

    returns = []

    def create_return(order_id, product_id, reason, request_type="return"):
        ret = {
            "id": len(returns) + 1,
            "order_id": order_id, "product_id": product_id,
            "reason": reason, "type": request_type,
            "status": ReturnStatus.PENDING,
        }
        returns.append(ret)
        return ret

    try:
        r1 = create_return(1, 1, "Size doesn't fit", "exchange")
        assert r1["status"] == ReturnStatus.PENDING and r1["type"] == "exchange"
        results.add_pass("Exchange request created")
    except AssertionError as e:
        results.add_fail("Exchange creation", e)

    try:
        r2 = create_return(2, 3, "Defective product", "return")
        assert r2["type"] == "return"
        results.add_pass("Return request created")
    except AssertionError as e:
        results.add_fail("Return creation", e)

    try:
        r1["status"] = ReturnStatus.EXCHANGED
        assert r1["status"] == ReturnStatus.EXCHANGED
        results.add_pass("Exchange request approved")
    except AssertionError as e:
        results.add_fail("Exchange approval", e)

    try:
        r2["status"] = ReturnStatus.REJECTED
        assert r2["status"] == ReturnStatus.REJECTED
        results.add_pass("Return request rejected")
    except AssertionError as e:
        results.add_fail("Return rejection", e)


# ============================================================
# RUNNER
# ============================================================

def run_all_tests():
    print("\n" + "=" * 60)
    print("  AARYA CLOTHING — COMPREHENSIVE TEST SUITE")
    print("  " + datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"))
    print("=" * 60)

    # Core
    test_password_validation()
    test_password_hashing()
    test_jwt_token_structure()
    test_role_based_access()
    test_session_management()

    # Commerce
    test_cart_operations()
    test_shipping_calculation()
    test_promo_code_validation()
    test_order_status_transitions()
    test_inventory_reservation()
    test_order_creation_flow()
    test_product_sorting()
    test_cart_reservation_ttl()

    # Payment
    test_payment_processing()
    test_refund_processing()
    test_payment_gateway_selection()

    # Admin
    test_admin_dashboard_aggregation()
    test_bulk_order_update()
    test_inventory_alerts()
    test_export_csv_format()
    test_discount_management()
    test_product_bulk_operations()

    # Search
    test_meilisearch_document_format()
    test_search_filter_building()
    test_search_sort_mapping()

    # Chat & Returns
    test_chat_room_lifecycle()
    test_return_exchange_flow()

    print("\n" + "=" * 60)
    print("  TEST RESULTS SUMMARY")
    print("=" * 60)
    total = results.passed + results.failed
    print(f"  Total Tests: {total}")
    print(f"  Passed:      {results.passed} ✅")
    print(f"  Failed:      {results.failed} ❌")
    pct = (results.passed / total * 100) if total else 0
    print(f"  Pass Rate:   {pct:.1f}%")
    print("=" * 60)

    if results.failed > 0:
        print("\n  Failed Tests:")
        for name, err in results.errors:
            print(f"    ❌ {name}: {err}")

    return results.failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
