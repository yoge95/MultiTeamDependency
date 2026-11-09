"""Authentication and authorization schemas."""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class AccessScope(BaseModel):
    """Access scope for a user session."""

    user_id: str
    roles: List[str]
    team_memberships: List[UUID] = Field(default_factory=list)
    accessible_domains: List[UUID] = Field(default_factory=list)
    source_scope_filter: dict = Field(default_factory=dict)


class TokenValidationResponse(BaseModel):
    """Response from Auth API token validation."""

    valid: bool
    user_id: str
    email: str
    roles: List[str] = Field(default_factory=list)
    expires_at: Optional[datetime] = None


class UserProfile(BaseModel):
    """User profile from User Service."""

    user_id: str
    email: str
    display_name: str
    roles: List[str] = Field(default_factory=list)
    team_memberships: List[UUID] = Field(default_factory=list)
    access_policies: List[dict] = Field(default_factory=list)


class CurrentUser(BaseModel):
    """Current authenticated user context."""

    user_id: str
    email: str
    roles: List[str]
    access_scope: AccessScope
