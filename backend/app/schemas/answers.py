"""Answer schemas for response models."""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class AnswerLimitationResponse(BaseModel):
    """Answer limitation detail."""

    limitation_type: str
    severity: str
    description: str
    affected_claims: Optional[List[str]] = Field(default_factory=list)
    escalation_guidance: Optional[str] = None


class CitationSummary(BaseModel):
    """Citation summary for answer response."""

    citation_id: UUID
    claim_text: str
    source_title: str
    section_path: Optional[str] = None
    chunk_id: UUID
    freshness_status: str
    last_reviewed_at: Optional[datetime] = None


class EscalationContact(BaseModel):
    """Escalation contact information."""

    contact_type: str
    contact_name: str
    contact_method: str
    contact_address: str


class AnswerResponse(BaseModel):
    """Complete answer response with citations and metadata."""

    answer_id: UUID
    session_id: UUID
    turn_id: UUID
    response_type: str
    answer_text: Optional[str] = None
    confidence_band: str
    confidence_score: Optional[float] = None
    citations: List[CitationSummary] = Field(default_factory=list)
    limitations: List[AnswerLimitationResponse] = Field(default_factory=list)
    escalation_contacts: List[EscalationContact] = Field(default_factory=list)
    freshness_warnings: List[str] = Field(default_factory=list)
    created_at: datetime


class ConfidenceDimensions(BaseModel):
    """Confidence score dimensions."""

    evidence_quality: float
    freshness: float
    consistency: float
    citation_coverage: float


class ConfidenceScoreDetail(BaseModel):
    """Detailed confidence scoring breakdown."""

    overall_score: float
    confidence_band: str
    dimensions: ConfidenceDimensions
    flags: List[str] = Field(default_factory=list)
    explanation: Optional[str] = None
