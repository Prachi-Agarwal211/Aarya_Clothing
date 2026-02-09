"""Category service for managing product categories."""
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_
from fastapi import HTTPException, status

from models.category import Category
from schemas.category import CategoryCreate, CategoryUpdate


class CategoryService:
    """Service for category management operations."""
    
    def __init__(self, db: Session):
        """Initialize category service."""
        self.db = db
    
    def get_all_categories(self, active_only: bool = True) -> List[Category]:
        """Get all categories."""
        query = self.db.query(Category)
        if active_only:
            query = query.filter(Category.is_active == True)
        return query.order_by(Category.display_order, Category.name).all()
    
    def get_root_categories(self, active_only: bool = True) -> List[Category]:
        """Get only root categories (no parent)."""
        query = self.db.query(Category).filter(Category.parent_id == None)
        if active_only:
            query = query.filter(Category.is_active == True)
        return query.order_by(Category.display_order, Category.name).all()
    
    def get_category_by_id(self, category_id: int) -> Optional[Category]:
        """Get category by ID."""
        return self.db.query(Category).filter(Category.id == category_id).first()
    
    def get_category_by_slug(self, slug: str) -> Optional[Category]:
        """Get category by slug."""
        return self.db.query(Category).filter(Category.slug == slug).first()
    
    def create_category(self, category_data: CategoryCreate) -> Category:
        """Create a new category."""
        # Check if slug exists
        existing = self.db.query(Category).filter(Category.slug == category_data.slug).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Category with slug '{category_data.slug}' already exists"
            )
        
        # Validate parent if specified
        if category_data.parent_id:
            parent = self.get_category_by_id(category_data.parent_id)
            if not parent:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Parent category with ID {category_data.parent_id} not found"
                )
        
        category = Category(**category_data.model_dump())
        self.db.add(category)
        self.db.commit()
        self.db.refresh(category)
        return category
    
    def update_category(self, category_id: int, category_data: CategoryUpdate) -> Category:
        """Update an existing category."""
        category = self.get_category_by_id(category_id)
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Category with ID {category_id} not found"
            )
        
        # Check slug uniqueness if updating
        if category_data.slug and category_data.slug != category.slug:
            existing = self.db.query(Category).filter(Category.slug == category_data.slug).first()
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Category with slug '{category_data.slug}' already exists"
                )
        
        # Update fields
        update_data = category_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(category, field, value)
        
        self.db.commit()
        self.db.refresh(category)
        return category
    
    def delete_category(self, category_id: int) -> bool:
        """Delete a category."""
        category = self.get_category_by_id(category_id)
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Category with ID {category_id} not found"
            )
        
        # Check if category has children
        children = self.db.query(Category).filter(Category.parent_id == category_id).first()
        if children:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete category with subcategories. Delete children first."
            )
        
        # Check if category has products
        if category.products:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete category with products. Move or delete products first."
            )
        
        self.db.delete(category)
        self.db.commit()
        return True
    
    def get_category_tree(self, parent_id: Optional[int] = None) -> List[Category]:
        """Get category tree structure."""
        if parent_id is None:
            # Get root categories
            return self.get_root_categories()
        else:
            # Get children of specific category
            return self.db.query(Category).filter(
                Category.parent_id == parent_id,
                Category.is_active == True
            ).order_by(Category.display_order, Category.name).all()
