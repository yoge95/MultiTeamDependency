"""Answer API endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.integrations.neo4j_client import Neo4jClient
from app.models.interaction import AnswerLimitation, AnswerRecord, CitationReference, QuestionSession
from app.schemas.answers import AnswerLimitationResponse, AnswerResponse, CitationSummary
from app.schemas.auth import CurrentUser
from app.services.escalation_routing_service import EscalationRoutingService

router = APIRouter(prefix="/answers", tags=["answers"])


@router.get("/{answer_id}", response_model=AnswerResponse)
def get_answer(
    answer_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieve answer with citations, confidence score, freshness warnings, and escalation guidance.

    Requires authentication and session ownership verification.
    """
    answer = db.execute(
        select(AnswerRecord).where(AnswerRecord.answer_id == answer_id)
    ).scalar_one_or_none()

    if not answer:
        raise HTTPException(status_code=404, detail="Answer not found")

    session = db.execute(
        select(QuestionSession).where(QuestionSession.session_id == answer.session_id)
    ).scalar_one_or_none()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if str(session.requesting_stakeholder_id) != current_user.user_id:
        raise HTTPException(
            status_code=403,
            detail="You do not have permission to view this answer"
        )

    citations = db.execute(
        select(CitationReference).where(CitationReference.answer_id == answer_id)
    ).scalars().all()

    citation_summaries = [
        CitationSummary(
            citation_id=c.citation_id,
            claim_text=c.claim_text,
            source_title=c.source_title or "Unknown Source",
            section_path=c.section_path,
            chunk_id=c.chunk_id,
            freshness_status=c.freshness_status,
            last_reviewed_at=None
        )
        for c in citations
    ]

    limitations = db.execute(
        select(AnswerLimitation).where(AnswerLimitation.answer_id == answer_id)
    ).scalars().all()

    limitation_responses = [
        AnswerLimitationResponse(
            limitation_type=lim.limitation_type,
            severity=lim.severity,
            description=lim.description,
            affected_claims=[],
            escalation_guidance=None
        )
        for lim in limitations
    ]

    escalation_contacts = []
    if answer.escalation_required_flag:
        neo4j_client = Neo4jClient()
        escalation_service = EscalationRoutingService(db=db, neo4j_client=neo4j_client)

        intent_classification = {}
        if answer.turn and answer.turn.intent_classification:
            intent_classification = answer.turn.intent_classification

        escalation_contacts = escalation_service.get_escalation_contacts(
            intent_classification=intent_classification,
            domain_id=answer.primary_domain_id,
            limitation_type=limitations[0].limitation_type if limitations else None
        )

    freshness_warnings = []
    stale_citations = [c for c in citations if c.freshness_status == 'stale']
    if stale_citations:
        freshness_warnings.append(
            f"{len(stale_citations)} source(s) have not been reviewed in over 90 days. "
            "Please verify with the domain steward."
        )

    return AnswerResponse(
        answer_id=answer.answer_id,
        session_id=answer.session_id,
        turn_id=answer.turn_id,
        response_type=answer.response_type,
        answer_text=answer.answer_text,
        confidence_band=answer.confidence_band,
        confidence_score=float(answer.confidence_score) if answer.confidence_score else None,
        citations=citation_summaries,
        limitations=limitation_responses,
        escalation_contacts=escalation_contacts,
        freshness_warnings=freshness_warnings,
        created_at=answer.created_at
    )
