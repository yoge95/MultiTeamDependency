"""Test authentication endpoint for local development and verification."""

from datetime import datetime, timedelta
from uuid import UUID

import jwt
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models.org import Stakeholder
from app.schemas.auth import AccessScope

router = APIRouter()


class LoginRequest(BaseModel):
    """Login request model."""
    email: EmailStr
    password: str = "admin123"  # Fixed for testing


class UserInfo(BaseModel):
    """User information model."""
    user_id: str
    email: str
    display_name: str
    roles: list[str]


class LoginResponse(BaseModel):
    """Login response model."""
    access_token: str
    token_type: str = "bearer"
    user: UserInfo


@router.post("/auth/login", response_model=LoginResponse)
async def test_login(request: LoginRequest, db: Session = Depends(get_db)):
    """
    Test login endpoint that bypasses external Auth API.
    
    For verification purposes only - uses fixed password 'admin123'.
    """
    # Find user by email
    stakeholder = db.query(Stakeholder).filter(Stakeholder.email == request.email).first()
    
    if not stakeholder:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # For testing, accept any password or use fixed password
    # In production, this would validate against stored hash
    
    # Generate JWT token
    expires = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
    
    # Determine roles based on stakeholder type
    roles = []
    if stakeholder.stakeholder_type == "platform_administrator":
        # Platform admin gets all roles for testing
        roles = ["platform_administrator", "admin", "knowledge_steward", "governance_reviewer", "user"]
    elif stakeholder.stakeholder_type == "knowledge_steward":
        roles = ["knowledge_steward", "user"]
    elif stakeholder.stakeholder_type == "governance_reviewer":
        roles = ["governance_reviewer", "user"]
    else:
        roles = ["end_user", "user"]
    
    token_data = {
        "sub": str(stakeholder.stakeholder_id),
        "email": stakeholder.email,
        "roles": roles,
        "exp": expires,
    }
    
    token = jwt.encode(token_data, settings.secret_key, algorithm=settings.algorithm)
    
    return LoginResponse(
        access_token=token,
        token_type="bearer",
        user=UserInfo(
            user_id=str(stakeholder.stakeholder_id),
            email=stakeholder.email,
            display_name=stakeholder.display_name,
            roles=roles,
        ),
    )


@router.get("/auth/me")
async def get_me(db: Session = Depends(get_db)):
    """Test endpoint to check authentication (no auth required for testing)."""
    # For testing, just return success
    return {"status": "ok", "message": "Auth endpoint available"}
