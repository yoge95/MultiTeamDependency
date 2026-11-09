"""Database configuration and session management."""

import os
from sqlalchemy import create_engine, JSON
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import sessionmaker, declarative_base

# Get database URL from environment, default to SQLite for development
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./app.db")

# Determine if we're using SQLite (which doesn't support schemas or JSONB)
USE_SCHEMAS = not DATABASE_URL.startswith("sqlite")
IS_SQLITE = DATABASE_URL.startswith("sqlite")

# JSON type that works for both SQLite and PostgreSQL
JSONType = JSON if IS_SQLITE else JSONB

# Create engine with appropriate connection args
connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database by creating all tables."""
    # Import all models so they are registered with Base.metadata
    from app.models import org, knowledge, interaction, governance, ops
    
    Base.metadata.create_all(bind=engine)
