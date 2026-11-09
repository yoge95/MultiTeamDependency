"""Unit tests for feedback API endpoints (schema validation only)."""

import pytest
from pydantic import ValidationError

from app.schemas.feedback import FeedbackSubmissionRequest, CitationFeedbackItem


def test_feedback_submission_request_valid():
    """Test valid feedback submission request."""
    request = FeedbackSubmissionRequest(
        answer_id="550e8400-e29b-41d4-a716-446655440000",
        feedback_type="helpful",
        feedback_text="Great answer!"
    )
    assert request.feedback_type == "helpful"
    assert request.feedback_text == "Great answer!"


def test_feedback_submission_request_invalid_type():
    """Test feedback submission with invalid feedback_type."""
    with pytest.raises(ValidationError) as exc_info:
        FeedbackSubmissionRequest(
            answer_id="550e8400-e29b-41d4-a716-446655440000",
            feedback_type="invalid_type"
        )
    assert "feedback_type" in str(exc_info.value)


def test_feedback_submission_request_text_too_long():
    """Test feedback submission with text exceeding 2000 chars."""
    with pytest.raises(ValidationError):
        FeedbackSubmissionRequest(
            answer_id="550e8400-e29b-41d4-a716-446655440000",
            feedback_type="helpful",
            feedback_text="x" * 2001
        )


def test_feedback_submission_request_html_blocked():
    """Test feedback submission with HTML/script tags is blocked."""
    with pytest.raises(ValidationError) as exc_info:
        FeedbackSubmissionRequest(
            answer_id="550e8400-e29b-41d4-a716-446655440000",
            feedback_type="helpful",
            feedback_text="Test <script>alert('xss')</script>"
        )
    assert "HTML or script" in str(exc_info.value)


def test_feedback_submission_request_javascript_blocked():
    """Test feedback submission with javascript: protocol is blocked."""
    with pytest.raises(ValidationError):
        FeedbackSubmissionRequest(
            answer_id="550e8400-e29b-41d4-a716-446655440000",
            feedback_type="helpful",
            feedback_text="Click here: javascript:alert('xss')"
        )


def test_feedback_submission_request_with_citations():
    """Test feedback submission with citation feedback."""
    request = FeedbackSubmissionRequest(
        answer_id="550e8400-e29b-41d4-a716-446655440000",
        feedback_type="unclear",
        feedback_text="Citations need improvement",
        citation_feedback=[
            CitationFeedbackItem(
                citation_id="650e8400-e29b-41d4-a716-446655440000",
                issue_type="unclear",
                comment="Source link is broken"
            )
        ]
    )
    assert len(request.citation_feedback) == 1
    assert request.citation_feedback[0].issue_type == "unclear"


def test_feedback_types():
    """Test all valid feedback types."""
    valid_types = ["helpful", "incomplete", "stale", "unclear", "incorrect", "other"]
    
    for feedback_type in valid_types:
        request = FeedbackSubmissionRequest(
            answer_id="550e8400-e29b-41d4-a716-446655440000",
            feedback_type=feedback_type
        )
        assert request.feedback_type == feedback_type


def test_feedback_text_optional():
    """Test that feedback_text is optional."""
    request = FeedbackSubmissionRequest(
        answer_id="550e8400-e29b-41d4-a716-446655440000",
        feedback_type="helpful"
    )
    assert request.feedback_text is None
