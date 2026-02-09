"""
Pytest configuration and shared fixtures for Aarya Clothing tests.
"""
import pytest
from unittest.mock import MagicMock, patch
import sys
import os

# Add services to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'services', 'commerce'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'services', 'core'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'services', 'payment'))


@pytest.fixture
def mock_db():
    """Create a mock database session."""
    return MagicMock()


@pytest.fixture
def mock_redis():
    """Create a mock Redis client."""
    return MagicMock()


@pytest.fixture
def sample_user():
    """Create a sample user for testing."""
    user = MagicMock()
    user.id = 1
    user.email = "test@example.com"
    user.username = "testuser"
    user.full_name = "Test User"
    user.hashed_password = "hashed_password"
    user.role.value = "customer"
    user.is_active = True
    return user


@pytest.fixture
def sample_product():
    """Create a sample product for testing."""
    product = MagicMock()
    product.id = 1
    product.name = "Test Shirt"
    product.price = 500.00
    product.is_active = True
    product.is_featured = False
    product.is_new_arrival = True
    return product


@pytest.fixture
def sample_cart():
    """Create a sample cart for testing."""
    return {
        "user_id": 1,
        "items": [
            {
                "product_id": 1,
                "name": "Test Shirt",
                "price": 500.00,
                "quantity": 2,
                "sku": "SHIRT-M-BLK"
            }
        ],
        "subtotal": 1000.00,
        "discount": 0,
        "total": 1000.00
    }


@pytest.fixture
def sample_order():
    """Create a sample order for testing."""
    order = MagicMock()
    order.id = 1
    order.user_id = 1
    order.subtotal = 1000.00
    order.discount_applied = 0
    order.shipping_cost = 50.00
    order.total_amount = 1050.00
    order.status.value = "pending"
    order.transaction_id = "txn_123"
    return order


@pytest.fixture
def sample_inventory():
    """Create sample inventory for testing."""
    inventory = MagicMock()
    inventory.id = 1
    inventory.product_id = 1
    inventory.sku = "SHIRT-M-BLK"
    inventory.quantity = 100
    inventory.reserved_quantity = 5
    inventory.low_stock_threshold = 10
    
    @property
    def available_quantity(self):
        return self.quantity - self.reserved_quantity
    
    inventory.available_quantity = property(available_quantity)
    return inventory
