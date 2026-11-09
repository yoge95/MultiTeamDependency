"""Unit tests for retrieval orchestration service and data store integrations."""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock, patch

from app.schemas.auth import AccessScope
from app.schemas.retrieval import (
    EvidenceBundle,
    RelationshipPath,
    RetrievalRequest,
    RetrievedChunk,
)
from app.services.access_control_service import AccessControlService
from app.services.ranking_service import RankingService
from app.services.retrieval_orchestration_service import RetrievalOrchestrationService
from app.integrations.opensearch_client import OpenSearchClient
from app.integrations.neo4j_client import Neo4jClient


@pytest.fixture
def mock_db():
    """Mock database session."""
    return MagicMock()


@pytest.fixture
def sample_access_scope():
    """Sample access scope for testing."""
    return AccessScope(
        user_id="user-123",
        roles=["end_user"],
        team_memberships=[uuid4()],
        accessible_domains=[uuid4(), uuid4()],
        source_scope_filter={},
    )


@pytest.fixture
def sample_chunks():
    """Sample retrieved chunks."""
    domain_id_1 = uuid4()
    domain_id_2 = uuid4()
    
    return [
        RetrievedChunk(
            chunk_id=uuid4(),
            source_record_id=uuid4(),
            source_version_id=uuid4(),
            section_path="/ownership/payment-service",
            content="The Payment Service is owned by the Payments Team.",
            relevance_score=0.85,
            access_scope_tag="internal",
            freshness_state="current",
            domain_id=domain_id_1,
            source_title="Service Ownership Registry",
            last_reviewed_at=datetime.utcnow() - timedelta(days=15),
        ),
        RetrievedChunk(
            chunk_id=uuid4(),
            source_record_id=uuid4(),
            source_version_id=uuid4(),
            section_path="/dependencies/payment-service",
            content="Payment Service depends on Auth API and User Service.",
            relevance_score=0.75,
            access_scope_tag="internal",
            freshness_state="current",
            domain_id=domain_id_2,
            source_title="Service Dependencies",
            last_reviewed_at=datetime.utcnow() - timedelta(days=45),
        ),
        RetrievedChunk(
            chunk_id=uuid4(),
            source_record_id=uuid4(),
            source_version_id=uuid4(),
            section_path="/sensitive/payment-data",
            content="Payment data processing restricted to authorized teams only.",
            relevance_score=0.70,
            access_scope_tag="restricted",
            freshness_state="current",
            domain_id=domain_id_1,
            source_title="Security Policies",
            last_reviewed_at=datetime.utcnow() - timedelta(days=5),
        ),
    ]


# Access Control Service Tests

def test_access_control_filters_by_domain(sample_chunks, sample_access_scope):
    """Test that access control filters chunks by accessible domains."""
    service = AccessControlService()
    
    # Set accessible_domains to only include first chunk's domain
    sample_access_scope.accessible_domains = [sample_chunks[0].domain_id]
    
    filtered = service.filter_chunks_by_access(sample_chunks, sample_access_scope)
    
    # Should only include chunks from accessible domain
    assert len(filtered) <= len(sample_chunks)
    for chunk in filtered:
        assert chunk.domain_id in sample_access_scope.accessible_domains


def test_access_control_filters_by_access_tag(sample_chunks, sample_access_scope):
    """Test that access control filters chunks by access scope tag."""
    service = AccessControlService()
    
    # End user should not see restricted content
    sample_access_scope.roles = ["end_user"]
    sample_access_scope.accessible_domains = []  # Allow all domains for this test
    
    filtered = service.filter_chunks_by_access(sample_chunks, sample_access_scope)
    
    # Should not include restricted chunk
    for chunk in filtered:
        assert chunk.access_scope_tag != "restricted"


def test_access_control_platform_admin_sees_restricted(sample_chunks, sample_access_scope):
    """Test that platform administrators can see restricted content."""
    service = AccessControlService()
    
    # Platform admin should see all content
    sample_access_scope.roles = ["platform_administrator"]
    sample_access_scope.accessible_domains = []  # Allow all domains
    
    filtered = service.filter_chunks_by_access(sample_chunks, sample_access_scope)
    
    # Should include restricted chunk
    restricted_chunks = [c for c in filtered if c.access_scope_tag == "restricted"]
    assert len(restricted_chunks) > 0


def test_access_control_respects_source_exclusions(sample_chunks, sample_access_scope):
    """Test that access control respects excluded sources."""
    service = AccessControlService()
    
    # Exclude first chunk's source
    excluded_source = str(sample_chunks[0].source_record_id)
    sample_access_scope.source_scope_filter = {
        "excluded_sources": [excluded_source]
    }
    sample_access_scope.accessible_domains = []  # Allow all domains
    
    filtered = service.filter_chunks_by_access(sample_chunks, sample_access_scope)
    
    # Should not include excluded source
    for chunk in filtered:
        assert str(chunk.source_record_id) != excluded_source


