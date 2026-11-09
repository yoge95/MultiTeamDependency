"""Source governance schemas for steward workflows."""

from datetime import date, datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class SourceListItem(BaseModel):
    """Source list item for governance views."""

    source_record_id: UUID
    source_key: str
    title: str
    source_type: str
    domain_id: UUID
    approval_state: str
    sensitivity_classification: str
    next_review_due_on: Optional[date]
    owner_team_id: UUID
    steward_team_id: UUID
    created_at: datetime
    updated_at: datetime


class SourceListResponse(BaseModel):
    """Paginated source list response."""

    items: list[SourceListItem]
    total: int
    page: int
    page_size: int


class SourceRegistrationRequest(BaseModel):
    """Request model for source registration."""

    source_key: str = Field(..., max_length=255, description="Unique source identifier")
    title: str = Field(..., max_length=500, description="Source title")
    source_type: str = Field(..., description="Type of source (confluence, wiki, runbook, etc.)")
    domain_id: UUID = Field(..., description="Knowledge domain ID")
    owner_team_id: UUID = Field(..., description="Owner team ID")
    steward_team_id: UUID = Field(..., description="Steward team ID")
    sensitivity_classification: str = Field(
        default="internal",
        description="Sensitivity classification (public, internal, confidential, restricted)"
    )

    @field_validator("sensitivity_classification")
    @classmethod
    def validate_sensitivity(cls, v: str) -> str:
        """Validate sensitivity classification."""
        allowed = {"public", "internal", "confidential", "restricted"}
        if v not in allowed:
            raise ValueError(f"sensitivity_classification must be one of {allowed}")
        return v


class SourceRegistrationResponse(BaseModel):
    """Response model for source registration."""

    source_record_id: UUID
    source_key: str
    title: str
    approval_state: str
    created_at: datetime


class SourceApprovalRequest(BaseModel):
    """Request model for source approval."""

    review_decision: str = Field(..., description="Review decision (approved, rejected, exception_granted, archived)")
    review_notes: Optional[str] = Field(None, max_length=2000, description="Review notes")
    next_review_due_on: Optional[date] = Field(None, description="Next review due date")

    @field_validator("review_decision")
    @classmethod
    def validate_review_decision(cls, v: str) -> str:
        """Validate review decision."""
        allowed = {"approved", "rejected", "exception_granted", "archived"}
        if v not in allowed:
            raise ValueError(f"review_decision must be one of {allowed}")
        return v


class SourceApprovalResponse(BaseModel):
    """Response model for source approval."""

    review_id: UUID
    source_record_id: UUID
    reviewer_stakeholder_id: UUID
    review_decision: str
    next_review_due_on: Optional[date]
    reviewed_at: datetime


class FreshnessExceptionRequest(BaseModel):
    """Request model for freshness exception."""

    reason: str = Field(..., max_length=2000, description="Reason for exception")
    exception_until: date = Field(..., description="Exception valid until date (max 180 days)")

    @field_validator("exception_until")
    @classmethod
    def validate_exception_date(cls, v: date) -> date:
        """Validate exception date is not more than 180 days in future."""
        from datetime import date as date_type
        from datetime import timedelta
        max_date = date_type.today() + timedelta(days=180)
        if v > max_date:
            raise ValueError("exception_until cannot be more than 180 days in the future")
        return v


class FreshnessExceptionResponse(BaseModel):
    """Response model for freshness exception."""

    review_id: UUID
    source_record_id: UUID
    exception_until: date
    reviewed_at: datetime
    message: str = "Freshness exception granted"
