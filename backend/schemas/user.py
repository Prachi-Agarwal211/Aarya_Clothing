from pydantic import BaseModel, EmailStr
from typing import Optional

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    
    class Config:
        from_attributes = True
