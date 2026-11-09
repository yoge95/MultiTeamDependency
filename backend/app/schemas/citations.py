"""Citation schemas for source attribution."""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class CitationDetail(BaseModel):
    """Detailed citation with full source context."""

    citation_id: UUID
    answer_id: UUID
    claim_text: str
    chunk_id: UUID
    source_record_id: UUID
    source_version_id: UUID
    source_title: str
    section_path: Optional[str] = None
    evidence_text: str
    freshness_status: str
    last_reviewed_at: Optional[datetime] = None
    approval_state: str
    created_at: datetime


class CitationCoverageReport(BaseModel):
    """Citation coverage analysis."""

    total_claims: int
    cited_claims: int
    coverage_percentage: float
    uncited_claims: List[str] = Field(default_factory=list)
    meets_threshold: bool


class SourceMetadata(BaseModel):
    """Source metadata for citation enrichment."""

    source_record_id: UUID
    title: str
    source_type: str
    domain_id: UUID
    owner_team_id: UUID
    approval_state: str
    last_reviewed_at: Optional[datetime] = None
