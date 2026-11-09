"""Tests for source governance API endpoints."""

import pytest
from uuid import uuid4
from datetime import date, datetime, timedelta

from app.models.knowledge import KnowledgeDomain, SourceRecord, SourceReview
from app.models.org import Team


@pytest.fixture
def mock_domain(db_session):
    """Create a mock knowledge domain."""
    team = Team(
        team_id=uuid4(),
        team_code="TEST",
        team_name="Test Team",
        team_type="engineering",
        status="active",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(team)
    
    domain = KnowledgeDomain(
        domain_id=uuid4(),
        domain_code="TEST_DOMAIN",
        domain_name="Test Domain",
        category="ownership",
        steward_team_id=team.team_id,
        stale_after_days=90,
        governance_sensitive=False,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(domain)
    db_session.commit()
    return domain


@pytest.fixture
def mock_source(db_session, mock_domain):
    """Create a mock source record."""
    team = db_session.query(Team).first()
    
    source = SourceRecord(
        source_record_id=uuid4(),
        source_key="TEST_SOURCE_001",
        title="Test Source",
        source_type="confluence",
        domain_id=mock_domain.domain_id,
        owner_team_id=team.team_id,
        steward_team_id=team.team_id,
        approval_state="pending",
        sensitivity_classification="internal",
        retention_days=365,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(source)
    db_session.commit()
    return source


def test_list_sources_as_steward(client, mock_source, mock_domain, mock_auth_user):
    """Test listing sources as knowledge_steward."""
    # Mock user as steward with access to domain
    mock_auth_user.roles = ["knowledge_steward"]
    mock_auth_user.access_scope.roles = ["knowledge_steward"]
    mock_auth_user.access_scope.roles = ["knowledge_steward"]
    mock_auth_user.access_scope.accessible_domains = [mock_domain.domain_id]
    
    response = client.get("/api/v1/sources/")
    
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert data["total"] >= 1
    assert len(data["items"]) >= 1
    
    # Verify source structure
    source_item = data["items"][0]
    assert "source_record_id" in source_item
    assert "source_key" in source_item
    assert "title" in source_item
    assert "approval_state" in source_item


def test_list_sources_with_domain_filter(client, mock_source, mock_domain, mock_auth_user):
    """Test listing sources filtered by domain."""
    mock_auth_user.roles = ["knowledge_steward"]
    mock_auth_user.access_scope.roles = ["knowledge_steward"]
    mock_auth_user.access_scope.accessible_domains = [mock_domain.domain_id]
    
    response = client.get(f"/api/v1/sources/?domain_id={mock_domain.domain_id}")
    
    assert response.status_code == 200
    data = response.json()
    assert all(item["domain_id"] == str(mock_domain.domain_id) for item in data["items"])


def test_list_sources_pagination(client, mock_source, mock_domain, mock_auth_user):
    """Test source list pagination."""
    mock_auth_user.roles = ["knowledge_steward"]
    mock_auth_user.access_scope.roles = ["knowledge_steward"]
    mock_auth_user.access_scope.accessible_domains = [mock_domain.domain_id]
    
    response = client.get("/api/v1/sources/?page=1&page_size=10")
    
    assert response.status_code == 200
    data = response.json()
    assert data["page"] == 1
    assert data["page_size"] == 10


def test_list_sources_requires_steward_role(client, mock_auth_user):
    """Test that listing sources requires knowledge_steward or governance_reviewer role."""
    mock_auth_user.roles = ["end_user"]
    
    response = client.get("/api/v1/sources/")
    
    assert response.status_code == 403


def test_register_source_success(client, mock_domain, mock_auth_user, db_session):
    """Test successful source registration."""
    mock_auth_user.roles = ["knowledge_steward"]
    mock_auth_user.access_scope.roles = ["knowledge_steward"]
    
    team = db_session.query(Team).first()
    
    response = client.post(
        "/api/v1/sources/",
        json={
            "source_key": "NEW_SOURCE_001",
            "title": "New Test Source",
            "source_type": "wiki",
            "domain_id": str(mock_domain.domain_id),
            "owner_team_id": str(team.team_id),
            "steward_team_id": str(team.team_id),
            "sensitivity_classification": "internal"
        }
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["source_key"] == "NEW_SOURCE_001"
    assert data["title"] == "New Test Source"
    assert data["approval_state"] == "pending"


def test_register_source_duplicate_key(client, mock_source, mock_domain, mock_auth_user, db_session):
    """Test source registration with duplicate source_key."""
    mock_auth_user.roles = ["knowledge_steward"]
    mock_auth_user.access_scope.roles = ["knowledge_steward"]
    
    team = db_session.query(Team).first()
    
    response = client.post(
        "/api/v1/sources/",
        json={
            "source_key": mock_source.source_key,
            "title": "Duplicate Source",
            "source_type": "confluence",
            "domain_id": str(mock_domain.domain_id),
            "owner_team_id": str(team.team_id),
            "steward_team_id": str(team.team_id)
        }
    )
    
    assert response.status_code == 409
    assert "already exists" in response.json()["detail"]


def test_approve_source_success(client, mock_source, mock_domain, mock_auth_user):
    """Test successful source approval."""
    mock_auth_user.roles = ["knowledge_steward"]
    mock_auth_user.access_scope.roles = ["knowledge_steward"]
    mock_auth_user.access_scope.accessible_domains = [mock_domain.domain_id]
    
    next_review = date.today() + timedelta(days=90)
    
    response = client.post(
        f"/api/v1/sources/{mock_source.source_record_id}/approve",
        json={
            "review_decision": "approved",
            "review_notes": "Source reviewed and approved",
            "next_review_due_on": next_review.isoformat()
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "review_id" in data
    assert data["review_decision"] == "approved"
    assert data["source_record_id"] == str(mock_source.source_record_id)


def test_approve_source_not_found(client, mock_auth_user):
    """Test approving non-existent source."""
    mock_auth_user.roles = ["knowledge_steward"]
    mock_auth_user.access_scope.roles = ["knowledge_steward"]
    
    response = client.post(
        f"/api/v1/sources/{uuid4()}/approve",
        json={
            "review_decision": "approved"
        }
    )
    
    assert response.status_code == 404


def test_approve_source_unauthorized_domain(client, mock_source, mock_auth_user):
    """Test approving source in domain user is not steward for."""
    mock_auth_user.roles = ["knowledge_steward"]
    mock_auth_user.access_scope.roles = ["knowledge_steward"]
    mock_auth_user.access_scope.accessible_domains = [uuid4()]  # Different domain
    
    response = client.post(
        f"/api/v1/sources/{mock_source.source_record_id}/approve",
        json={
            "review_decision": "approved"
        }
    )
    
    assert response.status_code == 403
    assert "not steward" in response.json()["detail"].lower()


def test_grant_freshness_exception_success(client, mock_source, mock_domain, mock_auth_user):
    """Test successful freshness exception grant."""
    mock_auth_user.roles = ["knowledge_steward"]
    mock_auth_user.access_scope.roles = ["knowledge_steward"]
    mock_auth_user.access_scope.accessible_domains = [mock_domain.domain_id]
    
    exception_date = date.today() + timedelta(days=90)
    
    response = client.post(
        f"/api/v1/sources/{mock_source.source_record_id}/freshness-exception",
        json={
            "reason": "Source is still accurate, reviewed manually",
            "exception_until": exception_date.isoformat()
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "review_id" in data
    assert data["exception_until"] == exception_date.isoformat()
    assert data["message"] == "Freshness exception granted"


def test_grant_freshness_exception_exceeds_180_days(client, mock_source, mock_domain, mock_auth_user):
    """Test freshness exception exceeding 180 days is rejected."""
    mock_auth_user.roles = ["knowledge_steward"]
    mock_auth_user.access_scope.roles = ["knowledge_steward"]
    mock_auth_user.access_scope.accessible_domains = [mock_domain.domain_id]
    
    exception_date = date.today() + timedelta(days=181)
    
    response = client.post(
        f"/api/v1/sources/{mock_source.source_record_id}/freshness-exception",
        json={
            "reason": "Test reason",
            "exception_until": exception_date.isoformat()
        }
    )
    
    assert response.status_code == 422


def test_governance_endpoints_require_auth(db_session, mock_source):
    """Test that governance endpoints require authentication."""
    from fastapi.testclient import TestClient
    from app.main import app
    from app.database import get_db
    
    # Create a client without auth override
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides.clear()
    app.dependency_overrides[get_db] = override_get_db
    
    test_client = TestClient(app)
    
    # List sources
    response = test_client.get("/api/v1/sources/")
    assert response.status_code in (401, 403)
    
    # Register source
    response = test_client.post("/api/v1/sources/", json={})
    assert response.status_code in (401, 403)
    
    # Approve source
    response = test_client.post(f"/api/v1/sources/{mock_source.source_record_id}/approve", json={})
    assert response.status_code in (401, 403)
    
    # Grant exception
    response = test_client.post(f"/api/v1/sources/{mock_source.source_record_id}/freshness-exception", json={})
    assert response.status_code in (401, 403)
    
    app.dependency_overrides.clear()
