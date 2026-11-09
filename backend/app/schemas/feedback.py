"""Feedback schemas for request and response models."""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class CitationFeedbackItem(BaseModel):
    """Citation-specific feedback."""

    citation_id: UUID
    issue_type: str = Field(..., description="Type of citation issue (missing, unclear, inaccurate)")
    comment: Optional[str] = Field(None, max_length=500, description="Additional comment about citation")


class FeedbackSubmissionRequest(BaseModel):
    """Request model for feedback submission."""

    answer_id: UUID
    feedback_type: str = Field(
        ...,
        description="Type of feedback (helpful, incomplete, stale, unclear, incorrect, other)"
    )
    feedback_text: Optional[str] = Field(None, max_length=2000, description="Optional feedback text")
    citation_feedback: Optional[List[CitationFeedbackItem]] = Field(
        default=None,
        description="Optional citation-specific feedback"
    )

    @field_validator("feedback_type")
    @classmethod
    def validate_feedback_type(cls, v: str) -> str:
        """Validate feedback type."""
        allowed_types = {"helpful", "incomplete", "stale", "unclear", "incorrect", "other"}
        if v not in allowed_types:
            raise ValueError(f"feedback_type must be one of {allowed_types}")
        return v

    @field_validator("feedback_text")
    @classmethod
    def validate_feedback_text(cls, v: Optional[str]) -> Optional[str]:
        """Validate feedback text does not contain HTML/script tags."""
        if v is None:
            return v

        # Check for HTML/script tags
        dangerous_patterns = ["<script", "</script", "<iframe", "</iframe", "javascript:", "onerror=", "onclick="]
        v_lower = v.lower()
        for pattern in dangerous_patterns:
            if pattern in v_lower:
                raise ValueError("feedback_text must not contain HTML or script tags")

        return v


class FeedbackSubmissionResponse(BaseModel):
    """Response model for feedback submission."""

    feedback_id: UUID
    answer_id: UUID
    feedback_type: str
    triage_status: str
    created_at: datetime
    message: str = "Thank you for your feedback!"


class FeedbackListResponse(BaseModel):
    """Response model for feedback list."""

    feedback_id: UUID
    answer_id: UUID
    stakeholder_id: UUID
    feedback_type: str
    feedback_comment: Optional[str]
    steward_action_required: bool
    created_at: datetime
