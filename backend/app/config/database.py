from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, scoped_session

from app.config.settings import settings
from app.config.logging import logger

# Create SQLAlchemy engine
engine = create_engine(
    str(settings.DATABASE_URI),
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    pool_recycle=3600,
    echo=settings.DEBUG,
)

# Create session factory
SessionLocal = scoped_session(
    sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine,
    )
)

# Base class for models
Base = declarative_base()

def init_db() -> None:
    """Initialize the database."""
    try:
        # Import all models here to ensure they are registered with SQLAlchemy
        from app import models  # noqa: F401
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        logger.info("Database initialized")
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        raise

@contextmanager
def get_db() -> Generator[Session, None, None]:
    ""
    Dependency for getting a database session.
    
    Yields:
        SQLAlchemy database session
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Database error: {e}")
        raise
    finally:
        db.close()

def get_db_session() -> Session:
    """Get a database session."""
    return SessionLocal()

# Create database tables when the module is imported
init_db()
