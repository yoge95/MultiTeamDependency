"""Seed database with default admin user and sample data."""

import sys
import os
from datetime import datetime, timedelta, date
from uuid import UUID, uuid4

# Ensure DATABASE_URL is set before importing models
if 'DATABASE_URL' not in os.environ:
    os.environ['DATABASE_URL'] = 'sqlite:///./app.db'

from sqlalchemy.orm import Session

from app.database import SessionLocal, engine, Base
from app.models.org import Team, Stakeholder, TeamMembership, ServiceEntity, ServiceDependency
from app.models.knowledge import (
    KnowledgeDomain,
    KnowledgeDomainAssignment,
    SourceRecord,
    SourceVersion,
    SourceReview,
    SourceChunk,
)


def seed_database():
    """Seed database with default admin user and comprehensive sample data."""
    # Ensure tables are created before seeding
    from app.database import init_db
    init_db()
    
    db = SessionLocal()
    try:
        # Check if admin already exists (idempotency)
        existing_admin = db.query(Stakeholder).filter_by(email="admin@example.com").first()
        if existing_admin:
            print("✓ Admin user already exists, skipping seed data creation")
            return

        print("Seeding database with default credentials and sample data...")

        # Create default admin user
        admin = Stakeholder(
            stakeholder_id=uuid4(),
            employee_ref="EMP-ADMIN-001",
            display_name="Platform Administrator",
            stakeholder_type="platform_administrator",
            email="admin@example.com",
            timezone="America/Los_Angeles",
            privileged_account=True,
            account_status="active",
        )
        db.add(admin)
        db.flush()

        # Create knowledge steward users (3-5 users)
        stewards = []
        steward_data = [
            {
                "employee_ref": "EMP-KS-001",
                "display_name": "Alice Johnson",
                "email": "alice.johnson@example.com",
                "timezone": "America/New_York",
            },
            {
                "employee_ref": "EMP-KS-002",
                "display_name": "Bob Chen",
                "email": "bob.chen@example.com",
                "timezone": "America/Chicago",
            },
            {
                "employee_ref": "EMP-KS-003",
                "display_name": "Carol Martinez",
                "email": "carol.martinez@example.com",
                "timezone": "America/Los_Angeles",
            },
            {
                "employee_ref": "EMP-KS-004",
                "display_name": "David Kim",
                "email": "david.kim@example.com",
                "timezone": "America/Denver",
            },
        ]

        for data in steward_data:
            steward = Stakeholder(
                stakeholder_id=uuid4(),
                employee_ref=data["employee_ref"],
                display_name=data["display_name"],
                stakeholder_type="knowledge_steward",
                email=data["email"],
                timezone=data["timezone"],
                privileged_account=False,
                account_status="active",
            )
            stewards.append(steward)
            db.add(steward)
        
        db.flush()

        # Create end users (5-10 users)
        end_users = []
        end_user_data = [
            {
                "employee_ref": "EMP-EU-001",
                "display_name": "Emma Wilson",
                "email": "emma.wilson@example.com",
                "timezone": "America/New_York",
            },
            {
                "employee_ref": "EMP-EU-002",
                "display_name": "Frank Lee",
                "email": "frank.lee@example.com",
                "timezone": "America/Chicago",
            },
            {
                "employee_ref": "EMP-EU-003",
                "display_name": "Grace Patel",
                "email": "grace.patel@example.com",
                "timezone": "America/Los_Angeles",
            },
            {
                "employee_ref": "EMP-EU-004",
                "display_name": "Henry Brown",
                "email": "henry.brown@example.com",
                "timezone": "America/Denver",
            },
            {
                "employee_ref": "EMP-EU-005",
                "display_name": "Iris Taylor",
                "email": "iris.taylor@example.com",
                "timezone": "America/New_York",
            },
            {
                "employee_ref": "EMP-EU-006",
                "display_name": "Jack Robinson",
                "email": "jack.robinson@example.com",
                "timezone": "America/Chicago",
            },
            {
                "employee_ref": "EMP-EU-007",
                "display_name": "Karen White",
                "email": "karen.white@example.com",
                "timezone": "America/Los_Angeles",
            },
            {
                "employee_ref": "EMP-EU-008",
                "display_name": "Luis Garcia",
                "email": "luis.garcia@example.com",
                "timezone": "America/Denver",
            },
        ]

        for data in end_user_data:
            user = Stakeholder(
                stakeholder_id=uuid4(),
                employee_ref=data["employee_ref"],
                display_name=data["display_name"],
                stakeholder_type="end_user",
                email=data["email"],
                timezone=data["timezone"],
                privileged_account=False,
                account_status="active",
            )
            end_users.append(user)
            db.add(user)
        
        db.flush()

        # Create teams (5-10 teams)
        teams = []
        team_data = [
            {
                "team_code": "PLATFORM",
                "team_name": "Platform Engineering",
                "team_type": "engineering",
                "primary_owner": stewards[0],
                "support_channel": "#platform-support",
            },
            {
                "team_code": "AUTH",
                "team_name": "Authentication Services",
                "team_type": "engineering",
                "primary_owner": stewards[1],
                "support_channel": "#auth-team",
            },
            {
                "team_code": "PAYMENTS",
                "team_name": "Payment Processing",
                "team_type": "engineering",
                "primary_owner": stewards[2],
                "support_channel": "#payments-team",
            },
            {
                "team_code": "DATA",
                "team_name": "Data Engineering",
                "team_type": "engineering",
                "primary_owner": stewards[3],
                "support_channel": "#data-engineering",
            },
            {
                "team_code": "FRONTEND",
                "team_name": "Frontend Platform",
                "team_type": "engineering",
                "primary_owner": stewards[0],
                "support_channel": "#frontend-platform",
            },
            {
                "team_code": "INFRA",
                "team_name": "Infrastructure & DevOps",
                "team_type": "operations",
                "primary_owner": stewards[1],
                "support_channel": "#infrastructure",
            },
            {
                "team_code": "SECURITY",
                "team_name": "Security & Compliance",
                "team_type": "security",
                "primary_owner": stewards[2],
                "support_channel": "#security-team",
            },
            {
                "team_code": "SUPPORT",
                "team_name": "Customer Support",
                "team_type": "support",
                "primary_owner": stewards[3],
                "support_channel": "#customer-support",
            },
        ]

        for data in team_data:
            team = Team(
                team_id=uuid4(),
                team_code=data["team_code"],
                team_name=data["team_name"],
                team_type=data["team_type"],
                primary_owner_stakeholder_id=data["primary_owner"].stakeholder_id,
                support_channel=data["support_channel"],
                status="active",
                last_reviewed_at=datetime.utcnow() - timedelta(days=15),
            )
            teams.append(team)
            db.add(team)
        
        db.flush()

        # Create team memberships (10-20 stakeholders with team memberships)
        memberships = []
        
        # Admin is member of Platform team
        memberships.append(
            TeamMembership(
                team_id=teams[0].team_id,
                stakeholder_id=admin.stakeholder_id,
                role="owner",
                effective_from=datetime.utcnow() - timedelta(days=180),
            )
        )

        # Stewards are owners of their respective teams
        for i, steward in enumerate(stewards[:len(teams)]):
            if i < len(teams):
                memberships.append(
                    TeamMembership(
                        team_id=teams[i].team_id,
                        stakeholder_id=steward.stakeholder_id,
                        role="owner",
                        effective_from=datetime.utcnow() - timedelta(days=120),
                    )
                )

        # End users are members of various teams
        for i, user in enumerate(end_users):
            team_idx = i % len(teams)
            memberships.append(
                TeamMembership(
                    team_id=teams[team_idx].team_id,
                    stakeholder_id=user.stakeholder_id,
                    role="member",
                    effective_from=datetime.utcnow() - timedelta(days=90),
                )
            )
        
        for membership in memberships:
            db.add(membership)
        
        db.flush()

        # Create knowledge domains (5-7 domains)
        domains = []
        domain_data = [
            {
                "domain_code": "ONBOARDING",
                "domain_name": "Onboarding & New Hire Resources",
                "category": "onboarding",
                "steward_team": teams[0],
                "stale_after_days": 90,
                "governance_sensitive": False,
            },
            {
                "domain_code": "OWNERSHIP",
                "domain_name": "Service & Team Ownership",
                "category": "ownership",
                "steward_team": teams[0],
                "stale_after_days": 90,
                "governance_sensitive": True,
            },
            {
                "domain_code": "DEPENDENCIES",
                "domain_name": "Service Dependencies & Architecture",
                "category": "dependencies",
                "steward_team": teams[3],
                "stale_after_days": 90,
                "governance_sensitive": False,
            },
            {
                "domain_code": "RUNBOOKS",
                "domain_name": "Operational Runbooks & Procedures",
                "category": "runbooks",
                "steward_team": teams[5],
                "stale_after_days": 90,
                "governance_sensitive": False,
            },
            {
                "domain_code": "GOVERNANCE",
                "domain_name": "Governance & Compliance",
                "category": "governance",
                "steward_team": teams[6],
                "stale_after_days": 180,
                "governance_sensitive": True,
            },
            {
                "domain_code": "OPERATIONS",
                "domain_name": "Operations & Monitoring",
                "category": "process",
                "steward_team": teams[5],
                "stale_after_days": 90,
                "governance_sensitive": False,
            },
            {
                "domain_code": "PROCESS",
                "domain_name": "Engineering Processes & Standards",
                "category": "process",
                "steward_team": teams[0],
                "stale_after_days": 180,
                "governance_sensitive": False,
            },
        ]

        for data in domain_data:
            domain = KnowledgeDomain(
                domain_id=uuid4(),
                domain_code=data["domain_code"],
                domain_name=data["domain_name"],
                category=data["category"],
                steward_team_id=data["steward_team"].team_id,
                stale_after_days=data["stale_after_days"],
                governance_sensitive=data["governance_sensitive"],
            )
            domains.append(domain)
            db.add(domain)
        
        db.flush()

        # Create domain assignments
        for domain in domains:
            assignment = KnowledgeDomainAssignment(
                domain_id=domain.domain_id,
                team_id=domain.steward_team_id,
                assignment_type="steward",
                effective_from=datetime.utcnow() - timedelta(days=180),
            )
            db.add(assignment)
        
        db.flush()

        # Create services (5-10 services)
        services = []
        service_data = [
            {
                "service_code": "auth-api",
                "service_name": "Authentication API",
                "owning_team": teams[1],
                "lifecycle_state": "active",
                "environment_scope": "production",
                "auth_dependency_flag": False,
                "payment_domain_related": False,
            },
            {
                "service_code": "payment-api",
                "service_name": "Payment Processing API",
                "owning_team": teams[2],
                "lifecycle_state": "active",
                "environment_scope": "production",
                "auth_dependency_flag": True,
                "payment_domain_related": True,
            },
            {
                "service_code": "user-service",
                "service_name": "User Profile Service",
                "owning_team": teams[0],
                "lifecycle_state": "active",
                "environment_scope": "production",
                "auth_dependency_flag": True,
                "payment_domain_related": False,
            },
            {
                "service_code": "knowledge-assistant",
                "service_name": "Knowledge Assistant API",
                "owning_team": teams[0],
                "lifecycle_state": "active",
                "environment_scope": "production",
                "auth_dependency_flag": True,
                "payment_domain_related": False,
            },
            {
                "service_code": "notification-service",
                "service_name": "Notification Service",
                "owning_team": teams[0],
                "lifecycle_state": "active",
                "environment_scope": "production",
                "auth_dependency_flag": True,
                "payment_domain_related": False,
            },
            {
                "service_code": "analytics-service",
                "service_name": "Analytics & Reporting",
                "owning_team": teams[3],
                "lifecycle_state": "active",
                "environment_scope": "production",
                "auth_dependency_flag": True,
                "payment_domain_related": False,
            },
            {
                "service_code": "search-indexer",
                "service_name": "Search Indexing Service",
                "owning_team": teams[3],
                "lifecycle_state": "active",
                "environment_scope": "production",
                "auth_dependency_flag": False,
                "payment_domain_related": False,
            },
            {
                "service_code": "api-gateway",
                "service_name": "API Gateway",
                "owning_team": teams[5],
                "lifecycle_state": "active",
                "environment_scope": "production",
                "auth_dependency_flag": True,
                "payment_domain_related": False,
            },
        ]

        for data in service_data:
            service = ServiceEntity(
                service_id=uuid4(),
                service_code=data["service_code"],
                service_name=data["service_name"],
                owning_team_id=data["owning_team"].team_id,
                lifecycle_state=data["lifecycle_state"],
                environment_scope=data["environment_scope"],
                auth_dependency_flag=data["auth_dependency_flag"],
                payment_domain_related=data["payment_domain_related"],
            )
            services.append(service)
            db.add(service)
        
        db.flush()

        # Create service dependencies (DEPENDS_ON relationships)
        dependencies = [
            # API Gateway depends on Auth API
            {
                "upstream": services[0],  # auth-api
                "downstream": services[7],  # api-gateway
                "dependency_type": "auth",
                "criticality": "critical",
            },
            # Payment API depends on Auth API
            {
                "upstream": services[0],  # auth-api
                "downstream": services[1],  # payment-api
                "dependency_type": "auth",
                "criticality": "critical",
            },
            # User Service depends on Auth API
            {
                "upstream": services[0],  # auth-api
                "downstream": services[2],  # user-service
                "dependency_type": "auth",
                "criticality": "critical",
            },
            # Knowledge Assistant depends on Auth API
            {
                "upstream": services[0],  # auth-api
                "downstream": services[3],  # knowledge-assistant
                "dependency_type": "auth",
                "criticality": "critical",
            },
            # Knowledge Assistant depends on User Service
            {
                "upstream": services[2],  # user-service
                "downstream": services[3],  # knowledge-assistant
                "dependency_type": "api",
                "criticality": "high",
            },
            # Analytics depends on User Service
            {
                "upstream": services[2],  # user-service
                "downstream": services[5],  # analytics-service
                "dependency_type": "data",
                "criticality": "medium",
            },
            # Search Indexer depends on Knowledge Assistant
            {
                "upstream": services[3],  # knowledge-assistant
                "downstream": services[6],  # search-indexer
                "dependency_type": "data",
                "criticality": "high",
            },
            # Payment API depends on User Service
            {
                "upstream": services[2],  # user-service
                "downstream": services[1],  # payment-api
                "dependency_type": "api",
                "criticality": "high",
            },
            # Notification Service depends on User Service
            {
                "upstream": services[2],  # user-service
                "downstream": services[4],  # notification-service
                "dependency_type": "api",
                "criticality": "medium",
            },
        ]

        for dep_data in dependencies:
            dependency = ServiceDependency(
                upstream_service_id=dep_data["upstream"].service_id,
                downstream_service_id=dep_data["downstream"].service_id,
                dependency_type=dep_data["dependency_type"],
                criticality=dep_data["criticality"],
                evidence_strength="verified",
                last_verified_at=datetime.utcnow() - timedelta(days=7),
            )
            db.add(dependency)
        
        db.flush()

        # Create source records (10-15 sources with mix of approval states)
        sources = []
        source_data = [
            {
                "source_key": "onboarding-guide-2024",
                "title": "New Engineer Onboarding Guide 2024",
                "source_type": "document",
                "domain": domains[0],  # ONBOARDING
                "owner_team": teams[0],
                "steward_team": teams[0],
                "approval_state": "approved",
                "sensitivity": "internal",
            },
            {
                "source_key": "team-ownership-map-q4-2024",
                "title": "Team Ownership Map Q4 2024",
                "source_type": "spreadsheet",
                "domain": domains[1],  # OWNERSHIP
                "owner_team": teams[0],
                "steward_team": teams[0],
                "approval_state": "approved",
                "sensitivity": "internal",
            },
            {
                "source_key": "service-dependency-graph",
                "title": "Service Dependency Graph",
                "source_type": "diagram",
                "domain": domains[2],  # DEPENDENCIES
                "owner_team": teams[3],
                "steward_team": teams[3],
                "approval_state": "approved",
                "sensitivity": "internal",
            },
            {
                "source_key": "payment-api-runbook",
                "title": "Payment API Operational Runbook",
                "source_type": "document",
                "domain": domains[3],  # RUNBOOKS
                "owner_team": teams[2],
                "steward_team": teams[5],
                "approval_state": "approved",
                "sensitivity": "confidential",
            },
            {
                "source_key": "auth-service-runbook",
                "title": "Auth Service Incident Response",
                "source_type": "document",
                "domain": domains[3],  # RUNBOOKS
                "owner_team": teams[1],
                "steward_team": teams[5],
                "approval_state": "approved",
                "sensitivity": "internal",
            },
            {
                "source_key": "soc2-compliance-checklist",
                "title": "SOC2 Compliance Checklist",
                "source_type": "document",
                "domain": domains[4],  # GOVERNANCE
                "owner_team": teams[6],
                "steward_team": teams[6],
                "approval_state": "approved",
                "sensitivity": "restricted",
            },
            {
                "source_key": "deployment-procedures",
                "title": "Production Deployment Procedures",
                "source_type": "document",
                "domain": domains[5],  # OPERATIONS
                "owner_team": teams[5],
                "steward_team": teams[5],
                "approval_state": "approved",
                "sensitivity": "internal",
            },
            {
                "source_key": "code-review-guidelines",
                "title": "Code Review Guidelines",
                "source_type": "document",
                "domain": domains[6],  # PROCESS
                "owner_team": teams[0],
                "steward_team": teams[0],
                "approval_state": "approved",
                "sensitivity": "public",
            },
            {
                "source_key": "pending-architecture-doc",
                "title": "Microservices Architecture Proposal",
                "source_type": "document",
                "domain": domains[2],  # DEPENDENCIES
                "owner_team": teams[0],
                "steward_team": teams[3],
                "approval_state": "pending",
                "sensitivity": "internal",
            },
            {
                "source_key": "pending-security-policy",
                "title": "Security Policy Update Draft",
                "source_type": "document",
                "domain": domains[4],  # GOVERNANCE
                "owner_team": teams[6],
                "steward_team": teams[6],
                "approval_state": "pending",
                "sensitivity": "restricted",
            },
            {
                "source_key": "rejected-old-process",
                "title": "Deprecated Release Process",
                "source_type": "document",
                "domain": domains[6],  # PROCESS
                "owner_team": teams[5],
                "steward_team": teams[5],
                "approval_state": "rejected",
                "sensitivity": "internal",
            },
            {
                "source_key": "escalation-contacts",
                "title": "Escalation Contact List",
                "source_type": "spreadsheet",
                "domain": domains[1],  # OWNERSHIP
                "owner_team": teams[0],
                "steward_team": teams[0],
                "approval_state": "approved",
                "sensitivity": "internal",
            },
            {
                "source_key": "api-documentation",
                "title": "API Integration Guide",
                "source_type": "document",
                "domain": domains[2],  # DEPENDENCIES
                "owner_team": teams[0],
                "steward_team": teams[3],
                "approval_state": "approved",
                "sensitivity": "internal",
            },
            {
                "source_key": "monitoring-setup",
                "title": "Monitoring & Alerting Setup",
                "source_type": "document",
                "domain": domains[5],  # OPERATIONS
                "owner_team": teams[5],
                "steward_team": teams[5],
                "approval_state": "approved",
                "sensitivity": "internal",
            },
            {
                "source_key": "incident-postmortem-template",
                "title": "Incident Postmortem Template",
                "source_type": "document",
                "domain": domains[5],  # OPERATIONS
                "owner_team": teams[5],
                "steward_team": teams[5],
                "approval_state": "approved",
                "sensitivity": "internal",
            },
        ]

        for data in source_data:
            next_review = None
            if data["approval_state"] == "approved":
                next_review = date.today() + timedelta(days=data["domain"].stale_after_days)
            
            source = SourceRecord(
                source_record_id=uuid4(),
                source_key=data["source_key"],
                title=data["title"],
                source_type=data["source_type"],
                domain_id=data["domain"].domain_id,
                owner_team_id=data["owner_team"].team_id,
                steward_team_id=data["steward_team"].team_id,
                approval_state=data["approval_state"],
                sensitivity_classification=data["sensitivity"],
                next_review_due_on=next_review,
                retention_days=365,
            )
            sources.append(source)
            db.add(source)
        
        db.flush()

        # Create source versions and reviews for approved sources
        for source in sources:
            if source.approval_state == "approved":
                # Create active version
                version = SourceVersion(
                    source_record_id=source.source_record_id,
                    version_number=1,
                    content_hash=f"sha256-{source.source_key}-v1",
                    storage_uri=f"s3://knowledge-sources/{source.source_key}/v1.pdf",
                    is_active=True,
                    extracted_at=datetime.utcnow() - timedelta(days=30),
                )
                db.add(version)
                db.flush()

                # Create source review
                reviewer = stewards[0] if source.steward_team_id == teams[0].team_id else stewards[1]
                review = SourceReview(
                    source_record_id=source.source_record_id,
                    reviewer_stakeholder_id=reviewer.stakeholder_id,
                    review_decision="approved",
                    freshness_exception_granted=False,
                    next_review_due_on=source.next_review_due_on,
                    review_notes="Initial approval during onboarding",
                    reviewed_at=datetime.utcnow() - timedelta(days=25),
                )
                db.add(review)

                # Create sample chunks for this version
                chunk_contents = [
                    f"Introduction to {source.title}. This document provides comprehensive guidance on {source.source_type} related topics.",
                    f"Section 1: Overview. The {source.title} covers essential information for team members to understand key concepts.",
                    f"Section 2: Best Practices. Follow these recommended approaches when working with related systems and processes.",
                ]

                for i, content in enumerate(chunk_contents):
                    chunk = SourceChunk(
                        chunk_id=uuid4(),
                        source_version_id=version.source_version_id,
                        section_path=f"/section_{i+1}",
                        chunk_order=i,
                        content=content,
                        token_count=len(content.split()),
                        access_scope_tag=source.sensitivity_classification,
                        freshness_state="current",
                    )
                    db.add(chunk)
        
        db.flush()

        # Commit all changes
        db.commit()
        
        print("✓ Database seeded successfully!")
        print(f"✓ Created admin user: admin@example.com / admin123")
        print(f"✓ Created {len(stewards)} knowledge stewards")
        print(f"✓ Created {len(end_users)} end users")
        print(f"✓ Created {len(teams)} teams")
        print(f"✓ Created {len(memberships)} team memberships")
        print(f"✓ Created {len(domains)} knowledge domains")
        print(f"✓ Created {len(services)} services")
        print(f"✓ Created {len(dependencies)} service dependencies")
        print(f"✓ Created {len(sources)} source records")

    except Exception as e:
        db.rollback()
        print(f"✗ Error seeding database: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    # Allow running as standalone script
    print("Running seed script...")
    seed_database()