def test_access_control_respects_source_whitelist(sample_chunks, sample_access_scope):
    """Test that access control respects allowed sources whitelist."""
    service = AccessControlService()
    
    # Only allow first chunk's source
    allowed_source = str(sample_chunks[0].source_record_id)
    sample_access_scope.source_scope_filter = {
        "allowed_sources": [allowed_source]
    }
    sample_access_scope.accessible_domains = []  # Allow all domains
    
    filtered = service.filter_chunks_by_access(sample_chunks, sample_access_scope)
    
    # Should only include allowed source
    for chunk in filtered:
        assert str(chunk.source_record_id) == allowed_source


def test_get_accessible_domains_empty_returns_all(sample_access_scope):
    """Test that empty accessible_domains means access to all domains."""
    service = AccessControlService()
    
    all_domains = [uuid4(), uuid4(), uuid4()]
    sample_access_scope.accessible_domains = []
    
    accessible = service.get_accessible_domains(sample_access_scope, all_domains)
    
    assert accessible == all_domains


def test_can_access_source_with_no_restrictions(sample_access_scope):
    """Test that user can access source with no restrictions."""
    service = AccessControlService()
    
    source_id = uuid4()
    sample_access_scope.source_scope_filter = {}
    
    assert service.can_access_source(source_id, sample_access_scope) is True


# Ranking Service Tests

def test_ranking_service_ranks_by_combined_score(mock_db, sample_chunks):
    """Test that ranking service combines multiple score dimensions."""
    # Mock database queries
    mock_source = MagicMock()
    mock_source.approval_state = "approved"
    mock_source.reviews = [MagicMock(reviewed_at=datetime.utcnow() - timedelta(days=10))]
    mock_db.query.return_value.filter.return_value.first.return_value = mock_source
    
    service = RankingService(mock_db)
    ranked = service.rank_by_relevance(sample_chunks)
    
    # Should return same number of chunks
    assert len(ranked) == len(sample_chunks)
    
    # Each ranked chunk should have combined score and components
    for rc in ranked:
        assert hasattr(rc, "combined_score")
        assert hasattr(rc, "score_components")
        assert "retrieval" in rc.score_components
        assert "freshness" in rc.score_components
        assert "approval" in rc.score_components
        assert "access" in rc.score_components
    
    # Should be sorted by combined_score descending
    scores = [rc.combined_score for rc in ranked]
    assert scores == sorted(scores, reverse=True)


def test_ranking_freshness_score_calculation(mock_db):
    """Test freshness score calculation."""
    service = RankingService(mock_db)
    
    # Very fresh (< 30 days)
    fresh_score = service._calculate_freshness_score(
        datetime.utcnow() - timedelta(days=15),
        "current"
    )
    assert fresh_score >= 0.9
    
    # Approaching staleness (60-90 days)
    aging_score = service._calculate_freshness_score(
        datetime.utcnow() - timedelta(days=75),
        "current"
    )
    assert 0.5 <= aging_score <= 0.8
    
    # Stale
    stale_score = service._calculate_freshness_score(
        datetime.utcnow() - timedelta(days=100),
        "stale"
    )
    assert stale_score <= 0.4
    
    # Archived
    archived_score = service._calculate_freshness_score(
        datetime.utcnow() - timedelta(days=50),
        "archived"
    )
    assert archived_score <= 0.2


def test_ranking_approval_score_calculation(mock_db):
    """Test approval score calculation."""
    service = RankingService(mock_db)
    
    assert service._calculate_approval_score("approved") == 1.0
    assert service._calculate_approval_score("pending") < 1.0
    assert service._calculate_approval_score("rejected") < 0.5
    assert service._calculate_approval_score("archived") < 0.5


def test_ranking_access_score_calculation(mock_db):
    """Test access score calculation."""
    service = RankingService(mock_db)
    
    assert service._calculate_access_score("public") == 1.0
    assert service._calculate_access_score("internal") >= 0.8
    assert service._calculate_access_score("confidential") < 0.8
    assert service._calculate_access_score("restricted") < 0.7


# Retrieval Orchestration Service Tests

