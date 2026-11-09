"""Knowledge governance models (knowledge schema)."""

from datetime import datetime, date
from uuid import uuid4

from sqlalchemy import Boolean, Column, Date, DateTime, ForeignKey, Integer, String, Text, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base, USE_SCHEMAS


def get_table_args(constraint_tuple, schema_name="knowledge"):
    """Get table args with optional schema based on database type."""
    if USE_SCHEMAS:
        return constraint_tuple + ({"schema": schema_name},)
    return constraint_tuple


class KnowledgeDomain(Base):
    """Knowledge domain entity."""

    __tablename__ = "knowledge_domain"
    __table_args__ = get_table_args((
        CheckConstraint(
            "category IN ('onboarding', 'ownership', 'dependencies', 'runbooks', 'governance', 'process')",
            name="domain_category_check",
        ),), "knowledge")

    domain_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    domain_code = Column(String(80), nullable=False, unique=True, index=True)
    domain_name = Column(String(255), nullable=False)
    category = Column(String(80), nullable=False)
    steward_team_id = Column(UUID(as_uuid=True), ForeignKey("team.team_id"), nullable=False, index=True)
    stale_after_days = Column(Integer, nullable=False, default=90)
    governance_sensitive = Column(Boolean, nullable=False, default=False, index=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    source_records = relationship("SourceRecord", back_populates="domain")
    domain_assignments = relationship("KnowledgeDomainAssignment", back_populates="domain", cascade="all, delete-orphan")


class KnowledgeDomainAssignment(Base):
    """Domain assignment to teams."""

    __tablename__ = "knowledge_domain_assignment"
    __table_args__ = get_table_args((
        CheckConstraint("assignment_type IN ('steward', 'owner', 'reviewer')", name="domain_assignment_type_check"),), "knowledge")

    assignment_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    domain_id = Column(
        UUID(as_uuid=True), ForeignKey("knowledge_domain.domain_id", ondelete="CASCADE"), nullable=False, index=True
    )
    team_id = Column(UUID(as_uuid=True), ForeignKey("team.team_id", ondelete="CASCADE"), nullable=False, index=True)
    assignment_type = Column(String(80), nullable=False)
    effective_from = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    effective_until = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    domain = relationship("KnowledgeDomain", back_populates="domain_assignments")


class SourceRecord(Base):
    """Source record metadata."""

    __tablename__ = "source_record"
    __table_args__ = get_table_args((
        CheckConstraint("approval_state IN ('pending', 'approved', 'rejected', 'archived')", name="source_approval_check"),
        CheckConstraint(
            "sensitivity_classification IN ('public', 'internal', 'confidential', 'restricted')",
            name="source_sensitivity_check",
        ),), "knowledge")

    source_record_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    source_key = Column(String(255), nullable=False, unique=True, index=True)
    title = Column(String(500), nullable=False)
    source_type = Column(String(80), nullable=False)
    domain_id = Column(UUID(as_uuid=True), ForeignKey("knowledge_domain.domain_id"), nullable=False, index=True)
    owner_team_id = Column(UUID(as_uuid=True), ForeignKey("team.team_id"), nullable=False, index=True)
    steward_team_id = Column(UUID(as_uuid=True), ForeignKey("team.team_id"), nullable=False, index=True)
    approval_state = Column(String(40), nullable=False, default="pending", index=True)
    sensitivity_classification = Column(String(40), nullable=False, default="internal")
    next_review_due_on = Column(Date, index=True)
    retention_days = Column(Integer, nullable=False, default=365)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    domain = relationship("KnowledgeDomain", back_populates="source_records")
    versions = relationship("SourceVersion", back_populates="source_record", cascade="all, delete-orphan")
    reviews = relationship("SourceReview", back_populates="source_record", cascade="all, delete-orphan")
    links = relationship("SourceRecordLink", back_populates="source_record", cascade="all, delete-orphan")


class SourceVersion(Base):
    """Source version tracking."""

    __tablename__ = "source_version"
    __table_args__ = get_table_args((), "knowledge")

    source_version_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    source_record_id = Column(
        UUID(as_uuid=True), ForeignKey("source_record.source_record_id", ondelete="CASCADE"), nullable=False, index=True
    )
    version_number = Column(Integer, nullable=False)
    content_hash = Column(String(128), nullable=False)
    storage_uri = Column(Text, nullable=False)
    is_active = Column(Boolean, nullable=False, default=False, index=True)
    extracted_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, index=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    source_record = relationship("SourceRecord", back_populates="versions")
    chunks = relationship("SourceChunk", back_populates="source_version", cascade="all, delete-orphan")


class SourceReview(Base):
    """Source review records."""

    __tablename__ = "source_review"
    __table_args__ = get_table_args((
        CheckConstraint(
            "review_decision IN ('approved', 'rejected', 'exception_granted', 'archived')",
            name="source_review_decision_check",
        ),), "knowledge")

    review_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    source_record_id = Column(
        UUID(as_uuid=True), ForeignKey("source_record.source_record_id", ondelete="CASCADE"), nullable=False, index=True
    )
    reviewer_stakeholder_id = Column(
        UUID(as_uuid=True), ForeignKey("stakeholder.stakeholder_id"), nullable=False, index=True
    )
    review_decision = Column(String(40), nullable=False, index=True)
    freshness_exception_granted = Column(Boolean, nullable=False, default=False)
    next_review_due_on = Column(Date, index=True)
    review_notes = Column(Text)
    reviewed_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    # Relationships
    source_record = relationship("SourceRecord", back_populates="reviews")


class SourceChunk(Base):
    """Source chunk for retrieval."""

    __tablename__ = "source_chunk"
    __table_args__ = get_table_args((
        CheckConstraint(
            "freshness_state IN ('current', 'stale', 'exception_granted', 'archived')", name="chunk_freshness_check"
        ),), "knowledge")

    chunk_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    source_version_id = Column(
        UUID(as_uuid=True), ForeignKey("source_version.source_version_id", ondelete="CASCADE"), nullable=False, index=True
    )
    section_path = Column(Text, nullable=False)
    chunk_order = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    token_count = Column(Integer, nullable=False)
    access_scope_tag = Column(String(80), nullable=False, default="internal", index=True)
    freshness_state = Column(String(40), nullable=False, default="current", index=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    source_version = relationship("SourceVersion", back_populates="chunks")
    relationship_assertions = relationship("ChunkRelationshipAssertion", back_populates="chunk", cascade="all, delete-orphan")


class ChunkRelationshipAssertion(Base):
    """Chunk relationship assertions for graph projection."""

    __tablename__ = "chunk_relationship_assertion"
    __table_args__ = get_table_args((
        CheckConstraint("confidence_band IN ('high', 'medium', 'low')", name="assertion_confidence_check"),), "knowledge")

    assertion_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    chunk_id = Column(
        UUID(as_uuid=True), ForeignKey("source_chunk.chunk_id", ondelete="CASCADE"), nullable=False, index=True
    )
    source_entity_type = Column(String(80), nullable=False, index=True)
    source_entity_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    target_entity_type = Column(String(80), nullable=False, index=True)
    target_entity_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    relationship_type = Column(String(80), nullable=False, index=True)
    confidence_band = Column(String(40), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    # Relationships
    chunk = relationship("SourceChunk", back_populates="relationship_assertions")


class SourceRecordLink(Base):
    """Links between source records and entities."""

    __tablename__ = "source_record_link"
    __table_args__ = get_table_args((), "knowledge")

    link_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    source_record_id = Column(
        UUID(as_uuid=True), ForeignKey("source_record.source_record_id", ondelete="CASCADE"), nullable=False, index=True
    )
    linked_entity_type = Column(String(80), nullable=False, index=True)
    linked_entity_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    link_type = Column(String(80), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    # Relationships
    source_record = relationship("SourceRecord", back_populates="links")
