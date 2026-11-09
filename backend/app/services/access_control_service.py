"""Access control service for filtering retrieved content by user's access scope."""

from typing import List
from uuid import UUID

from app.schemas.auth import AccessScope
from app.schemas.retrieval import RetrievedChunk


class AccessControlService:
    """Service for enforcing access-aware retrieval filtering."""

    def filter_chunks_by_access(self, chunks: List[RetrievedChunk], access_scope: AccessScope) -> List[RetrievedChunk]:
        """Filter chunks based on user's access scope.

        Enforces access control by:
        1. Checking domain accessibility (user must have access to chunk's domain)
        2. Checking access tag compatibility (chunk's tag must be within user's scope)
        3. Applying source-scope filter rules from user's access policies

        Args:
            chunks: List of retrieved chunks to filter
            access_scope: User's effective access scope

        Returns:
            List of chunks the user is authorized to access
        """
        filtered_chunks = []

        for chunk in chunks:
            if self._is_chunk_accessible(chunk, access_scope):
                filtered_chunks.append(chunk)

        return filtered_chunks

    def _is_chunk_accessible(self, chunk: RetrievedChunk, access_scope: AccessScope) -> bool:
        """Check if a single chunk is accessible to the user.

        Args:
            chunk: Chunk to check
            access_scope: User's access scope

        Returns:
            True if user can access this chunk
        """
        # Check domain accessibility
        if access_scope.accessible_domains and chunk.domain_id not in access_scope.accessible_domains:
            return False

        # Check access tag compatibility
        # Map access tags to authorization levels
        access_level_hierarchy = {
            "public": 0,
            "internal": 1,
            "confidential": 2,
            "restricted": 3,
        }

        chunk_level = access_level_hierarchy.get(chunk.access_scope_tag, 3)

        # Determine user's maximum access level from roles
        user_max_level = 1  # Default: internal

        if "platform_administrator" in access_scope.roles or "governance_reviewer" in access_scope.roles:
            user_max_level = 3  # Can access restricted
        elif "knowledge_steward" in access_scope.roles:
            user_max_level = 2  # Can access confidential

        # User can access chunks at or below their access level
        if chunk_level > user_max_level:
            return False

        # Apply source-scope filter rules
        source_scope_filter = access_scope.source_scope_filter or {}

        # Check if there are explicit source restrictions
        if "excluded_sources" in source_scope_filter:
            excluded = source_scope_filter["excluded_sources"]
            if str(chunk.source_record_id) in excluded:
                return False

        # Check if there's an allowed sources whitelist
        if "allowed_sources" in source_scope_filter:
            allowed = source_scope_filter["allowed_sources"]
            if allowed and str(chunk.source_record_id) not in allowed:
                return False

        return True

    def get_accessible_domains(self, access_scope: AccessScope, all_domain_ids: List[UUID]) -> List[UUID]:
        """Get list of domains the user can access.

        Args:
            access_scope: User's access scope
            all_domain_ids: All available domain IDs

        Returns:
            List of accessible domain IDs
        """
        # If accessible_domains is empty or None, user has access to all domains
        if not access_scope.accessible_domains:
            return all_domain_ids

        return [d for d in all_domain_ids if d in access_scope.accessible_domains]

    def can_access_source(self, source_record_id: UUID, access_scope: AccessScope) -> bool:
        """Check if user can access a specific source.

        Args:
            source_record_id: Source record UUID
            access_scope: User's access scope

        Returns:
            True if user can access this source
        """
        source_scope_filter = access_scope.source_scope_filter or {}

        # Check exclusions
        if "excluded_sources" in source_scope_filter:
            if str(source_record_id) in source_scope_filter["excluded_sources"]:
                return False

        # Check whitelist
        if "allowed_sources" in source_scope_filter:
            allowed = source_scope_filter["allowed_sources"]
            if allowed and str(source_record_id) not in allowed:
                return False

        return True
