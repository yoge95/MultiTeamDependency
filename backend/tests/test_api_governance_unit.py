"""Unit tests for governance API endpoints (schema validation only)."""

import pytest
from datetime import date, timedelta
from pydantic import ValidationError

from app.schemas.governance import (
    SourceRegistrationRequest,
    SourceApprovalRequest,
    FreshnessExceptionRequest
)


def test_source_registration_request_valid():
    """Test valid source registration request."""
    request = SourceRegistrationRequest(
        source_key="TEST_SOURCE_001",
        title="Test Source",
        source_type="confluence",
        domain_id="550e8400-e29b-41d4-a716-446655440000",
        owner_team_id="650e8400-e29b-41d4-a716-446655440000",
        steward_team_id="750e8400-e29b-41d4-a716-446655440000",
        sensitivity_classification="internal"
    )
    assert request.source_key == "TEST_SOURCE_001"
    assert request.sensitivity_classification == "internal"


def test_source_registration_invalid_sensitivity():
    """Test source registration with invalid sensitivity classification."""
    with pytest.raises(ValidationError) as exc_info:
        SourceRegistrationRequest(
            source_key="TEST_SOURCE_001",
            title="Test Source",
            source_type="confluence",
            domain_id="550e8400-e29b-41d4-a716-446655440000",
            owner_team_id="650e8400-e29b-41d4-a716-446655440000",
            steward_team_id="750e8400-e29b-41d4-a716-446655440000",
            sensitivity_classification="invalid"
        )
    assert "sensitivity_classification" in str(exc_info.value)


def test_source_approval_request_valid():
    """Test valid source approval request."""
    review_date = date.today() + timedelta(days=90)
    request = SourceApprovalRequest(
        review_decision="approved",
        review_notes="Source reviewed and approved",
        next_review_due_on=review_date
    )
    assert request.review_decision == "approved"
    assert request.next_review_due_on == review_date


def test_source_approval_invalid_decision():
    """Test source approval with invalid review decision."""
    with pytest.raises(ValidationError):
        SourceApprovalRequest(
            review_decision="invalid_decision"
        )


def test_freshness_exception_request_valid():
    """Test valid freshness exception request."""
    exception_date = date.today() + timedelta(days=90)
    request = FreshnessExceptionRequest(
        reason="Source is still accurate, reviewed manually",
        exception_until=exception_date
    )
    assert request.reason == "Source is still accurate, reviewed manually"
    assert request.exception_until == exception_date


def test_freshness_exception_exceeds_180_days():
    """Test freshness exception exceeding 180 days is rejected."""
    exception_date = date.today() + timedelta(days=181)
    with pytest.raises(ValidationError) as exc_info:
        FreshnessExceptionRequest(
            reason="Test reason",
            exception_until=exception_date
        )
    assert "180 days" in str(exc_info.value)


def test_freshness_exception_max_180_days():
    """Test freshness exception at exactly 180 days is accepted."""
    exception_date = date.today() + timedelta(days=180)
    request = FreshnessExceptionRequest(
        reason="Test reason",
        exception_until=exception_date
    )
    assert request.exception_until == exception_date


def test_sensitivity_classifications():
    """Test all valid sensitivity classifications."""
    valid_classifications = ["public", "internal", "confidential", "restricted"]
    
    for classification in valid_classifications:
        request = SourceRegistrationRequest(
            source_key="TEST_SOURCE",
            title="Test",
            source_type="wiki",
            domain_id="550e8400-e29b-41d4-a716-446655440000",
            owner_team_id="650e8400-e29b-41d4-a716-446655440000",
            steward_team_id="750e8400-e29b-41d4-a716-446655440000",
            sensitivity_classification=classification
        )
        assert request.sensitivity_classification == classification


def test_review_decisions():
    """Test all valid review decisions."""
    valid_decisions = ["approved", "rejected", "exception_granted", "archived"]
    
    for decision in valid_decisions:
        request = SourceApprovalRequest(
            review_decision=decision
        )
        assert request.review_decision == decision
