"""Tests for question submission and status endpoints."""

import pytest
from uuid import uuid4, UUID
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import Base, get_db
from app.models.org import Stakeholder
from app.models.interaction import QuestionSession, QuestionTurn, AnswerRecord
from app.schemas.auth import CurrentUser, AccessScope


# Test database setup - use temp file to avoid :memory: isolation issues
import tempfile
_test_db_fd, _test_db_path = tempfile.mkstemp(suffix='.db')
import os as _os
_os.close(_test_db_fd)

SQLALCHEMY_DATABASE_URL = f"sqlite:///{_test_db_path}"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override database dependency for testing."""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


# Module-level override removed - now handled in client fixture to avoid concurrent session issues


@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database for each test."""
    # Import all models so they are registered with Base.metadata
    from app.models import org, knowledge, interaction, governance, ops
    
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    yield db
    db.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def test_user(db_session):
    """Create a test user."""
    user = Stakeholder(
        stakeholder_id=uuid4(),
        employee_ref="test_user_001",
        email="test@example.com",
        display_name="Test User",
        stakeholder_type="end_user",
        account_status="active",
        created_at=datetime.utcnow(),
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def mock_current_user(test_user):
    """Mock authenticated current user."""
    return CurrentUser(
        user_id=str(test_user.stakeholder_id),
        email=test_user.email,
        roles=["end_user"],
        access_scope=AccessScope(
            user_id=str(test_user.stakeholder_id),
            roles=["end_user"],
            team_memberships=[],
            accessible_domains=[],
            source_scope_filter={},
        ),
    )


@pytest.fixture
def client(db_session, mock_current_user):
    """Create test client with database and auth overrides."""
    def override_get_current_user():
        return mock_current_user
    
    def override_get_db():
        return db_session
    
    from app.auth import get_current_user
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


@pytest.fixture
def unauthenticated_client(db_session):
    """Create test client with database but NO auth override (for auth tests)."""
    def override_get_db():
        return db_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


def test_health_endpoint(client):
    """Test health check endpoint (unauthenticated)."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_submit_question_new_session(client, db_session, mock_current_user):
    """Test submitting a question creates a new session."""
    response = client.post(
        "/api/v1/questions",
        json={"question_text": "Who owns the payment service?"},
    )
    
    assert response.status_code == 201
    data = response.json()
    
    assert "question_id" in data
    assert "session_id" in data
    assert "turn_id" in data
    assert data["status"] in ["processing", "clarification_needed"]
    assert data["question_id"] == data["turn_id"]
    
    # Verify session was created in database
    session = db_session.query(QuestionSession).filter_by(
        session_id=UUID(data["session_id"])
    ).first()
    assert session is not None
    assert str(session.requesting_stakeholder_id) == mock_current_user.user_id
    
    # Verify turn was created
    turn = db_session.query(QuestionTurn).filter_by(
        turn_id=UUID(data["turn_id"])
    ).first()
    assert turn is not None
    assert turn.question_text == "Who owns the payment service?"


def test_submit_question_existing_session(client, db_session, mock_current_user, test_user):
    """Test submitting a follow-up question to an existing session."""
    # Create an existing session
    session = QuestionSession(
        session_id=uuid4(),
        requesting_stakeholder_id=test_user.stakeholder_id,
        persona_type="engineer",
        session_status="active",
        created_at=datetime.utcnow(),
        last_activity_at=datetime.utcnow(),
    )
    db_session.add(session)
    db_session.commit()
    
    response = client.post(
        "/api/v1/questions",
        json={
            "question_text": "What about the user service?",
            "session_id": str(session.session_id),
        },
    )
    
    assert response.status_code == 201
    data = response.json()
    
    assert data["session_id"] == str(session.session_id)
    
    # Verify turn was added to existing session
    turns = db_session.query(QuestionTurn).filter_by(
        session_id=session.session_id
    ).all()
    assert len(turns) == 1


def test_submit_question_validation_empty(client, mock_current_user):
    """Test question validation rejects empty questions."""
    response = client.post(
        "/api/v1/questions",
        json={"question_text": "   "},
    )
    
    assert response.status_code == 422
    assert "validation" in response.json()["detail"].lower()


def test_submit_question_validation_too_long(client, mock_current_user):
    """Test question validation rejects questions over 2000 characters."""
    long_question = "a" * 2001
    
    response = client.post(
        "/api/v1/questions",
        json={"question_text": long_question},
    )
    
    assert response.status_code == 422


def test_submit_question_intent_classification_ownership(client, db_session, mock_current_user):
    """Test intent classification for ownership questions."""
    response = client.post(
        "/api/v1/questions",
        json={"question_text": "Who owns the auth service?"},
    )
    
    assert response.status_code == 201
    data = response.json()
    
    # Verify intent classification in database
    turn = db_session.query(QuestionTurn).filter_by(
        turn_id=UUID(data["turn_id"])
    ).first()
    assert turn.intent_classification is not None
    assert turn.intent_classification["primary_intent"] == "ownership"


def test_submit_question_intent_classification_dependency(client, db_session, mock_current_user):
    """Test intent classification for dependency questions."""
    response = client.post(
        "/api/v1/questions",
        json={"question_text": "What services depend on the database?"},
    )
    
    assert response.status_code == 201
    data = response.json()
    
    turn = db_session.query(QuestionTurn).filter_by(
        turn_id=UUID(data["turn_id"])
    ).first()
    assert turn.intent_classification["primary_intent"] == "dependency"


def test_submit_question_intent_classification_runbook(client, db_session, mock_current_user):
    """Test intent classification for runbook questions."""
    response = client.post(
        "/api/v1/questions",
        json={"question_text": "How to deploy the payment service?"},
    )
    
    assert response.status_code == 201
    data = response.json()
    
    turn = db_session.query(QuestionTurn).filter_by(
        turn_id=UUID(data["turn_id"])
    ).first()
    assert turn.intent_classification["primary_intent"] == "runbook"


def test_submit_question_ambiguous(client, db_session, mock_current_user):
    """Test ambiguous question returns clarification prompt."""
    response = client.post(
        "/api/v1/questions",
        json={"question_text": "What about it?"},
    )
    
    assert response.status_code == 201
    data = response.json()
    
    # Very short vague questions should trigger clarification
    turn = db_session.query(QuestionTurn).filter_by(
        turn_id=UUID(data["turn_id"])
    ).first()
    assert len(turn.intent_classification["ambiguity_flags"]) > 0


def test_get_question_status_found(client, db_session, mock_current_user, test_user):
    """Test getting status of an existing question."""
    # Create session and turn
    session = QuestionSession(
        session_id=uuid4(),
        requesting_stakeholder_id=test_user.stakeholder_id,
        persona_type="engineer",
        session_status="active",
        created_at=datetime.utcnow(),
        last_activity_at=datetime.utcnow(),
    )
    db_session.add(session)
    
    turn = QuestionTurn(
        turn_id=uuid4(),
        session_id=session.session_id,
        turn_sequence=1,
        question_text="Test question",
        intent_classification={"primary_intent": "ownership", "candidate_domains": [], "confidence": 0.8, "ambiguity_flags": []},
        created_at=datetime.utcnow(),
    )
    db_session.add(turn)
    db_session.commit()
    
    response = client.get(f"/api/v1/questions/{turn.turn_id}")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["question_id"] == str(turn.turn_id)
    assert data["session_id"] == str(session.session_id)
    assert data["status"] == "processing"
    assert data["answer_id"] is None


def test_get_question_status_with_answer(client, db_session, mock_current_user, test_user):
    """Test getting status of a completed question with answer."""
    # Create session, turn, and answer
    session = QuestionSession(
        session_id=uuid4(),
        requesting_stakeholder_id=test_user.stakeholder_id,
        persona_type="engineer",
        session_status="active",
        created_at=datetime.utcnow(),
        last_activity_at=datetime.utcnow(),
    )
    db_session.add(session)
    
    turn = QuestionTurn(
        turn_id=uuid4(),
        session_id=session.session_id,
        turn_sequence=1,
        question_text="Test question",
        intent_classification={"primary_intent": "ownership", "candidate_domains": [], "confidence": 0.8, "ambiguity_flags": []},
        created_at=datetime.utcnow(),
    )
    db_session.add(turn)
    
    answer = AnswerRecord(
        answer_id=uuid4(),
        session_id=session.session_id,
        turn_id=turn.turn_id,
        answer_text="Test answer",
        response_type="supported_answer",
        confidence_band="high",
        confidence_score=0.9,
        created_at=datetime.utcnow(),
    )
    db_session.add(answer)
    db_session.commit()
    
    response = client.get(f"/api/v1/questions/{turn.turn_id}")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["status"] == "completed"
    assert data["answer_id"] == str(answer.answer_id)
    assert data["completed_at"] is not None


def test_get_question_status_not_found(client, mock_current_user):
    """Test getting status of non-existent question returns 404."""
    fake_id = uuid4()
    
    response = client.get(f"/api/v1/questions/{fake_id}")
    
    assert response.status_code == 404


def test_get_question_status_wrong_user(client, db_session, mock_current_user):
    """Test user cannot access another user's question."""
    # Create session for different user
    other_user_id = uuid4()
    session = QuestionSession(
        session_id=uuid4(),
        requesting_stakeholder_id=other_user_id,
        persona_type="engineer",
        session_status="active",
        created_at=datetime.utcnow(),
        last_activity_at=datetime.utcnow(),
    )
    db_session.add(session)
    
    turn = QuestionTurn(
        turn_id=uuid4(),
        session_id=session.session_id,
        turn_sequence=1,
        question_text="Test question",
        intent_classification={},
        created_at=datetime.utcnow(),
    )
    db_session.add(turn)
    db_session.commit()
    
    response = client.get(f"/api/v1/questions/{turn.turn_id}")
    
    assert response.status_code == 404


def test_submit_question_idempotency(client, db_session, mock_current_user):
    """Test idempotency key prevents duplicate submissions."""
    idempotency_key = "test-key-123"
    question_data = {"question_text": "Who owns the payment service?"}
    
    # First request
    response1 = client.post(
        "/api/v1/questions",
        json=question_data,
        headers={"Idempotency-Key": idempotency_key},
    )
        
    # Second request with same key
    response2 = client.post(
        "/api/v1/questions",
        json=question_data,
        headers={"Idempotency-Key": idempotency_key},
    )
    
    assert response1.status_code == 201
    assert response2.status_code == 201
    
    # Should return same response
    assert response1.json()["question_id"] == response2.json()["question_id"]
    assert response1.json()["session_id"] == response2.json()["session_id"]
    
    # Verify only one turn was created
    turns = db_session.query(QuestionTurn).all()
    assert len(turns) == 1


def test_submit_question_requires_auth(unauthenticated_client):
    """Test question submission requires authentication."""
    response = unauthenticated_client.post(
        "/api/v1/questions",
        json={"question_text": "Who owns the payment service?"},
    )
    
    # Without mocked auth, should fail
    assert response.status_code in [401, 403, 422]  # Depends on auth middleware behavior


def test_get_question_status_requires_auth(unauthenticated_client):
    """Test question status requires authentication."""
    fake_id = uuid4()
    response = unauthenticated_client.get(f"/api/v1/questions/{fake_id}")
    
    # Without mocked auth, should fail
    assert response.status_code in [401, 403, 422]  # Depends on auth middleware behavior


def test_submit_question_invalid_session_id(client, mock_current_user):
    """Test invalid session ID format returns validation error."""
    response = client.post(
        "/api/v1/questions",
        json={
            "question_text": "Test question",
            "session_id": "not-a-uuid",
        },
    )
    
    assert response.status_code == 422
