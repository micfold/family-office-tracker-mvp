from sqlalchemy import create_engine, event
from sqlmodel import SQLModel
import os
import logging

# --- DB Setup ---
DB_FILE = "data/cfo_tracker.db"
DB_URL = f"sqlite:///{DB_FILE}"

# Suppress verbose SQLAlchemy logging
logging.basicConfig()
logger = logging.getLogger(__name__)

engine = create_engine(DB_URL, echo=False)


def init_db(recreate: bool = False):
    """
    Initializes the database, creating tables from SQLModel metadata.
    """
    # Import all models here so SQLModel knows about them
    from src.domain.models.MAsset import Asset
    from src.domain.models.MRule import CategoryRule

    if recreate:
        logger.info("Recreating database tables...")
        SQLModel.metadata.drop_all(engine)

    logger.info("Creating database tables if they don't exist...")
    SQLModel.metadata.create_all(engine)

    # Ensure the data directory exists and is writable
    db_dir = os.path.dirname(DB_FILE)
    if not os.path.exists(db_dir):
        os.makedirs(db_dir)
    if not os.access(db_dir, os.W_OK):
        raise PermissionError(f"Database directory is not writable: {db_dir}")

    if recreate and os.path.exists(DB_FILE):
        os.remove(DB_FILE)
