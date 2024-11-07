from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class UserCreateSchema(BaseModel):
    username: str
    password: str = Field(default="start@123", min_length=8)
    is_superuser: bool = False

class UserSchema(BaseModel):
    id: int
    username: str
    password: Optional[str] = None
    is_superuser: bool
    last_login: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class UserLoginSchema(BaseModel):
    username: str
    password: str