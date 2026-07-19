import os
from typing import Generator
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker, Session

# Load environment variables from a .env file
load_dotenv()

# We default to local PostgreSQL using the psycopg 3 driver protocol: postgresql+psycopg://
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql+psycopg://postgres:postgres@localhost:5432/oea_db"
)

# Initialize the SQLAlchemy engine
# pool_pre_ping=True automatically tests connections before using them
engine = create_engine(
    DATABASE_URL, 
    pool_pre_ping=True
)

# Create a session factory
SessionLocal = sessionmaker(
    autocommit=False, 
    autoflush=False, 
    bind=engine
)

# Modern SQLAlchemy 2.0 Declarative Base syntax
class Base(DeclarativeBase):
    pass

def get_db() -> Generator[Session, None, None]:
    """
    FastAPI-ready dependency helper that yields a database session 
    and guarantees it closes after the operation completes.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
