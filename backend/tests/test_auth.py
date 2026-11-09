"""Tests for authentication and authorization."""

from datetime import datetime, timedelta
from unittest.mock import MagicMock, Mock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from app.auth import get_current_user, require_auth, require_role
from app.integrations.auth_api_client import CircuitBreakerOpen
from app.schemas.auth import AccessScope, CurrentUser, TokenValidationResponse, UserProfile


class TestGetCurrentUser:
    """Tests for get_current_user dependency."""

    @pytest.mark.asyncio
    @patch("app.auth.get_redis_client")
    @patch("app.auth.auth_api_client")
    @patch("app.auth.user_service_client")
    async def test_valid_token_with_profile(self, mock_user_service, mock_auth_api, mock_redis):
        """Test successful authentication with user profile."""
        # Setup mocks
        mock_redis_instance = MagicMock()
        mock_redis_instance.get.return_value = None
        mock_redis.return_value = mock_redis_instance

        mock_auth_api.validate_token.return_value = TokenValidationResponse(
            valid=True,
            user_id="user-123",
            email="test@example.com",
            roles=["end_user"],
            expires_at=datetime.utcnow() + timedelta(hours=1),
        )

        team_id = uuid4()
        mock_user_service.get_user_profile.return_value = UserProfile(
            user_id="user-123",
            email="test@example.com",
            display_name="Test User",
            roles=["end_user", "knowledge_steward"],
            team_memberships=[team_id],
            access_policies=[],
        )

        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="valid-token")

        # Execute
        result = await get_current_user(credentials)

        # Verify
        assert result.user_id == "user-123"
        assert result.email == "test@example.com"
        assert "end_user" in result.roles
        assert "knowledge_steward" in result.roles
        assert result.access_scope.user_id == "user-123"
        assert team_id in result.access_scope.team_memberships

    @pytest.mark.asyncio
    @patch("app.auth.get_redis_client")
    @patch("app.auth.auth_api_client")
    async def test_invalid_token(self, mock_auth_api, mock_redis):
        """Test authentication failure with invalid token."""
        mock_redis_instance = MagicMock()
        mock_redis_instance.get.return_value = None
        mock_redis.return_value = mock_redis_instance

        mock_auth_api.validate_token.return_value = TokenValidationResponse(
            valid=False,
            user_id="",
            email="",
            roles=[],
        )

        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="invalid-token")

        # Execute and verify exception
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(credentials)

        assert exc_info.value.status_code == 401
        assert "Invalid or expired token" in exc_info.value.detail

    @pytest.mark.asyncio
    @patch("app.auth.get_redis_client")
    @patch("app.auth.auth_api_client")
    @patch("app.auth.user_service_client")
    async def test_degraded_mode_without_user_service(self, mock_user_service, mock_auth_api, mock_redis):
        """Test graceful degradation when User Service is unavailable."""
        mock_redis_instance = MagicMock()
        mock_redis_instance.get.return_value = None
        mock_redis.return_value = mock_redis_instance

        mock_auth_api.validate_token.return_value = TokenValidationResponse(
            valid=True,
            user_id="user-456",
            email="user@example.com",
            roles=["end_user"],
            expires_at=datetime.utcnow() + timedelta(hours=1),
        )

        mock_user_service.get_user_profile.side_effect = CircuitBreakerOpen("Circuit breaker open")

        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="valid-token")

        # Execute
        result = await get_current_user(credentials)

        # Verify degraded mode - minimal scope from token
        assert result.user_id == "user-456"
        assert result.email == "user@example.com"
        assert result.roles == ["end_user"]
        assert result.access_scope.team_memberships == []

    @pytest.mark.asyncio
    @patch("app.auth.get_redis_client")
    @patch("app.auth.auth_api_client")
    async def test_circuit_breaker_open_with_cache_fallback(self, mock_auth_api, mock_redis):
        """Test fallback to cache when Auth API circuit breaker is open."""
        import json

        cached_data = {
            "user_id": "user-789",
            "email": "cached@example.com",
            "roles": ["end_user"],
            "access_scope": {
                "user_id": "user-789",
                "roles": ["end_user"],
                "team_memberships": [],
                "accessible_domains": [],
                "source_scope_filter": {},
            },
        }

        mock_redis_instance = MagicMock()
        mock_redis_instance.get.return_value = json.dumps(cached_data)
        mock_redis.return_value = mock_redis_instance

        mock_auth_api.validate_token.side_effect = CircuitBreakerOpen("Circuit breaker open")

        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="valid-token")

        # Execute
        result = await get_current_user(credentials)

        # Verify cache fallback
        assert result.user_id == "user-789"
        assert result.email == "cached@example.com"

    @pytest.mark.asyncio
    @patch("app.auth.get_redis_client")
    @patch("app.auth.auth_api_client")
    async def test_circuit_breaker_open_without_cache(self, mock_auth_api, mock_redis):
        """Test service unavailable when circuit breaker open and no cache."""
        mock_redis_instance = MagicMock()
        mock_redis_instance.get.return_value = None
        mock_redis.return_value = mock_redis_instance

        mock_auth_api.validate_token.side_effect = CircuitBreakerOpen("Circuit breaker open")

        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="valid-token")

        # Execute and verify exception
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(credentials)

        assert exc_info.value.status_code == 503
        assert "temporarily unavailable" in exc_info.value.detail


