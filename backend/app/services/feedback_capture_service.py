"""Feedback capture service for collecting user feedback."""

from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy.orm import Session

from app.models.interaction import AnswerRecord, FeedbackRecord
from app.schemas.auth import CurrentUser
from app.schemas.feedback import FeedbackSubmissionRequest


class FeedbackCaptureService:
    """Service for capturing and managing user feedback."""

    def __init__(self, db: Session):
        """Initialize feedback capture service.

        Args:
            db: Database session
        """
        self.db = db

    async def submit_feedback(
        self,
        request: FeedbackSubmissionRequest,
        current_user: CurrentUser
    ) -> FeedbackRecord:
        """Submit feedback for an answer.

        Args:
            request: Feedback submission request
            current_user: Authenticated user

        Returns:
            Created feedback record

        Raises:
            ValueError: If answer does not belong to user or validation fails
        """
        # Verify answer belongs to authenticated user
        answer = self.db.query(AnswerRecord).filter(
            AnswerRecord.answer_id == request.answer_id
        ).first()

        if not answer:
            raise ValueError("Answer not found")

        # Get session to verify ownership
        from app.models.interaction import QuestionSession
        session = self.db.query(QuestionSession).filter(
            QuestionSession.session_id == answer.session_id
        ).first()

        if not session:
            raise ValueError("Session not found")

        # Verify user owns the session
        if str(session.requesting_stakeholder_id) != current_user.user_id:
            raise ValueError("Answer does not belong to authenticated user")

        # Determine if steward action is required
        steward_action_required = request.feedback_type in {
            "incomplete", "stale", "unclear", "incorrect"
        }

        # Create feedback record
        feedback = FeedbackRecord(
            feedback_id=uuid4(),
            answer_id=request.answer_id,
            stakeholder_id=UUID(current_user.user_id),
            feedback_type=request.feedback_type,
            feedback_comment=request.feedback_text,
            steward_action_required=steward_action_required,
            created_at=datetime.utcnow()
        )

        self.db.add(feedback)
        self.db.commit()
        self.db.refresh(feedback)

        return feedback

    async def get_pending_feedback(
        self,
        domain_id: Optional[UUID] = None,
        page: int = 1,
        page_size: int = 20
    ) -> tuple[list[FeedbackRecord], int]:
        """Get pending feedback for steward review.

        Args:
            domain_id: Optional domain filter
            page: Page number
            page_size: Items per page

        Returns:
            Tuple of (feedback list, total count)
        """
        query = self.db.query(FeedbackRecord).filter(
            FeedbackRecord.steward_action_required
        )

        if domain_id:
            # Join with answer and filter by domain
            query = query.join(AnswerRecord).filter(
                AnswerRecord.primary_domain_id == domain_id
            )

        # Get total count
        total = query.count()

        # Apply pagination
        offset = (page - 1) * page_size
        feedback_list = query.order_by(
            FeedbackRecord.created_at.desc()
        ).offset(offset).limit(page_size).all()

        return feedback_list, total
