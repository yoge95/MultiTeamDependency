"""Interaction models for questions, answers, and feedback (interaction schema)."""

from datetime import datetime
from uuid import uuid4

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text, Numeric, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base, USE_SCHEMAS, JSONType


def get_table_args(constraint_tuple, schema_name="interaction"):
    """Get table args with optional schema based on database type."""
    if USE_SCHEMAS:
        return constraint_tuple + ({"schema": schema_name},)
    return constraint_tuple


class QuestionSession(Base):
    """Question session tracking user conversations."""

    __tablename__ = "question_session"
    __table_args__ = get_table_args((
        CheckConstraint("session_status IN ('active', 'closed', 'expired')", name="session_status_check"),
        CheckConstraint(
            "persona_type IN ('new_joiner', 'engineer', 'stakeholder', 'support', 'admin')",
            name="session_persona_check",
        ),), "interaction")

    session_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    requesting_stakeholder_id = Column(
        UUID(as_uuid=True), ForeignKey("stakeholder.stakeholder_id"), nullable=False, index=True
    )
    persona_type = Column(String(80), nullable=False)
    primary_domain_id = Column(UUID(as_uuid=True), ForeignKey("knowledge_domain.domain_id"), index=True)
    session_status = Column(String(40), nullable=False, default="active", index=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, index=True)
    last_activity_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    closed_at = Column(DateTime(timezone=True))

    # Relationships
    access_scope = relationship("SessionAccessScope", back_populates="session", uselist=False, cascade="all, delete-orphan")
    turns = relationship("QuestionTurn", back_populates="session", cascade="all, delete-orphan")
    answers = relationship("AnswerRecord", back_populates="session", cascade="all, delete-orphan")


class SessionAccessScope(Base):
    """Session access scope cache."""

    __tablename__ = "session_access_scope"
    __table_args__ = get_table_args((), "interaction")

    scope_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    session_id = Column(
        UUID(as_uuid=True), ForeignKey("question_session.session_id", ondelete="CASCADE"), nullable=False, unique=True, index=True
    )
    user_id = Column(String(255), nullable=False)
    role_snapshot = Column(JSONType, nullable=False)
    team_scope = Column(JSONType, nullable=False)
    source_scope_filter = Column(JSONType, nullable=False)
    cached_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)

    # Relationships
    session = relationship("QuestionSession", back_populates="access_scope")


class QuestionTurn(Base):
    """Question turn within a session."""

    __tablename__ = "question_turn"
    __table_args__ = get_table_args((
        CheckConstraint("ambiguity_state IN ('clear', 'ambiguous', 'clarified')", name="turn_ambiguity_check"),
        CheckConstraint("processing_status IN ('pending', 'processing', 'completed', 'error')", name="turn_processing_check"),), "interaction")

    turn_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    session_id = Column(
        UUID(as_uuid=True), ForeignKey("question_session.session_id", ondelete="CASCADE"), nullable=False, index=True
    )
    turn_sequence = Column(Integer, nullable=False)
    question_text = Column(Text, nullable=False)
    intent_classification = Column(JSONType, nullable=False)
    ambiguity_state = Column(String(40), nullable=False, default="clear")
    processing_status = Column(String(40), nullable=False, default="pending")
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, index=True)

    # Relationships
    session = relationship("QuestionSession", back_populates="turns")
    answer = relationship("AnswerRecord", back_populates="turn", uselist=False)


class AnswerRecord(Base):
    """Answer record with confidence and citations."""

    __tablename__ = "answer_record"
    __table_args__ = get_table_args((
        CheckConstraint(
            "response_type IN ('supported_answer', 'clarification_required', 'limitation', 'escalation')",
            name="answer_response_type_check",
        ),
        CheckConstraint("confidence_band IN ('high', 'medium', 'low', 'insufficient')", name="answer_confidence_check"),), "interaction")

    answer_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    turn_id = Column(
        UUID(as_uuid=True), ForeignKey("question_turn.turn_id", ondelete="CASCADE"), nullable=False, index=True
    )
    session_id = Column(
        UUID(as_uuid=True), ForeignKey("question_session.session_id", ondelete="CASCADE"), nullable=False, index=True
    )
    response_type = Column(String(40), nullable=False, index=True)
    answer_text = Column(Text)
    confidence_band = Column(String(40), nullable=False, index=True)
    confidence_score = Column(Numeric(5, 4))
    citation_completeness_flag = Column(Boolean, nullable=False, default=False)
    escalation_required_flag = Column(Boolean, nullable=False, default=False)
    primary_domain_id = Column(UUID(as_uuid=True), ForeignKey("knowledge_domain.domain_id"), index=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, index=True)

    # Relationships
    turn = relationship("QuestionTurn", back_populates="answer")
    session = relationship("QuestionSession", back_populates="answers")
    limitations = relationship("AnswerLimitation", back_populates="answer", cascade="all, delete-orphan")
    citations = relationship("CitationReference", back_populates="answer", cascade="all, delete-orphan")
    feedback = relationship("FeedbackRecord", back_populates="answer", cascade="all, delete-orphan")


