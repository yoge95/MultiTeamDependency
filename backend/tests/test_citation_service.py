"""Tests for citation service."""

from datetime import datetime
from uuid import uuid4

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models.interaction import CitationReference
from app.models.knowledge import SourceChunk, SourceRecord, SourceVersion
from app.schemas.retrieval import RetrievedChunk
from app.services.citation_service import CitationService


@pytest.fixture
def db_session():
    """Create test database session."""
    # Import all models so they are registered with Base.metadata
    from app.models import org, knowledge, interaction, governance, ops
    
    import tempfile
    import os
    
    # Create a temporary database file
    fd, db_path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    
    engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    yield session
    session.close()
    engine.dispose()
    
    # Clean up temp file
    try:
        os.unlink(db_path)
    except:
        pass


@pytest.fixture
def citation_service(db_session):
    """Create citation service."""
    return CitationService(db=db_session)


@pytest.fixture
def sample_chunks():
    """Create sample chunks for citation generation."""
    return [
        RetrievedChunk(
            chunk_id=uuid4(),
            source_record_id=uuid4(),
            source_version_id=uuid4(),
            section_path="/ownership",
            content="The payment service is owned by the Platform Team and is responsible for processing transactions.",
            relevance_score=0.9,
            access_scope_tag="internal",
            freshness_state="current",
            domain_id=uuid4(),
            source_title="Payment Service Ownership",
            last_reviewed_at=datetime.utcnow()
        ),
        RetrievedChunk(
            chunk_id=uuid4(),
            source_record_id=uuid4(),
            source_version_id=uuid4(),
            section_path="/dependencies",
            content="The service depends on the authentication API and the database service for its operations.",
            relevance_score=0.85,
            access_scope_tag="internal",
            freshness_state="current",
            domain_id=uuid4(),
            source_title="System Dependencies",
            last_reviewed_at=datetime.utcnow()
        )
    ]


def test_generate_citations(citation_service, sample_chunks):
    """Test citation generation from answer text."""
    answer_text = "The payment service is owned by the Platform Team. It depends on the authentication API."
    answer_id = uuid4()

    citation_ids = citation_service.generate_citations(
        answer_text=answer_text,
        chunks=sample_chunks,
        answer_id=answer_id
    )

    assert len(citation_ids) > 0
    assert all(isinstance(cid, type(uuid4())) for cid in citation_ids)


def test_generate_citations_empty_chunks(citation_service):
    """Test citation generation with no chunks."""
    answer_text = "Some answer text without evidence."
    answer_id = uuid4()

    citation_ids = citation_service.generate_citations(
        answer_text=answer_text,
        chunks=[],
        answer_id=answer_id
    )

    assert len(citation_ids) == 0


def test_generate_citations_empty_answer(citation_service, sample_chunks):
    """Test citation generation with empty answer."""
    citation_ids = citation_service.generate_citations(
        answer_text="",
        chunks=sample_chunks,
        answer_id=uuid4()
    )

    assert len(citation_ids) == 0


def test_extract_claims(citation_service):
    """Test claim extraction from answer text."""
    answer_text = (
        "The payment service is owned by the Platform Team. "
        "It handles all transaction processing. "
        "The service was launched in 2023."
    )

    claims = citation_service._extract_claims(answer_text)

    assert len(claims) >= 2
    assert all(len(claim) >= citation_service.min_claim_length for claim in claims)


def test_extract_claims_filters_meta_sentences(citation_service):
    """Test that meta sentences are filtered out."""
    answer_text = (
        "Here is what I found about the service. "
        "The payment service is owned by the Platform Team. "
        "Please let me know if you need more information."
    )

    claims = citation_service._extract_claims(answer_text)

    assert not any(claim.lower().startswith("here") for claim in claims)
    assert not any(claim.lower().startswith("please") for claim in claims)


