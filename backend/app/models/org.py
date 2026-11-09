"""Organizational and Stakeholder models (org schema)."""

from datetime import datetime
from uuid import uuid4

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base, USE_SCHEMAS


def get_table_args(constraint_tuple, schema_name="org"):
    """Get table args with optional schema based on database type."""
    if USE_SCHEMAS:
        return constraint_tuple + ({"schema": schema_name},)
    return constraint_tuple


class Team(Base):
    """Team entity representing organizational teams."""

    __tablename__ = "team"
    __table_args__ = get_table_args(
        (CheckConstraint("status IN ('active', 'inactive', 'archived')", name="team_status_check"),),
        "org"
    )

    team_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    team_code = Column(String(80), nullable=False, unique=True, index=True)
    team_name = Column(String(255), nullable=False)
    team_type = Column(String(80), nullable=False, index=True)
    primary_owner_stakeholder_id = Column(UUID(as_uuid=True), ForeignKey("stakeholder.stakeholder_id"), nullable=True)
    support_channel = Column(String(255))
    status = Column(String(40), nullable=False, default="active", index=True)
    last_reviewed_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    memberships = relationship("TeamMembership", back_populates="team", cascade="all, delete-orphan")
    owned_services = relationship("ServiceEntity", back_populates="owning_team")


class Stakeholder(Base):
    """Stakeholder entity representing individuals in the organization."""

    __tablename__ = "stakeholder"
    __table_args__ = get_table_args(
        (CheckConstraint("account_status IN ('active', 'inactive', 'suspended')", name="stakeholder_status_check"),),
        "org"
    )

    stakeholder_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    employee_ref = Column(String(120), nullable=False, unique=True, index=True)
    display_name = Column(String(255), nullable=False)
    stakeholder_type = Column(String(80), nullable=False)
    email = Column(String(255), nullable=False, index=True)
    timezone = Column(String(80))
    privileged_account = Column(Boolean, nullable=False, default=False, index=True)
    account_status = Column(String(40), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    memberships = relationship("TeamMembership", back_populates="stakeholder", cascade="all, delete-orphan")


class TeamMembership(Base):
    """Team membership association between stakeholders and teams."""

    __tablename__ = "team_membership"
    __table_args__ = get_table_args(
        (CheckConstraint(
            "role IN ('owner', 'steward', 'reviewer', 'escalation_contact', 'member')",
            name="team_membership_role_check",
        ),),
        "org"
    )

    membership_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    team_id = Column(UUID(as_uuid=True), ForeignKey("team.team_id", ondelete="CASCADE"), nullable=False, index=True)
    stakeholder_id = Column(
        UUID(as_uuid=True), ForeignKey("stakeholder.stakeholder_id", ondelete="CASCADE"), nullable=False, index=True
    )
    role = Column(String(80), nullable=False)
    effective_from = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, index=True)
    effective_until = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    team = relationship("Team", back_populates="memberships")
    stakeholder = relationship("Stakeholder", back_populates="memberships")


class ServiceEntity(Base):
    """Service entity representing organizational services."""

    __tablename__ = "service_entity"
    __table_args__ = get_table_args(
        (CheckConstraint("lifecycle_state IN ('active', 'deprecated', 'retired')", name="service_lifecycle_check"),),
        "org"
    )

    service_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    service_code = Column(String(80), nullable=False, unique=True, index=True)
    service_name = Column(String(255), nullable=False)
    owning_team_id = Column(
        UUID(as_uuid=True), ForeignKey("team.team_id"), nullable=False, index=True
    )
    lifecycle_state = Column(String(40), nullable=False, index=True)
    environment_scope = Column(String(80))
    auth_dependency_flag = Column(Boolean, nullable=False, default=False)
    payment_domain_related = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    owning_team = relationship("Team", back_populates="owned_services")
    upstream_dependencies = relationship(
        "ServiceDependency", foreign_keys="ServiceDependency.downstream_service_id", back_populates="downstream_service"
    )
    downstream_dependencies = relationship(
        "ServiceDependency", foreign_keys="ServiceDependency.upstream_service_id", back_populates="upstream_service"
    )


class ServiceDependency(Base):
    """Service dependency relationships."""

    __tablename__ = "service_dependency"
    __table_args__ = get_table_args(
        (CheckConstraint("dependency_type IN ('api', 'data', 'auth', 'payment', 'infrastructure')", name="service_dependency_type_check"),
        CheckConstraint("criticality IN ('critical', 'high', 'medium', 'low')", name="service_dependency_criticality_check"),
        CheckConstraint("evidence_strength IN ('verified', 'inferred', 'stale')", name="service_dependency_evidence_check"),),
        "org"
    )

    dependency_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    upstream_service_id = Column(
        UUID(as_uuid=True), ForeignKey("service_entity.service_id", ondelete="CASCADE"), nullable=False, index=True
    )
    downstream_service_id = Column(
        UUID(as_uuid=True), ForeignKey("service_entity.service_id", ondelete="CASCADE"), nullable=False, index=True
    )
    dependency_type = Column(String(80), nullable=False)
    criticality = Column(String(40), nullable=False, index=True)
    evidence_strength = Column(String(40), nullable=False)
    last_verified_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    upstream_service = relationship("ServiceEntity", foreign_keys=[upstream_service_id], back_populates="downstream_dependencies")
    downstream_service = relationship("ServiceEntity", foreign_keys=[downstream_service_id], back_populates="upstream_dependencies")
