from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_

from models.product import Product, Category
from schemas.product import ProductCreate, ProductUpdate

class ProductService:
    def __init__(self, db: Session):
        self.db = db

    def get_product(self, product_id: int) -> Optional[Product]:
        """Get product by ID"""
        return self.db.query(Product).filter(Product.id == product_id).first()

    def get_products(self, skip: int = 0, limit: int = 100, category: str = None) -> List[Product]:
        """Get all products with optional category filtering"""
        query = self.db.query(Product).filter(Product.is_active == True)
        
        if category:
            query = query.filter(Product.category == category)
        
        return query.offset(skip).limit(limit).all()

    def create_product(self, product: ProductCreate) -> Product:
        """Create a new product"""
        db_product = Product(**product.model_dump())
        self.db.add(db_product)
        self.db.commit()
        self.db.refresh(db_product)
        return db_product

    def update_product(self, product_id: int, product_update: ProductUpdate) -> Optional[Product]:
        """Update product information"""
        product = self.get_product(product_id)
        if not product:
            return None
        
        update_data = product_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(product, field, value)
        
        self.db.commit()
        self.db.refresh(product)
        return product

    def delete_product(self, product_id: int) -> bool:
        """Delete product (soft delete by setting is_active=False)"""
        product = self.get_product(product_id)
        if not product:
            return False
        
        product.is_active = False
        self.db.commit()
        return True

    def get_categories(self) -> List[Category]:
        """Get all active categories"""
        return self.db.query(Category).filter(Category.is_active == True).all()

    def create_category(self, name: str, description: str = None) -> Category:
        """Create a new category"""
        db_category = Category(name=name, description=description)
        self.db.add(db_category)
        self.db.commit()
        self.db.refresh(db_category)
        return db_category
