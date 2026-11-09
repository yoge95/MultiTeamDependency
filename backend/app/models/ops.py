"""Operations models for ingestion, audit, and sync (ops schema)."""

from datetime import datetime, date
from uuid import uuid4

from sqlalchemy import Column, Date, DateTime, ForeignKey, Integer, String, Text, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base, USE_SCHEMAS, JSONType


def get_table_args(constraint_tuple, schema_name="ops"):
    """Get table args with optional schema based on database type."""
    if USE_SCHEMAS:
        return constraint_tuple + ({"schema": schema_name},)
    return constraint_tuple


class IngestionRun(Base):
    """Ingestion run tracking."""

    __tablename__ = "ingestion_run"
    __table_args__ = get_table_args((
        CheckConstraint("run_type IN ('full', 'incremental', 'manual')", name="ingestion_run_type_check"),
        CheckConstraint("run_status IN ('pending', 'running', 'completed', 'failed')", name="ingestion_run_status_check"),), "ops")

    run_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    run_type = Column(String(80), nullable=False)
    run_status = Column(String(40), nullable=False, default="pending", index=True)
    started_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, index=True)
    completed_at = Column(DateTime(timezone=True))
    error_message = Column(Text)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    # Relationships
    items = relationship("IngestionRunItem", back_populates="run", cascade="all, delete-orphan")


class IngestionRunItem(Base):
    """Ingestion run item tracking."""

    __tablename__ = "ingestion_run_item"
    __table_args__ = get_table_args((
        CheckConstraint(
            "item_status IN ('pending', 'processing', 'completed', 'failed', 'skipped')",
            name="ingestion_item_status_check",
        ),), "ops")

    item_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    run_id = Column(UUID(as_uuid=True), ForeignKey("ingestion_run.run_id", ondelete="CASCADE"), nullable=False, index=True)
    source_record_id = Column(
        UUID(as_uuid=True), ForeignKey("source_record.source_record_id"), nullable=False, index=True
    )
    item_status = Column(String(40), nullable=False, default="pending", index=True)
    chunks_created = Column(Integer, default=0)
    error_message = Column(Text)
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    # Relationships
    run = relationship("IngestionRun", back_populates="items")


class AuditEvent(Base):
    """Audit event tracking."""

    __tablename__ = "audit_event"
    __table_args__ = get_table_args((
        CheckConstraint("actor_type IN ('stakeholder', 'system', 'service')", name="audit_event_actor_check"),
        CheckConstraint("result_code IN ('success', 'failure', 'partial', 'denied')", name="audit_event_result_check"),), "ops")

    audit_event_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    event_type = Column(String(80), nullable=False, index=True)
    actor_type = Column(String(80), nullable=False, index=True)
    actor_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    subject_type = Column(String(80), index=True)
    subject_id = Column(UUID(as_uuid=True), index=True)
    result_code = Column(String(40), nullable=False)
    event_metadata = Column(JSONType)
    occurred_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, index=True)
    archive_date = Column(Date, index=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)


class PrivacyRequestLink(Base):
    """Privacy request link tracking."""

    __tablename__ = "privacy_request_link"
    __table_args__ = get_table_args((
        CheckConstraint("action_type IN ('restrict', 'export', 'delete')", name="privacy_action_type_check"),
        CheckConstraint("action_status IN ('pending', 'in_progress', 'completed', 'failed')", name="privacy_action_status_check"),), "ops")

    link_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    privacy_request_ref = Column(String(255), nullable=False, index=True)
    linked_entity_type = Column(String(80), nullable=False, index=True)
    linked_entity_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    action_type = Column(String(80), nullable=False)
    action_status = Column(String(40), nullable=False, default="pending", index=True)
    completed_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)


class GraphSyncBatch(Base):
    """Graph sync batch tracking."""

    __tablename__ = "graph_sync_batch"
    __table_args__ = get_table_args((
        CheckConstraint("sync_type IN ('full', 'incremental', 'manual')", name="graph_sync_type_check"),
        CheckConstraint("sync_status IN ('pending', 'running', 'completed', 'failed')", name="graph_sync_status_check"),), "ops")

    batch_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    sync_type = Column(String(80), nullable=False)
    sync_status = Column(String(40), nullable=False, default="pending", index=True)
    entities_synced = Column(Integer, default=0)
    relationships_synced = Column(Integer, default=0)
    started_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, index=True)
    completed_at = Column(DateTime(timezone=True))
    error_message = Column(Text)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
