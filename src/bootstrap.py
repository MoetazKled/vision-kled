"""Create tables and a single sample lead so the admin is not empty on first run."""

from sqlalchemy.orm import Session

from src import models  # noqa: F401  — register all tables on Base
from src.database import Base, SessionLocal, engine
from src.memory import upsert_lead
from src.models import Lead


def init_db() -> None:
    """Create tables if they do not exist yet."""
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_sample_lead(db)
    finally:
        db.close()


def seed_sample_lead(db: Session) -> None:
    """Insert one Tunisian test lead if the database is empty."""
    if db.query(Lead).count() > 0:
        return
    upsert_lead(
        db,
        {
            "name": "سارة بن علي",
            "phone": "+21620123456",
            "country": "Tunisia",
            "product": "portfolio",
            "source": "manual",
            "consent_opt_in": True,
            "language": "ar",
            "status": "new",
        },
    )
