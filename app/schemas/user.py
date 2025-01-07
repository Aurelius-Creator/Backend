from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel, Field, model_validator

from .pagination import PaginatedResponse, PaginationParams


class CustomBaseModel(BaseModel):
    """Base model with custom JSON encoders."""

    class Config:
        json_encoders = {
            datetime: lambda v: v.strftime("%Y-%m-%d %H:%M:%S"),
        }


class UserBase(BaseModel):
    """Base user model with common attributes."""

    id: int
    username: str

    class Config:
        from_attributes = True


class CreateUserSchema(BaseModel):
    """Schema for creating a new user."""

    username: str
    password: str = Field(default="start@123", min_length=8)
    is_superuser: bool = False
    permission_ids: Optional[List[int]] = None


class UserSchema(CustomBaseModel, UserBase):
    """Complete user schema with all attributes."""

    is_superuser: bool
    last_login: Optional[datetime] = None
    created_at: datetime
    active: bool = True

    @model_validator(mode="before")
    def set_active_based_on_deletion(cls, values):
        if values.deleted_at is not None:
            values.active = False
        return values

    class Config:
        from_attributes = True


class UserQueryParams(PaginationParams):
    """Parameters for querying users with pagination."""

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


class UserLoginSchema(BaseModel):
    """Schema for user login credentials."""

    username: str
    password: str


class UpdateUserPasswordSchema(BaseModel):
    """Schema for updating user password."""

    user_id: int
    password: str
    confirm_password: str


class UserPermissionSchema(BaseModel):
    """Schema for user permissions."""

    id: int
    user_id: int
    permission_id: int
    active: bool


class CreateUserPermissionSchema(BaseModel):
    """Schema for creating user permissions."""

    user_id: int
    permission_ids: List[int]


class UpdateUserPermissionSchema(BaseModel):
    """Schema for updating user permissions."""

    user_id: int
    active_ids: Optional[List[int]] = None
    inactive_ids: Optional[List[int]] = None


class UserCursorResponse(BaseModel):
    """Response schema for cursor-based pagination."""

    users: List[UserBase]
    next_cursor: Optional[int]


class PaginateUserResponse(PaginatedResponse[UserSchema]):
    """Response schema for offset-based pagination."""

    pass