def test_match_claim_to_chunk(citation_service, sample_chunks):
    """Test matching a claim to relevant chunk."""
    claim = "The payment service is owned by the Platform Team"

    matched_chunk = citation_service._match_claim_to_chunk(claim, sample_chunks)

    assert matched_chunk is not None
    assert "payment service" in matched_chunk.content.lower()


def test_match_claim_to_chunk_no_match(citation_service, sample_chunks):
    """Test matching with no relevant chunks."""
    claim = "Completely unrelated claim about something else"

    matched_chunk = citation_service._match_claim_to_chunk(claim, sample_chunks)

    assert matched_chunk is None


def test_validate_citation_coverage_meets_threshold(citation_service):
    """Test citation coverage validation meeting threshold."""
    answer_text = "The payment service is owned by the Platform Team. The authentication API handles user logins."
    answer_id = uuid4()

    citation1 = CitationReference(
        citation_id=uuid4(),
        answer_id=answer_id,
        chunk_id=uuid4(),
        claim_text="The payment service is owned by the Platform Team",
        source_title="Source 1",
        section_path="/section1",
        freshness_status="current"
    )
    citation2 = CitationReference(
        citation_id=uuid4(),
        answer_id=answer_id,
        chunk_id=uuid4(),
        claim_text="The authentication API handles user logins",
        source_title="Source 2",
        section_path="/section2",
        freshness_status="current"
    )

    citation_service.db.add_all([citation1, citation2])
    citation_service.db.commit()

    report = citation_service.validate_citation_coverage(
        answer_text=answer_text,
        citation_ids=[citation1.citation_id, citation2.citation_id]
    )

    assert report.total_claims == 2
    assert report.cited_claims == 2
    assert report.coverage_percentage == 1.0
    assert report.meets_threshold is True


def test_validate_citation_coverage_below_threshold(citation_service):
    """Test citation coverage validation below threshold."""
    answer_text = "The payment service is owned by the Platform Team. The authentication API handles user logins. The database service stores all data."
    answer_id = uuid4()

    citation1 = CitationReference(
        citation_id=uuid4(),
        answer_id=answer_id,
        chunk_id=uuid4(),
        claim_text="The payment service is owned by the Platform Team",
        source_title="Source 1",
        section_path="/section1",
        freshness_status="current"
    )

    citation_service.db.add(citation1)
    citation_service.db.commit()

    report = citation_service.validate_citation_coverage(
        answer_text=answer_text,
        citation_ids=[citation1.citation_id]
    )

    assert report.coverage_percentage < 0.9
    assert report.meets_threshold is False
    assert len(report.uncited_claims) > 0


def test_determine_freshness_status(citation_service):
    """Test freshness status determination."""
    current_chunk = RetrievedChunk(
        chunk_id=uuid4(),
        source_record_id=uuid4(),
        source_version_id=uuid4(),
        section_path="/section",
        content="Content",
        relevance_score=0.8,
        access_scope_tag="internal",
        freshness_state="current",
        domain_id=uuid4()
    )

    status = citation_service._determine_freshness_status(current_chunk)
    assert status == "current"

    stale_chunk = RetrievedChunk(
        chunk_id=uuid4(),
        source_record_id=uuid4(),
        source_version_id=uuid4(),
        section_path="/section",
        content="Content",
        relevance_score=0.8,
        access_scope_tag="internal",
        freshness_state="stale",
        domain_id=uuid4()
    )

    status = citation_service._determine_freshness_status(stale_chunk)
    assert status == "stale"

    exception_chunk = RetrievedChunk(
        chunk_id=uuid4(),
        source_record_id=uuid4(),
        source_version_id=uuid4(),
        section_path="/section",
        content="Content",
        relevance_score=0.8,
        access_scope_tag="internal",
        freshness_state="exception_granted",
        domain_id=uuid4()
    )

    status = citation_service._determine_freshness_status(exception_chunk)
    assert status == "exception_granted"
