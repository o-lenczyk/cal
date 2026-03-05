import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://cal:cal@localhost:5432/cal")

engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base = declarative_base()


def get_session():
    """Get a new database session."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def get_db():
    """Get a database session (non-generator version for direct use)."""
    return SessionLocal()