class AnswerLimitation(Base):
    """Answer limitation tracking."""

    __tablename__ = "answer_limitation"
    __table_args__ = get_table_args((
        CheckConstraint(
            "limitation_type IN ('missing_knowledge', 'stale_evidence', 'conflicting_evidence', 'restricted_access', 'ambiguous_question')",
            name="limitation_type_check",
        ),
        CheckConstraint("severity IN ('critical', 'high', 'medium', 'low')", name="limitation_severity_check"),), "interaction")

    limitation_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    answer_id = Column(
        UUID(as_uuid=True), ForeignKey("answer_record.answer_id", ondelete="CASCADE"), nullable=False, index=True
    )
    limitation_type = Column(String(80), nullable=False, index=True)
    severity = Column(String(40), nullable=False, index=True)
    description = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    # Relationships
    answer = relationship("AnswerRecord", back_populates="limitations")


class CitationReference(Base):
    """Citation reference linking answers to source chunks."""

    __tablename__ = "citation_reference"
    __table_args__ = get_table_args((), "interaction")

    citation_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    answer_id = Column(
        UUID(as_uuid=True), ForeignKey("answer_record.answer_id", ondelete="CASCADE"), nullable=False, index=True
    )
    chunk_id = Column(UUID(as_uuid=True), ForeignKey("source_chunk.chunk_id"), nullable=False, index=True)
    claim_text = Column(Text)
    source_title = Column(String(500))
    section_path = Column(Text)
    freshness_status = Column(String(40), nullable=False, default="current")
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    # Relationships
    answer = relationship("AnswerRecord", back_populates="citations")


class FeedbackRecord(Base):
    """Feedback on answers."""

    __tablename__ = "feedback_record"
    __table_args__ = get_table_args((
        CheckConstraint(
            "feedback_type IN ('helpful', 'incomplete', 'stale', 'unclear', 'incorrect')",
            name="feedback_type_check",
        ),), "interaction")

    feedback_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    answer_id = Column(
        UUID(as_uuid=True), ForeignKey("answer_record.answer_id", ondelete="CASCADE"), nullable=False, index=True
    )
    stakeholder_id = Column(
        UUID(as_uuid=True), ForeignKey("stakeholder.stakeholder_id"), nullable=False, index=True
    )
    feedback_type = Column(String(80), nullable=False, index=True)
    feedback_comment = Column(Text)
    steward_action_required = Column(Boolean, nullable=False, default=False, index=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, index=True)

    # Relationships
    answer = relationship("AnswerRecord", back_populates="feedback")
    review = relationship("FeedbackReview", back_populates="feedback", uselist=False, cascade="all, delete-orphan")


class FeedbackReview(Base):
    """Feedback review by stewards."""

    __tablename__ = "feedback_review"
    __table_args__ = get_table_args((
        CheckConstraint("review_status IN ('pending', 'in_progress', 'resolved', 'escalated')", name="feedback_review_status_check"),
        CheckConstraint(
            "resolution_code IN ('acknowledged', 'source_updated', 'policy_clarified', 'escalated', 'no_action')",
            name="feedback_review_resolution_check",
        ),), "interaction")

    review_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    feedback_id = Column(
        UUID(as_uuid=True), ForeignKey("feedback_record.feedback_id", ondelete="CASCADE"), nullable=False, index=True
    )
    reviewer_stakeholder_id = Column(
        UUID(as_uuid=True), ForeignKey("stakeholder.stakeholder_id"), nullable=False, index=True
    )
    review_status = Column(String(40), nullable=False, default="pending", index=True)
    resolution_code = Column(String(80))
    resolution_notes = Column(Text)
    reviewed_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    # Relationships
    feedback = relationship("FeedbackRecord", back_populates="review")
