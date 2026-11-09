"""Escalation routing service providing next-step guidance."""

from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.integrations.neo4j_client import Neo4jClient
from app.models.governance import EscalationRoute as EscalationRouteModel
from app.models.org import Stakeholder, Team
from app.schemas.answers import EscalationContact


class EscalationRoutingService:
    """Service for identifying escalation routes when confidence is low."""

    def __init__(self, db: Session, neo4j_client: Neo4jClient):
        self.db = db
        self.neo4j_client = neo4j_client

    def get_escalation_contacts(
        self,
        intent_classification: dict,
        domain_id: Optional[UUID] = None,
        limitation_type: Optional[str] = None
    ) -> List[EscalationContact]:
        """
        Identify next-step contacts via Neo4j traversal.

        Args:
            intent_classification: Intent classification from question
            domain_id: Knowledge domain ID if available
            limitation_type: Type of limitation encountered

        Returns:
            List of escalation contacts with contact information
        """
        contacts = []

        primary_intent = intent_classification.get('primary_intent', '')

        if primary_intent == 'ownership' and domain_id:
            contacts.extend(self._get_domain_stewards(domain_id))

        if primary_intent == 'routing' or limitation_type == 'missing_knowledge':
            contacts.extend(self._get_platform_admins())

        if limitation_type == 'restricted_access' and domain_id:
            contacts.extend(self._get_domain_stewards(domain_id))

        if not contacts:
            contacts.extend(self._get_fallback_contacts())

        return contacts[:5]

    def _get_domain_stewards(self, domain_id: UUID) -> List[EscalationContact]:
        """Get steward contacts for a knowledge domain."""
        try:
            from app.models.knowledge import KnowledgeDomain
            domain = self.db.execute(
                select(KnowledgeDomain).where(
                    KnowledgeDomain.domain_id == domain_id
                )
            ).scalar_one_or_none()

            if not domain or not domain.steward_team_id:
                return []

            team = self.db.execute(
                select(Team).where(
                    Team.team_id == domain.steward_team_id
                )
            ).scalar_one_or_none()

            if not team:
                return []

            contacts = []
            if team.primary_contact_email:
                contacts.append(EscalationContact(
                    contact_type="team",
                    contact_name=team.team_name,
                    contact_method="email",
                    contact_address=team.primary_contact_email
                ))

            if team.slack_channel_id:
                contacts.append(EscalationContact(
                    contact_type="team",
                    contact_name=team.team_name,
                    contact_method="slack",
                    contact_address=team.slack_channel_id
                ))

            return contacts
        except Exception:
            return []

    def _get_platform_admins(self) -> List[EscalationContact]:
        """Get platform administrator contacts."""
        try:
            from app.models.org import TeamMembership
            admin_memberships = self.db.execute(
                select(TeamMembership, Stakeholder).join(
                    Stakeholder,
                    Stakeholder.stakeholder_id == TeamMembership.stakeholder_id
                ).where(
                    TeamMembership.role_code == 'platform_administrator'
                ).limit(3)
            ).all()

            contacts = []
            for membership, stakeholder in admin_memberships:
                if stakeholder.email:
                    contacts.append(EscalationContact(
                        contact_type="stakeholder",
                        contact_name=stakeholder.display_name,
                        contact_method="email",
                        contact_address=stakeholder.email
                    ))

            return contacts
        except Exception:
            return []

    def _get_fallback_contacts(self) -> List[EscalationContact]:
        """Get fallback contacts when no specific route is found."""
        return [
            EscalationContact(
                contact_type="team",
                contact_name="Platform Support",
                contact_method="email",
                contact_address="platform-support@example.com"
            )
        ]

    def get_escalation_route_by_id(self, route_id: UUID) -> Optional[dict]:
        """
        Retrieve predefined escalation route by ID.

        Args:
            route_id: Escalation route ID

        Returns:
            Route details dictionary or None
        """
        try:
            route = self.db.execute(
                select(EscalationRouteModel).where(
                    EscalationRouteModel.route_id == route_id
                )
            ).scalar_one_or_none()

            if not route:
                return None

            return {
                'route_id': str(route.route_id),
                'route_name': route.route_name,
                'steps': route.route_steps or []
            }
        except Exception:
            return None