@pytest.mark.asyncio
async def test_retrieve_evidence_returns_bundle(mock_db, sample_access_scope):
    """Test that retrieve_evidence returns complete evidence bundle."""
    # Mock OpenSearch client
    mock_opensearch = AsyncMock(spec=OpenSearchClient)
    mock_opensearch.search_chunks.return_value = []
    
    # Mock Neo4j client
    mock_neo4j = AsyncMock(spec=Neo4jClient)
    mock_neo4j.get_ownership_path.return_value = []
    mock_neo4j.get_escalation_route.return_value = []
    
    service = RetrievalOrchestrationService(
        db=mock_db,
        opensearch_client=mock_opensearch,
        neo4j_client=mock_neo4j,
    )
    
    request = RetrievalRequest(
        question_text="Who owns the payment service?",
        domain_context=[],
        access_scope=sample_access_scope.dict(),
        max_chunks=20,
    )
    
    bundle = await service.retrieve_evidence(request, sample_access_scope)
    
    assert isinstance(bundle, EvidenceBundle)
    assert hasattr(bundle, "chunks")
    assert hasattr(bundle, "relationships")
    assert hasattr(bundle, "metadata")
    assert "retrieved_at" in bundle.metadata


@pytest.mark.asyncio
async def test_retrieve_evidence_filters_by_access(mock_db, sample_access_scope, sample_chunks):
    """Test that retrieve_evidence filters chunks by access control."""
    # Mock OpenSearch to return all chunks including restricted
    mock_opensearch = AsyncMock(spec=OpenSearchClient)
    mock_opensearch.search_chunks.return_value = sample_chunks
    
    # Mock Neo4j
    mock_neo4j = AsyncMock(spec=Neo4jClient)
    mock_neo4j.get_ownership_path.return_value = []
    
    # Mock database queries for ranking
    mock_source = MagicMock()
    mock_source.title = "Test Source"
    mock_source.approval_state = "approved"
    mock_source.reviews = []
    mock_db.query.return_value.filter.return_value.first.return_value = mock_source
    
    service = RetrievalOrchestrationService(
        db=mock_db,
        opensearch_client=mock_opensearch,
        neo4j_client=mock_neo4j,
    )
    
    # End user should not see restricted chunks
    sample_access_scope.roles = ["end_user"]
    sample_access_scope.accessible_domains = []  # Allow all domains
    
    request = RetrievalRequest(
        question_text="What are the payment policies?",
        access_scope=sample_access_scope.dict(),
    )
    
    bundle = await service.retrieve_evidence(request, sample_access_scope)
    
    # Restricted chunk should be filtered out
    for chunk in bundle.chunks:
        assert chunk.access_scope_tag != "restricted"


@pytest.mark.asyncio
async def test_retrieve_evidence_handles_opensearch_error(mock_db, sample_access_scope):
    """Test graceful handling of OpenSearch errors."""
    # Mock OpenSearch to raise exception
    mock_opensearch = AsyncMock(spec=OpenSearchClient)
    mock_opensearch.search_chunks.side_effect = Exception("OpenSearch connection error")
    
    # Mock Neo4j
    mock_neo4j = AsyncMock(spec=Neo4jClient)
    
    service = RetrievalOrchestrationService(
        db=mock_db,
        opensearch_client=mock_opensearch,
        neo4j_client=mock_neo4j,
    )
    
    request = RetrievalRequest(
        question_text="Who owns the payment service?",
        access_scope=sample_access_scope.dict(),
    )
    
    # Should not raise exception, return empty bundle
    bundle = await service.retrieve_evidence(request, sample_access_scope)
    
    assert isinstance(bundle, EvidenceBundle)
    assert len(bundle.chunks) == 0


@pytest.mark.asyncio
async def test_retrieve_evidence_enriches_chunks_with_metadata(mock_db, sample_access_scope, sample_chunks):
    """Test that chunks are enriched with PostgreSQL metadata."""
    # Mock OpenSearch
    mock_opensearch = AsyncMock(spec=OpenSearchClient)
    mock_opensearch.search_chunks.return_value = sample_chunks
    
    # Mock Neo4j
    mock_neo4j = AsyncMock(spec=Neo4jClient)
    mock_neo4j.get_ownership_path.return_value = []
    
    # Mock database to return source with title and reviews
    mock_source = MagicMock()
    mock_source.title = "Enriched Source Title"
    mock_source.approval_state = "approved"
    mock_review = MagicMock()
    mock_review.reviewed_at = datetime.utcnow() - timedelta(days=10)
    mock_source.reviews = [mock_review]
    mock_db.query.return_value.filter.return_value.first.return_value = mock_source
    
    service = RetrievalOrchestrationService(
        db=mock_db,
        opensearch_client=mock_opensearch,
        neo4j_client=mock_neo4j,
    )
    
    sample_access_scope.accessible_domains = []  # Allow all domains
    
    request = RetrievalRequest(
        question_text="Test question",
        access_scope=sample_access_scope.dict(),
    )
    
    bundle = await service.retrieve_evidence(request, sample_access_scope)
    
    # Chunks should have source_title enriched
    assert len(bundle.chunks) > 0


