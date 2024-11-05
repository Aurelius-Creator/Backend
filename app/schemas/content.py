from pydantic import BaseModel
from typing import Optional

class ContentTypeSchema(BaseModel):
    id: int
    content_name: str
    icon: Optional[str] = None
    
    class Config:
        from_attributes = True
        
class ContentTypeCreateSchema(BaseModel):
    content_name: str
    icon: Optional[str] = None
    
class ContentTypeUpdateSchema(BaseModel):
    content_name: Optional[str] = None
    icon: Optional[str] = None
        
class ContentPermissionSchema(BaseModel):
    id: int
    name: str
    content_type_id: int
    action: str
    
    class Config:
        from_attributes = True
        
class ContentPermissionCreateSchema(BaseModel):
    name: str
    content_type_id: int
    action: str