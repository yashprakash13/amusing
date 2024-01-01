from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from .models import Base


def get_new_db_session(name: str = "./library.db") -> Session:
    """Create db and table and return a new session."""
    DATABASE_URL = f"sqlite:///{name}"
    engine = create_engine(DATABASE_URL, pool_size=20)
    Base.metadata.create_all(bind=engine)

    session = Session(bind=engine)
    return session
