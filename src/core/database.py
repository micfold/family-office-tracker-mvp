# src/core/database.py
from sqlmodel import SQLModel, create_engine, Session
from pathlib import Path

# Ensure data directory exists
DATA_DIR = Path(".data")
DATA_DIR.mkdir(exist_ok=True)

SQLITE_FILENAME = "family_office.db"
SQLITE_URL = f"sqlite:///{DATA_DIR / SQLITE_FILENAME}"

# connect_args={"check_same_thread": False} is needed for Streamlit's threading model
engine = create_engine(SQLITE_URL, echo=False, connect_args={"check_same_thread": False})

def init_db():
    """Creates the database tables based on imported models."""
    SQLModel.metadata.create_all(engine)

def get_session():
    """Dependency for getting a database session."""
    with Session(engine) as session:
        yield session