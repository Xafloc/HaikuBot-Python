"""Database connection and session management."""

import logging
from contextlib import contextmanager
from typing import Generator
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.engine import Engine

from .models import Base

logger = logging.getLogger(__name__)

# Global engine and session factory
_engine: Engine = None
_SessionLocal: sessionmaker = None


@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_conn, connection_record):
    """Enable foreign key constraints for SQLite."""
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


def init_db(database_url: str) -> None:
    """Initialize the database connection and create tables.
    
    Args:
        database_url: SQLAlchemy database URL (e.g., 'sqlite:///haiku.db')
    """
    global _engine, _SessionLocal
    
    logger.info(f"Initializing database: {database_url}")
    
    # Create engine
    _engine = create_engine(
        database_url,
        connect_args={"check_same_thread": False} if database_url.startswith("sqlite") else {},
        echo=False,  # Set to True for SQL debug logging
    )
    
    # Create session factory
    _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_engine)
    
    # Create all tables
    Base.metadata.create_all(bind=_engine)
    
    logger.info("Database initialized successfully")


def get_db() -> Engine:
    """Get the database engine.
    
    Returns:
        SQLAlchemy engine
        
    Raises:
        RuntimeError: If database hasn't been initialized
    """
    if _engine is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")
    return _engine


@contextmanager
def get_session() -> Generator[Session, None, None]:
    """Get a database session context manager.
    
    Yields:
        Database session
        
    Usage:
        with get_session() as session:
            # Use session here
            session.add(obj)
            session.commit()
    """
    if _SessionLocal is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")
    
    session = _SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_session_factory() -> sessionmaker:
    """Get the session factory.
    
    Returns:
        SessionLocal factory
        
    Raises:
        RuntimeError: If database hasn't been initialized
    """
    if _SessionLocal is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")
    return _SessionLocal

