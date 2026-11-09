"""Tests for answer composition service."""

from datetime import datetime
from uuid import uuid4

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.integrations.neo4j_client import Neo4jClient
from app.models.interaction import AnswerLimitation, AnswerRecord
from app.schemas.retrieval import EvidenceBundle, RetrievedChunk
from app.services.answer_composition_service import AnswerCompositionService
from app.services.citation_service import CitationService
from app.services.confidence_scoring_service import ConfidenceScoringService
from app.services.escalation_routing_service import EscalationRoutingService


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
def answer_composition_service(db_session):
    """Create answer composition service."""
    citation_service = CitationService(db=db_session)
    confidence_service = ConfidenceScoringService()
    neo4j_client = Neo4jClient()
    escalation_service = EscalationRoutingService(db=db_session, neo4j_client=neo4j_client)

    return AnswerCompositionService(
        db=db_session,
        citation_service=citation_service,
        confidence_service=confidence_service,
        escalation_service=escalation_service
    )


@pytest.fixture
def sample_evidence_bundle():
    """Create sample evidence bundle."""
    chunks = [
        RetrievedChunk(
            chunk_id=uuid4(),
            source_record_id=uuid4(),
            source_version_id=uuid4(),
            section_path="/ownership",
            content="The payment service is owned by the Platform Team. The team is responsible for maintaining the service and ensuring its availability.",
            relevance_score=0.9,
            access_scope_tag="internal",
            freshness_state="current",
            domain_id=uuid4(),
            source_title="Payment Service Documentation",
            last_reviewed_at=datetime.utcnow()
        ),
        RetrievedChunk(
            chunk_id=uuid4(),
            source_record_id=uuid4(),
            source_version_id=uuid4(),
            section_path="/dependencies",
            content="The payment service depends on the authentication API for user verification and the database service for transaction storage.",
            relevance_score=0.85,
            access_scope_tag="internal",
            freshness_state="current",
            domain_id=uuid4(),
            source_title="System Architecture",
            last_reviewed_at=datetime.utcnow()
        )
    ]

    return EvidenceBundle(
        chunks=chunks,
        relationships=[],
        metadata={}
    )


def test_compose_answer_with_good_evidence(answer_composition_service, sample_evidence_bundle):
    """Test answer composition with good evidence."""
    session_id = uuid4()
    turn_id = uuid4()
    question_text = "Who owns the payment service?"
    intent_classification = {"primary_intent": "ownership"}
    domain_id = uuid4()

    answer_id = answer_composition_service.compose_answer(
        session_id=session_id,
        turn_id=turn_id,
        question_text=question_text,
        evidence_bundle=sample_evidence_bundle,
        intent_classification=intent_classification,
        domain_id=domain_id
    )

    assert answer_id is not None

    answer = answer_composition_service.db.query(AnswerRecord).filter_by(answer_id=answer_id).first()
    assert answer is not None
    assert answer.answer_text is not None
    assert len(answer.answer_text) > 0
    assert answer.confidence_band in ["high", "medium", "low", "insufficient"]
    assert answer.response_type in ["supported_answer", "limitation"]


def test_compose_answer_with_no_evidence(answer_composition_service):
    """Test answer composition with no evidence."""
    session_id = uuid4()
    turn_id = uuid4()
    question_text = "Who owns the unknown service?"
    intent_classification = {"primary_intent": "ownership"}
    domain_id = uuid4()

    empty_bundle = EvidenceBundle(chunks=[], relationships=[], metadata={})

    answer_id = answer_composition_service.compose_answer(
        session_id=session_id,
        turn_id=turn_id,
        question_text=question_text,
        evidence_bundle=empty_bundle,
        intent_classification=intent_classification,
        domain_id=domain_id
    )

    assert answer_id is not None

    answer = answer_composition_service.db.query(AnswerRecord).filter_by(answer_id=answer_id).first()
    assert answer is not None
    assert answer.response_type == "limitation"
    assert answer.confidence_band == "insufficient"
    assert answer.escalation_required_flag is True

    limitations = answer_composition_service.db.query(AnswerLimitation).filter_by(answer_id=answer_id).all()
    assert len(limitations) > 0
    assert limitations[0].limitation_type == "missing_knowledge"