@pytest.mark.asyncio
async def test_retrieve_evidence_with_ownership_intent(mock_db, sample_access_scope, sample_chunks):
    """Test that ownership intent triggers ownership relationship retrieval."""
    # Mock OpenSearch
    mock_opensearch = AsyncMock(spec=OpenSearchClient)
    mock_opensearch.search_chunks.return_value = sample_chunks[:1]  # Return one chunk
    
    # Mock Neo4j to return ownership paths
    mock_neo4j = AsyncMock(spec=Neo4jClient)
    ownership_path = RelationshipPath(
        relationship_type="OWNED_BY",
        source_entity_type="domain",
        source_entity_id=sample_chunks[0].domain_id,
        target_entity_type="team",
        target_entity_id=uuid4(),
        path_length=1,
    )
    mock_neo4j.get_ownership_path.return_value = [ownership_path]
    
    # Mock database
    mock_source = MagicMock()
    mock_source.title = "Test Source"
    mock_source.approval_state = "approved"
    mock_source.reviews = []
    mock_source.domain_id = sample_chunks[0].domain_id
    mock_db.query.return_value.filter.return_value.first.return_value = mock_source
    
    service = RetrievalOrchestrationService(
        db=mock_db,
        opensearch_client=mock_opensearch,
        neo4j_client=mock_neo4j,
    )
    
    sample_access_scope.accessible_domains = []  # Allow all domains
    
    request = RetrievalRequest(
        question_text="Who owns the payment service?",
        access_scope=sample_access_scope.dict(),
        intent_classification={"primary_intent": "ownership"},
    )
    
    bundle = await service.retrieve_evidence(request, sample_access_scope)
    
    # Should have called get_ownership_path
    assert mock_neo4j.get_ownership_path.called


def test_determine_access_tags_for_end_user(mock_db):
    """Test access tag determination for end user."""
    service = RetrievalOrchestrationService(db=mock_db)
    
    access_scope = AccessScope(
        user_id="user-123",
        roles=["end_user"],
        team_memberships=[],
        accessible_domains=[],
    )
    
    tags = service._determine_access_tags(access_scope)
    
    assert "public" in tags
    assert "internal" in tags
    assert "restricted" not in tags


def test_determine_access_tags_for_platform_admin(mock_db):
    """Test access tag determination for platform administrator."""
    service = RetrievalOrchestrationService(db=mock_db)
    
    access_scope = AccessScope(
        user_id="admin-123",
        roles=["platform_administrator"],
        team_memberships=[],
        accessible_domains=[],
    )
    
    tags = service._determine_access_tags(access_scope)
    
    assert "public" in tags
    assert "internal" in tags
    assert "confidential" in tags
    assert "restricted" in tags


# OpenSearch Client Tests

@pytest.mark.asyncio
async def test_opensearch_client_search_chunks():
    """Test OpenSearch client search_chunks interface."""
    client = OpenSearchClient()
    
    # Stub implementation returns empty list
    chunks = await client.search_chunks(
        query_text="test query",
        domain_ids=[uuid4()],
        access_tags=["internal"],
        max_results=10,
        min_score=0.5,
    )
    
    assert isinstance(chunks, list)


@pytest.mark.asyncio
async def test_opensearch_client_health_check():
    """Test OpenSearch client health check."""
    client = OpenSearchClient()
    await client.connect()
    
    is_healthy = await client.health_check()
    
    assert is_healthy is True
    
    await client.disconnect()


# Neo4j Client Tests

@pytest.mark.asyncio
async def test_neo4j_client_get_ownership_path():
    """Test Neo4j client get_ownership_path interface."""
    client = Neo4jClient()
    
    # Stub implementation returns empty list
    paths = await client.get_ownership_path(uuid4(), "service")
    
    assert isinstance(paths, list)


@pytest.mark.asyncio
async def test_neo4j_client_get_dependencies():
    """Test Neo4j client get_dependencies interface."""
    client = Neo4jClient()
    
    # Stub implementation returns empty list
    paths = await client.get_dependencies(uuid4(), direction="upstream")
    
    assert isinstance(paths, list)


@pytest.mark.asyncio
async def test_neo4j_client_get_escalation_route():
    """Test Neo4j client get_escalation_route interface."""
    client = Neo4jClient()
    
    # Stub implementation returns empty list
    paths = await client.get_escalation_route(uuid4())
    
    assert isinstance(paths, list)


@pytest.mark.asyncio
async def test_neo4j_client_health_check():
    """Test Neo4j client health check."""
    client = Neo4jClient()
    
    is_healthy = await client.health_check()
    
    assert is_healthy is True
