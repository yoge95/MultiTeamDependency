"""Auth API client with circuit breaker pattern."""

import time
from datetime import datetime
from typing import Optional

import httpx

from app.config import settings
from app.schemas.auth import TokenValidationResponse


class CircuitBreakerOpen(Exception):
    """Exception raised when circuit breaker is open."""

    pass


class CircuitBreaker:
    """Circuit breaker implementation for external service calls."""

    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 30):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time: Optional[float] = None
        self.state = "closed"  # closed, open, half_open

    def call(self, func, *args, **kwargs):
        """Execute function with circuit breaker protection."""
        if self.state == "open":
            if time.time() - self.last_failure_time >= self.recovery_timeout:
                self.state = "half_open"
            else:
                raise CircuitBreakerOpen("Circuit breaker is open")

        try:
            result = func(*args, **kwargs)
            if self.state == "half_open":
                self.reset()
            return result
        except Exception as e:
            self.record_failure()
            raise e

    def record_failure(self):
        """Record a failure and potentially open the circuit."""
        self.failure_count += 1
        self.last_failure_time = time.time()
        if self.failure_count >= self.failure_threshold:
            self.state = "open"

    def reset(self):
        """Reset the circuit breaker to closed state."""
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "closed"


class AuthAPIClient:
    """Client for Auth API integration with circuit breaker."""

    def __init__(self):
        self.base_url = settings.auth_api_url
        self.circuit_breaker = CircuitBreaker(failure_threshold=5, recovery_timeout=30)
        self.timeout = 0.5  # 500ms timeout

    def validate_token(self, token: str) -> TokenValidationResponse:
        """
        Validate OAuth 2.1 bearer token via Auth API.

        Args:
            token: Bearer token to validate

        Returns:
            TokenValidationResponse with user identity

        Raises:
            CircuitBreakerOpen: When circuit breaker is open
            httpx.HTTPError: On API communication failure
        """

        def _validate():
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(
                    f"{self.base_url}/oauth/introspect",
                    json={"token": token},
                    headers={"Content-Type": "application/json"},
                )
                response.raise_for_status()
                data = response.json()

                # Parse Auth API response
                return TokenValidationResponse(
                    valid=data.get("active", False),
                    user_id=data.get("sub", ""),
                    email=data.get("email", ""),
                    roles=data.get("roles", []),
                    expires_at=datetime.fromtimestamp(data["exp"]) if "exp" in data else None,
                )

        return self.circuit_breaker.call(_validate)


# Global client instance
auth_api_client = AuthAPIClient()