class TestRequireAuth:
    """Tests for require_auth dependency."""

    @pytest.mark.asyncio
    async def test_require_auth_with_valid_user(self):
        """Test require_auth passes through authenticated user."""
        current_user = CurrentUser(
            user_id="user-123",
            email="test@example.com",
            roles=["end_user"],
            access_scope=AccessScope(
                user_id="user-123",
                roles=["end_user"],
                team_memberships=[],
                accessible_domains=[],
                source_scope_filter={},
            ),
        )

        result = await require_auth(current_user)
        assert result.user_id == "user-123"


class TestRequireRole:
    """Tests for require_role factory."""

    @pytest.mark.asyncio
    async def test_require_role_with_matching_role(self):
        """Test authorization success when user has required role."""
        current_user = CurrentUser(
            user_id="user-123",
            email="steward@example.com",
            roles=["end_user", "knowledge_steward"],
            access_scope=AccessScope(
                user_id="user-123",
                roles=["end_user", "knowledge_steward"],
                team_memberships=[],
                accessible_domains=[],
                source_scope_filter={},
            ),
        )

        role_checker = require_role("knowledge_steward")
        result = await role_checker(current_user)
        assert result.user_id == "user-123"

    @pytest.mark.asyncio
    async def test_require_role_with_multiple_allowed_roles(self):
        """Test authorization success when user has one of multiple allowed roles."""
        current_user = CurrentUser(
            user_id="user-456",
            email="reviewer@example.com",
            roles=["governance_reviewer"],
            access_scope=AccessScope(
                user_id="user-456",
                roles=["governance_reviewer"],
                team_memberships=[],
                accessible_domains=[],
                source_scope_filter={},
            ),
        )

        role_checker = require_role("knowledge_steward", "governance_reviewer")
        result = await role_checker(current_user)
        assert result.user_id == "user-456"

    @pytest.mark.asyncio
    async def test_require_role_without_required_role(self):
        """Test authorization failure when user lacks required role."""
        current_user = CurrentUser(
            user_id="user-789",
            email="user@example.com",
            roles=["end_user"],
            access_scope=AccessScope(
                user_id="user-789",
                roles=["end_user"],
                team_memberships=[],
                accessible_domains=[],
                source_scope_filter={},
            ),
        )

        role_checker = require_role("platform_administrator")

        with pytest.raises(HTTPException) as exc_info:
            await role_checker(current_user)

        assert exc_info.value.status_code == 403
        assert "Insufficient permissions" in exc_info.value.detail
        assert "platform_administrator" in exc_info.value.detail


class TestCircuitBreaker:
    """Tests for circuit breaker functionality."""

    def test_circuit_breaker_opens_after_threshold(self):
        """Test circuit breaker opens after failure threshold."""
        from app.integrations.auth_api_client import CircuitBreaker

        breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=30)

        # Simulate failures
        for _ in range(3):
            try:
                breaker.call(lambda: (_ for _ in ()).throw(Exception("Test failure")))
            except Exception:
                pass

        # Circuit should be open
        assert breaker.state == "open"

        # Next call should raise CircuitBreakerOpen
        with pytest.raises(CircuitBreakerOpen):
            breaker.call(lambda: "success")

    def test_circuit_breaker_half_open_after_timeout(self):
        """Test circuit breaker transitions to half-open after recovery timeout."""
        from app.integrations.auth_api_client import CircuitBreaker
        import time

        breaker = CircuitBreaker(failure_threshold=2, recovery_timeout=1)

        # Open the circuit
        for _ in range(2):
            try:
                breaker.call(lambda: (_ for _ in ()).throw(Exception("Test failure")))
            except Exception:
                pass

        assert breaker.state == "open"

        # Wait for recovery timeout
        time.sleep(1.1)

        # Next call should transition to half-open
        try:
            breaker.call(lambda: "success")
        except CircuitBreakerOpen:
            # This shouldn't happen after timeout
            pytest.fail("Circuit breaker should transition to half-open")

        # Circuit should be closed after successful call
        assert breaker.state == "closed"
