"""Category schemas for commerce service."""
from pydantic import BaseModel, field_validator
from typing import Optional, List
from datetime import datetime
import re


class CategoryBase(BaseModel):
    """Base category schema."""
    name: str
    slug: Optional[str] = None
    description: Optional[str] = None
    parent_id: Optional[int] = None
    image_url: Optional[str] = None
    display_order: int = 0
    is_active: bool = True
    is_featured: bool = False
    
    @field_validator('slug', mode='before')
    @classmethod
    def generate_slug(cls, v, info):
        """Auto-generate slug from name if not provided."""
        if v:
            return v
        name = info.data.get('name', '')
        if name:
            # Convert to lowercase, replace spaces with hyphens, remove special chars
            slug = re.sub(r'[^a-z0-9-]', '', name.lower().replace(' ', '-'))
            return slug
        return v


class CategoryCreate(CategoryBase):
    """Schema for creating a category."""
    pass


class CategoryUpdate(BaseModel):
    """Schema for updating a category."""
    name: Optional[str] = None
    slug: Optional[str] = None
    description: Optional[str] = None
    parent_id: Optional[int] = None
    image_url: Optional[str] = None
    display_order: Optional[int] = None
    is_active: Optional[bool] = None
    is_featured: Optional[bool] = None


class CategoryResponse(BaseModel):
    """Schema for category response."""
    id: int
    name: str
    slug: str
    description: Optional[str] = None
    parent_id: Optional[int] = None
    image_url: Optional[str] = None
    display_order: int
    is_active: bool
    is_featured: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class CategoryWithChildren(CategoryResponse):
    """Category response with nested children."""
    children: List["CategoryWithChildren"] = []
    
    class Config:
        from_attributes = True


class CategoryTree(BaseModel):
    """Full category tree structure."""
    categories: List[CategoryWithChildren]
