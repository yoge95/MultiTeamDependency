"""Question submission and status endpoints."""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status

try:
    from slowapi import Limiter
    from slowapi.util import get_remote_address
    SLOWAPI_AVAILABLE = True
except ImportError:
    SLOWAPI_AVAILABLE = False
    Limiter = None

from app.auth import get_current_user
from app.schemas.auth import CurrentUser
from app.schemas.questions import (
    QuestionSubmissionRequest,
    QuestionSubmissionResponse,
    QuestionStatusResponse,
)
from app.services.question_intake_service import QuestionIntakeService
from app.services.session_context_service import SessionContextService
from app.database import get_db
from sqlalchemy.orm import Session

router = APIRouter()

if SLOWAPI_AVAILABLE:
    limiter = Limiter(key_func=get_remote_address)
else:
    limiter = None


def get_question_intake_service(db: Session = Depends(get_db)) -> QuestionIntakeService:
    """Dependency injection for QuestionIntakeService."""
    session_context_service = SessionContextService(db)
    return QuestionIntakeService(db, session_context_service)


def _apply_rate_limit(func):
    """Apply rate limiting decorator if slowapi is available."""
    if SLOWAPI_AVAILABLE and limiter:
        func = limiter.limit("100/minute")(func)
        func = limiter.limit("1000/hour")(func)
    return func


@router.post("/questions", response_model=QuestionSubmissionResponse, status_code=status.HTTP_201_CREATED)
@_apply_rate_limit
async def submit_question(
    request: Request,
    question_data: QuestionSubmissionRequest,
    current_user: CurrentUser = Depends(get_current_user),
    service: QuestionIntakeService = Depends(get_question_intake_service),
):
    """
    Submit a new question or follow-up turn.
    
    Rate limits:
    - 100 requests per minute per user
    - 1000 requests per hour per user
    
    Supports idempotency via Idempotency-Key header (24-hour window).
    
    Args:
        request: FastAPI request object
        question_data: Question submission request
        current_user: Authenticated user context
        service: Question intake service
    
    Returns:
        QuestionSubmissionResponse: Question ID, session ID, turn ID, and status
    """
    # Check for idempotency key
    idempotency_key = request.headers.get("idempotency-key")
    user_uuid = UUID(current_user.user_id)
    if idempotency_key:
        # Check if we've already processed this request
        cached_response = await service.check_idempotency_key(
            idempotency_key, user_uuid
        )
        if cached_response:
            return cached_response
    
    # Process the question
    result = await service.submit_question(
        question_text=question_data.question_text,
        session_id=question_data.session_id,
        user_id=user_uuid,
        access_scope=current_user.access_scope,
    )
    
    # Store idempotency key if provided
    if idempotency_key:
        await service.store_idempotency_key(
            idempotency_key, user_uuid, result
        )
    
    return result


@router.get("/questions/{question_id}", response_model=QuestionStatusResponse)
async def get_question_status(
    question_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    service: QuestionIntakeService = Depends(get_question_intake_service),
):
    """
    Get the status of a submitted question.
    
    User must own the question (via session ownership).
    
    Args:
        question_id: UUID of the question turn
        current_user: Authenticated user context
        service: Question intake service
    
    Returns:
        QuestionStatusResponse: Current processing status and answer if available
    
    Raises:
        HTTPException: 404 if question not found or user doesn't own it
    """
    status_result = await service.get_question_status(
        question_id=question_id,
        user_id=UUID(current_user.user_id),
    )
    
    if not status_result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Question not found or access denied",
        )
    
    return status_result
