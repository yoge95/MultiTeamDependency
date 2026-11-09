"""Retrieval schemas for evidence assembly."""

from datetime import datetime
from typing import Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class RetrievedChunk(BaseModel):
    """Single retrieved chunk from OpenSearch."""

    chunk_id: UUID
    source_record_id: UUID
    source_version_id: UUID
    section_path: str
    content: str
    relevance_score: float
    access_scope_tag: str
    freshness_state: str
    domain_id: UUID
    source_title: Optional[str] = None
    last_reviewed_at: Optional[datetime] = None


class RelationshipPath(BaseModel):
    """Relationship path from Neo4j traversal."""

    relationship_type: str
    source_entity_type: str
    source_entity_id: UUID
    target_entity_type: str
    target_entity_id: UUID
    path_length: int
    confidence: Optional[str] = None
    metadata: Dict = Field(default_factory=dict)


class EvidenceBundle(BaseModel):
    """Complete evidence bundle for answer composition."""

    chunks: List[RetrievedChunk] = Field(default_factory=list)
    relationships: List[RelationshipPath] = Field(default_factory=list)
    metadata: Dict = Field(default_factory=dict)


class RetrievalRequest(BaseModel):
    """Request for evidence retrieval."""

    question_text: str
    domain_context: Optional[List[UUID]] = Field(default_factory=list)
    access_scope: Dict
    intent_classification: Optional[Dict] = None
    max_chunks: int = Field(default=20, ge=1, le=100)
    min_relevance_score: float = Field(default=0.3, ge=0.0, le=1.0)


class RankedChunk(BaseModel):
    """Chunk with combined relevance ranking."""

    chunk: RetrievedChunk
    combined_score: float
    score_components: Dict[str, float] = Field(default_factory=dict)
