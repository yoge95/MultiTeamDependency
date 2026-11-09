"""Source governance API endpoints."""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.auth import require_role
from app.database import get_db
from app.schemas.auth import CurrentUser
from app.schemas.governance import (
    FreshnessExceptionRequest,
    FreshnessExceptionResponse,
    SourceApprovalRequest,
    SourceApprovalResponse,
    SourceListItem,
    SourceListResponse,
    SourceRegistrationRequest,
    SourceRegistrationResponse,
)
from app.services.source_governance_service import SourceGovernanceService

router = APIRouter(prefix="/sources", tags=["governance"])


@router.get("/", response_model=SourceListResponse)
async def list_sources(
    domain_id: Optional[UUID] = Query(None, description="Filter by domain ID"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user: CurrentUser = Depends(require_role("knowledge_steward", "governance_reviewer")),
    db: Session = Depends(get_db)
):
    """List sources filtered by user's steward domains.

    Args:
        domain_id: Optional domain filter
        page: Page number
        page_size: Items per page
        current_user: Authenticated user (must be steward or reviewer)
        db: Database session

    Returns:
        Paginated source list
    """
    service = SourceGovernanceService(db)

    sources, total = await service.list_sources(
        current_user=current_user,
        domain_id=domain_id,
        page=page,
        page_size=page_size
    )

    items = [
        SourceListItem(
            source_record_id=source.source_record_id,
            source_key=source.source_key,
            title=source.title,
            source_type=source.source_type,
            domain_id=source.domain_id,
            approval_state=source.approval_state,
            sensitivity_classification=source.sensitivity_classification,
            next_review_due_on=source.next_review_due_on,
            owner_team_id=source.owner_team_id,
            steward_team_id=source.steward_team_id,
            created_at=source.created_at,
            updated_at=source.updated_at
        )
        for source in sources
    ]

    return SourceListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size
    )


@router.post("/", response_model=SourceRegistrationResponse, status_code=status.HTTP_201_CREATED)
async def register_source(
    request: SourceRegistrationRequest,
    current_user: CurrentUser = Depends(require_role("knowledge_steward", "governance_reviewer")),
    db: Session = Depends(get_db)
):
    """Register a new source for governance.

    Args:
        request: Source registration request
        current_user: Authenticated user (must be steward or reviewer)
        db: Database session

    Returns:
        Source registration response

    Raises:
        HTTPException: 409 if source_key already exists, 400 if validation fails
    """
    service = SourceGovernanceService(db)

    try:
        source = await service.register_source(request, current_user)

        return SourceRegistrationResponse(
            source_record_id=source.source_record_id,
            source_key=source.source_key,
            title=source.title,
            approval_state=source.approval_state,
            created_at=source.created_at
        )

    except ValueError as e:
        error_msg = str(e)
        if "already exists" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=error_msg
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg
            )


@router.post("/{source_id}/approve", response_model=SourceApprovalResponse)
async def approve_source(
    source_id: UUID,
    request: SourceApprovalRequest,
    current_user: CurrentUser = Depends(require_role("knowledge_steward", "governance_reviewer")),
    db: Session = Depends(get_db)
):
    """Approve or review a source.

    Args:
        source_id: Source record ID
        request: Approval request
        current_user: Authenticated user (must be steward or reviewer)
        db: Database session

    Returns:
        Source approval response

    Raises:
        HTTPException: 404 if source not found, 403 if not authorized
    """
    service = SourceGovernanceService(db)

    try:
        review = await service.approve_source(source_id, request, current_user)

        return SourceApprovalResponse(
            review_id=review.review_id,
            source_record_id=review.source_record_id,
            reviewer_stakeholder_id=review.reviewer_stakeholder_id,
            review_decision=review.review_decision,
            next_review_due_on=review.next_review_due_on,
            reviewed_at=review.reviewed_at
        )

    except ValueError as e:
        error_msg = str(e)
        if "not found" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_msg
            )
        elif "not steward" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=error_msg
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg
            )


@router.post("/{source_id}/freshness-exception", response_model=FreshnessExceptionResponse)
async def grant_freshness_exception(
    source_id: UUID,
    request: FreshnessExceptionRequest,
    current_user: CurrentUser = Depends(require_role("knowledge_steward", "governance_reviewer")),
    db: Session = Depends(get_db)
):
    """Grant freshness exception for a source.

    Args:
        source_id: Source record ID
        request: Exception request
        current_user: Authenticated user (must be steward or reviewer)
        db: Database session

    Returns:
        Freshness exception response

    Raises:
        HTTPException: 404 if source not found, 403 if not authorized, 400 if validation fails
    """
    service = SourceGovernanceService(db)

    try:
        review = await service.grant_freshness_exception(source_id, request, current_user)

        return FreshnessExceptionResponse(
            review_id=review.review_id,
            source_record_id=review.source_record_id,
            exception_until=review.next_review_due_on,
            reviewed_at=review.reviewed_at,
            message="Freshness exception granted"
        )

    except ValueError as e:
        error_msg = str(e)
        if "not found" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_msg
            )
        elif "not steward" in error_msg or "180 days" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN if "not steward" in error_msg else status.HTTP_400_BAD_REQUEST,
                detail=error_msg
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg
            )
