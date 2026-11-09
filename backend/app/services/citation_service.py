"""Citation service for claim-to-source mapping with lineage verification."""

import re
from datetime import datetime
from typing import List, Optional
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.interaction import CitationReference as CitationReferenceModel
from app.models.knowledge import SourceChunk, SourceRecord, SourceVersion
from app.schemas.citations import CitationCoverageReport, CitationDetail
from app.schemas.retrieval import RetrievedChunk


class CitationService:
    """Service for generating claim-level citations with provenance tracking."""

    def __init__(self, db: Session):
        self.db = db
        self.min_claim_length = 20
        self.citation_coverage_threshold = 0.90

    def generate_citations(
        self,
        answer_text: str,
        chunks: List[RetrievedChunk],
        answer_id: UUID
    ) -> List[UUID]:
        """
        Generate claim-level citations linking answer to source chunks.

        Args:
            answer_text: The composed answer text
            chunks: Evidence chunks used in answer composition
            answer_id: Answer record ID for citation linking

        Returns:
            List of citation IDs created
        """
        if not answer_text or not chunks:
            return []

        claims = self._extract_claims(answer_text)
        citation_ids = []

        for claim in claims:
            matched_chunk = self._match_claim_to_chunk(claim, chunks)
            if matched_chunk:
                citation_id = self._create_citation(
                    answer_id=answer_id,
                    claim_text=claim,
                    chunk=matched_chunk
                )
                citation_ids.append(citation_id)

        self.db.commit()
        return citation_ids

    def validate_citation_coverage(
        self,
        answer_text: str,
        citation_ids: List[UUID]
    ) -> CitationCoverageReport:
        """
        Validate that substantive claims are citation-backed.

        Args:
            answer_text: The composed answer text
            citation_ids: List of citation IDs for this answer

        Returns:
            CitationCoverageReport with coverage metrics
        """
        claims = self._extract_claims(answer_text)
        total_claims = len(claims)

        citations = self.db.execute(
            select(CitationReferenceModel).where(
                CitationReferenceModel.citation_id.in_(citation_ids)
            )
        ).scalars().all()

        cited_claims_text = {c.claim_text for c in citations}
        cited_count = len(cited_claims_text)
        uncited = [c for c in claims if c not in cited_claims_text]

        coverage_percentage = cited_count / total_claims if total_claims > 0 else 0.0

        return CitationCoverageReport(
            total_claims=total_claims,
            cited_claims=cited_count,
            coverage_percentage=round(coverage_percentage, 4),
            uncited_claims=uncited[:5],
            meets_threshold=coverage_percentage >= self.citation_coverage_threshold
        )

    def get_citation_detail(self, citation_id: UUID) -> Optional[CitationDetail]:
        """
        Retrieve detailed citation with full source context.

        Args:
            citation_id: Citation ID to retrieve

        Returns:
            CitationDetail with source metadata or None if not found
        """
        citation = self.db.execute(
            select(CitationReferenceModel).where(
                CitationReferenceModel.citation_id == citation_id
            )
        ).scalar_one_or_none()

        if not citation:
            return None

        chunk = self.db.execute(
            select(SourceChunk).where(
                SourceChunk.chunk_id == citation.chunk_id
            )
        ).scalar_one_or_none()

        if not chunk:
            return None

        version = self.db.execute(
            select(SourceVersion).where(
                SourceVersion.source_version_id == chunk.source_version_id
            )
        ).scalar_one_or_none()

        source = self.db.execute(
            select(SourceRecord).where(
                SourceRecord.source_record_id == (version.source_record_id if version else None)
            )
        ).scalar_one_or_none()

        if not version or not source:
            return None

        return CitationDetail(
            citation_id=citation.citation_id,
            answer_id=citation.answer_id,
            claim_text=citation.claim_text,
            chunk_id=citation.chunk_id,
            source_record_id=source.source_record_id,
            source_version_id=version.source_version_id,
            source_title=source.title,
            section_path=chunk.section_path or "",
            evidence_text=chunk.chunk_text[:500],
            freshness_status=citation.freshness_status,
            last_reviewed_at=version.last_reviewed_at,
            approval_state=source.approval_state,
            created_at=citation.created_at
        )

    def _extract_claims(self, text: str) -> List[str]:
        """
        Extract substantive claims from answer text.

        Args:
            text: Answer text to analyze

        Returns:
            List of claim sentences
        """
        if not text:
            return []

        sentences = re.split(r'[.!?]+', text)
        claims = []

        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) >= self.min_claim_length:
                if not sentence.lower().startswith(('here', 'please', 'you can', 'i found', 'let me', 'based on')):
                    claims.append(sentence)

        return claims[:20]

    def _match_claim_to_chunk(
        self,
        claim: str,
        chunks: List[RetrievedChunk]
    ) -> Optional[RetrievedChunk]:
        """
        Match a claim to the most relevant evidence chunk.

        Args:
            claim: Claim text to match
            chunks: Available evidence chunks

        Returns:
            Best matching chunk or None
        """
        if not chunks:
            return None

        best_match = None
        best_score = 0.0

        claim_lower = claim.lower()
        claim_words = set(re.findall(r'\w+', claim_lower))

        for chunk in chunks:
            chunk_lower = chunk.content.lower()
            chunk_words = set(re.findall(r'\w+', chunk_lower))

            overlap = len(claim_words & chunk_words)
            if overlap > 0:
                score = overlap / len(claim_words)
                if score > best_score:
                    best_score = score
                    best_match = chunk

        return best_match if best_score > 0.2 else None

    def _create_citation(
        self,
        answer_id: UUID,
        claim_text: str,
        chunk: RetrievedChunk
    ) -> UUID:
        """
        Create citation reference with lineage verification.

        Args:
            answer_id: Answer record ID
            claim_text: Claim being cited
            chunk: Source chunk providing evidence

        Returns:
            Created citation ID
        """
        freshness_status = self._determine_freshness_status(chunk)

        citation = CitationReferenceModel(
            citation_id=uuid4(),
            answer_id=answer_id,
            chunk_id=chunk.chunk_id,
            claim_text=claim_text[:1000],
            source_title=chunk.source_title or "Unknown Source",
            section_path=chunk.section_path or "",
            freshness_status=freshness_status,
            created_at=datetime.utcnow()
        )

        self.db.add(citation)
        return citation.citation_id

    def _determine_freshness_status(self, chunk: RetrievedChunk) -> str:
        """Determine freshness status for citation."""
        if chunk.freshness_state == 'exception_granted':
            return 'exception_granted'
        elif chunk.freshness_state == 'stale':
            return 'stale'
        else:
            return 'current'
