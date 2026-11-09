"""Feedback API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth import require_auth
from app.database import get_db
from app.schemas.auth import CurrentUser
from app.schemas.feedback import FeedbackSubmissionRequest, FeedbackSubmissionResponse
from app.services.feedback_capture_service import FeedbackCaptureService

router = APIRouter(prefix="/feedback", tags=["feedback"])


@router.post("/", response_model=FeedbackSubmissionResponse, status_code=status.HTTP_201_CREATED)
async def submit_feedback(
    request: FeedbackSubmissionRequest,
    current_user: CurrentUser = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Submit feedback for an answer.

    Args:
        request: Feedback submission request
        current_user: Authenticated user
        db: Database session

    Returns:
        Feedback submission response

    Raises:
        HTTPException: 404 if answer not found, 403 if not authorized, 400 if validation fails
    """
    service = FeedbackCaptureService(db)

    try:
        feedback = await service.submit_feedback(request, current_user)

        return FeedbackSubmissionResponse(
            feedback_id=feedback.feedback_id,
            answer_id=feedback.answer_id,
            feedback_type=feedback.feedback_type,
            triage_status="pending",
            created_at=feedback.created_at,
            message="Thank you for your feedback!"
        )

    except ValueError as e:
        error_msg = str(e)
        if "not found" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_msg
            )
        elif "does not belong" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only provide feedback on your own answers"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg
            )
