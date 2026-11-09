"""Session context service for managing conversation sessions."""

from typing import Optional
from uuid import UUID, uuid4
from datetime import datetime

from sqlalchemy.orm import Session

from app.models.interaction import QuestionSession
from app.schemas.auth import AccessScope


class SessionContextService:
    """Service for managing question sessions and context."""
    
    def __init__(self, db: Session):
        """Initialize session context service."""
        self.db = db
    
    def create_session(
        self,
        user_id: UUID,
        access_scope: AccessScope,
    ) -> QuestionSession:
        """
        Create a new question session.
        
        Args:
            user_id: UUID of the authenticated user
            access_scope: User's access scope
        
        Returns:
            QuestionSession: Created session
        """
        # Determine initial domain context from access scope
        primary_domain_id = None
        if access_scope.accessible_domains:
            primary_domain_id = access_scope.accessible_domains[0]  # Use first accessible domain
        
        session = QuestionSession(
            session_id=uuid4(),
            requesting_stakeholder_id=user_id,
            persona_type="engineer",  # Default persona
            primary_domain_id=primary_domain_id,
            session_status="active",
            created_at=datetime.utcnow(),
            last_activity_at=datetime.utcnow(),
        )
        
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        
        return session
    
    def get_session(
        self,
        session_id: UUID,
        user_id: UUID,
    ) -> Optional[QuestionSession]:
        """
        Get an existing session if it belongs to the user.
        
        Args:
            session_id: UUID of the session
            user_id: UUID of the requesting user
        
        Returns:
            QuestionSession if found and owned by user, None otherwise
        """
        session = (
            self.db.query(QuestionSession)
            .filter(
                QuestionSession.session_id == session_id,
                QuestionSession.requesting_stakeholder_id == user_id,
                QuestionSession.session_status == "active",
            )
            .first()
        )
        
        return session
    
    def update_session_activity(
        self,
        session_id: UUID,
    ) -> None:
        """
        Update session last activity timestamp.
        
        Args:
            session_id: UUID of the session
        """
        session = (
            self.db.query(QuestionSession)
            .filter(QuestionSession.session_id == session_id)
            .first()
        )
        
        if session:
            session.last_activity_at = datetime.utcnow()
            self.db.commit()
