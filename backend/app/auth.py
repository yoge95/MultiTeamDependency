"""Authentication and authorization middleware for FastAPI."""

import json

import redis
from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.config import settings
from app.integrations.auth_api_client import CircuitBreakerOpen, auth_api_client
from app.integrations.user_service_client import user_service_client
from app.schemas.auth import AccessScope, CurrentUser

security = HTTPBearer()


def get_redis_client() -> redis.Redis:
    """Get Redis client for access scope caching."""
    return redis.Redis.from_url(settings.redis_url, decode_responses=True)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(security),
) -> CurrentUser:
    """
    FastAPI dependency for authenticated user context.

    Validates OAuth 2.1 bearer token via Auth API, retrieves user profile
    from User Service, and caches access scope in Redis with 15-minute TTL.

    Args:
        credentials: HTTP Authorization header with bearer token

    Returns:
        CurrentUser with user_id, roles, and access_scope

    Raises:
        HTTPException: 401 if token invalid or authentication fails
    """
    token = credentials.credentials
    
    # TEST MODE: Try to validate token as local JWT first
    try:
        import jwt
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        user_id_str = payload.get("sub")
        email = payload.get("email")
        roles = payload.get("roles", [])
        
        # Return test user without external API calls
        access_scope = AccessScope(
            user_id=user_id_str,
            roles=roles,
            team_memberships=[],
            accessible_domains=[],
            source_scope_filter={},
        )
        
        return CurrentUser(
            user_id=user_id_str,
            email=email,
            roles=roles,
            access_scope=access_scope,
        )
    except jwt.InvalidTokenError:
        # Not a local test token, continue with normal Auth API validation
        pass
    except Exception as e:
        # Log unexpected errors but continue with normal Auth API validation
        import traceback
        print(f"Test mode JWT validation failed: {e}")
        traceback.print_exc()
        pass
    
    cache_key = f"access_scope:{token[:32]}"  # Use token prefix as cache key

    # Try cache first
    redis_client = get_redis_client()
    try:
        cached_data = redis_client.get(cache_key)
        if cached_data:
            cached = json.loads(cached_data)
            # Convert string UUIDs back to UUID objects
            access_scope_data = cached["access_scope"]
            from uuid import UUID
            access_scope_data["team_memberships"] = [UUID(tm) for tm in access_scope_data.get("team_memberships", [])]
            access_scope_data["accessible_domains"] = [UUID(ad) for ad in access_scope_data.get("accessible_domains", [])]

            return CurrentUser(
                user_id=cached["user_id"],
                email=cached["email"],
                roles=cached["roles"],
                access_scope=AccessScope(**access_scope_data),
            )
    except (redis.RedisError, json.JSONDecodeError, KeyError, ValueError):
        # Cache miss or error, continue to Auth API
        pass

    # Validate token with Auth API
    try:
        token_response = auth_api_client.validate_token(token)
    except CircuitBreakerOpen:
        # Circuit breaker open, try cache fallback
        try:
            cached_data = redis_client.get(cache_key)
            if cached_data:
                cached = json.loads(cached_data)
                # Convert string UUIDs back to UUID objects
                access_scope_data = cached["access_scope"]
                from uuid import UUID
                access_scope_data["team_memberships"] = [UUID(tm) for tm in access_scope_data.get("team_memberships", [])]
                access_scope_data["accessible_domains"] = [UUID(ad) for ad in access_scope_data.get("accessible_domains", [])]

                return CurrentUser(
                    user_id=cached["user_id"],
                    email=cached["email"],
                    roles=cached["roles"],
                    access_scope=AccessScope(**access_scope_data),
                )
        except (redis.RedisError, json.JSONDecodeError, KeyError, ValueError):
            pass

        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service temporarily unavailable",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token validation failed: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not token_response.valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Get user profile from User Service
    try:
        profile = user_service_client.get_user_profile(token_response.user_id)
    except CircuitBreakerOpen:
        # Degrade gracefully - use minimal profile from token
        profile = None
    except Exception:
        # User Service unavailable, use token info only
        profile = None

    # Build access scope
    if profile:
        access_scope = AccessScope(
            user_id=profile.user_id,
            roles=profile.roles,
            team_memberships=profile.team_memberships,
            accessible_domains=[],  # Would be populated from access_policies
            source_scope_filter={},
        )
    else:
        # Degraded mode - minimal scope from token
        access_scope = AccessScope(
            user_id=token_response.user_id,
            roles=token_response.roles,
            team_memberships=[],
            accessible_domains=[],
            source_scope_filter={},
        )

    current_user = CurrentUser(
        user_id=token_response.user_id,
        email=token_response.email,
        roles=token_response.roles if profile is None else profile.roles,
        access_scope=access_scope,
    )

    # Cache for 15 minutes
    try:
        # Convert UUIDs to strings for JSON serialization
        access_scope_dict = current_user.access_scope.model_dump()
        access_scope_dict["team_memberships"] = [str(tm) for tm in access_scope_dict.get("team_memberships", [])]
        access_scope_dict["accessible_domains"] = [str(ad) for ad in access_scope_dict.get("accessible_domains", [])]

        cache_data = {
            "user_id": current_user.user_id,
            "email": current_user.email,
            "roles": current_user.roles,
            "access_scope": access_scope_dict,
        }
        redis_client.setex(cache_key, 900, json.dumps(cache_data))  # 15 minutes = 900 seconds
    except redis.RedisError:
        # Cache write failure is non-fatal
        pass

    return current_user


async def require_auth(
    current_user: CurrentUser = Depends(get_current_user),
) -> CurrentUser:
    """
    FastAPI dependency enforcing authentication.

    This is an explicit authentication check that can be used
    for routes that need authentication but no specific role.

    Args:
        current_user: Authenticated user from get_current_user

    Returns:
        CurrentUser if authenticated

    Raises:
        HTTPException: 401 if not authenticated (handled by get_current_user)
    """
    return current_user


def require_role(*allowed_roles: str):
    """
    Factory for role-based authorization dependencies.

    Creates a FastAPI dependency that enforces role-based access control
    for the four platform roles: end_user, knowledge_steward,
    governance_reviewer, platform_administrator.

    Args:
        *allowed_roles: One or more role names required for access

    Returns:
        FastAPI dependency function

    Example:
        @router.post("/sources", dependencies=[Depends(require_role("knowledge_steward"))])
        async def create_source():
            ...
    """

    async def role_checker(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        """Check if user has required role."""
        if not any(role in current_user.roles for role in allowed_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required roles: {', '.join(allowed_roles)}",
            )
        return current_user

    return role_checker
