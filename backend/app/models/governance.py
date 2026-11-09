"""Governance models for access policies and escalation routes (governance schema)."""

from datetime import datetime
from uuid import uuid4

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base, USE_SCHEMAS, JSONType


def get_table_args(constraint_tuple, schema_name="governance"):
    """Get table args with optional schema based on database type."""
    if USE_SCHEMAS:
        return constraint_tuple + ({"schema": schema_name},)
    return constraint_tuple


class AccessPolicy(Base):
    """Access policy definitions."""

    __tablename__ = "access_policy"
    __table_args__ = get_table_args((
        CheckConstraint(
            "policy_type IN ('source_access', 'domain_access', 'admin_function', 'governance_function')",
            name="policy_type_check",
        ),
        CheckConstraint("status IN ('active', 'inactive', 'archived')", name="policy_status_check"),), "governance")

    policy_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    policy_code = Column(String(80), nullable=False, unique=True, index=True)
    policy_name = Column(String(255), nullable=False)
    policy_type = Column(String(80), nullable=False, index=True)
    scope_expression = Column(JSONType, nullable=False)
    mfa_required = Column(Boolean, nullable=False, default=False)
    status = Column(String(40), nullable=False, default="active", index=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    bindings = relationship("AccessPolicyBinding", back_populates="policy", cascade="all, delete-orphan")


class AccessPolicyBinding(Base):
    """Access policy bindings to principals."""

    __tablename__ = "access_policy_binding"
    __table_args__ = get_table_args((
        CheckConstraint("principal_type IN ('stakeholder', 'team', 'stakeholder_group')", name="policy_binding_principal_check"),), "governance")

    binding_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    policy_id = Column(
        UUID(as_uuid=True), ForeignKey("access_policy.policy_id", ondelete="CASCADE"), nullable=False, index=True
    )
    principal_type = Column(String(80), nullable=False, index=True)
    principal_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    effective_from = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, index=True)
    effective_until = Column(DateTime(timezone=True), index=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    # Relationships
    policy = relationship("AccessPolicy", back_populates="bindings")


class EscalationRoute(Base):
    """Escalation route definitions."""

    __tablename__ = "escalation_route"
    __table_args__ = get_table_args((
        CheckConstraint("status IN ('active', 'inactive', 'archived')", name="escalation_route_status_check"),), "governance")

    route_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    route_code = Column(String(80), nullable=False, unique=True, index=True)
    route_name = Column(String(255), nullable=False)
    domain_id = Column(UUID(as_uuid=True), ForeignKey("knowledge_domain.domain_id"), index=True)
    service_id = Column(UUID(as_uuid=True), ForeignKey("service_entity.service_id"), index=True)
    status = Column(String(40), nullable=False, default="active", index=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    steps = relationship("EscalationRouteStep", back_populates="route", cascade="all, delete-orphan")


class EscalationRouteStep(Base):
    """Escalation route step."""

    __tablename__ = "escalation_route_step"
    __table_args__ = get_table_args((
        CheckConstraint("contact_type IN ('stakeholder', 'team', 'channel')", name="escalation_step_contact_check"),), "governance")

    step_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    route_id = Column(
        UUID(as_uuid=True), ForeignKey("escalation_route.route_id", ondelete="CASCADE"), nullable=False, index=True
    )
    step_order = Column(Integer, nullable=False)
    contact_type = Column(String(80), nullable=False, index=True)
    contact_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    contact_channel = Column(String(255))
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    # Relationships
    route = relationship("EscalationRoute", back_populates="steps")
