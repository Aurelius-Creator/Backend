from pydantic import BaseModel, Field, model_validator
from typing import Optional, List
from datetime import datetime, date
from .pagination import PaginationParams, PaginatedResponse

class CustomBaseModel(BaseModel):
    class Config:
        json_encoders = {
            datetime: lambda v: v.strftime('%Y-%m-%d %H:%M:%S'),
        }

class CreateUserSchema(BaseModel):
    username: str
    password: str = Field(default="start@123", min_length=8)
    is_superuser: bool = False
    permission_ids: Optional[List[int]] = None

class UserSchema(CustomBaseModel):
    id: int
    username: str
    is_superuser: bool
    last_login: Optional[datetime] = None
    created_at: datetime
    active: bool = True
    
    @model_validator(mode='before')
    def set_active_based_on_deletion(cls, values):
        if values.deleted_at is not None:
            values.active = False
        return values
    
    class Config:
        from_attributes = True

class UserQueryParams(PaginationParams):
    id: Optional[int] = None
    username: Optional[str] = None
    superuser: Optional[str] = Field(None, pattern="^(y|n|a)$")
    last_login_start: Optional[date] = None
    last_login_end: Optional[date] = None
    created_at_start: Optional[date] = None
    created_at_end: Optional[date] = None
    active: Optional[str] = Field(None, pattern="^(y|n|a)$")
    sort_by: str = Field(default="id")
    sort_order: str = Field("asc", pattern="^(asc|desc)$")
    
class PaginateUserResponse(PaginatedResponse[UserSchema]):
    pass

class UserLoginSchema(BaseModel):
    username: str
    password: str
    
class UserPermissionSchema(BaseModel):
    id: int
    user_id: int
    permission_id: int
    
class CreateUserPermissionSchema(BaseModel):
    user_id: int
    permission_ids: List[int]
    
class UserBase(BaseModel):
    id: int
    username: str
    
    class Config:
        from_attributes = True

class UserCursorResponse(BaseModel):
    users: List[UserBase]
    next_cursor: Optional[int]