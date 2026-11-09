"""User Service client with circuit breaker pattern."""

import time
from typing import Optional

import httpx

from app.config import settings
from app.schemas.auth import UserProfile


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


class UserServiceClient:
    """Client for User Service integration with circuit breaker."""

    def __init__(self):
        self.base_url = settings.user_service_url
        self.circuit_breaker = CircuitBreaker(failure_threshold=5, recovery_timeout=30)
        self.timeout = 1.0  # 1 second timeout

    def get_user_profile(self, user_id: str) -> UserProfile:
        """
        Retrieve user profile from User Service.

        Args:
            user_id: User identifier

        Returns:
            UserProfile with roles, teams, and access policies

        Raises:
            CircuitBreakerOpen: When circuit breaker is open
            httpx.HTTPError: On API communication failure
        """

        def _get_profile():
            with httpx.Client(timeout=self.timeout) as client:
                response = client.get(
                    f"{self.base_url}/api/v1/users/{user_id}",
                    headers={"Content-Type": "application/json"},
                )
                response.raise_for_status()
                data = response.json()

                return UserProfile(
                    user_id=data.get("user_id", user_id),
                    email=data.get("email", ""),
                    display_name=data.get("display_name", ""),
                    roles=data.get("roles", []),
                    team_memberships=data.get("team_memberships", []),
                    access_policies=data.get("access_policies", []),
                )

        return self.circuit_breaker.call(_get_profile)


# Global client instance
user_service_client = UserServiceClient()
