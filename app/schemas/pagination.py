from typing import List, Generic, TypeVar
from pydantic import BaseModel, Field

# Generic type for paginated data
T = TypeVar("T")

# Input schema for pagination parameters
class PaginationParams(BaseModel):
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1)

# Output schema for paginated responses
class PaginatedResponse(Generic[T], BaseModel):
    total_items: int
    page: int
    page_size: int
    total_pages: int
    data: List[T]

    class Config:
        from_attributes = True