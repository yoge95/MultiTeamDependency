"""Tests for feedback API endpoints."""

import pytest
from uuid import uuid4
from datetime import datetime

from app.models.interaction import AnswerRecord, FeedbackRecord, QuestionSession, QuestionTurn


@pytest.fixture
def mock_session(db_session):
    """Create a mock question session."""
    session = QuestionSession(
        session_id=uuid4(),
        requesting_stakeholder_id=uuid4(),
        persona_type="engineer",
        session_status="active",
        created_at=datetime.utcnow(),
        last_activity_at=datetime.utcnow()
    )
    db_session.add(session)
    db_session.commit()
    return session


@pytest.fixture
def mock_turn(db_session, mock_session):
    """Create a mock question turn."""
    turn = QuestionTurn(
        turn_id=uuid4(),
        session_id=mock_session.session_id,
        turn_sequence=1,
        question_text="Test question",
        intent_classification={"primary_intent": "ownership"},
        ambiguity_state="clear",
        processing_status="completed",
        created_at=datetime.utcnow()
    )
    db_session.add(turn)
    db_session.commit()
    return turn


@pytest.fixture
def mock_answer(db_session, mock_session, mock_turn):
    """Create a mock answer."""
    answer = AnswerRecord(
        answer_id=uuid4(),
        turn_id=mock_turn.turn_id,
        session_id=mock_session.session_id,
        response_type="supported_answer",
        answer_text="Test answer",
        confidence_band="high",
        confidence_score=0.95,
        citation_completeness_flag=True,
        escalation_required_flag=False,
        created_at=datetime.utcnow()
    )
    db_session.add(answer)
    db_session.commit()
    return answer


def test_submit_feedback_success(client, mock_answer, mock_session, mock_auth_user):
    """Test successful feedback submission."""
    # Mock authentication to return user_id matching session owner
    mock_auth_user.user_id = str(mock_session.requesting_stakeholder_id)
    
    response = client.post(
        "/api/v1/feedback/",
        json={
            "answer_id": str(mock_answer.answer_id),
            "feedback_type": "helpful",
            "feedback_text": "Great answer, very helpful!"
        }
    )
    
    assert response.status_code == 201
    data = response.json()
    assert "feedback_id" in data
    assert data["answer_id"] == str(mock_answer.answer_id)
    assert data["feedback_type"] == "helpful"
    assert data["triage_status"] == "pending"
    assert data["message"] == "Thank you for your feedback!"


def test_submit_feedback_invalid_type(client, mock_answer, mock_session, mock_auth_user):
    """Test feedback submission with invalid feedback_type."""
    mock_auth_user.user_id = str(mock_session.requesting_stakeholder_id)
    
    response = client.post(
        "/api/v1/feedback/",
        json={
            "answer_id": str(mock_answer.answer_id),
            "feedback_type": "invalid_type",
            "feedback_text": "Test"
        }
    )
    
    assert response.status_code == 422


def test_submit_feedback_text_too_long(client, mock_answer, mock_session, mock_auth_user):
    """Test feedback submission with text exceeding 2000 chars."""
    mock_auth_user.user_id = str(mock_session.requesting_stakeholder_id)
    
    response = client.post(
        "/api/v1/feedback/",
        json={
            "answer_id": str(mock_answer.answer_id),
            "feedback_type": "helpful",
            "feedback_text": "x" * 2001
        }
    )
    
    assert response.status_code == 422


def test_submit_feedback_html_blocked(client, mock_answer, mock_session, mock_auth_user):
    """Test feedback submission with HTML/script tags is blocked."""
    mock_auth_user.user_id = str(mock_session.requesting_stakeholder_id)
    
    response = client.post(
        "/api/v1/feedback/",
        json={
            "answer_id": str(mock_answer.answer_id),
            "feedback_type": "helpful",
            "feedback_text": "Test <script>alert('xss')</script>"
        }
    )
    
    assert response.status_code == 422


def test_submit_feedback_answer_not_found(client, mock_auth_user):
    """Test feedback submission for non-existent answer."""
    response = client.post(
        "/api/v1/feedback/",
        json={
            "answer_id": str(uuid4()),
            "feedback_type": "helpful",
            "feedback_text": "Test"
        }
    )
    
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_submit_feedback_unauthorized_user(client, mock_answer, mock_session, mock_auth_user):
    """Test feedback submission by user who doesn't own the answer."""
    # Set user_id to different user
    mock_auth_user.user_id = str(uuid4())
    
    response = client.post(
        "/api/v1/feedback/",
        json={
            "answer_id": str(mock_answer.answer_id),
            "feedback_type": "helpful",
            "feedback_text": "Test"
        }
    )
    
    assert response.status_code == 403
    assert "your own answers" in response.json()["detail"].lower()


def test_submit_feedback_steward_action_required(client, mock_answer, mock_session, mock_auth_user, db_session):
    """Test that negative feedback triggers steward_action_required flag."""
    from uuid import UUID
    
    mock_auth_user.user_id = str(mock_session.requesting_stakeholder_id)
    
    response = client.post(
        "/api/v1/feedback/",
        json={
            "answer_id": str(mock_answer.answer_id),
            "feedback_type": "incorrect",
            "feedback_text": "The answer contains incorrect information"
        }
    )
    
    assert response.status_code == 201
    
    # Verify steward_action_required flag is set in database
    feedback_id = UUID(response.json()["feedback_id"])
    feedback = db_session.query(FeedbackRecord).filter_by(
        feedback_id=feedback_id
    ).first()
    
    assert feedback is not None
    assert feedback.steward_action_required is True


def test_submit_feedback_with_citation_feedback(client, mock_answer, mock_session, mock_auth_user):
    """Test feedback submission with citation-specific feedback."""
    mock_auth_user.user_id = str(mock_session.requesting_stakeholder_id)
    
    citation_id = str(uuid4())
    response = client.post(
        "/api/v1/feedback/",
        json={
            "answer_id": str(mock_answer.answer_id),
            "feedback_type": "unclear",
            "feedback_text": "Citations need improvement",
            "citation_feedback": [
                {
                    "citation_id": citation_id,
                    "issue_type": "unclear",
                    "comment": "Source link is broken"
                }
            ]
        }
    )
    
    assert response.status_code == 201


def test_submit_feedback_requires_auth(db_session, mock_answer):
    """Test that feedback submission requires authentication."""
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
    response = test_client.post(
        "/api/v1/feedback/",
        json={
            "answer_id": str(mock_answer.answer_id),
            "feedback_type": "helpful"
        }
    )
    
    app.dependency_overrides.clear()
    
    # Should return 401 or 403 for unauthenticated request
    assert response.status_code in (401, 403)
