"""Pytest configuration and shared fixtures."""

import os
import pytest
from datetime import datetime
from uuid import uuid4

# Set test database URL before importing app modules
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from app.database import Base, get_db
from app.main import app
from app.schemas.auth import CurrentUser, AccessScope

# Import all models so they are registered with Base.metadata
from app.models import org, knowledge, interaction, governance, ops


# Test database setup - use temp file to avoid :memory: isolation issues
import tempfile
_test_db_fd, _test_db_path = tempfile.mkstemp(suffix='.db')
import os as _os
_os.close(_test_db_fd)

TEST_DATABASE_URL = f"sqlite:///{_test_db_path}"
test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False}
)
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database session for each test."""
    Base.metadata.create_all(bind=test_engine)
    session = TestSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="function")
def client(db_session, mock_auth_user):
    """Create a test client with database session override."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    def override_get_current_user():
        return mock_auth_user
    
    def override_require_auth():
        return mock_auth_user
    
    def override_require_role(roles):
        def role_dependency():
            if not any(role in mock_auth_user.roles for role in roles):
                from fastapi import HTTPException, status
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Insufficient permissions"
                )
            return mock_auth_user
        return role_dependency
    
    from app.auth import get_current_user, require_auth, require_role
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user
    app.dependency_overrides[require_auth] = override_require_auth
    app.dependency_overrides[require_role] = override_require_role
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


@pytest.fixture
def mock_auth_user():
    """Create a mock authenticated user."""
    user_id = str(uuid4())
    return CurrentUser(
        user_id=user_id,
        email="test@example.com",
        roles=["end_user"],
        access_scope=AccessScope(
            user_id=user_id,
            roles=["end_user"],
            team_memberships=[],
            accessible_domains=[],
            source_scope_filter={}
        )
    )
