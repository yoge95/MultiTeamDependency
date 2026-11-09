"""Ranking service for relevance scoring of retrieved evidence."""

from datetime import datetime
from typing import List

from sqlalchemy.orm import Session

from app.models.knowledge import SourceRecord
from app.schemas.retrieval import RankedChunk, RetrievedChunk


class RankingService:
    """Service for ranking retrieved chunks by combined relevance."""

    def __init__(self, db: Session):
        """Initialize ranking service.

        Args:
            db: Database session for fetching governance metadata
        """
        self.db = db

    def rank_by_relevance(self, chunks: List[RetrievedChunk]) -> List[RankedChunk]:
        """Rank chunks combining retrieval scores with governance metadata.

        Scoring dimensions:
        - Retrieval relevance (40%): Original semantic search score
        - Freshness (30%): How recently the source was reviewed
        - Approval state (20%): Source approval status
        - Access clarity (10%): Clarity of access scope

        Args:
            chunks: List of retrieved chunks with initial relevance scores

        Returns:
            List of ranked chunks with combined scores
        """
        ranked_chunks = []

        for chunk in chunks:
            # Fetch governance metadata from PostgreSQL
            metadata = self._fetch_governance_metadata(chunk.source_record_id, chunk.source_version_id)

            # Calculate dimension scores
            retrieval_score = chunk.relevance_score
            freshness_score = self._calculate_freshness_score(metadata.get("last_reviewed_at"), metadata.get("freshness_state"))
            approval_score = self._calculate_approval_score(metadata.get("approval_state"))
            access_score = self._calculate_access_score(chunk.access_scope_tag)

            # Weighted combination
            combined_score = (
                retrieval_score * 0.40 +
                freshness_score * 0.30 +
                approval_score * 0.20 +
                access_score * 0.10
            )

            ranked_chunk = RankedChunk(
                chunk=chunk,
                combined_score=combined_score,
                score_components={
                    "retrieval": retrieval_score,
                    "freshness": freshness_score,
                    "approval": approval_score,
                    "access": access_score,
                }
            )
            ranked_chunks.append(ranked_chunk)

        # Sort by combined score descending
        ranked_chunks.sort(key=lambda x: x.combined_score, reverse=True)

        return ranked_chunks

    def _fetch_governance_metadata(self, source_record_id, source_version_id) -> dict:
        """Fetch governance metadata from PostgreSQL.

        Args:
            source_record_id: Source record UUID
            source_version_id: Source version UUID

        Returns:
            Dictionary with approval_state, last_reviewed_at, freshness_state
        """
        # Query source record for approval state and review date
        source = self.db.query(SourceRecord).filter(
            SourceRecord.source_record_id == source_record_id
        ).first()

        if not source:
            return {
                "approval_state": "pending",
                "last_reviewed_at": None,
                "freshness_state": "current",
            }

        # Get the most recent review date
        last_reviewed_at = None
        if source.reviews:
            last_reviewed_at = max(review.reviewed_at for review in source.reviews)

        return {
            "approval_state": source.approval_state,
            "last_reviewed_at": last_reviewed_at,
            "freshness_state": "current",  # Would come from chunk metadata in production
        }

    def _calculate_freshness_score(self, last_reviewed_at, freshness_state: str) -> float:
        """Calculate freshness score based on review recency.

        Args:
            last_reviewed_at: Timestamp of last review
            freshness_state: Freshness state (current, stale, exception_granted, archived)

        Returns:
            Freshness score 0.0-1.0
        """
        # If archived or stale without exception, low score
        if freshness_state == "archived":
            return 0.1

        if freshness_state == "stale":
            return 0.3

        if freshness_state == "exception_granted":
            return 0.7

        # Current state: score based on recency
        if not last_reviewed_at:
            return 0.5  # No review date, moderate score

        days_since_review = (datetime.utcnow() - last_reviewed_at).days

        if days_since_review <= 30:
            return 1.0  # Very fresh
        elif days_since_review <= 60:
            return 0.9  # Fresh
        elif days_since_review <= 90:
            return 0.7  # Approaching staleness threshold
        elif days_since_review <= 180:
            return 0.5  # Past staleness threshold
        else:
            return 0.3  # Very old

    def _calculate_approval_score(self, approval_state: str) -> float:
        """Calculate approval score based on source state.

        Args:
            approval_state: Approval state (approved, pending, rejected, archived)

        Returns:
            Approval score 0.0-1.0
        """
        approval_scores = {
            "approved": 1.0,
            "pending": 0.6,
            "rejected": 0.2,
            "archived": 0.1,
        }
        return approval_scores.get(approval_state, 0.5)

    def _calculate_access_score(self, access_scope_tag: str) -> float:
        """Calculate access score based on access clarity.

        Args:
            access_scope_tag: Access scope tag (public, internal, confidential, restricted)

        Returns:
            Access score 0.0-1.0
        """
        # More accessible content scores slightly higher for general queries
        access_scores = {
            "public": 1.0,
            "internal": 0.9,
            "confidential": 0.7,
            "restricted": 0.5,
        }
        return access_scores.get(access_scope_tag, 0.5)
