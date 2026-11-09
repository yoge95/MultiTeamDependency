"""Confidence scoring service calculating multi-dimensional answer confidence."""

from datetime import datetime, timedelta
from typing import List

from app.schemas.answers import ConfidenceDimensions, ConfidenceScoreDetail
from app.schemas.retrieval import RetrievedChunk


class ConfidenceScoringService:
    """Service for calculating multi-dimensional confidence scores."""

    def __init__(self):
        self.evidence_quality_weight = 0.40
        self.freshness_weight = 0.25
        self.consistency_weight = 0.20
        self.citation_coverage_weight = 0.15
        self.stale_threshold_days = 90

    def score_confidence(
        self,
        chunks: List[RetrievedChunk],
        citation_coverage: float,
        total_claims: int = 0
    ) -> ConfidenceScoreDetail:
        """
        Calculate overall confidence score from multiple dimensions.

        Args:
            chunks: Retrieved evidence chunks
            citation_coverage: Citation coverage percentage (0.0-1.0)
            total_claims: Total number of substantive claims

        Returns:
            ConfidenceScoreDetail with overall score and dimension breakdown
        """
        if not chunks:
            return ConfidenceScoreDetail(
                overall_score=0.0,
                confidence_band="insufficient",
                dimensions=ConfidenceDimensions(
                    evidence_quality=0.0,
                    freshness=0.0,
                    consistency=0.0,
                    citation_coverage=0.0
                ),
                flags=["missing_knowledge"],
                explanation="No evidence available to support an answer."
            )

        evidence_quality = self.calculate_evidence_quality_score(chunks)
        freshness = self.calculate_freshness_score(chunks)
        consistency = self.calculate_consistency_score(chunks)

        overall_score = (
            evidence_quality * self.evidence_quality_weight +
            freshness * self.freshness_weight +
            consistency * self.consistency_weight +
            citation_coverage * self.citation_coverage_weight
        )

        confidence_band = self._determine_confidence_band(overall_score)
        flags = self._identify_confidence_flags(chunks, citation_coverage, evidence_quality, freshness, consistency)
        explanation = self._generate_explanation(confidence_band, flags, overall_score)

        return ConfidenceScoreDetail(
            overall_score=round(overall_score, 4),
            confidence_band=confidence_band,
            dimensions=ConfidenceDimensions(
                evidence_quality=round(evidence_quality, 4),
                freshness=round(freshness, 4),
                consistency=round(consistency, 4),
                citation_coverage=round(citation_coverage, 4)
            ),
            flags=flags,
            explanation=explanation
        )

    def calculate_evidence_quality_score(self, chunks: List[RetrievedChunk]) -> float:
        """
        Score evidence quality based on relevance, approval state, and source metadata.

        Args:
            chunks: Retrieved evidence chunks

        Returns:
            Quality score between 0.0 and 1.0
        """
        if not chunks:
            return 0.0

        total_score = 0.0
        for chunk in chunks:
            chunk_score = chunk.relevance_score * 0.6

            if hasattr(chunk, 'approval_state'):
                approval_score = {
                    'approved': 1.0,
                    'pending': 0.5,
                    'rejected': 0.0,
                    'archived': 0.3
                }.get(chunk.approval_state, 0.5)
                chunk_score += approval_score * 0.4
            else:
                chunk_score += 0.4

            total_score += chunk_score

        return min(total_score / len(chunks), 1.0)

    def calculate_freshness_score(self, chunks: List[RetrievedChunk]) -> float:
        """
        Score freshness based on review dates and staleness state.

        Args:
            chunks: Retrieved evidence chunks

        Returns:
            Freshness score between 0.0 and 1.0
        """
        if not chunks:
            return 0.0

        now = datetime.utcnow()
        stale_threshold = timedelta(days=self.stale_threshold_days)
        total_score = 0.0

        for chunk in chunks:
            if not chunk.last_reviewed_at:
                chunk_score = 0.5
            else:
                age = now - chunk.last_reviewed_at
                if age < stale_threshold:
                    chunk_score = 1.0
                elif age < stale_threshold * 2:
                    chunk_score = 0.6
                else:
                    chunk_score = 0.3

            if chunk.freshness_state == 'exception_granted':
                chunk_score = max(chunk_score, 0.7)
            elif chunk.freshness_state == 'stale':
                chunk_score = min(chunk_score, 0.4)

            total_score += chunk_score

        return total_score / len(chunks)

    def calculate_consistency_score(self, chunks: List[RetrievedChunk]) -> float:
        """
        Score consistency across retrieved chunks (simplified heuristic).

        Args:
            chunks: Retrieved evidence chunks

        Returns:
            Consistency score between 0.0 and 1.0
        """
        if not chunks:
            return 0.0

        if len(chunks) == 1:
            return 1.0

        relevance_scores = [c.relevance_score for c in chunks]
        mean_relevance = sum(relevance_scores) / len(relevance_scores)
        variance = sum((s - mean_relevance) ** 2 for s in relevance_scores) / len(relevance_scores)

        consistency = 1.0 - min(variance * 2, 1.0)
        return max(consistency, 0.0)

    def _determine_confidence_band(self, score: float) -> str:
        """Determine confidence band from overall score."""
        if score >= 0.80:
            return "high"
        elif score >= 0.60:
            return "medium"
        elif score >= 0.40:
            return "low"
        else:
            return "insufficient"

    def _identify_confidence_flags(
        self,
        chunks: List[RetrievedChunk],
        citation_coverage: float,
        evidence_quality: float,
        freshness: float,
        consistency: float
    ) -> List[str]:
        """Identify confidence flags based on dimension scores."""
        flags = []

        if evidence_quality < 0.5:
            flags.append("low_evidence")

        if freshness < 0.5:
            stale_count = sum(1 for c in chunks if c.freshness_state == 'stale')
            if stale_count > 0:
                flags.append("stale_sources")

        if consistency < 0.6:
            flags.append("conflicting_claims")

        if citation_coverage < 0.9:
            flags.append("low_citation_coverage")

        restricted_count = sum(1 for c in chunks if 'restricted' in c.access_scope_tag.lower())
        if restricted_count > len(chunks) * 0.3:
            flags.append("restricted_access")

        return flags

    def _generate_explanation(self, band: str, flags: List[str], score: float) -> str:
        """Generate human-readable explanation of confidence score."""
        if band == "high":
            return f"High confidence answer (score: {score:.2f}) based on approved, current sources with strong citation coverage."
        elif band == "medium":
            explanation = f"Medium confidence answer (score: {score:.2f})."
            if "stale_sources" in flags:
                explanation += " Some sources may be out of date."
            if "low_citation_coverage" in flags:
                explanation += " Citation coverage could be improved."
            return explanation
        elif band == "low":
            explanation = f"Low confidence answer (score: {score:.2f})."
            if "low_evidence" in flags:
                explanation += " Limited evidence available."
            if "stale_sources" in flags:
                explanation += " Sources are outdated."
            if "conflicting_claims" in flags:
                explanation += " Evidence sources contain inconsistencies."
            return explanation
        else:
            return f"Insufficient confidence (score: {score:.2f}) to provide a reliable answer. Consider escalating to a subject matter expert."
