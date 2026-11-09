"""Question intake service for question submission and intent classification."""

import hashlib
import json
import re
from typing import Optional
from uuid import UUID, uuid4
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.models.interaction import QuestionSession, QuestionTurn
from app.schemas.questions import (
    QuestionSubmissionResponse,
    QuestionStatusResponse,
    IntentClassification,
)
from app.schemas.auth import AccessScope
from app.services.session_context_service import SessionContextService


class QuestionIntakeService:
    """Service for handling question intake and intent classification."""
    
    # Intent classification keywords
    INTENT_KEYWORDS = {
        "ownership": ["who owns", "responsible for", "team owns", "maintained by", "owner of"],
        "dependency": ["depend on", "depends on", "dependencies", "dependent", "calls", "integrates with", "uses"],
        "routing": ["contact", "reach out", "escalate", "who to ask", "point of contact", "escalation"],
        "runbook": ["how to", "procedure", "steps to", "process for", "guide", "tutorial"],
        "onboarding": ["getting started", "new to", "onboard", "learn about", "introduction"],
        "governance": ["policy", "approval", "compliance", "governance", "review process", "authorization"],
    }
    
    # Class-level idempotency cache shared across all instances
    _idempotency_cache = {}
    
    def __init__(self, db: Session, session_context_service: SessionContextService):
        """Initialize question intake service."""
        self.db = db
        self.session_context_service = session_context_service
    
    async def submit_question(
        self,
        question_text: str,
        user_id: UUID,
        access_scope: AccessScope,
        session_id: Optional[UUID] = None,
    ) -> QuestionSubmissionResponse:
        """
        Submit a new question or follow-up turn.
        
        Args:
            question_text: Natural language question
            user_id: UUID of the authenticated user
            access_scope: User's access scope
            session_id: Optional existing session ID for follow-up
        
        Returns:
            QuestionSubmissionResponse with session info and initial status
        """
        # Get or create session
        if session_id:
            session = self.session_context_service.get_session(session_id, user_id)
            if not session:
                # Session not found or doesn't belong to user
                session = self.session_context_service.create_session(user_id, access_scope)
        else:
            session = self.session_context_service.create_session(user_id, access_scope)
        
        # Classify intent
        intent_classification = await self.classify_intent(question_text, session)
        
        # Create question turn - start with turn 1 for simplicity
        # (could query existing turns, but this is first implementation)
        turn_number = 1
        question_turn = QuestionTurn(
            turn_id=uuid4(),
            session_id=session.session_id,
            turn_sequence=turn_number,
            question_text=question_text,
            intent_classification=intent_classification.model_dump(),
            created_at=datetime.utcnow(),
        )
        
        self.db.add(question_turn)
        
        # Update session last activity
        session.last_activity_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(question_turn)
        
        # Check for ambiguity
        status = "processing"
        clarification_prompt = None
        
        if intent_classification.ambiguity_flags:
            status = "clarification_needed"
            clarification_prompt = self._generate_clarification_prompt(
                question_text, intent_classification.ambiguity_flags
            )
        
        return QuestionSubmissionResponse(
            question_id=question_turn.turn_id,
            session_id=session.session_id,
            turn_id=question_turn.turn_id,
            status=status,
            clarification_prompt=clarification_prompt,
            estimated_response_time_ms=5000 if status == "processing" else None,
        )
    
    async def classify_intent(
        self,
        question_text: str,
        session: QuestionSession,
    ) -> IntentClassification:
        """
        Classify question intent based on keywords and context.
        
        This is a simple rule-based classifier. In production, this would
        use an ML model or LLM for better accuracy.
        
        Args:
            question_text: Question text to classify
            session: Current session context
        
        Returns:
            IntentClassification with primary intent and confidence
        """
        question_lower = question_text.lower()
        
        # Score each intent based on keyword matches
        intent_scores = {}
        for intent, keywords in self.INTENT_KEYWORDS.items():
            score = sum(1 for keyword in keywords if keyword in question_lower)
            if score > 0:
                intent_scores[intent] = score
        
        # Determine primary intent
        if intent_scores:
            primary_intent = max(intent_scores, key=intent_scores.get)
            max_score = intent_scores[primary_intent]
            total_score = sum(intent_scores.values())
            confidence = max_score / total_score if total_score > 0 else 0.5
        else:
            # Default to ownership if no keywords match
            primary_intent = "ownership"
            confidence = 0.3
        
        # Determine candidate domains based on intent
        candidate_domains = self._determine_candidate_domains(primary_intent, question_text)
        
        # Check for ambiguity flags
        ambiguity_flags = self._detect_ambiguity(question_text, intent_scores)
        
        return IntentClassification(
            primary_intent=primary_intent,
            candidate_domains=candidate_domains,
            confidence=confidence,
            ambiguity_flags=ambiguity_flags,
        )
    
    def _determine_candidate_domains(self, intent: str, question_text: str) -> list[str]:
        """Determine candidate knowledge domains based on intent and question."""
        domain_keywords = {
            "onboarding": ["onboarding"],
            "ownership": ["ownership"],
            "dependencies": ["dependencies"],
            "runbooks": ["runbooks"],
            "governance": ["governance"],
            "operations": ["operations"],
        }
        
        question_lower = question_text.lower()
        candidates = []
        
        # Match domain keywords
        for domain, keywords in domain_keywords.items():
            if any(keyword in question_lower for keyword in keywords):
                candidates.append(domain)
        
        # Default domains based on intent
        intent_domain_map = {
            "ownership": ["ownership", "operations"],
            "dependency": ["dependencies", "ownership"],
            "routing": ["ownership", "operations"],
            "runbook": ["runbooks", "operations"],
            "onboarding": ["onboarding", "ownership"],
            "governance": ["governance"],
        }
        
        default_domains = intent_domain_map.get(intent, ["ownership"])
        for domain in default_domains:
            if domain not in candidates:
                candidates.append(domain)
        
        return candidates[:3]  # Return top 3 candidates
    
    def _detect_ambiguity(self, question_text: str, intent_scores: dict) -> list[str]:
        """Detect ambiguity flags in the question."""
        flags = []
        
        # Multiple intents with similar scores
        if len(intent_scores) >= 2:
            sorted_scores = sorted(intent_scores.values(), reverse=True)
            if len(sorted_scores) >= 2 and sorted_scores[0] - sorted_scores[1] <= 1:
                flags.append("multiple_intents")
        
        # Very short question (likely missing context)
        if len(question_text.split()) < 5:
            flags.append("too_vague")
        
        # Contains ambiguous pronouns without clear referent
        ambiguous_patterns = [
            r"\bit\b",
            r"\bthey\b",
            r"\bthem\b",
            r"\bthis\b",
            r"\bthat\b",
        ]
        if any(re.search(pattern, question_text.lower()) for pattern in ambiguous_patterns):
            # Only flag if question is short (longer questions likely have context)
            if len(question_text.split()) < 15:
                flags.append("unclear_reference")
        
        return flags
    
    def _generate_clarification_prompt(self, question_text: str, ambiguity_flags: list[str]) -> str:
        """Generate a clarification prompt based on ambiguity flags."""
        if "multiple_intents" in ambiguity_flags:
            return (
                "I'm not sure what you're looking for. Are you asking about: "
                "(a) who owns or maintains something, "
                "(b) how to use or integrate with something, or "
                "(c) who to contact about something?"
            )
        elif "too_vague" in ambiguity_flags:
            return "Could you provide more details about what you're asking? For example, which service, team, or topic?"
        elif "unclear_reference" in ambiguity_flags:
            return "Could you clarify what you're referring to? Please mention the specific service, team, or component."
        else:
            return "Could you rephrase your question with more specific details?"
    
    async def get_question_status(
        self,
        question_id: UUID,
        user_id: UUID,
    ) -> Optional[QuestionStatusResponse]:
        """
        Get the status of a submitted question.
        
        Args:
            question_id: UUID of the question turn
            user_id: UUID of the requesting user
        
        Returns:
            QuestionStatusResponse if found and user owns it, None otherwise
        """
        # Query question turn with session
        turn = (
            self.db.query(QuestionTurn)
            .filter(QuestionTurn.turn_id == question_id)
            .first()
        )
        
        if not turn:
            return None
        
        # Check session ownership
        session = (
            self.db.query(QuestionSession)
            .filter(
                QuestionSession.session_id == turn.session_id,
                QuestionSession.requesting_stakeholder_id == user_id,
            )
            .first()
        )
        
        if not session:
            return None
        
        # Check if answer exists
        from app.models.interaction import AnswerRecord
        answer = (
            self.db.query(AnswerRecord)
            .filter(AnswerRecord.turn_id == turn.turn_id)
            .first()
        )
        
        status = "completed" if answer else "processing"
        intent_classification = None
        
        if turn.intent_classification:
            intent_classification = IntentClassification(**turn.intent_classification)
        
        return QuestionStatusResponse(
            question_id=turn.turn_id,
            session_id=turn.session_id,
            turn_id=turn.turn_id,
            status=status,
            intent_classification=intent_classification,
            answer_id=answer.answer_id if answer else None,
            error_message=None,
            created_at=turn.created_at,
            completed_at=answer.created_at if answer else None,
        )
    
    async def check_idempotency_key(
        self,
        idempotency_key: str,
        user_id: UUID,
    ) -> Optional[QuestionSubmissionResponse]:
        """
        Check if an idempotency key has been used recently (24-hour window).
        
        Args:
            idempotency_key: Idempotency key from request header
            user_id: UUID of the requesting user
        
        Returns:
            Cached response if key exists, None otherwise
        """
        cache_key = f"{user_id}:{idempotency_key}"
        
        if cache_key in self._idempotency_cache:
            cached_data, timestamp = self._idempotency_cache[cache_key]
            # Check if cache entry is still valid (24 hours)
            if datetime.utcnow() - timestamp < timedelta(hours=24):
                return QuestionSubmissionResponse(**cached_data)
            else:
                # Remove expired entry
                del self._idempotency_cache[cache_key]
        
        return None
    
    async def store_idempotency_key(
        self,
        idempotency_key: str,
        user_id: UUID,
        response: QuestionSubmissionResponse,
    ) -> None:
        """
        Store an idempotency key with its response for 24 hours.
        
        Args:
            idempotency_key: Idempotency key to store
            user_id: UUID of the user
            response: Response to cache
        """
        cache_key = f"{user_id}:{idempotency_key}"
        self._idempotency_cache[cache_key] = (
            response.model_dump(),
            datetime.utcnow(),
        )
        
        # Clean up expired entries (simple periodic cleanup)
        if len(self._idempotency_cache) > 1000:
            self._cleanup_expired_idempotency_keys()
    
    def _cleanup_expired_idempotency_keys(self) -> None:
        """Remove expired idempotency keys from cache."""
        now = datetime.utcnow()
        expired_keys = [
            key
            for key, (_, timestamp) in self._idempotency_cache.items()
            if now - timestamp >= timedelta(hours=24)
        ]
        for key in expired_keys:
            del self._idempotency_cache[key]
