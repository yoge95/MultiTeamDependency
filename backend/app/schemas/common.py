"""Common Pydantic schemas used across modules."""

from typing import Optional
from uuid import UUID
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class TimestampMixin(BaseModel):
    """Mixin for created_at and updated_at timestamps."""
    
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)


class PaginatedResponse(BaseModel):
    """Standard paginated response wrapper."""
    
    items: list
    total: int
    page: int
    page_size: int
    
    @property
    def pages(self) -> int:
        """Calculate total number of pages."""
        return (self.total + self.page_size - 1) // self.page_size
    
    @property
    def has_next(self) -> bool:
        """Check if there are more pages."""
        return self.page < self.pages
    
    @property
    def has_prev(self) -> bool:
        """Check if there are previous pages."""
        return self.page > 1


class ErrorResponse(BaseModel):
    """Standard error response."""
    
    detail: str
    error_code: Optional[str] = None
    retry_after_ms: Optional[int] = None
