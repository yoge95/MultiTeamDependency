"""Tests for confidence scoring service."""

from datetime import datetime, timedelta
from uuid import uuid4

import pytest

from app.schemas.retrieval import RetrievedChunk
from app.services.confidence_scoring_service import ConfidenceScoringService


@pytest.fixture
def confidence_service():
    """Create confidence scoring service."""
    return ConfidenceScoringService()


@pytest.fixture
def sample_chunks():
    """Create sample chunks for testing."""
    now = datetime.utcnow()
    return [
        RetrievedChunk(
            chunk_id=uuid4(),
            source_record_id=uuid4(),
            source_version_id=uuid4(),
            section_path="/section1",
            content="Sample content about the payment service ownership.",
            relevance_score=0.9,
            access_scope_tag="internal",
            freshness_state="current",
            domain_id=uuid4(),
            source_title="Payment Service Documentation",
            last_reviewed_at=now - timedelta(days=30)
        ),
        RetrievedChunk(
            chunk_id=uuid4(),
            source_record_id=uuid4(),
            source_version_id=uuid4(),
            section_path="/section2",
            content="Additional information about payment service dependencies.",
            relevance_score=0.85,
            access_scope_tag="internal",
            freshness_state="current",
            domain_id=uuid4(),
            source_title="System Architecture",
            last_reviewed_at=now - timedelta(days=45)
        )
    ]


def test_score_confidence_with_good_evidence(confidence_service, sample_chunks):
    """Test confidence scoring with high-quality evidence."""
    result = confidence_service.score_confidence(
        chunks=sample_chunks,
        citation_coverage=0.95,
        total_claims=5
    )

    assert result.overall_score > 0.7
    assert result.confidence_band in ["high", "medium"]
    assert result.dimensions.evidence_quality > 0.7
    assert result.dimensions.freshness > 0.7
    assert result.dimensions.citation_coverage == 0.95


def test_score_confidence_with_no_evidence(confidence_service):
    """Test confidence scoring with no evidence."""
    result = confidence_service.score_confidence(
        chunks=[],
        citation_coverage=0.0,
        total_claims=0
    )

    assert result.overall_score == 0.0
    assert result.confidence_band == "insufficient"
    assert "missing_knowledge" in result.flags
    assert result.explanation is not None


def test_score_confidence_with_stale_sources(confidence_service):
    """Test confidence scoring with stale sources."""
    now = datetime.utcnow()
    stale_chunks = [
        RetrievedChunk(
            chunk_id=uuid4(),
            source_record_id=uuid4(),
            source_version_id=uuid4(),
            section_path="/section1",
            content="Old content",
            relevance_score=0.8,
            access_scope_tag="internal",
            freshness_state="stale",
            domain_id=uuid4(),
            source_title="Old Docs",
            last_reviewed_at=now - timedelta(days=200)
        )
    ]

    result = confidence_service.score_confidence(
        chunks=stale_chunks,
        citation_coverage=0.9,
        total_claims=3
    )

    assert "stale_sources" in result.flags
    assert result.dimensions.freshness < 0.5


def test_score_confidence_low_citation_coverage(confidence_service, sample_chunks):
    """Test confidence scoring with low citation coverage."""
    result = confidence_service.score_confidence(
        chunks=sample_chunks,
        citation_coverage=0.5,
        total_claims=10
    )

    assert "low_citation_coverage" in result.flags
    assert result.dimensions.citation_coverage == 0.5


def test_calculate_evidence_quality_score(confidence_service, sample_chunks):
    """Test evidence quality calculation."""
    score = confidence_service.calculate_evidence_quality_score(sample_chunks)

    assert 0.0 <= score <= 1.0
    assert score > 0.5


def test_calculate_freshness_score(confidence_service, sample_chunks):
    """Test freshness score calculation."""
    score = confidence_service.calculate_freshness_score(sample_chunks)

    assert 0.0 <= score <= 1.0
    assert score > 0.5


def test_calculate_freshness_score_with_exception(confidence_service):
    """Test freshness score with exception granted."""
    now = datetime.utcnow()
    chunks_with_exception = [
        RetrievedChunk(
            chunk_id=uuid4(),
            source_record_id=uuid4(),
            source_version_id=uuid4(),
            section_path="/section1",
            content="Content",
            relevance_score=0.8,
            access_scope_tag="internal",
            freshness_state="exception_granted",
            domain_id=uuid4(),
            last_reviewed_at=now - timedelta(days=150)
        )
    ]

    score = confidence_service.calculate_freshness_score(chunks_with_exception)
    assert score >= 0.7


def test_calculate_consistency_score(confidence_service, sample_chunks):
    """Test consistency score calculation."""
    score = confidence_service.calculate_consistency_score(sample_chunks)

    assert 0.0 <= score <= 1.0


def test_calculate_consistency_score_single_chunk(confidence_service):
    """Test consistency score with single chunk."""
    single_chunk = [
        RetrievedChunk(
            chunk_id=uuid4(),
            source_record_id=uuid4(),
            source_version_id=uuid4(),
            section_path="/section1",
            content="Content",
            relevance_score=0.9,
            access_scope_tag="internal",
            freshness_state="current",
            domain_id=uuid4()
        )
    ]

    score = confidence_service.calculate_consistency_score(single_chunk)
    assert score == 1.0


def test_confidence_bands(confidence_service):
    """Test confidence band determination."""
    assert confidence_service._determine_confidence_band(0.85) == "high"
    assert confidence_service._determine_confidence_band(0.70) == "medium"
    assert confidence_service._determine_confidence_band(0.50) == "low"
    assert confidence_service._determine_confidence_band(0.30) == "insufficient"


def test_confidence_flags_restricted_access(confidence_service):
    """Test confidence flags for restricted access."""
    restricted_chunks = [
        RetrievedChunk(
            chunk_id=uuid4(),
            source_record_id=uuid4(),
            source_version_id=uuid4(),
            section_path="/section1",
            content="Restricted content",
            relevance_score=0.9,
            access_scope_tag="restricted",
            freshness_state="current",
            domain_id=uuid4()
        )
    ]

    flags = confidence_service._identify_confidence_flags(
        chunks=restricted_chunks,
        citation_coverage=0.9,
        evidence_quality=0.8,
        freshness=0.9,
        consistency=0.9
    )

    assert "restricted_access" in flags
