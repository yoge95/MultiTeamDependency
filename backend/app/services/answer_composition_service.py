"""Answer composition service for evidence-grounded synthesis with limitation handling."""

from datetime import datetime
from typing import List, Optional
from uuid import UUID, uuid4

from sqlalchemy.orm import Session

from app.models.interaction import AnswerLimitation, AnswerRecord
from app.schemas.answers import ConfidenceScoreDetail
from app.schemas.retrieval import EvidenceBundle, RetrievedChunk
from app.services.citation_service import CitationService
from app.services.confidence_scoring_service import ConfidenceScoringService
from app.services.escalation_routing_service import EscalationRoutingService


class AnswerCompositionService:
    """Service for synthesizing grounded answers from evidence bundles."""

    def __init__(
        self,
        db: Session,
        citation_service: CitationService,
        confidence_service: ConfidenceScoringService,
        escalation_service: EscalationRoutingService
    ):
        self.db = db
        self.citation_service = citation_service
        self.confidence_service = confidence_service
        self.escalation_service = escalation_service

    def compose_answer(
        self,
        session_id: UUID,
        turn_id: UUID,
        question_text: str,
        evidence_bundle: EvidenceBundle,
        intent_classification: dict,
        domain_id: Optional[UUID] = None
    ) -> UUID:
        """
        Compose a grounded answer with citations and limitations.

        Args:
            session_id: Question session ID
            turn_id: Question turn ID
            question_text: Original question text
            evidence_bundle: Retrieved evidence bundle
            intent_classification: Intent classification from question intake
            domain_id: Primary knowledge domain ID

        Returns:
            Created answer_id
        """
        if not evidence_bundle.chunks:
            return self._compose_limitation_answer(
                session_id=session_id,
                turn_id=turn_id,
                intent_classification=intent_classification,
                limitation_type="missing_knowledge",
                domain_id=domain_id
            )

        answer_text = self._synthesize_answer_text(
            question_text=question_text,
            chunks=evidence_bundle.chunks,
            relationships=evidence_bundle.relationships,
            intent=intent_classification.get('primary_intent', '')
        )

        answer_id = uuid4()

        citation_ids = self.citation_service.generate_citations(
            answer_text=answer_text,
            chunks=evidence_bundle.chunks,
            answer_id=answer_id
        )

        coverage_report = self.citation_service.validate_citation_coverage(
            answer_text=answer_text,
            citation_ids=citation_ids
        )

        confidence_detail = self.confidence_service.score_confidence(
            chunks=evidence_bundle.chunks,
            citation_coverage=coverage_report.coverage_percentage,
            total_claims=coverage_report.total_claims
        )

        response_type = self._determine_response_type(confidence_detail)

        answer = AnswerRecord(
            answer_id=answer_id,
            turn_id=turn_id,
            session_id=session_id,
            response_type=response_type,
            answer_text=answer_text,
            confidence_band=confidence_detail.confidence_band,
            confidence_score=confidence_detail.overall_score,
            citation_completeness_flag=coverage_report.meets_threshold,
            escalation_required_flag=confidence_detail.confidence_band in ['low', 'insufficient'],
            primary_domain_id=domain_id,
            created_at=datetime.utcnow()
        )

        self.db.add(answer)

        self._create_limitations(
            answer_id=answer_id,
            confidence_detail=confidence_detail,
            chunks=evidence_bundle.chunks,
            coverage_report=coverage_report
        )

        self.db.commit()
        return answer_id

    def _synthesize_answer_text(
        self,
        question_text: str,
        chunks: List[RetrievedChunk],
        relationships: List,
        intent: str
    ) -> str:
        """
        Synthesize answer text from evidence chunks.

        Args:
            question_text: Original question
            chunks: Evidence chunks
            relationships: Relationship paths
            intent: Primary intent classification

        Returns:
            Synthesized answer text
        """
        if not chunks:
            return ""

        intro = self._generate_intro(intent)
        body_parts = []

        for i, chunk in enumerate(chunks[:5]):
            snippet = chunk.content[:300].strip()
            if snippet:
                body_parts.append(snippet)

        body = " ".join(body_parts)

        if len(body) > 1500:
            body = body[:1500] + "..."

        answer = f"{intro}\n\n{body}"

        if relationships and intent in ['ownership', 'dependency']:
            answer += self._append_relationship_context(relationships)

        return answer.strip()

    def _generate_intro(self, intent: str) -> str:
        """Generate intent-specific introduction."""
        intros = {
            'ownership': "Based on approved sources, here's what I found about ownership:",
            'dependency': "Here are the relevant dependencies from our knowledge base:",
            'routing': "Based on escalation routes, here are the relevant contacts:",
            'runbook': "Here's the operational guidance from approved runbooks:",
            'onboarding': "Here's onboarding information for new team members:",
            'governance': "Here's what I found about governance processes:"
        }
        return intros.get(intent, "Based on available sources:")

    def _append_relationship_context(self, relationships: List) -> str:
        """Append relationship context to answer."""
        if not relationships:
            return ""

        context_parts = ["\n\nRelated entities:"]
        for rel in relationships[:3]:
            context_parts.append(
                f"- {rel.source_entity_type} → {rel.target_entity_type} ({rel.relationship_type})"
            )

        return " ".join(context_parts)

    def _determine_response_type(self, confidence_detail: ConfidenceScoreDetail) -> str:
        """Determine response type based on confidence."""
        if confidence_detail.confidence_band == 'insufficient':
            return 'limitation'
        elif confidence_detail.confidence_band == 'low':
            return 'limitation'
        elif 'low_citation_coverage' in confidence_detail.flags:
            return 'supported_answer'
        else:
            return 'supported_answer'

    def _create_limitations(
        self,
        answer_id: UUID,
        confidence_detail: ConfidenceScoreDetail,
        chunks: List[RetrievedChunk],
        coverage_report
    ):
        """Create limitation records based on confidence flags."""
        for flag in confidence_detail.flags:
            limitation_type, severity, description = self._map_flag_to_limitation(
                flag, chunks, coverage_report
            )

            if limitation_type:
                limitation = AnswerLimitation(
                    answer_id=answer_id,
                    limitation_type=limitation_type,
                    severity=severity,
                    description=description,
                    created_at=datetime.utcnow()
                )
                self.db.add(limitation)

    def _map_flag_to_limitation(
        self,
        flag: str,
        chunks: List[RetrievedChunk],
        coverage_report
    ) -> tuple:
        """Map confidence flag to limitation details."""
        if flag == 'low_evidence':
            return (
                'missing_knowledge',
                'high',
                f'Limited evidence available ({len(chunks)} sources found).'
            )
        elif flag == 'stale_sources':
            stale_count = sum(1 for c in chunks if c.freshness_state == 'stale')
            return (
                'stale_evidence',
                'medium',
                f'{stale_count} of {len(chunks)} sources have not been reviewed in over 90 days.'
            )
        elif flag == 'conflicting_claims':
            return (
                'conflicting_evidence',
                'medium',
                'Evidence sources contain inconsistent information.'
            )
        elif flag == 'low_citation_coverage':
            return (
                'missing_knowledge',
                'low',
                f'Citation coverage is {coverage_report.coverage_percentage:.0%} (target: 90%).'
            )
        elif flag == 'restricted_access':
            return (
                'restricted_access',
                'high',
                'Some relevant sources are restricted and were filtered from results.'
            )
        else:
            return (None, None, None)

    def _compose_limitation_answer(
        self,
        session_id: UUID,
        turn_id: UUID,
        intent_classification: dict,
        limitation_type: str,
        domain_id: Optional[UUID] = None
    ) -> UUID:
        """Compose a limitation response when evidence is insufficient."""
        answer_id = uuid4()

        answer_text = self._generate_limitation_text(limitation_type, intent_classification)

        answer = AnswerRecord(
            answer_id=answer_id,
            turn_id=turn_id,
            session_id=session_id,
            response_type='limitation',
            answer_text=answer_text,
            confidence_band='insufficient',
            confidence_score=0.0,
            citation_completeness_flag=False,
            escalation_required_flag=True,
            primary_domain_id=domain_id,
            created_at=datetime.utcnow()
        )

        self.db.add(answer)

        limitation = AnswerLimitation(
            answer_id=answer_id,
            limitation_type=limitation_type,
            severity='critical',
            description='No approved sources available to answer this question.',
            created_at=datetime.utcnow()
        )
        self.db.add(limitation)

        self.db.commit()
        return answer_id

    def _generate_limitation_text(self, limitation_type: str, intent: dict) -> str:
        """Generate limitation explanation text."""
        primary_intent = intent.get('primary_intent', '')

        if limitation_type == 'missing_knowledge':
            return (
                f"I don't have approved sources to answer questions about {primary_intent}. "
                "Please contact the platform support team for assistance."
            )
        elif limitation_type == 'restricted_access':
            return (
                "Relevant sources for this question are restricted. "
                "Please request access from the domain steward."
            )
        else:
            return "I'm unable to provide a confident answer based on available sources."