def test_synthesize_answer_text_ownership_intent(answer_composition_service, sample_evidence_bundle):
    """Test answer text synthesis for ownership intent."""
    answer_text = answer_composition_service._synthesize_answer_text(
        question_text="Who owns the payment service?",
        chunks=sample_evidence_bundle.chunks,
        relationships=[],
        intent="ownership"
    )

    assert "ownership" in answer_text.lower()
    assert len(answer_text) > 0
    assert "Platform Team" in answer_text


def test_synthesize_answer_text_dependency_intent(answer_composition_service, sample_evidence_bundle):
    """Test answer text synthesis for dependency intent."""
    answer_text = answer_composition_service._synthesize_answer_text(
        question_text="What does the payment service depend on?",
        chunks=sample_evidence_bundle.chunks,
        relationships=[],
        intent="dependency"
    )

    assert len(answer_text) > 0
    assert "depend" in answer_text.lower() or "authentication" in answer_text.lower()


def test_generate_intro_for_different_intents(answer_composition_service):
    """Test intro generation for different intents."""
    ownership_intro = answer_composition_service._generate_intro("ownership")
    assert "ownership" in ownership_intro.lower()

    dependency_intro = answer_composition_service._generate_intro("dependency")
    assert "depend" in dependency_intro.lower()

    runbook_intro = answer_composition_service._generate_intro("runbook")
    assert "runbook" in runbook_intro.lower() or "operational" in runbook_intro.lower()


def test_determine_response_type(answer_composition_service):
    """Test response type determination."""
    from app.schemas.answers import ConfidenceDimensions, ConfidenceScoreDetail

    high_confidence = ConfidenceScoreDetail(
        overall_score=0.85,
        confidence_band="high",
        dimensions=ConfidenceDimensions(
            evidence_quality=0.9,
            freshness=0.9,
            consistency=0.8,
            citation_coverage=0.95
        ),
        flags=[]
    )

    response_type = answer_composition_service._determine_response_type(high_confidence)
    assert response_type == "supported_answer"

    insufficient_confidence = ConfidenceScoreDetail(
        overall_score=0.2,
        confidence_band="insufficient",
        dimensions=ConfidenceDimensions(
            evidence_quality=0.2,
            freshness=0.3,
            consistency=0.2,
            citation_coverage=0.1
        ),
        flags=["low_evidence", "missing_knowledge"]
    )

    response_type = answer_composition_service._determine_response_type(insufficient_confidence)
    assert response_type == "limitation"


def test_map_flag_to_limitation(answer_composition_service, sample_evidence_bundle):
    """Test mapping confidence flags to limitations."""
    from app.schemas.citations import CitationCoverageReport

    coverage_report = CitationCoverageReport(
        total_claims=10,
        cited_claims=7,
        coverage_percentage=0.70,
        uncited_claims=["claim1", "claim2", "claim3"],
        meets_threshold=False
    )

    limitation_type, severity, description = answer_composition_service._map_flag_to_limitation(
        flag="low_evidence",
        chunks=sample_evidence_bundle.chunks,
        coverage_report=coverage_report
    )

    assert limitation_type == "missing_knowledge"
    assert severity == "high"
    assert description is not None


def test_generate_limitation_text(answer_composition_service):
    """Test limitation text generation."""
    intent = {"primary_intent": "ownership"}

    text = answer_composition_service._generate_limitation_text("missing_knowledge", intent)
    assert "ownership" in text.lower()
    assert len(text) > 0

    text = answer_composition_service._generate_limitation_text("restricted_access", intent)
    assert "restricted" in text.lower()
