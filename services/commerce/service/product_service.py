"""Product service for managing product operations."""
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from fastapi import HTTPException, status
from decimal import Decimal

from models.product import Product
from models.category import Category
from schemas.product import ProductCreate, ProductUpdate


class ProductService:
    """Service for product management operations."""
    
    def __init__(self, db: Session):
        """Initialize product service."""
        self.db = db
    
    def get_products(
        self,
        skip: int = 0,
        limit: int = 100,
        category_id: Optional[int] = None,
        new_arrivals: bool = False,
        featured: bool = False,
        active_only: bool = True,
        min_price: Optional[Decimal] = None,
        max_price: Optional[Decimal] = None
    ) -> List[Product]:
        """Get products with filtering options."""
        query = self.db.query(Product)
        
        if active_only:
            query = query.filter(Product.is_active == True)
        
        if category_id:
            query = query.filter(Product.category_id == category_id)
        
        if new_arrivals:
            query = query.filter(Product.is_new_arrival == True)
        
        if featured:
            query = query.filter(Product.is_featured == True)
        
        if min_price is not None:
            query = query.filter(Product.price >= min_price)
        
        if max_price is not None:
            query = query.filter(Product.price <= max_price)
        
        return query.offset(skip).limit(limit).all()
    
    def get_product_by_id(self, product_id: int, active_only: bool = True) -> Optional[Product]:
        """Get product by ID."""
        query = self.db.query(Product).filter(Product.id == product_id)
        
        if active_only:
            query = query.filter(Product.is_active == True)
        
        return query.first()
    
    def get_product_by_slug(self, slug: str, active_only: bool = True) -> Optional[Product]:
        """Get product by slug."""
        query = self.db.query(Product).filter(Product.slug == slug)
        
        if active_only:
            query = query.filter(Product.is_active == True)
        
        return query.first()
    
    def create_product(self, product_data: ProductCreate) -> Product:
        """Create a new product."""
        # Validate category exists if provided
        if product_data.category_id:
            category = self.db.query(Category).filter(
                Category.id ==product_data.category_id
            ).first()
            if not category:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Category not found"
                )
        
        # Check slug uniqueness if provided
        if product_data.slug:
            existing = self.db.query(Product).filter(
                Product.slug == product_data.slug
            ).first()
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Product with slug '{product_data.slug}' already exists"
                )
        
        product = Product(**product_data.model_dump())
        self.db.add(product)
        self.db.commit()
        self.db.refresh(product)
        
        return product
    
    def update_product(self, product_id: int, product_data: ProductUpdate) -> Product:
        """Update a product."""
        product = self.db.query(Product).filter(Product.id == product_id).first()
        
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found"
            )
        
        # Validate category if being updated
        if product_data.category_id is not None:
            category = self.db.query(Category).filter(
                Category.id == product_data.category_id
            ).first()
            if not category:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Category not found"
                )
        
        # Check slug uniqueness if being updated
        if product_data.slug and product_data.slug != product.slug:
            existing = self.db.query(Product).filter(
                Product.slug == product_data.slug
            ).first()
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Product with slug '{product_data.slug}' already exists"
                )
        
        update_data = product_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(product, field, value)
        
        self.db.commit()
        self.db.refresh(product)
        
        return product
    
    def delete_product(self, product_id: int) -> bool:
        """Delete a product (soft delete by setting is_active=False)."""
        product = self.db.query(Product).filter(Product.id == product_id).first()
        
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found"
            )
        
        # Soft delete
        product.is_active = False
        self.db.commit()
        
        return True
    
    def search_products(
        self,
        query: str,
        skip: int = 0,
        limit: int = 50
    ) -> List[Product]:
        """
        Search products by name or description.
        Uses case-insensitive LIKE search.
        """
        search_pattern = f"%{query}%"
        
        products = self.db.query(Product).filter(
            and_(
                Product.is_active == True,
                or_(
                    Product.name.ilike(search_pattern),
                    Product.description.ilike(search_pattern),
                    Product.short_description.ilike(search_pattern)
                )
            )
        ).offset(skip).limit(limit).all()
        
        return products
    
    def get_featured_products(self, limit: int = 10) -> List[Product]:
        """Get featured products."""
        return self.db.query(Product).filter(
            Product.is_featured == True,
            Product.is_active == True
        ).limit(limit).all()
    
    def get_new_arrivals(self, limit: int = 20) -> List[Product]:
        """Get new arrival products."""
        return self.db.query(Product).filter(
            Product.is_new_arrival == True,
            Product.is_active == True
        ).order_by(Product.created_at.desc()).limit(limit).all()
    
    def get_products_by_category(
        self,
        category_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> List[Product]:
        """Get all products in a category."""
        return self.db.query(Product).filter(
            Product.category_id == category_id,
            Product.is_active == True
        ).offset(skip).limit(limit).all()
