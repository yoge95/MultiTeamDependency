"""Retrieval orchestration service coordinating multi-source evidence retrieval."""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.integrations.neo4j_client import Neo4jClient
from app.integrations.opensearch_client import OpenSearchClient
from app.models.knowledge import SourceRecord
from app.schemas.auth import AccessScope
from app.schemas.retrieval import (
    EvidenceBundle,
    RelationshipPath,
    RetrievalRequest,
    RetrievedChunk,
)
from app.services.access_control_service import AccessControlService
from app.services.ranking_service import RankingService


class RetrievalOrchestrationService:
    """Service for orchestrating multi-source retrieval from OpenSearch, Neo4j, and PostgreSQL."""

    def __init__(
        self,
        db: Session,
        opensearch_client: Optional[OpenSearchClient] = None,
        neo4j_client: Optional[Neo4jClient] = None,
    ):
        """Initialize retrieval orchestration service.

        Args:
            db: Database session for PostgreSQL queries
            opensearch_client: OpenSearch client for chunk retrieval
            neo4j_client: Neo4j client for relationship traversal
        """
        self.db = db
        self.opensearch_client = opensearch_client or OpenSearchClient()
        self.neo4j_client = neo4j_client or Neo4jClient()
        self.access_control = AccessControlService()
        self.ranking_service = RankingService(db)

    async def retrieve_evidence(self, request: RetrievalRequest, access_scope: AccessScope) -> EvidenceBundle:
        """Retrieve evidence bundle coordinating OpenSearch, Neo4j, and PostgreSQL queries.

        This is the main orchestration method that:
        1. Retrieves chunks from OpenSearch using semantic search
        2. Filters chunks by user's access scope
        3. Enriches chunks with PostgreSQL governance metadata
        4. Ranks chunks by combined relevance
        5. Retrieves relationship paths from Neo4j based on intent
        6. Assembles complete evidence bundle

        Args:
            request: Retrieval request with question and filters
            access_scope: User's effective access scope

        Returns:
            Evidence bundle with chunks, relationships, and metadata
        """
        # Step 1: Determine accessible domains
        accessible_domains = access_scope.accessible_domains or []
        if request.domain_context:
            # Intersect requested domains with accessible domains
            accessible_domains = [d for d in request.domain_context if not accessible_domains or d in accessible_domains]

        # Step 2: Retrieve chunks from OpenSearch
        chunks = await self._retrieve_chunks_from_opensearch(
            query_text=request.question_text,
            domain_ids=accessible_domains,
            access_scope=access_scope,
            max_results=request.max_chunks,
            min_score=request.min_relevance_score,
        )

        # Step 3: Filter chunks by access control
        filtered_chunks = self.access_control.filter_chunks_by_access(chunks, access_scope)

        # Step 4: Enrich chunks with PostgreSQL metadata
        enriched_chunks = self._enrich_chunks_with_metadata(filtered_chunks)

        # Step 5: Rank chunks by combined relevance
        ranked_chunks = self.ranking_service.rank_by_relevance(enriched_chunks)

        # Extract top-ranked chunks
        top_chunks = [rc.chunk for rc in ranked_chunks[:request.max_chunks]]

        # Step 6: Retrieve relationship paths from Neo4j based on intent
        relationships = await self._retrieve_relationships_from_neo4j(
            request=request,
            chunks=top_chunks,
            access_scope=access_scope,
        )

        # Step 7: Assemble evidence bundle
        bundle = EvidenceBundle(
            chunks=top_chunks,
            relationships=relationships,
            metadata={
                "retrieved_at": datetime.utcnow().isoformat(),
                "total_chunks_retrieved": len(chunks),
                "chunks_after_access_filter": len(filtered_chunks),
                "chunks_in_bundle": len(top_chunks),
                "relationships_retrieved": len(relationships),
                "intent": request.intent_classification.get("primary_intent") if request.intent_classification else None,
            }
        )

        return bundle

    async def _retrieve_chunks_from_opensearch(
        self,
        query_text: str,
        domain_ids: List[UUID],
        access_scope: AccessScope,
        max_results: int,
        min_score: float,
    ) -> List[RetrievedChunk]:
        """Retrieve chunks from OpenSearch with semantic search and filters.

        Args:
            query_text: Natural language query
            domain_ids: Filter by domain IDs
            access_scope: User's access scope for tag filtering
            max_results: Maximum chunks to retrieve
            min_score: Minimum relevance score

        Returns:
            List of retrieved chunks
        """
        # Determine access tags based on user's roles
        access_tags = self._determine_access_tags(access_scope)

        # Calculate freshness date threshold (90 days for time-sensitive sources)
        # For general retrieval, we don't exclude stale content but track it
        freshness_date = None  # Could be: datetime.utcnow() - timedelta(days=90)

        try:
            chunks = await self.opensearch_client.search_chunks(
                query_text=query_text,
                domain_ids=domain_ids,
                access_tags=access_tags,
                freshness_date=freshness_date,
                max_results=max_results * 2,  # Retrieve more to account for filtering
                min_score=min_score,
            )
            return chunks
        except Exception as e:
            # Log error and return empty list for graceful degradation
            print(f"OpenSearch retrieval error: {e}")
            return []

    def _enrich_chunks_with_metadata(self, chunks: List[RetrievedChunk]) -> List[RetrievedChunk]:
        """Enrich chunks with PostgreSQL governance metadata.

        Args:
            chunks: List of chunks to enrich

        Returns:
            Enriched chunks with source titles and review dates
        """
        enriched = []

        for chunk in chunks:
            # Fetch source record for title and review metadata
            source = self.db.query(SourceRecord).filter(
                SourceRecord.source_record_id == chunk.source_record_id
            ).first()

            if source:
                chunk.source_title = source.title

                # Get most recent review date
                if source.reviews:
                    chunk.last_reviewed_at = max(review.reviewed_at for review in source.reviews)

            enriched.append(chunk)

        return enriched

    async def _retrieve_relationships_from_neo4j(
        self,
        request: RetrievalRequest,
        chunks: List[RetrievedChunk],
        access_scope: AccessScope,
    ) -> List[RelationshipPath]:
        """Retrieve relationship paths from Neo4j based on intent.

        Args:
            request: Original retrieval request
            chunks: Retrieved chunks (for extracting entity references)
            access_scope: User's access scope

        Returns:
            List of relationship paths
        """
        relationships = []

        if not request.intent_classification:
            return relationships

        intent = request.intent_classification.get("primary_intent")

        try:
            # Ownership intent: retrieve ownership paths
            if intent == "ownership":
                relationships.extend(await self._retrieve_ownership_relationships(chunks))

            # Dependency intent: retrieve service dependencies
            elif intent == "dependency":
                relationships.extend(await self._retrieve_dependency_relationships(chunks))

            # Routing intent: retrieve escalation routes
            elif intent == "routing":
                relationships.extend(await self._retrieve_escalation_relationships(chunks, access_scope))

            # For other intents, retrieve general context relationships
            else:
                relationships.extend(await self._retrieve_context_relationships(chunks))

        except Exception as e:
            # Log error and continue with empty relationships
            print(f"Neo4j retrieval error: {e}")

        return relationships

    async def _retrieve_ownership_relationships(self, chunks: List[RetrievedChunk]) -> List[RelationshipPath]:
        """Retrieve ownership relationships for entities mentioned in chunks."""
        relationships = []

        # Extract entity references from chunks (simplified - would use NER in production)
        # For now, get domain ownership from source records
        for chunk in chunks:
            source = self.db.query(SourceRecord).filter(
                SourceRecord.source_record_id == chunk.source_record_id
            ).first()

            if source:
                # Create relationship path for domain ownership
                ownership_paths = await self.neo4j_client.get_ownership_path(
                    entity_id=source.domain_id,
                    entity_type="domain"
                )
                relationships.extend(ownership_paths)

        return relationships

    async def _retrieve_dependency_relationships(self, chunks: List[RetrievedChunk]) -> List[RelationshipPath]:
        """Retrieve service dependency relationships."""
        relationships = []

        # Would extract service references from chunks
        # For now, return empty list (requires NER and entity linking)

        return relationships

    async def _retrieve_escalation_relationships(
        self, chunks: List[RetrievedChunk], access_scope: AccessScope
    ) -> List[RelationshipPath]:
        """Retrieve escalation routes for domains in chunks."""
        relationships = []

        for chunk in chunks:
            escalation_paths = await self.neo4j_client.get_escalation_route(
                domain_id=chunk.domain_id,
                stakeholder_role="escalation_contact"
            )
            relationships.extend(escalation_paths)

        return relationships

    async def _retrieve_context_relationships(self, chunks: List[RetrievedChunk]) -> List[RelationshipPath]:
        """Retrieve general context relationships."""
        # For general intents, return minimal relationship context
        return []

    def _determine_access_tags(self, access_scope: AccessScope) -> List[str]:
        """Determine access tags user can retrieve based on roles.

        Args:
            access_scope: User's access scope

        Returns:
            List of access tags user can access
        """
        # Map roles to access levels
        if "platform_administrator" in access_scope.roles or "governance_reviewer" in access_scope.roles:
            return ["public", "internal", "confidential", "restricted"]
        elif "knowledge_steward" in access_scope.roles:
            return ["public", "internal", "confidential"]
        else:
            # End users: public and internal only
            return ["public", "internal"]
