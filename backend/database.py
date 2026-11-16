"""Database session for each request."""

from sqlalchemy.orm import sessionmaker

from .config import engine

SessionLocal = sessionmaker(bind=engine)


def get_db():
    """FastAPI dependency: opens a session for one request and closes it afterwards."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
