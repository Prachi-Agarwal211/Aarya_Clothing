"""Inventory service for stock management."""
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_
from fastapi import HTTPException, status

from models.inventory import Inventory
from models.product import Product
from schemas.inventory import InventoryCreate, InventoryUpdate, LowStockItem


class InventoryService:
    """Service for inventory management operations."""
    
    def __init__(self, db: Session):
        """Initialize inventory service."""
        self.db = db
    
    def get_inventory_by_sku(self, sku: str) -> Optional[Inventory]:
        """Get inventory by SKU."""
        return self.db.query(Inventory).filter(Inventory.sku == sku).first()
    
    def get_inventory_by_sku_for_update(self, sku: str) -> Optional[Inventory]:
        """Get inventory by SKU with pessimistic locking."""
        return self.db.query(Inventory).filter(
            Inventory.sku == sku
        ).with_for_update().first()
    
    def get_product_inventory(self, product_id: int) -> List[Inventory]:
        """Get all inventory for a product."""
        return self.db.query(Inventory).filter(Inventory.product_id == product_id).all()
    
    def create_inventory(self, inventory_data: InventoryCreate) -> Inventory:
        """Create new inventory record."""
        # Validate product exists
        product = self.db.query(Product).filter(Product.id == inventory_data.product_id).first()
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product with ID {inventory_data.product_id} not found"
            )
        
        # Check SKU uniqueness
        existing = self.get_inventory_by_sku(inventory_data.sku)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Inventory with SKU '{inventory_data.sku}' already exists"
            )
        
        inventory = Inventory(**inventory_data.model_dump())
        self.db.add(inventory)
        self.db.commit()
        self.db.refresh(inventory)
        return inventory
    
    def update_inventory(self, inventory_id: int, inventory_data: InventoryUpdate) -> Inventory:
        """Update inventory."""
        inventory = self.db.query(Inventory).filter(Inventory.id == inventory_id).first()
        if not inventory:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Inventory with ID {inventory_id} not found"
            )
        
        update_data = inventory_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(inventory, field, value)
        
        self.db.commit()
        self.db.refresh(inventory)
        return inventory
    
    def adjust_stock(self, sku: str, adjustment: int, reason: str = "") -> Inventory:
        """Adjust inventory stock."""
        inventory = self.get_inventory_by_sku(sku)
        if not inventory:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Inventory with SKU '{sku}' not found"
            )
        
        new_quantity = inventory.quantity + adjustment
        if new_quantity < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Stock cannot be negative"
            )
        
        inventory.quantity = new_quantity
        self.db.commit()
        self.db.refresh(inventory)
        return inventory
    
    def reserve_stock(self, sku: str, quantity: int) -> bool:
        """Reserve stock for an order with pessimistic locking."""
        inventory = self.get_inventory_by_sku_for_update(sku)
        if not inventory:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Inventory with SKU '{sku}' not found"
            )
        
        if inventory.available_quantity < quantity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Insufficient stock. Available: {inventory.available_quantity}, Requested: {quantity}"
            )
        
        inventory.reserved_quantity += quantity
        self.db.commit()
        return True
    
    def release_stock(self, sku: str, quantity: int) -> bool:
        """Release reserved stock with pessimistic locking."""
        inventory = self.get_inventory_by_sku_for_update(sku)
        if not inventory:
            return False
        
        inventory.reserved_quantity = max(0, inventory.reserved_quantity - quantity)
        self.db.commit()
        return True
    
    def confirm_reservation(self, sku: str, quantity: int) -> bool:
        """Confirm reservation and reduce actual stock with pessimistic locking."""
        inventory = self.get_inventory_by_sku_for_update(sku)
        if not inventory:
            return False
        
        inventory.quantity -= quantity
        inventory.reserved_quantity -= quantity
        
        # Ensure no negative values
        inventory.quantity = max(0, inventory.quantity)
        inventory.reserved_quantity = max(0, inventory.reserved_quantity)
        
        self.db.commit()
        return True
    
    def get_low_stock_items(self) -> List[LowStockItem]:
        """Get all low stock items."""
        low_stock = self.db.query(Inventory).filter(
            Inventory.quantity - Inventory.reserved_quantity <= Inventory.low_stock_threshold
        ).all()
        
        items = []
        for inv in low_stock:
            product = self.db.query(Product).filter(Product.id == inv.product_id).first()
            if product:
                items.append(LowStockItem(
                    product_id=inv.product_id,
                    product_name=product.name,
                    sku=inv.sku,
                    size=inv.size,
                    color=inv.color,
                    available_quantity=inv.available_quantity,
                    low_stock_threshold=inv.low_stock_threshold
                ))
        
        return items
