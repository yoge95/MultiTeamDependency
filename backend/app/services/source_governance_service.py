"""Source governance service for steward workflows."""

from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy.orm import Session

from app.models.knowledge import KnowledgeDomain, SourceRecord, SourceReview
from app.schemas.auth import CurrentUser
from app.schemas.governance import FreshnessExceptionRequest, SourceApprovalRequest, SourceRegistrationRequest


class SourceGovernanceService:
    """Service for source governance workflows."""

    def __init__(self, db: Session):
        """Initialize source governance service.

        Args:
            db: Database session
        """
        self.db = db

    async def list_sources(
        self,
        current_user: CurrentUser,
        domain_id: Optional[UUID] = None,
        page: int = 1,
        page_size: int = 20
    ) -> tuple[list[SourceRecord], int]:
        """List sources filtered by user's steward domains.

        Args:
            current_user: Authenticated user
            domain_id: Optional domain filter
            page: Page number
            page_size: Items per page

        Returns:
            Tuple of (source list, total count)
        """
        query = self.db.query(SourceRecord)

        # If user is knowledge_steward, filter by accessible domains
        if "knowledge_steward" in current_user.roles:
            accessible_domains = current_user.access_scope.accessible_domains or []
            if accessible_domains:
                query = query.filter(SourceRecord.domain_id.in_(accessible_domains))

        # Apply domain filter if provided
        if domain_id:
            query = query.filter(SourceRecord.domain_id == domain_id)

        # Get total count
        total = query.count()

        # Apply pagination
        offset = (page - 1) * page_size
        sources = query.order_by(
            SourceRecord.created_at.desc()
        ).offset(offset).limit(page_size).all()

        return sources, total

    async def register_source(
        self,
        request: SourceRegistrationRequest,
        current_user: CurrentUser
    ) -> SourceRecord:
        """Register a new source for governance.

        Args:
            request: Source registration request
            current_user: Authenticated user

        Returns:
            Created source record

        Raises:
            ValueError: If source_key already exists or validation fails
        """
        # Check if source_key already exists
        existing = self.db.query(SourceRecord).filter(
            SourceRecord.source_key == request.source_key
        ).first()

        if existing:
            raise ValueError(f"Source with key '{request.source_key}' already exists")

        # Verify domain exists
        domain = self.db.query(KnowledgeDomain).filter(
            KnowledgeDomain.domain_id == request.domain_id
        ).first()

        if not domain:
            raise ValueError("Domain not found")

        # Create source record
        source = SourceRecord(
            source_record_id=uuid4(),
            source_key=request.source_key,
            title=request.title,
            source_type=request.source_type,
            domain_id=request.domain_id,
            owner_team_id=request.owner_team_id,
            steward_team_id=request.steward_team_id,
            approval_state="pending",
            sensitivity_classification=request.sensitivity_classification,
            next_review_due_on=None,
            retention_days=365,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        self.db.add(source)
        self.db.commit()
        self.db.refresh(source)

        return source

    async def approve_source(
        self,
        source_id: UUID,
        request: SourceApprovalRequest,
        current_user: CurrentUser
    ) -> SourceReview:
        """Approve or review a source.

        Args:
            source_id: Source record ID
            request: Approval request
            current_user: Authenticated user (must be steward)

        Returns:
            Created source review record

        Raises:
            ValueError: If source not found or user not authorized
        """
        # Get source
        source = self.db.query(SourceRecord).filter(
            SourceRecord.source_record_id == source_id
        ).first()

        if not source:
            raise ValueError("Source not found")

        # Verify user is steward for this domain
        if "knowledge_steward" in current_user.roles:
            accessible_domains = current_user.access_scope.accessible_domains or []
            if source.domain_id not in accessible_domains:
                raise ValueError("User is not steward for this source's domain")

        # Create review record
        review = SourceReview(
            review_id=uuid4(),
            source_record_id=source_id,
            reviewer_stakeholder_id=UUID(current_user.user_id),
            review_decision=request.review_decision,
            freshness_exception_granted=False,
            next_review_due_on=request.next_review_due_on,
            review_notes=request.review_notes,
            reviewed_at=datetime.utcnow(),
            created_at=datetime.utcnow()
        )

        # Update source approval state
        if request.review_decision in {"approved", "rejected", "archived"}:
            source.approval_state = request.review_decision

        # Update next review date
        if request.next_review_due_on:
            source.next_review_due_on = request.next_review_due_on

        source.updated_at = datetime.utcnow()

        self.db.add(review)
        self.db.commit()
        self.db.refresh(review)

        return review

    async def grant_freshness_exception(
        self,
        source_id: UUID,
        request: FreshnessExceptionRequest,
        current_user: CurrentUser
    ) -> SourceReview:
        """Grant freshness exception for a source.

        Args:
            source_id: Source record ID
            request: Exception request
            current_user: Authenticated user (must be steward)

        Returns:
            Created source review record with exception

        Raises:
            ValueError: If source not found or user not authorized
        """
        # Get source
        source = self.db.query(SourceRecord).filter(
            SourceRecord.source_record_id == source_id
        ).first()

        if not source:
            raise ValueError("Source not found")

        # Verify user is steward for this domain
        if "knowledge_steward" in current_user.roles:
            accessible_domains = current_user.access_scope.accessible_domains or []
            if source.domain_id not in accessible_domains:
                raise ValueError("User is not steward for this source's domain")

        # Create review record with exception
        review = SourceReview(
            review_id=uuid4(),
            source_record_id=source_id,
            reviewer_stakeholder_id=UUID(current_user.user_id),
            review_decision="exception_granted",
            freshness_exception_granted=True,
            next_review_due_on=request.exception_until,
            review_notes=request.reason,
            reviewed_at=datetime.utcnow(),
            created_at=datetime.utcnow()
        )

        # Update source next review date
        source.next_review_due_on = request.exception_until
        source.updated_at = datetime.utcnow()

        self.db.add(review)
        self.db.commit()
        self.db.refresh(review)

        return review
