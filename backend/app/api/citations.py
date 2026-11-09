"""Citation API endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.schemas.auth import CurrentUser
from app.schemas.citations import CitationDetail
from app.services.citation_service import CitationService

router = APIRouter(prefix="/citations", tags=["citations"])


@router.get("/{citation_id}", response_model=CitationDetail)
def get_citation(
    citation_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieve citation details with source context.

    Returns citation with full lineage: chunk_id → source_version_id → source_record_id.
    """
    citation_service = CitationService(db=db)

    citation_detail = citation_service.get_citation_detail(citation_id)

    if not citation_detail:
        raise HTTPException(status_code=404, detail="Citation not found")

    return citation_detail
