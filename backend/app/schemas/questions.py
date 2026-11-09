"""Pydantic schemas for question submission and status."""

from typing import Optional
from uuid import UUID
from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class QuestionSubmissionRequest(BaseModel):
    """Request schema for question submission."""
    
    question_text: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="Natural language question (1-2000 characters)",
    )
    session_id: Optional[UUID] = Field(
        None,
        description="Optional existing session ID for follow-up questions",
    )
    
    @field_validator("question_text")
    @classmethod
    def validate_question_text(cls, v: str) -> str:
        """Validate question text is not empty after stripping."""
        stripped = v.strip()
        if not stripped:
            raise ValueError("Question text cannot be empty or whitespace only")
        return stripped


class QuestionSubmissionResponse(BaseModel):
    """Response schema for question submission."""
    
    question_id: UUID = Field(..., description="UUID of the question turn")
    session_id: UUID = Field(..., description="UUID of the conversation session")
    turn_id: UUID = Field(..., description="UUID of this turn (same as question_id)")
    status: str = Field(
        ...,
        description="Processing status: processing, clarification_needed, completed, error",
    )
    clarification_prompt: Optional[str] = Field(
        None,
        description="Clarification prompt if status is clarification_needed",
    )
    estimated_response_time_ms: Optional[int] = Field(
        None,
        description="Estimated time until answer is ready (milliseconds)",
    )


class IntentClassification(BaseModel):
    """Intent classification result."""
    
    primary_intent: str = Field(
        ...,
        description="Primary intent: ownership, dependency, routing, runbook, onboarding, governance",
    )
    candidate_domains: list[str] = Field(
        default_factory=list,
        description="Candidate knowledge domains for this question",
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Classification confidence score (0.0-1.0)",
    )
    ambiguity_flags: list[str] = Field(
        default_factory=list,
        description="Ambiguity flags if question is unclear",
    )


class QuestionStatusResponse(BaseModel):
    """Response schema for question status check."""
    
    question_id: UUID
    session_id: UUID
    turn_id: UUID
    status: str = Field(
        ...,
        description="Current status: processing, clarification_needed, completed, error",
    )
    intent_classification: Optional[IntentClassification] = None
    answer_id: Optional[UUID] = Field(
        None,
        description="UUID of the answer if status is completed",
    )
    error_message: Optional[str] = Field(
        None,
        description="Error message if status is error",
    )
    created_at: datetime
    completed_at: Optional[datetime] = None
