from pydantic import BaseModel, field_validator, Field
from typing import Optional, List

class ContentTypeSchema(BaseModel):
    id: int
    content_name: str
    icon: Optional[str] = None
    
    class Config:
        from_attributes = True
        
class ContentTypeCreateSchema(BaseModel):
    content_name: str = Field(..., min_length=1, max_length=50)
    icon: Optional[str] = None
    
    @field_validator('content_name')
    def name_must_not_be_empty(cls, v):
        if not v.strip():
            raise ValueError("content_name must not be empty")
        return v
    
class ContentTypeUpdateSchema(BaseModel):
    content_name: Optional[str] = Field(None, min_length=1, max_length=50)
    icon: Optional[str] = None
    
    @field_validator('content_name')
    def name_must_not_be_empty(cls, v):
        if v is not None and not v.strip():
            raise ValueError("content_name must not be empty if provided")
        return v
        
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
    
class PermissionsSchema(BaseModel):
    name: str
    action: str
    
    class Config:
        from_atributes = True

class FullContentSchemas(BaseModel):
    id: int
    content_name: str
    icon: Optional[str] = None
    permissions: List[PermissionsSchema] = []
    
    class Config:
        from_attributes = True