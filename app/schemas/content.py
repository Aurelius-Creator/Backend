from pydantic import BaseModel
from typing import Optional

class ContentTypeSchema(BaseModel):
    id: int
    content_name: str
    icon: Optional[str] = None
    
    class Config:
        from_attributes = True
        
class ContentTypeCreate(BaseModel):
    content_name: str
    icon: Optional[str] = None
    
class ContentTypeUpdate(BaseModel):
    content_name: Optional[str] = None
    icon: Optional[str] = None
        
class ContentPermissionSchema(BaseModel):
    id: int
    name: str
    content_type_id: int
    action: str
    
    class Config:
        from_attributes = True
        
class ContentPermissionCreate(BaseModel):
    name: str
    content_type_id: int
    action: str