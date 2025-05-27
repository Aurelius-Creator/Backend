from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class BaseContentType(BaseModel):
    """Base class for content type schemas with common fields."""

    content_name: str = Field(
        min_length=1, max_length=50, description="Name of the content type"
    )
    icon: Optional[str] = Field(
        default=None, description="Optional icon identifier for the content type"
    )

    @field_validator("content_name")
    def validate_content_name(cls, v: str) -> str:
        """Validate that content_name is not empty or just whitespace."""
        if not v.strip():
            raise ValueError("content_name must not be empty")
        return v.strip()


class ContentTypeSchema(BaseContentType):
    """Schema for retrieving content types."""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(description="Unique identifier for the content type")


class ContentTypeCreateSchema(BaseContentType):
    """Schema for creating new content types."""

    pass


class ContentTypeUpdateSchema(BaseModel):
    """Schema for updating existing content types."""

    content_name: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=50,
        description="New name for the content type",
    )
    icon: Optional[str] = Field(
        default=None, description="New icon identifier for the content type"
    )

    @field_validator("content_name")
    def validate_content_name(cls, v: Optional[str]) -> Optional[str]:
        """Validate that content_name is not empty or just whitespace if provided."""
        if v is not None and not v.strip():
            raise ValueError("content_name must not be empty if provided")
        return v.strip() if v is not None else v


class BasePermission(BaseModel):
    """Base class for permission schemas with common fields."""

    name: str = Field(description="Name of the permission")
    action: str = Field(
        description="Action type (C: Create, R: Read, U: Update, D: Delete)"
    )

    @field_validator("action")
    def validate_action(cls, v: str) -> str:
        """Validate that action is one of the allowed CRUD values."""
        allowed_actions = {"C", "R", "U", "D"}
        if v not in allowed_actions:
            raise ValueError(f"action must be one of: {', '.join(allowed_actions)}")
        return v


class ContentPermissionSchema(BasePermission):
    """Schema for retrieving content permissions."""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(description="Unique identifier for the permission")
    content_type_id: int = Field(description="ID of the associated content type")


class ContentPermissionCreateSchema(BasePermission):
    """Schema for creating new content permissions."""

    content_type_id: int = Field(description="ID of the content type to associate with")


class PermissionSchema(BaseModel):
    """Schema for basic permission information."""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(description="Unique identifier for the permission")
    name: str = Field(description="Name of the permission")
    action: str = Field(
        description="Action type (C: Create, R: Read, U: Update, D: Delete)"
    )


class FullContentSchema(BaseModel):
    """Schema for content type with its associated permissions."""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(description="Unique identifier for the content type")
    content_name: str = Field(description="Name of the content type")
    icon: Optional[str] = Field(
        default=None, description="Optional icon identifier for the content type"
    )
    permissions: List[PermissionSchema] = Field(
        default_factory=list,
        description="List of permissions associated with this content type",
    )


class PermissionResponse(BaseModel):
    """Standardized permission response model"""

    authorized: bool
    permission_id: Optional[int] = None
    user_id: Optional[int] = None
    content_type_id: Optional[int] = None
    action: Optional[str] = None
