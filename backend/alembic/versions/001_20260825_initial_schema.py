"""Initial schema with all five schemas and tables

Revision ID: 001
Revises: 
Create Date: 2026-08-25 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create schemas
    op.execute('CREATE SCHEMA IF NOT EXISTS org')
    op.execute('CREATE SCHEMA IF NOT EXISTS knowledge')
    op.execute('CREATE SCHEMA IF NOT EXISTS interaction')
    op.execute('CREATE SCHEMA IF NOT EXISTS governance')
    op.execute('CREATE SCHEMA IF NOT EXISTS ops')
    
    # Enable UUID extension for PostgreSQL
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
    
    # ORG SCHEMA TABLES
    
    # org.stakeholder (must be created before org.team due to FK reference)
    op.create_table(
        'stakeholder',
        sa.Column('stakeholder_id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('employee_ref', sa.String(120), nullable=False, unique=True),
        sa.Column('display_name', sa.String(255), nullable=False),
        sa.Column('stakeholder_type', sa.String(80), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('timezone', sa.String(80)),
        sa.Column('privileged_account', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('account_status', sa.String(40), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.CheckConstraint("account_status IN ('active', 'inactive', 'suspended')", name='stakeholder_status_check'),
        schema='org'
    )
    op.create_index('idx_stakeholder_employee_ref', 'stakeholder', ['employee_ref'], schema='org')
    op.create_index('idx_stakeholder_email', 'stakeholder', ['email'], schema='org')
    op.create_index('idx_stakeholder_privileged', 'stakeholder', ['privileged_account'], schema='org', postgresql_where=sa.text('privileged_account = true'))
    
    # org.team
    op.create_table(
        'team',
        sa.Column('team_id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('team_code', sa.String(80), nullable=False, unique=True),
        sa.Column('team_name', sa.String(255), nullable=False),
        sa.Column('team_type', sa.String(80), nullable=False),
        sa.Column('primary_owner_stakeholder_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('org.stakeholder.stakeholder_id')),
        sa.Column('support_channel', sa.String(255)),
        sa.Column('status', sa.String(40), nullable=False, server_default='active'),
        sa.Column('last_reviewed_at', sa.DateTime(timezone=True)),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.CheckConstraint("status IN ('active', 'inactive', 'archived')", name='team_status_check'),
        schema='org'
    )
    op.create_index('idx_team_code', 'team', ['team_code'], schema='org')
    op.create_index('idx_team_status', 'team', ['status'], schema='org')
    op.create_index('idx_team_type', 'team', ['team_type'], schema='org')
    
    # org.team_membership
    op.create_table(
        'team_membership',
        sa.Column('membership_id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('team_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('org.team.team_id', ondelete='CASCADE'), nullable=False),
        sa.Column('stakeholder_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('org.stakeholder.stakeholder_id', ondelete='CASCADE'), nullable=False),
        sa.Column('role', sa.String(80), nullable=False),
        sa.Column('effective_from', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('effective_until', sa.DateTime(timezone=True)),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.CheckConstraint("role IN ('owner', 'steward', 'reviewer', 'escalation_contact', 'member')", name='team_membership_role_check'),
        sa.UniqueConstraint('team_id', 'stakeholder_id', 'effective_from', name='team_membership_unique'),
        schema='org'
    )
    op.create_index('idx_team_membership_team', 'team_membership', ['team_id'], schema='org')
    op.create_index('idx_team_membership_stakeholder', 'team_membership', ['stakeholder_id'], schema='org')
    op.create_index('idx_team_membership_effective', 'team_membership', ['effective_from', 'effective_until'], schema='org')
    
    # org.service_entity
    op.create_table(
        'service_entity',
        sa.Column('service_id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('service_code', sa.String(80), nullable=False, unique=True),
        sa.Column('service_name', sa.String(255), nullable=False),
        sa.Column('owning_team_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('org.team.team_id'), nullable=False),
        sa.Column('lifecycle_state', sa.String(40), nullable=False),
        sa.Column('environment_scope', sa.String(80)),
        sa.Column('auth_dependency_flag', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('payment_domain_related', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.CheckConstraint("lifecycle_state IN ('active', 'deprecated', 'retired')", name='service_lifecycle_check'),
        schema='org'
    )
    op.create_index('idx_service_code', 'service_entity', ['service_code'], schema='org')
    op.create_index('idx_service_owning_team', 'service_entity', ['owning_team_id'], schema='org')
    op.create_index('idx_service_lifecycle', 'service_entity', ['lifecycle_state'], schema='org')
    
    # org.service_dependency
    op.create_table(
        'service_dependency',
        sa.Column('dependency_id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('upstream_service_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('org.service_entity.service_id', ondelete='CASCADE'), nullable=False),
        sa.Column('downstream_service_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('org.service_entity.service_id', ondelete='CASCADE'), nullable=False),
        sa.Column('dependency_type', sa.String(80), nullable=False),
        sa.Column('criticality', sa.String(40), nullable=False),
        sa.Column('evidence_strength', sa.String(40), nullable=False),
        sa.Column('last_verified_at', sa.DateTime(timezone=True)),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.CheckConstraint("dependency_type IN ('api', 'data', 'auth', 'payment', 'infrastructure')", name='service_dependency_type_check'),
        sa.CheckConstraint("criticality IN ('critical', 'high', 'medium', 'low')", name='service_dependency_criticality_check'),
        sa.CheckConstraint("evidence_strength IN ('verified', 'inferred', 'stale')", name='service_dependency_evidence_check'),
        sa.UniqueConstraint('upstream_service_id', 'downstream_service_id', 'dependency_type', name='service_dependency_unique'),
        schema='org'
    )
    op.create_index('idx_service_dependency_upstream', 'service_dependency', ['upstream_service_id'], schema='org')
    op.create_index('idx_service_dependency_downstream', 'service_dependency', ['downstream_service_id'], schema='org')
    op.create_index('idx_service_dependency_criticality', 'service_dependency', ['criticality'], schema='org')
    
    # KNOWLEDGE SCHEMA TABLES
    
    # knowledge.knowledge_domain
    op.create_table(
        'knowledge_domain',
        sa.Column('domain_id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('domain_code', sa.String(80), nullable=False, unique=True),
        sa.Column('domain_name', sa.String(255), nullable=False),
        sa.Column('category', sa.String(80), nullable=False),
        sa.Column('steward_team_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('org.team.team_id'), nullable=False),
        sa.Column('stale_after_days', sa.Integer, nullable=False, server_default='90'),
        sa.Column('governance_sensitive', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.CheckConstraint("category IN ('onboarding', 'ownership', 'dependencies', 'runbooks', 'governance', 'process')", name='domain_category_check'),
        schema='knowledge'
    )
    op.create_index('idx_domain_code', 'knowledge_domain', ['domain_code'], schema='knowledge')
    op.create_index('idx_domain_steward_team', 'knowledge_domain', ['steward_team_id'], schema='knowledge')
    op.create_index('idx_domain_governance_sensitive', 'knowledge_domain', ['governance_sensitive'], schema='knowledge', postgresql_where=sa.text('governance_sensitive = true'))
    
    # knowledge.knowledge_domain_assignment
    op.create_table(
        'knowledge_domain_assignment',
        sa.Column('assignment_id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('domain_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('knowledge.knowledge_domain.domain_id', ondelete='CASCADE'), nullable=False),
        sa.Column('team_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('org.team.team_id', ondelete='CASCADE'), nullable=False),
        sa.Column('assignment_type', sa.String(80), nullable=False),
        sa.Column('effective_from', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('effective_until', sa.DateTime(timezone=True)),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.CheckConstraint("assignment_type IN ('steward', 'owner', 'reviewer')", name='domain_assignment_type_check'),
        sa.UniqueConstraint('domain_id', 'team_id', 'effective_from', name='domain_assignment_unique'),
        schema='knowledge'
    )
    op.create_index('idx_domain_assignment_domain', 'knowledge_domain_assignment', ['domain_id'], schema='knowledge')
    op.create_index('idx_domain_assignment_team', 'knowledge_domain_assignment', ['team_id'], schema='knowledge')
    
    # knowledge.source_record
    op.create_table(
        'source_record',
        sa.Column('source_record_id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('source_key', sa.String(255), nullable=False, unique=True),
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('source_type', sa.String(80), nullable=False),
        sa.Column('domain_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('knowledge.knowledge_domain.domain_id'), nullable=False),
        sa.Column('owner_team_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('org.team.team_id'), nullable=False),
        sa.Column('steward_team_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('org.team.team_id'), nullable=False),
        sa.Column('approval_state', sa.String(40), nullable=False, server_default='pending'),
        sa.Column('sensitivity_classification', sa.String(40), nullable=False, server_default='internal'),
        sa.Column('next_review_due_on', sa.Date),
        sa.Column('retention_days', sa.Integer, nullable=False, server_default='365'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.CheckConstraint("approval_state IN ('pending', 'approved', 'rejected', 'archived')", name='source_approval_check'),
        sa.CheckConstraint("sensitivity_classification IN ('public', 'internal', 'confidential', 'restricted')", name='source_sensitivity_check'),
        schema='knowledge'
    )
    op.create_index('idx_source_key', 'source_record', ['source_key'], schema='knowledge')
    op.create_index('idx_source_domain', 'source_record', ['domain_id'], schema='knowledge')
    op.create_index('idx_source_owner_team', 'source_record', ['owner_team_id'], schema='knowledge')
    op.create_index('idx_source_steward_team', 'source_record', ['steward_team_id'], schema='knowledge')
    op.create_index('idx_source_approval_state', 'source_record', ['approval_state'], schema='knowledge')
    op.create_index('idx_source_next_review', 'source_record', ['next_review_due_on'], schema='knowledge', postgresql_where=sa.text('next_review_due_on IS NOT NULL'))
    
    # knowledge.source_version
    op.create_table(
        'source_version',
        sa.Column('source_version_id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('source_record_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('knowledge.source_record.source_record_id', ondelete='CASCADE'), nullable=False),
        sa.Column('version_number', sa.Integer, nullable=False),
        sa.Column('content_hash', sa.String(128), nullable=False),
        sa.Column('storage_uri', sa.Text, nullable=False),
        sa.Column('is_active', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('extracted_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.UniqueConstraint('source_record_id', 'version_number', name='source_version_unique'),
        schema='knowledge'
    )
    op.create_index('idx_source_version_record', 'source_version', ['source_record_id'], schema='knowledge')
    op.create_index('idx_source_version_active', 'source_version', ['source_record_id', 'is_active'], schema='knowledge', postgresql_where=sa.text('is_active = true'))
    op.create_index('idx_source_version_extracted', 'source_version', ['extracted_at'], schema='knowledge')
    
    # knowledge.source_review
    op.create_table(
        'source_review',
        sa.Column('review_id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('source_record_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('knowledge.source_record.source_record_id', ondelete='CASCADE'), nullable=False),
        sa.Column('reviewer_stakeholder_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('org.stakeholder.stakeholder_id'), nullable=False),
        sa.Column('review_decision', sa.String(40), nullable=False),
        sa.Column('freshness_exception_granted', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('next_review_due_on', sa.Date),
        sa.Column('review_notes', sa.Text),
        sa.Column('reviewed_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.CheckConstraint("review_decision IN ('approved', 'rejected', 'exception_granted', 'archived')", name='source_review_decision_check'),
        schema='knowledge'
    )
    op.create_index('idx_source_review_record', 'source_review', ['source_record_id'], schema='knowledge')
    op.create_index('idx_source_review_reviewer', 'source_review', ['reviewer_stakeholder_id'], schema='knowledge')
    op.create_index('idx_source_review_decision', 'source_review', ['review_decision'], schema='knowledge')
    op.create_index('idx_source_review_next_due', 'source_review', ['next_review_due_on'], schema='knowledge', postgresql_where=sa.text('next_review_due_on IS NOT NULL'))
    
    # knowledge.source_chunk
    op.create_table(
        'source_chunk',
        sa.Column('chunk_id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('source_version_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('knowledge.source_version.source_version_id', ondelete='CASCADE'), nullable=False),
        sa.Column('section_path', sa.Text, nullable=False),
        sa.Column('chunk_order', sa.Integer, nullable=False),
        sa.Column('content', sa.Text, nullable=False),
        sa.Column('token_count', sa.Integer, nullable=False),
        sa.Column('access_scope_tag', sa.String(80), nullable=False, server_default='internal'),
        sa.Column('freshness_state', sa.String(40), nullable=False, server_default='current'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.CheckConstraint("freshness_state IN ('current', 'stale', 'exception_granted', 'archived')", name='chunk_freshness_check'),
        sa.UniqueConstraint('source_version_id', 'chunk_order', name='chunk_order_unique'),
        schema='knowledge'
    )
    op.create_index('idx_source_chunk_version', 'source_chunk', ['source_version_id'], schema='knowledge')
    op.create_index('idx_source_chunk_access_scope', 'source_chunk', ['access_scope_tag'], schema='knowledge')
    op.create_index('idx_source_chunk_freshness', 'source_chunk', ['freshness_state'], schema='knowledge')
    
    # knowledge.chunk_relationship_assertion
    op.create_table(
        'chunk_relationship_assertion',
        sa.Column('assertion_id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('chunk_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('knowledge.source_chunk.chunk_id', ondelete='CASCADE'), nullable=False),
        sa.Column('source_entity_type', sa.String(80), nullable=False),
        sa.Column('source_entity_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('target_entity_type', sa.String(80), nullable=False),
        sa.Column('target_entity_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('relationship_type', sa.String(80), nullable=False),
        sa.Column('confidence_band', sa.String(40), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.CheckConstraint("confidence_band IN ('high', 'medium', 'low')", name='assertion_confidence_check'),
        schema='knowledge'
    )
    op.create_index('idx_chunk_assertion_chunk', 'chunk_relationship_assertion', ['chunk_id'], schema='knowledge')
    op.create_index('idx_chunk_assertion_source', 'chunk_relationship_assertion', ['source_entity_type', 'source_entity_id'], schema='knowledge')
    op.create_index('idx_chunk_assertion_target', 'chunk_relationship_assertion', ['target_entity_type', 'target_entity_id'], schema='knowledge')
    op.create_index('idx_chunk_assertion_relationship', 'chunk_relationship_assertion', ['relationship_type'], schema='knowledge')
    
    # knowledge.source_record_link
    op.create_table(
        'source_record_link',
        sa.Column('link_id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('source_record_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('knowledge.source_record.source_record_id', ondelete='CASCADE'), nullable=False),
        sa.Column('linked_entity_type', sa.String(80), nullable=False),
        sa.Column('linked_entity_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('link_type', sa.String(80), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.UniqueConstraint('source_record_id', 'linked_entity_type', 'linked_entity_id', 'link_type', name='source_link_unique'),
        schema='knowledge'
    )
    op.create_index('idx_source_link_record', 'source_record_link', ['source_record_id'], schema='knowledge')
    op.create_index('idx_source_link_entity', 'source_record_link', ['linked_entity_type', 'linked_entity_id'], schema='knowledge')
    
    # INTERACTION SCHEMA TABLES
    
    # interaction.question_session
    op.create_table(
        'question_session',
        sa.Column('session_id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('requesting_stakeholder_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('org.stakeholder.stakeholder_id'), nullable=False),
        sa.Column('persona_type', sa.String(80), nullable=False),
        sa.Column('primary_domain_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('knowledge.knowledge_domain.domain_id')),
        sa.Column('session_status', sa.String(40), nullable=False, server_default='active'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('last_activity_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('closed_at', sa.DateTime(timezone=True)),
        sa.CheckConstraint("session_status IN ('active', 'closed', 'expired')", name='session_status_check'),
        sa.CheckConstraint("persona_type IN ('new_joiner', 'engineer', 'stakeholder', 'support', 'admin')", name='session_persona_check'),
        schema='interaction'
    )
    op.create_index('idx_session_stakeholder', 'question_session', ['requesting_stakeholder_id'], schema='interaction')
    op.create_index('idx_session_domain', 'question_session', ['primary_domain_id'], schema='interaction')
    op.create_index('idx_session_status', 'question_session', ['session_status'], schema='interaction')
    op.create_index('idx_session_created', 'question_session', ['created_at'], schema='interaction')
    
    # interaction.session_access_scope
    op.create_table(
        'session_access_scope',
        sa.Column('scope_id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('session_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('interaction.question_session.session_id', ondelete='CASCADE'), nullable=False, unique=True),
        sa.Column('user_id', sa.String(255), nullable=False),
        sa.Column('role_snapshot', postgresql.JSONB, nullable=False),
        sa.Column('team_scope', postgresql.JSONB, nullable=False),
        sa.Column('source_scope_filter', postgresql.JSONB, nullable=False),
        sa.Column('cached_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        schema='interaction'
    )
    op.create_index('idx_session_access_scope_session', 'session_access_scope', ['session_id'], schema='interaction')
    op.create_index('idx_session_access_scope_expires', 'session_access_scope', ['expires_at'], schema='interaction')
    
    # interaction.question_turn
    op.create_table(
        'question_turn',
        sa.Column('turn_id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('session_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('interaction.question_session.session_id', ondelete='CASCADE'), nullable=False),
        sa.Column('turn_sequence', sa.Integer, nullable=False),
        sa.Column('question_text', sa.Text, nullable=False),
        sa.Column('intent_classification', postgresql.JSONB, nullable=False),
        sa.Column('ambiguity_state', sa.String(40), nullable=False, server_default='clear'),
        sa.Column('processing_status', sa.String(40), nullable=False, server_default='pending'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.CheckConstraint("ambiguity_state IN ('clear', 'ambiguous', 'clarified')", name='turn_ambiguity_check'),
        sa.CheckConstraint("processing_status IN ('pending', 'processing', 'completed', 'error')", name='turn_processing_check'),
        sa.UniqueConstraint('session_id', 'turn_sequence', name='turn_sequence_unique'),
        schema='interaction'
    )
    op.create_index('idx_question_turn_session', 'question_turn', ['session_id'], schema='interaction')
    op.create_index('idx_question_turn_created', 'question_turn', ['created_at'], schema='interaction')
    
    # interaction.answer_record
    op.create_table(
        'answer_record',
        sa.Column('answer_id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('turn_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('interaction.question_turn.turn_id', ondelete='CASCADE'), nullable=False),
        sa.Column('session_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('interaction.question_session.session_id', ondelete='CASCADE'), nullable=False),
        sa.Column('response_type', sa.String(40), nullable=False),
        sa.Column('answer_text', sa.Text),
        sa.Column('confidence_band', sa.String(40), nullable=False),
        sa.Column('confidence_score', sa.Numeric(5, 4)),
        sa.Column('citation_completeness_flag', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('escalation_required_flag', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('primary_domain_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('knowledge.knowledge_domain.domain_id')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.CheckConstraint("response_type IN ('supported_answer', 'clarification_required', 'limitation', 'escalation')", name='answer_response_type_check'),
        sa.CheckConstraint("confidence_band IN ('high', 'medium', 'low', 'insufficient')", name='answer_confidence_check'),
        schema='interaction'
    )
    op.create_index('idx_answer_turn', 'answer_record', ['turn_id'], schema='interaction')
    op.create_index('idx_answer_session', 'answer_record', ['session_id'], schema='interaction')
    op.create_index('idx_answer_domain', 'answer_record', ['primary_domain_id'], schema='interaction')
    op.create_index('idx_answer_response_type', 'answer_record', ['response_type'], schema='interaction')
    op.create_index('idx_answer_confidence', 'answer_record', ['confidence_band'], schema='interaction')
    op.create_index('idx_answer_created', 'answer_record', ['created_at'], schema='interaction')
    
    # interaction.answer_limitation
    op.create_table(
        'answer_limitation',
        sa.Column('limitation_id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('answer_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('interaction.answer_record.answer_id', ondelete='CASCADE'), nullable=False),
        sa.Column('limitation_type', sa.String(80), nullable=False),
        sa.Column('severity', sa.String(40), nullable=False),
        sa.Column('description', sa.Text, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.CheckConstraint("limitation_type IN ('missing_knowledge', 'stale_evidence', 'conflicting_evidence', 'restricted_access', 'ambiguous_question')", name='limitation_type_check'),
        sa.CheckConstraint("severity IN ('critical', 'high', 'medium', 'low')", name='limitation_severity_check'),
        schema='interaction'
    )
    op.create_index('idx_answer_limitation_answer', 'answer_limitation', ['answer_id'], schema='interaction')
    op.create_index('idx_answer_limitation_type', 'answer_limitation', ['limitation_type'], schema='interaction')
    op.create_index('idx_answer_limitation_severity', 'answer_limitation', ['severity'], schema='interaction')
    
    # interaction.citation_reference
    op.create_table(
        'citation_reference',
        sa.Column('citation_id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('answer_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('interaction.answer_record.answer_id', ondelete='CASCADE'), nullable=False),
        sa.Column('chunk_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('knowledge.source_chunk.chunk_id'), nullable=False),
        sa.Column('source_version_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('knowledge.source_version.source_version_id'), nullable=False),
        sa.Column('source_record_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('knowledge.source_record.source_record_id'), nullable=False),
        sa.Column('section_path', sa.Text, nullable=False),
        sa.Column('claim_text', sa.Text),
        sa.Column('freshness_warning', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('citation_order', sa.Integer, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.UniqueConstraint('answer_id', 'citation_order', name='citation_order_unique'),
        schema='interaction'
    )
    op.create_index('idx_citation_answer', 'citation_reference', ['answer_id'], schema='interaction')
    op.create_index('idx_citation_chunk', 'citation_reference', ['chunk_id'], schema='interaction')
    op.create_index('idx_citation_source_version', 'citation_reference', ['source_version_id'], schema='interaction')
    op.create_index('idx_citation_source_record', 'citation_reference', ['source_record_id'], schema='interaction')
    
    # interaction.feedback_record
    op.create_table(
        'feedback_record',
        sa.Column('feedback_id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('answer_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('interaction.answer_record.answer_id', ondelete='CASCADE'), nullable=False),
        sa.Column('stakeholder_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('org.stakeholder.stakeholder_id'), nullable=False),
        sa.Column('feedback_type', sa.String(80), nullable=False),
        sa.Column('feedback_comment', sa.Text),
        sa.Column('steward_action_required', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.CheckConstraint("feedback_type IN ('helpful', 'incomplete', 'stale', 'unclear', 'incorrect')", name='feedback_type_check'),
        schema='interaction'
    )
    op.create_index('idx_feedback_answer', 'feedback_record', ['answer_id'], schema='interaction')
    op.create_index('idx_feedback_stakeholder', 'feedback_record', ['stakeholder_id'], schema='interaction')
    op.create_index('idx_feedback_type', 'feedback_record', ['feedback_type'], schema='interaction')
    op.create_index('idx_feedback_steward_action', 'feedback_record', ['steward_action_required'], schema='interaction', postgresql_where=sa.text('steward_action_required = true'))
    op.create_index('idx_feedback_created', 'feedback_record', ['created_at'], schema='interaction')
    
    # interaction.feedback_review
    op.create_table(
        'feedback_review',
        sa.Column('review_id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('feedback_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('interaction.feedback_record.feedback_id', ondelete='CASCADE'), nullable=False),
        sa.Column('reviewer_stakeholder_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('org.stakeholder.stakeholder_id'), nullable=False),
        sa.Column('review_status', sa.String(40), nullable=False, server_default='pending'),
        sa.Column('resolution_code', sa.String(80)),
        sa.Column('resolution_notes', sa.Text),
        sa.Column('reviewed_at', sa.DateTime(timezone=True)),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.CheckConstraint("review_status IN ('pending', 'in_progress', 'resolved', 'escalated')", name='feedback_review_status_check'),
        sa.CheckConstraint("resolution_code IN ('acknowledged', 'source_updated', 'policy_clarified', 'escalated', 'no_action')", name='feedback_review_resolution_check'),
        schema='interaction'
    )
    op.create_index('idx_feedback_review_feedback', 'feedback_review', ['feedback_id'], schema='interaction')
    op.create_index('idx_feedback_review_reviewer', 'feedback_review', ['reviewer_stakeholder_id'], schema='interaction')
    op.create_index('idx_feedback_review_status', 'feedback_review', ['review_status'], schema='interaction')
    
    # GOVERNANCE SCHEMA TABLES
    
    # governance.access_policy
    op.create_table(
        'access_policy',
        sa.Column('policy_id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('policy_code', sa.String(80), nullable=False, unique=True),
        sa.Column('policy_name', sa.String(255), nullable=False),
        sa.Column('policy_type', sa.String(80), nullable=False),
        sa.Column('scope_expression', postgresql.JSONB, nullable=False),
        sa.Column('mfa_required', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('status', sa.String(40), nullable=False, server_default='active'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.CheckConstraint("policy_type IN ('source_access', 'domain_access', 'admin_function', 'governance_function')", name='policy_type_check'),
        sa.CheckConstraint("status IN ('active', 'inactive', 'archived')", name='policy_status_check'),
        schema='governance'
    )
    op.create_index('idx_access_policy_code', 'access_policy', ['policy_code'], schema='governance')
    op.create_index('idx_access_policy_type', 'access_policy', ['policy_type'], schema='governance')
    op.create_index('idx_access_policy_status', 'access_policy', ['status'], schema='governance')
    
    # governance.access_policy_binding
    op.create_table(
        'access_policy_binding',
        sa.Column('binding_id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('policy_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('governance.access_policy.policy_id', ondelete='CASCADE'), nullable=False),
        sa.Column('principal_type', sa.String(80), nullable=False),
        sa.Column('principal_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('effective_from', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('effective_until', sa.DateTime(timezone=True)),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.CheckConstraint("principal_type IN ('stakeholder', 'team', 'stakeholder_group')", name='policy_binding_principal_check'),
        sa.UniqueConstraint('policy_id', 'principal_type', 'principal_id', 'effective_from', name='policy_binding_unique'),
        schema='governance'
    )
    op.create_index('idx_policy_binding_policy', 'access_policy_binding', ['policy_id'], schema='governance')
    op.create_index('idx_policy_binding_principal', 'access_policy_binding', ['principal_type', 'principal_id'], schema='governance')
    op.create_index('idx_policy_binding_effective', 'access_policy_binding', ['effective_from', 'effective_until'], schema='governance')
    
    # governance.escalation_route
    op.create_table(
        'escalation_route',
        sa.Column('route_id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('route_code', sa.String(80), nullable=False, unique=True),
        sa.Column('route_name', sa.String(255), nullable=False),
        sa.Column('domain_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('knowledge.knowledge_domain.domain_id')),
        sa.Column('service_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('org.service_entity.service_id')),
        sa.Column('status', sa.String(40), nullable=False, server_default='active'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.CheckConstraint("status IN ('active', 'inactive', 'archived')", name='escalation_route_status_check'),
        schema='governance'
    )
    op.create_index('idx_escalation_route_code', 'escalation_route', ['route_code'], schema='governance')
    op.create_index('idx_escalation_route_domain', 'escalation_route', ['domain_id'], schema='governance')
    op.create_index('idx_escalation_route_service', 'escalation_route', ['service_id'], schema='governance')
    op.create_index('idx_escalation_route_status', 'escalation_route', ['status'], schema='governance')
    
    # governance.escalation_route_step
    op.create_table(
        'escalation_route_step',
        sa.Column('step_id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('route_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('governance.escalation_route.route_id', ondelete='CASCADE'), nullable=False),
        sa.Column('step_order', sa.Integer, nullable=False),
        sa.Column('contact_type', sa.String(80), nullable=False),
        sa.Column('contact_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('contact_channel', sa.String(255)),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.CheckConstraint("contact_type IN ('stakeholder', 'team', 'channel')", name='escalation_step_contact_check'),
        sa.UniqueConstraint('route_id', 'step_order', name='escalation_step_unique'),
        schema='governance'
    )
    op.create_index('idx_escalation_step_route', 'escalation_route_step', ['route_id'], schema='governance')
    op.create_index('idx_escalation_step_contact', 'escalation_route_step', ['contact_type', 'contact_id'], schema='governance')
    
    # OPS SCHEMA TABLES
    
    # ops.ingestion_run
    op.create_table(
        'ingestion_run',
        sa.Column('run_id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('run_type', sa.String(80), nullable=False),
        sa.Column('run_status', sa.String(40), nullable=False, server_default='pending'),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('completed_at', sa.DateTime(timezone=True)),
        sa.Column('error_message', sa.Text),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.CheckConstraint("run_type IN ('full', 'incremental', 'manual')", name='ingestion_run_type_check'),
        sa.CheckConstraint("run_status IN ('pending', 'running', 'completed', 'failed')", name='ingestion_run_status_check'),
        schema='ops'
    )
    op.create_index('idx_ingestion_run_status', 'ingestion_run', ['run_status'], schema='ops')
    op.create_index('idx_ingestion_run_started', 'ingestion_run', ['started_at'], schema='ops')
    
    # ops.ingestion_run_item
    op.create_table(
        'ingestion_run_item',
        sa.Column('item_id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('run_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('ops.ingestion_run.run_id', ondelete='CASCADE'), nullable=False),
        sa.Column('source_record_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('knowledge.source_record.source_record_id'), nullable=False),
        sa.Column('item_status', sa.String(40), nullable=False, server_default='pending'),
        sa.Column('chunks_created', sa.Integer, server_default='0'),
        sa.Column('error_message', sa.Text),
        sa.Column('started_at', sa.DateTime(timezone=True)),
        sa.Column('completed_at', sa.DateTime(timezone=True)),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.CheckConstraint("item_status IN ('pending', 'processing', 'completed', 'failed', 'skipped')", name='ingestion_item_status_check'),
        schema='ops'
    )
    op.create_index('idx_ingestion_item_run', 'ingestion_run_item', ['run_id'], schema='ops')
    op.create_index('idx_ingestion_item_source', 'ingestion_run_item', ['source_record_id'], schema='ops')
    op.create_index('idx_ingestion_item_status', 'ingestion_run_item', ['item_status'], schema='ops')
    
    # ops.audit_event
    op.create_table(
        'audit_event',
        sa.Column('audit_event_id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('event_type', sa.String(80), nullable=False),
        sa.Column('actor_type', sa.String(80), nullable=False),
        sa.Column('actor_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('subject_type', sa.String(80)),
        sa.Column('subject_id', postgresql.UUID(as_uuid=True)),
        sa.Column('result_code', sa.String(40), nullable=False),
        sa.Column('event_metadata', postgresql.JSONB),
        sa.Column('occurred_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('archive_date', sa.Date),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.CheckConstraint("actor_type IN ('stakeholder', 'system', 'service')", name='audit_event_actor_check'),
        sa.CheckConstraint("result_code IN ('success', 'failure', 'partial', 'denied')", name='audit_event_result_check'),
        schema='ops'
    )
    op.create_index('idx_audit_event_type', 'audit_event', ['event_type'], schema='ops')
    op.create_index('idx_audit_event_actor', 'audit_event', ['actor_type', 'actor_id'], schema='ops')
    op.create_index('idx_audit_event_subject', 'audit_event', ['subject_type', 'subject_id'], schema='ops')
    op.create_index('idx_audit_event_occurred', 'audit_event', ['occurred_at'], schema='ops')
    op.create_index('idx_audit_event_archive', 'audit_event', ['archive_date'], schema='ops', postgresql_where=sa.text('archive_date IS NOT NULL'))
    
    # ops.privacy_request_link
    op.create_table(
        'privacy_request_link',
        sa.Column('link_id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('privacy_request_ref', sa.String(255), nullable=False),
        sa.Column('linked_entity_type', sa.String(80), nullable=False),
        sa.Column('linked_entity_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('action_type', sa.String(80), nullable=False),
        sa.Column('action_status', sa.String(40), nullable=False, server_default='pending'),
        sa.Column('completed_at', sa.DateTime(timezone=True)),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.CheckConstraint("action_type IN ('restrict', 'export', 'delete')", name='privacy_action_type_check'),
        sa.CheckConstraint("action_status IN ('pending', 'in_progress', 'completed', 'failed')", name='privacy_action_status_check'),
        sa.UniqueConstraint('privacy_request_ref', 'linked_entity_type', 'linked_entity_id', name='privacy_link_unique'),
        schema='ops'
    )
    op.create_index('idx_privacy_link_request', 'privacy_request_link', ['privacy_request_ref'], schema='ops')
    op.create_index('idx_privacy_link_entity', 'privacy_request_link', ['linked_entity_type', 'linked_entity_id'], schema='ops')
    op.create_index('idx_privacy_link_status', 'privacy_request_link', ['action_status'], schema='ops')
    
    # ops.graph_sync_batch
    op.create_table(
        'graph_sync_batch',
        sa.Column('batch_id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('sync_type', sa.String(80), nullable=False),
        sa.Column('sync_status', sa.String(40), nullable=False, server_default='pending'),
        sa.Column('entities_synced', sa.Integer, server_default='0'),
        sa.Column('relationships_synced', sa.Integer, server_default='0'),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('completed_at', sa.DateTime(timezone=True)),
        sa.Column('error_message', sa.Text),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.CheckConstraint("sync_type IN ('full', 'incremental', 'manual')", name='graph_sync_type_check'),
        sa.CheckConstraint("sync_status IN ('pending', 'running', 'completed', 'failed')", name='graph_sync_status_check'),
        schema='ops'
    )
    op.create_index('idx_graph_sync_status', 'graph_sync_batch', ['sync_status'], schema='ops')
    op.create_index('idx_graph_sync_started', 'graph_sync_batch', ['started_at'], schema='ops')


def downgrade() -> None:
    # Drop all tables in reverse order
    op.drop_table('graph_sync_batch', schema='ops')
    op.drop_table('privacy_request_link', schema='ops')
    op.drop_table('audit_event', schema='ops')
    op.drop_table('ingestion_run_item', schema='ops')
    op.drop_table('ingestion_run', schema='ops')
    
    op.drop_table('escalation_route_step', schema='governance')
    op.drop_table('escalation_route', schema='governance')
    op.drop_table('access_policy_binding', schema='governance')
    op.drop_table('access_policy', schema='governance')
    
    op.drop_table('feedback_review', schema='interaction')
    op.drop_table('feedback_record', schema='interaction')
    op.drop_table('citation_reference', schema='interaction')
    op.drop_table('answer_limitation', schema='interaction')
    op.drop_table('answer_record', schema='interaction')
    op.drop_table('question_turn', schema='interaction')
    op.drop_table('session_access_scope', schema='interaction')
    op.drop_table('question_session', schema='interaction')
    
    op.drop_table('source_record_link', schema='knowledge')
    op.drop_table('chunk_relationship_assertion', schema='knowledge')
    op.drop_table('source_chunk', schema='knowledge')
    op.drop_table('source_review', schema='knowledge')
    op.drop_table('source_version', schema='knowledge')
    op.drop_table('source_record', schema='knowledge')
    op.drop_table('knowledge_domain_assignment', schema='knowledge')
    op.drop_table('knowledge_domain', schema='knowledge')
    
    op.drop_table('service_dependency', schema='org')
    op.drop_table('service_entity', schema='org')
    op.drop_table('team_membership', schema='org')
    op.drop_table('team', schema='org')
    op.drop_table('stakeholder', schema='org')
    
    # Drop schemas
    op.execute('DROP SCHEMA IF EXISTS ops CASCADE')
    op.execute('DROP SCHEMA IF EXISTS governance CASCADE')
    op.execute('DROP SCHEMA IF EXISTS interaction CASCADE')
    op.execute('DROP SCHEMA IF EXISTS knowledge CASCADE')
    op.execute('DROP SCHEMA IF EXISTS org CASCADE')
