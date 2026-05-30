"""Database seeding. Runs on startup and populates the DB only if empty.

Persists just the observable incident columns (latent training labels from the
synthetic generator are intentionally dropped here).
"""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import Base, SessionLocal, engine
from app.models import Crew, Incident
from data.synth_generator import generate_crews, generate_incidents


def init_db() -> None:
    """Create all tables if they do not exist."""
    Base.metadata.create_all(bind=engine)


def _is_empty(db: Session) -> bool:
    return db.scalar(select(Incident.id).limit(1)) is None


def seed_if_empty() -> None:
    """Populate the DB with synthetic data if there are no incidents yet."""
    init_db()
    db = SessionLocal()
    try:
        if not _is_empty(db):
            return

        for crew in generate_crews():
            db.add(Crew(**crew))

        for rec in generate_incidents():
            db.add(
                Incident(
                    lat=rec["lat"],
                    lng=rec["lng"],
                    reported_at=rec["reported_at"],
                    cause=rec["cause"],
                    customers_affected=rec["customers_affected"],
                    weather_severity=rec["weather_severity"],
                    is_rural=rec["is_rural"],
                    near_critical_facility=rec["near_critical_facility"],
                    status=rec["status"],
                )
            )
        db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    seed_if_empty()
    print("Seed complete.")
